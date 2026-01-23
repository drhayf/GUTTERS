"""
GUTTERS Synthesis Module

Cross-system profile synthesis using LLM.
"""
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
]
