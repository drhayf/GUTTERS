"""
Trait Categories and Frameworks

This module now re-exports from the fractal categories/ folder.
The original implementation has been preserved in _categories_legacy.py.

For TraitCategory: imports from categories/
For TraitFramework: imports from _categories_legacy.py (to be migrated in Slice 1.2)
For ConfidenceThreshold: imports from _categories_legacy.py (to be migrated in Slice 1.3)

@module TraitCategories
"""

# Re-export TraitCategory from the new fractal module
from .categories import (
    TraitCategory,
    CategoryRegistry,
    CategoryInfo,
    get_category_registry,
    # Individual category values
    PERSONALITY, ARCHETYPE, COGNITION, EMOTION, SHADOW,
    BEHAVIOR, HABIT, TENDENCY, ENERGY, RHYTHM,
    PREFERENCE, STYLE, GOAL, VALUE, WOUND, GIFT,
    HEALTH, SOMATIC, DEMOGRAPHIC, CONTEXT,
    CALCULATED, DETECTED, STATED,
)

# Re-export TraitFramework and ConfidenceThreshold from legacy (to be migrated)
from ._categories_legacy import TraitFramework, ConfidenceThreshold

__all__ = [
    # Categories (new fractal module)
    "TraitCategory",
    "CategoryRegistry",
    "CategoryInfo",
    "get_category_registry",
    # Frameworks and thresholds (legacy, to be migrated)
    "TraitFramework",
    "ConfidenceThreshold",
    # Individual category values
    "PERSONALITY", "ARCHETYPE", "COGNITION", "EMOTION", "SHADOW",
    "BEHAVIOR", "HABIT", "TENDENCY", "ENERGY", "RHYTHM",
    "PREFERENCE", "STYLE", "GOAL", "VALUE", "WOUND", "GIFT",
    "HEALTH", "SOMATIC", "DEMOGRAPHIC", "CONTEXT",
    "CALCULATED", "DETECTED", "STATED",
]
