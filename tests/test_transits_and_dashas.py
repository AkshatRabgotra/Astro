"""Unit tests for Vimshottari Antardasha calculation, Gochara transits, and multi-turn context."""

from datetime import date, datetime, timezone
import pytest
from chart.engine import calculate_chart_facts
from chart.models import BirthInput
from chart.dasha import calculate_vimshottari_periods
from chart.transits import calculate_today_transits
from llm.prompts import build_reading_prompt


def test_dasha_calculation_includes_antardashas():
    # Moon in Chitra (ruled by Mars)
    moon_lon = 185.0
    birth_dt = datetime(1990, 5, 20, 14, 0, tzinfo=timezone.utc)
    target_dt = datetime(2026, 11, 1, tzinfo=timezone.utc)

    current_dasha, all_dashas, antardashas = calculate_vimshottari_periods(
        moon_longitude=moon_lon,
        birth_dt=birth_dt,
        target_dt=target_dt
    )

    assert current_dasha is not None
    assert current_dasha.mahadasha_lord is not None
    assert current_dasha.antardasha_lord is not None
    assert len(all_dashas) > 0

    # Ensure 9 Antardashas are computed for the active Mahadasha
    assert len(antardashas) == 9
    lords = [ad.antardasha_lord for ad in antardashas]
    assert current_dasha.antardasha_lord in lords


def test_today_transits_calculation():
    # Test for Scorpio Lagna (8) and Virgo Moon (6)
    transits_report = calculate_today_transits(
        natal_lagna_sign_num=8,
        natal_moon_sign_num=6
    )

    assert transits_report.calculated_at_utc is not None
    assert len(transits_report.transits) == 9  # Sun..Ketu

    # Verify house calculations from Lagna and Moon
    for p in transits_report.transits:
        assert 1 <= p.house_from_lagna <= 12
        assert 1 <= p.house_from_moon <= 12
        assert p.sign is not None
        assert p.nakshatra_name is not None

    # Verify Sade Sati structure
    assert isinstance(transits_report.sade_sati_active, bool)
    assert transits_report.sade_sati_status is not None

    # Verify Jupiter Transit summary
    assert "Jupiter" in transits_report.jupiter_transit_summary


def test_build_reading_prompt_with_conversation_history():
    bi = BirthInput(
        birth_date=date(1995, 3, 10),
        birth_time="12:00:00",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
        place_name="Mumbai, India"
    )
    chart = calculate_chart_facts(bi)

    conversation_history = [
        {"user": "What is my career direction?", "assistant": "Your 10th house is energized by Jupiter [F05]."}
    ]

    prompt = build_reading_prompt(
        chart_facts=chart,
        question="Will this year bring promotions?",
        conversation_history=conversation_history
    )

    # Verify conversation history block is embedded in prompt
    assert "PREVIOUS CONVERSATION CONTEXT" in prompt
    assert "What is my career direction?" in prompt
    assert "Your 10th house is energized by Jupiter" in prompt
    assert "Will this year bring promotions?" in prompt
