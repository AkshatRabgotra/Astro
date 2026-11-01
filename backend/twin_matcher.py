"""Dasha Twin matching engine.

Pure deterministic code matching the user's active dasha lord
with notable public figures' verified milestones under the same lord.
"""

from datetime import date, datetime, timedelta
import hashlib
import random
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models import BirthProfile, Event, EventDasha, FigureEvent, PublicFigure
from chart.engine import calculate_chart_facts
from chart.models import BirthInput
from chart.dasha import calculate_vimshottari_periods


def get_user_current_dasha_lord(
    profile: BirthProfile,
    target_dt: Optional[datetime] = None,
    level: str = "pratyantar",
) -> Dict[str, Any]:
    """
    Compute user's active dasha lord at the specified level (default: pratyantar).
    If birth time is unknown, forces level="mahadasha" and is_approximate=True.
    """
    if target_dt is None:
        target_dt = datetime.now()

    is_approximate = not bool(profile.time_known)
    effective_level = "mahadasha" if is_approximate else level.lower()
    birth_time = profile.birth_time if (profile.time_known and profile.birth_time) else "12:00"

    # Calculate chart facts to extract Moon's sidereal longitude
    chart = calculate_chart_facts(
        BirthInput(
            name=profile.name,
            birth_date=profile.birth_date.strftime("%Y-%m-%d") if isinstance(profile.birth_date, (date, datetime)) else str(profile.birth_date),
            birth_time=birth_time,
            latitude=profile.latitude,
            longitude=profile.longitude,
            timezone_str=profile.timezone_str or "Asia/Kolkata",
        )
    )
    moon = next(p for p in chart.planets if p.planet == "Moon")

    birth_dt = datetime.strptime(
        f"{profile.birth_date} {birth_time}",
        "%Y-%m-%d %H:%M" if len(birth_time.split(":")) == 2 else "%Y-%m-%d %H:%M:%S"
    )

    curr_dasha, _, _ = calculate_vimshottari_periods(
        moon_longitude=moon.longitude,
        birth_dt=birth_dt,
        target_dt=target_dt,
        is_approximate=is_approximate,
    )

    if effective_level == "pratyantar":
        active_lord = curr_dasha.pratyantardasha_lord or curr_dasha.antardasha_lord
    elif effective_level == "antardasha":
        active_lord = curr_dasha.antardasha_lord
    else:
        active_lord = curr_dasha.mahadasha_lord

    return {
        "active_lord": active_lord,
        "mahadasha_lord": curr_dasha.mahadasha_lord,
        "antardasha_lord": curr_dasha.antardasha_lord,
        "pratyantar_lord": curr_dasha.pratyantardasha_lord,
        "effective_level": effective_level,
        "is_approximate": is_approximate,
        "moon_longitude": moon.longitude,
        "start_date": curr_dasha.start_date,
        "end_date": curr_dasha.end_date,
    }


def find_dasha_twin(
    db: Session,
    profile: BirthProfile,
    target_date: Optional[date] = None,
    level: str = "pratyantar",
    exclude_figure_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Match user's current dasha lord with a verified public figure's career milestone.
    
    Deterministic:
    - Same user_id and target_date returns identical card.
    - Excludes milestones shown in the last 14 days where possible.
    - If no match found, returns generic phase card.
    """
    if target_date is None:
        target_date = date.today()

    target_dt = datetime.combine(target_date, datetime.min.time())
    user_dasha = get_user_current_dasha_lord(profile, target_dt, level)
    user_lord = user_dasha["active_lord"]
    effective_level = user_dasha["effective_level"]
    is_approximate = user_dasha["is_approximate"]

    # Query all events whose figure Mahadasha lord equals user_lord
    query = (
        db.query(FigureEvent, PublicFigure, EventDasha)
        .join(PublicFigure, FigureEvent.figure_id == PublicFigure.id)
        .join(EventDasha, FigureEvent.id == EventDasha.event_id)
        .filter(PublicFigure.verified == True)
        .filter(PublicFigure.rodden_rating.in_(["AA", "A"]))
        .filter(EventDasha.mahadasha_lord == user_lord)
    )

    if exclude_figure_ids:
        query = query.filter(~PublicFigure.id.in_(exclude_figure_ids))

    all_matches = query.all()

    if not all_matches:
        # Fallback to generic phase card with no person
        return {
            "match_type": "generic_phase",
            "user_lord": user_lord,
            "user_level": effective_level,
            "figure_level": "Mahadasha",
            "is_approximate": is_approximate,
            "headline": f"Your {user_lord} {effective_level.capitalize()} Phase",
            "body": (
                f"You are currently in your {user_lord} {effective_level.capitalize()} Dasha period. "
                f"In Vedic astrology, this phase calls for focused energy aligned with {user_lord}'s natural significations."
            ),
            "figure": None,
            "event": None,
            "fact_ids": ["F_DASHA_USER"],
            "disclaimer": "For reflection and fun, not prediction.",
        }

    # Retrieve events shown to this user in the last 14 days
    user_id_str = profile.user_id or profile.id
    fourteen_days_ago = datetime.now() - timedelta(days=14)
    recent_events = (
        db.query(Event)
        .filter(Event.user_id == user_id_str)
        .filter(Event.event_name.in_(["card_viewed", "card_refresh"]))
        .filter(Event.created_at >= fourteen_days_ago)
        .all()
    )
    recent_event_ids = set()
    for ev in recent_events:
        if ev.payload and isinstance(ev.payload, dict) and "event_id" in ev.payload:
            recent_event_ids.add(ev.payload["event_id"])

    # Prefer candidates not recently shown
    fresh_candidates = [m for m in all_matches if m[0].id not in recent_event_ids]
    candidate_pool = fresh_candidates if fresh_candidates else all_matches

    # Rank by quality (AA before A) and seed deterministically with (user_id, target_date)
    # Sort candidates by (rodden_rating AA>A, figure_id, event_id) for stability
    candidate_pool.sort(
        key=lambda m: (0 if m[1].rodden_rating == "AA" else 1, m[1].field, m[1].id, m[0].id)
    )

    seed_key = f"{user_id_str}_{target_date.strftime('%Y-%m-%d')}_{effective_level}"
    seed_hash = int(hashlib.sha256(seed_key.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed_hash)

    chosen_event, chosen_figure, chosen_dasha = rng.choice(candidate_pool)

    return {
        "match_type": "twin_match",
        "user_lord": user_lord,
        "user_level": effective_level,
        "figure_level": "Mahadasha",
        "is_approximate": is_approximate,
        "figure": {
            "id": chosen_figure.id,
            "display_name": chosen_figure.display_name,
            "field": chosen_figure.field.capitalize(),
            "rodden_rating": chosen_figure.rodden_rating,
            "source_url": chosen_figure.source_url,
            "monogram": "".join([part[0].upper() for part in chosen_figure.display_name.split()[:2]]),
        },
        "event": {
            "id": chosen_event.id,
            "title": chosen_event.title,
            "event_date": chosen_event.event_date.strftime("%Y-%m-%d"),
            "category": chosen_event.category,
            "source_url": chosen_event.source_url,
            "figure_mahadasha": chosen_dasha.mahadasha_lord,
            "figure_antardasha": chosen_dasha.antardasha_lord,
        },
        "headline_template": f"Your {effective_level.capitalize()}, their Mahadasha",
        "disclaimer": "For reflection and fun, not prediction.",
    }
