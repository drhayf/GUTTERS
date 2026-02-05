"""
I-Ching Logic Kernel Module

Provides the complete I-Ching / Human Design / Gene Keys calculation engine.
"""

from .kernel import (
    # Core Kernel
    IChingKernel,
    
    # Data Classes
    Activation,
    DailyCode,
    GateData,
    LineArchetype,
    ChannelData,
    ProfileData,
    
    # Enums
    Trigram,
    Center,
    
    # Constants
    GATE_DATABASE,
    GATE_CIRCLE,
    CHANNELS,
    PROFILES,
    INCARNATION_CROSSES,
    LINE_ARCHETYPES,
    ICHING_OFFSET,
    
    # Ephemeris
    SwissEphemerisService,
)

__all__ = [
    "IChingKernel",
    "Activation",
    "DailyCode",
    "GateData",
    "LineArchetype",
    "ChannelData",
    "ProfileData",
    "Trigram",
    "Center",
    "GATE_DATABASE",
    "GATE_CIRCLE",
    "CHANNELS",
    "PROFILES",
    "INCARNATION_CROSSES",
    "LINE_ARCHETYPES",
    "ICHING_OFFSET",
    "SwissEphemerisService",
]
