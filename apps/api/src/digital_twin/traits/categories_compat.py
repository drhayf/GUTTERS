"""
Trait Frameworks - Compatibility Module

This file contains TraitFramework which will be migrated to its own fractal
structure in Slice 1.2. Until then, it lives here to avoid circular imports.

For TraitCategory:
- Primary source: src.digital_twin.traits.categories/ (fractal folder structure)

For TraitFramework:
- Currently defined here (will be migrated in Slice 1.2)
- Future source: src.digital_twin.traits.frameworks/

@module TraitFrameworks (Compat)
"""

from enum import Enum
from typing import List, Optional


class TraitFramework(str, Enum):
    """
    Wisdom frameworks that traits can be associated with.
    
    A trait can belong to multiple frameworks. For example,
    "introversion" is relevant to both Jungian and MBTI frameworks.
    
    NOTE: This will be migrated to src.digital_twin.traits.frameworks/
    in Slice 1.2 of the True Fractal Migration.
    """
    # Primary Frameworks
    HUMAN_DESIGN = "human_design"
    JUNGIAN = "jungian"
    GENE_KEYS = "gene_keys"
    MBTI = "mbti"
    ENNEAGRAM = "enneagram"
    
    # Astrological
    ASTROLOGY = "astrology"
    VEDIC = "vedic_astrology"
    
    # Numerological
    NUMEROLOGY = "numerology"
    
    # Somatic/Body
    SOMATIC = "somatic"
    SOMATIC_AWARENESS = "somatic_awareness"  # Body awareness patterns
    AYURVEDA = "ayurveda"
    
    # Modern Psychology
    BIG_FIVE = "big_five"
    ATTACHMENT = "attachment_theory"
    
    # Health
    HEALTH_METRICS = "health_metrics"
    BIOMETRICS = "biometrics"
    
    # Behavioral & Patterns
    BEHAVIORAL_PATTERNS = "behavioral_patterns"  # Observed behavioral patterns
    CORE_PATTERNS = "core_patterns"              # Deep core patterns
    
    # Custom/General
    SOVEREIGN = "sovereign"           # Sovereign-specific insights
    GENERAL = "general"               # No specific framework
    
    @property
    def display_name(self) -> str:
        """Get human-readable name."""
        names = {
            self.HUMAN_DESIGN: "Human Design",
            self.JUNGIAN: "Jungian Psychology",
            self.GENE_KEYS: "Gene Keys",
            self.MBTI: "MBTI",
            self.ENNEAGRAM: "Enneagram",
            self.ASTROLOGY: "Western Astrology",
            self.VEDIC: "Vedic Astrology",
            self.NUMEROLOGY: "Numerology",
            self.SOMATIC: "Somatic Intelligence",
            self.AYURVEDA: "Ayurveda",
            self.BIG_FIVE: "Big Five Personality",
            self.ATTACHMENT: "Attachment Theory",
            self.HEALTH_METRICS: "Health Metrics",
            self.BIOMETRICS: "Biometrics",
            self.SOVEREIGN: "Sovereign Insights",
            self.GENERAL: "General",
        }
        return names.get(self, self.value.replace("_", " ").title())
    
    @property
    def icon(self) -> str:
        """Get emoji icon for the framework."""
        icons = {
            self.HUMAN_DESIGN: "🔮",
            self.JUNGIAN: "🧠",
            self.GENE_KEYS: "🧬",
            self.MBTI: "📊",
            self.ENNEAGRAM: "⭐",
            self.ASTROLOGY: "♈",
            self.VEDIC: "🕉️",
            self.NUMEROLOGY: "🔢",
            self.SOMATIC: "🫀",
            self.AYURVEDA: "🌿",
            self.BIG_FIVE: "📈",
            self.ATTACHMENT: "💕",
            self.HEALTH_METRICS: "❤️",
            self.BIOMETRICS: "📱",
            self.SOVEREIGN: "👑",
            self.GENERAL: "📝",
        }
        return icons.get(self, "📝")
