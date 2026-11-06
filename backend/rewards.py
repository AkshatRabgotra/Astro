"""Rewards, Daily Streak, Referral, and Mantra Jaap engine for Melooha."""

from datetime import date, datetime, timedelta, timezone
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ledger import get_balance
from backend.models import BalanceLedger, Event, User


STREAK_REWARDS = [
    {"day": 1, "reward_coins": 5, "reward_questions": 1},
    {"day": 2, "reward_coins": 7, "reward_questions": 1},
    {"day": 3, "reward_coins": 9, "reward_questions": 1},
    {"day": 4, "reward_coins": 11, "reward_questions": 1},
    {"day": 5, "reward_coins": 13, "reward_questions": 2},
    {"day": 6, "reward_coins": 15, "reward_questions": 2},
    {"day": 7, "reward_coins": 17, "reward_questions": 3},
]

PLANET_MANTRAS = {
    "Mars": {
        "title": "Mars Mantra",
        "sanskrit": "ॐ अं अंगारकाय नमः",
        "transliteration": "Om Am Angarakaya Namah",
        "significance": "Pacifies Mangal, ignites courage, eliminates lethargy, and shields against conflict.",
        "planet": "Mars",
        "reward_coins": 1,
        "reward_questions": 1,
    },
    "Sun": {
        "title": "Surya Gayatri Mantra",
        "sanskrit": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "transliteration": "Om Hram Hreem Hroum Sah Suryaya Namah",
        "significance": "Enhances soul vitality, leadership authority, and clear health energy.",
        "planet": "Sun",
        "reward_coins": 1,
        "reward_questions": 1,
    },
    "Moon": {
        "title": "Chandra Shanti Mantra",
        "sanskrit": "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः",
        "transliteration": "Om Shram Shreem Shroum Sah Chandraya Namah",
        "significance": "Brings mental peace, soothes anxiety, and awakens emotional intuition.",
        "planet": "Moon",
        "reward_coins": 1,
        "reward_questions": 1,
    },
    "Jupiter": {
        "title": "Brihaspati Mantra",
        "sanskrit": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "transliteration": "Om Gram Greem Graum Sah Gurave Namah",
        "significance": "Expands wisdom, educational luck, financial abundance, and moral clarity.",
        "planet": "Jupiter",
        "reward_coins": 1,
        "reward_questions": 1,
    },
    "Venus": {
        "title": "Shukra Stotram Mantra",
        "sanskrit": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "transliteration": "Om Dram Dreem Droum Sah Shukraya Namah",
        "significance": "Nurtures romantic harmony, artistic grace, and refined prosperity.",
        "planet": "Venus",
        "reward_coins": 1,
        "reward_questions": 1,
    },
    "Saturn": {
        "title": "Shani Shanti Mantra",
        "sanskrit": "ॐ शं शनैश्चराय नमः",
        "transliteration": "Om Sham Shanaishcharaya Namah",
        "significance": "Neutralizes karmic delays, instills discipline, and protects during Sade Sati.",
        "planet": "Saturn",
        "reward_coins": 1,
        "reward_questions": 1,
    },
}


def generate_referral_code(user_id: str) -> str:
    """Generate deterministic, memorable 6-character referral code (e.g. 9X47WP)."""
    digest = hashlib.md5(user_id.encode("utf-8")).hexdigest().upper()
    return f"{digest[0:2]}{digest[4:6]}{digest[8:10]}"


def get_user_reward_state(db: Session, user_id: str, profile_id: Optional[str] = None) -> Dict[str, Any]:
    """Calculate the user's current streak, claimable state, and mantras, segregated per profile if provided."""
    today = datetime.now(timezone.utc).date()
    ref_code = generate_referral_code(user_id)

    # Find streak claim events, filtering by profile_id if available
    query = (
        db.query(Event)
        .filter(Event.user_id == user_id, Event.event_name == "streak_claimed")
        .order_by(Event.created_at.desc())
    )
    all_events = query.all()

    # Filter to this specific profile or legacy global events
    if profile_id:
        streak_events = [
            e for e in all_events
            if (e.payload or {}).get("profile_id") == profile_id
        ]
    else:
        streak_events = all_events

    last_claim_date = None
    streak_count = 1
    streak_was_broken = False

    if streak_events:
        last_evt = streak_events[0]
        # In SQLite/Postgres normalize date
        created_dt = last_evt.created_at
        if isinstance(created_dt, str):
            try:
                last_claim_date = datetime.fromisoformat(created_dt.replace("Z", "+00:00")).date()
            except Exception:
                last_claim_date = today
        elif hasattr(created_dt, "date"):
            last_claim_date = created_dt.date()
        else:
            last_claim_date = today

        payload = last_evt.payload or {}
        prev_day = payload.get("day", 1)

        diff = (today - last_claim_date).days
        if diff == 0:
            # Already claimed today
            can_claim_today = False
            streak_count = prev_day
        elif diff == 1:
            # Active strictly consecutive streak
            streak_count = (prev_day % 7) + 1
            can_claim_today = True
        else:
            # Broken streak (e.g. came day 1, skipped day 2, came on day 3)
            # Must restart at Day 1
            streak_count = 1
            can_claim_today = True
            streak_was_broken = True
    else:
        can_claim_today = True
        streak_count = 1

    # Current streak rewards tier
    curr_tier = STREAK_REWARDS[min(streak_count - 1, 6)]
    next_tier = STREAK_REWARDS[min(streak_count, 6)]

    # Mantra claims count today
    mantra_claims_today = (
        db.query(Event)
        .filter(
            Event.user_id == user_id,
            Event.event_name == "mantra_claimed",
            Event.created_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
        )
        .count()
    )

    # Balance and wallet representation
    balance = get_balance(db, user_id)
    wallet_coins = 5 + (balance * 5)  # Representational wallet ₹ coin value

    return {
        "user_id": user_id,
        "profile_id": profile_id,
        "referral_code": ref_code,
        "streak_count": streak_count,
        "can_claim_today": can_claim_today,
        "streak_was_broken": streak_was_broken,
        "today_reward_coins": curr_tier["reward_coins"],
        "today_reward_questions": curr_tier["reward_questions"],
        "next_reward_coins": next_tier["reward_coins"],
        "streak_days": STREAK_REWARDS,
        "mantra_claims_today": mantra_claims_today,
        "mantras": list(PLANET_MANTRAS.values()),
        "wallet_coins": wallet_coins,
        "question_balance": balance,
    }


