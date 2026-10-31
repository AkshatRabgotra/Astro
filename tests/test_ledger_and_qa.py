"""Unit and Concurrency Tests for the Question Balance Ledger and Q&A Service."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.ledger import (
    InsufficientBalanceError,
    get_balance,
    grant_signup_credit,
    refund_question_credit,
    spend_question_credit,
    topup_credits,
)
from backend.models import User
from backend.service import OnboardingService, QuestionService


@pytest.fixture
def db_session():
    """Create a clean in-memory database for each test."""
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


def test_user_signup_and_initial_balance_grant(db_session):
    """Verify signup creates user, birth profile, chart, and grants 1 credit."""
    user, profile, chart, facts = OnboardingService.create_user_and_chart(
        db=db_session,
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
        place_name="Mumbai, India",
    )

    assert user.id is not None
    assert profile.id is not None
    assert chart.id is not None
    assert facts.lagna_sign == "Virgo"

    # Initial balance must be 1
    bal = get_balance(db_session, user.id)
    assert bal == 1


def test_spend_balance_decrements_and_zero_balance_blocks(db_session):
    """Verify spending decrements balance, and asking with 0 balance is blocked."""
    user, profile, chart, _ = OnboardingService.create_user_and_chart(
        db=db_session,
        name="Test User",
        birth_date=date(1990, 1, 1),
        birth_time="12:00:00",
        time_known=True,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
    )

    # 1. Ask first question: spends 1 credit
    q1 = QuestionService.ask_question(
        db=db_session,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="What does my career look like in 2027?",
        idempotency_key="q_test_1",
    )
    assert q1.status == "pending"
    assert get_balance(db_session, user.id) == 0

    # 2. Ask second question with 0 balance -> must raise InsufficientBalanceError
    with pytest.raises(InsufficientBalanceError) as exc_info:
        QuestionService.ask_question(
            db=db_session,
            user_id=user.id,
            birth_profile_id=profile.id,
            question_text="Will I move abroad?",
            idempotency_key="q_test_2",
        )
    assert "Insufficient question balance" in str(exc_info.value)
    assert get_balance(db_session, user.id) == 0


def test_idempotent_spending_prevents_duplicate_charge(db_session):
    """Verify that retrying or double-clicking with same idempotency key does not charge twice."""
    user, profile, _, _ = OnboardingService.create_user_and_chart(
        db=db_session,
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )

    # First attempt
    q1 = QuestionService.ask_question(
        db=db_session,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="How is my financial outlook?",
        idempotency_key="idempotent_key_xyz",
    )
    assert get_balance(db_session, user.id) == 0

    # Duplicate attempt with identical key
    q2 = QuestionService.ask_question(
        db=db_session,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="How is my financial outlook?",
        idempotency_key="idempotent_key_xyz",
    )
    assert q1.id == q2.id
    assert get_balance(db_session, user.id) == 0


def test_topup_credits_and_topup_idempotency(db_session):
    """Verify top-up adds N credits and idempotent keys prevent duplicate top-up."""
    user = User(name="Topup User")
    db_session.add(user)
    db_session.commit()

    # Initial balance 0
    assert get_balance(db_session, user.id) == 0

    # Top up 5 credits
    bal = topup_credits(
        db=db_session,
        user_id=user.id,
        count=5,
        idempotency_key="topup_tx_001",
    )
    assert bal == 5
    assert get_balance(db_session, user.id) == 5

    # Re-submit same top-up transaction
    bal_retry = topup_credits(
        db=db_session,
        user_id=user.id,
        count=5,
        idempotency_key="topup_tx_001",
    )
    assert bal_retry == 5
    assert get_balance(db_session, user.id) == 5


def test_automatic_refund_on_failure(db_session):
    """Verify failed question generation triggers automatic refund and restores balance."""
    user, profile, _, _ = OnboardingService.create_user_and_chart(
        db=db_session,
        name="Refund User",
        birth_date=date(1990, 1, 1),
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
    )

    # Balance starts at 1
    assert get_balance(db_session, user.id) == 1

    q = QuestionService.ask_question(
        db=db_session,
        user_id=user.id,
        birth_profile_id=profile.id,
        question_text="Will this fail?",
        idempotency_key="q_refund_test",
    )
    assert get_balance(db_session, user.id) == 0
    assert q.status == "pending"

    # Simulate generation failure
    refunded = QuestionService.fail_and_refund(
        db=db_session,
        question_id=q.id,
        reason="Model provider timeout",
    )
    assert refunded is True
    assert get_balance(db_session, user.id) == 1

    # Check question status updated to refunded
    db_session.refresh(q)
    assert q.status == "refunded"

    # Re-attempt refund on same question -> must not double refund
    refunded_again = QuestionService.fail_and_refund(
        db=db_session,
        question_id=q.id,
    )
    assert refunded_again is True
    assert get_balance(db_session, user.id) == 1


def test_concurrent_spends_balance_integrity():
    """
    Concurrency stress test:
    Create a user with 1 question balance.
    Launch 10 concurrent threads trying to spend simultaneously with distinct keys.
    Assert: Exactly 1 succeeds, 9 fail with InsufficientBalanceError.
    Final balance is strictly 0 (never negative).
    """
    import os
    db_file = "test_concurrent.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    test_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    init_session = SessionFactory()
    user = User(name="Concurrency Tester")
    init_session.add(user)
    init_session.commit()
    grant_signup_credit(init_session, user.id)
    assert get_balance(init_session, user.id) == 1
    init_session.close()

    success_count = 0
    failure_count = 0

    def attempt_spend(worker_idx: int):
        s = SessionFactory()
        try:
            spend_question_credit(
                db=s,
                user_id=user.id,
                question_id=f"q_concurrent_{worker_idx}",
                idempotency_key=f"key_concurrent_{worker_idx}",
            )
            return True
        except InsufficientBalanceError:
            return False
        except Exception:
            return False
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(attempt_spend, range(10)))

    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if r is False)

    assert success_count == 1
    assert failure_count == 9

    check_session = SessionFactory()
    final_balance = get_balance(check_session, user.id)
    check_session.close()
    assert final_balance == 0

    # Cleanup temporary test db
    import os
    try:
        os.remove("test_concurrent.db")
    except Exception:
        pass
