"""Server-Sent Events (SSE) streaming engine for Grounded Q&A readings."""

import json
import time
from typing import Generator, Optional
from sqlalchemy.orm import Session

from backend.ledger import get_balance
from backend.models import Answer, BirthProfile, Chart, Question
from backend.service import QuestionService
from chart.models import ChartFacts
from llm.client import AllProvidersFailedError, ModelOrchestrator
from llm.fallback import build_safe_templated_answer, build_astro_references
from llm.prompts import SYSTEM_PROMPT, build_reading_prompt
from llm.validator import AnswerValidator, parse_llm_json


def sse_event(event_name: str, data: dict) -> str:
    """Format SSE payload."""
    return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"


def stream_question_answer(
    db: Session,
    question_id: str,
    orchestrator: Optional[ModelOrchestrator] = None,
) -> Generator[str, None, None]:
    """
    Generator yielding SSE events for reading generation, validation, and evidence verification.
    Handles streaming tokens, verification event, replace event on violation, and automatic refund.
    """
    if orchestrator is None:
        orchestrator = ModelOrchestrator()

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        yield sse_event("error", {"message": "Question not found", "refunded": False})
        return

    # Fetch cached chart facts
    chart = db.query(Chart).filter(Chart.birth_profile_id == question.birth_profile_id).first()
    if not chart:
        yield sse_event("error", {"message": "Birth chart not found", "refunded": False})
        return

    # Fetch member profile for personalized consultation
    profile = db.query(BirthProfile).filter(BirthProfile.id == question.birth_profile_id).first()
    user_name = profile.name if profile and profile.name else "Friend"

    chart_facts = ChartFacts.model_validate(chart.facts_json)

    # 1. Attempt generation via dual-provider orchestrator
    try:
        yield sse_event("status", {"state": "generating", "provider": "gemini", "message": "Consulting planetary positions..."})

        # Retrieve recent conversation turns for multi-turn follow-ups
        recent_qs = (
            db.query(Question)
            .filter(
                Question.user_id == question.user_id,
                Question.birth_profile_id == question.birth_profile_id,
                Question.status == "completed",
                Question.id != question.id,
            )
            .order_by(Question.created_at.desc())
            .limit(2)
            .all()
        )
        conversation_history = []
        for rq in reversed(recent_qs):
            ans = db.query(Answer).filter(Answer.question_id == rq.id).first()
            if ans and ans.answer_text:
                conversation_history.append({"user": rq.question_text, "assistant": ans.answer_text})

        prompt = build_reading_prompt(
            chart_facts=chart_facts,
            question=question.question_text,
            conversation_history=conversation_history,
            user_name=user_name,
        )
        resp = orchestrator.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        provider = resp.provider

        # Stream draft tokens to client for low perceived latency
        parsed_data, parse_err = parse_llm_json(resp.content)
        raw_answer_text = parsed_data.get("answer", resp.content) if parsed_data else resp.content

        # Stream words as tokens
        words = raw_answer_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield sse_event("token", {"token": token})
            time.sleep(0.015)  # Natural reading pacing (~40 tokens/sec)

        # 2. Run Grounding Validation in code
        val_result = AnswerValidator.validate(resp.content, chart_facts)

        if not val_result.is_valid:
            # Retry once with violations fed back
            yield sse_event("status", {"state": "validating", "message": "Grounding verification check in progress..."})
            retry_prompt = build_reading_prompt(
                chart_facts=chart_facts,
                question=question.question_text,
                previous_error="; ".join(val_result.violations),
                conversation_history=conversation_history,
                user_name=user_name,
            )
            try:
                retry_resp = orchestrator.generate(prompt=retry_prompt, system_prompt=SYSTEM_PROMPT)
                retry_val = AnswerValidator.validate(retry_resp.content, chart_facts)
                if retry_val.is_valid:
                    val_result = retry_val
                    resp = retry_resp
                    parsed_data, _ = parse_llm_json(retry_resp.content)
            except Exception:
                pass  # Proceed to safe fallback below

        # 3. Final event resolution
        if val_result.is_valid and parsed_data:
            # Valid reading: save answer and emit verified event
            final_answer_text = parsed_data.get("answer", raw_answer_text)
            cited_ids = parsed_data.get("cited_fact_ids", [])

            QuestionService.complete_question(
                db=db,
                question_id=question_id,
                answer_text=final_answer_text,
                cited_fact_ids=cited_ids,
                provider=provider,
                is_verified=True,
            )

            evidence = [
                {
                    "id": f.id,
                    "category": f.category,
                    "subject": f.subject,
                    "text": f.text,
                    "metadata": f.metadata,
                }
                for f in val_result.verified_cited_facts
            ]

            astro_refs = parsed_data.get("astro_references")
            if not astro_refs or not isinstance(astro_refs, list):
                astro_refs = build_astro_references(chart_facts, cited_ids, question.question_text)

            yield sse_event(
                "verified",
                {
                    "status": "completed",
                    "provider": provider,
                    "cited_facts": evidence,
                    "astro_references": astro_refs,
                },
            )

        else:
            # Grounding violation persisted: fall back to safe deterministic templated reading
            fallback = build_safe_templated_answer(chart_facts, question.question_text, user_name=user_name)
            fallback_text = fallback["answer"]
            fallback_ids = fallback["cited_fact_ids"]
            fallback_astro_refs = fallback.get("astro_references") or build_astro_references(chart_facts, fallback_ids, question.question_text)

            QuestionService.complete_question(
                db=db,
                question_id=question_id,
                answer_text=fallback_text,
                cited_fact_ids=fallback_ids,
                provider="template_fallback",
                is_verified=True,
                verification_notes="Replaced by safe grounded template after validation violation",
            )

            evidence = [
                {
                    "id": f.id,
                    "category": f.category,
                    "subject": f.subject,
                    "text": f.text,
                    "metadata": f.metadata,
                }
                for fid in fallback_ids
                if (f := chart_facts.get_fact(fid)) is not None
            ]

            yield sse_event(
                "replace",
                {
                    "status": "completed",
                    "provider": "template_fallback",
                    "answer": fallback_text,
                    "cited_facts": evidence,
                    "astro_references": fallback_astro_refs,
                    "reason": "Grounding verification correction applied",
                },
            )

    except Exception as e:
        # Automatic refund on failure
        QuestionService.fail_and_refund(db, question_id, reason=str(e))
        rem_balance = get_balance(db, question.user_id)
        friendly_msg = (
            "The cosmic connection was briefly interrupted. "
            "Your question credit has been automatically refunded. Please tap Retry to try again."
        )
        yield sse_event(
            "error",
            {
                "message": friendly_msg,
                "refunded": True,
                "balance": rem_balance,
            },
        )

    yield sse_event("end", {"done": True})
