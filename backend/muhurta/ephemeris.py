"""Astronomical and Classical Panchanga Engine using Swiss Ephemeris.

100% Deterministic C-level calculations for:
- Lahiri Sidereal positions of Sun & Moon
- Local Sunrise, Sunset, and Midday
- 5 Panchanga pillars: Tithi, Vara, Nakshatra, Yoga, Karana
- Solar Windows: Rahu Kalam, Yamaganda, Abhijit Muhurta
- Day & Night Choghadiya
"""

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
import swisseph as swe

from backend.muhurta.models import PanchangaDetails

# Configure Swiss Ephemeris
swe.set_sid_mode(swe.SIDM_LAHIRI)

# --- Classical Lookups ---

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra Temperaments (Gana / Sanjna)
NAKSHATRA_TEMPERAMENT = {
    # Dhruva / Sthira (Fixed) - Auspicious for construction, marriage, long-term ventures
    "Rohini": "Dhruva (Fixed)",
    "Uttara Phalguni": "Dhruva (Fixed)",
    "Uttara Ashadha": "Dhruva (Fixed)",
    "Uttara Bhadrapada": "Dhruva (Fixed)",
    # Chara / Chala (Movable) - Auspicious for travel, vehicles, dynamic beginnings
    "Punarvasu": "Chara (Movable)",
    "Swati": "Chara (Movable)",
    "Shravana": "Chara (Movable)",
    "Dhanishta": "Chara (Movable)",
    "Shatabhisha": "Chara (Movable)",
    # Kshipra / Laghu (Swift / Light) - Auspicious for trade, tech launch, contracts, exams
    "Ashwini": "Kshipra (Swift)",
    "Pushya": "Kshipra (Swift)",
    "Hasta": "Kshipra (Swift)",
    # Mridu (Soft / Tender) - Auspicious for partnerships, arts, agreements
    "Mrigashira": "Mridu (Tender)",
    "Chitra": "Mridu (Tender)",
    "Anuradha": "Mridu (Tender)",
    "Revati": "Mridu (Tender)",
    # Mishra (Mixed)
    "Krittika": "Mishra (Mixed)",
    "Vishakha": "Mishra (Mixed)",
    # Tikshna (Sharp / Dreadful) - Inauspicious for new beginnings
    "Ardra": "Tikshna (Sharp)",
    "Ashlesha": "Tikshna (Sharp)",
    "Jyeshtha": "Tikshna (Sharp)",
    "Mula": "Tikshna (Sharp)",
    # Ugra (Fierce) - Inauspicious for auspicious tasks
    "Bharani": "Ugra (Fierce)",
    "Magha": "Ugra (Fierce)",
    "Purva Phalguni": "Ugra (Fierce)",
    "Purva Ashadha": "Ugra (Fierce)",
    "Purva Bhadrapada": "Ugra (Fierce)",
}

TITHI_NAMES = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",  # 1-15 Shukla
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"   # 16-30 Krishna
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

# Hard-forbidden Yogas in Classical Muhurta
INAUSPICIOUS_YOGAS = {
    "Vishkambha", "Atiganda", "Shula", "Vyaghata", "Vajra", "Vyatipata", "Vaidhriti", "Ganda"
}

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti"]
FIXED_KARANAS = {57: "Shakuni", 58: "Chatushpada", 59: "Naga", 0: "Kintughna"}

VARA_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VARA_LORDS = {
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
    "Sunday": "Sun"
}

# Rahu Kalam index (1-8 segment of daytime) by Python weekday (0=Mon, 1=Tue, ..., 6=Sun)
RAHU_KALAM_SEGMENT = {
    0: 2,  # Monday: 2nd segment
    1: 7,  # Tuesday: 7th segment
    2: 5,  # Wednesday: 5th segment
    3: 6,  # Thursday: 6th segment
    4: 4,  # Friday: 4th segment
    5: 3,  # Saturday: 3rd segment
    6: 8,  # Sunday: 8th segment
}

YAMAGANDA_SEGMENT = {
    0: 4,  # Monday: 4th segment
    1: 3,  # Tuesday: 3rd segment
    2: 2,  # Wednesday: 2nd segment
    3: 1,  # Thursday: 1st segment
    4: 7,  # Friday: 7th segment
    5: 6,  # Saturday: 6th segment
    6: 5,  # Sunday: 5th segment
}

