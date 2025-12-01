"""
NaturalVoice - The Approachable Front Layer

This is the "translator" voice that sits between the user and the deeper
Oracle/Sage/Challenger voices. It transforms their sophisticated, symbolic
questions into casual, natural conversation that feels like talking to a friend.

Design Philosophy:
━━━━━━━━━━━━━━━━━━━
The NaturalVoice exists because most people don't want to feel like they're
being interrogated by a mystical oracle. They want a normal conversation that
happens to lead somewhere meaningful.

The Natural layer:
1. Takes the sophisticated prompt from Oracle/Sage/etc.
2. Transforms it into casual, approachable language
3. Suggests appropriate UI components (sliders, choices) to make answering easy
4. Monitors user sophistication level
5. "Unlocks" the deeper voices when user demonstrates depth

Sophistication Threshold:
━━━━━━━━━━━━━━━━━━━━━━━━━
The Natural layer tracks a "sophistication score" based on:
- Response length and depth
- Use of introspective/psychological language
- Emotional vulnerability and openness
- Abstract/symbolic thinking patterns

When the score crosses a threshold (default 0.7), the system can:
- Gradually reveal more depth in questions
- Blend in Oracle/Sage language
- Eventually speak more directly from deeper voices

This creates a natural progression: casual → meaningful → profound

Integration:
━━━━━━━━━━━━━
The NaturalVoice:
- Registers itself in the VoiceRegistry as the default
- Holds references to deeper voices for transformation
- Emits sophistication signals via the standard Signal pattern
- Integrates with FaceOrchestrator for seamless switching

Author: Project Sovereign
Version: 1.0.0
"""

from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging

