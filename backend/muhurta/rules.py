"""Classical Vedic Activity Rules and Constraints for Muhurta Evaluation."""

from typing import Dict, List, Set
from backend.muhurta.models import ActivityOverride, VedicActivityCategory

# Inauspicious Tithis (Rikta + Amavasya + Krishna Chaturdashi)
RIKTA_TITHIS = {4, 9, 14, 19, 24, 29, 30}  # Chaturthi, Navami, Chaturdashi, Amavasya

# Universal Favorable Tithis
FAVORABLE_TITHIS = {2, 3, 5, 7, 10, 11, 12, 13, 15}  # Dwitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi, Dwadashi, Trayodashi, Purnima

CATEGORY_RULES: Dict[str, Dict] = {
    VedicActivityCategory.BUSINESS_FINANCE.value: {
        "favored_varas": {"Wednesday", "Thursday", "Friday"},
        "prohibited_varas": {"Saturday", "Tuesday"},
        "favored_temperaments": {"Kshipra (Swift)", "Chara (Movable)", "Dhruva (Fixed)"},
        "prohibited_temperaments": {"Tikshna (Sharp)", "Ugra (Fierce)"},
        "favored_choghadiyas": {"Labh", "Amrit", "Shubh"},
        "base_weight": 1.0,
    },
    VedicActivityCategory.PROPERTY_CONSTRUCTION.value: {
        "favored_varas": {"Thursday", "Friday", "Monday", "Wednesday"},
        "prohibited_varas": {"Tuesday", "Sunday"},
        "favored_temperaments": {"Dhruva (Fixed)", "Mridu (Tender)"},
        "prohibited_temperaments": {"Tikshna (Sharp)", "Ugra (Fierce)", "Chara (Movable)"},
        "favored_choghadiyas": {"Amrit", "Shubh"},
        "base_weight": 1.2,
    },
    VedicActivityCategory.MARRIAGE_RELATIONSHIP.value: {
        "favored_varas": {"Thursday", "Friday", "Monday", "Wednesday"},
        "prohibited_varas": {"Tuesday", "Saturday", "Sunday"},
        "favored_temperaments": {"Dhruva (Fixed)", "Mridu (Tender)", "Kshipra (Swift)"},
        "prohibited_temperaments": {"Tikshna (Sharp)", "Ugra (Fierce)"},
        "favored_choghadiyas": {"Amrit", "Shubh"},
        "base_weight": 1.3,
    },
    VedicActivityCategory.EDUCATION_LEARNING.value: {
        "favored_varas": {"Wednesday", "Thursday", "Sunday", "Monday"},
        "prohibited_varas": {"Tuesday"},
        "favored_temperaments": {"Kshipra (Swift)", "Mridu (Tender)", "Chara (Movable)"},
        "prohibited_temperaments": {"Ugra (Fierce)"},
        "favored_choghadiyas": {"Shubh", "Labh", "Amrit"},
        "base_weight": 1.0,
    },
    VedicActivityCategory.TRAVEL_JOURNEY.value: {
        "favored_varas": {"Thursday", "Friday", "Wednesday", "Monday"},
        "prohibited_varas": {"Tuesday"},
        "favored_temperaments": {"Chara (Movable)", "Kshipra (Swift)"},
        "prohibited_temperaments": {"Dhruva (Fixed)", "Ugra (Fierce)"},
        "favored_choghadiyas": {"Char", "Amrit", "Labh", "Shubh"},
        "base_weight": 1.0,
    },
    VedicActivityCategory.HEALTH_MEDICAL.value: {
        "favored_varas": {"Tuesday", "Thursday", "Sunday"},  # Tuesday for fighting disease / surgery
        "prohibited_varas": {"Saturday"},
        "favored_temperaments": {"Kshipra (Swift)", "Chara (Movable)"},
        "prohibited_temperaments": {"Tikshna (Sharp)"},
        "favored_choghadiyas": {"Amrit", "Shubh"},
        "base_weight": 1.1,
    },
    VedicActivityCategory.SPIRITUAL_RELIGIOUS.value: {
        "favored_varas": {"Thursday", "Monday", "Sunday", "Tuesday"},
        "prohibited_varas": set(),
        "favored_temperaments": {"Dhruva (Fixed)", "Kshipra (Swift)", "Mridu (Tender)"},
        "prohibited_temperaments": set(),
        "favored_choghadiyas": {"Amrit", "Shubh", "Labh"},
        "base_weight": 1.0,
    },
    VedicActivityCategory.JOB_CAREER.value: {
        "favored_varas": {"Thursday", "Sunday", "Wednesday", "Monday"},
        "prohibited_varas": {"Saturday"},
        "favored_temperaments": {"Dhruva (Fixed)", "Kshipra (Swift)"},
        "prohibited_temperaments": {"Tikshna (Sharp)", "Ugra (Fierce)"},
        "favored_choghadiyas": {"Labh", "Amrit", "Shubh"},
        "base_weight": 1.1,
    },
}

