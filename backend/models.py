"""Database ORM models for Users, Charts, Ledger, Q&A, and Events."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from backend.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class BirthProfile(Base):
    __tablename__ = "birth_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(String(10), nullable=True)  # HH:MM or HH:MM:SS
    time_known = Column(Boolean, default=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone_str = Column(String(64), nullable=False)
    place_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Chart(Base):
    __tablename__ = "charts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    birth_profile_id = Column(String(36), ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    ayanamsa = Column(String(32), default="Lahiri", nullable=False)
    facts_json = Column(JSON, nullable=False)  # Serialized ChartFacts
    calculated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class BalanceLedger(Base):
    """
    Append-only ledger for user question balance.
    Sum(amount) = current balance.
    Positive values: signup grant (+1), top-up (+N), failure refund (+1).
    Negative values: question spent (-1).
    """
    __tablename__ = "balance_ledger"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    entry_type = Column(String(32), nullable=False)  # "signup_grant", "topup", "question_spend", "refund"
    idempotency_key = Column(String(128), nullable=True, unique=True, index=True)
    reference_id = Column(String(128), nullable=True, index=True)  # question_id or topup_id
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_ledger_user_created", "user_id", "created_at"),
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    birth_profile_id = Column(String(36), ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    status = Column(String(32), default="pending", nullable=False)  # "pending", "completed", "failed", "refunded"
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    answer_text = Column(Text, nullable=False)
    cited_fact_ids = Column(JSON, nullable=False)  # List of fact IDs like ["F01", "F09"]
    provider = Column(String(32), nullable=False)  # "gemini", "groq", "template_fallback"
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Event(Base):
    """Event table for tracking product interactions and metric computation."""
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    event_name = Column(String(64), nullable=False, index=True)  # e.g. "answer_viewed", "evidence_opened", "second_question_asked", "topup_clicked"
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_events_name_created", "event_name", "created_at"),
    )
