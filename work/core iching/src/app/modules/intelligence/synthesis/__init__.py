"""
Harmonic Synthesis Module - The Council of Systems

Provides cross-system integration for multiple metaphysical frameworks.
"""

from .harmonic import (
    # Main Classes
    CouncilOfSystems,
    HarmonicSynthesis,
    SystemReading,
    
    # Adapters
    IChingAdapter,
    CardologyAdapter,
    
    # Resonance
    ResonanceType,
    ElementalResonance,
    get_elemental_resonance,
    
    # Elements
    Element,
    FrequencyBand,
    FrequencyState,
    
    # Core Functions
    cross_system_synthesis,
    
    # Constants
    CARDOLOGY_SUIT_ELEMENTS,
    HD_CENTER_ELEMENTS,
    TRIGRAM_ELEMENTS,
    ELEMENTAL_MATRIX,
)

__all__ = [
    "CouncilOfSystems",
    "HarmonicSynthesis",
    "SystemReading",
    "IChingAdapter",
    "CardologyAdapter",
    "ResonanceType",
    "ElementalResonance",
    "get_elemental_resonance",
    "Element",
    "FrequencyBand",
    "FrequencyState",
    "cross_system_synthesis",
    "CARDOLOGY_SUIT_ELEMENTS",
    "HD_CENTER_ELEMENTS",
    "TRIGRAM_ELEMENTS",
    "ELEMENTAL_MATRIX",
]