OVERRIDE_RULES: Dict[str, Dict] = {
    ActivityOverride.TECH_STARTUP_LAUNCH.value: {
        "favored_varas": {"Wednesday", "Thursday", "Friday"},
        "favored_temperaments": {"Kshipra (Swift)", "Chara (Movable)"},
        "target_choghadiyas": {"Labh", "Amrit"},
        "bonus_pts": 4.0,
        "advice": "Ideal for fast digital scalability, funding conversations, and algorithmic product releases.",
    },
    ActivityOverride.GRIHA_PRAVESH.value: {
        "favored_varas": {"Thursday", "Friday", "Monday", "Wednesday"},
        "strict_prohibit_varas": {"Tuesday", "Sunday"},
        "favored_temperaments": {"Dhruva (Fixed)", "Mridu (Tender)"},
        "target_choghadiyas": {"Amrit", "Shubh"},
        "bonus_pts": 5.0,
        "advice": "Combines domestic peace, enduring Vastu stability, and family longevity.",
    },
    ActivityOverride.PROPERTY_PURCHASE.value: {
        "favored_varas": {"Thursday", "Friday", "Wednesday"},
        "favored_temperaments": {"Dhruva (Fixed)"},
        "target_choghadiyas": {"Labh", "Amrit"},
        "bonus_pts": 3.5,
        "advice": "Solidifies legal titles and ensures uninterrupted asset appreciation.",
    },
    ActivityOverride.VEHICLE_PURCHASE.value: {
        "favored_varas": {"Friday", "Wednesday", "Thursday"},
        "favored_temperaments": {"Chara (Movable)", "Kshipra (Swift)"},
        "target_choghadiyas": {"Char", "Amrit"},
        "bonus_pts": 3.0,
        "advice": "Invokes dynamic protection against mechanical wear and road accidents.",
    },
    ActivityOverride.CONTRACT_SIGNING.value: {
        "favored_varas": {"Wednesday", "Thursday", "Friday"},
        "favored_temperaments": {"Mridu (Tender)", "Kshipra (Swift)"},
        "target_choghadiyas": {"Labh", "Shubh"},
        "bonus_pts": 4.0,
        "advice": "Secures bilateral goodwill, mutual profit, and contractual fidelity.",
    },
    ActivityOverride.VIVAH_MARRIAGE.value: {
        "favored_varas": {"Thursday", "Friday", "Monday"},
        "strict_prohibit_varas": {"Tuesday", "Saturday", "Sunday"},
        "favored_temperaments": {"Dhruva (Fixed)", "Mridu (Tender)"},
        "target_choghadiyas": {"Amrit", "Shubh"},
        "bonus_pts": 5.0,
        "advice": "Blessed for eternal marital harmony, progeny growth, and joint spiritual dharma.",
    },
}