def claim_streak_reward(db: Session, user_id: str, profile_id: Optional[str] = None) -> Dict[str, Any]:
    """Claim today's streak reward idempotently, adding question credits to balance."""
    today = datetime.now(timezone.utc).date()
    state = get_user_reward_state(db, user_id, profile_id=profile_id)

    if not state["can_claim_today"]:
        return {
            "success": False,
            "message": "Today's streak reward has already been claimed! Return tomorrow to keep your streak alive.",
            "state": state,
        }

    day_num = state["streak_count"]
    coins = state["today_reward_coins"]
    questions = state["today_reward_questions"]
    p_key = profile_id or "default"
    idempotency_key = f"streak_{user_id}_{p_key}_{today.isoformat()}"

    # Verify idempotency in ledger
    existing = (
        db.query(BalanceLedger)
        .filter(BalanceLedger.idempotency_key == idempotency_key)
        .first()
    )
    if not existing:
        ledger_entry = BalanceLedger(
            user_id=user_id,
            amount=questions,
            entry_type="reward_streak",
            idempotency_key=idempotency_key,
            reference_id=f"day_{day_num}_{p_key}",
            description=f"Day {day_num} Streak Reward (+{coins} coins / +{questions} free questions)",
        )
        db.add(ledger_entry)

        # Log event with profile_id
        evt = Event(
            user_id=user_id,
            event_name="streak_claimed",
            payload={
                "profile_id": profile_id,
                "day": day_num,
                "coins": coins,
                "questions": questions,
                "date": today.isoformat(),
            },
        )
        db.add(evt)
        db.commit()

    updated_state = get_user_reward_state(db, user_id, profile_id=profile_id)
    return {
        "success": True,
        "message": f"Claimed ₹{coins} reward! Added +{questions} question credit to your balance.",
        "state": updated_state,
    }


def claim_mantra_reward(db: Session, user_id: str, planet: str) -> Dict[str, Any]:
    """Claim +1 question credit for completing a remedial mantra jaap session."""
    today = datetime.now(timezone.utc).date()
    mantra_info = PLANET_MANTRAS.get(planet, PLANET_MANTRAS["Mars"])

    idempotency_key = f"mantra_{user_id}_{planet}_{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"

    ledger_entry = BalanceLedger(
        user_id=user_id,
        amount=1,
        entry_type="reward_mantra",
        idempotency_key=idempotency_key,
        reference_id=planet,
        description=f"Remedial Mantra Jaap: {mantra_info['title']} (+1 question credit)",
    )
    db.add(ledger_entry)

    evt = Event(
        user_id=user_id,
        event_name="mantra_claimed",
        payload={"planet": planet, "coins": 1, "questions": 1, "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db.add(evt)
    db.commit()

    updated_state = get_user_reward_state(db, user_id)
    return {
        "success": True,
        "message": f"Chant verified! Added +1 question credit to your account.",
        "state": updated_state,
    }


def redeem_referral_code(db: Session, user_id: str, code: str) -> Dict[str, Any]:
    """Redeem a friend's referral code to receive +5 free questions (+₹50 value)."""
    cleaned_code = code.strip().upper()
    own_code = generate_referral_code(user_id)

    if cleaned_code == own_code:
        return {"success": False, "message": "You cannot redeem your own referral code."}

    idempotency_key = f"referral_{user_id}"
    existing = (
        db.query(BalanceLedger)
        .filter(BalanceLedger.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        return {"success": False, "message": "You have already redeemed a referral code."}

    # Award +5 questions to the redeeming user
    ledger_entry = BalanceLedger(
        user_id=user_id,
        amount=5,
        entry_type="reward_referral",
        idempotency_key=idempotency_key,
        reference_id=cleaned_code,
        description=f"Redeemed friend referral code {cleaned_code} (+₹50 / +5 free questions)",
    )
    db.add(ledger_entry)

    evt = Event(
        user_id=user_id,
        event_name="referral_redeemed",
        payload={"code": cleaned_code, "questions": 5},
    )
    db.add(evt)
    db.commit()

    updated_state = get_user_reward_state(db, user_id)
    return {
        "success": True,
        "message": f"Referral code verified! Added +5 free questions (₹50 value) to your wallet.",
        "state": updated_state,
    }
