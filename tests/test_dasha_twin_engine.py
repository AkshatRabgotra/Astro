"""Tests for Dasha Twin Dataset, Swiss Ephemeris calculations, and Matching Engine."""

from datetime import date, datetime
import json
import os
import pytest
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend.models import BirthProfile, FigureEvent, PublicFigure, EventDasha, User
from backend.seed_figures import seed_database_and_compute_dashas
from backend.twin_matcher import find_dasha_twin, get_user_current_dasha_lord
from chart.engine import calculate_chart_facts
from chart.models import BirthInput
from chart.dasha import calculate_vimshottari_periods


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database_and_compute_dashas()
    yield


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_dataset_integrity():
    """Verify data/figures.json contains 30 verified figures with Rodden rating A or AA."""
    assert os.path.exists("data/figures.json"), "data/figures.json must exist"
    with open("data/figures.json", "r", encoding="utf-8") as f:
        figures = json.load(f)

    assert len(figures) >= 30, f"Expected at least 30 figures, got {len(figures)}"

    total_events = 0
    for fig in figures:
        assert fig["verified"] is True, f"Figure {fig['id']} must be marked verified: true"
        assert fig["rodden_rating"] in ["AA", "A"], f"Figure {fig['id']} must have Rodden rating A or AA"
        assert fig["lat"] is not None and fig["lon"] is not None
        assert fig["timezone"]
        assert len(fig["events"]) >= 2, f"Figure {fig['id']} must have at least 2 events"
        assert len(fig["events"]) <= 4, f"Figure {fig['id']} must have at most 4 events"

        for ev in fig["events"]:
            total_events += 1
            assert ev["category"] in ["career", "creative", "achievement"]
            assert '"' not in ev["title"], f"Event title should not contain double quotes: {ev['title']}"
            assert ev["source_url"].startswith("http")

    assert total_events >= 60, f"Expected at least 60 events across dataset, got {total_events}"


def test_golden_dasha_reference_einstein():
    """Golden reference test: Albert Einstein (Ulm, 1879-03-14 11:30, Rodden AA)."""
    chart = calculate_chart_facts(
        BirthInput(
            name="Albert Einstein",
            birth_date="1879-03-14",
            birth_time="11:30",
            latitude=48.4011,
            longitude=9.9876,
            timezone_str="Europe/Berlin",
        )
    )
    moon = next(p for p in chart.planets if p.planet == "Moon")
    # Sidereal Moon in Scorpio (Jyeshtha nakshatra, lord Mercury)
    assert moon.sign == "Scorpio"
    assert moon.nakshatra.name == "Jyeshtha"
    assert moon.nakshatra.lord == "Mercury"

    # Annus Mirabilis (1905): Venus Mahadasha
    birth_dt = datetime(1879, 3, 14, 11, 30)
    dasha_1905, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=datetime(1905, 6, 9))
    assert dasha_1905.mahadasha_lord == "Venus"

    # Nobel Prize in Physics (1922): Moon Mahadasha (Sun ended March 1922)
    dasha_1922, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=datetime(1922, 11, 9))
    assert dasha_1922.mahadasha_lord == "Moon"


def test_golden_dasha_reference_jobs():
    """Golden reference test: Steve Jobs (San Francisco, 1955-02-24 19:15, Rodden AA)."""
    chart = calculate_chart_facts(
        BirthInput(
            name="Steve Jobs",
            birth_date="1955-02-24",
            birth_time="19:15",
            latitude=37.7749,
            longitude=-122.4194,
            timezone_str="America/Los_Angeles",
        )
    )
    moon = next(p for p in chart.planets if p.planet == "Moon")
    # Sidereal Moon in Pisces (Uttara Bhadrapada, lord Saturn)
    assert moon.sign == "Pisces"
    assert moon.nakshatra.name == "Uttara Bhadrapada"
    assert moon.nakshatra.lord == "Saturn"

    # Macintosh launch (1984): Venus Mahadasha
    birth_dt = datetime(1955, 2, 24, 19, 15)
    dasha_1984, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=datetime(1984, 1, 24))
    assert dasha_1984.mahadasha_lord == "Venus"

    # iPhone launch (2007): Sun Mahadasha
    dasha_2007, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=datetime(2007, 1, 9))
    assert dasha_2007.mahadasha_lord == "Sun"


