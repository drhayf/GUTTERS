"""
GUTTERS Synthesis Module

Cross-system profile synthesis using LLM and Harmonic Council of Systems.
"""
from .harmonic import (
    CardologyAdapter,
    CouncilOfSystems,
    Element,
    ElementalResonance,
    HarmonicSynthesis,
    IChingAdapter,
    ResonanceType,
    SystemReading,
    cross_system_synthesis,
)
from .module import SynthesisModule, module
from .schemas import ModuleInsights, SynthesisPattern, SynthesisRequest, SynthesisResponse, UnifiedProfile
from .synthesizer import (
    ALLOWED_MODELS,
    DEFAULT_MODEL,
    ProfileSynthesizer,
    get_user_preferred_model,
    update_user_preference,
)

__all__ = [
    # Module
    "SynthesisModule",
    "module",
    # Schemas
    "UnifiedProfile",
    "SynthesisPattern",
    "ModuleInsights",
    "SynthesisRequest",
    "SynthesisResponse",
    # Synthesizer
    "ProfileSynthesizer",
    "get_user_preferred_model",
    "update_user_preference",
    # Constants
    "ALLOWED_MODELS",
    "DEFAULT_MODEL",
    # Council of Systems / Harmonic Synthesis
    "CouncilOfSystems",
    "HarmonicSynthesis",
    "SystemReading",
    "ElementalResonance",
    "ResonanceType",
    "Element",
    "IChingAdapter",
    "CardologyAdapter",
    "cross_system_synthesis",
]
