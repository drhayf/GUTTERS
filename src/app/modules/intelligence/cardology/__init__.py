"""
GUTTERS Cardology Module (Magi OS)

The Deterministic Time-Mapping Engine based on the Order of the Magi system.
This module provides "The Script" - mathematically precise temporal cycles
derived from the 52-card calendar system.

Key Components:
- kernel.py: Pure stateless calculation engine (DO NOT MODIFY)
- module.py: GUTTERS BaseModule wrapper for integration
- schemas.py: Pydantic models for API responses

The kernel calculates:
- Birth Card from any date
- Planetary Ruling Card based on zodiac
- Karma Cards (First/Second)
- 52-Day Planetary Period timelines
- Relationship connection analysis
"""

from .module import CardologyModule, module
from .kernel import (
    # Core Types
    Card,
    Suit,
    Planet,
    ZodiacSign,
    PlanetaryPeriod,
    CardologyBlueprint,
    RelationshipConnection,
    # Core Functions
    generate_blueprint,
    calculate_birth_card,
    calculate_birth_card_from_date,
    get_current_period_info,
    generate_yearly_timeline,
    analyze_connections,
    # Spreads
    LIFE_SPREAD,
    NATURAL_SPREAD,
    # Constants
    JOKER,
    FIXED_CARDS,
)

__all__ = [
    # Module
    "CardologyModule",
    "module",
    # Types
    "Card",
    "Suit", 
    "Planet",
    "ZodiacSign",
    "PlanetaryPeriod",
    "CardologyBlueprint",
    "RelationshipConnection",
    # Functions
    "generate_blueprint",
    "calculate_birth_card",
    "calculate_birth_card_from_date",
    "get_current_period_info",
    "generate_yearly_timeline",
    "analyze_connections",
    # Data
    "LIFE_SPREAD",
    "NATURAL_SPREAD",
    "JOKER",
    "FIXED_CARDS",
]
