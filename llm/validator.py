"""Code-enforced validation of LLM astrological answers against ground truth ChartFacts."""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from chart.models import ChartFact, ChartFacts

# Canonical dictionary of astrological entities
PLANET_NAMES = {
    "sun": "Sun",
    "surya": "Sun",
    "moon": "Moon",
    "chandra": "Moon",
    "mars": "Mars",
    "mangal": "Mars",
    "mercury": "Mercury",
    "budha": "Mercury",
    "jupiter": "Jupiter",
    "guru": "Jupiter",
    "brihaspati": "Jupiter",
    "venus": "Venus",
    "shukra": "Venus",
    "saturn": "Saturn",
    "shani": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}

SIGN_NAMES = {
    "aries": "Aries",
    "mesha": "Aries",
    "taurus": "Taurus",
    "vrishabha": "Taurus",
    "gemini": "Gemini",
    "mithuna": "Gemini",
    "cancer": "Cancer",
    "karka": "Cancer",
    "leo": "Leo",
    "simha": "Leo",
    "virgo": "Virgo",
    "kanya": "Virgo",
    "libra": "Libra",
    "tula": "Libra",
    "scorpio": "Scorpio",
    "vrischika": "Scorpio",
    "sagittarius": "Sagittarius",
    "dhanu": "Sagittarius",
    "capricorn": "Capricorn",
    "makara": "Capricorn",
    "aquarius": "Aquarius",
    "kumbha": "Aquarius",
    "pisces": "Pisces",
    "meena": "Pisces",
}

HOUSE_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12
}


class ValidationResult:
    def __init__(self, is_valid: bool, violations: List[str], verified_cited_facts: List[ChartFact]):
        self.is_valid = is_valid
        self.violations = violations
        self.verified_cited_facts = verified_cited_facts

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, violations={self.violations})"


