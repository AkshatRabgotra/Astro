"""Atomic and idempotent balance ledger operations."""

from collections import defaultdict
import threading
from typing import Dict, Optional
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from backend.models import BalanceLedger, Question, User

_lock_registry_mutex = threading.Lock()
_user_locks: Dict[str, threading.Lock] = {}


def _get_user_lock(user_id: str) -> threading.Lock:
    """Retrieve or create an in-process serialization lock for a user."""
    with _lock_registry_mutex:
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        return _user_locks[user_id]


class InsufficientBalanceError(Exception):
    """Raised when an operation requires more question balance than available."""
    pass


class LedgerError(Exception):
    """General ledger exception."""
    pass


def get_balance(db: Session, user_id: str) -> int:
    """Compute current user balance as the sum of all ledger entries."""
    result = db.query(func.coalesce(func.sum(BalanceLedger.amount), 0)).filter(
        BalanceLedger.user_id == user_id
    ).scalar()
    return int(result or 0)


def grant_signup_credit(db: Session, user_id: str) -> Optional[BalanceLedger]:
    """
    Grant 1 free question credit upon user signup.
    Idempotent by key 'signup_{user_id}'.
    """
    idempotency_key = f"signup_{user_id}"
    existing = db.query(BalanceLedger).filter(
        BalanceLedger.idempotency_key == idempotency_key
    ).first()
    if existing:
        return existing

    entry = BalanceLedger(
        user_id=user_id,
        amount=1,
        entry_type="signup_grant",
        idempotency_key=idempotency_key,
        reference_id=user_id,
        description="Initial free question on signup",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def topup_credits(
    db: Session,
    user_id: str,
    count: int,
    idempotency_key: str,
    description: Optional[str] = None
) -> int:
    """
    Top up user balance by N question credits (no real payments).
    Idempotent by idempotency_key.
    Returns new total balance.
    """
    if count <= 0:
        raise ValueError("Top-up credit count must be greater than 0")

    existing = db.query(BalanceLedger).filter(
        BalanceLedger.idempotency_key == idempotency_key
    ).first()
    if existing:
        return get_balance(db, user_id)

    entry = BalanceLedger(
        user_id=user_id,
        amount=count,
        entry_type="topup",
        idempotency_key=idempotency_key,
        reference_id=idempotency_key,
        description=description or f"Added {count} questions (no payment)",
    )
    db.add(entry)
    db.commit()
    return get_balance(db, user_id)


def spend_question_credit(
    db: Session,
    user_id: str,
    question_id: str,
    idempotency_key: str
) -> bool:
    """
    Atomically and idempotently spend 1 question credit from user's balance.
    Locks the user row when supported (Postgres) and serializes in-process requests.
    Raises InsufficientBalanceError if balance <= 0.
    """
    with _get_user_lock(user_id):
        # Ensure fresh transaction snapshot
        db.expire_all()
        # 1. Check idempotency first: if already spent for this key, treat as successful idempotent call
        existing = db.query(BalanceLedger).filter(
            BalanceLedger.idempotency_key == idempotency_key
        ).first()
        if existing:
            return True

        # 2. Lock user record to serialize concurrent spends for this user (PostgreSQL)
        try:
            bind_name = db.bind.dialect.name if db.bind else ""
            if bind_name == "postgresql":
                db.query(User).filter(User.id == user_id).with_for_update().first()
            elif bind_name == "sqlite":
                # Ensure write transaction
                db.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            pass

        # 3. Check current balance
        current_bal = get_balance(db, user_id)
        if current_bal < 1:
            raise InsufficientBalanceError(
                f"Insufficient question balance. Current balance is {current_bal}. Please top up."
            )

        # 4. Append spend entry
        spend_entry = BalanceLedger(
            user_id=user_id,
            amount=-1,
            entry_type="question_spend",
            idempotency_key=idempotency_key,
            reference_id=question_id,
            description=f"Spent 1 question credit for question {question_id}",
        )
        db.add(spend_entry)
        db.commit()
        return True


def refund_question_credit(
    db: Session,
    user_id: str,
    question_id: str,
    reason: str = "Answer generation failure"
) -> bool:
    """
    Automatically refund 1 question credit if generation fails after all provider fallbacks.
    Idempotent by key 'refund_{question_id}'.
    """
    refund_key = f"refund_{question_id}"
    existing_refund = db.query(BalanceLedger).filter(
        BalanceLedger.idempotency_key == refund_key
    ).first()
    if existing_refund:
        return True

    # Check that a spend was actually recorded for this question
    spend_entry = db.query(BalanceLedger).filter(
        BalanceLedger.reference_id == question_id,
        BalanceLedger.entry_type == "question_spend",
    ).first()
    if not spend_entry:
        # Nothing was spent for this question, no refund needed
        return False

    refund_entry = BalanceLedger(
        user_id=user_id,
        amount=1,
        entry_type="refund",
        idempotency_key=refund_key,
        reference_id=question_id,
        description=f"Refund: {reason}",
    )
    db.add(refund_entry)

    # Update question status to 'refunded'
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        question.status = "refunded"

    db.commit()
    return True
