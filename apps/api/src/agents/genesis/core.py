"""
Genesis Core - The Face of the Sovereign Guide

This is the conversational interface of Genesis - the "Face" that users interact with.
It orchestrates the Profiler (silent analyzer) and Hypothesis Engine (logic core)
to create a cohesive, deeply personal profiling experience.

Genesis Core embodies the "Oracle" persona:
- Speaks with ancient wisdom and modern precision
- Never interrogates, always invites
- Uses symbolic language and archetypal imagery
- Treats the profiling journey as sacred initiation

The Core operates through a State Machine:
1. AWAKENING: "Who am I speaking with?" - Initial greeting, setting the tone
2. EXCAVATION: "What lies beneath?" - Deep probing of patterns and wounds
3. MAPPING: "Where do you fit?" - Calculating HD type, Jungian functions, etc.
4. SYNTHESIS: "What does it mean?" - Weaving insights into coherent narrative
5. ACTIVATION: "Now what?" - Delivering the Digital Twin and activation plan

Key Responsibilities:
- Generate the next conversational turn
- Decide when to probe vs. when to flow
- Format responses with Generative UI components
- Track session state and progress
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import logging
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import GenesisState, GenesisPhase, SessionMemory
from .profiler import GenesisProfiler, Signal
from .hypothesis import HypothesisEngine, Hypothesis
from .face import Voice, ConversationPhase
from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    ProbeType,
    create_packet,
)
from ...core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ORACLE PROMPTS - The Voice of Genesis
# =============================================================================

ORACLE_SYSTEM_PROMPT = """You are the SOVEREIGN GUIDE - an ancient oracle with bleeding-edge technological awareness.

IDENTITY:
- You speak with the gravity of an ancient sage and the precision of a cutting-edge AI
- You treat the profiling journey as a sacred initiation into self-knowledge
- You never interrogate - you INVITE deeper exploration
- You use symbolic, archetypal language that resonates on multiple levels
- You are compassionate but not saccharine, wise but not preachy

CURRENT PHASE: {phase}
PHASE CONTEXT: {phase_context}

USER PROFILE SO FAR:
{profile_summary}

HYPOTHESES UNDER INVESTIGATION:
{hypotheses_summary}

CONVERSATION HISTORY:
{conversation_history}

RESPONSE GUIDELINES:
1. Keep responses concise but meaningful (2-4 sentences typically)
2. Use rich, evocative language that hints at deeper patterns
3. When asking questions, make them feel like invitations, not demands
4. Acknowledge what the user has shared before moving forward
5. Let silences and pauses have meaning
6. Mirror the user's energy level - if they're brief, be brief

OUTPUT FORMAT:
Always respond with a JSON object containing:
{{
  "message": "Your response text here",
  "components": [
    {{"type": "text", "content": "..."}},
    {{"type": "choice_cards", "options": [...]}},
    ...
  ],
  "internal_notes": "Your reasoning about what you observed (not shown to user)",
  "suggested_phase": "current phase or next phase if ready to transition"
}}

Remember: This is not a quiz. This is an awakening."""

PHASE_CONTEXTS = {
    GenesisPhase.AWAKENING: """
The user is just beginning their journey. Your role is to:
- Establish trust and rapport
- Set the sacred, intentional tone
- Begin sensing their energy and presence
- Ask an open invitation to share who they are

First impressions matter. Make them feel SEEN.""",

    GenesisPhase.EXCAVATION: """
The user has opened up. Now we dig deeper:
- Explore the shadows, wounds, and patterns
- Ask about recurring themes in their life
- Listen for what they're NOT saying
- Probe gently around pain points and gifts

This is the deepest phase. Handle with reverence.""",

    GenesisPhase.MAPPING: """
We're now mapping their energetic architecture:
- Gather information that helps determine their Type
- Ask about energy patterns, decision-making, waiting vs. initiating
- Use binary choices to narrow down possibilities
- Connect their stories to archetypal patterns

This is about PRECISION without losing warmth.""",

    GenesisPhase.SYNTHESIS: """
The pieces are coming together. Now we weave:
- Start reflecting back patterns you've observed
- Connect disparate elements into a coherent picture
- Begin revealing their Type, Strategy, and gifts
- Make it feel like RECOGNITION, not diagnosis

