"""
Trait Frameworks - Fractal Module

Each framework is independently addressable and extensible.
Add new frameworks by creating a new folder with definition.py.

This module provides:
1. TraitFramework enum for backward compatibility
2. FrameworkRegistry for dynamic discovery
3. Direct imports of each framework value

@module TraitFrameworks
"""

from enum import Enum
from typing import Optional

from .registry import FrameworkRegistry, FrameworkInfo, get_framework_registry

# Import all framework values for backward compatibility
from .human_design import HUMAN_DESIGN
from .jungian import JUNGIAN
from .gene_keys import GENE_KEYS
from .mbti import MBTI
from .enneagram import ENNEAGRAM
from .astrology import ASTROLOGY
from .vedic import VEDIC
from .numerology import NUMEROLOGY
from .somatic import SOMATIC
from .somatic_awareness import SOMATIC_AWARENESS
from .ayurveda import AYURVEDA
from .big_five import BIG_FIVE
from .attachment import ATTACHMENT
from .health_metrics import HEALTH_METRICS
from .biometrics import BIOMETRICS
from .behavioral_patterns import BEHAVIORAL_PATTERNS
from .core_patterns import CORE_PATTERNS
from .sovereign import SOVEREIGN
from .general import GENERAL


class TraitFramework(str, Enum):
    """
    Trait frameworks - backward compatible enum.
    
    Each value corresponds to a fractal folder in frameworks/.
    New frameworks should be added as folders, and this enum
    will be auto-updated to include them.
    """
    # Primary Frameworks
    HUMAN_DESIGN = HUMAN_DESIGN
    JUNGIAN = JUNGIAN
    GENE_KEYS = GENE_KEYS
    MBTI = MBTI
    ENNEAGRAM = ENNEAGRAM
    
    # Astrological
    ASTROLOGY = ASTROLOGY
    VEDIC = VEDIC
    
    # Numerological
    NUMEROLOGY = NUMEROLOGY
    
    # Somatic/Body
    SOMATIC = SOMATIC
    SOMATIC_AWARENESS = SOMATIC_AWARENESS
    AYURVEDA = AYURVEDA
    
    # Modern Psychology
    BIG_FIVE = BIG_FIVE
    ATTACHMENT = ATTACHMENT
    
    # Health
    HEALTH_METRICS = HEALTH_METRICS
    BIOMETRICS = BIOMETRICS
    
    # Behavioral & Patterns
    BEHAVIORAL_PATTERNS = BEHAVIORAL_PATTERNS
    CORE_PATTERNS = CORE_PATTERNS
    
    # Custom/General
    SOVEREIGN = SOVEREIGN
    GENERAL = GENERAL
    
    @property
    def display_name(self) -> str:
        """Get human-readable name from registry."""
        registry = get_framework_registry()
        # Convert enum value to registry key
        for key, info in registry.get_all_info().items():
            if info.value == self.value:
                return info.display_name
        return self.value.replace("_", " ").title()
    
    @property
    def icon(self) -> str:
        """Get emoji icon from registry."""
        registry = get_framework_registry()
        for key, info in registry.get_all_info().items():
            if info.value == self.value:
                return info.icon
        return "📝"


__all__ = [
    # Enum and Registry
    "TraitFramework",
    "FrameworkRegistry",
    "FrameworkInfo",
    "get_framework_registry",
    # Individual framework values
    "HUMAN_DESIGN", "JUNGIAN", "GENE_KEYS", "MBTI", "ENNEAGRAM",
    "ASTROLOGY", "VEDIC", "NUMEROLOGY",
    "SOMATIC", "SOMATIC_AWARENESS", "AYURVEDA",
    "BIG_FIVE", "ATTACHMENT",
    "HEALTH_METRICS", "BIOMETRICS",
    "BEHAVIORAL_PATTERNS", "CORE_PATTERNS",
    "SOVEREIGN", "GENERAL",
]
