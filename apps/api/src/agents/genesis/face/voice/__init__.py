"""
Voice System - The Vocal Character of the Face

The Voice defines HOW the system speaks - its tone, personality, vocabulary,
and conversational style. This is separate from WHAT it says (content logic).

Design Principles:
━━━━━━━━━━━━━━━━━━━
1. SEPARATION: Voice (how) vs Content (what) are decoupled
2. COMPOSABILITY: Voices can be mixed or layered
3. EXTENSIBILITY: New voices can be added without touching existing code
4. ADAPTABILITY: Voice selection can be manual, adaptive, or dynamic

Voice Anatomy:
━━━━━━━━━━━━━━
Each Voice has:
- identity: Name and description
- tone: Emotional quality (warm, intense, neutral, etc.)
- vocabulary: Word choices and speech patterns
- prompts: The system prompts that embody this voice
- modifiers: Adjustments based on context (phase, user state, etc.)

Built-in Voices:
━━━━━━━━━━━━━━━━
1. ORACLE    - Ancient wisdom, symbolic, penetrating questions
2. SAGE      - Calm, measured, practical wisdom
3. COMPANION - Warm, supportive, encouraging
4. CHALLENGER - Direct, provocative, pushes boundaries
5. MIRROR    - Reflective, echoes back, minimal interpretation

Usage:
    voice = VoiceRegistry.get("oracle")
    response = voice.transform(content, context)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class VoiceSelectionMode(str, Enum):
    """How the system selects which voice to use."""
    MANUAL = "manual"        # User explicitly chooses
    ADAPTIVE = "adaptive"    # System learns preference over time
    DYNAMIC = "dynamic"      # Context-aware switching
    HYBRID = "hybrid"        # Combination approach


class VoiceTone(str, Enum):
    """The emotional quality of a voice."""
    WARM = "warm"
    NEUTRAL = "neutral"
    INTENSE = "intense"
    PLAYFUL = "playful"
    SOLEMN = "solemn"
    MYSTERIOUS = "mysterious"
    DIRECT = "direct"
    REFLECTIVE = "reflective"


class ConversationPhase(str, Enum):
    """Maps to Genesis phases for voice modulation."""
    AWAKENING = "awakening"
    EXCAVATION = "excavation"
    MAPPING = "mapping"
    SYNTHESIS = "synthesis"
    ACTIVATION = "activation"


# =============================================================================
# VOICE CONFIGURATION
# =============================================================================

@dataclass
class VoiceIdentity:
    """The identity and metadata of a voice."""
    id: str
    name: str
    description: str
    icon: str = "🗣️"
    primary_tone: VoiceTone = VoiceTone.NEUTRAL
    secondary_tones: list[VoiceTone] = field(default_factory=list)
    suitable_phases: list[ConversationPhase] = field(default_factory=list)
    intensity_range: tuple[float, float] = (0.3, 0.8)  # Min/max intensity
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "primary_tone": self.primary_tone.value,
            "secondary_tones": [t.value for t in self.secondary_tones],
            "suitable_phases": [p.value for p in self.suitable_phases],
        }


@dataclass
class VoiceModifiers:
    """
    Contextual modifiers that adjust voice behavior.
    
    These are applied dynamically based on conversation state.
    """
    intensity: float = 0.5          # 0.0 (gentle) to 1.0 (intense)
    formality: float = 0.5          # 0.0 (casual) to 1.0 (formal)
    verbosity: float = 0.5          # 0.0 (terse) to 1.0 (elaborate)
    directness: float = 0.5         # 0.0 (indirect) to 1.0 (direct)
    warmth: float = 0.5             # 0.0 (cool) to 1.0 (warm)
    mystery: float = 0.3            # 0.0 (plain) to 1.0 (cryptic)
    
    def apply_phase_adjustment(self, phase: ConversationPhase) -> "VoiceModifiers":
        """Return modified copy based on conversation phase."""
        adjustments = {
            ConversationPhase.AWAKENING: {
                "warmth": min(1.0, self.warmth + 0.2),
                "mystery": min(1.0, self.mystery + 0.1),
                "intensity": max(0.0, self.intensity - 0.1),
            },
            ConversationPhase.EXCAVATION: {
                "intensity": min(1.0, self.intensity + 0.2),
                "directness": min(1.0, self.directness + 0.1),
                "warmth": max(0.0, self.warmth - 0.1),
            },
            ConversationPhase.MAPPING: {
                "formality": min(1.0, self.formality + 0.1),
                "verbosity": max(0.0, self.verbosity - 0.1),
                "directness": min(1.0, self.directness + 0.2),
            },
            ConversationPhase.SYNTHESIS: {
                "verbosity": min(1.0, self.verbosity + 0.2),
                "warmth": min(1.0, self.warmth + 0.1),
                "mystery": max(0.0, self.mystery - 0.2),
            },
            ConversationPhase.ACTIVATION: {
                "intensity": min(1.0, self.intensity + 0.3),
                "directness": min(1.0, self.directness + 0.2),
                "warmth": min(1.0, self.warmth + 0.2),
            },
        }
        
        adj = adjustments.get(phase, {})
        return VoiceModifiers(
            intensity=adj.get("intensity", self.intensity),
            formality=adj.get("formality", self.formality),
            verbosity=adj.get("verbosity", self.verbosity),
            directness=adj.get("directness", self.directness),
            warmth=adj.get("warmth", self.warmth),
            mystery=adj.get("mystery", self.mystery),
        )


# =============================================================================
# ABSTRACT VOICE BASE CLASS
# =============================================================================

class Voice(ABC):
    """
    Abstract base class for all Voice implementations.
    
    A Voice is responsible for:
    1. Defining its identity and characteristics
    2. Providing system prompts that embody its personality
    3. Transforming raw content into voiced output
    4. Adapting to context through modifiers
    
    Subclasses MUST implement:
    - identity property
    - get_system_prompt()
    - transform()
    
    Subclasses MAY override:
    - get_modifiers()
    - should_activate()
    - blend_with()
    """
    
    @property
    @abstractmethod
    def identity(self) -> VoiceIdentity:
        """Return the voice's identity configuration."""
        pass
    
    @abstractmethod
    def get_system_prompt(
        self, 
        phase: Optional[ConversationPhase] = None,
        modifiers: Optional[VoiceModifiers] = None,
    ) -> str:
        """
        Generate the system prompt for this voice.
        
        Args:
            phase: Current conversation phase for contextualization
            modifiers: Dynamic modifiers to adjust tone
            
        Returns:
            The complete system prompt string
        """
        pass
    
    @abstractmethod
    def transform(
        self,
        content: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Transform content into this voice's style.
        
        This is used for post-processing LLM output to ensure
        consistency with the voice's personality.
        
        Args:
            content: The raw content to transform
            context: Additional context for transformation
            
        Returns:
            The transformed content
        """
        pass
    
    def get_modifiers(self, context: Optional[dict] = None) -> VoiceModifiers:
        """
        Get the default modifiers for this voice, potentially
        adjusted based on context.
        
        Override this to provide voice-specific modifier defaults.
        """
        return VoiceModifiers()
    
    def should_activate(
        self,
        context: dict,
        history: list[dict],
    ) -> tuple[bool, float]:
        """
        Determine if this voice should activate in the given context.
        
        Used by the DYNAMIC voice selection mode.
        
        Args:
            context: Current conversation context
            history: Recent conversation history
            
        Returns:
            Tuple of (should_activate, confidence_score)
        """
        # Default: always available with neutral confidence
        return (True, 0.5)
    
    def blend_with(
        self,
        other: "Voice",
        ratio: float = 0.5,
    ) -> "BlendedVoice":
        """
        Create a blended voice combining this voice with another.
        
        Args:
            other: The voice to blend with
            ratio: Blend ratio (0.0 = all this, 1.0 = all other)
            
        Returns:
            A new BlendedVoice instance
        """
        return BlendedVoice(self, other, ratio)
    
    def __repr__(self) -> str:
        return f"<Voice: {self.identity.name}>"


# =============================================================================
# BLENDED VOICE (Composite Pattern)
# =============================================================================

class BlendedVoice(Voice):
    """
    A composite voice that blends two voices together.
    
    This enables gradual transitions between voices and
    creating unique hybrid personalities.
    """
    
    def __init__(
        self,
        primary: Voice,
        secondary: Voice,
        ratio: float = 0.5,
    ):
        self.primary = primary
        self.secondary = secondary
        self.ratio = max(0.0, min(1.0, ratio))
    
    @property
    def identity(self) -> VoiceIdentity:
        return VoiceIdentity(
            id=f"{self.primary.identity.id}_{self.secondary.identity.id}",
            name=f"{self.primary.identity.name} + {self.secondary.identity.name}",
            description=f"Blend of {self.primary.identity.name} and {self.secondary.identity.name}",
            icon="🎭",
            primary_tone=self.primary.identity.primary_tone,
            secondary_tones=[self.secondary.identity.primary_tone],
        )
    
    def get_system_prompt(
        self,
        phase: Optional[ConversationPhase] = None,
        modifiers: Optional[VoiceModifiers] = None,
    ) -> str:
        primary_prompt = self.primary.get_system_prompt(phase, modifiers)
        secondary_prompt = self.secondary.get_system_prompt(phase, modifiers)
        
        # For blended voices, we instruct the LLM to combine styles
        return f"""You are speaking with a blended voice that combines two personalities:

PRIMARY VOICE ({100 - int(self.ratio * 100)}%):
{primary_prompt}

SECONDARY VOICE ({int(self.ratio * 100)}%):
{secondary_prompt}

Blend these voices naturally, leaning {'more toward the secondary' if self.ratio > 0.5 else 'more toward the primary'} style.
The blend should feel organic, not jarring or inconsistent."""
    
    def transform(
        self,
        content: str,
        context: Optional[dict] = None,
    ) -> str:
        # Apply both transforms with weighted influence
        # In practice, this would use more sophisticated blending
        if self.ratio < 0.3:
            return self.primary.transform(content, context)
        elif self.ratio > 0.7:
            return self.secondary.transform(content, context)
        else:
            # For middle ratios, we rely on the blended prompt
            return content


# =============================================================================
# VOICE REGISTRY
# =============================================================================

class VoiceRegistry:
    """
    Central registry for all available voices.
    
    Voices register themselves here and can be discovered dynamically.
    This enables plugin-style extensibility.
    
    Usage:
        # Register a voice
        VoiceRegistry.register(MyCustomVoice())
        
        # Get a voice
        voice = VoiceRegistry.get("oracle")
        
        # List all voices
        voices = VoiceRegistry.list_all()
    """
    
    _voices: dict[str, Voice] = {}
    _initialized: bool = False
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazy initialization of built-in voices."""
        if not cls._initialized:
            # Register built-in voices
            from .voices import (
                OracleVoice,
                SageVoice,
                CompanionVoice,
                ChallengerVoice,
                MirrorVoice,
            )
            from .natural import NaturalVoice
            
            # Register Natural voice FIRST as it's the default front layer
            cls.register(NaturalVoice())
            
            # Register deeper voices (used by Natural layer or when threshold crossed)
            cls.register(OracleVoice())
            cls.register(SageVoice())
            cls.register(CompanionVoice())
            cls.register(ChallengerVoice())
            cls.register(MirrorVoice())
            cls._initialized = True
    
    @classmethod
    def register(cls, voice: Voice) -> None:
        """Register a voice in the registry."""
        cls._voices[voice.identity.id] = voice
        logger.info(f"[VoiceRegistry] Registered voice: {voice.identity.name}")
    
    @classmethod
    def unregister(cls, voice_id: str) -> Optional[Voice]:
        """Remove a voice from the registry."""
        return cls._voices.pop(voice_id, None)
    
    @classmethod
    def get(cls, voice_id: str) -> Optional[Voice]:
        """Get a voice by ID."""
        cls._ensure_initialized()
        return cls._voices.get(voice_id)
    
    @classmethod
    def get_or_default(cls, voice_id: str, default_id: str = "oracle") -> Voice:
        """Get a voice by ID, falling back to default if not found."""
        cls._ensure_initialized()
        voice = cls._voices.get(voice_id)
        if voice is None:
            voice = cls._voices.get(default_id)
        if voice is None:
            raise ValueError(f"Neither '{voice_id}' nor default '{default_id}' found in registry")
        return voice
    
    @classmethod
    def list_all(cls) -> list[Voice]:
        """List all registered voices."""
        cls._ensure_initialized()
        return list(cls._voices.values())
    
    @classmethod
    def list_ids(cls) -> list[str]:
        """List all registered voice IDs."""
        cls._ensure_initialized()
        return list(cls._voices.keys())
    
    @classmethod
    def get_for_phase(cls, phase: ConversationPhase) -> list[Voice]:
        """Get voices suitable for a specific phase."""
        cls._ensure_initialized()
        return [
            v for v in cls._voices.values()
            if not v.identity.suitable_phases or phase in v.identity.suitable_phases
        ]
    
    @classmethod
    def clear(cls) -> None:
        """Clear all voices (mainly for testing)."""
        cls._voices.clear()
        cls._initialized = False


# =============================================================================
# VOICE SELECTOR
# =============================================================================

class VoiceSelector:
    """
    Intelligent voice selection based on configured mode.
    
    Modes:
    - MANUAL: Uses the explicitly set voice
    - ADAPTIVE: Learns from user feedback over time
    - DYNAMIC: Selects based on context signals
    - HYBRID: Combines adaptive preferences with dynamic context
    
    Usage:
        selector = VoiceSelector(mode=VoiceSelectionMode.DYNAMIC)
        voice = selector.select(context, history)
    """
    
    def __init__(
        self,
        mode: VoiceSelectionMode = VoiceSelectionMode.DYNAMIC,
        default_voice_id: str = "oracle",
        manual_voice_id: Optional[str] = None,
    ):
        self.mode = mode
        self.default_voice_id = default_voice_id
        self.manual_voice_id = manual_voice_id
        
        # Adaptive learning state
        self._preference_scores: dict[str, float] = {}
        self._interaction_count: int = 0
        
        # Dynamic selection weights
        self._context_weights: dict[str, float] = {
            "phase": 0.3,
            "user_state": 0.3,
            "history_pattern": 0.2,
            "explicit_request": 0.2,
        }
    
    def select(
        self,
        context: Optional[dict] = None,
        history: Optional[list[dict]] = None,
    ) -> Voice:
        """
        Select the appropriate voice based on mode and context.
        
        Args:
            context: Current conversation context
            history: Recent conversation history
            
        Returns:
            The selected Voice instance
        """
        context = context or {}
        history = history or []
        
        if self.mode == VoiceSelectionMode.MANUAL:
            return self._select_manual()
        elif self.mode == VoiceSelectionMode.ADAPTIVE:
            return self._select_adaptive(context, history)
        elif self.mode == VoiceSelectionMode.DYNAMIC:
            return self._select_dynamic(context, history)
        elif self.mode == VoiceSelectionMode.HYBRID:
            return self._select_hybrid(context, history)
        else:
            return VoiceRegistry.get_or_default(self.default_voice_id)
    
    def _select_manual(self) -> Voice:
        """Manual selection - use explicitly set voice."""
        voice_id = self.manual_voice_id or self.default_voice_id
        return VoiceRegistry.get_or_default(voice_id)
    
    def _select_adaptive(
        self,
        context: dict,
        history: list[dict],
    ) -> Voice:
        """Adaptive selection - based on learned preferences."""
        if not self._preference_scores:
            return VoiceRegistry.get_or_default(self.default_voice_id)
        
        # Select voice with highest preference score
        best_voice_id = max(self._preference_scores, key=self._preference_scores.get)
        return VoiceRegistry.get_or_default(best_voice_id)
    
    def _select_dynamic(
        self,
        context: dict,
        history: list[dict],
    ) -> Voice:
        """Dynamic selection - based on context signals."""
        candidates: list[tuple[Voice, float]] = []
        
        for voice in VoiceRegistry.list_all():
            should_activate, confidence = voice.should_activate(context, history)
            if should_activate:
                # Apply context-based scoring
                score = self._score_voice_for_context(voice, context, confidence)
                candidates.append((voice, score))
        
        if not candidates:
            return VoiceRegistry.get_or_default(self.default_voice_id)
        
        # Select highest scoring voice
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def _select_hybrid(
        self,
        context: dict,
        history: list[dict],
    ) -> Voice:
        """Hybrid selection - combines adaptive and dynamic."""
        # Get dynamic candidate
        dynamic_voice = self._select_dynamic(context, history)
        
        # If we have strong adaptive preference, weight toward that
        if self._preference_scores:
            adaptive_voice_id = max(self._preference_scores, key=self._preference_scores.get)
            adaptive_score = self._preference_scores[adaptive_voice_id]
            
            # If adaptive preference is strong enough, use it
            if adaptive_score > 0.7:
                return VoiceRegistry.get_or_default(adaptive_voice_id)
            
            # Otherwise, consider blending
            if adaptive_score > 0.4 and adaptive_voice_id != dynamic_voice.identity.id:
                adaptive_voice = VoiceRegistry.get(adaptive_voice_id)
                if adaptive_voice:
                    # Blend based on preference strength
                    return dynamic_voice.blend_with(adaptive_voice, adaptive_score)
        
        return dynamic_voice
    
    def _score_voice_for_context(
        self,
        voice: Voice,
        context: dict,
        base_confidence: float,
    ) -> float:
        """Calculate a context-aware score for a voice."""
        score = base_confidence
        
        # Phase matching
        phase = context.get("phase")
        if phase and isinstance(phase, str):
            try:
                phase_enum = ConversationPhase(phase)
                if phase_enum in voice.identity.suitable_phases:
                    score += self._context_weights["phase"]
            except ValueError:
                pass
        
        # User state matching (future: user prefers warm voices when stressed)
        user_state = context.get("user_state", {})
        if user_state.get("needs_support") and voice.identity.primary_tone == VoiceTone.WARM:
            score += self._context_weights["user_state"]
        if user_state.get("needs_challenge") and voice.identity.primary_tone == VoiceTone.DIRECT:
            score += self._context_weights["user_state"]
        
        return min(1.0, score)
    
    def record_feedback(self, voice_id: str, positive: bool) -> None:
        """
        Record user feedback for adaptive learning.
        
        Args:
            voice_id: The voice that was used
            positive: Whether the user gave positive feedback
        """
        current = self._preference_scores.get(voice_id, 0.5)
        
        # Exponential moving average update
        alpha = 0.1  # Learning rate
        delta = 0.1 if positive else -0.1
        new_score = current + alpha * delta
        
        self._preference_scores[voice_id] = max(0.0, min(1.0, new_score))
        self._interaction_count += 1
    
    def set_manual_voice(self, voice_id: str) -> None:
        """Set the voice for manual mode."""
        self.manual_voice_id = voice_id
    
    def get_preferences(self) -> dict[str, float]:
        """Get current preference scores."""
        return self._preference_scores.copy()
    
    def reset_preferences(self) -> None:
        """Reset learned preferences."""
        self._preference_scores.clear()
        self._interaction_count = 0


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "VoiceSelectionMode",
    "VoiceTone",
    "ConversationPhase",
    
    # Data classes
    "VoiceIdentity",
    "VoiceModifiers",
    
    # Core abstractions
    "Voice",
    "BlendedVoice",
    "VoiceRegistry",
    "VoiceSelector",
]