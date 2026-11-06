"""Unit tests for Section A (Past Check Engine) and Section D (Test Requirements)."""

from datetime import date, datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import BirthProfile, PastCheckItem, PastCheckSet
from backend.past_check import (
    ALLOWED_THEMES,
    FORBIDDEN_THEMES,
    build_statement_text,
    compute_chart_hash,
    generate_candidate_events,
    get_or_assign_experiment_arm,
    get_or_create_past_check_set,
    record_past_check_answer,
    select_past_check_statements,
)


@pytest.fixture
def db():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_profile():
    return BirthProfile(
        id="prof-1",
        user_id="user-treat-1",
        name="Akshat",
        birth_date=date(1995, 5, 24),
        birth_time="14:15",
        time_known=True,
        latitude=19.0760,
        longitude=72.8777,
        timezone_str="Asia/Kolkata",
    )


def test_arm_assignment_is_stable(db):
    """Arm assignment (control vs treatment) is stable across repeated calls."""
    arm1 = get_or_assign_experiment_arm(db, "user-stable-123")
    arm2 = get_or_assign_experiment_arm(db, "user-stable-123")
    assert arm1 in ["control", "treatment"]
    assert arm1 == arm2


def test_statement_generation_is_deterministic(sample_profile):
    """Candidate event extraction is deterministic for the exact same birth chart."""
    cands1 = generate_candidate_events(sample_profile, today=date(2026, 11, 1))
    cands2 = generate_candidate_events(sample_profile, today=date(2026, 11, 1))

    assert len(cands1) > 0
    assert len(cands1) == len(cands2)
    for c1, c2 in zip(cands1, cands2):
        assert c1["fact_id"] == c2["fact_id"]
        assert c1["event_date"] == c2["event_date"]
        assert c1["theme"] == c2["theme"]


def test_excluded_themes_never_appear(sample_profile):
    """Excluded themes (health, death, trauma, legal, pregnancy) strictly never appear."""
    candidates = generate_candidate_events(sample_profile, today=date(2026, 11, 1))
    statements, _ = select_past_check_statements(candidates, sample_profile.user_id, today=date(2026, 11, 1))

    for item in statements:
        assert item["theme"] in ALLOWED_THEMES, f"Theme '{item['theme']}' is not in allowed themes!"
        for bad in FORBIDDEN_THEMES:
            assert bad not in item["theme"].lower()
            assert bad not in item["text_en"].lower()
            assert bad not in item["text_hi"].lower()


def test_decoy_window_contains_no_trigger_event(sample_profile):
    """Decoy event window contains no real trigger event within +/- 120 days."""
    candidates = generate_candidate_events(sample_profile, today=date(2026, 11, 1))

    # Force a seed that triggers decoy
    # We test with a user_id that triggers has_decoy
    found_decoy_test = False
    for i in range(50):
        test_uid = f"user_test_decoy_{i}"
        stmts, has_decoy = select_past_check_statements(candidates, test_uid, today=date(2026, 11, 1))
        if has_decoy:
            decoy = next((s for s in stmts if s["is_decoy"]), None)
            assert decoy is not None
            assert decoy["fact_id"] == "DECOY_CONTROL_WINDOW"
            # Verify no candidate trigger event occurred within +/- 120 days
            all_dates = [c["event_date"] for c in candidates]
            assert all(abs((decoy["event_date"] - ed).days) > 120 for ed in all_dates)
            found_decoy_test = True
            break

    assert found_decoy_test, "Should generate a decoy in 50 test iterations"


def test_is_decoy_never_present_in_api_response(db, sample_profile):
    """CRITICAL PRIVACY CHECK: is_decoy is never sent in the client API response."""
    # Force treatment arm
    from backend.models import Experiment
    db.add(Experiment(user_id=sample_profile.user_id, arm="treatment"))
    db.commit()

    res = get_or_create_past_check_set(db, sample_profile.user_id, sample_profile, lang="en")
    assert res["should_show"] is True
    assert "statements" in res

    for stmt in res["statements"]:
        assert "is_decoy" not in stmt, "LEAK: 'is_decoy' was exposed in client statement payload!"
        assert "statement" in stmt
        assert "theme" in stmt
        assert "event_date" in stmt