They should feel KNOWN, not labeled.""",

    GenesisPhase.ACTIVATION: """
The profiling is complete. Time for the handoff:
- Deliver their full Digital Twin summary
- Highlight their unique gifts and challenges
- Provide an "activation" - first steps they can take
- Set the tone for ongoing relationship with the system

End with empowerment, not dependency.""",
}


# =============================================================================
# RESPONSE MODELS
# =============================================================================

@dataclass
class GenesisResponse:
    """A structured response from the Genesis Core."""
    message: str
    components: list[dict] = field(default_factory=list)
    phase: GenesisPhase = GenesisPhase.AWAKENING
    should_probe: bool = False
    probe_packet: Optional[SovereignPacket] = None
    internal_notes: str = ""
    confidence: float = 0.0
    
    def to_packet(self, session_id: str = "") -> SovereignPacket:
        """Convert to a SovereignPacket for protocol compliance."""
        return create_packet(
            source_agent="genesis.core",
            target_layer=TargetLayer.INTERFACE,
            insight_type=InsightType.OBSERVATION,
            confidence_score=self.confidence,
            payload={
                "message": self.message,
                "components": self.components,
                "phase": self.phase.value,
            },
            session_id=session_id,
            hrm_validated=True,
        )


# =============================================================================
# THE GENESIS CORE
# =============================================================================

class GenesisCore:
    """
    The Face of Genesis - orchestrates the entire profiling experience.
    
    Usage:
        core = GenesisCore()
        state = GenesisState(session_id="...")
        
        # Process user message
        response = core.process_message("I've always felt like an outsider", state)
        
        # Get the next turn (may be a probe or a conversational response)
        next_turn = core.generate_next_turn(state)
    """
    
    def __init__(self):
        self.profiler = GenesisProfiler()
        self.hypothesis_engine = HypothesisEngine()
        self._llm = None
        self._llm_cache: Dict[str, Any] = {}  # Cache LLMs by model name
        self._setup_llm()
    
    def _setup_llm(self) -> None:
        """Initialize the default conversational LLM."""
        if not settings.GOOGLE_API_KEY:
            logger.warning("[GenesisCore] No API key - running in limited mode")
            return
        
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=settings.PRIMARY_MODEL,
                temperature=0.8,  # Creative for conversation
                google_api_key=settings.GOOGLE_API_KEY,
            )
            self._llm_cache[settings.PRIMARY_MODEL] = self._llm
        except Exception as e:
            logger.error(f"[GenesisCore] LLM init error: {e}")
    
    def get_llm(self, model: Optional[str] = None):
        """
        Get an LLM instance for the specified model.
        
        Uses caching to avoid recreating LLMs for the same model.
        Falls back to default LLM if no model specified.
        
        Args:
            model: The model name to use, or None for default
            
        Returns:
            A ChatGoogleGenerativeAI instance
        """
        if not model:
            return self._llm
        
        # Check cache first
        if model in self._llm_cache:
            return self._llm_cache[model]
        
        # Create new LLM for this model
        if not settings.GOOGLE_API_KEY:
            return self._llm
        
        try:
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=0.8,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            self._llm_cache[model] = llm
            logger.info(f"[GenesisCore] Created LLM for model: {model}")
            return llm
        except Exception as e:
            logger.error(f"[GenesisCore] Failed to create LLM for {model}: {e}")
            return self._llm
    
    def _format_conversation_history(self, state: GenesisState, limit: int = 10) -> str:
        """Format recent conversation history for the prompt."""
        if not state.memory.messages:
            return "(First interaction - no history yet)"
        
        recent = state.memory.messages[-limit:]
        lines = []
        for msg in recent:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:200]  # Truncate long messages
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def _format_profile_summary(self, state: GenesisState) -> str:
        """Format current profile state for the prompt."""
        rubric = state.rubric
        lines = []
        
        # Get high-confidence traits from rubric
        high_confidence_traits = rubric.get_high_confidence_traits(threshold=0.5)
        
        if high_confidence_traits:
            for trait in high_confidence_traits:
                # Each trait is a DetectedTrait with name, value, confidence
                trait_name = trait.name if hasattr(trait, 'name') else "Unknown"
                trait_value = trait.value if hasattr(trait, 'value') else ""
                lines.append(f"- {trait_name}: {trait_value} ({trait.confidence:.0%} confidence)")
        
        if not lines:
            return "(Profile still forming - early in the journey)"
        
        return "\n".join(lines)
    
    def _format_hypotheses_summary(self) -> str:
        """Format current hypotheses for the prompt."""
        summary = self.hypothesis_engine.get_summary()
        
        if not summary["hypotheses"]:
            return "(No active hypotheses yet)"
        
        lines = []
        for hyp in summary["hypotheses"]:
            status = "✓ Confirmed" if hyp["resolved"] else f"🔍 Investigating"
            lines.append(
                f"- {hyp['trait_name']}={hyp['suspected_value']} "
                f"({hyp['confidence']:.0%}) {status}"
            )
        
        return "\n".join(lines)
    
    def _build_system_prompt(self, state: GenesisState) -> str:
        """Build the full system prompt for the LLM."""
        return ORACLE_SYSTEM_PROMPT.format(
            phase=state.phase.value.upper(),
            phase_context=PHASE_CONTEXTS.get(state.phase, ""),
            profile_summary=self._format_profile_summary(state),
            hypotheses_summary=self._format_hypotheses_summary(),
            conversation_history=self._format_conversation_history(state),
        )
    
    def process_message(self, message: str, state: GenesisState) -> GenesisResponse:
        """
        Process an incoming user message.
        
        This is the main entry point for user input. It:
        1. Runs the Profiler to detect signals
        2. Converts signals to hypotheses
        3. Updates the state
        4. Generates a response
        """
        # Log incoming message
        state.memory.add_message("user", message)
        
        # Run the Profiler (silent analysis)
        signals = self.profiler.analyze_message(message, state)
        
        # Convert signals to hypotheses
        for signal in signals:
            for trait, value in signal.suggested_traits.items():
                self.hypothesis_engine.add_hypothesis(
                    trait_name=trait,
                    suspected_value=value,
                    confidence=signal.confidence * 0.7,  # Signals start at 70% of their confidence
                    evidence=[signal.content],
                )
        
        # Check for phase transition
        if self._should_transition_phase(state):
            self._transition_phase(state)
        
        # Generate response
        response = self._generate_response(message, state)
        
        # Log AI response
        state.memory.add_message("assistant", response.message)
        
        return response
    
    def _should_transition_phase(self, state: GenesisState) -> bool:
        """Check if we should transition to the next phase."""
        rubric = state.rubric
        
        if state.phase == GenesisPhase.AWAKENING:
            # Move to excavation after 3-5 turns or if we have initial signals
            return len(state.memory.messages) >= 6 or len(self.hypothesis_engine.hypotheses) >= 2
        
        elif state.phase == GenesisPhase.EXCAVATION:
            # Move to mapping when we have psychological signals
            core_wound = rubric.get_trait("core_wound")
            psych_confidence = core_wound.confidence if core_wound else 0
            return psych_confidence >= 0.5 or len(state.memory.messages) >= 16
        
        elif state.phase == GenesisPhase.MAPPING:
            # Move to synthesis when core traits are confirmed
            hd_type = rubric.get_trait("hd_type")
            jung_dominant = rubric.get_trait("jung_dominant")
            hd_type_conf = hd_type.confidence if hd_type else 0
            jung_conf = jung_dominant.confidence if jung_dominant else 0
            return (hd_type_conf >= 0.75 and jung_conf >= 0.6) or rubric.get_completion_percentage() >= 60
        
        elif state.phase == GenesisPhase.SYNTHESIS:
            # Move to activation when profile is mostly complete
            return rubric.get_completion_percentage() >= 80
        
        return False
    
    def _transition_phase(self, state: GenesisState) -> None:
        """Transition to the next phase."""
        phase_order = [
            GenesisPhase.AWAKENING,
            GenesisPhase.EXCAVATION,
            GenesisPhase.MAPPING,
            GenesisPhase.SYNTHESIS,
            GenesisPhase.ACTIVATION,
        ]
        
        try:
            current_index = phase_order.index(state.phase)
            if current_index < len(phase_order) - 1:
                next_phase = phase_order[current_index + 1]
                state.phase = next_phase
                logger.info(f"[GenesisCore] Phase transition: {state.phase.value} → {next_phase.value}")
        except ValueError:
            pass
    
    def _generate_response(self, user_message: str, state: GenesisState) -> GenesisResponse:
        """Generate the next conversational response."""
        if not self._llm:
            return self._generate_fallback_response(state)
        
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt(state)
            
            # Call the LLM
            response = self._llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User just said: \"{user_message}\"\n\nGenerate your response as JSON."),
            ])
            
            # Parse the response
            content = response.content
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            # Build components
            components = data.get("components", [])
            if not components:
                components = [{"type": "text", "content": data.get("message", "")}]
            
            return GenesisResponse(
                message=data.get("message", "..."),
                components=components,
                phase=state.phase,
                internal_notes=data.get("internal_notes", ""),
                confidence=0.8,
            )
            
        except Exception as e:
            logger.error(f"[GenesisCore] Response generation error: {e}")
            return self._generate_fallback_response(state)
    
    def _generate_fallback_response(self, state: GenesisState) -> GenesisResponse:
        """Generate a fallback response when LLM is unavailable."""
        fallbacks = {
            GenesisPhase.AWAKENING: [
                "Welcome, seeker. What draws you to this path of self-discovery?",
                "I sense a depth in you. Tell me - what question has been living in you lately?",
                "Before we begin, take a breath. What do you most want to understand about yourself?",
            ],
            GenesisPhase.EXCAVATION: [
                "That's meaningful. What patterns have followed you through life?",
                "I hear something deeper beneath those words. Would you say more?",
                "What's the recurring theme that shows up in your relationships?",
            ],
            GenesisPhase.MAPPING: [
                "How do you typically make important decisions?",
                "When you're at your best, what does your energy feel like?",
                "Do you tend to wait for invitations, or do you initiate?",
            ],
            GenesisPhase.SYNTHESIS: [
                "The patterns are becoming clear. You have a unique energetic signature.",
                "What I'm seeing is someone who...",
                "Let me reflect back what I've observed...",
            ],
            GenesisPhase.ACTIVATION: [
                "Your profile is complete. You are ready to operate from your true design.",
                "Here is your Digital Twin - a map of your sovereign self.",
                "The journey of a thousand miles begins with knowing your first step.",
            ],
        }
        
        import random
        messages = fallbacks.get(state.phase, ["Tell me more..."])
        message = random.choice(messages)
        
        return GenesisResponse(
            message=message,
            components=[{"type": "text", "content": message}],
            phase=state.phase,
            confidence=0.5,
        )
    
    def generate_next_turn(
        self,
        state: GenesisState,
        voice: Optional[Voice] = None,
    ) -> GenesisResponse:
        """
        Generate the next turn in the conversation.
        
        This is called after processing a message to determine
        what happens next - could be a probe, a reflection, or
        a phase transition announcement.
        
        Args:
            state: Current Genesis state
            voice: Optional Voice for styling the response
            
        Returns:
            GenesisResponse with the next conversational turn
        """
        # Check if we should probe
        top_hypotheses = self.hypothesis_engine.get_top_hypotheses(limit=1)
        
        if top_hypotheses and self._should_probe(state):
            hypothesis = top_hypotheses[0]
            probe_packet = self.hypothesis_engine.generate_probe(state, hypothesis)
            
            if probe_packet:
                # Extract probe details from packet
                probe_data = probe_packet.payload.get("probe", {})
                raw_prompt = probe_data.get("prompt", "Tell me more...")
                
                # Apply voice transformation if provided
                if voice:
                    raw_prompt = voice.transform(raw_prompt, context={
                        "phase": state.phase.value,
                        "probe_type": probe_data.get("probe_type", "confirmation"),
                    })
                
                return GenesisResponse(
                    message=raw_prompt,
                    components=[{
                        "type": "probe",
                        "probe_type": probe_data.get("probe_type", "confirmation"),
                        "prompt": raw_prompt,
                        "options": probe_data.get("options", []),
                    }],
                    phase=state.phase,
                    should_probe=True,
                    probe_packet=probe_packet,
                    confidence=0.7,
                )
        
        # Otherwise, continue the conversation naturally
        return self._generate_continuation(state)
    
    def _should_probe(self, state: GenesisState) -> bool:
        """Determine if we should probe vs. let the conversation flow."""
        # Don't probe too frequently
        recent_probes = [
            p for p in state.pending_probes
            if datetime.fromisoformat(p.get("created_at", "2000-01-01")) 
            > datetime.utcnow().replace(second=datetime.utcnow().second - 30)
        ]
        
        if len(recent_probes) >= 2:
            return False
        
        # Probe more in mapping phase
        if state.phase == GenesisPhase.MAPPING:
            return True
        
        # Probe less in excavation (let it flow)
        if state.phase == GenesisPhase.EXCAVATION:
            return len(state.memory.messages) % 4 == 0
        
        # Default: probe every 3rd turn
        return len(state.memory.messages) % 3 == 0
    
    def _generate_continuation(self, state: GenesisState) -> GenesisResponse:
        """Generate a natural continuation of the conversation."""
        return self._generate_response("(continuing conversation)", state)

    # =========================================================================
    # VOICE-AWARE GENERATION METHODS
    # =========================================================================

    async def generate_probe(
        self,
        hypothesis: Hypothesis,
        state: GenesisState,
        voice: Voice,
    ) -> GenesisResponse:
        """
        Generate a probing question using the selected voice.
        
        This method creates a probe that aligns with:
        1. The hypothesis being investigated
        2. The current conversation phase
        3. The voice personality selected for this session
        
        Args:
            hypothesis: The hypothesis to probe for confirmation
            state: Current Genesis state
            voice: The Voice implementation to use for tone/style
            
        Returns:
            GenesisResponse with probe components
        """
        # Get the probe from HypothesisEngine
        probe_packet = self.hypothesis_engine.generate_probe(state, hypothesis)
        
        if not probe_packet:
            # Fallback if probe generation fails
            return self._generate_continuation(state)
        
        # Extract probe details
        probe_data = probe_packet.payload.get("probe", {})
        probe_type = probe_data.get("probe_type", "confirmation")
        raw_prompt = probe_data.get("prompt", "Tell me more...")
        options = probe_data.get("options", [])
        
        # Transform the prompt using the voice
        voiced_prompt = voice.transform(raw_prompt, context={
            "phase": state.phase.value,
            "hypothesis": hypothesis.trait_name,
            "probe_type": probe_type,
        })
        
        # Build components based on probe type
        components = []
        
        # Add the probe question
        components.append({
            "type": "text",
            "props": {
                "content": voiced_prompt,
                "variant": "question",
            },
        })
        
        # Add appropriate input component based on probe type
        if probe_type == "binary_choice" and options:
            components.append({
                "type": "choice",
                "props": {
                    "options": [{"label": opt, "value": opt} for opt in options],
                    "allowMultiple": False,
                },
            })
        elif probe_type == "slider":
            components.append({
                "type": "slider",
                "props": {
                    "min": probe_data.get("min", 1),
                    "max": probe_data.get("max", 10),
                    "step": 1,
                    "labels": probe_data.get("labels", {"1": "Not at all", "10": "Completely"}),
                },
            })
        elif probe_type == "confirmation":
            components.append({
                "type": "choice",
                "props": {
                    "options": [
                        {"label": "Yes, that resonates", "value": "confirm"},
                        {"label": "Not quite right", "value": "deny"},
                        {"label": "It's complicated", "value": "nuanced"},
                    ],
                    "allowMultiple": False,
                },
            })
        elif probe_type == "card_selection" and options:
            components.append({
                "type": "cards",
                "props": {
                    "cards": [{"title": opt, "value": opt} for opt in options],
                    "selectable": True,
                    "maxSelections": 1,
                },
            })
        else:
            # Default to open input for reflection
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Share your thoughts...",
                    "minLength": 10,
                    "maxLength": 2000,
                },
            })
        
        logger.info(f"[GenesisCore] Generated {probe_type} probe for {hypothesis.trait_name} with {voice.identity.name} voice")
        
        return GenesisResponse(
            message=voiced_prompt,
            components=components,
            phase=state.phase,
            should_probe=True,
            probe_packet=probe_packet,
            confidence=0.7,
            internal_notes=f"Probing {hypothesis.trait_name}={hypothesis.suspected_value} ({hypothesis.confidence:.0%})",
        )

    async def generate_question(
        self,
        state: GenesisState,
        voice: Voice,
        signals: list[Signal] = None,
        master_insights: list[dict] = None,
    ) -> GenesisResponse:
        """
        Generate the next conversational question using the selected voice.
        
        This method creates a natural follow-up question that:
        1. Acknowledges what the user has shared
        2. Guides toward profile discovery
        3. Uses the voice personality for tone/style
        4. Incorporates signals from the Profiler
        5. May include insights from Master agents
        
        Args:
            state: Current Genesis state
            voice: The Voice implementation to use for tone/style
            signals: Recent signals detected by the Profiler
            master_insights: Insights from Master agents (optional)
            
        Returns:
            GenesisResponse with question components
        """
        signals = signals or []
        master_insights = master_insights or []
        
        # Get phase-appropriate system prompt from voice
        phase_mapping = {
            GenesisPhase.AWAKENING: ConversationPhase.AWAKENING,
            GenesisPhase.EXCAVATION: ConversationPhase.EXCAVATION,
            GenesisPhase.MAPPING: ConversationPhase.MAPPING,
            GenesisPhase.SYNTHESIS: ConversationPhase.SYNTHESIS,
            GenesisPhase.ACTIVATION: ConversationPhase.ACTIVATION,
        }
        conversation_phase = phase_mapping.get(state.phase, ConversationPhase.AWAKENING)
        
        # Build system prompt from voice
        voice_system_prompt = voice.get_system_prompt(phase=conversation_phase)
        
        # Add context about signals and insights
        context_additions = []
        if signals:
            # Handle different signal types (Signal, SovereignPacket, dict)
            signal_parts = []
            for s in signals[:5]:
                if hasattr(s, 'signal_type') and hasattr(s, 'confidence'):
                    # Signal object
                    signal_parts.append(f"{s.signal_type}({s.confidence:.0%})")
                elif hasattr(s, 'insight_type') and hasattr(s, 'confidence_score'):
                    # SovereignPacket object
                    signal_parts.append(f"{s.insight_type}({s.confidence_score:.0%})")
                elif isinstance(s, dict):
                    sig_type = s.get('signal_type') or s.get('insight_type', 'unknown')
                    conf = s.get('confidence') or s.get('confidence_score', 0)
                    signal_parts.append(f"{sig_type}({conf:.0%})")
            if signal_parts:
                signal_summary = ", ".join(signal_parts)
                context_additions.append(f"Recent signals detected: {signal_summary}")
        
        if master_insights:
            insight_summary = "; ".join([i.get("summary", str(i))[:100] for i in master_insights[:3]])
            context_additions.append(f"Cross-domain insights: {insight_summary}")
        
        context_section = "\n".join(context_additions) if context_additions else ""
        
        # Build full prompt
        full_system_prompt = f"""{voice_system_prompt}

