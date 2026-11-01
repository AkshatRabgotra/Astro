"""Pydantic data models for Vedic Astrology Chart Engine."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BirthInput(BaseModel):
    """User birth input parameters."""
    birth_date: date = Field(..., description="Date of birth in YYYY-MM-DD")
    birth_time: Optional[str] = Field(None, description="Time of birth in HH:MM or HH:MM:SS (24h). None if unknown.")
    time_known: bool = Field(True, description="Whether the exact birth time is known.")
    latitude: float = Field(..., description="Latitude of birth place (-90 to +90)")
    longitude: float = Field(..., description="Longitude of birth place (-180 to +180)")
    timezone_str: str = Field(..., description="IANA timezone (e.g. 'Asia/Kolkata') or UTC offset (e.g. '+05:30')")
    place_name: Optional[str] = Field(None, description="Human readable place name (e.g. 'New Delhi, India')")


class NakshatraDetail(BaseModel):
    """Nakshatra information for a celestial body."""
    number: int = Field(..., description="Nakshatra index 1 to 27")
    name: str = Field(..., description="Nakshatra name, e.g. 'Rohini'")
    pada: int = Field(..., description="Pada (quarter) 1 to 4")
    lord: str = Field(..., description="Vimshottari lord of the nakshatra")
    degree_in_nakshatra: float = Field(..., description="Degrees traversed in this nakshatra (0 to 13.333)")


class PlanetPosition(BaseModel):
    """Calculated position of a planet in the sidereal zodiac."""
    planet: str = Field(..., description="Planet name (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)")
    longitude: float = Field(..., description="Absolute sidereal longitude (0 to 360)")
    sign: str = Field(..., description="Zodiac sign name (Aries to Pisces)")
    sign_number: int = Field(..., description="Zodiac sign number 1 (Aries) to 12 (Pisces)")
    sign_degree: float = Field(..., description="Degree within sign (0 to 30)")
    formatted_sign_degree: str = Field(..., description="Formatted degree: e.g. 15°22'")
    house: Optional[int] = Field(None, description="Whole-sign house (1 to 12). None if birth time unknown.")
    nakshatra: NakshatraDetail
    is_retrograde: bool = Field(False, description="Whether the planet is retrograde")
    speed: float = Field(..., description="Daily speed in degrees")
    is_exalted: bool = Field(False, description="Whether the planet is in its exaltation sign")
    is_debilitated: bool = Field(False, description="Whether the planet is in its debilitation sign")


class DashaPeriod(BaseModel):
    """Vimshottari Dasha period."""
    mahadasha_lord: str = Field(..., description="Mahadasha lord")
    antardasha_lord: str = Field(..., description="Antardasha lord")
    pratyantardasha_lord: Optional[str] = Field(None, description="Pratyantardasha lord (sub-sub-period)")
    start_date: str = Field(..., description="Period start date in YYYY-MM-DD")
    end_date: str = Field(..., description="Period end date in YYYY-MM-DD")
    is_approximate: bool = Field(False, description="True if birth time was unknown and noon was assumed")


class AspectRelation(BaseModel):
    """Parashari aspect relation."""
    aspecting_planet: str
    from_sign: str
    from_house: Optional[int]
    aspect_type: str  # "7th", "4th", "8th", "5th", "9th", "3rd", "10th"
    target_sign: str
    target_house: Optional[int]
    target_planets: List[str] = Field(default_factory=list)


class ChartFact(BaseModel):
    """An individual atomic fact derived from the birth chart, with a stable ID."""
    id: str = Field(..., description="Stable deterministic ID, e.g. 'F01', 'F12'")
    category: str = Field(..., description="Fact category: 'lagna', 'planet', 'nakshatra', 'dasha', 'aspect'")
    subject: str = Field(..., description="Entity described: 'Lagna', 'Moon', 'Saturn', 'Current Dasha', etc.")
    text: str = Field(..., description="Human-readable fact description")
    is_time_dependent: bool = Field(False, description="True if this fact depends on precise birth time")
    is_available: bool = Field(True, description="False if unavailable due to missing birth time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured values for verification")


class ChartFacts(BaseModel):
    """Complete collection of computed facts from a birth chart."""
    birth_input: BirthInput
    calculated_at_utc: datetime
    ayanamsa_name: str = "Lahiri"
    ayanamsa_value: float
    time_known: bool
    lagna_sign: Optional[str] = None
    lagna_sign_number: Optional[int] = None
    lagna_degree: Optional[float] = None
    formatted_lagna_degree: Optional[str] = None
    planets: List[PlanetPosition]
    current_dasha: Optional[DashaPeriod] = None
    all_dashas: List[DashaPeriod] = Field(default_factory=list)
    antardashas: List[DashaPeriod] = Field(default_factory=list)
    aspects: List[AspectRelation] = Field(default_factory=list)
    facts: List[ChartFact] = Field(default_factory=list)

    def get_fact(self, fact_id: str) -> Optional[ChartFact]:
        for f in self.facts:
            if f.id == fact_id:
                return f
        return None

    def to_llm_context(self) -> str:
        """Render a clean, grounded text listing of all available facts for LLM consumption."""
        lines = [
            f"=== COMPUTED CHART FACTS (Lahiri Sidereal / Whole-Sign Houses) ===",
            f"Birth Date: {self.birth_input.birth_date}",
            f"Birth Time: {self.birth_input.birth_time if self.time_known else 'UNKNOWN (Time-dependent facts marked unavailable)'}",
            f"Birth Place: {self.birth_input.place_name or f'{self.birth_input.latitude}, {self.birth_input.longitude}'}",
            f"Ayanamsa: {self.ayanamsa_name} ({self.ayanamsa_value:.4f}°)",
            "",
            "FACTS LIST (Use ONLY these facts for your astrological reasoning; cite by ID):"
        ]
        for f in self.facts:
            status = "" if f.is_available else " [UNAVAILABLE - Birth time unknown]"
            lines.append(f"[{f.id}] ({f.category.upper()}) {f.text}{status}")
        return "\n".join(lines)
