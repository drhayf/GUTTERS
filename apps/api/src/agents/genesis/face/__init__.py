"""
Genesis Face - The Expressive Interface Layer

The "Face" of Genesis is the user-facing interface - everything the user
perceives as the "personality" of the system. It is designed with
FRACTAL EXTENSIBILITY in mind.

Architecture Philosophy:
━━━━━━━━━━━━━━━━━━━━━━━━━
The Face is not a monolith. It is a collection of modular "features" that
can be added, removed, or swapped independently:

    Face/
    ├── voice/       # HOW it speaks (tone, personality, vocabulary)
    ├── eyes/        # HOW it perceives (future: emotion detection)
    ├── ears/        # HOW it listens (future: audio processing)
    ├── expression/  # HOW it emotes (future: visual expressions)
    └── memory/      # HOW it remembers context

Each "feature" follows the same pattern:
1. A base abstract class defining the interface
2. Multiple implementations that can be swapped
3. A registry for dynamic discovery
4. A selector for choosing the right one (manual, adaptive, or dynamic)

Voice Selection Modes:
━━━━━━━━━━━━━━━━━━━━━━━━
- MANUAL: User explicitly chooses their preferred voice
- ADAPTIVE: System learns user's preference over time
- DYNAMIC: Context-aware switching based on conversation state
- HYBRID: Combination of the above

This is the Fractal Pattern - infinitely extensible, cleanly separated.
"""

from typing import Optional, TYPE_CHECKING

# Voice system imports
from .voice import (
    # Core abstractions
    Voice,
    VoiceIdentity,
    VoiceModifiers,
    VoiceRegistry,
    VoiceSelector,
    VoiceSelectionMode,
    VoiceTone,
    ConversationPhase,
    BlendedVoice,
)

# Built-in voice implementations
from .voice.voices import (
    OracleVoice,
    SageVoice,
    CompanionVoice,
    ChallengerVoice,
    MirrorVoice,
)

# Natural voice layer (the approachable front)
from .voice.natural import NaturalVoice, SophisticationAnalyzer, SophisticationMetrics


# =============================================================================
# FACE ORCHESTRATOR
# =============================================================================