def test_answering_is_idempotent_upsert(db, sample_profile):
    """Answering a statement is an idempotent upsert and updates progress."""
    from backend.models import Experiment
    db.add(Experiment(user_id=sample_profile.user_id, arm="treatment"))
    db.commit()

    res = get_or_create_past_check_set(db, sample_profile.user_id, sample_profile, lang="en")
    first_item_id = res["statements"][0]["id"]

    # 1. Answer 'yes'
    ans1 = record_past_check_answer(db, sample_profile.user_id, first_item_id, "yes")
    assert ans1["status"] == "recorded"
    assert ans1["answer"] == "yes"
    assert ans1["recognized_count"] == 1

    # 2. Update answer to 'not_really' (idempotent upsert)
    ans2 = record_past_check_answer(db, sample_profile.user_id, first_item_id, "not_really")
    assert ans2["status"] == "recorded"
    assert ans2["answer"] == "not_really"
    assert ans2["recognized_count"] == 0


def test_wilson_score_interval_matches_hand_calc():
    """Wilson 95% confidence interval matches standard textbook values."""
    from backend.past_check_metrics import format_rate_with_ci, wilson_score_interval

    # 1. 50/100 -> [0.4038, 0.5962] -> 40.4% to 59.6%
    p_hat, low, high = wilson_score_interval(50, 100)
    assert p_hat == 0.5
    assert round(low, 3) == 0.404
    assert round(high, 3) == 0.596

    formatted = format_rate_with_ci(50, 100)
    assert "50.0% [95% CI: 40.4% – 59.6%, n=100]" in formatted

    # 2. Edge case: 0/0
    p0, l0, h0 = wilson_score_interval(0, 0)
    assert (p0, l0, h0) == (0.0, 0.0, 0.0)


def test_compute_past_check_experiment_metrics_structure(db, sample_profile):
    """Past Check experiment metrics calculates retention, decoys, delta, and small sample warning."""
    from backend.models import Experiment, Question, User
    from backend.past_check_metrics import compute_past_check_experiment_metrics

    # Create 1 control user and 1 treatment user
    u_ctrl = User(id="user_ctrl_1", name="Ctrl", email="ctrl@example.com")
    u_treat = User(id="user_treat_1", name="Treat", email="treat@example.com")
    db.add_all([u_ctrl, u_treat])
    db.add(Experiment(user_id="user_ctrl_1", arm="control"))
    db.add(Experiment(user_id="user_treat_1", arm="treatment"))

    # Add questions
    q1 = Question(id="q1", user_id="user_ctrl_1", birth_profile_id=sample_profile.id, question_text="Q1", status="answered", idempotency_key="k1")
    q2 = Question(id="q2", user_id="user_treat_1", birth_profile_id=sample_profile.id, question_text="Q2", status="answered", idempotency_key="k2")
    q3 = Question(id="q3", user_id="user_treat_1", birth_profile_id=sample_profile.id, question_text="Q3", status="answered", idempotency_key="k3")
    db.add_all([q1, q2, q3])
    db.commit()

    metrics = compute_past_check_experiment_metrics(db)
    assert "control_arm" in metrics
    assert "treatment_arm" in metrics
    assert "delta" in metrics
    assert "decoy_analysis" in metrics
    assert "completion" in metrics

    # Verify small sample warnings trigger below n = 30
    assert metrics["control_arm"]["is_small_sample"] is True
    assert metrics["treatment_arm"]["is_small_sample"] is True

    # Treatment user asked 2 questions -> 100% conversion in treatment arm
    assert metrics["treatment_arm"]["converted_count"] == 1
    assert metrics["treatment_arm"]["sample_size"] == 1

    # Control user asked 1 question -> 0% conversion in control arm
    assert metrics["control_arm"]["converted_count"] == 0
    assert metrics["control_arm"]["sample_size"] == 1

    # Format never shows a bare percentage
    assert "[95% CI:" in metrics["control_arm"]["formatted"]
    assert "[95% CI:" in metrics["treatment_arm"]["formatted"]
