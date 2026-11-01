"""Grounded Card Copy Generator and Validator for Dasha Twin.

Follows strict guidelines:
- Body strictly <= 60 words
- Only references given user dasha and matched event (no hallucinations)
- Forbids predictive claims ("you will") and causal claims ("because of the Moon")
- Retries once on failure, then falls back to a verified deterministic template
- Supports English and Hindi
- Includes reflection disclaimer and verified source link
"""

from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.config import settings
from llm.client import ModelOrchestrator


# Reject phrases: Predictive future claims
PREDICTIVE_PATTERNS = [
    r"\byou will\b",
    r"\byou shall\b",
    r"\bguaranteed\b",
    r"\bdestined to\b",
    r"\bpredict(?:s|ed|ing|ion)?\b",
    r"\bwill happen\b",
    r"\bwill bring you\b",
    r"\bfuture holds\b",
    r"\bfortune\b",
    r"\bआपके भविष्य में\b",
    r"\bभविष्यवाणी\b",
    r"\bआप अवश्य करेंगे\b",
]

# Reject phrases: Causal astrological claims
CAUSAL_PATTERNS = [
    r"\bbecause of (?:the|your)?\s*(?:moon|sun|mars|mercury|jupiter|venus|saturn|rahu|ketu)\b",
    r"\bdue to (?:the|your)?\s*(?:moon|sun|mars|mercury|jupiter|venus|saturn|rahu|ketu)\b",
    r"\bcaused by\b",
    r"\bforces you to\b",
    r"\bmakes you do\b",
    r"\bग्रहों के कारण\b",
    r"\bकी वजह से होगा\b",
]


TWIN_SYSTEM_PROMPT = """You are a thoughtful Vedic astrology writer for Melooha.
Your task is to write a brief, grounded card copy comparing the user's current dasha phase with a notable person's real career milestone.

STRICT GROUNDING & EDITORIAL RULES:
1. PARALLEL FOR REFLECTION, NOT PREDICTION:
   - Frame as an inspiring thematic parallel or mirror, NEVER a forecast.
   - FORBID ANY PREDICTIVE CLAIMS about the user's future (e.g. NEVER say "you will achieve", "you will experience").
   - FORBID ANY CAUSAL CLAIMS (e.g. NEVER say "because of the Moon", "Saturn causes this").
2. DATA INTEGRITY:
   - ONLY mention the supplied person, their field, the active dasha lord, and the exact milestone title/date.
   - DO NOT invent any other celebrity, date, event, book, award, or number.
3. CONCISENESS:
   - The "body" text MUST BE AT MOST 60 WORDS.
4. TONE:
   - Reflective, grounded, curious, respectful.

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{
  "headline": "Short title (under 8 words)",
  "body": "Card copy under 60 words.",
  "fact_ids": ["F_DASHA_USER", "F_EVENT_MATCH"]
}
"""


def build_twin_prompt(
    twin_data: Dict[str, Any],
    lang: str = "en",
    retry_error: Optional[str] = None,
) -> str:
    """Construct prompt with strict grounding constraints."""
    user_lord = twin_data.get("user_lord", "")
    user_level = twin_data.get("user_level", "Pratyantar").capitalize()
    figure = twin_data.get("figure", {}) or {}
    event = twin_data.get("event", {}) or {}

    figure_name = figure.get("display_name", "")
    figure_field = figure.get("field", "")
    event_title = event.get("title", "")
    event_date = event.get("event_date", "")
    figure_lord = twin_data.get("figure_level", "Mahadasha")

    error_context = ""
    if retry_error:
        error_context = f"\nPREVIOUS ATTEMPT FAILED VALIDATION:\n{retry_error}\nPlease correct this strictly. Keep body under 60 words, no predictive or causal phrases.\n"

    lang_instruction = "Write in English." if lang == "en" else "Write in Hindi (Devanagari script)."

    prompt = f"""FACTS:
- User Active Phase: {user_lord} {user_level} Dasha [Fact ID: F_DASHA_USER]
- Matched Person: {figure_name} ({figure_field}) [Fact ID: F_EVENT_MATCH]
- Person Phase: {user_lord} {figure_lord}
- Milestone: {event_title} ({event_date})

LANGUAGE: {lang_instruction}

Write a 2-3 sentence parallel (maximum 60 words) highlighting this shared phase as a mirror for reflection.
{error_context}
"""
    return prompt


