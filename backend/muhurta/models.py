"""Pydantic schemas and enums for Melooha Auspicious Muhurta Engine."""

from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VedicActivityCategory(str, Enum):
    BUSINESS_FINANCE = "business_finance"
    PROPERTY_CONSTRUCTION = "property_construction"
    MARRIAGE_RELATIONSHIP = "marriage_relationship"
    EDUCATION_LEARNING = "education_learning"
    TRAVEL_JOURNEY = "travel_journey"
    HEALTH_MEDICAL = "health_medical"
    SPIRITUAL_RELIGIOUS = "spiritual_religious"
    JOB_CAREER = "job_career"


class ActivityOverride(str, Enum):
    # Business & Finance
    TECH_STARTUP_LAUNCH = "tech_startup_launch"
    OFFICE_SHOP_INAUGURATION = "office_shop_inauguration"
    CONTRACT_SIGNING = "contract_signing"
    INVESTING_TRADING = "investing_trading"
    LOAN_APPLICATION = "loan_application"

    # Property & Construction
    GRIHA_PRAVESH = "griha_pravesh"
    BHUMI_PUJAN = "bhumi_pujan"
    PROPERTY_PURCHASE = "property_purchase"
    PROPERTY_REGISTRATION = "property_registration"
    RENOVATION_START = "renovation_start"

    # Marriage & Sanskars
    VIVAH_MARRIAGE = "vivah_marriage"
    ENGAGEMENT_ROKA = "engagement_roka"
    NAMAKARANA = "namakarana"
    ANNAPRASHANA = "annaprashana"
    UPANAYANA = "upanayana"

    # Travel & Vehicles
    VEHICLE_PURCHASE = "vehicle_purchase"
    INTERNATIONAL_TRAVEL = "international_travel"
    DOMESTIC_JOURNEY = "domestic_journey"

    # Health & Career
    MEDICAL_SURGERY = "medical_surgery"
    JOB_JOINING = "job_joining"
    NEW_EDUCATION_COURSE = "new_education_course"
    EXAM_COMMENCEMENT = "exam_commencement"


class TimeOfDayPreference(str, Enum):
    ANY = "any"
    MORNING = "morning"       # Sunrise to 12:00
    AFTERNOON = "afternoon"   # 12:00 to 16:30
    EVENING = "evening"       # 16:30 to Sunset
    NIGHT = "night"           # Sunset to Sunrise (for specific ceremonies)
    ABHIJIT = "abhijit"       # Abhijit Muhurta (~midday solar noon)


class ParsedMuhurtaIntent(BaseModel):
    category: VedicActivityCategory
    override: Optional[ActivityOverride] = None
    target_start_date: str = Field(..., description="YYYY-MM-DD")
    target_end_date: str = Field(..., description="YYYY-MM-DD")
    time_preference: TimeOfDayPreference = TimeOfDayPreference.ANY
    target_location_name: str
    latitude: float
    longitude: float
    timezone_str: str = "Asia/Kolkata"
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    raw_query: str


class PanchangaDetails(BaseModel):
    tithi: str
    tithi_number: int
    paksha: str  # Shukla / Krishna
    nakshatra: str
    nakshatra_number: int
    nakshatra_temperament: str  # Dhruva, Chara, Kshipra, Mridu, Ugra, Tikshna, Mishra
    vara: str  # Day of week
    vara_lord: str
    yoga: str
    yoga_number: int
    is_inauspicious_yoga: bool
    karana: str
    is_vishti_bhadra: bool
    choghadiya: str
    choghadiya_is_favorable: bool
    is_rahu_kalam: bool = False
    is_yamaganda: bool = False
    is_abhijit: bool = False


class PersonalAlignment(BaseModel):
    tara_bala: str
    tara_bala_number: int  # 1 to 9
    tara_bala_is_favorable: bool
    chandra_bala: str
    chandra_house: int  # 1 to 12 relative to Janma Rashi
    chandra_bala_is_favorable: bool
    is_ashtama_chandra: bool  # 8th house transit (major flaw)
    score_contribution: str


class CalendarPayload(BaseModel):
    title: str
    description: str
    location: str
    start_time_iso: str
    end_time_iso: str
    google_calendar_url: str
    ics_data: str


class MuhurtaSlot(BaseModel):
    rank: int
    score: float
    start_time_local: str
    end_time_local: str
    panchanga: PanchangaDetails
    personal_alignment: PersonalAlignment
    explanation: str
    calendar_payload: CalendarPayload


class MuhurtaQueryRequest(BaseModel):
    user_id: Optional[str] = None
    profile_id: Optional[str] = None
    query: str = Field(..., min_length=3, description="Natural language query or event request")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone_str: Optional[str] = None
    category: Optional[VedicActivityCategory] = None
    override: Optional[ActivityOverride] = None


class MuhurtaResponse(BaseModel):
    muhurta_id: str
    user_id: str
    profile_name: str
    activity: Dict[str, Any]  # category, override, confidence
    location: Dict[str, Any]  # name, coordinates, timezone
    slots: List[MuhurtaSlot]
    advisory_note: str
    created_at: str
