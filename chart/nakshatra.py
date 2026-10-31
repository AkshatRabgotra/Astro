"""Nakshatra definitions and calculations for Vedic Astrology."""

from typing import Tuple
from chart.models import NakshatraDetail

# 27 Nakshatras in order
NAKSHATRAS = [
    ("Ashwini", "Ketu"),
    ("Bharani", "Venus"),
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Mrigashira", "Mars"),
    ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"),
    ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"),
    ("Purva Phalguni", "Venus"),
    ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"),
    ("Chitra", "Mars"),
    ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"),
    ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"),
    ("Dhanishta", "Mars"),
    ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"),
    ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

# Span of one nakshatra: 360 / 27 = 13 degrees 20 minutes = 13.333333333333334 degrees
NAKSHATRA_SPAN = 360.0 / 27.0
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3 degrees 20 minutes = 3.3333333333333335 degrees


def calculate_nakshatra(longitude: float) -> NakshatraDetail:
    """
    Calculate Nakshatra, Pada, and Lord for a given sidereal longitude (0 to 360).
    """
    lon = longitude % 360.0
    idx = int(lon // NAKSHATRA_SPAN)
    if idx >= 27:
        idx = 26
    
    nak_name, lord = NAKSHATRAS[idx]
    deg_in_nak = lon - (idx * NAKSHATRA_SPAN)
    pada = int(deg_in_nak // PADA_SPAN) + 1
    if pada > 4:
        pada = 4
        
    return NakshatraDetail(
        number=idx + 1,
        name=nak_name,
        pada=pada,
        lord=lord,
        degree_in_nakshatra=round(deg_in_nak, 4)
    )
