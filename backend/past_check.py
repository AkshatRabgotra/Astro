"""Past Check Engine: Trust and Resonance Measurement Before the Paywall.

Follows strict rules:
- Code-only candidate generation from chart (Mahadashas, Antardashas, Transits)
- Window: between 6 months and 8 years ago
- Strict themes: 'relationships', 'career', 'money', 'home', 'learning'
- Strictly forbids: health, death, trauma, legal, pregnancy
- Selects 3 candidates with distinct themes and well-spread dates
- A/B Experiment assignment: control vs treatment
- Decoy injection: ~30% of treatment sets replace 1 item with a decoy where no trigger occurred
- Server-only is_decoy (never exposed to API responses)
- Idempotent answering
"""

from datetime import date, datetime, timedelta, timezone
import hashlib
import random
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models import BirthProfile, Chart, Experiment, PastCheckItem, PastCheckSet
from chart.engine import calculate_chart_facts, SIGNS
from chart.models import BirthInput, ChartFacts
from chart.dasha import calculate_vimshottari_periods


ALLOWED_THEMES = ["relationships", "career", "money", "home", "learning"]
FORBIDDEN_THEMES = ["health", "death", "trauma", "legal", "pregnancy", "illness", "disease"]

THEME_TEMPLATES = {
    "career": {
        "en": "your career, workplace responsibilities, or vocation",
        "hi": "करियर, कार्यस्थल की जिम्मेदारियों या व्यवसाय",
    },
    "relationships": {
        "en": "your close partnerships, key relationships, or social circle",
        "hi": "निकट संबंधों, साझेदारी या मित्र मंडली",
    },
    "money": {
        "en": "your financial stewardship, income flow, or resource allocation",
        "hi": "वित्तीय प्राथमिकताओं, आय के साधन या संसाधनों",
    },
    "home": {
        "en": "your home environment, domestic routines, or living arrangement",
        "hi": "पारिवारिक परिवेश, घरेलू दिनचर्या या आवास",
    },
    "learning": {
        "en": "your intellectual pursuits, specialized learning, or key skill development",
        "hi": "ज्ञानार्जन, बौद्धिक रुचि या किसी नए कौशल",
    },
}

LORD_THEME_MAP = {
    "Sun": "career",
    "Mars": "career",
    "Saturn": "career",
    "Venus": "relationships",
    "Moon": "home",
    "Mercury": "learning",
    "Jupiter": "learning",
    "Rahu": "money",
    "Ketu": "learning",
}


def compute_chart_hash(profile: BirthProfile) -> str:
    """Compute deterministic hash of birth profile inputs."""
    raw = f"{profile.birth_date}_{profile.birth_time}_{profile.latitude:.4f}_{profile.longitude:.4f}_{profile.timezone_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_or_assign_experiment_arm(db: Session, user_id: str) -> str:
    """Stable assignment to control (50%) or treatment (50%)."""
    exp = db.query(Experiment).filter(Experiment.user_id == user_id).first()
    if exp:
        return exp.arm

    # Deterministic 50/50 split based on user_id hash
    hash_val = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:8], 16)
    arm = "treatment" if (hash_val % 2 == 0) else "control"

    exp = Experiment(user_id=user_id, arm=arm)
    db.add(exp)
    db.commit()
    return arm


def build_statement_text(event_date: date, theme: str, lang: str = "en") -> str:
    """Template-based, checkable statement text."""
    mon_yyyy_en = event_date.strftime("%B %Y")
    mon_names_hi = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
    mon_yyyy_hi = f"{mon_names_hi[event_date.month - 1]} {event_date.year}"

    if lang == "hi":
        theme_str = THEME_TEMPLATES.get(theme, {}).get("hi", "जीवन के इस क्षेत्र")
        return f"लगभग {mon_yyyy_hi} के समय, क्या आपके {theme_str} में कोई महत्वपूर्ण बदलाव आया था?"
    
    theme_str = THEME_TEMPLATES.get(theme, {}).get("en", "this area of life")
    return f"Around {mon_yyyy_en}, did something in {theme_str} shift noticeably for you?"


