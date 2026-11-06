"""FastAPI Application entry point for Melooha AI Vedic Astrology."""

from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.ledger import (
    InsufficientBalanceError,
    get_balance,
    refund_question_credit,
    topup_credits,
)
from backend.models import Answer, BalanceLedger, BirthProfile, Chart, Event, MuhurtaPlan, Question, User
from backend.places import search_cities
from backend.service import OnboardingService, QuestionService
from backend.rewards import (
    claim_mantra_reward,
    claim_streak_reward,
    get_user_reward_state,
    redeem_referral_code,
)
from chart.models import ChartFacts
from chart.transits import calculate_today_transits
from backend.streaming import stream_question_answer
from llm.fallback import build_astro_references
from backend.twin_router import router as twin_router
from backend.past_check_router import router as past_check_router
from backend.auth_router import router as auth_router
from backend.muhurta_router import router as muhurta_router
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Melooha AI Vedic Astrology API",
    description="Backend with Swiss Ephemeris chart engine, append-only credit ledger, grounded Q&A, and metrics.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(twin_router)
app.include_router(past_check_router)
app.include_router(auth_router)
app.include_router(muhurta_router)


# --- Request & Response Schemas ---
class OnboardingRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Akshat"})
    birth_date: date = Field(..., json_schema_extra={"example": "1995-05-24"})
    birth_time: Optional[str] = Field(None, json_schema_extra={"example": "14:15:00"})
    time_known: bool = Field(True)
    latitude: float = Field(..., json_schema_extra={"example": 19.0760})
    longitude: float = Field(..., json_schema_extra={"example": 72.8777})
    timezone_str: str = Field(..., json_schema_extra={"example": "Asia/Kolkata"})
    place_name: Optional[str] = Field(None, json_schema_extra={"example": "Mumbai, Maharashtra, India"})
    email: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)
    profile_id: Optional[str] = Field(None)
    is_new_profile: bool = Field(False)


class TopupRequest(BaseModel):
    count: int = Field(..., gt=0, json_schema_extra={"example": 5})
    idempotency_key: str = Field(..., json_schema_extra={"example": "topup_12345"})


class AskQuestionRequest(BaseModel):
    user_id: str
    birth_profile_id: str
    question_text: str = Field(..., min_length=3)
    idempotency_key: str


# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Melooha API"}


@app.get("/api/places/search")
def search_places(q: str = "", limit: int = 15):
    """Search global and Indian cities for birth chart calculations."""
    return {"places": search_cities(q, limit=limit)}


@app.post("/api/onboarding", status_code=status.HTTP_201_CREATED)
def onboard_user(req: OnboardingRequest, db: Session = Depends(get_db)):
    """
    Onboard a user, add a family member, or update an existing profile.
    """
    try:
        user, profile, chart, facts = OnboardingService.create_user_and_chart(
            db=db,
            name=req.name,
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            time_known=req.time_known,
            latitude=req.latitude,
            longitude=req.longitude,
            timezone_str=req.timezone_str,
            place_name=req.place_name,
            email=req.email,
            user_id=req.user_id,
            profile_id=req.profile_id,
            is_new_profile=req.is_new_profile,
        )
        all_profiles = (
            db.query(BirthProfile)
            .filter(BirthProfile.user_id == user.id)
            .order_by(BirthProfile.created_at.asc())
            .all()
        )
        current_bal = get_balance(db, user.id)
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "auth_provider": user.auth_provider,
            },
            "profile": {
                "id": profile.id,
                "user_id": user.id,
                "name": profile.name,
                "place_name": profile.place_name,
                "birth_date": str(profile.birth_date),
                "birth_time": profile.birth_time,
                "time_known": profile.time_known,
                "latitude": profile.latitude,
                "longitude": profile.longitude,
                "timezone_str": profile.timezone_str,
            },
            "profiles": [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "name": p.name,
                    "place_name": p.place_name,
                    "birth_date": str(p.birth_date),
                    "birth_time": p.birth_time,
                    "time_known": p.time_known,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "timezone_str": p.timezone_str,
                }
                for p in all_profiles
            ],
            "chart_id": chart.id,
            "chart_facts": facts.model_dump(),
            "balance": current_bal,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/user/{user_id}/profiles")