def test_golden_dasha_reference_dilip_kumar():
    """Golden reference test matching user screenshot: Dilip Kumar (1922-12-11 10:00)."""
    chart = calculate_chart_facts(
        BirthInput(
            name="Dilip Kumar",
            birth_date="1922-12-11",
            birth_time="10:00",
            latitude=34.0151,
            longitude=71.5249,
            timezone_str="Asia/Karachi",
        )
    )
    moon = next(p for p in chart.planets if p.planet == "Moon")
    assert moon.sign == "Leo"
    assert moon.nakshatra.name == "Purva Phalguni"
    assert moon.nakshatra.lord == "Venus"

    # Andaz (1949): Moon Mahadasha exactly as shown in screenshot!
    birth_dt = datetime(1922, 12, 11, 10, 0)
    dasha_1949, _, _ = calculate_vimshottari_periods(moon.longitude, birth_dt, target_dt=datetime(1949, 3, 21))
    assert dasha_1949.mahadasha_lord == "Moon"


def test_matching_is_deterministic(db_session: Session):
    """Verify that same user and day returns the exact same card 100% of the time."""
    test_profile = BirthProfile(
        id="test-profile-1",
        user_id="test-user-1",
        name="Akshat",
        birth_date=date(1995, 8, 15),
        birth_time="14:30",
        time_known=True,
        latitude=28.6139,
        longitude=77.2090,
        timezone_str="Asia/Kolkata",
    )

    day1 = date(2026, 11, 1)

    result_a = find_dasha_twin(db_session, test_profile, target_date=day1, level="pratyantar")
    result_b = find_dasha_twin(db_session, test_profile, target_date=day1, level="pratyantar")

    assert result_a["match_type"] == result_b["match_type"]
    assert result_a["user_lord"] == result_b["user_lord"]
    assert result_a["user_level"] == result_b["user_level"]
    if result_a["figure"]:
        assert result_a["figure"]["id"] == result_b["figure"]["id"]
        assert result_a["event"]["id"] == result_b["event"]["id"]


def test_unknown_birth_time_fallback(db_session: Session):
    """When birth time is unknown, forces level='mahadasha' and marks is_approximate=True."""
    approx_profile = BirthProfile(
        id="test-profile-approx",
        user_id="test-user-approx",
        name="Unknown Time User",
        birth_date=date(1990, 5, 20),
        birth_time=None,
        time_known=False,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )

    result = find_dasha_twin(db_session, approx_profile, target_date=date(2026, 11, 1), level="pratyantar")
    assert result["is_approximate"] is True
    assert result["user_level"] == "mahadasha"


def test_validator_enforces_word_count():
    """Validator rejects copy over 60 words."""
    from backend.twin_copy import validate_twin_copy

    dummy_data = {
        "event": {"event_date": "1949-03-21"},
        "figure": {"display_name": "Dilip Kumar"}
    }
    long_body = "word " * 65
    is_valid, err = validate_twin_copy({"headline": "Test", "body": long_body}, dummy_data)
    assert is_valid is False
    assert "exceeds 60 words" in err


def test_validator_rejects_predictive_claims():
    """Validator rejects claims predicting the user's future."""
    from backend.twin_copy import validate_twin_copy

    dummy_data = {
        "event": {"event_date": "1949-03-21"},
        "figure": {"display_name": "Dilip Kumar"}
    }
    pred_body = "During this phase you will achieve unprecedented wealth and fame."
    is_valid, err = validate_twin_copy({"headline": "Test", "body": pred_body}, dummy_data)
    assert is_valid is False
    assert "predictive" in err.lower()


def test_validator_rejects_causal_astrology_claims():
    """Validator rejects deterministic causal claims (e.g. because of the Moon)."""
    from backend.twin_copy import validate_twin_copy

    dummy_data = {
        "event": {"event_date": "1949-03-21"},
        "figure": {"display_name": "Dilip Kumar"}
    }
    causal_body = "This milestone occurred because of the Moon forcing greatness."
    is_valid, err = validate_twin_copy({"headline": "Test", "body": causal_body}, dummy_data)
    assert is_valid is False
    assert "causal" in err.lower()


def test_validator_rejects_invented_dates():
    """Validator rejects unauthorized years not matching the milestone."""
    from backend.twin_copy import validate_twin_copy

    dummy_data = {
        "event": {"event_date": "1949-03-21"},
        "figure": {"display_name": "Dilip Kumar"}
    }
    invented_date_body = "Dilip Kumar established his breakthrough in 1988 with immense grace."
    is_valid, err = validate_twin_copy({"headline": "Test", "body": invented_date_body}, dummy_data)
    assert is_valid is False
    assert "unauthorized year" in err.lower()


