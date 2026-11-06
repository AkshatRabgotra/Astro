"""Deterministic Scoring Engine for Candidate Muhurta Windows."""

from typing import Dict, List, Optional, Tuple
from backend.muhurta.ephemeris import FAVORABLE_CHOGHADIYAS
from backend.muhurta.models import (
    ActivityOverride,
    PanchangaDetails,
    PersonalAlignment,
    VedicActivityCategory,
)
from backend.muhurta.rules import (
    CATEGORY_RULES,
    FAVORABLE_TITHIS,
    OVERRIDE_RULES,
    RIKTA_TITHIS,
)


def score_muhurta_slot(
    panchanga: PanchangaDetails,
    personal: PersonalAlignment,
    category: VedicActivityCategory,
    override: Optional[ActivityOverride] = None,
) -> Tuple[float, bool, List[str]]:
    """
    Compute deterministic mathematical score for a candidate 30-to-90 min time slot.
    Returns:
        (total_score, is_acceptable, reasons_list)
    """
    score = 10.0  # Base calibration
    reasons = []
    is_acceptable = True

    # ==========================================
    # 1. HARD CLASSICAL FILTERS (Instant Disqualification)
    # ==========================================
    if panchanga.is_rahu_kalam:
        score -= 50.0
        is_acceptable = False
        reasons.append("Disqualified: Occurs during inauspicious Rahu Kalam window")

    if panchanga.is_yamaganda:
        score -= 30.0
        is_acceptable = False
        reasons.append("Disqualified: Occurs during Yamaganda window")

    if panchanga.is_vishti_bhadra:
        score -= 35.0
        is_acceptable = False
        reasons.append("Disqualified: Afflicted by Vishti (Bhadra) Karana")

    if personal.is_ashtama_chandra:
        score -= 40.0
        is_acceptable = False
        reasons.append("Disqualified: Strict Ashtama Chandra (Moon transiting 8th from Janma Rashi)")

    if personal.tara_bala_number == 7:  # Naidhana / Vadha
        score -= 25.0
        is_acceptable = False
        reasons.append("Disqualified: Naidhana Tara (Fatal afflictive birth-star relation)")

    if panchanga.tithi_number == 30:  # Amavasya
        score -= 30.0
        is_acceptable = False
        reasons.append("Disqualified: New Moon (Amavasya) unsuitable for auspicious beginnings")

    # If already disqualified by major hard flaws, return immediately
    if not is_acceptable:
        return round(score, 1), False, reasons

    # ==========================================
    # 2. UNIVERSAL PANCHANGA QUALITY
    # ==========================================
    # Tithi
    if panchanga.tithi_number in FAVORABLE_TITHIS:
        score += 3.5
        reasons.append(f"Auspicious {panchanga.tithi} (+3.5)")
    elif panchanga.tithi_number in RIKTA_TITHIS:
        score -= 8.0
        reasons.append(f"Rikta Tithi penalty ({panchanga.tithi}) (-8.0)")

    # Yoga
    if panchanga.is_inauspicious_yoga:
        score -= 10.0
        reasons.append(f"Inauspicious Yoga ({panchanga.yoga}) (-10.0)")
    else:
        score += 2.0

    # Choghadiya
    if panchanga.choghadiya == "Amrit":
        score += 5.0
        reasons.append("Amrit Choghadiya (+5.0)")
    elif panchanga.choghadiya in ["Shubh", "Labh"]:
        score += 4.0
        reasons.append(f"{panchanga.choghadiya} Choghadiya (+4.0)")
    elif panchanga.choghadiya == "Char":
        score += 2.0
    else:
        score -= 7.0
        reasons.append(f"Inauspicious Choghadiya ({panchanga.choghadiya}) (-7.0)")

    # Abhijit Muhurta
    if panchanga.is_abhijit:
        score += 6.0
        reasons.append("Sacred Abhijit Muhurta solar alignment (+6.0)")

    # ==========================================
    # 3. CATEGORY & OVERRIDE ALIGNMENT
    # ==========================================
    cat_rule = CATEGORY_RULES.get(category.value, {})
    if cat_rule:
        if panchanga.vara in cat_rule.get("favored_varas", set()):
            score += 3.0
            reasons.append(f"Favored day {panchanga.vara} for {category.value} (+3.0)")
        elif panchanga.vara in cat_rule.get("prohibited_varas", set()):
            score -= 6.0
            reasons.append(f"Prohibited day {panchanga.vara} for {category.value} (-6.0)")

        # Nakshatra Temperament match
        temp = panchanga.nakshatra_temperament
        if temp in cat_rule.get("favored_temperaments", set()):
            score += 4.0
            reasons.append(f"Harmonious {temp} Nakshatra (+4.0)")
        elif temp in cat_rule.get("prohibited_temperaments", set()):
            score -= 6.0
            reasons.append(f"Incompatible {temp} Nakshatra (-6.0)")

    # Specific Activity Override bonus
    if override and override.value in OVERRIDE_RULES:
        ov_rule = OVERRIDE_RULES[override.value]
        if panchanga.vara in ov_rule.get("strict_prohibit_varas", set()):
            score -= 15.0
            is_acceptable = False
            reasons.append(f"Strict prohibition: {panchanga.vara} for {override.value}")
        elif panchanga.vara in ov_rule.get("favored_varas", set()):
            score += ov_rule.get("bonus_pts", 3.0)
            reasons.append(f"Target match for {override.value} (+{ov_rule.get('bonus_pts', 3.0)})")

    # ==========================================
    # 4. PERSONAL ALIGNMENT (TARA BALA & CHANDRA BALA)
    # ==========================================
    # Tara Bala
    tara_num = personal.tara_bala_number
    if tara_num == 6:  # Sadhana
        score += 6.0
        reasons.append("Sadhana Tara (+6.0)")
    elif tara_num in [2, 9]:  # Sampat, Parama Mitra
        score += 5.0
        reasons.append(f"{personal.tara_bala.split(' ')[0]} Tara (+5.0)")
    elif tara_num in [4, 8]:  # Kshema, Mitra
        score += 4.0
        reasons.append(f"{personal.tara_bala.split(' ')[0]} Tara (+4.0)")
    elif tara_num in [3, 5]:  # Vipat, Pratyak
        score -= 7.0
        reasons.append(f"{personal.tara_bala.split(' ')[0]} Tara penalty (-7.0)")

    # Chandra Bala
    ch_house = personal.chandra_house
    if ch_house == 11:
        score += 7.0
        reasons.append("11th House Lunar Transit (Labha / Gain) (+7.0)")
    elif ch_house in [6, 10]:
        score += 6.0
        reasons.append(f"{ch_house}th House Lunar Transit (+6.0)")
    elif ch_house in [3, 7]:
        score += 5.0
        reasons.append(f"{ch_house}th House Lunar Transit (+5.0)")
    elif ch_house == 1:
        score += 4.0
    elif ch_house in [4, 12]:
        score -= 4.0
        reasons.append(f"{ch_house}th House Lunar Transit penalty (-4.0)")

    final_score = max(0.0, round(score, 1))
    return final_score, is_acceptable, reasons