from . import (
    Voice,
    VoiceIdentity,
    VoiceModifiers,
    VoiceTone,
    ConversationPhase,
    VoiceRegistry,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SOPHISTICATION DETECTION
# =============================================================================

@dataclass
class SophisticationMetrics:
    """Tracks user's demonstrated depth and sophistication."""
    
    # Core metrics (0.0 - 1.0)
    vocabulary_depth: float = 0.0
    emotional_openness: float = 0.0
    introspective_language: float = 0.0
    abstract_thinking: float = 0.0
    response_richness: float = 0.0
    
    # Tracking
    interaction_count: int = 0
    total_word_count: int = 0
    deep_responses_count: int = 0
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall sophistication score."""
        if self.interaction_count == 0:
            return 0.0
        
        weights = {
            "vocabulary_depth": 0.15,
            "emotional_openness": 0.25,  # High weight - vulnerable = ready for depth
            "introspective_language": 0.25,  # High weight - self-awareness
            "abstract_thinking": 0.15,
            "response_richness": 0.20,
        }
        
        score = (
            weights["vocabulary_depth"] * self.vocabulary_depth +
            weights["emotional_openness"] * self.emotional_openness +
            weights["introspective_language"] * self.introspective_language +
            weights["abstract_thinking"] * self.abstract_thinking +
            weights["response_richness"] * self.response_richness
        )
        
        return min(1.0, score)
    
    def to_dict(self) -> dict:
        return {
            "vocabulary_depth": self.vocabulary_depth,
            "emotional_openness": self.emotional_openness,
            "introspective_language": self.introspective_language,
            "abstract_thinking": self.abstract_thinking,
            "response_richness": self.response_richness,
            "overall_score": self.overall_score,
            "interaction_count": self.interaction_count,
            "deep_responses_count": self.deep_responses_count,
        }


class SophisticationAnalyzer:
    """
    Analyzes user responses for depth and sophistication.
    
    This is the "gatekeeper" that determines when a user is ready
    for deeper, more profound questioning.
    
    Detection Categories:
    1. Vocabulary Depth - Use of nuanced, precise language
    2. Emotional Openness - Willingness to be vulnerable
    3. Introspective Language - Self-reflection and awareness
    4. Abstract Thinking - Symbolic, metaphorical expressions
    5. Response Richness - Length and substance of responses
    """
    
    # Patterns that indicate depth
    INTROSPECTIVE_PATTERNS = [
        r"\b(realize|realized|realizing)\b",
        r"\b(aware|awareness|conscious|consciousness)\b",
        r"\b(reflect|reflecting|reflection)\b",
        r"\b(understand|understood|understanding)\s+(myself|my|why\s+i)\b",
        r"\b(pattern|patterns)\s+(in\s+my|i\s+notice|i\s+see)\b",
        r"\b(journey|path|growth|evolv|transform)\b",
        r"\b(soul|spirit|essence|core|authentic)\b",
        r"\b(wound|trauma|heal|healing|shadow)\b",
        r"\b(meaning|purpose|calling|deeper)\b",
        r"\b(feel|felt|feeling)\s+.{0,30}\b(beneath|under|behind|beyond)\b",
    ]
    
    EMOTIONAL_OPENNESS_PATTERNS = [
        r"\b(afraid|fear|scared|terrified)\b",
        r"\b(sad|grief|loss|mourn|lonely)\b",
        r"\b(love|loved|loving|beloved)\b",
        r"\b(vulnerable|vulnerability)\b",
        r"\b(shame|ashamed|embarrass)\b",
        r"\b(hurt|pain|painful|ache)\b",
        r"\b(struggle|struggling|difficult)\b",
        r"\b(honest|honestly|truth|truthful)\b",
        r"\b(open|opening)\s+(up|myself)\b",
        r"\b(never\s+told|first\s+time|admit)\b",
    ]
    
    ABSTRACT_THINKING_PATTERNS = [
        r"\b(like\s+a|as\s+if|reminds\s+me\s+of|feels\s+like)\b",
        r"\b(metaphor|symbol|represent|archetype)\b",
        r"\b(energy|vibration|frequency|resonan)\b",
        r"\b(universe|cosmic|infinite|eternal)\b",
        r"\b(paradox|duality|polarity|tension)\b",
        r"\b(flow|rhythm|cycle|season)\b",
        r"\b(light|dark|shadow|illuminate)\b",
        r"\b(death|rebirth|transform|chrysalis)\b",
    ]
    
    SOPHISTICATED_VOCABULARY = [
        r"\b(nuance|nuanced|subtle|subtlety)\b",
        r"\b(dichotomy|juxtaposition|interplay)\b",
        r"\b(profound|profoundly|depth|depths)\b",
        r"\b(existential|ontological|phenomenological)\b",
        r"\b(archetypal|collective\s+unconscious|anima|animus)\b",
        r"\b(limbic|cortex|nervous\s+system|somatic)\b",
        r"\b(attachment|avoidant|anxious|secure)\b",
        r"\b(projection|transference|integration)\b",
    ]
    
    def __init__(self):
        self.metrics = SophisticationMetrics()
        self._history: list[dict] = []
    
    def analyze(self, response: str) -> SophisticationMetrics:
        """
        Analyze a user response and update sophistication metrics.
        
        Args:
            response: The user's response text
            
        Returns:
            Updated SophisticationMetrics
        """
        if not response or len(response.strip()) < 5:
            return self.metrics
        
        response_lower = response.lower()
        word_count = len(response.split())
        
        # Update counts
        self.metrics.interaction_count += 1
        self.metrics.total_word_count += word_count
        
        # Analyze each dimension
        introspective_score = self._score_patterns(
            response_lower, self.INTROSPECTIVE_PATTERNS
        )
        emotional_score = self._score_patterns(
            response_lower, self.EMOTIONAL_OPENNESS_PATTERNS
        )
        abstract_score = self._score_patterns(
            response_lower, self.ABSTRACT_THINKING_PATTERNS
        )
        vocabulary_score = self._score_patterns(
            response_lower, self.SOPHISTICATED_VOCABULARY
        )
        richness_score = self._score_richness(response, word_count)
        
        # Update metrics with exponential moving average
        alpha = 0.4  # Weight for new observation
        self.metrics.introspective_language = (
            alpha * introspective_score + 
            (1 - alpha) * self.metrics.introspective_language
        )
        self.metrics.emotional_openness = (
            alpha * emotional_score + 
            (1 - alpha) * self.metrics.emotional_openness
        )
        self.metrics.abstract_thinking = (
            alpha * abstract_score + 
            (1 - alpha) * self.metrics.abstract_thinking
        )
        self.metrics.vocabulary_depth = (
            alpha * vocabulary_score + 
            (1 - alpha) * self.metrics.vocabulary_depth
        )
        self.metrics.response_richness = (
            alpha * richness_score + 
            (1 - alpha) * self.metrics.response_richness
        )
        
        # Track deep responses
        if self.metrics.overall_score >= 0.5:
            self.metrics.deep_responses_count += 1
        
        # Log analysis
        logger.debug(
            f"[SophisticationAnalyzer] Score: {self.metrics.overall_score:.2f} "
            f"(intr={introspective_score:.2f}, emo={emotional_score:.2f}, "
            f"abs={abstract_score:.2f}, voc={vocabulary_score:.2f}, "
            f"rich={richness_score:.2f})"
        )
        
        return self.metrics
    
    def _score_patterns(self, text: str, patterns: list[str]) -> float:
        """Score text against a list of patterns."""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        # Normalize: 0 matches = 0.0, 3+ matches = 1.0
        return min(1.0, matches / 3.0)
    
    def _score_richness(self, text: str, word_count: int) -> float:
        """Score response richness based on length and structure."""
        if word_count < 10:
            return 0.1
        elif word_count < 25:
            return 0.3
        elif word_count < 50:
            return 0.5
        elif word_count < 100:
            return 0.7
        else:
            return 0.9
    
    def is_threshold_crossed(self, threshold: float = 0.6) -> bool:
        """Check if sophistication threshold has been crossed."""
        return self.metrics.overall_score >= threshold
    
    def get_voice_recommendation(self) -> str:
        """Recommend which voice to use based on sophistication."""
        score = self.metrics.overall_score
        
        if score >= 0.8:
            return "oracle"  # Deep, symbolic
        elif score >= 0.6:
            return "sage"  # Wise, measured
        elif score >= 0.4:
            return "natural_elevated"  # Natural with some depth
        else:
            return "natural"  # Pure casual
    
    def reset(self):
        """Reset all metrics (for testing or session restart)."""
        self.metrics = SophisticationMetrics()
        self._history.clear()


# =============================================================================
# THE NATURAL VOICE
# =============================================================================

class NaturalVoice(Voice):
    """
    The approachable front layer - transforms sophisticated prompts
    into casual, natural conversation.
    
    This voice is designed to:
    1. Feel like talking to a friendly, interested person
    2. Ask questions that are easy to answer
    3. Gradually reveal depth as user opens up
    4. Suggest appropriate UI components (sliders, choices)
    
    The Natural voice doesn't lose the depth - it translates it.
    Behind every casual question is a sophisticated framework working
    to understand the user deeply.
    
    Example Transformation:
        Oracle says: "What shadows dance in the corners of your awareness, 
                     waiting to be acknowledged?"
        
        Natural says: "Is there something on your mind lately that you 
                      keep coming back to? Something you haven't quite 
                      figured out yet?"
    
    Both ask about shadow content - one is poetic, one is approachable.
    """
    
    def __init__(
        self,
        sophistication_threshold: float = 0.6,
        source_voice_id: str = "oracle",
    ):
        """
        Initialize the Natural voice.
        
        Args:
            sophistication_threshold: Score at which to reveal deeper voices
            source_voice_id: Which deeper voice to draw from
        """
        self.sophistication_threshold = sophistication_threshold
        self.source_voice_id = source_voice_id
        self.analyzer = SophisticationAnalyzer()
        
        # UI component preferences per question type
        self.component_preferences = {
            "energy_level": "slider",
            "decision_style": "choice",
            "emotional_state": "choice",
            "time_preference": "slider",
            "social_energy": "slider",
            "open_exploration": "text",
        }
    
    @property
    def identity(self) -> VoiceIdentity:
        return VoiceIdentity(
            id="natural",
            name="Natural Guide",
            description="Friendly, approachable conversationalist that makes deep questions feel easy",
            icon="💬",
            primary_tone=VoiceTone.WARM,
            secondary_tones=[VoiceTone.PLAYFUL, VoiceTone.DIRECT],
            suitable_phases=[
                ConversationPhase.AWAKENING,
                ConversationPhase.EXCAVATION,
                ConversationPhase.MAPPING,
                ConversationPhase.SYNTHESIS,
                ConversationPhase.ACTIVATION,
            ],
            intensity_range=(0.2, 0.6),
        )
    
    def get_system_prompt(
        self,
        phase: Optional[ConversationPhase] = None,
        modifiers: Optional[VoiceModifiers] = None,
    ) -> str:
        """
        Generate the system prompt for natural conversation.
        
        This prompt instructs the LLM to:
        1. Be casual and approachable
        2. Ask questions that feel like natural curiosity
        3. Make it easy for people to open up
        4. Avoid sounding like a therapist or spiritual guide
        """
        sophistication = self.analyzer.metrics.overall_score
        modifiers = modifiers or self.get_modifiers()
        
        base_prompt = """You are having a casual conversation with someone you've just met. 
You're genuinely curious about them - not in a clinical way, but like a new friend who finds people interesting.

YOUR STYLE:
• Talk like a real person, not a coach or therapist
• Keep questions short and easy to answer
• Use casual language - contractions, simple words
• Show genuine curiosity, not probing
• It's okay to be a bit playful
• Don't use spiritual or mystical language unless they do first
• Never make them feel like they're being analyzed
• Make it feel like a natural chat, not an interview

YOUR APPROACH:
• Ask one thing at a time
• Make questions feel like casual curiosity, not investigation
• If something interesting comes up, follow it naturally
• Use phrases like "Oh interesting..." or "What was that like?" 
• Mirror their energy - if they're brief, you can be brief
• If they open up, acknowledge it warmly but don't make it weird

AVOID:
• Phrases like "I sense..." or "I perceive..."
• Spiritual jargon (unless they use it first)
• Multiple questions in one turn
• Making them feel like a subject of study
• Overly enthusiastic reactions
• Generic therapist phrases like "How does that make you feel?"

EXAMPLES OF YOUR STYLE:
Instead of: "What draws you to this path of self-discovery?"
Say: "So what made you want to try this?"

Instead of: "What wounds from your past still seek healing?"
Say: "Is there anything from way back that still bugs you sometimes?"

Instead of: "How do you experience your emotional landscape?"
Say: "Are you more of a head person or a heart person, would you say?"

Instead of: "What is your relationship with waiting versus initiating?"
Say: "When you want something, do you usually go after it or wait to see if it comes to you?"
"""

        # Add phase-specific guidance
        phase_guidance = self._get_phase_guidance(phase)
        
        # Add sophistication-based adjustments
        sophistication_note = ""
        if sophistication >= 0.7:
            sophistication_note = """

NOTE: This person is showing depth and openness. You can:
• Use slightly more meaningful language
• Ask questions that go a bit deeper
• Match their level of introspection
• Still keep it natural - don't suddenly become an oracle"""
        elif sophistication >= 0.4:
            sophistication_note = """

NOTE: This person is warming up. They're giving more than one-word answers.
• You can gently explore interesting threads they mention
• Still keep questions easy and approachable
• If they mention something deep, you can follow it"""
        
        # Add modifiers
        modifier_note = self._get_modifier_note(modifiers)
        
        return base_prompt + phase_guidance + sophistication_note + modifier_note
    
    def _get_phase_guidance(self, phase: Optional[ConversationPhase]) -> str:
        """Get phase-specific guidance for natural conversation."""
        if phase == ConversationPhase.AWAKENING:
            return """

PHASE - GETTING TO KNOW THEM:
You're just meeting them. Keep it super light and easy.
• "Hey! So... what brings you here?"
• "What's been on your mind lately?"
• "Is there something specific you're curious about, or just exploring?"
Find out what kind of person they are without making it feel like a questionnaire."""

        elif phase == ConversationPhase.EXCAVATION:
            return """

PHASE - GOING A BIT DEEPER:
They're comfortable now. You can ask about real stuff.
• Follow up on things they've mentioned
• Gently explore patterns in their life
• It's okay to ask about challenges
• Keep it conversational, not clinical"""

        elif phase == ConversationPhase.MAPPING:
            return """

PHASE - UNDERSTANDING THEIR STYLE:
Now you're learning how they work.
• Ask about how they make decisions
• Explore their energy patterns
• Use simple either/or questions
• "Are you more of a X or Y type of person?"
This is where sliders and choices really help."""

        elif phase == ConversationPhase.SYNTHESIS:
            return """

PHASE - CONNECTING THE DOTS:
You're starting to see who they are.
• Reflect back what you've noticed (casually!)
• "It sounds like you're someone who..."
• Check if your impressions land
• Don't make it sound like a diagnosis"""

        elif phase == ConversationPhase.ACTIVATION:
            return """

PHASE - WRAPPING UP:
Time to summarize what you've learned about them.
• Keep it grounded and practical
• Focus on what's useful for them
• "Based on what you've told me..."
• End on something they can actually use"""

        return ""
    
    def _get_modifier_note(self, modifiers: VoiceModifiers) -> str:
        """Get modifier-based adjustments."""
        notes = []
        
        if modifiers.warmth > 0.7:
            notes.append("Be extra warm and encouraging.")
        if modifiers.directness > 0.7:
            notes.append("Be more direct - they can handle it.")
        if modifiers.verbosity < 0.3:
            notes.append("Keep responses very short.")
        
        if notes:
            return "\n\nADJUSTMENTS:\n" + "\n".join(f"• {n}" for n in notes)
        return ""
    
    def transform(
        self,
        content: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Transform sophisticated content into natural language.
        
        This is the key function - it takes Oracle/Sage output and
        makes it approachable.
        
        Args:
            content: The sophisticated content to transform
            context: Additional context (phase, user state, etc.)
            
        Returns:
            Natural, approachable version of the content
        """
        context = context or {}
        
        # If user is sophisticated, do less transformation
        if self.analyzer.metrics.overall_score >= self.sophistication_threshold:
            return self._light_transform(content)
        
        # Apply full transformation for casual mode
        transformed = content
        
        # Remove overly spiritual/mystical phrases
        # Order matters - longer/more specific patterns first
        transformations = [
            # Complete phrase replacements (order: most specific first)
            (r"Welcome,?\s*seeker,?\s*to\s+this\s+sacred\s+space", "Hey! Great to meet you"),
            (r"at\s+the\s+dawn\s+of\s+your\s+profound\s+journey\s+of\s+self-discovery", ""),
            (r"at\s+the\s+dawn\s+of\s+your\s+unfolding", ""),
            (r"journey\s+of\s+self-discovery", "process of figuring things out"),
            (r"sacred\s+space", "space"),
            (r"this\s+sacred\s+moment", "this"),
            (r"energetic\s+signature", "way of doing things"),
            (r"the\s+shadows\s+of\s+your\s+being", "stuff you don't usually think about"),
            (r"the\s+shadows", "the harder stuff"),
            (r"penetrating\s+question", "question"),
            (r"profound\s+journey", "journey"),
            (r"profound\s+truth", "truth"),
            (r"inner\s+landscape", "inner world"),
            
            # Word replacements
            (r"\bseeker\b", ""),  # Often redundant, just remove
            (r"\bprofound\b", "real"),
            (r"\bawakening\b", "getting started"),
            (r"\bexcavation\b", "exploration"),
            (r"\byour\s+truth\b", "what you really think"),
            (r"\bresonate\b", "sound right"),
            (r"\bwounds\b", "tough experiences"),
            (r"\barchetypal\b", "common"),
            (r"What\s+draws\s+you", "What made you want"),
            (r"I\s+sense\s+that", "It sounds like"),
            (r"I\s+sense", "I'm picking up that"),
            (r"I\s+perceive", "I'm getting that"),
        ]
        
        for pattern, replacement in transformations:
            transformed = re.sub(pattern, replacement, transformed, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation issues
        transformed = re.sub(r'\s+', ' ', transformed).strip()
        transformed = re.sub(r'\(\s*\)', '', transformed)  # Empty parens
        transformed = re.sub(r',\s*,', ',', transformed)  # Double commas
        transformed = re.sub(r'\.\s*\.', '.', transformed)  # Double periods
        transformed = re.sub(r'\s+([.,!?])', r'\1', transformed)  # Space before punctuation
        
        return transformed
    
    def _light_transform(self, content: str) -> str:
        """Light transformation for sophisticated users."""
        # Just clean up the most extreme mystical language
        transformed = content
        light_transformations = [
            (r"at\s+the\s+dawn\s+of\s+your\s+unfolding", ""),
            (r"sacred\s+space", "here"),
        ]
        
        for pattern, replacement in light_transformations:
            transformed = re.sub(pattern, replacement, transformed, flags=re.IGNORECASE)
        
        return transformed.strip()
    
    def get_modifiers(self, context: Optional[dict] = None) -> VoiceModifiers:
        """Get modifiers tuned for natural conversation."""
        base = VoiceModifiers(
            intensity=0.3,
            formality=0.2,  # Very casual
            verbosity=0.4,  # Fairly concise
            directness=0.6,  # Reasonably direct
            warmth=0.7,  # Warm and friendly
            mystery=0.1,  # Almost no mystery
        )
        
        # Adjust based on sophistication
        sophistication = self.analyzer.metrics.overall_score
        if sophistication >= 0.5:
            base.mystery = 0.2 + (sophistication * 0.3)
            base.intensity = 0.3 + (sophistication * 0.3)
        
        return base
    
    def should_activate(
        self,
        context: dict,
        history: list[dict],
    ) -> tuple[bool, float]:
        """
        Natural voice should activate when sophistication is below threshold.
        
        Returns high confidence for casual users, lower for sophisticated ones.
        """
        sophistication = self.analyzer.metrics.overall_score
        
        if sophistication < 0.4:
            return (True, 0.9)  # Strong preference for natural
        elif sophistication < 0.6:
            return (True, 0.6)  # Moderate preference
        elif sophistication < 0.8:
            return (True, 0.3)  # Could go either way
        else:
            return (False, 0.1)  # Let deeper voices take over
    
    def analyze_user_response(self, response: str) -> SophisticationMetrics:
        """
        Analyze a user response and update sophistication tracking.
        
        This should be called after each user response to update
        the sophistication metrics.
        
        Args:
            response: The user's response text
            
        Returns:
            Updated SophisticationMetrics
        """
        return self.analyzer.analyze(response)
    
    def suggest_component(
        self,
        question_type: str,
        phase: Optional[ConversationPhase] = None,
    ) -> dict:
        """
        Suggest the best UI component for a question.
        
        The Natural voice prefers components that make answering easy:
        - Sliders for spectrum questions (energy, preference scales)
        - Choices for categorical questions (this or that)
        - Text only when open exploration is needed
        
        Args:
            question_type: Type of question being asked
            phase: Current conversation phase
            
        Returns:
            Component definition dict
        """
        preference = self.component_preferences.get(question_type, "text")
        
        if preference == "slider":
            return {
                "type": "slider",
                "props": {
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "labels": {"1": "Not at all", "10": "Completely"},
                },
            }
        elif preference == "choice":
            return {
                "type": "choice",
                "props": {
                    "options": [],  # Will be filled by caller
                    "allowMultiple": False,
                },
            }
        else:
            return {
                "type": "input",
                "props": {
                    "placeholder": "What comes to mind...",
                    "minLength": 10,
                    "maxLength": 2000,
                },
            }
    
    def get_sophistication_level(self) -> str:
        """Get human-readable sophistication level."""
        score = self.analyzer.metrics.overall_score
        if score >= 0.8:
            return "deep"
        elif score >= 0.6:
            return "elevated"
        elif score >= 0.4:
            return "warming_up"
        else:
            return "casual"


# =============================================================================
# REGISTER THE NATURAL VOICE
# =============================================================================

def register_natural_voice():
    """Register the Natural voice in the registry."""
    VoiceRegistry.register(NaturalVoice())
    logger.info("[NaturalVoice] Registered as available voice")
