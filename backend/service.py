"""Domain services for User Onboarding, Birth Chart Calculation, and Q&A."""

from datetime import date, datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.ledger import (
    InsufficientBalanceError,
    get_balance,
    grant_signup_credit,
    refund_question_credit,
    spend_question_credit,
    topup_credits,
)
from backend.models import (
    Answer,
    BalanceLedger,
    BirthProfile,
    Chart,
    Event,
    Question,
    User,
    generate_uuid,
)
from chart.engine import calculate_chart_facts
from chart.models import BirthInput, ChartFacts


class OnboardingService:
    @staticmethod
    def create_user_and_chart(
        db: Session,
        name: str,
        birth_date: date,
        latitude: float,
        longitude: float,
        timezone_str: str,
        birth_time: Optional[str] = None,
        time_known: bool = True,
        place_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Tuple[User, BirthProfile, Chart, ChartFacts]:
        """
        Create a new user, birth profile, grant +1 free credit, and compute & cache ChartFacts.
        """
        # 1. Create User
        user = User(name=name, email=email)
        db.add(user)
        db.flush()

        # 2. Grant initial free question credit (+1)
        grant_signup_credit(db, user.id)

        # 3. Create Birth Profile
        profile = BirthProfile(
            user_id=user.id,
            name=name,
            birth_date=birth_date,
            birth_time=birth_time if time_known else None,
            time_known=time_known,
            latitude=latitude,
            longitude=longitude,
            timezone_str=timezone_str,
            place_name=place_name,
        )
        db.add(profile)
        db.flush()

        # 4. Compute Chart using pure-Python engine
        birth_input = BirthInput(
            birth_date=birth_date,
            birth_time=birth_time,
            time_known=time_known,
            latitude=latitude,
            longitude=longitude,
            timezone_str=timezone_str,
            place_name=place_name,
        )
        chart_facts = calculate_chart_facts(birth_input)

        # 5. Cache Chart in database
        chart = Chart(
            birth_profile_id=profile.id,
            ayanamsa=chart_facts.ayanamsa_name,
            facts_json=json.loads(chart_facts.model_dump_json()),
        )
        db.add(chart)

        # 6. Log onboarding event
        event = Event(
            user_id=user.id,
            event_name="user_onboarded",
            payload={
                "has_birth_time": time_known,
                "place_name": place_name,
                "lagna": chart_facts.lagna_sign,
            },
        )
        db.add(event)

        db.commit()
        db.refresh(user)
        db.refresh(profile)
        db.refresh(chart)

        return user, profile, chart, chart_facts


class QuestionService:
    @staticmethod
    def ask_question(
        db: Session,
        user_id: str,
        birth_profile_id: str,
        question_text: str,
        idempotency_key: str,
    ) -> Question:
        """
        Initiate a question:
        - Check idempotency: if already created, return existing Question.
        - Spend 1 credit from balance atomically.
        - Create Question record in 'pending' status.
        - Log event.
        """
        # Idempotency check on question
        existing_q = db.query(Question).filter(Question.idempotency_key == idempotency_key).first()
        if existing_q:
            return existing_q

        # Verify birth profile belongs to user
        profile = db.query(BirthProfile).filter(
            BirthProfile.id == birth_profile_id,
            BirthProfile.user_id == user_id
        ).first()
        if not profile:
            raise ValueError("Birth profile not found or does not belong to user")

        question_id = generate_uuid()

        # Atomically spend 1 credit (raises InsufficientBalanceError if balance < 1)
        spend_question_credit(
            db=db,
            user_id=user_id,
            question_id=question_id,
            idempotency_key=f"spend_{idempotency_key}",
        )

        question = Question(
            id=question_id,
            user_id=user_id,
            birth_profile_id=birth_profile_id,
            question_text=question_text.strip(),
            status="pending",
            idempotency_key=idempotency_key,
        )
        db.add(question)

        # Track question asked event
        user_total_questions = db.query(Question).filter(Question.user_id == user_id).count()
        event_name = "second_question_asked" if user_total_questions == 1 else "question_asked"
        db.add(
            Event(
                user_id=user_id,
                event_name=event_name,
                payload={"question_id": question_id, "question_number": user_total_questions + 1},
            )
        )

        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def complete_question(
        db: Session,
        question_id: str,
        answer_text: str,
        cited_fact_ids: List[str],
        provider: str,
        is_verified: bool,
        verification_notes: Optional[str] = None,
    ) -> Answer:
        """Record completed and validated answer."""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError(f"Question {question_id} not found")

        answer = Answer(
            question_id=question_id,
            answer_text=answer_text,
            cited_fact_ids=cited_fact_ids,
            provider=provider,
            is_verified=is_verified,
            verification_notes=verification_notes,
        )
        db.add(answer)
        question.status = "completed"

        # Log event
        db.add(
            Event(
                user_id=question.user_id,
                event_name="answer_viewed",
                payload={
                    "question_id": question_id,
                    "provider": provider,
                    "cited_count": len(cited_fact_ids),
                    "is_verified": is_verified,
                },
            )
        )

        db.commit()
        db.refresh(answer)
        return answer

    @staticmethod
    def fail_and_refund(
        db: Session,
        question_id: str,
        reason: str = "Provider failure",
    ) -> bool:
        """Mark question as failed and issue automatic refund."""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False

        question.status = "failed"
        refunded = refund_question_credit(db, question.user_id, question_id, reason=reason)
        db.commit()
        return refunded
