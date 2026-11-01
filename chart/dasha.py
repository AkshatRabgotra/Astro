"""Vimshottari Dasha calculation module (Mahadasha and Antardasha)."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from chart.models import DashaPeriod
from chart.nakshatra import NAKSHATRAS, NAKSHATRA_SPAN

# Vimshottari Dasha periods in solar years (total 120 years)
VIMSHOTTARI_LORDS = [
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17),
]

LORD_DURATIONS: Dict[str, float] = {lord: years for lord, years in VIMSHOTTARI_LORDS}
LORD_ORDER: List[str] = [lord for lord, _ in VIMSHOTTARI_LORDS]

DAYS_PER_YEAR = 365.2425


def calculate_vimshottari_periods(
    moon_longitude: float,
    birth_dt: datetime,
    target_dt: Optional[datetime] = None,
    is_approximate: bool = False,
) -> Tuple[DashaPeriod, List[DashaPeriod]]:
    """
    Calculate Vimshottari Mahadasha and Antardashas.
    Returns:
        (current_dasha, all_mahadashas_summary)
    """
    if target_dt is None:
        target_dt = datetime.now()

    lon = moon_longitude % 360.0
    nak_idx = int(lon // NAKSHATRA_SPAN)
    if nak_idx >= 27:
        nak_idx = 26

    _, birth_lord = NAKSHATRAS[nak_idx]
    deg_in_nak = lon - (nak_idx * NAKSHATRA_SPAN)
    fraction_elapsed = deg_in_nak / NAKSHATRA_SPAN
    fraction_remaining = 1.0 - fraction_elapsed

    # Find birth lord index in VIMSHOTTARI_LORDS
    start_lord_idx = LORD_ORDER.index(birth_lord)
    birth_lord_years = LORD_DURATIONS[birth_lord]

    # Calculate starting Mahadasha window
    elapsed_days = fraction_elapsed * birth_lord_years * DAYS_PER_YEAR
    remaining_days = fraction_remaining * birth_lord_years * DAYS_PER_YEAR

    first_md_start = birth_dt - timedelta(days=elapsed_days)
    first_md_end = birth_dt + timedelta(days=remaining_days)

    # Build sequence of Mahadashas up to 120 years
    mahadashas: List[Tuple[str, datetime, datetime]] = []
    current_start = first_md_start
    current_end = first_md_end

    for i in range(len(LORD_ORDER) * 2):  # Cover up to ~240 years if needed
        lord = LORD_ORDER[(start_lord_idx + i) % len(LORD_ORDER)]
        if i == 0:
            mahadashas.append((lord, current_start, current_end))
            current_start = current_end
        else:
            years = LORD_DURATIONS[lord]
            current_end = current_start + timedelta(days=years * DAYS_PER_YEAR)
            mahadashas.append((lord, current_start, current_end))
            current_start = current_end
            
        if current_start > target_dt + timedelta(days=365.25 * 30):
            break

    # Locate the active Mahadasha for target_dt
    active_md = mahadashas[0]
    for md in mahadashas:
        if md[1] <= target_dt < md[2]:
            active_md = md
            break
        if md[1] > target_dt:
            break

    md_lord, md_start, md_end = active_md
    md_total_duration = md_end - md_start

    # Calculate 9 Antardashas within active Mahadasha
    md_lord_idx = LORD_ORDER.index(md_lord)
    ad_runner = md_start
    active_ad = (LORD_ORDER[md_lord_idx], md_start, md_end)
    all_antardashas: List[DashaPeriod] = []

    for j in range(len(LORD_ORDER)):
        ad_lord = LORD_ORDER[(md_lord_idx + j) % len(LORD_ORDER)]
        ad_years = LORD_DURATIONS[ad_lord]
        ad_fraction = ad_years / 120.0
        ad_duration = timedelta(days=md_total_duration.total_seconds() / 86400.0 * ad_fraction)
        ad_finish = ad_runner + ad_duration

        if ad_runner <= target_dt < ad_finish:
            active_ad = (ad_lord, ad_runner, ad_finish)

        all_antardashas.append(
            DashaPeriod(
                mahadasha_lord=md_lord,
                antardasha_lord=ad_lord,
                start_date=ad_runner.strftime("%Y-%m-%d"),
                end_date=ad_finish.strftime("%Y-%m-%d"),
                is_approximate=is_approximate,
            )
        )
        ad_runner = ad_finish

    # Calculate 9 Pratyantardashas within active Antardasha
    ad_lord_name, ad_active_start, ad_active_end = active_ad
    ad_total_seconds = (ad_active_end - ad_active_start).total_seconds()
    ad_lord_idx = LORD_ORDER.index(ad_lord_name)
    pd_runner = ad_active_start
    active_pd = (ad_lord_name, ad_active_start, ad_active_end)

    for k in range(len(LORD_ORDER)):
        pd_lord = LORD_ORDER[(ad_lord_idx + k) % len(LORD_ORDER)]
        pd_years = LORD_DURATIONS[pd_lord]
        pd_fraction = pd_years / 120.0
        pd_duration = timedelta(days=ad_total_seconds / 86400.0 * pd_fraction)
        pd_finish = pd_runner + pd_duration

        if pd_runner <= target_dt < pd_finish:
            active_pd = (pd_lord, pd_runner, pd_finish)
            break
        pd_runner = pd_finish

    current_dasha = DashaPeriod(
        mahadasha_lord=md_lord,
        antardasha_lord=active_ad[0],
        pratyantardasha_lord=active_pd[0],
        start_date=active_ad[1].strftime("%Y-%m-%d"),
        end_date=active_ad[2].strftime("%Y-%m-%d"),
        is_approximate=is_approximate,
    )

    all_summaries = []
    for md in mahadashas:
        all_summaries.append(
            DashaPeriod(
                mahadasha_lord=md[0],
                antardasha_lord=md[0],  # Indicating start of MD
                pratyantardasha_lord=md[0],
                start_date=md[1].strftime("%Y-%m-%d"),
                end_date=md[2].strftime("%Y-%m-%d"),
                is_approximate=is_approximate,
            )
        )

    return current_dasha, all_summaries, all_antardashas


def get_dasha_hierarchy_at_date(
    moon_longitude: float,
    birth_dt: datetime,
    target_dt: datetime,
    is_approximate: bool = False,
) -> Dict[str, Any]:
    """
    Get full Mahadasha, Antardasha, and Pratyantardasha at a specific target date.
    Deterministic and pure function.
    """
    curr, _, _ = calculate_vimshottari_periods(
        moon_longitude=moon_longitude,
        birth_dt=birth_dt,
        target_dt=target_dt,
        is_approximate=is_approximate,
    )
    return {
        "mahadasha_lord": curr.mahadasha_lord,
        "antardasha_lord": curr.antardasha_lord,
        "pratyantar_lord": curr.pratyantardasha_lord,
        "start_date": curr.start_date,
        "end_date": curr.end_date,
        "is_approximate": is_approximate,
    }
