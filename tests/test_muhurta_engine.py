"""Unit and Integration Tests for Melooha Auspicious Muhurta Engine."""

from datetime import datetime
import pytest
from zoneinfo import ZoneInfo

from backend.muhurta.calendar_gen import generate_calendar_payload
from backend.muhurta.ephemeris import (
    calculate_panchanga_at_instant,
    calculate_sun_times,
    get_julian_day,
    get_sidereal_positions,
)
from backend.muhurta.models import (
    ActivityOverride,
    PanchangaDetails,
    PersonalAlignment,
    VedicActivityCategory,
)
from backend.muhurta.orchestrator import muhurta_graph
from backend.muhurta.personalization import (
    calculate_chandra_bala,
    calculate_tara_bala,
    compute_personal_alignment,
)
from backend.muhurta.scorer import score_muhurta_slot
from backend.muhurta.validator import (
    build_grounded_fallback_explanation,
    validate_explanation_facts,
)


def test_ephemeris_deterministic_panchanga():
    """Verify Swiss Ephemeris produces mathematical consistency for a fixed epoch."""
    tz_str = "Asia/Kolkata"
    fixed_dt = datetime(2026, 11, 8, 8, 30, tzinfo=ZoneInfo(tz_str))
    lat, lon = 12.9716, 77.5946

    panchang = calculate_panchanga_at_instant(fixed_dt, lat, lon, tz_str)

    assert panchang.tithi is not None
    assert 1 <= panchang.tithi_number <= 30
    assert 1 <= panchang.nakshatra_number <= 27
    assert panchang.vara in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assert panchang.choghadiya in ["Amrit", "Shubh", "Labh", "Char", "Udveg", "Kaal", "Rog"]


def test_tara_bala_mathematical_precision():
    """Tara Bala: ((SlotNak - UserNak) % 27) % 9 + 1."""
    # User is Ashwini (1), Slot is Rohini (4) -> diff = 3 -> (3 % 9) + 1 = 4 (Kshema)
    name, num, is_fav, score = calculate_tara_bala(4, 1)
    assert num == 4
    assert "Kshema" in name
    assert is_fav is True
    assert score == 4.0

    # User is Ashwini (1), Slot is Pushya (8) -> diff = 7 -> (7 % 9) + 1 = 8 (Mitra)
    name, num, is_fav, score = calculate_tara_bala(8, 1)
    assert num == 8
    assert "Mitra" in name
    assert is_fav is True

    # User is Ashwini (1), Slot is Ashlesha (9) -> diff = 8 -> (8 % 9) + 1 = 9 (Parama Mitra)
    name, num, is_fav, score = calculate_tara_bala(9, 1)
    assert num == 9
    assert "Parama Mitra" in name
    assert is_fav is True

    # User is Ashwini (1), Slot is Magha (10) -> diff = 9 -> (9 % 9) + 1 = 1 (Janma)
    name, num, is_fav, score = calculate_tara_bala(10, 1)
    assert num == 1
    assert "Janma" in name

    # User is Ashwini (1), Slot is Purva Phalguni (11) -> diff = 10 -> (10 % 9) + 1 = 2 (Sampat)
    name, num, is_fav, score = calculate_tara_bala(11, 1)
    assert num == 2
    assert "Sampat" in name
    assert is_fav is True


def test_chandra_bala_ashtama_chandra_disqualification():
    """8th house lunar transit from Janma Rashi must trigger Ashtama Chandra flaw."""
    # User is Aries (1), Slot Moon is Scorpio (8) -> House 8
    desc, house_num, is_fav, is_ashtama, score = calculate_chandra_bala(8, 1)
    assert house_num == 8
    assert is_ashtama is True
    assert is_fav is False
    assert score == -20.0

    # User is Taurus (2), Slot Moon is Pisces (12) -> House 11 (Labha)
    desc, house_num, is_fav, is_ashtama, score = calculate_chandra_bala(12, 2)
    assert house_num == 11
    assert is_ashtama is False
    assert is_fav is True
    assert score == 7.0


