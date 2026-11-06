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
    google_id = Column(String(100), nullable=True, unique=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    auth_provider = Column(String(50), default="google")
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
    event_name = Column(String(64), nullable=False, index=True)  # e.g. "answer_viewed", "card_viewed", "share_clicked"
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_events_name_created", "event_name", "created_at"),
    )


class PublicFigure(Base):
    """Notable public figure with verified birth time and Rodden rating A or AA."""
    __tablename__ = "public_figures"

    id = Column(String(64), primary_key=True)  # e.g. "dilip-kumar", "albert-einstein"
    display_name = Column(String(128), nullable=False)
    field = Column(String(64), nullable=False)  # "actor", "cricketer", "scientist", "entrepreneur"
    birth_date = Column(Date, nullable=False)
    birth_time = Column(String(10), nullable=False)  # "HH:MM"
    birth_place = Column(String(128), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    timezone = Column(String(64), nullable=False)
    rodden_rating = Column(String(8), nullable=False)  # "AA" or "A"
    source_url = Column(String(512), nullable=False)
    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class FigureEvent(Base):
    """Career, creative, or achievement milestone of a public figure."""
    __tablename__ = "figure_events"

    id = Column(String(64), primary_key=True)
    figure_id = Column(String(64), ForeignKey("public_figures.id", ondelete="CASCADE"), nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    title = Column(String(512), nullable=False)  # One factual line in our own words, no quotes
    category = Column(String(64), nullable=False)  # "career", "creative", "achievement"
    source_url = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class EventDasha(Base):
    """Cached Vimshottari dasha lords for a figure's milestone event."""
    __tablename__ = "event_dasha"

    id = Column(String(64), primary_key=True)
    event_id = Column(String(64), ForeignKey("figure_events.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    figure_id = Column(String(64), nullable=False, index=True)
    mahadasha_lord = Column(String(32), nullable=False, index=True)
    antardasha_lord = Column(String(32), nullable=False)
    pratyantar_lord = Column(String(32), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    calculated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ShareSnapshot(Base):
    """Card share snapshot stored under a random 128-bit token with 90-day expiry."""
    __tablename__ = "share_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), unique=True, index=True, nullable=False)  # 128-bit hex token
    user_id = Column(String(36), nullable=True, index=True)
    headline = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    figure_name = Column(String(128), nullable=False)
    figure_field = Column(String(64), nullable=False)
    lord = Column(String(32), nullable=False)
    theme = Column(String(64), nullable=False)
    first_name = Column(String(64), nullable=True)  # Omitted by default for privacy
    source_url = Column(String(512), nullable=True)
    is_approximate = Column(Boolean, default=False, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    image_path = Column(String(512), nullable=True)
    story_image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class Experiment(Base):
    """A/B experiment assignment for users (e.g. control vs treatment for Past Check)."""
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), unique=True, index=True, nullable=False)
    arm = Column(String(16), nullable=False)  # "control" or "treatment"
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PastCheckSet(Base):
    """Past Check set tied to a user and their chart hash."""
    __tablename__ = "past_check_sets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), index=True, nullable=False)
    chart_hash = Column(String(64), index=True, nullable=False)
    has_decoy = Column(Boolean, default=False, nullable=False)
    is_skipped = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "chart_hash", name="uq_user_chart_hash"),
    )


class PastCheckItem(Base):
    """Individual statement item within a Past Check set."""
    __tablename__ = "past_check_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    set_id = Column(String(36), ForeignKey("past_check_sets.id", ondelete="CASCADE"), index=True, nullable=False)
    fact_id = Column(String(64), nullable=False)
    event_date = Column(Date, nullable=False)
    theme = Column(String(32), nullable=False)  # "relationships", "career", "money", "home", "learning"
    text_en = Column(String(512), nullable=False)
    text_hi = Column(String(512), nullable=False)
    is_decoy = Column(Boolean, default=False, nullable=False)
    answer = Column(String(16), nullable=True)  # "yes", "not_really", "cant_recall"
    answered_at = Column(DateTime(timezone=True), nullable=True)


class MuhurtaPlan(Base):
    """Auspicious Muhurta Plan requested by user with personalized Vedic rankings."""
    __tablename__ = "muhurta_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    birth_profile_id = Column(String(36), ForeignKey("birth_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    category = Column(String(64), nullable=False)
    override = Column(String(64), nullable=True)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone_str = Column(String(64), nullable=False)
    target_start_date = Column(Date, nullable=False)
    target_end_date = Column(Date, nullable=False)
    time_preference = Column(String(32), default="any", nullable=False)
    slots_json = Column(JSON, nullable=False)
    advisory_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class MuhurtaNotification(Base):
    """Proactive WhatsApp/Telegram/Push alerts scheduled for upcoming Muhurta windows."""
    __tablename__ = "muhurta_notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    muhurta_plan_id = Column(String(36), ForeignKey("muhurta_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(32), default="push", nullable=False)  # "push", "whatsapp", "telegram"
    trigger_time = Column(DateTime(timezone=True), nullable=False, index=True)
    reminder_type = Column(String(16), nullable=False)  # "24h", "1h"
    status = Column(String(32), default="pending", nullable=False)  # "pending", "sent", "failed"
    payload = Column(JSON, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

