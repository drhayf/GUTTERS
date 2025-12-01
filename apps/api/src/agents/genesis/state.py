"""
Genesis State - The Rubric and Session Memory

This module defines the shared state for the Genesis subsystem:
- The ProfileRubric: A structured container for all detected traits
- The GenesisState: Session-specific state including phase, responses, hypotheses
- Confidence tracking for each trait category

The Rubric is organized by framework:
- Human Design: Type, Strategy, Authority, Profile, Centers, Gates, Channels
- Jungian: Cognitive Functions, Shadow, Persona
- Somatic: Energy patterns, Nervous system state
- Gene Keys: Shadow/Gift/Siddhi patterns

Each trait has:
- value: The detected value
- confidence: 0.0-1.0 certainty
- evidence: List of indicators that led to this detection
- probed: Whether we've directly asked about this
"""

from typing import Optional, Literal, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# =============================================================================
# PHASE DEFINITIONS
# =============================================================================

class GenesisPhase(str, Enum):
    """The 5 phases of the Genesis profiling journey."""
    AWAKENING = "awakening"
    EXCAVATION = "excavation"
    MAPPING = "mapping"
    SYNTHESIS = "synthesis"
    ACTIVATION = "activation"
    
    def next_phase(self) -> Optional["GenesisPhase"]:
        """Get the next phase in the sequence."""
        phases = list(GenesisPhase)
        try:
            idx = phases.index(self)
            if idx < len(phases) - 1:
                return phases[idx + 1]
        except ValueError:
            pass
        return None
    
    def prev_phase(self) -> Optional["GenesisPhase"]:
        """Get the previous phase in the sequence."""
        phases = list(GenesisPhase)
        try:
            idx = phases.index(self)
            if idx > 0:
                return phases[idx - 1]
        except ValueError:
            pass
        return None
    
    @property
    def theme(self) -> dict[str, Any]:
        """Get the visual theme for this phase."""
        themes = {
            GenesisPhase.AWAKENING: {
                "color": "#6B21A8",  # Deep purple
                "accent": "#A855F7",
                "animation": "pulse",
                "icon": "eye",
                "description": "Opening the inner eye",
            },
            GenesisPhase.EXCAVATION: {
                "color": "#92400E",  # Earth brown
                "accent": "#D97706",
                "animation": "dig",
                "icon": "pickaxe",
                "description": "Unearthing hidden patterns",
            },
            GenesisPhase.MAPPING: {
                "color": "#0891B2",  # Cyan
                "accent": "#06B6D4",
                "animation": "connect",
                "icon": "constellation",
                "description": "Connecting the stars",
            },
            GenesisPhase.SYNTHESIS: {
                "color": "#7C3AED",  # Violet
                "accent": "#A78BFA",
                "animation": "spiral",
                "icon": "weave",
                "description": "Weaving the tapestry",
            },
            GenesisPhase.ACTIVATION: {
                "color": "#DC2626",  # Fire red
                "accent": "#F87171",
                "animation": "ignite",
                "icon": "flame",
                "description": "Igniting the sovereign",
            },
        }
        return themes.get(self, themes[GenesisPhase.AWAKENING])


# =============================================================================
# TRAIT TRACKING
# =============================================================================

@dataclass
class DetectedTrait:
    """A single detected trait with confidence tracking."""
    name: str
    value: Any
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    probed: bool = False
    detected_at: datetime = field(default_factory=datetime.utcnow)
    framework: str = "general"
    category: str = "trait"
    
    def add_evidence(self, evidence: str, confidence_boost: float = 0.1) -> None:
        """Add supporting evidence and increase confidence."""
        if evidence not in self.evidence:
            self.evidence.append(evidence)
            self.confidence = min(1.0, self.confidence + confidence_boost)
    
    def add_contradiction(self, evidence: str, confidence_penalty: float = 0.15) -> None:
        """Add contradicting evidence and decrease confidence."""
        self.confidence = max(0.0, self.confidence - confidence_penalty)
        self.evidence.append(f"[CONTRA] {evidence}")
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "probed": self.probed,
            "detected_at": self.detected_at.isoformat(),
            "framework": self.framework,
            "category": self.category,
        }


# =============================================================================
# THE PROFILE RUBRIC
# =============================================================================

