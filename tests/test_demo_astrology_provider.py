"""Unit tests for DemoAstrologyProvider ensuring rich, grounded astrological readings."""

import json
import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chart.engine import calculate_chart_facts
from chart.models import BirthInput
from llm.client import DemoAstrologyProvider
from llm.prompts import build_reading_prompt
from llm.validator import AnswerValidator
from backend.database import Base
from backend.models import BalanceLedger, Event, User
from backend.rewards import get_user_reward_state, claim_streak_reward


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_demo_astrology_provider_career_known_time():
    b = BirthInput(
        birth_date="1990-05-15",
        birth_time="14:30",
        latitude=28.6139,
        longitude=77.2090,
        place_name="New Delhi",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "whats my career best fit", user_name="Akshat")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "answer" in data
    assert len(data["answer"]) > 200
    assert "Namaste Akshat," in data["answer"]
    assert "Direct Answer & Best-Fit Career Path" in data["answer"]
    assert "Key Astrological Drivers" in data["answer"]
    assert "F01" in data["cited_fact_ids"]
    assert "F03" in data["cited_fact_ids"]
    assert "F09" in data["cited_fact_ids"]
    assert "F12" in data["cited_fact_ids"]

    # Strict grounding validation
    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_demo_astrology_provider_career_unknown_time():
    b = BirthInput(
        birth_date="1990-05-15",
        birth_time=None,
        latitude=28.6139,
        longitude=77.2090,
        place_name="New Delhi",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "whats my career best fit")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "answer" in data
    assert len(data["answer"]) > 200
    assert "Direct Answer & Best-Fit Career Path" in data["answer"]
    assert "F01" not in data["cited_fact_ids"]  # F01 is unavailable without birth time
    assert "F03" in data["cited_fact_ids"]

    # Strict grounding validation (no house claims allowed without birth time)
    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_demo_astrology_provider_relationship():
    b = BirthInput(
        birth_date="1990-05-15",
        birth_time="14:30",
        latitude=28.6139,
        longitude=77.2090,
        place_name="New Delhi",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "When will I get married?")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "F08" in data["cited_fact_ids"]
    assert "F04" in data["cited_fact_ids"]
    assert "F12" in data["cited_fact_ids"]

    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_demo_astrology_provider_timing():
    b = BirthInput(
        birth_date="1990-05-15",
        birth_time="14:30",
        latitude=28.6139,
        longitude=77.2090,
        place_name="New Delhi",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "When is my next favorable time period?")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "F12" in data["cited_fact_ids"]
    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_demo_astrology_provider_hindi_remedies():
    b = BirthInput(
        birth_date="2002-08-27",
        birth_time="21:30",
        latitude=32.7266,
        longitude=74.8570,
        place_name="Jammu",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "क्या उपाय इस ऊर्जा को संतुलित करते हैं?", user_name="राहुल")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "नमस्ते राहुल," in data["answer"]
    assert "ज्योतिषीय आधार" in data["answer"]
    assert "ऊर्जा संतुलन एवं वैदिक उपाय" in data["answer"]
    assert "सूर्य" in data["answer"]
    assert "F03" in data["cited_fact_ids"]
    assert "F12" in data["cited_fact_ids"]

    # Verify no English headers leaked
    assert "Astrological Foundation" not in data["answer"]
    assert "Direct Answer" not in data["answer"]

    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_demo_astrology_provider_hindi_career():
    b = BirthInput(
        birth_date="2002-08-27",
        birth_time="21:30",
        latitude=32.7266,
        longitude=74.8570,
        place_name="Jammu",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    prompt = build_reading_prompt(chart, "मेरा करियर कैसा रहेगा और कौन सा क्षेत्र सर्वोत्तम है?", user_name="अमित")

    provider = DemoAstrologyProvider()
    raw_response = provider.generate(prompt=prompt, system_prompt="")
    data = json.loads(raw_response)

    assert "नमस्ते अमित," in data["answer"]
    assert "प्रत्यक्ष उत्तर एवं सर्वोत्तम कार्यक्षेत्र" in data["answer"]
    assert "सूर्य" in data["answer"]
    assert "F03" in data["cited_fact_ids"]

    val = AnswerValidator.validate(raw_response, chart)
    assert val.is_valid is True, f"Violations: {val.violations}"


def test_bilingual_conversational_personalization_flow():
    b = BirthInput(
        birth_date="1995-05-24",
        birth_time="14:15",
        latitude=19.0760,
        longitude=72.8777,
        place_name="Mumbai",
        timezone_str="Asia/Kolkata",
    )
    chart = calculate_chart_facts(b)
    provider = DemoAstrologyProvider()

    # 1. Ask in English with user name "Priya"
    eng_prompt = build_reading_prompt(chart, "When is the best time for my job change?", user_name="Priya")
    eng_resp = provider.generate(prompt=eng_prompt, system_prompt="")
    eng_data = json.loads(eng_resp)
    assert "Namaste Priya," in eng_data["answer"]
    assert "Mahadasha" in eng_data["answer"] or "Dasha" in eng_data["answer"]
    assert "F12" in eng_data["cited_fact_ids"]
    assert AnswerValidator.validate(eng_resp, chart).is_valid is True

    # 2. Ask in Hindi with user name "राहुल"
    hi_prompt = build_reading_prompt(chart, "मेरी कुंडली में करियर का सही समय कब है?", user_name="राहुल")
    hi_resp = provider.generate(prompt=hi_prompt, system_prompt="")
    hi_data = json.loads(hi_resp)
    assert "नमस्ते राहुल," in hi_data["answer"]
    assert "महादशा" in hi_data["answer"]
    assert "F12" in hi_data["cited_fact_ids"]
    assert AnswerValidator.validate(hi_resp, chart).is_valid is True

    # 3. Ask again in English -> Verify returns strictly English with new name "Arjun"
    eng_prompt2 = build_reading_prompt(chart, "Which career fits my leadership skills?", user_name="Arjun")
    eng_resp2 = provider.generate(prompt=eng_prompt2, system_prompt="")
    eng_data2 = json.loads(eng_resp2)
    assert "Namaste Arjun," in eng_data2["answer"]
    assert "नमस्ते" not in eng_data2["answer"]
    assert "F03" in eng_data2["cited_fact_ids"] or "F01" in eng_data2["cited_fact_ids"]
    assert AnswerValidator.validate(eng_resp2, chart).is_valid is True


def test_reward_streak_consecutive_days_logic(db):
    """Verify that streak increments only on strictly consecutive days, and resets to 1 if a day is skipped."""
    user = User(name="StreakUser")
    db.add(user)
    db.commit()

    profile_id = "prof_streak_1"
    today = datetime.now(timezone.utc).date()

    # Initial state: Day 1 claimable
    state = get_user_reward_state(db, user.id, profile_id=profile_id)
    assert state["streak_count"] == 1
    assert state["can_claim_today"] is True

    # Simulate Day 1 claim made yesterday
    yesterday = today - timedelta(days=1)
    evt_day1 = Event(
        user_id=user.id,
        event_name="streak_claimed",
        payload={"profile_id": profile_id, "day": 1, "coins": 5, "questions": 1, "date": yesterday.isoformat()},
        created_at=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc),
    )
    db.add(evt_day1)
    db.commit()

    # Consecutive day (today = yesterday + 1): streak advances to Day 2
    state2 = get_user_reward_state(db, user.id, profile_id=profile_id)
    assert state2["streak_count"] == 2
    assert state2["can_claim_today"] is True
    assert state2["streak_was_broken"] is False

    # Simulate claim made 3 days ago (skipping Day 2 and coming back on Day 4)
    db.query(Event).filter(Event.user_id == user.id).delete()
    three_days_ago = today - timedelta(days=3)
    evt_skipped = Event(
        user_id=user.id,
        event_name="streak_claimed",
        payload={"profile_id": profile_id, "day": 2, "coins": 7, "questions": 1, "date": three_days_ago.isoformat()},
        created_at=datetime.combine(three_days_ago, datetime.min.time(), tzinfo=timezone.utc),
    )
    db.add(evt_skipped)
    db.commit()

    # Day skipped -> Streak broken, resets to 1
    state_broken = get_user_reward_state(db, user.id, profile_id=profile_id)
    assert state_broken["streak_count"] == 1
    assert state_broken["can_claim_today"] is True
    assert state_broken["streak_was_broken"] is True
