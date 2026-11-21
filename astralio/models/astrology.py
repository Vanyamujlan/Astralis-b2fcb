"""Astrology domain models: natal chart, synastry compatibility, and transit forecasts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    """Resolved geographic location for astronomical calculations."""

    name: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    timezone: str
    source: str = "gazetteer"


class PlanetPosition(BaseModel):
    """Calculated ecliptic position of a celestial body."""

    key: str
    name_ru: str
    symbol: str
    longitude: float = Field(ge=0.0, lt=360.0)
    sign_key: str
    sign_ru: str
    sign_symbol: str
    degree_in_sign: float = Field(ge=0.0, lt=30.0)
    speed: float = 0.0
    is_retrograde: bool = False
    house: int | None = Field(default=None, ge=1, le=12)


class HouseCusp(BaseModel):
    """Calculated astrological house cusp."""

    number: int = Field(ge=1, le=12)
    longitude: float = Field(ge=0.0, lt=360.0)
    sign_key: str
    sign_ru: str
    sign_symbol: str
    degree_in_sign: float = Field(ge=0.0, lt=30.0)


class Aspect(BaseModel):
    """Major astrological aspect between two celestial bodies."""

    body_a: str
    body_b: str
    aspect_key: str
    aspect_ru: str
    angle: float
    orb: float
    is_harmonious: bool


class NatalChart(BaseModel):
    """Calculated natal chart produced by Swiss Ephemeris."""

    subject_name: str
    birth_date: date
    birth_time_str: str | None = None
    birth_place: str | None = None
    calculated_utc: datetime
    julian_day: float
    has_exact_time: bool
    has_coordinates: bool
    planets: list[PlanetPosition]
    ascendant: PlanetPosition | None = None
    midheaven: PlanetPosition | None = None
    houses: list[HouseCusp] = Field(default_factory=list)
    aspects: list[Aspect] = Field(default_factory=list)
    dominant_element: str
    limitations: list[str] = Field(default_factory=list)


class SynastryAspect(BaseModel):
    """Cross-chart aspect between Person 1 and Person 2."""

    person_a_body: str
    person_b_body: str
    aspect_key: str
    aspect_ru: str
    orb: float
    is_harmonious: bool
    summary: str


class CompatibilityReport(BaseModel):
    """Calculated synastry compatibility report between two people."""

    person_a_name: str
    person_b_name: str
    chart_a: NatalChart
    chart_b: NatalChart
    overall_score: int = Field(ge=0, le=100)
    emotional_score: int = Field(ge=0, le=100)
    romance_score: int = Field(ge=0, le=100)
    communication_score: int = Field(ge=0, le=100)
    long_term_score: int = Field(ge=0, le=100)
    synastry_aspects: list[SynastryAspect]
    strengths: list[str]
    challenges: list[str]
    advice: str
    limitations: list[str] = Field(default_factory=list)


class ForecastPeriod(StrEnum):
    """Supported forecast horizons."""

    DAILY = "daily"
    WEEKLY = "weekly"


class TransitEvent(BaseModel):
    """A real calculated transit aspect to a user's natal planet."""

    transit_date: date
    transit_planet: str
    natal_planet: str
    aspect_key: str
    aspect_ru: str
    orb: float
    is_harmonious: bool
    theme: str
    guidance: str


class ForecastReport(BaseModel):
    """Personalized transit-based forecast report."""

    period: ForecastPeriod
    start_date: date
    end_date: date
    sun_sign_ru: str
    moon_sign_ru: str
    active_transits: list[TransitEvent]
    key_themes: list[str]
    practical_advice: list[str]
    limitations: list[str] = Field(default_factory=list)
    interpretation_source: str = "local"