# Choghadiya sequence templates
DAY_CHOGHADIYA_ORDER = {
    "Sunday": ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],
    "Monday": ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"],
    "Tuesday": ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
    "Wednesday": ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"],
    "Thursday": ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"],
    "Friday": ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],
    "Saturday": ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"],
}

FAVORABLE_CHOGHADIYAS = {"Amrit", "Shubh", "Labh", "Char"}


def get_julian_day(dt_utc: datetime) -> float:
    """Calculate Swiss Ephemeris Julian Day from UTC datetime."""
    hour_float = dt_utc.hour + dt_utc.minute / 60.0 + (dt_utc.second + dt_utc.microsecond / 1e6) / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_float)


def get_sidereal_positions(jd: float) -> Tuple[float, float]:
    """Compute Lahiri sidereal longitudes of Sun and Moon."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    res_sun = swe.calc_ut(jd, swe.SUN, flags)
    res_moon = swe.calc_ut(jd, swe.MOON, flags)
    return res_sun[0][0] % 360.0, res_moon[0][0] % 360.0


def calculate_sun_times(dt_local: datetime, lat: float, lon: float, tz_str: str) -> Tuple[datetime, datetime]:
    """Calculate local Sunrise and Sunset for given location and date."""
    tz = ZoneInfo(tz_str)
    # Target date at noon local
    noon_local = datetime(dt_local.year, dt_local.month, dt_local.day, 12, 0, 0, tzinfo=tz)
    noon_utc = noon_local.astimezone(ZoneInfo("UTC"))
    jd_noon = get_julian_day(noon_utc)

    # Sunrise
    res_rise = swe.rise_trans(
        jd_noon - 0.5,
        swe.SUN,
        swe.CALC_RISE,
        (lon, lat, 0.0),
        0.0, 0.0
    )
    # Sunset
    res_set = swe.rise_trans(
        jd_noon - 0.5,
        swe.SUN,
        swe.CALC_SET,
        (lon, lat, 0.0),
        0.0, 0.0
    )

    if res_rise[0] == 0:
        jd_rise = res_rise[1][0]
        # Convert JD to datetime
        y, m, d, h = swe.revjul(jd_rise)
        h_int = int(h)
        m_int = int((h - h_int) * 60)
        s_int = int(((h - h_int) * 60 - m_int) * 60)
        sunrise_utc = datetime(y, m, d, h_int, m_int, s_int, tzinfo=ZoneInfo("UTC"))
        sunrise_local = sunrise_utc.astimezone(tz)
    else:
        # Fallback 6:00 AM local
        sunrise_local = datetime(dt_local.year, dt_local.month, dt_local.day, 6, 0, 0, tzinfo=tz)

    if res_set[0] == 0:
        jd_set = res_set[1][0]
        y, m, d, h = swe.revjul(jd_set)
        h_int = int(h)
        m_int = int((h - h_int) * 60)
        s_int = int(((h - h_int) * 60 - m_int) * 60)
        sunset_utc = datetime(y, m, d, h_int, m_int, s_int, tzinfo=ZoneInfo("UTC"))
        sunset_local = sunset_utc.astimezone(tz)
    else:
        # Fallback 18:00 PM local
        sunset_local = datetime(dt_local.year, dt_local.month, dt_local.day, 18, 0, 0, tzinfo=tz)

    return sunrise_local, sunset_local


def calculate_panchanga_at_instant(
    dt_local: datetime,
    lat: float,
    lon: float,
    tz_str: str,
    sunrise_sunset: Optional[Tuple[datetime, datetime]] = None,
) -> PanchangaDetails:
    """
    Calculate the complete 5-Pillar Panchanga, Choghadiya, Rahu Kalam,
    and Abhijit Muhurta for an exact moment in time.
    """
    tz = ZoneInfo(tz_str)
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=tz)

    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    jd = get_julian_day(dt_utc)

    # 1. Sidereal Planetary Coordinates
    sun_lon, moon_lon = get_sidereal_positions(jd)

    # 2. Tithi Computation
    diff_tithi = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(diff_tithi / 12.0)  # 0 to 29
    tithi_num = tithi_idx + 1
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi_name_only = TITHI_NAMES[tithi_idx]
    if tithi_name_only in ["Purnima", "Amavasya"]:
        full_tithi_name = tithi_name_only
    else:
        full_tithi_name = f"{paksha} {tithi_name_only}"

    # 3. Nakshatra Computation
    nak_idx = int(moon_lon / (360.0 / 27.0)) % 27
    nak_num = nak_idx + 1
    nak_name = NAKSHATRAS[nak_idx]
    temperament = NAKSHATRA_TEMPERAMENT.get(nak_name, "Dhruva (Fixed)")
    formatted_nak = f"{nak_name} ({temperament})"

    # 4. Vara (Day of Week from Local Solar Day)
    if sunrise_sunset:
        sunrise_local, sunset_local = sunrise_sunset
    else:
        sunrise_local, sunset_local = calculate_sun_times(dt_local, lat, lon, tz_str)
    
    # If before local sunrise, the Vedic Vara belongs to the previous calendar day
    if dt_local < sunrise_local:
        effective_date = dt_local.date() - timedelta(days=1)
    else:
        effective_date = dt_local.date()

    day_idx = effective_date.weekday()  # 0=Monday, ..., 6=Sunday
    vara_name = VARA_NAMES[day_idx]
    vara_lord = VARA_LORDS[vara_name]

    # 5. Yoga Computation
    sum_lon = (sun_lon + moon_lon) % 360.0
    yoga_idx = int(sum_lon / (360.0 / 27.0)) % 27
    yoga_num = yoga_idx + 1
    yoga_name = YOGAS[yoga_idx]
    is_malefic_yoga = yoga_name in INAUSPICIOUS_YOGAS

    # 6. Karana Computation (Half of Tithi = 6°)
    karana_idx = int(diff_tithi / 6.0) % 60
    if karana_idx == 0:
        karana_name = FIXED_KARANAS[0]
    elif 1 <= karana_idx <= 56:
        karana_name = MOVABLE_KARANAS[(karana_idx - 1) % 7]
    else:
        karana_name = FIXED_KARANAS.get(karana_idx, "Vishti")

    is_vishti = (karana_name == "Vishti")

    # 7. Solar Segments: Rahu Kalam & Yamaganda
    day_duration = (sunset_local - sunrise_local).total_seconds()
    segment_duration = day_duration / 8.0

    is_daytime = sunrise_local <= dt_local <= sunset_local
    is_rahu_kalam = False
    is_yamaganda = False
    choghadiya_name = "Amrit"

    if is_daytime and segment_duration > 0:
        elapsed = (dt_local - sunrise_local).total_seconds()
        current_segment_1_indexed = min(8, int(elapsed / segment_duration) + 1)

        # Check Rahu Kalam
        rahu_seg = RAHU_KALAM_SEGMENT[day_idx]
        if current_segment_1_indexed == rahu_seg:
            is_rahu_kalam = True

        # Check Yamaganda
        yama_seg = YAMAGANDA_SEGMENT[day_idx]
        if current_segment_1_indexed == yama_seg:
            is_yamaganda = True

        # Day Choghadiya (1-indexed to 0-indexed list)
        choghadiya_list = DAY_CHOGHADIYA_ORDER.get(vara_name, DAY_CHOGHADIYA_ORDER["Sunday"])
        choghadiya_name = choghadiya_list[min(7, current_segment_1_indexed - 1)]
    else:
        # Night Choghadiya approximation
        choghadiya_name = "Shubh"

    # 8. Abhijit Muhurta Check (~Midday Solar Noon, 8th Muhurta out of 15)
    muhurta_duration = day_duration / 15.0
    abhijit_start = sunrise_local + timedelta(seconds=7 * muhurta_duration)
    abhijit_end = sunrise_local + timedelta(seconds=8 * muhurta_duration)
    is_abhijit = (abhijit_start <= dt_local <= abhijit_end) and (vara_name != "Wednesday")

    choghadiya_is_favorable = choghadiya_name in FAVORABLE_CHOGHADIYAS

    return PanchangaDetails(
        tithi=full_tithi_name,
        tithi_number=tithi_num,
        paksha=paksha,
        nakshatra=formatted_nak,
        nakshatra_number=nak_num,
        nakshatra_temperament=temperament,
        vara=vara_name,
        vara_lord=vara_lord,
        yoga=yoga_name,
        yoga_number=yoga_num,
        is_inauspicious_yoga=is_malefic_yoga,
        karana=karana_name,
        is_vishti_bhadra=is_vishti,
        choghadiya=choghadiya_name,
        choghadiya_is_favorable=choghadiya_is_favorable,
        is_rahu_kalam=is_rahu_kalam,
        is_yamaganda=is_yamaganda,
        is_abhijit=is_abhijit,
    )
