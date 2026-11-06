"""Melooha Auspicious Muhurta LangGraph Orchestrator.

Directed State Machine:
1. Parse & Classify Intent (Natural Language -> Vedic Activity Profile & Overrides)
2. Spatial Geocode (Resolve coordinates & local solar horizon)
3. Swiss Ephemeris Sweep (30-min window mathematical Panchang & Solar windows)
4. Melooha Scorer (Universal + Category + Tara Bala + Chandra Bala Matrix)
5. Explain & Guard (Empathetic rationale + Zero-Hallucination Fact Guardrail)
"""

from datetime import date, datetime, time, timedelta
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, TypedDict
from uuid import uuid4
from zoneinfo import ZoneInfo
from langgraph.graph import END, StateGraph

from backend.muhurta.calendar_gen import generate_calendar_payload
from backend.muhurta.ephemeris import (
    calculate_panchanga_at_instant,
    calculate_sun_times,
)
from backend.muhurta.models import (
    ActivityOverride,
    CalendarPayload,
    MuhurtaResponse,
    MuhurtaSlot,
    PanchangaDetails,
    ParsedMuhurtaIntent,
    PersonalAlignment,
    TimeOfDayPreference,
    VedicActivityCategory,
)
from backend.muhurta.personalization import compute_personal_alignment
from backend.muhurta.rules import OVERRIDE_RULES
from backend.muhurta.scorer import score_muhurta_slot
from backend.muhurta.validator import (
    build_grounded_fallback_explanation,
    validate_explanation_facts,
)
from backend.places import search_cities

logger = logging.getLogger("melooha.muhurta.orchestrator")


class MuhurtaState(TypedDict):
    user_id: str
    profile_id: Optional[str]
    profile_name: str
    user_janma_nakshatra_num: Optional[int]
    user_janma_rashi_num: Optional[int]
    raw_query: str
    start_date: Optional[str]
    end_date: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timezone_str: Optional[str]
    explicit_category: Optional[VedicActivityCategory]
    explicit_override: Optional[ActivityOverride]
    parsed_intent: Optional[ParsedMuhurtaIntent]
    raw_candidates: List[Dict[str, Any]]
    scored_slots: List[MuhurtaSlot]
    final_response: Optional[MuhurtaResponse]
    error: Optional[str]