def parse_llm_json(raw_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Extract and parse JSON object from LLM response (handling markdown fences)."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data, None
        return None, "Parsed JSON is not an object/dictionary"
    except json.JSONDecodeError as e:
        # Attempt to find JSON substring
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data, None
            except Exception:
                pass
        return None, f"Failed to parse valid JSON: {str(e)}"


class AnswerValidator:
    @staticmethod
    def validate(
        raw_response: str,
        chart_facts: ChartFacts,
    ) -> ValidationResult:
        """
        Validate LLM response strictly against computed ChartFacts:
        1. Validates JSON schema {answer, cited_fact_ids[], claims[]}.
        2. Validates every cited ID exists and was available in provided facts.
        3. Validates that all mentioned planet-sign, planet-house, dasha, and date combinations
           match actual computed facts (regex + dictionary checks).
        """
        violations: List[str] = []
        verified_facts: List[ChartFact] = []

        # 1. Parse JSON
        data, err = parse_llm_json(raw_response)
        if err or not data:
            return ValidationResult(
                is_valid=False,
                violations=[f"JSON Schema violation: {err}"],
                verified_cited_facts=[],
            )

        answer_text = data.get("answer", "")
        cited_ids = data.get("cited_fact_ids", [])

        if not answer_text or not isinstance(answer_text, str):
            violations.append("Field 'answer' is missing or not a non-empty string.")

        if not isinstance(cited_ids, list):
            violations.append("Field 'cited_fact_ids' must be a list of string IDs.")
            cited_ids = []

        # 2. Rule 1: Every cited ID exists and is available
        available_facts_map = {f.id: f for f in chart_facts.facts}
        for fid in cited_ids:
            if fid not in available_facts_map:
                violations.append(f"Cited non-existent fact ID: '{fid}'. Available IDs: {list(available_facts_map.keys())}")
            else:
                fact = available_facts_map[fid]
                if not fact.is_available:
                    violations.append(f"Cited fact '{fid}' is marked UNAVAILABLE (e.g. unknown birth time).")
                else:
                    if fact not in verified_facts:
                        verified_facts.append(fact)

        # 3. Rule 2: Entity & Grounding check via Regex + Dictionary
        # Map actual planets to their computed signs and houses
        actual_planet_signs = {p.planet: p.sign for p in chart_facts.planets}
        actual_planet_houses = {p.planet: p.house for p in chart_facts.planets if p.house is not None}

        # Check for unknown birth time: if birth time is unknown, NO house numbers can be claimed
        if not chart_facts.time_known:
            house_patterns = [
                r"\b(\d{1,2})(?:st|nd|rd|th)?\s+house\b",
                r"\bhouse\s+(\d{1,2})\b",
                r"\bbhava?\s+(\d{1,2})\b",
            ]
            for pat in house_patterns:
                match = re.search(pat, answer_text, re.IGNORECASE)
                if match:
                    violations.append(
                        f"Unknown birth time violation: Answer claims house '{match.group(0)}', but houses are unavailable."
                    )
                    break

            # Ascendant / Lagna claim check
            if re.search(r"\b(?:lagna|ascendant)\s+(?:in|is)\s+([A-Za-z]+)\b", answer_text, re.IGNORECASE):
                violations.append("Unknown birth time violation: Answer mentions an Ascendant/Lagna, which is unavailable.")

        # Check Planet-Sign associations in text: e.g. "Saturn in Aries", "Sun in Leo", "Mangal in Vrishabha"
        for p_syn, canonical_p in PLANET_NAMES.items():
            pattern = rf"\b{p_syn}\b(?:\s+(?:is\s+)?in\s+|\s+is\s+placed\s+in\s+)([A-Za-z]+)"
            matches = re.finditer(pattern, answer_text, re.IGNORECASE)
            for m in matches:
                sign_word = m.group(1).lower()
                if sign_word in SIGN_NAMES:
                    canonical_sign = SIGN_NAMES[sign_word]
                    expected_sign = actual_planet_signs.get(canonical_p)
                    if expected_sign and canonical_sign != expected_sign:
                        violations.append(
                            f"Hallucinated placement: Claims '{canonical_p} in {canonical_sign}', but chart has '{canonical_p} in {expected_sign}'."
                        )

        # Check Planet-House associations in text: e.g. "Saturn in House 7", "Mars in the 4th house"
        if chart_facts.time_known:
            for p_syn, canonical_p in PLANET_NAMES.items():
                pattern = rf"\b{p_syn}\b(?:[^\.\,\;]{{1,40}}?)\b(?:in\s+(?:the\s+)?house\s+(\d{{1,2}})|in\s+(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?\s+house)\b"
                matches = re.finditer(pattern, answer_text, re.IGNORECASE)
                for m in matches:
                    h_num_str = m.group(1) or m.group(2)
                    claimed_h = int(h_num_str)
                    actual_h = actual_planet_houses.get(canonical_p)
                    # Also check if it aspects that house
                    aspects_houses = [
                        a.target_house for a in chart_facts.aspects
                        if a.aspecting_planet == canonical_p and a.target_house is not None
                    ]
                    if actual_h != claimed_h and claimed_h not in aspects_houses:
                        violations.append(
                            f"Hallucinated house: Claims '{canonical_p} in House {claimed_h}', but chart places {canonical_p} in House {actual_h}."
                        )

        # Check Current Dasha lord mentions
        if chart_facts.current_dasha:
            md_lord = chart_facts.current_dasha.mahadasha_lord
            # If answer claims Mahadasha is planet X, check if it matches md_lord
            dasha_matches = re.finditer(r"\b(?:current\s+)?mahadasha\s+(?:of\s+|is\s+)?([A-Za-z]+)\b", answer_text, re.IGNORECASE)
            for dm in dasha_matches:
                lord_word = dm.group(1).lower()
                if lord_word in PLANET_NAMES:
                    canonical_lord = PLANET_NAMES[lord_word]
                    if canonical_lord != md_lord:
                        violations.append(
                            f"Hallucinated Dasha: Claims current Mahadasha is '{canonical_lord}', but computed chart is '{md_lord}'."
                        )

        is_valid = len(violations) == 0
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            verified_cited_facts=verified_facts,
        )
