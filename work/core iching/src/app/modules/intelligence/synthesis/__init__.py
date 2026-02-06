"""
Harmonic Synthesis Module - The Council of Systems

Provides cross-system integration for multiple metaphysical frameworks.
"""

from .harmonic import (
    # Constants
    CARDOLOGY_SUIT_ELEMENTS,
    ELEMENTAL_MATRIX,
    HD_CENTER_ELEMENTS,
    TRIGRAM_ELEMENTS,
    CardologyAdapter,
    # Main Classes
    CouncilOfSystems,
    # Elements
    Element,
    ElementalResonance,
    FrequencyBand,
    FrequencyState,
    HarmonicSynthesis,
    # Adapters
    IChingAdapter,
    # Resonance
    ResonanceType,
    SystemReading,
    # Core Functions
    cross_system_synthesis,
    get_elemental_resonance,
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
