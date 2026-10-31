"""Unit tests for LLM Provider failover (Gemini -> Groq) and Circuit Breaker."""

import json
from unittest.mock import MagicMock
import pytest

from llm.circuit_breaker import CircuitBreaker, CircuitState
from llm.client import (
    AllProvidersFailedError,
    GeminiProvider,
    GroqProvider,
    ModelOrchestrator,
)


def test_circuit_breaker_transitions():
    cb = CircuitBreaker("test_cb", failure_threshold=2, recovery_timeout_seconds=0.1)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

    # First failure: still closed
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

    # Second failure: trips to OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

    # Wait for recovery timeout
    import time
    time.sleep(0.12)

    # After recovery timeout: allows trial request and moves to HALF_OPEN
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success in half open restores CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_orchestrator_gemini_primary_success():
    mock_gemini = MagicMock(spec=GeminiProvider)
    mock_gemini.generate.return_value = json.dumps({
        "answer": "Grounded answer from Gemini",
        "cited_fact_ids": ["F01"],
        "claims": [],
    })
    mock_groq = MagicMock(spec=GroqProvider)

    orchestrator = ModelOrchestrator(gemini_provider=mock_gemini, groq_provider=mock_groq)
    resp = orchestrator.generate(prompt="prompt", system_prompt="sys")

    assert resp.provider == "gemini"
    assert resp.is_fallback is False
    assert "Gemini" in resp.content
    mock_gemini.generate.assert_called_once()
    mock_groq.generate.assert_not_called()


def test_orchestrator_gemini_fails_falls_back_to_groq():
    """Verify that when Gemini raises an error (e.g. 429), it automatically fails over to Groq."""
    mock_gemini = MagicMock(spec=GeminiProvider)
    mock_gemini.generate.side_effect = RuntimeError("HTTP 429: Resource exhausted")

    mock_groq = MagicMock(spec=GroqProvider)
    mock_groq.generate.return_value = json.dumps({
        "answer": "Resilient answer from Groq fallback",
        "cited_fact_ids": ["F01"],
        "claims": [],
    })

    orchestrator = ModelOrchestrator(gemini_provider=mock_gemini, groq_provider=mock_groq)
    resp = orchestrator.generate(prompt="prompt", system_prompt="sys")

    assert resp.provider == "groq"
    assert resp.is_fallback is True
    assert "Groq fallback" in resp.content

    mock_gemini.generate.assert_called_once()
    mock_groq.generate.assert_called_once()
    assert orchestrator.gemini_circuit.failure_count == 1
    assert orchestrator.groq_circuit.failure_count == 0


def test_circuit_breaker_skips_failing_gemini():
    """When Gemini circuit trips to OPEN after threshold failures, subsequent calls skip Gemini."""
    mock_gemini = MagicMock(spec=GeminiProvider)
    mock_gemini.generate.side_effect = RuntimeError("Connection timeout")

    mock_groq = MagicMock(spec=GroqProvider)
    mock_groq.generate.return_value = json.dumps({"answer": "Groq answer", "cited_fact_ids": [], "claims": []})

    orchestrator = ModelOrchestrator(
        gemini_provider=mock_gemini,
        groq_provider=mock_groq,
        circuit_failure_threshold=2,
    )

    # 1st failure
    orchestrator.generate("p", "s")
    assert orchestrator.gemini_circuit.state == CircuitState.CLOSED

    # 2nd failure -> trips circuit to OPEN
    orchestrator.generate("p", "s")
    assert orchestrator.gemini_circuit.state == CircuitState.OPEN

    # 3rd call -> Gemini must be skipped completely
    mock_gemini.generate.reset_mock()
    resp = orchestrator.generate("p", "s")

    assert resp.provider == "groq"
    mock_gemini.generate.assert_not_called()  # Gemini skipped because circuit is OPEN!


def test_orchestrator_both_providers_fail_friendly_error():
    """When both providers fail, user receives a friendly error instead of raw stack traces."""
    mock_gemini = MagicMock(spec=GeminiProvider)
    mock_gemini.generate.side_effect = RuntimeError("Gemini 503 Service Unavailable")

    mock_groq = MagicMock(spec=GroqProvider)
    mock_groq.generate.side_effect = RuntimeError("Groq 500 Internal Error")

    orchestrator = ModelOrchestrator(gemini_provider=mock_gemini, groq_provider=mock_groq)

    with pytest.raises(AllProvidersFailedError) as exc_info:
        orchestrator.generate("p", "s")

    err = exc_info.value
    assert "cosmic servers are experiencing high volume" in err.user_friendly_message
    assert "gemini" in err.provider_errors
    assert "groq" in err.provider_errors
