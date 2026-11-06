"""FastAPI Router for Melooha Auspicious Muhurta Engine."""

from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BirthProfile, Chart, MuhurtaNotification, MuhurtaPlan, User
from backend.muhurta.models import (
    MuhurtaQueryRequest,
    MuhurtaResponse,
    MuhurtaSlot,
)
from backend.muhurta.orchestrator import muhurta_graph

router = APIRouter(prefix="/api/muhurta", tags=["Auspicious Muhurta Engine"])


@router.post("/plan", response_model=MuhurtaResponse, status_code=status.HTTP_200_OK)
def plan_auspicious_muhurta(req: MuhurtaQueryRequest, db: Session = Depends(get_db)):
    """
    Generate mathematically exact, hyper-personalized auspicious Muhurta time windows
    synchronized with user's Vedic birth chart using Swiss Ephemeris and LangGraph.
    """
    user_janma_nakshatra_num = None
    user_janma_rashi_num = None
    profile_name = "You"

    # 1. Fetch User & Birth Chart if provided
    profile = None
    if req.profile_id:
        profile = db.query(BirthProfile).filter(BirthProfile.id == req.profile_id).first()
    elif req.user_id:
        profile = (
            db.query(BirthProfile)
            .filter(BirthProfile.user_id == req.user_id)
            .order_by(BirthProfile.created_at.desc())
            .first()
        )

    if profile:
        profile_name = profile.name
        chart = db.query(Chart).filter(Chart.birth_profile_id == profile.id).first()
        if chart and chart.facts_json:
            facts = chart.facts_json
            # Find Moon in chart planets
            planets = facts.get("planets", [])
            moon_p = next((p for p in planets if p.get("planet") == "Moon"), None)
            if moon_p:
                user_janma_rashi_num = moon_p.get("sign_number")
                nak = moon_p.get("nakshatra", {})
                user_janma_nakshatra_num = nak.get("number")

    # 2. Setup initial state for LangGraph
    initial_state = {
        "user_id": req.user_id or "guest_user",
        "profile_id": req.profile_id or (profile.id if profile else None),
        "profile_name": profile_name,
        "user_janma_nakshatra_num": user_janma_nakshatra_num,
        "user_janma_rashi_num": user_janma_rashi_num,
        "raw_query": req.query,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "location_name": req.location_name or (profile.place_name if profile else None),
        "latitude": req.latitude or (profile.latitude if profile else None),
        "longitude": req.longitude or (profile.longitude if profile else None),
        "timezone_str": req.timezone_str or (profile.timezone_str if profile else None),
        "explicit_category": req.category,
        "explicit_override": req.override,
        "parsed_intent": None,
        "raw_candidates": [],
        "scored_slots": [],
        "final_response": None,
        "error": None,
    }

    try:
        graph_output = muhurta_graph.invoke(initial_state)
        response: Optional[MuhurtaResponse] = graph_output.get("final_response")
        if not response:
            raise HTTPException(status_code=500, detail="Muhurta calculation failed to produce slots")

        # 3. Persist plan in Database
        user_to_bind = None
        if req.user_id:
            user_to_bind = db.query(User).filter(User.id == req.user_id).first()
        if not user_to_bind and profile and profile.user_id:
            user_to_bind = db.query(User).filter(User.id == profile.user_id).first()

        if user_to_bind:
            slots_data = [slot.model_dump() for slot in response.slots]
            plan_rec = MuhurtaPlan(
                id=response.muhurta_id,
                user_id=user_to_bind.id,
                birth_profile_id=profile.id if profile else None,
                query_text=req.query,
                category=response.activity.get("category", "business_finance"),
                override=response.activity.get("override"),
                location_name=response.location.get("name", "Unknown"),
                latitude=response.location["coordinates"]["lat"],
                longitude=response.location["coordinates"]["lon"],
                timezone_str=response.location.get("timezone", "Asia/Kolkata"),
                target_start_date=datetime.fromisoformat(response.slots[0].start_time_local).date() if response.slots else datetime.now().date(),
                target_end_date=datetime.fromisoformat(response.slots[-1].end_time_local).date() if response.slots else datetime.now().date(),
                time_preference=graph_output["parsed_intent"].time_preference.value,
                slots_json=slots_data,
                advisory_note=response.advisory_note,
            )
            db.add(plan_rec)
            db.flush()  # Persist parent record first to satisfy foreign key constraints

            # Schedule 24h & 1h notifications for the top slot
            if response.slots:
                try:
                    top_start = datetime.fromisoformat(response.slots[0].start_time_local)
                    now_utc = datetime.now(ZoneInfo("UTC"))

                    # 24h before
                    t_24h = top_start - timedelta(hours=24)
                    if t_24h > now_utc:
                        db.add(MuhurtaNotification(
                            muhurta_plan_id=response.muhurta_id,
                            user_id=user_to_bind.id,
                            channel="push",
                            trigger_time=t_24h,
                            reminder_type="24h",
                            status="pending",
                            payload={"activity": response.activity, "slot_time": response.slots[0].start_time_local},
                        ))

                    # 1h before
                    t_1h = top_start - timedelta(hours=1)
                    if t_1h > now_utc:
                        db.add(MuhurtaNotification(
                            muhurta_plan_id=response.muhurta_id,
                            user_id=user_to_bind.id,
                            channel="push",
                            trigger_time=t_1h,
                            reminder_type="1h",
                            status="pending",
                            payload={"activity": response.activity, "slot_time": response.slots[0].start_time_local},
                        ))
                except Exception as notif_err:
                    print("Notification scheduling note:", notif_err)

            db.commit()

        return response
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Muhurta calculation error: {str(e)}")