class FaceOrchestrator:
    """
    Central orchestrator for all Face components.
    
    Currently manages:
    - Voice selection and application
    - Sophistication tracking (Natural → Deeper voice progression)
    - UI component suggestions
    
    Future components:
    - Eyes (emotion detection from images)
    - Ears (audio processing, tone analysis)
    - Expression (visual feedback generation)
    - Memory (conversational context)
    
    The orchestrator coordinates these components to produce
    a coherent, personality-rich interaction.
    
    Natural Layer Integration:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━
    By default, the orchestrator uses the NaturalVoice which:
    1. Transforms sophisticated prompts into casual conversation
    2. Tracks user sophistication over time
    3. Gradually reveals deeper voices as user opens up
    4. Suggests appropriate UI components (sliders, choices)
    
    The sophistication threshold (default 0.6) determines when
    deeper voices like Oracle/Sage can take over.
    """
    
    def __init__(
        self,
        voice_mode: VoiceSelectionMode = VoiceSelectionMode.DYNAMIC,
        default_voice: str = "natural",  # Changed from "oracle" to "natural"
        sophistication_threshold: float = 0.6,
    ):
        self.voice_selector = VoiceSelector(
            mode=voice_mode,
            default_voice_id=default_voice,
        )
        self.sophistication_threshold = sophistication_threshold
        
        # Central sophistication analyzer shared across the session
        self._sophistication_analyzer = SophisticationAnalyzer()
        
        # Track which deeper voice to use when threshold crossed
        self._deeper_voice_preference = "oracle"
        
        # Placeholder for future components
        self._eyes = None  # Future: EmotionDetector
        self._ears = None  # Future: ToneAnalyzer
        self._expression = None  # Future: ExpressionGenerator
    
    @property
    def current_voice(self) -> Voice:
        """Get the currently active voice."""
        return self.voice_selector.select()
    
    @property
    def sophistication(self) -> SophisticationMetrics:
        """Get current sophistication metrics."""
        return self._sophistication_analyzer.metrics
    
    @property
    def sophistication_level(self) -> str:
        """Get human-readable sophistication level."""
        score = self._sophistication_analyzer.metrics.overall_score
        if score >= 0.8:
            return "deep"
        elif score >= 0.6:
            return "elevated"
        elif score >= 0.4:
            return "warming_up"
        else:
            return "casual"
    
    def analyze_user_response(self, response: str) -> SophisticationMetrics:
        """
        Analyze a user response for sophistication signals.
        
        This should be called after each user response. It updates
        the sophistication tracking and may trigger voice transitions.
        
        Args:
            response: The user's response text
            
        Returns:
            Updated SophisticationMetrics
        """
        metrics = self._sophistication_analyzer.analyze(response)
        
        # Also update Natural voice's analyzer if it's registered
        natural_voice = VoiceRegistry.get("natural")
        if natural_voice and isinstance(natural_voice, NaturalVoice):
            natural_voice.analyzer = self._sophistication_analyzer
        
        return metrics
    
    def is_threshold_crossed(self) -> bool:
        """Check if sophistication threshold has been crossed."""
        return self._sophistication_analyzer.metrics.overall_score >= self.sophistication_threshold
    
    def get_voice(
        self,
        context: Optional[dict] = None,
        history: Optional[list[dict]] = None,
    ) -> Voice:
        """
        Get the appropriate voice for the current context.
        
        With Natural layer integration:
        - Below threshold: Returns Natural voice
        - Above threshold: Returns deeper voice based on context
        - Context can override via 'force_voice' key
        
        Args:
            context: Current conversation context
            history: Recent conversation history
            
        Returns:
            Selected Voice instance
        """
        context = context or {}
        
        # Allow forced voice override
        if context.get("force_voice"):
            forced = VoiceRegistry.get(context["force_voice"])
            if forced:
                return forced
        
        # Check sophistication threshold
        if self.is_threshold_crossed():
            # User is sophisticated - use deeper voice
            context_with_sophistication = {
                **context,
                "sophistication": self._sophistication_analyzer.metrics.overall_score,
                "sophistication_level": self.sophistication_level,
            }
            return self.voice_selector.select(context_with_sophistication, history)
        else:
            # User is casual - use Natural voice
            return VoiceRegistry.get_or_default("natural")
    
    def get_system_prompt(
        self,
        context: Optional[dict] = None,
        history: Optional[list[dict]] = None,
        phase: Optional[ConversationPhase] = None,
    ) -> str:
        """
        Get the complete system prompt from the selected voice.
        
        Args:
            context: Current conversation context
            history: Recent conversation history
            phase: Current conversation phase
            
        Returns:
            The system prompt string
        """
        voice = self.get_voice(context, history)
        return voice.get_system_prompt(phase=phase)
    
    def transform_response(
        self,
        content: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Transform a response through the current voice.
        
        This applies the voice's transformation logic to make
        sophisticated content match the appropriate tone.
        
        Args:
            content: The raw content to transform
            context: Additional context
            
        Returns:
            Transformed content
        """
        voice = self.get_voice(context)
        return voice.transform(content, context)
    
    def suggest_component(
        self,
        question_type: str,
        phase: Optional[ConversationPhase] = None,
    ) -> dict:
        """
        Suggest an appropriate UI component for a question.
        
        The Natural layer prefers easy-to-answer components:
        - Sliders for spectrum questions
        - Choices for categorical questions
        - Text for open exploration
        
        Args:
            question_type: Type of question
            phase: Current conversation phase
            
        Returns:
            Component definition dict
        """
        natural_voice = VoiceRegistry.get("natural")
        if natural_voice and isinstance(natural_voice, NaturalVoice):
            return natural_voice.suggest_component(question_type, phase)
        
        # Fallback
        return {
            "type": "input",
            "props": {
                "placeholder": "Share your thoughts...",
                "minLength": 10,
            },
        }
    
    def set_manual_voice(self, voice_id: str) -> None:
        """Switch to manual mode with a specific voice."""
        self.voice_selector.mode = VoiceSelectionMode.MANUAL
        self.voice_selector.set_manual_voice(voice_id)
    
    def set_dynamic_mode(self) -> None:
        """Switch to dynamic voice selection."""
        self.voice_selector.mode = VoiceSelectionMode.DYNAMIC
    
    def set_adaptive_mode(self) -> None:
        """Switch to adaptive voice selection."""
        self.voice_selector.mode = VoiceSelectionMode.ADAPTIVE
    
    def set_natural_mode(self) -> None:
        """Force Natural voice as the front layer."""
        self.voice_selector.mode = VoiceSelectionMode.DYNAMIC
        self.voice_selector.default_voice_id = "natural"
    
    def record_feedback(self, positive: bool) -> None:
        """Record user feedback for the current voice."""
        voice = self.current_voice
        self.voice_selector.record_feedback(voice.identity.id, positive)
    
    def list_available_voices(self) -> list[dict]:
        """Get list of all available voices with their metadata."""
        return [v.identity.to_dict() for v in VoiceRegistry.list_all()]
    
    def get_sophistication_signal(self) -> dict:
        """
        Get a signal packet describing user's sophistication level.
        
        This can be sent to other agents (via SwarmBus) to inform
        them about the user's demonstrated depth.
        
        Returns:
            Signal dict compatible with SwarmBus
        """
        metrics = self._sophistication_analyzer.metrics
        return {
            "type": "sophistication_signal",
            "level": self.sophistication_level,
            "score": metrics.overall_score,
            "metrics": metrics.to_dict(),
            "threshold_crossed": self.is_threshold_crossed(),
            "recommended_voice": self._sophistication_analyzer.get_voice_recommendation(),
        }


# =============================================================================
# FACE FACTORY
# =============================================================================

class FaceFactory:
    """
    Factory for creating Face orchestrators with specific configurations.
    
    Provides preset configurations for common use cases:
    - natural: Natural voice as front layer (NEW DEFAULT)
    - default: Same as natural (for backward compatibility)
    - therapeutic: Emphasizes Companion and Mirror voices
    - coaching: Emphasizes Challenger and Sage voices
    - mystical: Emphasizes Oracle with high mystery (bypasses Natural)
    """
    
    @staticmethod
    def create_default() -> FaceOrchestrator:
        """
        Create Face with Natural voice as the approachable front layer.
        
        This is the NEW DEFAULT - uses casual, friendly conversation
        that progressively reveals depth as user opens up.
        """
        return FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",  # Changed from "oracle"
            sophistication_threshold=0.6,
        )
    
    @staticmethod
    def create_natural() -> FaceOrchestrator:
        """
        Create Face with Natural voice - casual, approachable conversation.
        
        The Natural layer:
        - Transforms sophisticated prompts into casual language
        - Tracks user sophistication over time
        - Gradually reveals deeper voices as user opens up
        - Suggests easy UI components (sliders, choices)
        """
        return FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",
            sophistication_threshold=0.6,
        )
    
    @staticmethod
    def create_natural_strict() -> FaceOrchestrator:
        """
        Create Face with Natural voice and HIGH threshold.
        
        Keeps conversation casual for longer - only reveals depth
        when user shows significant sophistication (0.8+).
        Good for users who prefer casual interaction.
        """
        return FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",
            sophistication_threshold=0.8,
        )
    
    @staticmethod
    def create_natural_permissive() -> FaceOrchestrator:
        """
        Create Face with Natural voice and LOW threshold.
        
        Quickly transitions to deeper voices when user shows
        any depth (0.4+). Good for users who want more meaning.
        """
        return FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",
            sophistication_threshold=0.4,
        )
    
    @staticmethod
    def create_therapeutic() -> FaceOrchestrator:
        """Create Face optimized for therapeutic interactions."""
        face = FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",  # Start natural
            sophistication_threshold=0.5,  # Lower threshold
        )
        # Boost preference for supportive voices when threshold crossed
        face.voice_selector._preference_scores["companion"] = 0.6
        face.voice_selector._preference_scores["mirror"] = 0.5
        return face
    
    @staticmethod
    def create_coaching() -> FaceOrchestrator:
        """Create Face optimized for coaching interactions."""
        face = FaceOrchestrator(
            voice_mode=VoiceSelectionMode.DYNAMIC,
            default_voice="natural",  # Start natural
            sophistication_threshold=0.5,
        )
        # Boost preference for growth-oriented voices when threshold crossed
        face.voice_selector._preference_scores["challenger"] = 0.6
        face.voice_selector._preference_scores["sage"] = 0.5
        return face
    
    @staticmethod
    def create_mystical() -> FaceOrchestrator:
        """
        Create Face that BYPASSES the Natural layer.
        
        Goes straight to Oracle voice - for users who explicitly
        want the deep, symbolic experience from the start.
        """
        face = FaceOrchestrator(
            voice_mode=VoiceSelectionMode.MANUAL,
            default_voice="oracle",
            sophistication_threshold=0.0,  # Always "sophisticated"
        )
        face.set_manual_voice("oracle")
        return face
    
    @staticmethod
    def create_with_voice(voice_id: str) -> FaceOrchestrator:
        """Create Face locked to a specific voice."""
        face = FaceOrchestrator(
            voice_mode=VoiceSelectionMode.MANUAL,
            default_voice=voice_id,
            sophistication_threshold=0.0,
        )
        face.set_manual_voice(voice_id)
        return face


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Face orchestration
    "FaceOrchestrator",
    "FaceFactory",
    
    # Sophistication tracking
    "SophisticationAnalyzer",
    "SophisticationMetrics",
    
    # Voice core abstractions
    "Voice",
    "VoiceIdentity",
    "VoiceModifiers",
    "VoiceRegistry",
    "VoiceSelector",
    "VoiceSelectionMode",
    "VoiceTone",
    "ConversationPhase",
    "BlendedVoice",
    
    # Built-in voice implementations
    "NaturalVoice",
    "OracleVoice",
    "SageVoice", 
    "CompanionVoice",
    "ChallengerVoice",
    "MirrorVoice",
]
