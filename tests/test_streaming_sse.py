"""Unit tests for Server-Sent Events (SSE) streaming, verification, and replacement."""

from datetime import date
import json
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.ledger import get_balance
from backend.models import Answer, Question
from backend.service import OnboardingService, QuestionService
from backend.streaming import stream_question_answer
from llm.client import AllProvidersFailedError, LLMResponse, ModelOrchestrator


@pytest.fixture
def test_db():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


def parse_sse_events(raw_stream):
    """Parse list of SSE events from string generator."""
    events = []
    current_event = None
    current_data = None
    for chunk in raw_stream:
        lines = chunk.strip().split("\n")
        for line in lines:
            if line.startswith("event: "):
                current_event = line[7:].strip()
            elif line.startswith("data: "):
                current_data = json.loads(line[6:].strip())
        if current_event and current_data is not None:
            events.append({"event": current_event, "data": current_data})
            current_event = None
            current_data = None
    return events


def test_streaming_verified_happy_path(test_db):
    user, profile, chart, facts = OnboardingService.create_user_and_chart(
        db=test_db,
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )
    q = QuestionService.ask_question(
        db=test_db,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="What does my career look like?",
        idempotency_key="q_stream_1",
    )

    # Mock orchestrator
    mock_orch = MagicMock(spec=ModelOrchestrator)
    mock_orch.generate.return_value = LLMResponse(
        content=json.dumps({
            "answer": "Your chart features Virgo Lagna in House 1 [F01]. Current Mahadasha is Venus [F12].",
            "cited_fact_ids": ["F01", "F12"],
            "claims": [],
        }),
        provider="gemini",
        duration_ms=250.0,
    )

    stream_gen = stream_question_answer(test_db, q.id, orchestrator=mock_orch)
    events = parse_sse_events(stream_gen)

    event_names = [e["event"] for e in events]
    assert "status" in event_names
    assert "token" in event_names
    assert "verified" in event_names
    assert "end" in event_names

    # Verify final 'verified' payload
    verified_ev = next(e for e in events if e["event"] == "verified")
    assert verified_ev["data"]["status"] == "completed"
    assert verified_ev["data"]["provider"] == "gemini"
    assert len(verified_ev["data"]["cited_facts"]) == 2

    # Database verification
    test_db.refresh(q)
    assert q.status == "completed"
    ans = test_db.query(Answer).filter(Answer.question_id == q.id).first()
    assert ans is not None
    assert ans.is_verified is True


def test_streaming_replace_on_grounding_violation(test_db):
    """When LLM hallucinates an invalid fact ID, SSE emits 'replace' with safe fallback."""
    user, profile, _, _ = OnboardingService.create_user_and_chart(
        db=test_db,
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )
    q = QuestionService.ask_question(
        db=test_db,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="What does my career look like?",
        idempotency_key="q_stream_2",
    )

    mock_orch = MagicMock(spec=ModelOrchestrator)
    # Returns hallucinated fact ID F99
    mock_orch.generate.return_value = LLMResponse(
        content=json.dumps({
            "answer": "Hallucinated reading with invalid ID [F99].",
            "cited_fact_ids": ["F99"],
            "claims": [],
        }),
        provider="gemini",
        duration_ms=200.0,
    )

    stream_gen = stream_question_answer(test_db, q.id, orchestrator=mock_orch)
    events = parse_sse_events(stream_gen)

    event_names = [e["event"] for e in events]
    assert "replace" in event_names
    replace_ev = next(e for e in events if e["event"] == "replace")
    assert replace_ev["data"]["status"] == "completed"
    assert replace_ev["data"]["provider"] == "template_fallback"
    assert "Grounded Vedic Astrology Reading" in replace_ev["data"]["answer"]

    # In database
    test_db.refresh(q)
    assert q.status == "completed"
    ans = test_db.query(Answer).filter(Answer.question_id == q.id).first()
    assert ans.provider == "template_fallback"


def test_streaming_provider_failure_triggers_automatic_refund(test_db):
    """When generation fails completely, question is refunded and friendly error event is emitted."""
    user, profile, _, _ = OnboardingService.create_user_and_chart(
        db=test_db,
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )
    # Balance is 1 after signup
    assert get_balance(test_db, user.id) == 1

    q = QuestionService.ask_question(
        db=test_db,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="Will this fail?",
        idempotency_key="q_stream_3",
    )
    # Balance spent: 0
    assert get_balance(test_db, user.id) == 0

    mock_orch = MagicMock(spec=ModelOrchestrator)
    mock_orch.generate.side_effect = AllProvidersFailedError("All failed", {})

    stream_gen = stream_question_answer(test_db, q.id, orchestrator=mock_orch)
    events = parse_sse_events(stream_gen)

    event_names = [e["event"] for e in events]
    assert "error" in event_names
    error_ev = next(e for e in events if e["event"] == "error")
    assert error_ev["data"]["refunded"] is True
    assert "cosmic connection was briefly interrupted" in error_ev["data"]["message"]

    # Balance automatically refunded back to 1!
    assert get_balance(test_db, user.id) == 1
    test_db.refresh(q)
    assert q.status == "refunded"
