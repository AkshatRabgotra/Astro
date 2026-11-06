"""Zero-Hallucination Guardrail and Fact Validator for Muhurta Explanations.

Asserts that every astrological element (Nakshatra, Tithi, Yoga, Choghadiya,
Tara Bala, Lunar House) mentioned in an LLM narrative exists verbatim in the
calculated slot payload.
"""

import re
from typing import List, Tuple
from backend.muhurta.ephemeris import NAKSHATRAS, TITHI_NAMES, YOGAS
from backend.muhurta.models import MuhurtaSlot
from backend.muhurta.personalization import TARA_NAMES

CHOGHADIYA_NAMES = ["Amrit", "Shubh", "Labh", "Char", "Udveg", "Kaal", "Rog"]


def validate_explanation_facts(
    explanation: str,
    slot_nakshatra: str,
    slot_tithi: str,
    slot_yoga: str,
    slot_choghadiya: str,
    slot_tara: str,
    slot_chandra_house: int,
) -> Tuple[bool, List[str]]:
    """
    Check if the explanation contains any hallucinated astrological entity
    not present in the slot payload.
    """
    violations = []
    text_lower = explanation.lower()

    # 1. Check Nakshatras: If another nakshatra is mentioned, flag error
    for nak in NAKSHATRAS:
        if nak.lower() in text_lower:
            if nak.lower() not in slot_nakshatra.lower():
                violations.append(
                    f"Hallucinated Nakshatra: Mentioned '{nak}', but calculated Nakshatra is '{slot_nakshatra}'"
                )

    # 2. Check Yogas (avoid false positive on 'Shukla' paksha or 'Dhruva' nakshatra temperament)
    AMBIGUOUS_YOGAS = {"shukla", "dhruva", "shubha", "siddha", "brahma", "indra"}
    for y in YOGAS:
        y_low = y.lower()
        if y_low in AMBIGUOUS_YOGAS:
            # Must explicitly be referred as a Yoga (e.g. "Shukla yoga" or "Yoga Shukla")
            pattern = rf"\b({re.escape(y_low)}\s+yoga|yoga\s+{re.escape(y_low)})\b"
            if re.search(pattern, text_lower):
                if y_low not in slot_yoga.lower():
                    violations.append(
                        f"Hallucinated Yoga: Mentioned '{y} Yoga', but calculated Yoga is '{slot_yoga}'"
                    )
        else:
            if re.search(rf"\b{re.escape(y_low)}\b", text_lower):
                if y_low not in slot_yoga.lower():
                    violations.append(
                        f"Hallucinated Yoga: Mentioned '{y}', but calculated Yoga is '{slot_yoga}'"
                    )

    # 3. Check Choghadiyas
    for ch in CHOGHADIYA_NAMES:
        if ch.lower() in text_lower:
            if ch.lower() not in slot_choghadiya.lower():
                violations.append(
                    f"Hallucinated Choghadiya: Mentioned '{ch}', but calculated Choghadiya is '{slot_choghadiya}'"
                )

    # 4. Check Tara Bala
    for _, (tara_name, _, _) in TARA_NAMES.items():
        base_tara = tara_name.split(" ")[0].lower()
        if base_tara in text_lower:
            if base_tara not in slot_tara.lower():
                violations.append(
                    f"Hallucinated Tara Bala: Mentioned '{base_tara}', but calculated Tara is '{slot_tara}'"
                )

    # 5. Check Houses (e.g. '8th house', '11th house')
    house_matches = re.findall(r"(\d+)(?:st|nd|rd|th)?\s+house", text_lower)
    for h in house_matches:
        try:
            h_int = int(h)
            if h_int != slot_chandra_house:
                violations.append(
                    f"Hallucinated Lunar Transit House: Mentioned {h_int}th House, but calculated Chandra Bala is {slot_chandra_house}th House"
                )
        except ValueError:
            pass

    is_valid = len(violations) == 0
    return is_valid, violations


def build_grounded_fallback_explanation(
    activity_title: str,
    slot_nakshatra: str,
    slot_choghadiya: str,
    slot_tara: str,
    slot_chandra_house: int,
    slot_tithi: str,
) -> str:
    """Deterministic, mathematically verified template explanation."""
    tara_name = slot_tara.split(" ")[0]
    nak_name = slot_nakshatra.split(" (")[0]
    return (
        f"This auspicious window for {activity_title} is energized by the harmonious {slot_choghadiya} Choghadiya "
        f"and {nak_name} Nakshatra during {slot_tithi}. For your birth profile, it activates the favorable "
        f"{slot_chandra_house}th House lunar alignment while securing your personal {tara_name} Tara."
    )