@dataclass
class ProfileRubric:
    """
    The master container for all detected traits and patterns.
    
    Organized by framework (Human Design, Jungian, etc.) and category.
    This is the "Digital Twin" data structure.
    """
    
    # Human Design Framework
    hd_type: Optional[DetectedTrait] = None  # Generator, Projector, Manifestor, Reflector, MG
    hd_strategy: Optional[DetectedTrait] = None  # Wait to Respond, Wait for Invitation, etc.
    hd_authority: Optional[DetectedTrait] = None  # Sacral, Emotional, Splenic, etc.
    hd_profile: Optional[DetectedTrait] = None  # 1/3, 2/4, 3/5, etc.
    hd_definition: Optional[DetectedTrait] = None  # Single, Split, Triple, Quadruple
    
    # Jungian/Cognitive Functions
    jung_dominant: Optional[DetectedTrait] = None  # Ni, Ne, Si, Se, Ti, Te, Fi, Fe
    jung_auxiliary: Optional[DetectedTrait] = None
    jung_tertiary: Optional[DetectedTrait] = None
    jung_inferior: Optional[DetectedTrait] = None
    jung_shadow: Optional[DetectedTrait] = None  # Primary shadow pattern
    
    # Somatic/Energetic
    energy_pattern: Optional[DetectedTrait] = None  # Sustainable, Burst, Wave, etc.
    nervous_system: Optional[DetectedTrait] = None  # Regulated, Hypervigilant, Collapsed
    rest_style: Optional[DetectedTrait] = None  # Active rest, Complete stillness, etc.
    
    # Core Patterns
    core_wound: Optional[DetectedTrait] = None
    core_gift: Optional[DetectedTrait] = None
    core_desire: Optional[DetectedTrait] = None
    core_fear: Optional[DetectedTrait] = None
    
    # Behavioral
    decision_style: Optional[DetectedTrait] = None  # Intuitive, Analytical, Emotional, Collaborative
    social_style: Optional[DetectedTrait] = None  # Leader, Supporter, Observer, Catalyst
    conflict_style: Optional[DetectedTrait] = None  # Confront, Avoid, Mediate, Withdraw
    
    # Additional traits as key-value
    additional_traits: dict[str, DetectedTrait] = field(default_factory=dict)
    
    def get_trait(self, name: str) -> Optional[DetectedTrait]:
        """Get a trait by name from any category."""
        # Check built-in fields first
        if hasattr(self, name) and getattr(self, name) is not None:
            return getattr(self, name)
        # Check additional traits
        return self.additional_traits.get(name)
    
    def set_trait(self, name: str, trait: DetectedTrait) -> None:
        """Set a trait by name."""
        if hasattr(self, name):
            setattr(self, name, trait)
        else:
            self.additional_traits[name] = trait
    
    def get_all_traits(self) -> list[DetectedTrait]:
        """Get all detected traits with confidence > 0."""
        traits = []
        for attr in dir(self):
            if attr.startswith('_') or attr in ['additional_traits', 'get_trait', 'set_trait', 'get_all_traits', 'to_dict', 'get_high_confidence_traits', 'get_low_confidence_traits', 'completion_percentage']:
                continue
            value = getattr(self, attr)
            if isinstance(value, DetectedTrait) and value.confidence > 0:
                traits.append(value)
        traits.extend([t for t in self.additional_traits.values() if t.confidence > 0])
        return traits
    
    def get_high_confidence_traits(self, threshold: float = 0.8) -> list[DetectedTrait]:
        """Get traits with high confidence (verified)."""
        return [t for t in self.get_all_traits() if t.confidence >= threshold]
    
    def get_low_confidence_traits(self, threshold: float = 0.6) -> list[DetectedTrait]:
        """Get traits needing more probing."""
        return [t for t in self.get_all_traits() if 0 < t.confidence < threshold]
    
    def completion_percentage(self) -> float:
        """Calculate how complete the profile is."""
        core_fields = [
            'hd_type', 'hd_strategy', 'hd_authority',
            'jung_dominant', 'energy_pattern',
            'core_wound', 'core_gift', 'decision_style'
        ]
        filled = sum(1 for f in core_fields if getattr(self, f) is not None and getattr(self, f).confidence >= 0.7)
        return filled / len(core_fields)
    
    def get_completion_percentage(self) -> float:
        """Alias for completion_percentage - returns as percentage (0-100)."""
        return self.completion_percentage() * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {}
        for trait in self.get_all_traits():
            result[trait.name] = trait.to_dict()
        return result