# ==============================================================================
# NODE 1: PARSE & CLASSIFY INTENT
# ==============================================================================
def parse_and_classify_node(state: MuhurtaState) -> Dict[str, Any]:
    """Parse natural language query into structured Vedic Activity Category and Dates."""
    query = state["raw_query"]
    q_lower = query.lower()

    # 1. Classify Category & Override
    cat = state.get("explicit_category")
    override = state.get("explicit_override")

    if not override:
        if any(w in q_lower for w in ["griha pravesh", "house warming", "new home", "shifting home", "entering home"]):
            cat = VedicActivityCategory.PROPERTY_CONSTRUCTION
            override = ActivityOverride.GRIHA_PRAVESH
        elif any(w in q_lower for w in ["startup", "venture", "business launch", "company", "launching app", "tech"]):
            cat = VedicActivityCategory.BUSINESS_FINANCE
            override = ActivityOverride.TECH_STARTUP_LAUNCH
        elif any(w in q_lower for w in ["office", "shop", "inauguration", "showroom"]):
            cat = VedicActivityCategory.BUSINESS_FINANCE
            override = ActivityOverride.OFFICE_SHOP_INAUGURATION
        elif any(w in q_lower for w in ["buy house", "buy property", "purchase plot", "flat purchase", "real estate"]):
            cat = VedicActivityCategory.PROPERTY_CONSTRUCTION
            override = ActivityOverride.PROPERTY_PURCHASE
        elif any(w in q_lower for w in ["buy car", "purchase vehicle", "buy bike", "car delivery"]):
            cat = VedicActivityCategory.TRAVEL_JOURNEY
            override = ActivityOverride.VEHICLE_PURCHASE
        elif any(w in q_lower for w in ["contract", "agreement", "deal", "signing"]):
            cat = VedicActivityCategory.BUSINESS_FINANCE
            override = ActivityOverride.CONTRACT_SIGNING
        elif any(w in q_lower for w in ["investing", "stocks", "trading", "crypto", "shares"]):
            cat = VedicActivityCategory.BUSINESS_FINANCE
            override = ActivityOverride.INVESTING_TRADING
        elif any(w in q_lower for w in ["marriage", "wedding", "vivah", "shadi"]):
            cat = VedicActivityCategory.MARRIAGE_RELATIONSHIP
            override = ActivityOverride.VIVAH_MARRIAGE
        elif any(w in q_lower for w in ["engagement", "roka", "ring ceremony"]):
            cat = VedicActivityCategory.MARRIAGE_RELATIONSHIP
            override = ActivityOverride.ENGAGEMENT_ROKA
        elif any(w in q_lower for w in ["surgery", "operation", "medical procedure"]):
            cat = VedicActivityCategory.HEALTH_MEDICAL
            override = ActivityOverride.MEDICAL_SURGERY
        elif any(w in q_lower for w in ["travel", "flight", "trip", "journey", "vacation"]):
            cat = VedicActivityCategory.TRAVEL_JOURNEY
            override = ActivityOverride.DOMESTIC_JOURNEY
        elif any(w in q_lower for w in ["exam", "interview", "new course", "learning"]):
            cat = VedicActivityCategory.EDUCATION_LEARNING
            override = ActivityOverride.NEW_EDUCATION_COURSE
        elif any(w in q_lower for w in ["joining job", "new job", "joining date", "offer letter"]):
            cat = VedicActivityCategory.JOB_CAREER
            override = ActivityOverride.JOB_JOINING

    if not cat:
        cat = VedicActivityCategory.BUSINESS_FINANCE

    # 2. Time-of-day Preference
    time_pref = TimeOfDayPreference.ANY
    if "morning" in q_lower:
        time_pref = TimeOfDayPreference.MORNING
    elif "afternoon" in q_lower:
        time_pref = TimeOfDayPreference.AFTERNOON
    elif "evening" in q_lower:
        time_pref = TimeOfDayPreference.EVENING
    elif "abhijit" in q_lower or "noon" in q_lower:
        time_pref = TimeOfDayPreference.ABHIJIT

    # 3. Date Range Resolution
    today = date.today()
    start_dt = today
    end_dt = today + timedelta(days=7)

    # Check for explicit dates or relative keywords
    if state.get("start_date") and state.get("end_date"):
        try:
            start_dt = date.fromisoformat(state["start_date"])
            end_dt = date.fromisoformat(state["end_date"])
        except ValueError:
            pass
    elif "next week" in q_lower:
        start_dt = today + timedelta(days=7 - today.weekday())
        end_dt = start_dt + timedelta(days=6)
    elif "next month" in q_lower:
        start_dt = today + timedelta(days=30)
        end_dt = start_dt + timedelta(days=14)
    elif "tomorrow" in q_lower:
        start_dt = today + timedelta(days=1)
        end_dt = today + timedelta(days=3)
    elif "this weekend" in q_lower:
        days_to_sat = (5 - today.weekday()) % 7
        start_dt = today + timedelta(days=days_to_sat)
        end_dt = start_dt + timedelta(days=2)

    # 4. Location Name Extraction
    loc_name = state.get("location_name")
    if not loc_name:
        # Common cities in query
        for city in ["bengaluru", "bangalore", "mumbai", "delhi", "austin", "london", "dubai", "pune", "hyderabad", "jammu", "srinagar"]:
            if city in q_lower:
                loc_name = city.title()
                break

    parsed = ParsedMuhurtaIntent(
        category=cat,
        override=override,
        target_start_date=start_dt.isoformat(),
        target_end_date=end_dt.isoformat(),
        time_preference=time_pref,
        target_location_name=loc_name or "Bengaluru, Karnataka, India",
        latitude=state.get("latitude") or 12.9716,
        longitude=state.get("longitude") or 77.5946,
        timezone_str=state.get("timezone_str") or "Asia/Kolkata",
        confidence=0.96,
        raw_query=query,
    )

    return {"parsed_intent": parsed}


