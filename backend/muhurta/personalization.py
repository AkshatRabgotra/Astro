"""Melooha Personalization Layer: Tara Bala & Chandra Bala calculations.

Grounded strictly in the authenticated user's natal birth chart (Janma Nakshatra and Janma Rashi).
Calculates exact mathematical compatibility without LLM hallucination.
"""

from typing import Dict, Optional, Tuple
from backend.muhurta.models import PersonalAlignment

# The 9 Classical Taras
TARA_NAMES = {
    1: ("Janma (Birth)", "Neutral for general tasks; caution for critical ceremonies", False),
    2: ("Sampat (Wealth & Prosperity)", "Highly auspicious for finance, investments, and growth", True),
    3: ("Vipat (Danger / Adversity)", "Inauspicious; brings unforeseen delays and loss", False),
    4: ("Kshema (Well-being & Security)", "Favorable for stability, construction, and peace", True),
    5: ("Pratyak (Obstacles / Resistance)", "Inauspicious; projects face opposition", False),
    6: ("Sadhana (Accomplishment & Success)", "Super auspicious; ensures victory and achievement", True),
    7: ("Naidhana (Severe Affliction)", "Severely inauspicious; should be strictly avoided", False),
    8: ("Mitra (Friendship & Harmony)", "Favorable for partnerships, agreement, and joy", True),
    9: ("Parama Mitra (Supreme Ally)", "Most auspicious; brings divine support and expansion", True),
}

# The 12 Chandra Bala Houses relative to Janma Rashi
CHANDRA_HOUSE_MEANINGS = {
    1: ("1st House (Tanur / Self)", True, "+4.0 pts", "Enhances personal focus and leadership"),
    2: ("2nd House (Dhana / Wealth)", False, "-2.0 pts", "Mild friction; financial scrutiny required"),
    3: ("3rd House (Sahaja / Courage)", True, "+5.0 pts", "Strong initiatives, valor, and swift success"),
    4: ("4th House (Sukha / Comfort)", False, "-3.0 pts", "Domestic unrest; mental unease"),
    5: ("5th House (Suta / Intellect)", False, "-1.0 pts", "Speculative caution; creative divergence"),
    6: ("6th House (Shatru / Victory)", True, "+6.0 pts", "Overcoming competition, health, and debt"),
    7: ("7th House (Kalatra / Alliance)", True, "+5.0 pts", "Auspicious for partnerships, contracts, and unions"),
    8: ("8th House (Ashtama Chandra)", False, "-20.0 pts", "Severe flaw; transit Moon in 8th causes loss and anxiety"),
    9: ("9th House (Bhagya / Fortune)", False, "-2.0 pts", "Delay in spiritual/karmic fruit"),
    10: ("10th House (Karma / Profession)", True, "+6.0 pts", "Exalted career, business prestige, and authority"),
    11: ("11th House (Labha / Gain)", True, "+7.0 pts", "Maximum material fulfillment, prosperity, and joy"),
    12: ("12th House (Vyaya / Expenditure)", False, "-4.0 pts", "High drain of energy and unforeseen costs"),
}


def calculate_tara_bala(
    candidate_nakshatra_num: int,
    user_janma_nakshatra_num: int,
) -> Tuple[str, int, bool, float]:
    """
    Compute Tara Bala (1 to 9) from User's Janma Nakshatra to Slot's Nakshatra.
    Formula: ((SlotNak - UserNak) % 27) % 9 + 1
    """
    diff = (candidate_nakshatra_num - user_janma_nakshatra_num) % 27
    tara_num = (diff % 9) + 1

    name, desc, is_fav = TARA_NAMES[tara_num]

    # Scoring weights
    if tara_num in [2, 9]:
        score = 5.0
    elif tara_num == 6:
        score = 6.0
    elif tara_num in [4, 8]:
        score = 4.0
    elif tara_num == 1:
        score = 0.0
    elif tara_num in [3, 5]:
        score = -8.0
    elif tara_num == 7:
        score = -15.0  # Naidhana / Vadha
    else:
        score = 0.0

    return name, tara_num, is_fav, score


def calculate_chandra_bala(
    candidate_moon_sign_num: int,
    user_janma_rashi_num: int,
) -> Tuple[str, int, bool, bool, float]:
    """
    Compute Chandra Bala (1 to 12) from User's Janma Rashi to Slot's Moon Sign.
    Formula: (SlotSign - UserSign) % 12 + 1
    """
    house_num = ((candidate_moon_sign_num - user_janma_rashi_num) % 12) + 1

    name_label, is_fav, pts_str, desc = CHANDRA_HOUSE_MEANINGS[house_num]
    is_ashtama = (house_num == 8)

    # Scoring weights
    if house_num == 11:
        score = 7.0
    elif house_num in [6, 10]:
        score = 6.0
    elif house_num in [3, 7]:
        score = 5.0
    elif house_num == 1:
        score = 4.0
    elif is_ashtama:
        score = -20.0
    elif house_num == 12:
        score = -4.0
    elif house_num == 4:
        score = -3.0
    else:
        score = -1.5

    return f"{name_label} - {desc}", house_num, is_fav, is_ashtama, score


def compute_personal_alignment(
    candidate_nakshatra_num: int,
    candidate_moon_sign_num: int,
    user_janma_nakshatra_num: Optional[int] = None,
    user_janma_rashi_num: Optional[int] = None,
) -> Tuple[PersonalAlignment, float]:
    """
    Produce structured PersonalAlignment and net personalized score contribution.
    If user's birth data is missing, falls back to neutral universal alignment.
    """
    if not user_janma_nakshatra_num or not user_janma_rashi_num:
        # Generic neutral
        alignment = PersonalAlignment(
            tara_bala="Universal Harmony (No Janma Nakshatra provided)",
            tara_bala_number=4,
            tara_bala_is_favorable=True,
            chandra_bala="Universal Lunar Transit",
            chandra_house=1,
            chandra_bala_is_favorable=True,
            is_ashtama_chandra=False,
            score_contribution="+0.0 pts (Generic)",
        )
        return alignment, 0.0

    tara_name, tara_num, tara_fav, tara_score = calculate_tara_bala(
        candidate_nakshatra_num, user_janma_nakshatra_num
    )

    chandra_desc, house_num, chandra_fav, is_ashtama, chandra_score = calculate_chandra_bala(
        candidate_moon_sign_num, user_janma_rashi_num
    )

    net_score = tara_score + chandra_score
    sign_str = "+" if net_score >= 0 else ""
    contrib_str = f"{sign_str}{net_score:.1f} pts"

    alignment = PersonalAlignment(
        tara_bala=tara_name,
        tara_bala_number=tara_num,
        tara_bala_is_favorable=tara_fav,
        chandra_bala=chandra_desc,
        chandra_house=house_num,
        chandra_bala_is_favorable=chandra_fav,
        is_ashtama_chandra=is_ashtama,
        score_contribution=contrib_str,
    )
    return alignment, net_score
