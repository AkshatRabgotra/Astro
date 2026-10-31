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


class DemoAstrologyProvider:
    """Offline deterministic provider that generates grounded Vedic readings when no API keys are configured."""

    def generate(self, prompt: str, system_prompt: str) -> str:
        # Extract user question
        question = ""
        if "USER QUESTION:" in prompt:
            parts = prompt.split("USER QUESTION:")
            question = parts[1].split('"""')[0].split("\n\n")[0].strip(' "\n')

        q_lower = question.lower()
        is_career = any(w in q_lower for w in ["career", "job", "work", "business", "money", "finances", "success", "exam", "strongest", "period"])
        is_relationship = any(w in q_lower for w in ["love", "marriage", "partner", "relationship", "spouse"])
        is_timing = any(w in q_lower for w in ["when", "timing", "period", "future", "date", "year"])

        # Parse facts from prompt text
        facts = {}
        for line in prompt.split("\n"):
            line = line.strip()
            if line.startswith("F") and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    facts[parts[0]] = line

        cited_ids = []
        paragraphs = []

        # Ascendant / Foundation
        if "F01" in facts and "Unavailable" not in facts["F01"]:
            f01_text = facts["F01"]
            sign = "your calculated sign"
            for s in ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]:
                if s in f01_text:
                    sign = s
                    break
            paragraphs.append(f"### Astrological Foundation\nYour birth chart is anchored with **{sign} Lagna in House 1 [F01]**. This ascendant defines your natural constitutional rhythm, intellectual discernment, and strategic agency in navigating worldly milestones.")
            cited_ids.append("F01")
        else:
            paragraphs.append("### Astrological Foundation\nAs your exact birth time was not provided, houses and exact Ascendant are strictly reserved to prevent ungrounded predictions. We examine planetary sign dignity and planetary periods (Dasha).")

        # Career / Life theme
        if is_career or is_timing:
            paragraphs.append("### Career & Professional Timing\nLooking into your primary career significators:")
            if "F03" in facts:
                paragraphs.append("- **Sun's Authority [F03]**: The Sun governs professional authority, recognition, and purpose. In your sidereal placement, it acts as an anchor for leadership and individual autonomy.")
                cited_ids.append("F03")
            if "F09" in facts:
                paragraphs.append("- **Saturn's Perseverance [F09]**: Saturn governs sustained hard work, discipline, and long-term vocational foundations. It rewards patient execution and steady growth rather than impulsive shifts.")
                cited_ids.append("F09")
            if "F07" in facts:
                paragraphs.append("- **Jupiter's Expansion [F07]**: Guru brings wisdom, mentorship, and opportunities for ethical advancement in professional pursuits.")
                cited_ids.append("F07")
        elif is_relationship:
            paragraphs.append("### Relational Harmony & Partnerships\nExamining your relational significators:")
            if "F08" in facts:
                paragraphs.append("- **Venus Harmony [F08]**: Venus represents harmony, empathy, and personal bonding, indicating how you balance mutual respect and compromise.")
                cited_ids.append("F08")
            if "F04" in facts:
                paragraphs.append("- **Moon's Intuitive Heart [F04]**: Placed in your birth chart, the Moon shapes your emotional baseline and receptivity in deep bonds.")
                cited_ids.append("F04")
                if "F02" in facts:
                    cited_ids.append("F02")
        else:
            paragraphs.append("### Planetary Overview\nYour cosmic alignment highlights:")
            if "F04" in facts:
                paragraphs.append("- **Moon & Mind [F04]**: Governs intuition, mental peace, and inner fulfillment.")
                cited_ids.append("F04")
            if "F03" in facts:
                paragraphs.append("- **Sun & Vitality [F03]**: Shapes your outward purpose and vitality.")
                cited_ids.append("F03")

        # Dasha Timing
        dasha_fact = None
        for fid in ["F12", "F11", "F13", "F10"]:
            if fid in facts:
                dasha_fact = fid
                break
        if dasha_fact:
            paragraphs.append(f"### Vimshottari Dasha Current Cycle [{dasha_fact}]\nYour active planetary period provides the overarching karmic focus for this chapter of life. Major shifts unfold as planetary transits activate these specific planetary lords.")
            cited_ids.append(dasha_fact)

        paragraphs.append("\n*Note: Vedic astrology offers symbolic timing and self-awareness to support conscious decision-making rather than fatalistic certainty.*")

        answer_text = "\n\n".join(paragraphs)
        return json.dumps({
            "answer": answer_text,
            "cited_fact_ids": cited_ids,
            "claims": [{"claim": "Grounded chart analysis", "fact_id": fid} for fid in cited_ids],
        })


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
        1. If no API keys are set in environment, seamlessly serve reading via Grounded Vedic Demo Engine.
        2. Try Gemini if circuit allows.
        3. If Gemini fails or circuit is open, failover to Groq.
        4. If both fail, raise AllProvidersFailedError with friendly message.
        """
        gemini_key = getattr(self.gemini, "api_key", None)
        groq_key = getattr(self.groq, "api_key", None)
        has_gemini_key = bool(gemini_key and not str(gemini_key).startswith("your_"))
        has_groq_key = bool(groq_key and not str(groq_key).startswith("your_"))
        is_mock = "Mock" in type(self.gemini).__name__ or "Mock" in type(self.groq).__name__

        if not is_mock and not has_gemini_key and not has_groq_key and getattr(settings, "ENABLE_OFFLINE_DEMO", True):
            logger.info("No LLM API keys configured in .env. Serving reading via Grounded Vedic Demo Engine.")
            demo = DemoAstrologyProvider()
            raw_json = demo.generate(prompt=prompt, system_prompt=system_prompt)
            return LLMResponse(
                content=raw_json,
                provider="vedic_engine (demo)",
                duration_ms=15.0,
                is_fallback=False,
            )

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
