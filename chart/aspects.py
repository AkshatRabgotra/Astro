"""Parashari aspect calculations for Vedic Astrology."""

from typing import Dict, List, Optional, Tuple
from chart.models import AspectRelation, PlanetPosition

# Sign names 1 to 12
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Aspect definitions: planet -> list of (aspect_type_name, sign_offset)
# Offsets are 0-indexed relative to current sign (e.g. 7th house aspect = offset 6)
ASPECT_RULES: Dict[str, List[Tuple[str, int]]] = {
    "Sun": [("7th", 6)],
    "Moon": [("7th", 6)],
    "Mars": [("4th", 3), ("7th", 6), ("8th", 7)],
    "Mercury": [("7th", 6)],
    "Jupiter": [("5th", 4), ("7th", 6), ("9th", 8)],
    "Venus": [("7th", 6)],
    "Saturn": [("3rd", 2), ("7th", 6), ("10th", 9)],
    "Rahu": [("5th", 4), ("7th", 6), ("9th", 8)],
    "Ketu": [("5th", 4), ("7th", 6), ("9th", 8)],
}


def calculate_aspects(
    planets: List[PlanetPosition],
    lagna_sign_number: Optional[int] = None
) -> List[AspectRelation]:
    """
    Calculate all planetary aspects according to Vedic Parashara rules.
    If lagna_sign_number is None (unknown birth time), houses remain None.
    """
    # Map sign number (1-12) to list of planets present
    planets_by_sign: Dict[int, List[str]] = {s: [] for s in range(1, 13)}
    for p in planets:
        planets_by_sign[p.sign_number].append(p.planet)

    relations: List[AspectRelation] = []

    for p in planets:
        rules = ASPECT_RULES.get(p.planet, [("7th", 6)])
        from_sign_num = p.sign_number
        from_house = p.house

        for aspect_name, offset in rules:
            target_sign_num = ((from_sign_num - 1 + offset) % 12) + 1
            target_sign = SIGNS[target_sign_num - 1]

            target_house: Optional[int] = None
            if lagna_sign_number is not None and from_house is not None:
                target_house = ((from_house - 1 + offset) % 12) + 1

            target_planets = planets_by_sign.get(target_sign_num, [])

            relations.append(
                AspectRelation(
                    aspecting_planet=p.planet,
                    from_sign=p.sign,
                    from_house=from_house,
                    aspect_type=aspect_name,
                    target_sign=target_sign,
                    target_house=target_house,
                    target_planets=list(target_planets),
                )
            )

    return relations