# =============================================================================
# SESSION MEMORY
# =============================================================================

@dataclass
class SessionMemory:
    """Conversation history and context for a session."""
    messages: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to the conversation history."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            msg["metadata"] = metadata
        self.messages.append(msg)
    
    def add_turn(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Alias for add_message (for backwards compatibility)."""
        self.add_message(role=role, content=content, metadata=metadata)
    
    def get_last_n(self, n: int = 10) -> list[dict]:
        """Get the last N messages."""
        return self.messages[-n:]
    
    def to_dict(self) -> dict:
        return {
            "messages": self.messages,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionMemory":
        memory = cls()
        memory.messages = data.get("messages", [])
        memory.context = data.get("context", {})
        return memory


# =============================================================================
# ACTIVE SIGNAL
# =============================================================================

@dataclass 
class ActiveSignal:
    """A signal that is currently being tracked/investigated."""
    source: str = ""
    content: str = ""
    signal_type: str = ""
    confidence: float = 0.0
    suggested_traits: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "content": self.content,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "suggested_traits": self.suggested_traits,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# GENESIS SESSION STATE
# =============================================================================

@dataclass
class GenesisState:
    """
    The complete state for a Genesis profiling session.
    
    This is passed through the LangGraph workflow and contains:
    - Current phase and question progress
    - All user responses
    - The profile rubric being built
    - Active hypotheses being probed
    - Conversation history
    """
    
    # Session identity
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # Phase tracking
    phase: GenesisPhase = GenesisPhase.AWAKENING
    question_index: int = 0
    total_questions_asked: int = 0
    
    # Responses
    responses: list[dict] = field(default_factory=list)
    
    # The Profile being built
    rubric: ProfileRubric = field(default_factory=ProfileRubric)
    
    # Session memory (conversation history)
    memory: SessionMemory = field(default_factory=SessionMemory)
    
    # Active signals being tracked
    active_signals: list[ActiveSignal] = field(default_factory=list)
    
    # Current hypotheses from the Hypothesis Engine
    current_hypotheses: list[dict] = field(default_factory=list)
    
    # Extracted insights (human-readable summaries)
    insights: list[str] = field(default_factory=list)
    
    # Pending probes awaiting user response
    pending_probes: list[dict] = field(default_factory=list)
    
    # Whether the profile is complete enough to proceed
    profile_complete: bool = False
    
    # Conversation turn counter
    conversation_turn: int = 0
    
    # The current question being asked (for tracking responses)
    current_question: str = ""
    
    def add_response(self, question: str, response: str, phase: Optional[GenesisPhase] = None) -> None:
        """Record a user response."""
        self.responses.append({
            "phase": (phase or self.phase).value,
            "question": question,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "turn": self.conversation_turn,
        })
        self.total_questions_asked += 1
        self.conversation_turn += 1
        self.last_activity = datetime.utcnow()
    
    def advance_question(self, questions_per_phase: int = 3) -> bool:
        """
        Advance to the next phase when the current phase is complete.
        
        This is called when _should_advance_phase returns True, meaning
        we've collected enough responses for the current phase.
        
        Returns True if phase changed, False otherwise.
        """
        # Get actual response count for current phase
        current_phase_responses = len(self.get_phase_responses(self.phase.value))
        
        # Only advance if we've actually met the target
        if current_phase_responses >= questions_per_phase:
            next_phase = self.phase.next_phase()
            if next_phase:
                self.phase = next_phase
                self.question_index = 0  # Reset for new phase
                return True
            else:
                # Completed all phases
                self.profile_complete = True
                return True  # Return True to signal completion
        
        # Increment question index within phase
        self.question_index += 1
        return False
    
    def add_insight(self, insight: str) -> None:
        """Add a discovered insight."""
        if insight not in self.insights:
            self.insights.append(insight)
    
    def add_pending_probe(self, probe: dict) -> None:
        """Add a probe awaiting user response."""
        self.pending_probes.append(probe)
    
    def resolve_probe(self, probe_id: str) -> Optional[dict]:
        """Remove and return a resolved probe."""
        for i, probe in enumerate(self.pending_probes):
            if probe.get('id') == probe_id:
                return self.pending_probes.pop(i)
        return None
    
    def add_signal(self, signal: ActiveSignal) -> None:
        """Add an active signal being tracked."""
        self.active_signals.append(signal)
    
    def get_phase_responses(self, phase: str) -> list[dict]:
        """Get all responses for a specific phase."""
        return [r for r in self.responses if r.get("phase") == phase]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "phase": self.phase.value,
            "question_index": self.question_index,
            "total_questions_asked": self.total_questions_asked,
            "responses": self.responses,
            "rubric": self.rubric.to_dict(),
            "insights": self.insights,
            "pending_probes": self.pending_probes,
            "profile_complete": self.profile_complete,
            "conversation_turn": self.conversation_turn,
            "current_question": self.current_question,
            "completion_percentage": self.rubric.completion_percentage(),
            "memory": self.memory.to_dict(),
            "active_signals": [s.to_dict() for s in self.active_signals],
            "current_hypotheses": self.current_hypotheses,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GenesisState":
        """Reconstruct from dictionary."""
        state = cls()
        state.session_id = data.get("session_id", "")
        state.phase = GenesisPhase(data.get("phase", "awakening"))
        state.question_index = data.get("question_index", 0)
        state.total_questions_asked = data.get("total_questions_asked", 0)
        state.responses = data.get("responses", [])
        state.insights = data.get("insights", [])
        state.pending_probes = data.get("pending_probes", [])
        state.profile_complete = data.get("profile_complete", False)
        state.conversation_turn = data.get("conversation_turn", 0)
        state.current_question = data.get("current_question", "")
        state.current_hypotheses = data.get("current_hypotheses", [])
        
        # Reconstruct memory
        if "memory" in data:
            state.memory = SessionMemory.from_dict(data["memory"])
        
        # Reconstruct active signals
        for sig_data in data.get("active_signals", []):
            sig = ActiveSignal(
                source=sig_data.get("source", ""),
                content=sig_data.get("content", ""),
                signal_type=sig_data.get("signal_type", ""),
                confidence=sig_data.get("confidence", 0.0),
                suggested_traits=sig_data.get("suggested_traits", {}),
            )
            state.active_signals.append(sig)
        
        # Note: rubric reconstruction would need more logic
        return state


# =============================================================================
# PHASE QUESTIONS
# =============================================================================

PHASE_QUESTIONS: dict[GenesisPhase, list[str]] = {
    GenesisPhase.AWAKENING: [
        "What brings you here today? What are you seeking to understand about yourself?",
        "Describe a moment when you felt completely alive and aligned. What were you doing?",
        "What pattern in your life keeps recurring, perhaps appearing as both challenge and gift?",
    ],
    GenesisPhase.EXCAVATION: [
        "What truth about yourself have you been avoiding?",
        "Describe your relationship with rest and activity. When do you feel depleted?",
        "What emotions do you tend to suppress, and which ones flow freely?",
    ],
    GenesisPhase.MAPPING: [
        "How do you typically make important decisions - through logic, emotion, or intuition?",
        "Describe your ideal environment for deep work and reflection.",
        "What role do you naturally assume in group dynamics?",
    ],
    GenesisPhase.SYNTHESIS: [
        "Looking at the patterns we've uncovered, what theme emerges most strongly?",
        "How might your challenges actually be pointing toward your gifts?",
        "What wisdom from your past self would serve you now?",
    ],
    GenesisPhase.ACTIVATION: [
        "What one practice could you begin today that honors your true design?",
        "How will you know when you're living in alignment with your authentic self?",
        "What is the next brave step your soul is calling you toward?",
    ],
}


def get_phase_question(phase: GenesisPhase, index: int) -> str:
    """Get the question for a specific phase and index."""
    questions = PHASE_QUESTIONS.get(phase, [])
    if 0 <= index < len(questions):
        return questions[index]
    return questions[0] if questions else "Tell me more about yourself."


def get_questions_in_phase(phase: GenesisPhase) -> int:
    """Get the number of questions in a phase."""
    return len(PHASE_QUESTIONS.get(phase, []))