def test_fixed_template_validity_and_multilingual():
    """Fixed fallback template complies with word limit and grounding in English and Hindi."""
    from backend.twin_copy import get_fixed_template_copy, validate_twin_copy

    twin_data = {
        "user_lord": "Moon",
        "user_level": "pratyantar",
        "figure": {"display_name": "Dilip Kumar", "field": "Actor"},
        "event": {
            "title": "Starred in Andaz alongside Raj Kapoor and Nargis",
            "event_date": "1949-03-21",
            "source_url": "https://en.wikipedia.org/wiki/Andaz_(1949_film)"
        }
    }

    # English template
    en_copy = get_fixed_template_copy(twin_data, lang="en")
    is_valid_en, err_en = validate_twin_copy(en_copy, twin_data)
    assert is_valid_en is True, f"English fallback template failed validation: {err_en}"
    assert len(en_copy["body"].split()) <= 60
    assert "For reflection and fun, not prediction." in en_copy["disclaimer"]

    # Hindi template
    hi_copy = get_fixed_template_copy(twin_data, lang="hi")
    assert len(hi_copy["body"].split()) <= 60
    assert "भविष्यवाणी नहीं" in hi_copy["disclaimer"]


def test_public_share_payload_has_no_birth_data(db_session: Session):
    """The public share payload strictly never contains birth details."""
    from fastapi import BackgroundTasks
    from backend.twin_router import CreateShareRequest, create_share_snapshot, get_share_data

    bg = BackgroundTasks()
    req = CreateShareRequest(
        user_id="test-user-privacy",
        headline="Your Pratyantar, their Mahadasha",
        body="Dilip Kumar starred in Andaz alongside Raj Kapoor and Nargis.",
        figure_name="Dilip Kumar",
        figure_field="Actor",
        lord="Moon",
        theme="Moon",
        include_first_name=False,
        source_url="https://en.wikipedia.org/wiki/Andaz_(1949_film)",
    )

    class DummyRequest:
        client = None

    share_res = create_share_snapshot(req=req, background_tasks=bg, request=DummyRequest(), db=db_session)
    token = share_res["token"]
    assert len(token) == 32  # 128-bit hex token

    # Check public JSON data
    public_data = get_share_data(token=token, db=db_session)

    # CRITICAL: Verify NO birth data exists in payload
    forbidden_keys = ["birth_date", "birth_time", "latitude", "longitude", "timezone_str", "facts", "planets"]
    for key in forbidden_keys:
        assert key not in public_data, f"Forbidden privacy leak: '{key}' found in public share payload!"


def test_image_generation_idempotency_and_revoke_404(db_session: Session):
    """Image generation is idempotent, and revoked tokens return 404."""
    from fastapi import BackgroundTasks, HTTPException
    from backend.twin_router import CreateShareRequest, create_share_snapshot, get_share_data, revoke_share
    from backend.twin_image_generator import render_twin_card_images

    # 1. Test image generator idempotency
    token = "test-idem-token-999"
    c1, s1 = render_twin_card_images(
        token=token,
        headline="Test Headline",
        body="Test Body paragraph for reflection.",
        figure_name="Albert Einstein",
        figure_field="Scientist",
        lord="Sun",
    )
    c2, s2 = render_twin_card_images(
        token=token,
        headline="Test Headline",
        body="Test Body paragraph for reflection.",
        figure_name="Albert Einstein",
        figure_field="Scientist",
        lord="Sun",
    )
    assert c1 == c2 and os.path.exists(c1)
    assert s1 == s2 and os.path.exists(s1)

    # 2. Test Revocation returns 404
    bg = BackgroundTasks()
    req = CreateShareRequest(
        user_id="test-user-revoke",
        headline="Will Be Revoked",
        body="Snapshot body text.",
        figure_name="Steve Jobs",
        figure_field="Entrepreneur",
        lord="Venus",
    )
    create_res = create_share_snapshot(req=req, background_tasks=bg, request=None, db=db_session)
    rev_token = create_res["token"]

    # Verify active first
    active_data = get_share_data(token=rev_token, db=db_session)
    assert active_data["headline"] == "Will Be Revoked"

    # Revoke
    revoke_res = revoke_share(token=rev_token, db=db_session)
    assert revoke_res["status"] == "revoked"

    # Subsequent access MUST raise 404
    with pytest.raises(HTTPException) as excinfo:
        get_share_data(token=rev_token, db=db_session)
    assert excinfo.value.status_code == 404



