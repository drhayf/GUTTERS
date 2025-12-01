"""
Trait Categories - Fractal Module

Each category is independently addressable and extensible.
Add new categories by creating a new folder with definition.py.

This module provides:
1. TraitCategory enum for backward compatibility
2. CategoryRegistry for dynamic discovery
3. Direct imports of each category value

@module TraitCategories
"""

from enum import Enum
from typing import List

from .registry import CategoryRegistry, CategoryInfo, get_category_registry

# Import all category values for backward compatibility
from .personality import PERSONALITY
from .archetype import ARCHETYPE
from .cognition import COGNITION
from .emotion import EMOTION
from .shadow import SHADOW
from .behavior import BEHAVIOR
from .habit import HABIT
from .tendency import TENDENCY
from .energy import ENERGY
from .rhythm import RHYTHM
from .preference import PREFERENCE
from .style import STYLE
from .goal import GOAL
from .value import VALUE
from .wound import WOUND
from .gift import GIFT
from .health import HEALTH
from .somatic import SOMATIC
from .demographic import DEMOGRAPHIC
from .context import CONTEXT
from .calculated import CALCULATED
from .detected import DETECTED
from .stated import STATED


class TraitCategory(str, Enum):
    """
    Trait categories - backward compatible enum.
    
    Each value corresponds to a fractal folder in categories/.
    New categories should be added as folders, and this enum
    will be auto-updated to include them.
    """
    # Core Identity
    PERSONALITY = PERSONALITY
    ARCHETYPE = ARCHETYPE
    
    # Cognitive & Psychological
    COGNITION = COGNITION
    EMOTION = EMOTION
    SHADOW = SHADOW
    
    # Behavioral
    BEHAVIOR = BEHAVIOR
    HABIT = HABIT
    TENDENCY = TENDENCY
    
    # Energetic
    ENERGY = ENERGY
    RHYTHM = RHYTHM
    
    # Preferences
    PREFERENCE = PREFERENCE
    STYLE = STYLE
    
    # Goals & Values
    GOAL = GOAL
    VALUE = VALUE
    WOUND = WOUND
    GIFT = GIFT
    
    # Health & Body
    HEALTH = HEALTH
    SOMATIC = SOMATIC
    
    # External
    DEMOGRAPHIC = DEMOGRAPHIC
    CONTEXT = CONTEXT
    
    # System
    CALCULATED = CALCULATED
    DETECTED = DETECTED
    STATED = STATED
    
    @classmethod
    def get_priority_order(cls) -> List["TraitCategory"]:
        """Get categories in priority order for display/synthesis."""
        # Use registry to get priority-sorted categories
        registry = get_category_registry()
        sorted_ids = registry.list_sorted_by_priority()
        return [cls(registry.get(id).value) for id in sorted_ids if registry.get(id)]


# =============================================================================
# BACKWARD COMPATIBILITY: Import TraitFramework and ConfidenceThreshold
# These will be migrated to their own fractal modules in Slice 1.2 and 1.3
# =============================================================================
from .._categories_legacy import TraitFramework, ConfidenceThreshold


__all__ = [
    # Enum and Registry
    "TraitCategory",
    "CategoryRegistry",
    "CategoryInfo",
    "get_category_registry",
    # Backward compatibility (will be migrated in later slices)
    "TraitFramework",
    "ConfidenceThreshold",
    # Individual category values
    "PERSONALITY", "ARCHETYPE", "COGNITION", "EMOTION", "SHADOW",
    "BEHAVIOR", "HABIT", "TENDENCY", "ENERGY", "RHYTHM",
    "PREFERENCE", "STYLE", "GOAL", "VALUE", "WOUND", "GIFT",
    "HEALTH", "SOMATIC", "DEMOGRAPHIC", "CONTEXT",
    "CALCULATED", "DETECTED", "STATED",
]
