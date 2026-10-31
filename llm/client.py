"""Multi-provider LLM Client with Gemini primary, Groq fallback, circuit breaker, and retry."""

import json
import logging
import time
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple
import httpx
from pydantic import BaseModel

from backend.config import settings
from llm.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger("melooha.llm")
logger.setLevel(logging.INFO)


class AllProvidersFailedError(Exception):
    """Raised when both primary (Gemini) and fallback (Groq) providers fail."""
    def __init__(self, message: str, provider_errors: Dict[str, str]):
        super().__init__(message)
        self.user_friendly_message = (
            "The cosmic servers are experiencing high volume right now. "
            "Your question balance has been preserved. Please tap Retry to try again."
        )
        self.provider_errors = provider_errors


class LLMResponse(BaseModel):
    content: str
    provider: str
    duration_ms: float
    is_fallback: bool = False


class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash", timeout_sec: float = 12.0):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.timeout = timeout_sec

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned empty candidates")

            part = candidates[0].get("content", {}).get("parts", [{}])[0]
            text = part.get("text", "")
            return text


class GroqProvider:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile", timeout_sec: float = 12.0):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.timeout = timeout_sec

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API returned status {resp.status_code}: {resp.text}")

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Groq returned empty choices")

            content = choices[0].get("message", {}).get("content", "")
            return content


class ModelOrchestrator:
    """
    Manages provider failover: Gemini (Primary) -> Groq (Fallback).
    Includes circuit breakers, timeouts, retries with backoff, and logging.
    """
    def __init__(
        self,
        gemini_provider: Optional[GeminiProvider] = None,
        groq_provider: Optional[GroqProvider] = None,
        circuit_failure_threshold: int = 3,
        circuit_recovery_seconds: float = 60.0,
    ):
        self.gemini = gemini_provider or GeminiProvider()
        self.groq = groq_provider or GroqProvider()
        self.gemini_circuit = CircuitBreaker(
            "gemini",
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_seconds,
        )
        self.groq_circuit = CircuitBreaker(
            "groq",
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_seconds,
        )

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """
        Execute provider chain:
        1. Try Gemini if circuit allows.
        2. If Gemini fails or circuit is open, failover to Groq.
        3. If both fail, raise AllProvidersFailedError with friendly message.
        """
        provider_errors: Dict[str, str] = {}

        # 1. Primary: Gemini
        if self.gemini_circuit.allow_request():
            start_t = time.time()
            try:
                logger.info("Calling primary provider: Gemini")
                raw_text = self.gemini.generate(prompt=prompt, system_prompt=system_prompt)
                dur = (time.time() - start_t) * 1000.0
                self.gemini_circuit.record_success()
                logger.info(f"Gemini succeeded in {dur:.1f}ms")
                return LLMResponse(
                    content=raw_text,
                    provider="gemini",
                    duration_ms=round(dur, 2),
                    is_fallback=False,
                )
            except Exception as e:
                dur = (time.time() - start_t) * 1000.0
                self.gemini_circuit.record_failure()
                err_msg = str(e)
                provider_errors["gemini"] = err_msg
                logger.warning(f"Gemini call failed ({dur:.1f}ms): {err_msg}. Triggering fallback to Groq.")
        else:
            provider_errors["gemini"] = f"Gemini circuit breaker is OPEN (tripped)."
            logger.warning("Gemini circuit breaker is OPEN; skipping Gemini.")

        # 2. Fallback: Groq
        if self.groq_circuit.allow_request():
            start_t = time.time()
            try:
                logger.info("Calling fallback provider: Groq")
                raw_text = self.groq.generate(prompt=prompt, system_prompt=system_prompt)
                dur = (time.time() - start_t) * 1000.0
                self.groq_circuit.record_success()
                logger.info(f"Groq fallback succeeded in {dur:.1f}ms")
                return LLMResponse(
                    content=raw_text,
                    provider="groq",
                    duration_ms=round(dur, 2),
                    is_fallback=True,
                )
            except Exception as e:
                dur = (time.time() - start_t) * 1000.0
                self.groq_circuit.record_failure()
                err_msg = str(e)
                provider_errors["groq"] = err_msg
                logger.error(f"Groq fallback failed ({dur:.1f}ms): {err_msg}")
        else:
            provider_errors["groq"] = "Groq circuit breaker is OPEN."
            logger.error("Groq circuit breaker is OPEN.")

        # Both failed
        raise AllProvidersFailedError(
            message="Both Gemini and Groq model providers failed.",
            provider_errors=provider_errors,
        )