def get_user_profiles(user_id: str, db: Session = Depends(get_db)):
    """Retrieve all family member birth profiles for a user."""
    profiles = db.query(BirthProfile).filter(BirthProfile.user_id == user_id).order_by(BirthProfile.created_at.asc()).all()
    return {
        "profiles": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "name": p.name,
                "place_name": p.place_name,
                "birth_date": str(p.birth_date),
                "birth_time": p.birth_time,
                "time_known": p.time_known,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "timezone_str": p.timezone_str,
            }
            for p in profiles
        ]
    }


@app.get("/api/profile/{profile_id}/chart")
def get_profile_chart(profile_id: str, db: Session = Depends(get_db)):
    """Retrieve birth profile and calculated chart facts for an active member."""
    profile = db.query(BirthProfile).filter(BirthProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    chart = db.query(Chart).filter(Chart.birth_profile_id == profile.id).first()
    facts_data = None
    if chart and chart.facts_json:
        facts_data = chart.facts_json
    else:
        # Calculate chart if missing
        from chart.models import BirthInput
        from chart.engine import calculate_chart_facts
        import json
        birth_input = BirthInput(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            time_known=profile.time_known,
            latitude=profile.latitude,
            longitude=profile.longitude,
            timezone_str=profile.timezone_str,
            place_name=profile.place_name,
        )
        facts = calculate_chart_facts(birth_input)
        facts_data = json.loads(facts.model_dump_json())
        chart = Chart(
            birth_profile_id=profile.id,
            ayanamsa=facts.ayanamsa_name,
            facts_json=facts_data,
        )
        db.add(chart)
        db.commit()

    return {
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "name": profile.name,
            "place_name": profile.place_name,
            "birth_date": str(profile.birth_date),
            "birth_time": profile.birth_time,
            "time_known": profile.time_known,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "timezone_str": profile.timezone_str,
        },
        "chart_facts": facts_data,
    }