def test_rahu_kalam_hard_filter_exclusion():
    """Any slot during Rahu Kalam must be disqualified from final output."""
    dummy_panch = PanchangaDetails(
        tithi="Shukla Dashami",
        tithi_number=10,
        paksha="Shukla",
        nakshatra="Rohini (Dhruva (Fixed))",
        nakshatra_number=4,
        nakshatra_temperament="Dhruva (Fixed)",
        vara="Sunday",
        vara_lord="Sun",
        yoga="Siddhi",
        yoga_number=16,
        is_inauspicious_yoga=False,
        karana="Bava",
        is_vishti_bhadra=False,
        choghadiya="Amrit",
        choghadiya_is_favorable=True,
        is_rahu_kalam=True,  # Afflicted!
        is_yamaganda=False,
        is_abhijit=False,
    )
    dummy_personal = PersonalAlignment(
        tara_bala="Sadhana",
        tara_bala_number=6,
        tara_bala_is_favorable=True,
        chandra_bala="11th House",
        chandra_house=11,
        chandra_bala_is_favorable=True,
        is_ashtama_chandra=False,
        score_contribution="+13.0 pts",
    )

    score, is_acceptable, reasons = score_muhurta_slot(
        panchanga=dummy_panch,
        personal=dummy_personal,
        category=VedicActivityCategory.PROPERTY_CONSTRUCTION,
        override=ActivityOverride.GRIHA_PRAVESH,
    )

    assert is_acceptable is False
    assert any("Rahu Kalam" in r for r in reasons)


def test_zero_hallucination_guardrail():
    """Assert validator rejects hallucinated astrological entities."""
    # Real slot has Rohini Nakshatra and Amrit Choghadiya
    slot_nak = "Rohini (Dhruva (Fixed))"
    slot_tithi = "Shukla Dashami"
    slot_yoga = "Siddhi"
    slot_chog = "Amrit"
    slot_tara = "Sadhana (Accomplishment)"
    slot_house = 11

    # Good explanation
    valid_text = "This morning window combines Rohini with Amrit Choghadiya. It activates your 11th House and Sadhana Tara."
    is_valid, violations = validate_explanation_facts(
        valid_text, slot_nak, slot_tithi, slot_yoga, slot_chog, slot_tara, slot_house
    )
    assert is_valid is True
    assert len(violations) == 0

    # Hallucinated explanation (mentions Revati Nakshatra and 8th House)
    hallucinated_text = "This window is powered by Revati Nakshatra and activates your 8th House."
    is_valid_bad, violations_bad = validate_explanation_facts(
        hallucinated_text, slot_nak, slot_tithi, slot_yoga, slot_chog, slot_tara, slot_house
    )
    assert is_valid_bad is False
    assert any("Hallucinated Nakshatra" in v for v in violations_bad)
    assert any("Hallucinated Lunar Transit House" in v for v in violations_bad)


def test_calendar_payload_rfc5545():
    """Verify RFC 5545 compliance and Google Calendar URL generation."""
    start_dt = datetime(2026, 11, 8, 8, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    end_dt = datetime(2026, 11, 8, 9, 45, tzinfo=ZoneInfo("Asia/Kolkata"))

    payload = generate_calendar_payload(
        title="Auspicious Timing: Griha Pravesh",
        description="Ceremony auspicious window",
        location_name="Bengaluru, India",
        start_dt=start_dt,
        end_dt=end_dt,
    )

    assert "BEGIN:VCALENDAR" in payload.ics_data
    assert "SUMMARY:Auspicious Timing: Griha Pravesh" in payload.ics_data
    assert "https://calendar.google.com/calendar/render" in payload.google_calendar_url


def test_end_to_end_langgraph_orchestration():
    """Full pipeline execution for natural language query."""
    initial_state = {
        "user_id": "test-user-456",
        "profile_id": None,
        "profile_name": "Avantika",
        "user_janma_nakshatra_num": 4,  # Rohini
        "user_janma_rashi_num": 2,      # Taurus
        "raw_query": "Griha Pravesh ceremony in Austin next month",
        "start_date": None,
        "end_date": None,
        "location_name": None,
        "latitude": None,
        "longitude": None,
        "timezone_str": None,
        "explicit_category": None,
        "explicit_override": None,
        "parsed_intent": None,
        "raw_candidates": [],
        "scored_slots": [],
        "final_response": None,
        "error": None,
    }

    result = muhurta_graph.invoke(initial_state)
    resp = result["final_response"]

    assert resp is not None
    assert resp.activity["category"] == "property_construction"
    assert resp.activity["override"] == "griha_pravesh"
    assert "Austin" in resp.location["name"]
    assert len(resp.slots) > 0
    top = resp.slots[0]
    assert top.rank == 1
    assert top.score >= 16.0
    assert top.panchanga.tithi is not None
    assert top.personal_alignment.tara_bala is not None
    assert top.calendar_payload.google_calendar_url.startswith("https://calendar.google.com")
