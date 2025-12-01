"""
Trait System - The Atomic Units of Identity

This module defines the fundamental building blocks of the Digital Twin:
- Trait: A single characteristic with value, confidence, and provenance
- TraitCategory: Classification of traits
- TraitSource: Where a trait value came from
- TraitChange: History of changes to a trait

Each Trait represents a single piece of understanding about the user,
with full provenance tracking (who detected it, when, with what evidence).

@module Traits
"""

from .base import (
    Trait,
    TraitValue,
    TraitConfidence,
    TraitSource,
    TraitChange,
)
from .categories import (
    TraitCategory,
    TraitFramework,
    ConfidenceThreshold,
)
from .validation import (
    TraitValidator,
    ValidationResult,
    ValidationError,
)

__all__ = [
    "Trait",
    "TraitValue",
    "TraitConfidence",
    "TraitSource",
    "TraitChange",
    "TraitCategory",
    "TraitFramework",
    "ConfidenceThreshold",
    "TraitValidator",
    "ValidationResult",
    "ValidationError",
]