@router.get("/history/{user_id}")
def get_user_muhurta_history(user_id: str, db: Session = Depends(get_db)):
    """Retrieve history of auspicious Muhurta searches for user."""
    plans = (
        db.query(MuhurtaPlan)
        .filter(MuhurtaPlan.user_id == user_id)
        .order_by(MuhurtaPlan.created_at.desc())
        .limit(15)
        .all()
    )

    return {
        "user_id": user_id,
        "history": [
            {
                "muhurta_id": p.id,
                "query": p.query_text,
                "category": p.category,
                "override": p.override,
                "location": p.location_name,
                "slots_count": len(p.slots_json) if isinstance(p.slots_json, list) else 0,
                "top_slot": p.slots_json[0] if (isinstance(p.slots_json, list) and len(p.slots_json) > 0) else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in plans
        ]
    }


@router.get("/{muhurta_id}/ics")
def download_muhurta_ics(muhurta_id: str, slot_rank: int = 1, db: Session = Depends(get_db)):
    """Direct downloadable RFC 5545 iCalendar (.ics) file for 1-tap booking."""
    plan = db.query(MuhurtaPlan).filter(MuhurtaPlan.id == muhurta_id).first()
    if not plan or not plan.slots_json:
        raise HTTPException(status_code=404, detail="Muhurta plan not found")

    slots = plan.slots_json
    target_slot = next((s for s in slots if s.get("rank") == slot_rank), slots[0] if slots else None)
    if not target_slot or "calendar_payload" not in target_slot:
        raise HTTPException(status_code=404, detail="Calendar payload missing in slot")

    ics_data = target_slot["calendar_payload"]["ics_data"]
    filename = f"melooha-muhurta-{plan.override or plan.category}-{muhurta_id[:8]}.ics"

    return Response(
        content=ics_data,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class ScheduleAlertRequest(BaseModel):
    channel: str = "push"  # "push", "whatsapp", "telegram"
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None


@router.post("/{muhurta_id}/schedule-alert")
def schedule_muhurta_alert(muhurta_id: str, req: ScheduleAlertRequest, db: Session = Depends(get_db)):
    """Activate push, WhatsApp, or Telegram webhook alerts for this Muhurta."""
    plan = db.query(MuhurtaPlan).filter(MuhurtaPlan.id == muhurta_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Muhurta plan not found")

    notifs = db.query(MuhurtaNotification).filter(MuhurtaNotification.muhurta_plan_id == muhurta_id).all()
    for n in notifs:
        n.channel = req.channel
        if not n.payload:
            n.payload = {}
        if req.phone_number:
            n.payload["phone_number"] = req.phone_number
        if req.telegram_chat_id:
            n.payload["telegram_chat_id"] = req.telegram_chat_id

    db.commit()
    return {
        "status": "scheduled",
        "muhurta_id": muhurta_id,
        "channel": req.channel,
        "alerts_count": len(notifs),
        "message": f"Auspicious Muhurta reminders activated via {req.channel}."
    }
