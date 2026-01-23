"""
GUTTERS Astrology Schemas

Pydantic models for astrology data structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class PlanetPosition(BaseModel):
    """Position of a planet in the natal chart."""
    name: str = Field(description="Planet name (Sun, Moon, Mercury, etc.)")
    sign: str = Field(description="Zodiac sign (Aries, Taurus, etc.)")
    degree: float = Field(ge=0, lt=360, description="Degree within the sign (0-29.99)")
    house: int = Field(ge=1, le=12, description="House placement (1-12)")
    retrograde: bool = Field(default=False, description="Whether planet is retrograde")


class HouseCusp(BaseModel):
    """House cusp in the natal chart."""
    number: int = Field(ge=1, le=12, description="House number (1-12)")
    sign: str = Field(description="Zodiac sign on the cusp")
    degree: float = Field(ge=0, lt=360, description="Degree of the cusp")


class Aspect(BaseModel):
    """Aspect between two planets."""
    planet1: str = Field(description="First planet in aspect")
    planet2: str = Field(description="Second planet in aspect")
    type: str = Field(description="Aspect type (conjunction, opposition, trine, etc.)")
    orb: float = Field(ge=0, description="Orb in degrees (how exact the aspect is)")


class ElementDistribution(BaseModel):
    """Distribution of planets across elements."""
    fire: int = Field(ge=0, description="Planets in fire signs (Aries, Leo, Sagittarius)")
    earth: int = Field(ge=0, description="Planets in earth signs (Taurus, Virgo, Capricorn)")
    air: int = Field(ge=0, description="Planets in air signs (Gemini, Libra, Aquarius)")
    water: int = Field(ge=0, description="Planets in water signs (Cancer, Scorpio, Pisces)")


class ModalityDistribution(BaseModel):
    """Distribution of planets across modalities."""
    cardinal: int = Field(ge=0, description="Planets in cardinal signs")
    fixed: int = Field(ge=0, description="Planets in fixed signs")
    mutable: int = Field(ge=0, description="Planets in mutable signs")


class RisingSignProbability(BaseModel):
    """Probability of a rising sign based on birth date analysis."""
    sign: str = Field(description="Zodiac sign")
    probability: float = Field(ge=0.0, le=1.0, description="Probability (0-1)")
    hours_count: int = Field(description="Number of hours this sign appears as rising")
    confidence: Literal["certain", "high", "medium", "low"] = Field(description="Confidence level")


class PlanetStability(BaseModel):
    """Tracks whether a planet's sign/house is stable across all hours of the day."""
    planet: str = Field(description="Planet name")
    sign: str = Field(description="Zodiac sign (stable if same all day)")
    sign_stable: bool = Field(description="True if sign is same for all 24 hours")
    house_range: tuple[int, int] = Field(description="Range of possible houses (min, max)")
    house_stable: bool = Field(description="True if house is same for all 24 hours")
    note: Optional[str] = Field(None, description="Description of variability")


class AspectStability(BaseModel):
    """Tracks whether an aspect is stable (present) across all hours of the day."""
    planet1: str = Field(description="First planet")
    planet2: str = Field(description="Second planet")
    aspect_type: str = Field(description="Aspect type (conjunction, trine, etc.)")
    stable: bool = Field(description="True if aspect is present all 24 hours")
    hours_present: int = Field(description="Number of hours aspect is present")
    confidence: Literal["certain", "high", "medium", "low"] = Field(description="Confidence level")


class AnglePosition(BaseModel):
    """Position of a chart angle (Ascendant, Midheaven, etc.)."""
    sign: str = Field(description="Zodiac sign")
    degree: float = Field(ge=0, lt=360, description="Degree position")


class BirthData(BaseModel):
    """Birth data used for chart calculation."""
    date: str = Field(description="Birth date (YYYY-MM-DD)")
    time: str = Field(description="Birth time (HH:MM)")
    latitude: float = Field(ge=-90, le=90, description="Birth latitude")
    longitude: float = Field(ge=-180, le=180, description="Birth longitude")
    timezone: str = Field(description="IANA timezone")


class ChartSubject(BaseModel):
    """Subject of the natal chart."""
    name: str = Field(description="Subject's name")
    birth_data: BirthData = Field(description="Birth data used for calculation")


class NatalChartResult(BaseModel):
    """Complete natal chart calculation result."""
    subject: ChartSubject = Field(description="Chart subject and birth data")
    planets: list[PlanetPosition] = Field(description="Planetary positions")
    houses: list[HouseCusp] = Field(description="House cusps")
    aspects: list[Aspect] = Field(description="Planetary aspects")
    elements: ElementDistribution = Field(description="Element distribution")
    modalities: ModalityDistribution = Field(description="Modality distribution")
    ascendant: Optional[AnglePosition] = Field(None, description="Ascendant (Rising sign) - None if birth time unknown")
    midheaven: Optional[AnglePosition] = Field(None, description="Midheaven (MC) - None if birth time unknown")
    
    # Probabilistic data (when birth time unknown)
    accuracy: Literal["full", "solar", "probabilistic"] = Field("full", description="Chart accuracy level")
    rising_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in rising sign (0-1)")
    rising_probabilities: Optional[list[RisingSignProbability]] = Field(None, description="All possible rising signs with probabilities")
    planet_stability: Optional[list[PlanetStability]] = Field(None, description="Sign/house stability for each planet")
    aspect_stability: Optional[list[AspectStability]] = Field(None, description="Stability of major aspects")
    note: Optional[str] = Field(None, description="Additional notes about accuracy")
    available_data: list[str] = Field(default_factory=list, description="List of available data types")


class NatalChartWithInterpretation(NatalChartResult):
    """Natal chart with AI-generated interpretation."""
    interpretation: str | None = Field(
        default=None,
        description="Natural language interpretation of the chart"
    )
    summary: str | None = Field(
        default=None,
        description="Brief summary (Sun in X, Moon in Y, Z Rising)"
    )
