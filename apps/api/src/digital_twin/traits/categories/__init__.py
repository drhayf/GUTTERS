"""
Trait Categories - Fractal Module

Each category is independently addressable and extensible.
Add new categories by creating a new folder with definition.py.

This module provides:
1. Auto-discovery via CategoryRegistry
2. Backward-compatible TraitCategory enum
3. Direct imports of individual category constants
4. TraitFramework re-export (until Slice 1.2 migration)

Part of the True Fractal Pattern architecture.

@module TraitCategories
"""
from enum import Enum
from typing import List

# Registry for dynamic discovery
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

# Re-export TraitFramework from compat file (until Slice 1.2 migration)
from ..categories_compat import TraitFramework


class TraitCategory(str, Enum):
    """
    Trait categories - backward compatible enum.
    
    This enum is maintained for backward compatibility.
    New code should prefer using the CategoryRegistry for dynamic access.
    
    Each enum value matches the string constant in the category's definition.py.
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
        """
        Get categories in priority order for display/synthesis.
        
        Priority is based on the PRIORITY constant in each category's definition.
        Lower priority number = higher importance.
        """
        registry = get_category_registry()
        priority_order = registry.list_by_priority()
        
        # Map registry results back to enum members
        result = []
        for info in priority_order:
            try:
                result.append(cls(info.value))
            except ValueError:
                pass  # Skip any categories not in the enum
        return result


# Confidence thresholds (kept here for backward compatibility)
class ConfidenceThreshold:
    """
    Standard confidence thresholds for trait handling.
    
    These determine how traits are treated based on confidence level.
    """
    CERTAIN = 0.95       # Store as verified fact
    HIGH = 0.80          # Store, no more probing needed
    MODERATE = 0.60      # Store, may probe for confirmation
    LOW = 0.40           # Hypothesis, needs probing
    SPECULATION = 0.20   # Weak signal, track but don't store
    
    @classmethod
    def get_level_name(cls, confidence: float) -> str:
        """Get human-readable confidence level name."""
        if confidence >= cls.CERTAIN:
            return "certain"
        elif confidence >= cls.HIGH:
            return "high"
        elif confidence >= cls.MODERATE:
            return "moderate"
        elif confidence >= cls.LOW:
            return "low"
        else:
            return "speculation"
    
    @classmethod
    def needs_probing(cls, confidence: float) -> bool:
        """Check if a confidence level requires more probing."""
        return confidence < cls.HIGH
    
    @classmethod
    def can_store(cls, confidence: float) -> bool:
        """Check if a confidence level is high enough to store."""
        return confidence >= cls.LOW


__all__ = [
    # Registry
    "TraitCategory",
    "CategoryRegistry",
    "CategoryInfo",
    "get_category_registry",
    "ConfidenceThreshold",
    # TraitFramework (re-exported, will be migrated in Slice 1.2)
    "TraitFramework",
    # Individual categories (for direct import)
    "PERSONALITY", "ARCHETYPE", "COGNITION", "EMOTION", "SHADOW",
    "BEHAVIOR", "HABIT", "TENDENCY", "ENERGY", "RHYTHM",
    "PREFERENCE", "STYLE", "GOAL", "VALUE", "WOUND", "GIFT",
    "HEALTH", "SOMATIC", "DEMOGRAPHIC", "CONTEXT",
    "CALCULATED", "DETECTED", "STATED",
]
