"""
GUTTERS Numerology Schemas

Pydantic models for numerology chart data including core numbers,
master numbers, and karmic debt indicators.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class NumerologyChart(BaseModel):
    """Complete Pythagorean numerology chart data"""

    # Core numbers (1-9 or master 11, 22, 33)
    life_path: int = Field(..., ge=1, le=33, description="Core life purpose from birth date")
    expression: int = Field(..., ge=1, le=33, description="Natural talents from full name")
    soul_urge: int = Field(..., ge=1, le=33, description="Inner desires from name vowels")
    personality: int = Field(..., ge=1, le=33, description="Outer persona from name consonants")
    birthday: int = Field(..., ge=1, le=31, description="Natural gift from birth day")

    # Master number flags
    is_master_life_path: bool = False
    is_master_expression: bool = False
    is_master_soul_urge: bool = False

    # Special numbers
    karmic_debt_numbers: list[int] = Field(default_factory=list)
    master_numbers: list[int] = Field(default_factory=list)

    # Metadata - numerology is unaffected by birth time
    accuracy: Literal["full"] = "full"
    note: Optional[str] = None
