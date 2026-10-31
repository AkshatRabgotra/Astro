"""Unit and Golden Tests for the Vedic Astrology Chart Engine."""

from datetime import date, datetime, timezone
import pytest
from chart.engine import calculate_chart_facts, format_degree, parse_timezone
from chart.models import BirthInput


def test_format_degree():
    assert format_degree(15.5) == "15°30'"
    assert format_degree(0.0) == "0°00'"
    assert format_degree(29.9999) == "30°00'"


def test_parse_timezone():
    tz1 = parse_timezone("Asia/Kolkata")
    assert tz1 is not None
    tz2 = parse_timezone("+05:30")
    assert tz2.utcoffset(None).total_seconds() == 5.5 * 3600
    tz3 = parse_timezone("-04:00")
    assert tz3.utcoffset(None).total_seconds() == -4.0 * 3600
    tz4 = parse_timezone("UTC")
    assert tz4.utcoffset(None).total_seconds() == 0


def test_golden_chart_1_new_delhi_1980():
    """Golden Test 1: New Delhi (1980-10-15 10:30 IST)"""
    bi = BirthInput(
        birth_date=date(1980, 10, 15),
        birth_time="10:30:00",
        time_known=True,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
        place_name="New Delhi, India"
    )
    ref_dt = datetime(2026, 10, 31, tzinfo=timezone.utc)
    chart = calculate_chart_facts(bi, target_dt=ref_dt)

    # Ascendant must be Scorpio (Sign 8)
    assert chart.lagna_sign == "Scorpio"
    assert chart.lagna_sign_number == 8
    assert chart.time_known is True

    # Planetary Placements & Whole-sign houses
    planets_map = {p.planet: p for p in chart.planets}
    assert planets_map["Sun"].sign == "Virgo"
    assert planets_map["Sun"].house == 11
    assert planets_map["Sun"].nakshatra.name == "Chitra"

    assert planets_map["Moon"].sign == "Sagittarius"
    assert planets_map["Moon"].house == 2
    assert planets_map["Moon"].nakshatra.name == "Mula"
    assert planets_map["Moon"].nakshatra.lord == "Ketu"

    assert planets_map["Mars"].sign == "Scorpio"
    assert planets_map["Mars"].house == 1

    assert planets_map["Mercury"].sign == "Libra"
    assert planets_map["Mercury"].house == 12

    assert planets_map["Jupiter"].sign == "Virgo"
    assert planets_map["Jupiter"].house == 11

    assert planets_map["Venus"].sign == "Leo"
    assert planets_map["Venus"].house == 10

    assert planets_map["Saturn"].sign == "Virgo"
    assert planets_map["Saturn"].house == 11

    assert planets_map["Rahu"].sign == "Cancer"
    assert planets_map["Rahu"].house == 9

    assert planets_map["Ketu"].sign == "Capricorn"
    assert planets_map["Ketu"].house == 3

    # Facts list verification
    assert len(chart.facts) == 21
    fact_ids = [f.id for f in chart.facts]
    assert fact_ids == [f"F{i:02d}" for i in range(1, 22)]

    f01 = chart.get_fact("F01")
    assert f01.is_available is True
    assert "Scorpio" in f01.text
    assert "House 1" in f01.text

    f14 = chart.get_fact("F14")  # Jupiter aspects
    assert "Capricorn" in f14.text
    assert "Ketu" in f14.text

    f15 = chart.get_fact("F15")  # Saturn aspects
    assert "Scorpio" in f15.text
    assert "Mars" in f15.text


def test_golden_chart_2_mumbai_1995():
    """Golden Test 2: Mumbai (1995-05-24 14:15 IST)"""
    bi = BirthInput(
        birth_date=date(1995, 5, 24),
        birth_time="14:15:00",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
        place_name="Mumbai, India"
    )
    ref_dt = datetime(2026, 10, 31, tzinfo=timezone.utc)
    chart = calculate_chart_facts(bi, target_dt=ref_dt)

    # Ascendant must be Virgo (Sign 6)
    assert chart.lagna_sign == "Virgo"
    assert chart.lagna_sign_number == 6

    planets_map = {p.planet: p for p in chart.planets}
    # Jupiter in Scorpio (House 3), Retrograde
    assert planets_map["Jupiter"].sign == "Scorpio"
    assert planets_map["Jupiter"].house == 3
    assert planets_map["Jupiter"].is_retrograde is True

    # Moon in Pisces (House 7)
    assert planets_map["Moon"].sign == "Pisces"
    assert planets_map["Moon"].house == 7
    assert planets_map["Moon"].nakshatra.name == "Uttara Bhadrapada"

    # Current Dasha at ref_dt
    assert chart.current_dasha is not None
    assert chart.current_dasha.mahadasha_lord == "Venus"


def test_golden_chart_3_bengaluru_2000():
    """Golden Test 3: Bengaluru (2000-01-01 05:45 IST) - Dignity & Retrograde checks"""
    bi = BirthInput(
        birth_date=date(2000, 1, 1),
        birth_time="05:45:00",
        time_known=True,
        latitude=12.9716,
        longitude=77.5946,
        timezone_str="Asia/Kolkata",
        place_name="Bengaluru, India"
    )
    ref_dt = datetime(2026, 10, 31, tzinfo=timezone.utc)
    chart = calculate_chart_facts(bi, target_dt=ref_dt)

    assert chart.lagna_sign == "Sagittarius"
    assert chart.lagna_sign_number == 9

    planets_map = {p.planet: p for p in chart.planets}
    saturn = planets_map["Saturn"]
    assert saturn.sign == "Aries"
    assert saturn.house == 5
    assert saturn.is_debilitated is True
    assert saturn.is_retrograde is True

    # Current Dasha check
    assert chart.current_dasha.mahadasha_lord == "Saturn"


def test_unknown_birth_time_explicit_handling():
    """Verify that unknown birth time marks time-dependent facts unavailable without guessing."""
    bi = BirthInput(
        birth_date=date(1980, 10, 15),
        birth_time=None,
        time_known=False,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
        place_name="New Delhi, India"
    )
    chart = calculate_chart_facts(bi)

    # Lagna must be None
    assert chart.lagna_sign is None
    assert chart.lagna_sign_number is None
    assert chart.time_known is False

    # Fact F01 must be unavailable
    f01 = chart.get_fact("F01")
    assert f01.is_available is False
    assert f01.is_time_dependent is True
    assert "unavailable" in f01.text.lower()

    # All planets must have house as None
    for p in chart.planets:
        assert p.house is None

    # Planet facts must be marked time_dependent and mention house unavailable
    f03 = chart.get_fact("F03")  # Sun
    assert f03.is_time_dependent is True
    assert "House unavailable" in f03.text

    # Current dasha must be flagged as approximate
    assert chart.current_dasha.is_approximate is True


def test_llm_context_rendering():
    """Verify clean string rendering of facts for LLM prompting."""
    bi = BirthInput(
        birth_date=date(2000, 1, 1),
        birth_time="05:45:00",
        time_known=True,
        latitude=12.9716,
        longitude=77.5946,
        timezone_str="Asia/Kolkata",
        place_name="Bengaluru, India"
    )
    chart = calculate_chart_facts(bi)
    context = chart.to_llm_context()

    assert "=== COMPUTED CHART FACTS" in context
    assert "[F01]" in context
    assert "[F12]" in context
    assert "[F21]" in context
    assert "Debilitated" in context