@app.get("/api/user/{user_id}/balance")
def get_user_balance(user_id: str, db: Session = Depends(get_db)):
    """Retrieve current balance and full append-only ledger history."""
    bal = get_balance(db, user_id)
    ledger_entries = db.query(BalanceLedger).filter(
        BalanceLedger.user_id == user_id
    ).order_by(BalanceLedger.created_at.desc()).all()

    return {
        "user_id": user_id,
        "balance": bal,
        "ledger": [
            {
                "id": entry.id,
                "amount": entry.amount,
                "entry_type": entry.entry_type,
                "description": entry.description,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in ledger_entries
        ],
    }


@app.post("/api/user/{user_id}/topup")
def topup_user_credits(user_id: str, req: TopupRequest, db: Session = Depends(get_db)):
    """
    Top up question balance by N credits (no payment). Idempotent.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_bal = topup_credits(
        db=db,
        user_id=user_id,
        count=req.count,
        idempotency_key=req.idempotency_key,
    )

    # Log topup event
    db.add(Event(user_id=user_id, event_name="topup_completed", payload={"count": req.count}))
    db.commit()

    return {"user_id": user_id, "balance": new_bal, "added": req.count}


@app.post("/api/questions")
def ask_question(req: AskQuestionRequest, db: Session = Depends(get_db)):
    """
    Spend 1 credit and create a question.
    """
    try:
        question = QuestionService.ask_question(
            db=db,
            user_id=req.user_id,
            birth_profile_id=req.birth_profile_id,
            question_text=req.question_text,
            idempotency_key=req.idempotency_key,
        )
        rem_balance = get_balance(db, req.user_id)
        return {
            "question_id": question.id,
            "status": question.status,
            "question_text": question.question_text,
            "remaining_balance": rem_balance,
        }
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/questions/{question_id}/stream")
def stream_answer(question_id: str, db: Session = Depends(get_db)):
    """
    Stream answer generation over SSE with token-by-token emission,
    final verified grounding event, or replace event if safe fallback is triggered.
    """
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    return StreamingResponse(
        stream_question_answer(db=db, question_id=question_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/user/{user_id}/history")
def get_user_history(user_id: str, db: Session = Depends(get_db), birth_profile_id: Optional[str] = None):
    """Get all past questions, answers, and auspicious muhurta plans, optionally filtered by birth_profile_id."""
    if isinstance(birth_profile_id, Session):
        db, birth_profile_id = birth_profile_id, None

    # 1. Vedic Astrology Questions
    q_query = db.query(Question).filter(Question.user_id == user_id)
    if birth_profile_id:
        q_query = q_query.filter(Question.birth_profile_id == birth_profile_id)
    questions = q_query.all()

    history = []
    # Cache charts for building astro_references
    profile_charts = {}

    for q in questions:
        ans = db.query(Answer).filter(Answer.question_id == q.id).first()
        astro_refs = []
        if ans and ans.cited_fact_ids:
            if q.birth_profile_id not in profile_charts:
                ch = db.query(Chart).filter(Chart.birth_profile_id == q.birth_profile_id).first()
                if ch and ch.facts_json:
                    profile_charts[q.birth_profile_id] = ChartFacts.model_validate(ch.facts_json)
                else:
                    profile_charts[q.birth_profile_id] = None
            cf = profile_charts.get(q.birth_profile_id)
            if cf:
                astro_refs = build_astro_references(cf, ans.cited_fact_ids, q.question_text)

        history.append({
            "id": q.id,
            "type": "astrology",
            "category_label": "Vedic Astrology",
            "birth_profile_id": q.birth_profile_id,
            "question_text": q.question_text,
            "status": q.status,
            "created_at": q.created_at.isoformat() if hasattr(q.created_at, "isoformat") else str(q.created_at),
            "answer": {
                "id": ans.id,
                "answer_text": ans.answer_text,
                "cited_fact_ids": ans.cited_fact_ids,
                "astro_references": astro_refs,
                "provider": ans.provider,
                "is_verified": ans.is_verified,
                "verification_notes": ans.verification_notes,
                "created_at": ans.created_at.isoformat() if hasattr(ans.created_at, "isoformat") else str(ans.created_at),
            } if ans else None,
        })

    # 2. Auspicious Muhurta Plans
    m_query = db.query(MuhurtaPlan).filter(MuhurtaPlan.user_id == user_id)
    if birth_profile_id:
        m_query = m_query.filter(MuhurtaPlan.birth_profile_id == birth_profile_id)
    muhurtas = m_query.all()

    for m in muhurtas:
        slots = m.slots_json or []
        slot_lines = []
        for s in slots[:3]:
            start_str = s.get("start_time_local", "")
            end_str = s.get("end_time_local", "")
            quality = s.get("quality", "Auspicious")
            score = s.get("score", s.get("total_score", 90))
            slot_lines.append(f"- **{start_str}** to **{end_str}** ({quality}) — Score: {score}/100")

        ans_markdown = (
            f"### Auspicious Muhurta Recommendation\n"
            f"{m.advisory_note or 'Calculated aligned with your natal Moon chart.'}\n\n"
            f"**Auspicious Time Windows**:\n"
            + ("\n".join(slot_lines) if slot_lines else "Calculated Muhurta slot recorded.")
        )

        history.append({
            "id": m.id,
            "type": "muhurta",
            "category_label": "Auspicious Muhurta",
            "birth_profile_id": m.birth_profile_id,
            "question_text": m.query_text or f"Auspicious timing for {m.category.replace('_', ' ').title()}",
            "status": "completed",
            "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
            "muhurta_data": {
                "category": m.category,
                "location": m.location_name,
                "slots": slots,
            },
            "answer": {
                "id": f"ans_{m.id}",
                "answer_text": ans_markdown,
                "cited_fact_ids": [],
                "provider": "muhurta_engine",
                "is_verified": True,
                "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
            },
        })

    # Sort combined history by created_at descending (newest first)
    history.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

    return {"user_id": user_id, "birth_profile_id": birth_profile_id, "history": history}


@app.get("/api/chart/{birth_profile_id}")
def get_profile_chart(birth_profile_id: str, db: Session = Depends(get_db)):
    """Retrieve computed ChartFacts for a birth profile."""
    chart = db.query(Chart).filter(Chart.birth_profile_id == birth_profile_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return chart.facts_json


@app.get("/api/chart/{birth_profile_id}/transits")
def get_chart_transits(birth_profile_id: str, db: Session = Depends(get_db)):
    """Calculate today's real-time planetary transits overlaid on natal chart."""
    chart = db.query(Chart).filter(Chart.birth_profile_id == birth_profile_id).first()
    if not chart:
        # Check if user_id or profile_id was passed
        profile = db.query(BirthProfile).filter((BirthProfile.id == birth_profile_id) | (BirthProfile.user_id == birth_profile_id)).first()
        if profile:
            chart = db.query(Chart).filter(Chart.birth_profile_id == profile.id).first()
        else:
            # Check by Chart.id
            chart = db.query(Chart).filter(Chart.id == birth_profile_id).first()
            if not chart:
                chart = db.query(Chart).first()

    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    facts = ChartFacts.model_validate(chart.facts_json)
    moon_planet = next((p for p in facts.planets if p.planet == "Moon"), None)
    if not moon_planet:
        raise HTTPException(status_code=400, detail="Moon position missing in chart")

    report = calculate_today_transits(
        natal_lagna_sign_num=facts.lagna_sign_number,
        natal_moon_sign_num=moon_planet.sign_number,
    )
    return report.model_dump()


@app.get("/api/user/{user_id}/home-content")
def get_user_home_content(
    user_id: str,
    profile_id: Optional[str] = None,
    lang: str = "en",
    db: Session = Depends(get_db),
):
    """
    Get 100% grounded Home screen content with explicit Fact IDs:
    - Daily Moon transit insight
    - Traditional Varadhipati (day-lord) color & number
    - Gochara balance percentage with formula
    - Dynamically generated questions anchored to active dasha and transits
    """
    profile = None
    if profile_id:
        profile = (
            db.query(BirthProfile)
            .filter(BirthProfile.id == profile_id)
            .first()
        )

    if not profile:
        profile = (
            db.query(BirthProfile)
            .filter(BirthProfile.user_id == user_id)
            .order_by(BirthProfile.created_at.desc())
            .first()
        )

    if not profile:
        profile = db.query(BirthProfile).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    chart = db.query(Chart).filter(Chart.birth_profile_id == profile.id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    facts = ChartFacts.model_validate(chart.facts_json)
    moon = next((p for p in facts.planets if p.planet == "Moon"), None)
    if not moon:
        raise HTTPException(status_code=500, detail="Moon position missing in chart facts")

    lagna_num = facts.lagna_sign_number
    active_md = facts.current_dasha.mahadasha_lord if facts.current_dasha else "Moon"
    active_ad = facts.current_dasha.antardasha_lord if facts.current_dasha else "Jupiter"

    from backend.home_content import get_grounded_home_content
    return get_grounded_home_content(
        natal_lagna_sign_num=lagna_num,
        natal_moon_sign_num=moon.sign_number,
        active_mahadasha=active_md,
        active_antardasha=active_ad,
        lang=lang,
    )


class ClaimMantraRequest(BaseModel):
    planet: str = "Mars"


class RedeemReferralRequest(BaseModel):
    code: str


@app.get("/api/user/{user_id}/rewards")
def get_rewards_state(user_id: str, db: Session = Depends(get_db), profile_id: Optional[str] = None):
    """Fetch user's daily streak, referral code, and mantra progress for active family member."""
    if isinstance(profile_id, Session):
        db, profile_id = profile_id, None
    return get_user_reward_state(db, user_id, profile_id=profile_id)


@app.post("/api/user/{user_id}/rewards/claim-streak")
def handle_claim_streak(user_id: str, db: Session = Depends(get_db), profile_id: Optional[str] = None):
    """Claim today's 7-day streak reward for active family member."""
    if isinstance(profile_id, Session):
        db, profile_id = profile_id, None
    return claim_streak_reward(db, user_id, profile_id=profile_id)


@app.post("/api/user/{user_id}/rewards/claim-mantra")
def handle_claim_mantra(user_id: str, req: ClaimMantraRequest, db: Session = Depends(get_db)):
    """Claim remedial mantra reward for peace and consistency."""
    return claim_mantra_reward(db, user_id, req.planet)


@app.post("/api/user/{user_id}/rewards/redeem-referral")
def handle_redeem_referral(user_id: str, req: RedeemReferralRequest, db: Session = Depends(get_db)):
    """Redeem friend's referral code to get +5 questions free."""
    return redeem_referral_code(db, user_id, req.code)


@app.post("/api/events")
def record_event(user_id: Optional[str] = None, event_name: str = "custom", payload: Optional[Dict[str, Any]] = None, db: Session = Depends(get_db)):
    """Ingest UI interaction events for conversion tracking."""
    event = Event(user_id=user_id, event_name=event_name, payload=payload or {})
    db.add(event)
    db.commit()
    return {"status": "recorded"}


@app.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """
    Computes the primary metric:
    Share of free-question users who ask a second question.
    """
    total_users = db.query(User).count()
    if total_users == 0:
        return {
            "total_users": 0,
            "users_asked_at_least_one": 0,
            "users_asked_second_question": 0,
            "second_question_retention_rate_pct": 0.0,
            "total_questions_asked": 0,
            "total_topups": 0,
            "evidence_opened_count": 0,
        }

    # Count questions asked per user
    user_q_counts = {}
    for q in db.query(Question).all():
        user_q_counts[q.user_id] = user_q_counts.get(q.user_id, 0) + 1

    users_asked_1 = sum(1 for c in user_q_counts.values() if c >= 1)
    users_asked_2 = sum(1 for c in user_q_counts.values() if c >= 2)

    retention_pct = round((users_asked_2 / users_asked_1 * 100.0), 2) if users_asked_1 > 0 else 0.0

    total_topups = db.query(Event).filter(Event.event_name == "topup_completed").count()
    evidence_clicks = db.query(Event).filter(Event.event_name == "evidence_opened").count()

    return {
        "total_users": total_users,
        "users_asked_at_least_one": users_asked_1,
        "users_asked_second_question": users_asked_2,
        "second_question_retention_rate_pct": retention_pct,
        "total_questions_asked": sum(user_q_counts.values()),
        "total_topups": total_topups,
        "evidence_opened_count": evidence_clicks,
    }


@app.get("/api/metrics/past-check")
def get_past_check_metrics(db: Session = Depends(get_db)):
    """
    Returns Past Check A/B experiment metrics:
    - 2nd question retention rate by arm with n and Wilson 95% confidence intervals
    - Difference between arms
    - Real vs Decoy statement Yes-rate
    - Past Check completion rate
    - Small sample warnings (< 30)
    """
    from backend.past_check_metrics import compute_past_check_experiment_metrics
    return compute_past_check_experiment_metrics(db)


# Mount built frontend static files if present (for single-command unified deployment)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        # Allow API routes to be handled by FastAPI
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