def generate_candidate_events(
    profile: BirthProfile,
    today: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Extract candidate astrological trigger events between 6 months and 8 years ago.
    """
    if today is None:
        today = date.today()

    min_date = today - timedelta(days=365 * 8)
    max_date = today - timedelta(days=180)

    birth_time = profile.birth_time if (profile.time_known and profile.birth_time) else "12:00"
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

    # 1. Antardasha start dates
    candidates = []
    # Probe every ~6 months from birth up to today to collect dasha transitions
    probe = birth_dt
    visited_dasha_keys = set()

    while probe.date() <= today:
        curr, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=probe)
        key = f"{curr.mahadasha_lord}_{curr.antardasha_lord}_{curr.start_date}"
        if key not in visited_dasha_keys:
            visited_dasha_keys.add(key)
            if curr.start_date:
                start_d = datetime.strptime(curr.start_date, "%Y-%m-%d").date()
                if min_date <= start_d <= max_date:
                    theme = LORD_THEME_MAP.get(curr.antardasha_lord, "career")
                    candidates.append({
                        "fact_id": f"FACT_DASHA_{curr.mahadasha_lord.upper()}_{curr.antardasha_lord.upper()}",
                        "event_date": start_d,
                        "theme": theme,
                        "strength": 8.0 if curr.mahadasha_lord == curr.antardasha_lord else 6.5,
                        "description": f"{curr.mahadasha_lord}-{curr.antardasha_lord} Dasha onset",
                    })
        probe += timedelta(days=90)

    # 2. Add Jupiter transit sign ingress events (~12 months per sign)
    # Jupiter transits through houses 2, 5, 7, 9, 10, 11 from Moon create notable shifts
    for year in range(min_date.year, max_date.year + 1):
        for month in [3, 9]:
            approx_date = date(year, month, 15)
            if min_date <= approx_date <= max_date:
                # Cycle themes across years
                theme_idx = (year + month) % len(ALLOWED_THEMES)
                theme = ALLOWED_THEMES[theme_idx]
                candidates.append({
                    "fact_id": f"FACT_TRANSIT_JUPITER_APPROX_{year}_{month}",
                    "event_date": approx_date,
                    "theme": theme,
                    "strength": 5.0,
                    "description": f"Jupiter transit window {year}",
                })

    # Sort candidates by date
    candidates.sort(key=lambda c: c["event_date"])
    return candidates


def select_past_check_statements(
    candidates: List[Dict[str, Any]],
    user_id: str,
    today: Optional[date] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Select 3 candidates with different themes and well-spread dates (>= 9 months apart).
    Injects decoy for ~30% of sets.
    """
    if len(candidates) < 2:
        return [], False

    # Seed RNG deterministically with user_id
    seed_int = int(hashlib.sha256(f"past_check_{user_id}".encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed_int)

    # 30% decoy probability
    has_decoy = (seed_int % 100) < 30

    chosen: List[Dict[str, Any]] = []
    used_themes = set()

    # Prioritize higher strength candidates
    shuffled_candidates = sorted(candidates, key=lambda c: (-c["strength"], c["event_date"]))

    for cand in shuffled_candidates:
        theme = cand["theme"]
        if theme in used_themes:
            continue
        # Ensure dates are spread apart by at least 250 days (~8.5 months)
        if any(abs((cand["event_date"] - c["event_date"]).days) < 250 for c in chosen):
            continue

        chosen.append({
            "fact_id": cand["fact_id"],
            "event_date": cand["event_date"],
            "theme": theme,
            "text_en": build_statement_text(cand["event_date"], theme, "en"),
            "text_hi": build_statement_text(cand["event_date"], theme, "hi"),
            "is_decoy": False,
        })
        used_themes.add(theme)
        if len(chosen) == 3:
            break

    # If we couldn't find 3 well-spread distinct themes, relax spacing
    if len(chosen) < 3:
        for cand in shuffled_candidates:
            if cand["theme"] not in used_themes:
                chosen.append({
                    "fact_id": cand["fact_id"],
                    "event_date": cand["event_date"],
                    "theme": cand["theme"],
                    "text_en": build_statement_text(cand["event_date"], cand["theme"], "en"),
                    "text_hi": build_statement_text(cand["event_date"], cand["theme"], "hi"),
                    "is_decoy": False,
                })
                used_themes.add(cand["theme"])
                if len(chosen) == 3:
                    break

    # If still fewer than 2, skip feature
    if len(chosen) < 2:
        return [], False

    # Inject Decoy if eligible
    if has_decoy and len(chosen) >= 3:
        # Pick an unused theme or last theme
        unused_themes = [t for t in ALLOWED_THEMES if t not in used_themes]
        decoy_theme = unused_themes[0] if unused_themes else "learning"

        # Find a decoy date window where NO trigger occurred (maximum gap distance)
        all_event_dates = [c["event_date"] for c in candidates]
        best_date = None
        best_min_dist = -1
        min_date = (today or date.today()) - timedelta(days=365 * 8)
        max_date = (today or date.today()) - timedelta(days=180)

        probe_d = min_date
        while probe_d <= max_date:
            min_dist = min(abs((probe_d - ev_d).days) for ev_d in all_event_dates)
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_date = probe_d
            probe_d += timedelta(days=15)

        decoy_date = best_date if (best_date and best_min_dist > 120) else (today or date.today()) - timedelta(days=365 * 5)

        decoy_item = {
            "fact_id": "DECOY_CONTROL_WINDOW",
            "event_date": decoy_date,
            "theme": decoy_theme,
            "text_en": build_statement_text(decoy_date, decoy_theme, "en"),
            "text_hi": build_statement_text(decoy_date, decoy_theme, "hi"),
            "is_decoy": True,
        }
        # Replace the middle or last item
        replace_idx = rng.choice([1, 2])
        chosen[replace_idx] = decoy_item

    # Sort final items by date chronologically
    chosen.sort(key=lambda x: x["event_date"])
    return chosen, has_decoy


def get_or_create_past_check_set(
    db: Session,
    user_id: str,
    profile: BirthProfile,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Retrieve or create the Past Check set for a user.
    Returns payload for client with is_decoy strictly hidden.
    """
    arm = get_or_assign_experiment_arm(db, user_id)
    if arm == "control":
        return {
            "arm": "control",
            "should_show": False,
            "reason": "Control arm does not receive Past Check before paywall",
        }

    chart_hash = compute_chart_hash(profile)
    existing_set = (
        db.query(PastCheckSet)
        .filter(PastCheckSet.user_id == user_id)
        .filter(PastCheckSet.chart_hash == chart_hash)
        .first()
    )

    if not existing_set:
        candidates = generate_candidate_events(profile)
        statements, has_decoy = select_past_check_statements(candidates, user_id)

        if len(statements) < 2:
            existing_set = PastCheckSet(
                user_id=user_id,
                chart_hash=chart_hash,
                has_decoy=False,
                is_skipped=True,
            )
            db.add(existing_set)
            db.commit()
            return {
                "arm": "treatment",
                "should_show": False,
                "reason": "Insufficient verified candidate events to generate statements",
            }

        existing_set = PastCheckSet(
            user_id=user_id,
            chart_hash=chart_hash,
            has_decoy=has_decoy,
            is_skipped=False,
        )
        db.add(existing_set)
        db.flush()

        for st in statements:
            item = PastCheckItem(
                set_id=existing_set.id,
                fact_id=st["fact_id"],
                event_date=st["event_date"],
                theme=st["theme"],
                text_en=st["text_en"],
                text_hi=st["text_hi"],
                is_decoy=st["is_decoy"],
            )
            db.add(item)
        db.commit()

    if existing_set.is_skipped:
        return {
            "arm": "treatment",
            "should_show": False,
            "reason": "Skipped due to sparse chart data",
        }

    # Fetch items
    items = db.query(PastCheckItem).filter(PastCheckItem.set_id == existing_set.id).all()
    answered_count = sum(1 for it in items if it.answer is not None)
    yes_count = sum(1 for it in items if it.answer == "yes")
    is_completed = answered_count == len(items)

    # Format client payload: NEVER include is_decoy!
    client_items = []
    for it in items:
        client_items.append({
            "id": it.id,
            "fact_id": it.fact_id,
            "event_date": it.event_date.strftime("%Y-%m-%d"),
            "theme": it.theme,
            "statement": it.text_hi if lang == "hi" else it.text_en,
            "answer": it.answer,
            "is_answered": it.answer is not None,
        })

    return {
        "arm": "treatment",
        "should_show": True,
        "set_id": existing_set.id,
        "is_completed": is_completed,
        "answered_count": answered_count,
        "total_statements": len(items),
        "recognized_count": yes_count,
        "statements": client_items,
        "disclaimer": (
            "यह आपके अतीत का विचारणीय प्रतिबिंब है, कोई निश्चित प्रमाण नहीं।"
            if lang == "hi"
            else "This measures resonance and reflection, not astrological proof."
        ),
    }


def record_past_check_answer(
    db: Session,
    user_id: str,
    item_id: str,
    answer: str,
) -> Dict[str, Any]:
    """
    Idempotent upsert of a user's answer to a statement item.
    answer: 'yes' | 'not_really' | 'cant_recall'
    """
    if answer not in ["yes", "not_really", "cant_recall"]:
        raise ValueError(f"Invalid answer '{answer}'. Must be 'yes', 'not_really', or 'cant_recall'.")

    item = db.query(PastCheckItem).filter(PastCheckItem.id == item_id).first()
    if not item:
        raise ValueError("Past check item not found")

    item.answer = answer
    item.answered_at = datetime.now(timezone.utc)
    db.commit()

    # Recalculate set progress
    set_items = db.query(PastCheckItem).filter(PastCheckItem.set_id == item.set_id).all()
    answered_count = sum(1 for it in set_items if it.answer is not None)
    yes_count = sum(1 for it in set_items if it.answer == "yes")
    is_completed = answered_count == len(set_items)

    return {
        "status": "recorded",
        "item_id": item_id,
        "answer": answer,
        "is_completed": is_completed,
        "recognized_count": yes_count,
        "total_statements": len(set_items),
    }
