"""Vedic Astrology Chart Engine using Swiss Ephemeris (Lahiri Sidereal)."""

from datetime import date, datetime, time, timedelta, timezone
import re
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
import swisseph as swe

from chart.aspects import SIGNS, calculate_aspects
from chart.dasha import calculate_vimshottari_periods
from chart.models import (
    BirthInput,
    ChartFact,
    ChartFacts,
    DashaPeriod,
    NakshatraDetail,
    PlanetPosition,
)
from chart.nakshatra import calculate_nakshatra

# Exaltation and Debilitation signs (1-indexed: 1 = Aries, ..., 12 = Pisces)
EXALTATION_SIGNS = {
    "Sun": 1,        # Aries
    "Moon": 2,       # Taurus
    "Mars": 10,      # Capricorn
    "Mercury": 6,    # Virgo
    "Jupiter": 4,    # Cancer
    "Venus": 12,     # Pisces
    "Saturn": 7,     # Libra
}

DEBILITATION_SIGNS = {
    "Sun": 7,        # Libra
    "Moon": 8,       # Scorpio
    "Mars": 4,       # Cancer
    "Mercury": 12,   # Pisces
    "Jupiter": 10,   # Capricorn
    "Venus": 6,      # Virgo
    "Saturn": 1,     # Aries
}

SWE_PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
]


def format_degree(degree_val: float) -> str:
    """Format floating degree to string like 15°22'."""
    deg = int(degree_val)
    minute_val = round((degree_val - deg) * 60)
    if minute_val == 60:
        deg += 1
        minute_val = 0
    return f"{deg}°{minute_val:02d}'"


def parse_timezone(tz_str: str) -> timezone:
    """Parse IANA string ('Asia/Kolkata') or offset string ('+05:30', '-04:00', 'UTC')."""
    cleaned = tz_str.strip()
    if cleaned.upper() in ("UTC", "GMT", "Z"):
        return timezone.utc

    offset_match = re.match(r"^([+-])(\d{1,2}):?(\d{2})?$", cleaned)
    if offset_match:
        sign, hours, minutes = offset_match.groups()
        mins = int(minutes) if minutes else 0
        delta = timedelta(hours=int(hours), minutes=mins)
        if sign == "-":
            delta = -delta
        return timezone(delta)

    try:
        return ZoneInfo(cleaned)  # type: ignore
    except Exception:
        # Fallback to UTC if timezone is invalid
        return timezone.utc


def get_utc_datetime(birth_input: BirthInput) -> Tuple[datetime, bool]:
    """
    Returns (utc_datetime, is_approximate).
    If time_known is False or birth_time is None, local noon (12:00:00) is used as reference.
    """
    tz = parse_timezone(birth_input.timezone_str)
    
    if birth_input.time_known and birth_input.birth_time:
        parts = [int(p) for p in birth_input.birth_time.split(":") if p.strip()]
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else 0
        second = parts[2] if len(parts) > 2 else 0
        local_dt = datetime.combine(birth_input.birth_date, time(hour, minute, second), tzinfo=tz)
        return local_dt.astimezone(timezone.utc), False
    else:
        # Reference noon for approximate slow planet placements
        local_dt = datetime.combine(birth_input.birth_date, time(12, 0, 0), tzinfo=tz)
        return local_dt.astimezone(timezone.utc), True


