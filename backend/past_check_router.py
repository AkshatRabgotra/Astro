"""FastAPI Router for Past Check Trust Feature and A/B Experiment."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BirthProfile, Event
from backend.past_check import (
    get_or_create_past_check_set,
    record_past_check_answer,
    get_or_assign_experiment_arm,
)

router = APIRouter(prefix="/api/user/{user_id}/past-check", tags=["past-check"])


class PastCheckAnswerRequest(BaseModel):
    item_id: str
    answer: str = Field(..., pattern="^(yes|not_really|cant_recall)$")


@router.get("")
def get_past_check(
    user_id: str,
    lang: str = Query("en", pattern="^(en|hi)$"),
    db: Session = Depends(get_db),
):
    """
    Fetch the Past Check set for the user before the zero-balance paywall.
    Assigned to control (50%) or treatment (50%).
    is_decoy is strictly stripped on the server and never returned.
    """
    profile = db.query(BirthProfile).filter(BirthProfile.user_id == user_id).first()
    if not profile:
        profile = db.query(BirthProfile).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Birth profile not found")

    res = get_or_create_past_check_set(db=db, user_id=user_id, profile=profile, lang=lang)

    # Log past_check_shown event if treatment and active
    if res.get("should_show"):
        ev = Event(
            user_id=user_id,
            event_name="past_check_shown",
            payload={"arm": res.get("arm"), "set_id": res.get("set_id"), "lang": lang},
        )
        db.add(ev)
        db.commit()

    return res


@router.post("/answer")
def submit_past_check_answer(
    user_id: str,
    req: PastCheckAnswerRequest,
    db: Session = Depends(get_db),
):
    """
    Submit answer to a Past Check statement item ('yes', 'not_really', 'cant_recall').
    Idempotent upsert. Logs past_check_answered and past_check_completed.
    """
    arm = get_or_assign_experiment_arm(db, user_id)
    try:
        res = record_past_check_answer(
            db=db,
            user_id=user_id,
            item_id=req.item_id,
            answer=req.answer,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Log analytics
    ev_ans = Event(
        user_id=user_id,
        event_name="past_check_answered",
        payload={"arm": arm, "item_id": req.item_id, "answer": req.answer},
    )
    db.add(ev_ans)

    if res.get("is_completed"):
        ev_comp = Event(
            user_id=user_id,
            event_name="past_check_completed",
            payload={
                "arm": arm,
                "recognized_count": res.get("recognized_count"),
                "total": res.get("total_statements"),
            },
        )
        db.add(ev_comp)

    db.commit()
    return res