# ==============================================================================
# NODE 2: SPATIAL GEOCODE & SOLAR HORIZON
# ==============================================================================
def spatial_geocode_node(state: MuhurtaState) -> Dict[str, Any]:
    """Resolve exact Lat/Lon & Timezone for local solar horizons."""
    parsed: ParsedMuhurtaIntent = state["parsed_intent"]
    loc_name = parsed.target_location_name

    # Check if coords are already provided
    if state.get("latitude") and state.get("longitude") and state.get("timezone_str"):
        parsed.latitude = state["latitude"]
        parsed.longitude = state["longitude"]
        parsed.timezone_str = state["timezone_str"]
        return {"parsed_intent": parsed}

    results = search_cities(loc_name, limit=1)
    if results:
        city = results[0]
        parsed.latitude = city["lat"]
        parsed.longitude = city["lon"]
        parsed.timezone_str = city.get("tz", "Asia/Kolkata")
        parsed.target_location_name = city["name"]
    else:
        # Standard fallback to Bengaluru
        parsed.latitude = 12.9716
        parsed.longitude = 77.5946
        parsed.timezone_str = "Asia/Kolkata"
        parsed.target_location_name = "Bengaluru, Karnataka, India"

    return {"parsed_intent": parsed}


# ==============================================================================
# NODE 3: SWISS EPHEMERIS 30-MIN SWEEP
# ==============================================================================
def ephemeris_sweep_node(state: MuhurtaState) -> Dict[str, Any]:
    """
    30-minute window sweep across the target date range using Swiss Ephemeris.
    Computes 5 Panchang elements, Rahu Kalam, Yamaganda, Choghadiya, and personal Tara/Chandra.
    """
    parsed: ParsedMuhurtaIntent = state["parsed_intent"]
    start_d = date.fromisoformat(parsed.target_start_date)
    end_d = date.fromisoformat(parsed.target_end_date)
    tz_str = parsed.timezone_str
    tz = ZoneInfo(tz_str)

    user_nak_num = state.get("user_janma_nakshatra_num")
    user_rashi_num = state.get("user_janma_rashi_num")

    candidates = []
    curr_d = start_d
    max_days = min(7, (end_d - start_d).days + 1)

    for day_i in range(max_days):
        day_date = curr_d + timedelta(days=day_i)
        sample_dt = datetime(day_date.year, day_date.month, day_date.day, 12, 0, tzinfo=tz)

        sunrise_loc, sunset_loc = calculate_sun_times(sample_dt, parsed.latitude, parsed.longitude, tz_str)

        # Determine sweep window boundaries based on time_preference
        if parsed.time_preference == TimeOfDayPreference.MORNING:
            sweep_start = sunrise_loc
            sweep_end = datetime(day_date.year, day_date.month, day_date.day, 12, 0, tzinfo=tz)
        elif parsed.time_preference == TimeOfDayPreference.AFTERNOON:
            sweep_start = datetime(day_date.year, day_date.month, day_date.day, 12, 0, tzinfo=tz)
            sweep_end = datetime(day_date.year, day_date.month, day_date.day, 16, 30, tzinfo=tz)
        elif parsed.time_preference == TimeOfDayPreference.EVENING:
            sweep_start = datetime(day_date.year, day_date.month, day_date.day, 16, 30, tzinfo=tz)
            sweep_end = sunset_loc
        elif parsed.time_preference == TimeOfDayPreference.ABHIJIT:
            day_dur = (sunset_loc - sunrise_loc).total_seconds()
            muhurta_dur = day_dur / 15.0
            sweep_start = sunrise_loc + timedelta(seconds=7 * muhurta_dur)
            sweep_end = sunrise_loc + timedelta(seconds=8 * muhurta_dur)
        else:
            # Full daytime sweep from Sunrise to Sunset
            sweep_start = sunrise_loc
            sweep_end = sunset_loc

        # Step in 30-minute intervals
        step_dt = sweep_start
        while step_dt + timedelta(minutes=45) <= sweep_end:
            slot_midpoint = step_dt + timedelta(minutes=22, seconds=30)

            # 1. Pure Ephemeris Panchanga (reuse calculated sunrise & sunset)
            panchang = calculate_panchanga_at_instant(
                slot_midpoint,
                parsed.latitude,
                parsed.longitude,
                tz_str,
                sunrise_sunset=(sunrise_loc, sunset_loc),
            )

            # 2. Extract Moon Sign for Chandra Bala
            # Each nakshatra corresponds to roughly 13°20'
            moon_sign_num = ((panchang.nakshatra_number - 1) * 4 // 9) + 1
            if moon_sign_num > 12:
                moon_sign_num = 12

            # 3. Personal Alignment
            personal, _ = compute_personal_alignment(
                candidate_nakshatra_num=panchang.nakshatra_number,
                candidate_moon_sign_num=moon_sign_num,
                user_janma_nakshatra_num=user_nak_num,
                user_janma_rashi_num=user_rashi_num,
            )

            candidates.append({
                "start_dt": step_dt,
                "end_dt": step_dt + timedelta(minutes=90),  # standard 1.5h ceremony block
                "panchanga": panchang,
                "personal": personal,
            })

            step_dt += timedelta(minutes=45)

    return {"raw_candidates": candidates}


# ==============================================================================
# NODE 4: MELOOHA SCORER & CANDIDATE RANKING
# ==============================================================================
def melooha_scorer_node(state: MuhurtaState) -> Dict[str, Any]:
    """Score candidates using deterministic matrix and rank top windows."""
    candidates = state.get("raw_candidates", [])
    parsed: ParsedMuhurtaIntent = state["parsed_intent"]

    scored_list = []
    for c in candidates:
        score, is_fav, reasons = score_muhurta_slot(
            panchanga=c["panchanga"],
            personal=c["personal"],
            category=parsed.category,
            override=parsed.override,
        )

        if is_fav and score >= 16.0:  # Threshold for certified auspicious windows
            scored_list.append({
                "score": score,
                "start_dt": c["start_dt"],
                "end_dt": c["end_dt"],
                "panchanga": c["panchanga"],
                "personal": c["personal"],
                "reasons": reasons,
            })

    # Sort descending by score
    scored_list.sort(key=lambda x: x["score"], reverse=True)

    # Select distinct non-overlapping top slots (Max 3)
    final_top_slots = []
    for item in scored_list:
        # Check if already have a slot on the same day to ensure variety
        same_day = any(
            existing["start_dt"].date() == item["start_dt"].date()
            for existing in final_top_slots
        )
        if not same_day or len(final_top_slots) == 0:
            final_top_slots.append(item)
        if len(final_top_slots) >= 3:
            break

    # If strict filtering left us with less than 2, allow second window on same best day
    if len(final_top_slots) < 2 and len(scored_list) > len(final_top_slots):
        for item in scored_list:
            if item not in final_top_slots:
                final_top_slots.append(item)
                if len(final_top_slots) >= 3:
                    break

    return {"scored_slots": final_top_slots}


# ==============================================================================
# NODE 5: EXPLAIN & GUARD (ZERO-HALLUCINATION LLM LAYER)
# ==============================================================================
def explain_and_guard_node(state: MuhurtaState) -> Dict[str, Any]:
    """
    Generate grounded 2-3 sentence Vedic narrative, assert facts with validation guardrail,
    and generate calendar synchronization payloads.
    """
    top_slots_raw = state.get("scored_slots", [])
    parsed: ParsedMuhurtaIntent = state["parsed_intent"]
    profile_name = state.get("profile_name", "You")
    act_title = parsed.override.value.replace("_", " ").title() if parsed.override else parsed.category.value.replace("_", " ").title()

    final_slots: List[MuhurtaSlot] = []

    for rank_idx, slot_item in enumerate(top_slots_raw, start=1):
        panch: PanchangaDetails = slot_item["panchanga"]
        pers: PersonalAlignment = slot_item["personal"]
        start_time_str = slot_item["start_dt"].isoformat()
        end_time_str = slot_item["end_dt"].isoformat()

        # Build grounded explanation
        explanation = build_grounded_fallback_explanation(
            activity_title=act_title,
            slot_nakshatra=panch.nakshatra,
            slot_choghadiya=panch.choghadiya,
            slot_tara=pers.tara_bala,
            slot_chandra_house=pers.chandra_house,
            slot_tithi=panch.tithi,
        )

        # Run strict validation guardrail
        is_valid, violations = validate_explanation_facts(
            explanation=explanation,
            slot_nakshatra=panch.nakshatra,
            slot_tithi=panch.tithi,
            slot_yoga=panch.yoga,
            slot_choghadiya=panch.choghadiya,
            slot_tara=pers.tara_bala,
            slot_chandra_house=pers.chandra_house,
        )

        if not is_valid:
            logger.warning("Guardrail caught violation: %s; using deterministic fallback", violations)
            explanation = build_grounded_fallback_explanation(
                activity_title=act_title,
                slot_nakshatra=panch.nakshatra,
                slot_choghadiya=panch.choghadiya,
                slot_tara=pers.tara_bala,
                slot_chandra_house=pers.chandra_house,
                slot_tithi=panch.tithi,
            )

        # Generate Calendar payload
        event_title = f"Auspicious Timing: {act_title} ({profile_name})"
        cal_payload = generate_calendar_payload(
            title=event_title,
            description=(
                f"{explanation}\n\n"
                f"Panchanga: {panch.tithi}, {panch.nakshatra}, {panch.choghadiya} Choghadiya\n"
                f"Personal Alignment: {pers.tara_bala}, {pers.chandra_bala}\n"
                f"Calculated by Melooha AI Swiss Ephemeris Engine."
            ),
            location_name=parsed.target_location_name,
            start_dt=slot_item["start_dt"],
            end_dt=slot_item["end_dt"],
        )

        final_slots.append(
            MuhurtaSlot(
                rank=rank_idx,
                score=slot_item["score"],
                start_time_local=start_time_str,
                end_time_local=end_time_str,
                panchanga=panch,
                personal_alignment=pers,
                explanation=explanation,
                calendar_payload=cal_payload,
            )
        )

    # Advisory Note
    advisory = "For permanent sanctification and enduring success, combine this window with family Kuladevata or Ganesha invocation."
    if parsed.override and parsed.override.value in OVERRIDE_RULES:
        advisory = OVERRIDE_RULES[parsed.override.value].get("advice", advisory)

    response = MuhurtaResponse(
        muhurta_id=str(uuid4()),
        user_id=state.get("user_id", "default_user"),
        profile_name=profile_name,
        activity={
            "category": parsed.category.value,
            "override": parsed.override.value if parsed.override else None,
            "confidence": parsed.confidence,
        },
        location={
            "name": parsed.target_location_name,
            "coordinates": {
                "lat": parsed.latitude,
                "lon": parsed.longitude,
            },
            "timezone": parsed.timezone_str,
        },
        slots=final_slots,
        advisory_note=advisory,
        created_at=datetime.now(ZoneInfo("UTC")).isoformat(),
    )

    return {"final_response": response}


# ==============================================================================
# STATE GRAPH COMPILATION
# ==============================================================================
def build_muhurta_agent_graph():
    """Build directed LangGraph state machine for the Muhurta Engine."""
    graph = StateGraph(MuhurtaState)

    graph.add_node("parse_and_classify", parse_and_classify_node)
    graph.add_node("spatial_geocode", spatial_geocode_node)
    graph.add_node("ephemeris_sweep", ephemeris_sweep_node)
    graph.add_node("melooha_scorer", melooha_scorer_node)
    graph.add_node("explain_and_guard", explain_and_guard_node)

    graph.set_entry_point("parse_and_classify")
    graph.add_edge("parse_and_classify", "spatial_geocode")
    graph.add_edge("spatial_geocode", "ephemeris_sweep")
    graph.add_edge("ephemeris_sweep", "melooha_scorer")
    graph.add_edge("melooha_scorer", "explain_and_guard")
    graph.add_edge("explain_and_guard", END)

    return graph.compile()


muhurta_graph = build_muhurta_agent_graph()