def calculate_chart_facts(
    birth_input: BirthInput,
    target_dt: Optional[datetime] = None
) -> ChartFacts:
    """
    Main entry point: turns birth inputs into complete, validated ChartFacts.
    Pure Python, deterministic, grounds every fact with a stable ID.
    """
    # Configure Swiss Ephemeris for Lahiri Sidereal Zodiac
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    utc_dt, is_time_approx = get_utc_datetime(birth_input)
    hour_ut = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0) + (utc_dt.microsecond / 3.6e9)
    jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_ut)

    ayanamsa_val = swe.get_ayanamsa_ut(jd_ut)

    # 1. Ascendant (Lagna) & Houses
    lagna_sign_name: Optional[str] = None
    lagna_sign_num: Optional[int] = None
    lagna_deg: Optional[float] = None
    formatted_lagna_deg: Optional[str] = None

    time_is_known = birth_input.time_known and (birth_input.birth_time is not None)

    if time_is_known:
        # Whole sign houses: 'W'
        cusps, ascmc = swe.houses_ex(jd_ut, birth_input.latitude, birth_input.longitude, b"W", swe.FLG_SIDEREAL)
        asc_deg_total = ascmc[0] % 360.0
        lagna_sign_num = int(asc_deg_total // 30.0) + 1
        lagna_sign_name = SIGNS[lagna_sign_num - 1]
        lagna_deg = asc_deg_total - ((lagna_sign_num - 1) * 30.0)
        formatted_lagna_deg = format_degree(lagna_deg)

    # 2. Planetary positions
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    calculated_planets: List[PlanetPosition] = []

    for name, p_id in SWE_PLANETS:
        res = swe.calc_ut(jd_ut, p_id, flags)
        coords = res[0]
        lon = coords[0] % 360.0
        speed = coords[3]
        is_retrograde = speed < 0.0

        sign_num = int(lon // 30.0) + 1
        sign_name = SIGNS[sign_num - 1]
        sign_deg = lon - ((sign_num - 1) * 30.0)

        # Whole-sign house
        house: Optional[int] = None
        if lagna_sign_num is not None:
            house = ((sign_num - lagna_sign_num) % 12) + 1

        nak_detail = calculate_nakshatra(lon)
        is_exalted = (EXALTATION_SIGNS.get(name) == sign_num)
        is_debilitated = (DEBILITATION_SIGNS.get(name) == sign_num)

        calculated_planets.append(
            PlanetPosition(
                planet=name,
                longitude=round(lon, 4),
                sign=sign_name,
                sign_number=sign_num,
                sign_degree=round(sign_deg, 4),
                formatted_sign_degree=format_degree(sign_deg),
                house=house,
                nakshatra=nak_detail,
                is_retrograde=is_retrograde,
                speed=round(speed, 6),
                is_exalted=is_exalted,
                is_debilitated=is_debilitated,
            )
        )

    # Rahu (Mean Lunar Node)
    rahu_res = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
    rahu_lon = rahu_res[0][0] % 360.0
    rahu_speed = rahu_res[0][3]
    rahu_sign_num = int(rahu_lon // 30.0) + 1
    rahu_sign_name = SIGNS[rahu_sign_num - 1]
    rahu_sign_deg = rahu_lon - ((rahu_sign_num - 1) * 30.0)
    rahu_house = (((rahu_sign_num - lagna_sign_num) % 12) + 1) if lagna_sign_num else None

    calculated_planets.append(
        PlanetPosition(
            planet="Rahu",
            longitude=round(rahu_lon, 4),
            sign=rahu_sign_name,
            sign_number=rahu_sign_num,
            sign_degree=round(rahu_sign_deg, 4),
            formatted_sign_degree=format_degree(rahu_sign_deg),
            house=rahu_house,
            nakshatra=calculate_nakshatra(rahu_lon),
            is_retrograde=True,
            speed=round(rahu_speed, 6),
            is_exalted=False,
            is_debilitated=False,
        )
    )

    # Ketu (180 degrees from Rahu)
    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_sign_num = int(ketu_lon // 30.0) + 1
    ketu_sign_name = SIGNS[ketu_sign_num - 1]
    ketu_sign_deg = ketu_lon - ((ketu_sign_num - 1) * 30.0)
    ketu_house = (((ketu_sign_num - lagna_sign_num) % 12) + 1) if lagna_sign_num else None

    calculated_planets.append(
        PlanetPosition(
            planet="Ketu",
            longitude=round(ketu_lon, 4),
            sign=ketu_sign_name,
            sign_number=ketu_sign_num,
            sign_degree=round(ketu_sign_deg, 4),
            formatted_sign_degree=format_degree(ketu_sign_deg),
            house=ketu_house,
            nakshatra=calculate_nakshatra(ketu_lon),
            is_retrograde=True,
            speed=round(rahu_speed, 6),
            is_exalted=False,
            is_debilitated=False,
        )
    )

    # 3. Vimshottari Dasha
    moon_planet = next(p for p in calculated_planets if p.planet == "Moon")
    current_dasha, all_dashas, antardashas = calculate_vimshottari_periods(
        moon_longitude=moon_planet.longitude,
        birth_dt=utc_dt,
        target_dt=target_dt or datetime.now(timezone.utc),
        is_approximate=is_time_approx,
    )

    # 4. Aspects
    aspects = calculate_aspects(calculated_planets, lagna_sign_num)

    # 5. Build stable atomic ChartFacts list
    facts: List[ChartFact] = []

    # F01: Lagna (Ascendant)
    if time_is_known and lagna_sign_name is not None and lagna_deg is not None:
        facts.append(
            ChartFact(
                id="F01",
                category="lagna",
                subject="Lagna",
                text=f"Lagna (Ascendant) in {lagna_sign_name} at {formatted_lagna_deg} (House 1)",
                is_time_dependent=True,
                is_available=True,
                metadata={
                    "sign": lagna_sign_name,
                    "sign_number": lagna_sign_num,
                    "degree": round(lagna_deg, 4),
                    "formatted_degree": formatted_lagna_deg,
                    "house": 1,
                },
            )
        )
    else:
        facts.append(
            ChartFact(
                id="F01",
                category="lagna",
                subject="Lagna",
                text="Ascendant (Lagna) is unavailable because exact birth time was not provided.",
                is_time_dependent=True,
                is_available=False,
                metadata={"reason": "unknown_birth_time"},
            )
        )

    # F02: Moon Nakshatra
    nak = moon_planet.nakshatra
    moon_approx_str = " (approximate position, birth time not provided)" if is_time_approx else ""
    facts.append(
        ChartFact(
            id="F02",
            category="nakshatra",
            subject="Moon Nakshatra",
            text=(
                f"Moon in Nakshatra {nak.name} (Pada {nak.pada}, lord {nak.lord}) "
                f"in {moon_planet.sign} at {moon_planet.formatted_sign_degree}{moon_approx_str}"
            ),
            is_time_dependent=is_time_approx,
            is_available=True,
            metadata={
                "nakshatra_name": nak.name,
                "pada": nak.pada,
                "lord": nak.lord,
                "sign": moon_planet.sign,
                "sign_number": moon_planet.sign_number,
                "degree": moon_planet.sign_degree,
                "is_approximate": is_time_approx,
            },
        )
    )

    # F03 to F11: 9 Planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
    planet_id_map = {
        "Sun": "F03",
        "Moon": "F04",
        "Mars": "F05",
        "Mercury": "F06",
        "Jupiter": "F07",
        "Venus": "F08",
        "Saturn": "F09",
        "Rahu": "F10",
        "Ketu": "F11",
    }

    for p in calculated_planets:
        fid = planet_id_map[p.planet]
        dignity_parts = []
        if p.is_exalted:
            dignity_parts.append("Exalted")
        elif p.is_debilitated:
            dignity_parts.append("Debilitated")
        if p.is_retrograde and p.planet not in ("Rahu", "Ketu"):
            dignity_parts.append("Retrograde")

        dignity_str = f" ({', '.join(dignity_parts)})" if dignity_parts else ""

        if time_is_known and p.house is not None:
            text = (
                f"{p.planet} in {p.sign}, House {p.house} at {p.formatted_sign_degree}{dignity_str}, "
                f"Nakshatra {p.nakshatra.name} (Pada {p.nakshatra.pada})"
            )
        else:
            text = (
                f"{p.planet} in {p.sign} at {p.formatted_sign_degree}{dignity_str}, "
                f"Nakshatra {p.nakshatra.name} (House unavailable without birth time)"
            )

        facts.append(
            ChartFact(
                id=fid,
                category="planet",
                subject=p.planet,
                text=text,
                is_time_dependent=not time_is_known,
                is_available=True,
                metadata={
                    "planet": p.planet,
                    "sign": p.sign,
                    "sign_number": p.sign_number,
                    "house": p.house,
                    "degree": p.sign_degree,
                    "is_retrograde": p.is_retrograde,
                    "is_exalted": p.is_exalted,
                    "is_debilitated": p.is_debilitated,
                    "nakshatra": p.nakshatra.name,
                    "nakshatra_pada": p.nakshatra.pada,
                },
            )
        )

    # F12: Current Mahadasha / Antardasha
    dasha_approx_str = " [approximate]" if is_time_approx else ""
    facts.append(
        ChartFact(
            id="F12",
            category="dasha",
            subject="Current Dasha",
            text=(
                f"Current Mahadasha: {current_dasha.mahadasha_lord}, "
                f"Antardasha: {current_dasha.antardasha_lord} "
                f"({current_dasha.start_date} to {current_dasha.end_date}){dasha_approx_str}"
            ),
            is_time_dependent=is_time_approx,
            is_available=True,
            metadata={
                "mahadasha": current_dasha.mahadasha_lord,
                "antardasha": current_dasha.antardasha_lord,
                "start_date": current_dasha.start_date,
                "end_date": current_dasha.end_date,
                "is_approximate": is_time_approx,
            },
        )
    )

    # F13 to F21: Key Planetary Aspects
    aspect_id_map = {
        "Mars": "F13",
        "Jupiter": "F14",
        "Saturn": "F15",
        "Sun": "F16",
        "Moon": "F17",
        "Mercury": "F18",
        "Venus": "F19",
        "Rahu": "F20",
        "Ketu": "F21",
    }

    # Group aspects by aspecting planet
    aspects_by_planet: Dict[str, List[str]] = {p: [] for p in aspect_id_map.keys()}
    for asp in aspects:
        target_info = f"{asp.target_sign}"
        if asp.target_house is not None:
            target_info += f" (House {asp.target_house})"
        if asp.target_planets:
            target_info += f" containing {', '.join(asp.target_planets)}"
        aspects_by_planet[asp.aspecting_planet].append(f"{asp.aspect_type} aspect to {target_info}")

    for planet_name, fid in aspect_id_map.items():
        asp_list = aspects_by_planet.get(planet_name, [])
        planet_obj = next((p for p in calculated_planets if p.planet == planet_name), None)
        origin_str = f"{planet_name} in {planet_obj.sign}" if planet_obj else planet_name
        if planet_obj and planet_obj.house is not None:
            origin_str += f" (House {planet_obj.house})"

        if asp_list:
            aspect_desc = "; ".join(asp_list)
            text = f"{origin_str} casts {aspect_desc}"
        else:
            text = f"{origin_str} casts no special aspects"

        facts.append(
            ChartFact(
                id=fid,
                category="aspect",
                subject=f"{planet_name} Aspects",
                text=text,
                is_time_dependent=not time_is_known,
                is_available=True,
                metadata={
                    "planet": planet_name,
                    "aspects_count": len(asp_list),
                    "houses_available": time_is_known,
                },
            )
        )

    return ChartFacts(
        birth_input=birth_input,
        calculated_at_utc=datetime.now(timezone.utc),
        ayanamsa_name="Lahiri",
        ayanamsa_value=round(ayanamsa_val, 6),
        time_known=time_is_known,
        lagna_sign=lagna_sign_name,
        lagna_sign_number=lagna_sign_num,
        lagna_degree=round(lagna_deg, 4) if lagna_deg is not None else None,
        formatted_lagna_degree=formatted_lagna_deg,
        planets=calculated_planets,
        current_dasha=current_dasha,
        all_dashas=all_dashas,
        antardashas=antardashas,
        aspects=aspects,
        facts=facts,
    )
