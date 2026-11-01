"""Live Planetary Transits (Gochara) Engine using Swiss Ephemeris.

Calculates real-time celestial positions for today and overlays them against
the user's natal Lagna and natal Moon (Chandra Lagna).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import swisseph as swe

from chart.engine import SIGNS, SWE_PLANETS, format_degree
from chart.nakshatra import calculate_nakshatra


class TransitPlanet(BaseModel):
    planet: str
    sign: str
    sign_number: int
    degree: float
    formatted_degree: str
    is_retrograde: bool
    speed: float
    house_from_lagna: Optional[int] = None
    house_from_moon: int
    nakshatra_name: str
    is_favorable_from_moon: bool = False
    transit_significance: str = ""


class GocharaReport(BaseModel):
    calculated_at_utc: str
    natal_lagna: Optional[str] = None
    natal_moon_sign: str
    transits: List[TransitPlanet]
    sade_sati_status: str
    sade_sati_active: bool
    jupiter_transit_summary: str
    saturn_transit_summary: str


# Traditional Gochara favorable houses from Natal Moon (Phaladeepika Ch. 26)
FAVORABLE_FROM_MOON = {
    "Sun": {3, 6, 10, 11},
    "Moon": {1, 3, 6, 7, 10, 11},
    "Mars": {3, 6, 11},
    "Mercury": {2, 4, 6, 8, 10, 11},
    "Jupiter": {2, 5, 7, 9, 11},
    "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "Saturn": {3, 6, 11},
    "Rahu": {3, 6, 10, 11},
    "Ketu": {3, 6, 11},
}


def calculate_today_transits(
    natal_lagna_sign_num: Optional[int],
    natal_moon_sign_num: int,
    target_dt: Optional[datetime] = None,
) -> GocharaReport:
    """Calculate today's real-time planetary transits overlaid on natal chart."""
    if target_dt is None:
        target_dt = datetime.now(timezone.utc)

    # Configure Swiss Ephemeris Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    hour_ut = target_dt.hour + (target_dt.minute / 60.0) + (target_dt.second / 3600.0)
    jd_ut = swe.julday(target_dt.year, target_dt.month, target_dt.day, hour_ut)

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    transits: List[TransitPlanet] = []

    for name, p_id in SWE_PLANETS:
        res = swe.calc_ut(jd_ut, p_id, flags)
        lon = res[0][0] % 360.0
        speed = res[0][3]
        is_retro = speed < 0.0

        sign_num = int(lon // 30.0) + 1
        sign_name = SIGNS[sign_num - 1]
        deg = lon - ((sign_num - 1) * 30.0)

        house_from_lagna = None
        if natal_lagna_sign_num is not None:
            house_from_lagna = ((sign_num - natal_lagna_sign_num) % 12) + 1

        house_from_moon = ((sign_num - natal_moon_sign_num) % 12) + 1
        nak = calculate_nakshatra(lon)
        is_fav = house_from_moon in FAVORABLE_FROM_MOON.get(name, set())

        # Significance summary
        signif = f"Transiting House {house_from_moon} from your Moon sign ({sign_name})"
        if house_from_lagna:
            signif += f" and House {house_from_lagna} from Lagna"

        transits.append(
            TransitPlanet(
                planet=name,
                sign=sign_name,
                sign_number=sign_num,
                degree=round(deg, 4),
                formatted_degree=format_degree(deg),
                is_retrograde=is_retro,
                speed=round(speed, 6),
                house_from_lagna=house_from_lagna,
                house_from_moon=house_from_moon,
                nakshatra_name=nak.name,
                is_favorable_from_moon=is_fav,
                transit_significance=signif,
            )
        )

    # 8. Rahu (Mean Node)
    rahu_res = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
    rahu_lon = rahu_res[0][0] % 360.0
    rahu_speed = rahu_res[0][3]
    rahu_sign_num = int(rahu_lon // 30.0) + 1
    rahu_sign_name = SIGNS[rahu_sign_num - 1]
    rahu_deg = rahu_lon - ((rahu_sign_num - 1) * 30.0)
    rahu_house_lagna = (((rahu_sign_num - natal_lagna_sign_num) % 12) + 1) if natal_lagna_sign_num else None
    rahu_house_moon = ((rahu_sign_num - natal_moon_sign_num) % 12) + 1
    rahu_nak = calculate_nakshatra(rahu_lon)
    rahu_fav = rahu_house_moon in FAVORABLE_FROM_MOON.get("Rahu", {3, 6, 10, 11})

    transits.append(
        TransitPlanet(
            planet="Rahu",
            sign=rahu_sign_name,
            sign_number=rahu_sign_num,
            degree=round(rahu_deg, 4),
            formatted_degree=format_degree(rahu_deg),
            is_retrograde=True,
            speed=round(rahu_speed, 6),
            house_from_lagna=rahu_house_lagna,
            house_from_moon=rahu_house_moon,
            nakshatra_name=rahu_nak.name,
            is_favorable_from_moon=rahu_fav,
            transit_significance=f"Transiting House {rahu_house_moon} from Moon ({rahu_sign_name})",
        )
    )

    # 9. Ketu (180 deg from Rahu)
    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_sign_num = int(ketu_lon // 30.0) + 1
    ketu_sign_name = SIGNS[ketu_sign_num - 1]
    ketu_deg = ketu_lon - ((ketu_sign_num - 1) * 30.0)
    ketu_house_lagna = (((ketu_sign_num - natal_lagna_sign_num) % 12) + 1) if natal_lagna_sign_num else None
    ketu_house_moon = ((ketu_sign_num - natal_moon_sign_num) % 12) + 1
    ketu_nak = calculate_nakshatra(ketu_lon)
    ketu_fav = ketu_house_moon in FAVORABLE_FROM_MOON.get("Ketu", {3, 6, 11})

    transits.append(
        TransitPlanet(
            planet="Ketu",
            sign=ketu_sign_name,
            sign_number=ketu_sign_num,
            degree=round(ketu_deg, 4),
            formatted_degree=format_degree(ketu_deg),
            is_retrograde=True,
            speed=round(rahu_speed, 6),
            house_from_lagna=ketu_house_lagna,
            house_from_moon=ketu_house_moon,
            nakshatra_name=ketu_nak.name,
            is_favorable_from_moon=ketu_fav,
            transit_significance=f"Transiting House {ketu_house_moon} from Moon ({ketu_sign_name})",
        )
    )

    # Check Sade Sati (Saturn in 12th, 1st, or 2nd from natal Moon)
    saturn_transit = next(p for p in transits if p.planet == "Saturn")
    saturn_house_moon = saturn_transit.house_from_moon

    sade_sati_active = False
    sade_sati_status = "No Sade Sati active"

    if saturn_house_moon == 12:
        sade_sati_active = True
        sade_sati_status = "Sade Sati Phase 1 (Rising Phase): Transiting 12th house from Moon. Focus on emotional resilience, foreign travel, and careful expenditure."
    elif saturn_house_moon == 1:
        sade_sati_active = True
        sade_sati_status = "Sade Sati Phase 2 (Peak Phase): Transiting over natal Moon. Tests personal discipline, inner maturity, and patience under pressure."
    elif saturn_house_moon == 2:
        sade_sati_active = True
        sade_sati_status = "Sade Sati Phase 3 (Setting Phase): Transiting 2nd house from Moon. Financial consolidation and family balance."
    elif saturn_house_moon in (4, 8):
        sade_sati_status = f"Dhaiya (Small Panoti): Saturn transiting House {saturn_house_moon} from Moon. Prompts steady structural diligence."

    # Jupiter Transit Summary (Guru Gochara)
    jupiter_transit = next(p for p in transits if p.planet == "Jupiter")
    j_house_moon = jupiter_transit.house_from_moon
    if jupiter_transit.is_favorable_from_moon:
        jupiter_summary = f"Jupiter transits House {j_house_moon} from your Moon ({jupiter_transit.sign}), an auspicious position promoting wisdom, expansion, and positive recognition."
    else:
        jupiter_summary = f"Jupiter transits House {j_house_moon} from your Moon ({jupiter_transit.sign}), encouraging introspective spiritual growth and measured expansion."

    saturn_summary = f"Saturn transits House {saturn_house_moon} from your Moon in {saturn_transit.sign} at {saturn_transit.formatted_degree}."

    natal_lagna_name = SIGNS[natal_lagna_sign_num - 1] if natal_lagna_sign_num else None
    natal_moon_name = SIGNS[natal_moon_sign_num - 1]

    return GocharaReport(
        calculated_at_utc=target_dt.strftime("%Y-%m-%d %H:%M UTC"),
        natal_lagna=natal_lagna_name,
        natal_moon_sign=natal_moon_name,
        transits=transits,
        sade_sati_status=sade_sati_status,
        sade_sati_active=sade_sati_active,
        jupiter_transit_summary=jupiter_summary,
        saturn_transit_summary=saturn_summary,
    )
