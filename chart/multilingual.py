"""Multilingual Vedic Astrology definitions and translations (English <-> Hindi/Devanagari)."""

from typing import Dict, List, Optional

# Planet translations: English -> (Devanagari, Transliterated)
PLANET_I18N: Dict[str, Dict[str, str]] = {
    "Sun": {"hi": "सूर्य", "translit": "Surya"},
    "Moon": {"hi": "चन्द्र", "translit": "Chandra"},
    "Mars": {"hi": "मंगल", "translit": "Mangal"},
    "Mercury": {"hi": "बुध", "translit": "Budha"},
    "Jupiter": {"hi": "बृहस्पति", "translit": "Guru"},
    "Venus": {"hi": "शुक्र", "translit": "Shukra"},
    "Saturn": {"hi": "शनि", "translit": "Shani"},
    "Rahu": {"hi": "राहु", "translit": "Rahu"},
    "Ketu": {"hi": "केतु", "translit": "Ketu"},
}

# Sign translations: English -> (Devanagari, Transliterated)
SIGN_I18N: Dict[str, Dict[str, str]] = {
    "Aries": {"hi": "मेष", "translit": "Mesha"},
    "Taurus": {"hi": "वृषभ", "translit": "Vrishabha"},
    "Gemini": {"hi": "मिथुन", "translit": "Mithuna"},
    "Cancer": {"hi": "कर्क", "translit": "Karka"},
    "Leo": {"hi": "सिंह", "translit": "Simha"},
    "Virgo": {"hi": "कन्या", "translit": "Kanya"},
    "Libra": {"hi": "तुला", "translit": "Tula"},
    "Scorpio": {"hi": "वृश्चिक", "translit": "Vrischika"},
    "Sagittarius": {"hi": "धनु", "translit": "Dhanu"},
    "Capricorn": {"hi": "मकर", "translit": "Makara"},
    "Aquarius": {"hi": "कुम्भ", "translit": "Kumbha"},
    "Pisces": {"hi": "मीन", "translit": "Meena"},
}

# House translations: 1-12 -> Devanagari Bhava
HOUSE_I18N: Dict[int, str] = {
    1: "प्रथम भाव",
    2: "द्वितीय भाव",
    3: "तृतीय भाव",
    4: "चतुर्थ भाव",
    5: "पंचम भाव",
    6: "षष्ठ भाव",
    7: "सप्तम भाव",
    8: "अष्टम भाव",
    9: "नवम भाव",
    10: "दशम भाव",
    11: "एकादश भाव",
    12: "द्वादश भाव",
}

# Reverse lookups for Devanagari and transliterated names
HINDI_TO_PLANET: Dict[str, str] = {}
for en, data in PLANET_I18N.items():
    HINDI_TO_PLANET[data["hi"]] = en
    HINDI_TO_PLANET[data["translit"].lower()] = en
    HINDI_TO_PLANET[en.lower()] = en

HINDI_TO_SIGN: Dict[str, str] = {}
for en, data in SIGN_I18N.items():
    HINDI_TO_SIGN[data["hi"]] = en
    HINDI_TO_SIGN[data["translit"].lower()] = en
    HINDI_TO_SIGN[en.lower()] = en

HINDI_HOUSE_WORDS: Dict[str, int] = {
    "प्रथम": 1, "पहला": 1, "पहले": 1,
    "द्वितीय": 2, "दूसरा": 2, "दूसरे": 2,
    "तृतीय": 3, "तीसरा": 3, "तीसरे": 3,
    "चतुर्थ": 4, "चौथा": 4, "चौथे": 4,
    "पंचम": 5, "पांचवां": 5, "पांचवें": 5,
    "षष्ठ": 6, "छठा": 6, "छठे": 6,
    "सप्तम": 7, "सातवां": 7, "सातवें": 7,
    "अष्टम": 8, "आठवां": 8, "आठवें": 8,
    "नवम": 9, "नौवां": 9, "नौवें": 9,
    "दशम": 10, "दसवां": 10, "दसवें": 10,
    "एकादश": 11, "ग्यारहवां": 11, "ग्यारहवें": 11,
    "द्वादश": 12, "बारहवां": 12, "बारहवें": 12,
}
