"""
Trait Categories - Fractal Module

Each category is independently addressable and extensible.
Add new categories by creating a new folder with definition.py.

This module provides:
- TraitCategory enum for backward compatibility
- CategoryRegistry for dynamic discovery
- Individual category imports for direct access
- TraitFramework enum (temporarily from legacy, to be migrated in Slice 1.2)
- ConfidenceThreshold class (temporarily from legacy)
"""
from enum import Enum
from typing import List

from .registry import CategoryRegistry, get_category_registry

# Import from legacy file for backward compatibility
# ConfidenceThreshold will be migrated to its own fractal structure later
from ..categories_legacy import ConfidenceThreshold

# Import TraitFramework from the new fractal structure
from ..frameworks import TraitFramework

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
    
    Categories of traits based on their nature.
    These categories help organize traits and determine how they're displayed,
    prioritized, and used in synthesis.
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
        return [
            cls.PERSONALITY,
            cls.ARCHETYPE,
            cls.ENERGY,
            cls.COGNITION,
            cls.EMOTION,
            cls.BEHAVIOR,
            cls.GIFT,
            cls.WOUND,
            cls.VALUE,
            cls.GOAL,
            cls.STYLE,
            cls.PREFERENCE,
            cls.TENDENCY,
            cls.HABIT,
            cls.HEALTH,
            cls.SOMATIC,
            cls.RHYTHM,
            cls.SHADOW,
            cls.CALCULATED,
            cls.DETECTED,
            cls.STATED,
            cls.DEMOGRAPHIC,
            cls.CONTEXT,
        ]


__all__ = [
    # Main exports
    "TraitCategory",
    "CategoryRegistry",
    "get_category_registry",
    # From legacy (to be migrated)
    "TraitFramework",
    "ConfidenceThreshold",
    # Individual categories
    "PERSONALITY", "ARCHETYPE", "COGNITION", "EMOTION", "SHADOW",
    "BEHAVIOR", "HABIT", "TENDENCY", "ENERGY", "RHYTHM",
    "PREFERENCE", "STYLE", "GOAL", "VALUE", "WOUND", "GIFT",
    "HEALTH", "SOMATIC", "DEMOGRAPHIC", "CONTEXT",
    "CALCULATED", "DETECTED", "STATED",
]
