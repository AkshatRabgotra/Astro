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
from backend.models import Answer, BalanceLedger, BirthProfile, Chart, Event, Question, User
from backend.places import search_cities
from backend.service import OnboardingService, QuestionService
from backend.streaming import stream_question_answer
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
    Onboard a user, calculate birth chart facts, grant 1 free question credit.
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
        )
        current_bal = get_balance(db, user.id)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "birth_date": str(profile.birth_date),
                "birth_time": profile.birth_time,
                "time_known": profile.time_known,
                "place_name": profile.place_name,
            },
            "chart_id": chart.id,
            "chart_facts": facts.model_dump(),
            "balance": current_bal,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    """Get all past questions, answers, and cited chart facts."""
    questions = db.query(Question).filter(
        Question.user_id == user_id
    ).order_by(Question.created_at.asc()).all()

    history = []
    for q in questions:
        ans = db.query(Answer).filter(Answer.question_id == q.id).first()
        history.append({
            "id": q.id,
            "question_text": q.question_text,
            "status": q.status,
            "created_at": q.created_at.isoformat(),
            "answer": {
                "id": ans.id,
                "answer_text": ans.answer_text,
                "cited_fact_ids": ans.cited_fact_ids,
                "provider": ans.provider,
                "is_verified": ans.is_verified,
                "verification_notes": ans.verification_notes,
                "created_at": ans.created_at.isoformat(),
            } if ans else None,
        })

    return {"user_id": user_id, "history": history}


@app.get("/api/chart/{birth_profile_id}")
def get_profile_chart(birth_profile_id: str, db: Session = Depends(get_db)):
    """Retrieve computed ChartFacts for a birth profile."""
    chart = db.query(Chart).filter(Chart.birth_profile_id == birth_profile_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return chart.facts_json


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
