"""Vimshottari Dasha calculation module (Mahadasha and Antardasha)."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
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
    ad_start = md_start
    active_ad = (LORD_ORDER[md_lord_idx], md_start, md_end)

    for j in range(len(LORD_ORDER)):
        ad_lord = LORD_ORDER[(md_lord_idx + j) % len(LORD_ORDER)]
        ad_years = LORD_DURATIONS[ad_lord]
        ad_fraction = ad_years / 120.0
        ad_duration = timedelta(days=md_total_duration.total_seconds() / 86400.0 * ad_fraction)
        ad_end = ad_start + ad_duration
        
        if ad_start <= target_dt < ad_end:
            active_ad = (ad_lord, ad_start, ad_end)
            break
        ad_start = ad_end

    current_dasha = DashaPeriod(
        mahadasha_lord=md_lord,
        antardasha_lord=active_ad[0],
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
                start_date=md[1].strftime("%Y-%m-%d"),
                end_date=md[2].strftime("%Y-%m-%d"),
                is_approximate=is_approximate,
            )
        )

    return current_dasha, all_summaries