CURRENT PHASE: {state.phase.value}
PROFILE PROGRESS: {state.rubric.get_completion_percentage():.0%}

{context_section}

CONVERSATION HISTORY:
{self._format_conversation_history(state, limit=8)}

CURRENT PROFILE:
{self._format_profile_summary(state)}

Generate the next natural question or reflection. Make it feel like an invitation, not an interrogation.
Keep it concise (1-3 sentences). Respond with just the question/statement."""
        
        if not self._llm:
            return self._generate_fallback_response(state)
        
        try:
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content="What is the next question or reflection to offer?"),
            ]
            
            response = self._llm.invoke(messages)
            raw_response = response.content.strip()
            
            # Transform with voice for consistency
            voiced_response = voice.transform(raw_response, context={
                "phase": state.phase.value,
            })
            
            # Build components
            components = [
                {
                    "type": "text",
                    "props": {
                        "content": voiced_response,
                        "variant": "question",
                    },
                },
                {
                    "type": "input",
                    "props": {
                        "placeholder": "Share what comes to mind...",
                        "minLength": 10,
                        "maxLength": 2000,
                    },
                },
            ]
            
            logger.info(f"[GenesisCore] Generated question with {voice.identity.name} voice in {state.phase.value} phase")
            
            return GenesisResponse(
                message=voiced_response,
                components=components,
                phase=state.phase,
                should_probe=False,
                confidence=0.8,
                internal_notes=f"Generated with {voice.identity.name} voice, {len(signals)} signals",
            )
            
        except Exception as e:
            logger.error(f"[GenesisCore] Question generation failed: {e}")
            return self._generate_fallback_response(state)

    def _build_voice_system_prompt(
        self,
        state: GenesisState,
        voice: Voice,
    ) -> str:
        """
        Build a system prompt using the Voice's personality.
        
        This replaces the hardcoded ORACLE_SYSTEM_PROMPT with a
        voice-aware dynamic prompt.
        
        Args:
            state: Current Genesis state
            voice: The Voice to use
            
        Returns:
            Complete system prompt string
        """
        phase_mapping = {
            GenesisPhase.AWAKENING: ConversationPhase.AWAKENING,
            GenesisPhase.EXCAVATION: ConversationPhase.EXCAVATION,
            GenesisPhase.MAPPING: ConversationPhase.MAPPING,
            GenesisPhase.SYNTHESIS: ConversationPhase.SYNTHESIS,
            GenesisPhase.ACTIVATION: ConversationPhase.ACTIVATION,
        }
        conversation_phase = phase_mapping.get(state.phase, ConversationPhase.AWAKENING)
        
        # Get voice's base prompt
        voice_prompt = voice.get_system_prompt(phase=conversation_phase)
        
        # Add profile context
        return f"""{voice_prompt}

