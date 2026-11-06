"""Tests for Section B6: Home screen content grounding and verification."""

from datetime import datetime, timezone
import pytest

from backend.home_content import get_grounded_home_content


def test_home_content_has_fact_ids_and_no_copied_strings():
    """
    Verify that every Home string either has explicit fact_ids or is labelled static.
    Verifies that hard-coded strings (e.g. 'Wear Light Blue', 'Lucky No. 2', 99%)
    are replaced with verified calculations and documented rules.
    """
    # Sample user with Aries Lagna (1) and Taurus Moon (2)
    payload = get_grounded_home_content(
        natal_lagna_sign_num=1,
        natal_moon_sign_num=2,
        active_mahadasha="Jupiter",
        active_antardasha="Saturn",
        lang="en",
    )

    # 1. Daily Insight is grounded with fact_ids
    insight = payload["daily_insight"]
    assert insight["type"] == "grounded"
    assert len(insight["fact_ids"]) >= 2
    assert all(fid.startswith("FACT_") for fid in insight["fact_ids"])
    assert insight["title"]
    assert insight["text"]
    assert "99%" not in insight["text"]

    # 2. Traditional Convention has fact_id and documented rule
    conv = payload["traditional_convention"]
    assert conv["type"] == "traditional_convention"
    assert len(conv["fact_ids"]) >= 1
    assert conv["fact_ids"][0].startswith("FACT_VARA_")
    assert "Brihat Samhita" in conv["documentation"]
    assert conv["day"]
    assert conv["lord"]
    assert conv["color"]
    assert isinstance(conv["number"], int)

    # 3. Gochara Harmony has exact formula and fact_id
    harmony = payload["gochara_harmony"]
    assert harmony["type"] == "grounded"
    assert "FACT_GOCHARA_HARMONY_RATIO" in harmony["fact_ids"]
    assert 0 <= harmony["percentage"] <= 100
    assert "Phaladeepika Ch. 26" in harmony["formula"]
    assert "/" in harmony["formula"]

    # 4. Questions For You are dynamically anchored to Dasha and Transits
    questions = payload["questions_for_you"]
    assert len(questions) == 4
    for q in questions:
        assert q["type"] == "grounded"
        assert len(q["fact_ids"]) >= 1
        assert any(fid.startswith("FACT_") for fid in q["fact_ids"])
        assert len(q["text"]) > 10

    # Verify active Mahadasha (Jupiter) and Antardasha (Saturn) appear in generated questions
    assert "Jupiter" in questions[0]["text"]
    assert "Saturn" in questions[1]["text"]


def test_home_content_hindi_localization():
    """Verify Hindi generation for all home content."""
    payload = get_grounded_home_content(
        natal_lagna_sign_num=1,
        natal_moon_sign_num=2,
        active_mahadasha="Jupiter",
        active_antardasha="Saturn",
        lang="hi",
    )
    assert "चंद्र गोचर" in payload["daily_insight"]["title"]
    assert "गोचर संतुलन" in payload["gochara_harmony"]["label"]
    assert len(payload["questions_for_you"]) == 4
    assert all(q["type"] == "grounded" for q in payload["questions_for_you"])
