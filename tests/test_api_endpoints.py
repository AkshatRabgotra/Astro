"""Integration tests for FastAPI application endpoint functions."""

from datetime import date
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.main import (
    AskQuestionRequest,
    ClaimMantraRequest,
    OnboardingRequest,
    RedeemReferralRequest,
    TopupRequest,
    ask_question,
    get_metrics,
    get_profile_chart,
    get_rewards_state,
    get_user_balance,
    get_user_history,
    handle_claim_mantra,
    handle_claim_streak,
    handle_redeem_referral,
    health_check,
    onboard_user,
    search_places,
    topup_user_credits,
)


@pytest.fixture
def db():
    """In-memory database session fixture."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "ok"
    assert "Melooha" in res["app"]


def test_places_search_endpoint():
    # Test prefix matching
    res = search_places(q="mum")
    assert len(res["places"]) > 0
    assert "Mumbai" in res["places"][0]["name"]

    # Test global city search
    res = search_places(q="London")
    assert any("London" in p["name"] for p in res["places"])

    # Test empty query returns top cities
    res_empty = search_places(q="")
    assert len(res_empty["places"]) > 0


def test_api_onboarding_and_balance_flow(db):
    # 1. Onboarding
    req = OnboardingRequest(
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
        place_name="Mumbai, India",
    )
    res = onboard_user(req, db)
    user_id = res["user"]["id"]
    profile_id = res["profile"]["id"]
    assert res["balance"] == 1
    assert res["chart_facts"]["lagna_sign"] == "Virgo"

    # 2. Check balance endpoint
    bal_res = get_user_balance(user_id, db)
    assert bal_res["balance"] == 1
    assert len(bal_res["ledger"]) == 1
    assert bal_res["ledger"][0]["entry_type"] == "signup_grant"

    # 3. Retrieve computed chart endpoint
    chart_facts = get_profile_chart(profile_id, db)
    assert chart_facts["lagna_sign"] == "Virgo"
    assert len(chart_facts["facts"]) == 21

    # 4. Ask first question (spends 1 credit)
    q_req = AskQuestionRequest(
        user_id=user_id,
        birth_profile_id=profile_id,
        question_text="What does 2027 look like for my career?",
        idempotency_key="q_endpoint_test_1",
    )
    q_res = ask_question(q_req, db)
    assert q_res["status"] == "pending"
    assert q_res["remaining_balance"] == 0

    # 5. Attempt second question with 0 balance -> raises HTTP 402
    q2_req = AskQuestionRequest(
        user_id=user_id,
        birth_profile_id=profile_id,
        question_text="Will I move abroad?",
        idempotency_key="q_endpoint_test_2",
    )
    with pytest.raises(HTTPException) as exc_info:
        ask_question(q2_req, db)
    assert exc_info.value.status_code == 402

    # 6. Top up 5 credits (no real payments)
    topup_req = TopupRequest(count=5, idempotency_key="topup_flow_1")
    topup_res = topup_user_credits(user_id, topup_req, db)
    assert topup_res["balance"] == 5

    # 7. Ask second question now succeeds
    q2_ok_res = ask_question(q2_req, db)
    assert q2_ok_res["status"] == "pending"
    assert q2_ok_res["remaining_balance"] == 4

    # 8. Check user history endpoint
    history_res = get_user_history(user_id, db)
    assert len(history_res["history"]) == 2
    history_questions = [h["question_text"] for h in history_res["history"]]
    assert "Will I move abroad?" in history_questions
    assert "What does 2027 look like for my career?" in history_questions

    # 9. Metrics endpoint computes second question retention rate
    metrics = get_metrics(db)
    assert metrics["total_users"] == 1
    assert metrics["users_asked_at_least_one"] == 1
    assert metrics["users_asked_second_question"] == 1
    assert metrics["second_question_retention_rate_pct"] == 100.0
    assert metrics["total_questions_asked"] == 2
    assert metrics["total_topups"] == 1

    # 10. Rewards: Get initial streak state
    rewards = get_rewards_state(user_id, db)
    assert rewards["can_claim_today"] is True
    assert rewards["streak_count"] == 1
    assert rewards["referral_code"] is not None

    # 11. Claim streak reward -> increases balance
    initial_bal = get_user_balance(user_id, db)["balance"]
    claim_res = handle_claim_streak(user_id, db)
    assert claim_res["success"] is True
    new_bal = get_user_balance(user_id, db)["balance"]
    assert new_bal > initial_bal

    # 12. Claim mantra jaap reward
    mantra_res = handle_claim_mantra(user_id, ClaimMantraRequest(planet="Mars"), db)
    assert mantra_res["success"] is True
    assert get_user_balance(user_id, db)["balance"] == new_bal + 1

    # 13. Redeem referral code
    ref_res = handle_redeem_referral(user_id, RedeemReferralRequest(code="FRIEND99"), db)
    assert ref_res["success"] is True
    assert get_user_balance(user_id, db)["balance"] == new_bal + 1 + 5