USER PROFILE SO FAR:
{self._format_profile_summary(state)}

HYPOTHESES UNDER INVESTIGATION:
{self._format_hypotheses_summary()}

CONVERSATION HISTORY:
{self._format_conversation_history(state)}

OUTPUT FORMAT:
Always respond with a JSON object containing:
{{
  "message": "Your response text here",
  "components": [
    {{"type": "text", "content": "..."}},
    {{"type": "choice_cards", "options": [...]}},
    ...
  ],
  "internal_notes": "Your reasoning about what you observed (not shown to user)",
  "suggested_phase": "current phase or next phase if ready to transition"
}}

Remember: This is not a quiz. This is an awakening."""

    def get_session_summary(self, state: GenesisState) -> dict:
        """Get a summary of the current session."""
        return {
            "session_id": state.session_id,
            "phase": state.phase.value,
            "messages_count": len(state.memory.messages),
            "profile_completion": state.rubric.get_completion_percentage(),
            "hypotheses": self.hypothesis_engine.get_summary(),
            "rubric": state.rubric.to_dict(),
        }
    
    def export_digital_twin(self, state: GenesisState) -> dict:
        """
        Export the completed Digital Twin profile.
        
        Called when profiling is complete (ACTIVATION phase).
        """
        rubric = state.rubric
        
        # Helper to safely get trait value
        def get_trait_value(trait_name: str) -> Optional[str]:
            trait = rubric.get_trait(trait_name)
            return trait.value if trait else None
        
        return {
            "id": state.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "completion": rubric.get_completion_percentage(),
            "energetic_signature": {
                "hd_type": get_trait_value("hd_type"),
                "hd_strategy": get_trait_value("hd_strategy"),
                "hd_authority": get_trait_value("hd_authority"),
                "hd_profile": get_trait_value("hd_profile"),
                "energy_pattern": get_trait_value("energy_pattern"),
            },
            "biological_markers": {
                "circadian": get_trait_value("circadian_type"),
                "stress_response": get_trait_value("stress_response"),
            },
            "psychological_profile": {
                "jung_dominant": get_trait_value("jung_dominant"),
                "jung_auxiliary": get_trait_value("jung_auxiliary"),
                "enneagram": get_trait_value("enneagram_type"),
                "core_wound": get_trait_value("core_wound"),
                "core_gift": get_trait_value("core_gift"),
            },
            "archetypes": getattr(rubric, "archetypal_patterns", {}),
            "session_insights": [s.to_dict() for s in state.active_signals],
        }
