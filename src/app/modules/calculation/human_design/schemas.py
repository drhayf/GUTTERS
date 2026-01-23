"""
GUTTERS Human Design Schemas

Pydantic models for Human Design chart data including gates, channels,
centers, and full chart structures.

Updated to support full gate activations (color, tone, base) and
probabilistic calculations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, time


class ChartSubject(BaseModel):
    """Person's birth data for chart calculation."""
    name: str
    birth_date: date
    birth_time: Optional[time] = None
    latitude: float
    longitude: float
    timezone: str


class HDGate(BaseModel):
    """A single Human Design gate activation with full sub-line data."""
    planet: str
    gate: int = Field(..., ge=1, le=64)
    line: int = Field(..., ge=1, le=6)
    color: int = Field(default=1, ge=1, le=6, description="Color sub-line")
    tone: int = Field(default=1, ge=1, le=6, description="Tone sub-line")
    base: int = Field(default=1, ge=1, le=5, description="Base sub-line")
    sign: str = Field(default="", description="Zodiac sign (optional)")
    degree: float = Field(default=0.0, description="Ecliptic longitude")


class HDChannel(BaseModel):
    """A Human Design channel connecting two centers."""
    gates: tuple[int, int]
    name: str
    defined: bool = True
    theme: str = Field(default="", description="Channel theme/description (for backward compatibility)")


class HDCenter(BaseModel):
    """A Human Design energy center."""
    name: Literal["Head", "Ajna", "Throat", "G", "Sacral", "Solar Plexus", "Spleen", "Heart", "Root"]
    defined: bool
    gates: list[int] = Field(default_factory=list)


class TypeProbability(BaseModel):
    """Probability of a Human Design type based on sampling all hours."""
    value: str = Field(..., description="Type name")
    probability: float = Field(..., ge=0.0, le=1.0)
    sample_count: int = Field(..., description="Number of hours this type appears")
    confidence: Literal["certain", "high", "medium", "low"]


class PlanetStability(BaseModel):
    """Tracks if a planet's gate is stable across all sampled hours."""
    planet: str
    gate: int
    line: int
    stable: bool = Field(..., description="True if same across ALL samples")
    variation: Optional[str] = Field(None, description="Description if varies")


class HumanDesignChart(BaseModel):
    """Complete Human Design chart data."""
    # Required subject info
    subject: Optional[ChartSubject] = None
    
    # Core type info
    type: str
    strategy: str
    authority: str
    profile: str = Field(..., description="Profile in X/Y format")
    
    # Optional signature/not-self (from TYPE_DETAILS)
    signature: Optional[str] = None
    not_self: Optional[str] = None
    
    # Incarnation cross and definition
    incarnation_cross: Optional[str] = None
    definition: Optional[str] = None
    
    # Gates and channels
    personality_gates: list[HDGate] = Field(default_factory=list)
    design_gates: list[HDGate] = Field(default_factory=list)
    channels: list[HDChannel] = Field(default_factory=list)
    
    # Centers
    defined_centers: list[str] = Field(default_factory=list)
    undefined_centers: list[str] = Field(default_factory=list)
    
    # Accuracy and notes
    accuracy: Literal["full", "partial", "probabilistic"]
    note: Optional[str] = None
    
    # Probabilistic type data (when birth time unknown)
    type_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    type_probabilities: Optional[list[TypeProbability]] = None
    planet_stability: Optional[list[PlanetStability]] = None


# Backward compatibility aliases
ElementDistribution = BaseModel
ModalityDistribution = BaseModel
