"""
Trait Categories and Frameworks

Defines the classification systems for traits:
- TraitCategory: What kind of trait (personality, behavior, preference, etc.)
- TraitFramework: Which wisdom framework it belongs to (Human Design, Jungian, etc.)

These enums provide standardized classification while remaining extensible.

@module TraitCategories
"""

from enum import Enum
from typing import List, Optional


class TraitCategory(str, Enum):
    """
    Categories of traits based on their nature.
    
    These categories help organize traits and determine how they're displayed,
    prioritized, and used in synthesis.
    """
    # Core Identity
    PERSONALITY = "personality"       # Fundamental character traits
    ARCHETYPE = "archetype"           # Archetypal patterns (Hero, Sage, etc.)
    
    # Cognitive & Psychological
    COGNITION = "cognition"           # How they think (Ni, Ne, Si, etc.)
    EMOTION = "emotion"               # Emotional patterns
    SHADOW = "shadow"                 # Shadow aspects (Jungian)
    
    # Behavioral
    BEHAVIOR = "behavior"             # Observable behaviors
    HABIT = "habit"                   # Recurring patterns
    TENDENCY = "tendency"             # Inclinations
    
    # Energetic
    ENERGY = "energy"                 # Energy patterns (HD type, etc.)
    RHYTHM = "rhythm"                 # Biological rhythms
    
    # Preferences
    PREFERENCE = "preference"         # User preferences
    STYLE = "style"                   # Decision style, communication style
    
    # Goals & Values
    GOAL = "goal"                     # What they want to achieve
    VALUE = "value"                   # Core values
    WOUND = "wound"                   # Core wounds
    GIFT = "gift"                     # Core gifts
    
    # Health & Body
    HEALTH = "health"                 # Health-related traits
    SOMATIC = "somatic"               # Body-based patterns
    
    # External
    DEMOGRAPHIC = "demographic"       # Age, location, etc.
    CONTEXT = "context"               # Contextual information
    
    # System
    CALCULATED = "calculated"         # Derived from birth data (HD chart)
    DETECTED = "detected"             # AI-detected patterns
    STATED = "stated"                 # User-stated information
    
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


class TraitFramework(str, Enum):
    """
    Wisdom frameworks that traits can be associated with.
    
    A trait can belong to multiple frameworks. For example,
    "introversion" is relevant to both Jungian and MBTI frameworks.
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


# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

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