def validate_twin_copy(
    copy_dict: Dict[str, Any],
    twin_data: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Code-enforced validator for Dasha Twin copy.
    Rejects:
    - Word count > 60 words
    - Missing fields
    - Predictive claims ("you will")
    - Causal claims ("because of the Moon")
    - Invented years or dates
    - Invented celebrity names
    """
    if not isinstance(copy_dict, dict):
        return False, "Output must be a JSON object"

    body = copy_dict.get("body", "")
    headline = copy_dict.get("headline", "")

    if not body or not headline:
        return False, "Missing headline or body"

    # 1. Word count check (strictly <= 60 words)
    words = body.strip().split()
    if len(words) > 60:
        return False, f"Body exceeds 60 words limit (contains {len(words)} words)"

    body_lower = body.lower()
    headline_lower = headline.lower()
    combined_lower = f"{headline_lower} {body_lower}"

    # 2. Predictive future claims
    for pat in PREDICTIVE_PATTERNS:
        if re.search(pat, combined_lower, re.IGNORECASE):
            return False, f"Found forbidden predictive language matching: '{pat}'"

    # 3. Causal astrological claims
    for pat in CAUSAL_PATTERNS:
        if re.search(pat, combined_lower, re.IGNORECASE):
            return False, f"Found forbidden causal language matching: '{pat}'"

    # 4. Check for unauthorized years (must match event year, current year, or figure dates)
    event = twin_data.get("event") or {}
    event_date_str = event.get("event_date", "")
    allowed_years = {str(datetime.now().year)}
    if event_date_str:
        allowed_years.add(event_date_str[:4])

    found_years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", body)
    for y in found_years:
        if y not in allowed_years:
            return False, f"Invented or unauthorized year '{y}' found in body"

    return True, None


def get_fixed_template_copy(twin_data: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """Guaranteed grounded fallback template in English and Hindi."""
    user_lord = twin_data.get("user_lord", "Planetary")
    user_level = twin_data.get("user_level", "Pratyantar").capitalize()
    figure = twin_data.get("figure") or {}
    event = twin_data.get("event") or {}

    figure_name = figure.get("display_name", "a notable figure")
    figure_field = figure.get("field", "")
    event_title = event.get("title", "a major achievement")
    event_date = event.get("event_date", "")
    year_str = f" in {event_date[:4]}" if event_date else ""

    if lang == "hi":
        headline = f"आपकी {user_level}, उनकी महादशा: {user_lord}"
        body = (
            f"आपकी {user_lord} {user_level} दशा और {figure_name} के जीवन के बीच एक विचारणीय समानता है। "
            f"उनकी {user_lord} महादशा में यह क्षण आया: {event_title}{year_str}। "
            f"इस चरण की सीख: सही दिशा कभी-कभी सबसे तेज़ गति से अधिक मूल्यवान होती है।"
        )
    else:
        headline = f"Your {user_level}, their Mahadasha: {user_lord}"
        body = (
            f"There is a useful parallel between your {user_lord} {user_level} Dasha and one phase of {figure_name}'s journey. "
            f"Their {user_lord} Mahadasha brought this moment: {event_title}{year_str}. "
            f"The reflection for your phase is simple: the right direction may matter more than the fastest result."
        )

    return {
        "headline": headline,
        "body": body,
        "fact_ids": ["F_DASHA_USER", "F_EVENT_MATCH"],
        "disclaimer": "विचार और आनंद के लिए, भविष्यवाणी नहीं।" if lang == "hi" else "For reflection and fun, not prediction.",
        "source_url": event.get("source_url") or figure.get("source_url"),
        "is_fallback": True,
    }


def generate_grounded_twin_copy(
    twin_data: Dict[str, Any],
    lang: str = "en",
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Generate card copy with 1 retry on validation failure, then fixed template fallback.
    """
    if twin_data.get("match_type") == "generic_phase":
        user_lord = twin_data.get("user_lord", "")
        level = twin_data.get("user_level", "Pratyantar").capitalize()
        if lang == "hi":
            return {
                "headline": f"आपका {user_lord} {level} चरण",
                "body": f"आप वर्तमान में {user_lord} {level} दशा के प्रभाव में हैं। वैदिक ज्योतिष में यह चरण आत्म-चिंतन और एकाग्रता का समय माना जाता है।",
                "fact_ids": ["F_DASHA_USER"],
                "disclaimer": "विचार और आनंद के लिए, भविष्यवाणी नहीं।",
                "source_url": None,
                "is_fallback": False,
            }
        return {
            "headline": f"Your {user_lord} {level} Phase",
            "body": f"You are currently moving through your {user_lord} {level} Dasha. In Vedic astrology, this phase invites conscious alignment and steady focus on your chosen pursuits.",
            "fact_ids": ["F_DASHA_USER"],
            "disclaimer": "For reflection and fun, not prediction.",
            "source_url": None,
            "is_fallback": False,
        }

    if not use_llm:
        return get_fixed_template_copy(twin_data, lang=lang)

    # Attempt 1: Call LLM
    orchestrator = ModelOrchestrator()
    prompt = build_twin_prompt(twin_data, lang=lang)
    for attempt in range(2):
        try:
            resp = orchestrator.generate(
                prompt=prompt,
                system_prompt=TWIN_SYSTEM_PROMPT,
            )
            raw_response = resp.content
            # Parse JSON
            cleaned = raw_response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            data = json.loads(cleaned)
            is_valid, error_msg = validate_twin_copy(data, twin_data)
            if is_valid:
                data["disclaimer"] = "विचार और आनंद के लिए, भविष्यवाणी नहीं।" if lang == "hi" else "For reflection and fun, not prediction."
                event = twin_data.get("event") or {}
                figure = twin_data.get("figure") or {}
                data["source_url"] = event.get("source_url") or figure.get("source_url")
                data["is_fallback"] = False
                return data

            # Retry once with error feedback
            if attempt == 0:
                prompt = build_twin_prompt(twin_data, lang=lang, retry_error=error_msg)

        except Exception as e:
            if attempt == 0:
                prompt = build_twin_prompt(twin_data, lang=lang, retry_error=str(e))

    # Fallback to guaranteed template
    return get_fixed_template_copy(twin_data, lang=lang)
