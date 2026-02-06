"""
GUTTERS Protocol Package

Event constants and packet schema for GUTTERS event-driven communication.

This package defines:
- Event type constants (no magic strings in code)
- Packet dataclass for event messages
"""
from .events import (
    COSMIC_FULL_MOON,
    # Cosmic events
    COSMIC_STORM_DETECTED,
    COSMIC_TRANSIT_EXACT,
    MODULE_ERROR,
    # Module events
    MODULE_INITIALIZED,
    MODULE_PROFILE_CALCULATED,
    SYNTHESIS_COMPLETED,
    # Synthesis events
    SYNTHESIS_TRIGGERED,
    SYNTHESIS_UPDATED,
    USER_BIRTH_DATA_UPDATED,
    # User events
    USER_CREATED,
    USER_PREFERENCES_CHANGED,
)
from .packet import Packet

__all__ = [
    # Event constants
    "USER_CREATED",
    "USER_BIRTH_DATA_UPDATED",
    "USER_PREFERENCES_CHANGED",
    "MODULE_INITIALIZED",
    "MODULE_PROFILE_CALCULATED",
    "MODULE_ERROR",
    "COSMIC_STORM_DETECTED",
    "COSMIC_FULL_MOON",
    "COSMIC_TRANSIT_EXACT",
    "SYNTHESIS_TRIGGERED",
    "SYNTHESIS_COMPLETED",
    "SYNTHESIS_UPDATED",
    # Packet class
    "Packet",
]
