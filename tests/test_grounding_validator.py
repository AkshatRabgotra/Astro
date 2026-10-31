"""Unit tests for the Grounding and Fact Validation Engine."""

from datetime import date, datetime, timezone
import json
import pytest

from chart.engine import calculate_chart_facts
from chart.models import BirthInput
from llm.fallback import build_safe_templated_answer
from llm.validator import AnswerValidator, parse_llm_json


@pytest.fixture
def sample_known_chart():
    """Known chart: New Delhi 1980 (Scorpio Lagna, Sun in Virgo H11, Mars in Scorpio H1, Saturn in Virgo H11)."""
    bi = BirthInput(
        birth_date=date(1980, 10, 15),
        birth_time="10:30:00",
        time_known=True,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
        place_name="New Delhi, India",
    )
    ref_dt = datetime(2026, 10, 31, tzinfo=timezone.utc)
    return calculate_chart_facts(bi, target_dt=ref_dt)


@pytest.fixture
def sample_unknown_time_chart():
    """Unknown time chart: houses unavailable."""
    bi = BirthInput(
        birth_date=date(1980, 10, 15),
        birth_time=None,
        time_known=False,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
        place_name="New Delhi, India",
    )
    return calculate_chart_facts(bi)


def test_valid_grounded_answer(sample_known_chart):
    raw_response = json.dumps({
        "answer": (
            "Your chart features Scorpio Lagna in House 1 [F01]. Mars is in Scorpio in House 1 [F05], "
            "giving you tremendous perseverance. Meanwhile, Sun is in Virgo in House 11 [F03], supporting large networks. "
            "Your current Mahadasha is Mars [F12]."
        ),
        "cited_fact_ids": ["F01", "F03", "F05", "F12"],
        "claims": [
            {"claim": "Scorpio Lagna in House 1", "fact_id": "F01"},
            {"claim": "Mars in Scorpio in House 1", "fact_id": "F05"},
            {"claim": "Sun in Virgo in House 11", "fact_id": "F03"},
            {"claim": "Current Mahadasha is Mars", "fact_id": "F12"},
        ],
    })

    result = AnswerValidator.validate(raw_response, sample_known_chart)
    assert result.is_valid is True
    assert len(result.violations) == 0
    assert len(result.verified_cited_facts) == 4


def test_violation_non_existent_fact_id(sample_known_chart):
    raw_response = json.dumps({
        "answer": "Saturn in Virgo brings structure [F99].",
        "cited_fact_ids": ["F99"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_known_chart)
    assert result.is_valid is False
    assert any("Cited non-existent fact ID: 'F99'" in v for v in result.violations)


def test_violation_citing_unavailable_fact(sample_unknown_time_chart):
    raw_response = json.dumps({
        "answer": "Your Lagna is Scorpio [F01].",
        "cited_fact_ids": ["F01"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_unknown_time_chart)
    assert result.is_valid is False
    assert any("marked UNAVAILABLE" in v for v in result.violations)


def test_violation_hallucinated_planet_sign(sample_known_chart):
    raw_response = json.dumps({
        "answer": "You have Mars in Gemini which brings communication restlessness [F05].",
        "cited_fact_ids": ["F05"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_known_chart)
    assert result.is_valid is False
    assert any("Claims 'Mars in Gemini', but chart has 'Mars in Scorpio'" in v for v in result.violations)


def test_violation_hallucinated_planet_house(sample_known_chart):
    raw_response = json.dumps({
        "answer": "Saturn in House 7 delays marital commitments [F09].",
        "cited_fact_ids": ["F09"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_known_chart)
    assert result.is_valid is False
    assert any("Claims 'Saturn in House 7', but chart places Saturn in House 11" in v for v in result.violations)


def test_violation_unknown_time_claiming_houses(sample_unknown_time_chart):
    raw_response = json.dumps({
        "answer": "Jupiter is placed in the 7th house granting spiritual partnership [F07].",
        "cited_fact_ids": ["F07"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_unknown_time_chart)
    assert result.is_valid is False
    assert any("Unknown birth time violation" in v for v in result.violations)


def test_violation_hallucinated_dasha_lord(sample_known_chart):
    raw_response = json.dumps({
        "answer": "You are currently running the Mahadasha of Rahu [F12].",
        "cited_fact_ids": ["F12"],
        "claims": [],
    })
    result = AnswerValidator.validate(raw_response, sample_known_chart)
    assert result.is_valid is False
    assert any("Claims current Mahadasha is 'Rahu', but computed chart is 'Mars'" in v for v in result.violations)


def test_safe_templated_fallback_passes_validation(sample_known_chart, sample_unknown_time_chart):
    # Test on known chart
    career_fallback = build_safe_templated_answer(sample_known_chart, "What are my career prospects?")
    raw_career = json.dumps(career_fallback)
    result_career = AnswerValidator.validate(raw_career, sample_known_chart)
    assert result_career.is_valid is True
    assert len(result_career.violations) == 0

    # Test on unknown time chart
    rel_fallback = build_safe_templated_answer(sample_unknown_time_chart, "Tell me about my marriage.")
    raw_rel = json.dumps(rel_fallback)
    result_rel = AnswerValidator.validate(raw_rel, sample_unknown_time_chart)
    assert result_rel.is_valid is True
    assert len(result_rel.violations) == 0
