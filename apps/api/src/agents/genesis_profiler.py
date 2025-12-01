"""
Genesis Profiler Agent - High-Fidelity Intelligent Profiling System

This is the main entry point for the Genesis profiling system. It follows
the Fractal Extensibility Pattern, acting as a thin orchestration layer
that delegates to specialized modules:

    - session_manager.py  - Session lifecycle and state management
    - swarm_integration.py - SwarmBus communication with Master agents
    - core.py             - The Face (Oracle persona, response generation)
    - profiler.py         - The Scout (silent pattern detection)
    - hypothesis.py       - The Logic (confidence-based probing)
    - state.py            - The Memory (ProfileRubric, session state)
    - face/               - Voice personalities and modulation

Design Principles:
    - Thin orchestration layer (under 500 lines)
    - All heavy logic delegated to specialized modules
    - Clean interface for the chat router
    - Full SwarmBus integration for Master agent coordination
    - Meticulous error handling and logging

Author: Project Sovereign
Version: 2.0.0 (Fractal Architecture)
"""

from typing import AsyncGenerator, Optional, Dict, Any, List, Union
from datetime import datetime
import logging
import asyncio

from ..core.schemas import AgentInput, AgentContext, AgentOutput

from .base import BaseAgent
from .genesis import (
    GenesisState,
    GenesisPhase,
    ProfileRubric,
    GenesisCore,
    GenesisProfiler,
    HypothesisEngine,
    Signal,
)
from .genesis.session_manager import GenesisSessionManager, GenesisSession
from .genesis.swarm_integration import GenesisSwarmHandler
from .genesis.face import FaceOrchestrator, VoiceSelectionMode, ConversationPhase
from ..core.config import settings
from ..shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    PacketPriority,
    create_packet,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Phrases that indicate a fresh session start (not a user response)
INITIALIZATION_PHRASES = frozenset([
    "begin the genesis",
    "start the genesis",
    "initialize genesis",
    "begin profiling",
    "start profiling",
    "first interaction",
    "introduce yourself",
    "who are you",
    "hello",
    "hi",
    "hey",
    "start",
    "begin",
])

# Phase to voice mapping for personality selection (voice IDs are strings)
PHASE_VOICE_MAP: Dict[str, str] = {
    "awakening": "oracle",
    "excavation": "mirror",
    "mapping": "sage",
    "synthesis": "oracle",
    "activation": "challenger",
}

# Target interactions per phase before advancing
PHASE_TARGETS: Dict[GenesisPhase, int] = {
    GenesisPhase.AWAKENING: 3,
    GenesisPhase.EXCAVATION: 5,
    GenesisPhase.MAPPING: 5,
    GenesisPhase.SYNTHESIS: 3,
    GenesisPhase.ACTIVATION: 2,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_initialization_request(message: str) -> bool:
    """
    Detect if a message is an initialization request vs a user response.
    
    Args:
        message: The user's message text
    
    Returns:
        True if this is an initialization request, False if it's a response
    """
    if not message:
        return True
    
    normalized = message.lower().strip()
    
    for phrase in INITIALIZATION_PHRASES:
        if phrase in normalized:
            return True
    
    if len(normalized) < 10 and normalized in {"start", "begin", "go", "ok", "yes"}:
        return True
    
    return False


def get_voice_for_phase(phase: str) -> str:
    """Get the appropriate voice ID for the current profiling phase."""
    return PHASE_VOICE_MAP.get(phase, "oracle")


# ============================================================================
# GENESIS PROFILER AGENT
# ============================================================================

class GenesisProfilerAgent(BaseAgent):
    """
    High-fidelity intelligent profiling agent.
    
    This agent builds a comprehensive Digital Twin by:
    1. Engaging in natural, adaptive conversation
    2. Silently detecting patterns in user responses
    3. Forming and testing hypotheses about traits
    4. Coordinating with Master agents for cross-domain insights
    5. Generating rich UI components for interaction
    
    The agent progresses through 5 phases:
        - AWAKENING: Initial connection and trust building
        - EXCAVATION: Deep exploration of patterns and history
        - MAPPING: Structured assessment and confirmation
        - SYNTHESIS: Integration and insight generation
        - ACTIVATION: Empowerment and practical application
    """
    
    # Class-level attributes required by BaseAgent
    name = "genesis_profiler"
    description = "Intelligent profiling system for building your Digital Twin"
    version = "2.0.0"
    frameworks = ["human-design", "gene-keys", "jungian", "somatic"]
    capabilities = [
        "profiling",
        "generative-ui",
        "multi-phase",
        "voice-selection",
        "pattern-detection",
        "hypothesis-probing",
        "swarm-communication",
    ]
    requires_hrm = False
    
    def __init__(self):
        """Initialize the Genesis Profiler with all subsystems."""
        # Core fractal components
        self._session_manager = GenesisSessionManager()
        self._swarm = GenesisSwarmHandler(self._session_manager)
        self._core = GenesisCore()
        self._profiler = GenesisProfiler()
        self._hypothesis_engine = HypothesisEngine()
        
        # Initialization flag
        self._initialized = False
        
        logger.info("[GenesisProfilerAgent] Initialized with fractal architecture")
    
    async def initialize(self) -> None:
        """
        Initialize async components (SwarmBus subscription).
        
        This should be called once during application startup.
        """
        if self._initialized:
            return
        
        try:
            # Register with SwarmBus
            from ..core.swarm_bus import get_bus, AgentTier
            bus = await get_bus()
            await bus.subscribe(
                agent_id="genesis.profiler",
                handler=self._swarm.handle_message,
                agent_tier=AgentTier.DOMAIN,
                domain="genesis",
                capability="profiling",
            )
            self._initialized = True
            logger.info("[GenesisProfilerAgent] Async initialization complete")
        except Exception as e:
            logger.error(f"[GenesisProfilerAgent] Initialization error: {e}")
            self._initialized = True
    
    async def _handle_swarm_message(
        self, 
        envelope: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle incoming messages from the SwarmBus.
        
        Args:
            envelope: The SwarmEnvelope containing the message
        
        Returns:
            Optional response to send back
        """
        try:
            packet = envelope.get("packet", {})
            source = packet.get("source_agent", "unknown")
            payload = packet.get("payload", {})
            session_id = packet.get("session_id")
            
            logger.debug(
                f"[GenesisProfilerAgent] Received from {source}: "
                f"{payload.get('type', 'unknown')}"
            )
            
            if session_id:
                session = self._session_manager.get_session(session_id)
                if session:
                    session.add_master_insight(source, payload)
            
            message_type = payload.get("type")
            
            if message_type == "hypothesis_correlation":
                return await self._handle_hypothesis_correlation(payload, session_id)
            elif message_type == "profile_insight":
                return await self._handle_profile_insight(payload, session_id)
            elif message_type == "request_status":
                return self._get_status(session_id)
            
            return None
            
        except Exception as e:
            logger.error(f"[GenesisProfilerAgent] Error handling swarm message: {e}")
            return {"error": str(e)}
    
    async def _handle_hypothesis_correlation(
        self,
        payload: Dict[str, Any],
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Handle a hypothesis correlation from Master Hypothesis Engine."""
        correlation = payload.get("correlation", {})
        
        if session_id:
            session = self._session_manager.get_session(session_id)
            if session:
                for trait_key, confidence in correlation.get("traits", {}).items():
                    self._hypothesis_engine.add_hypothesis(
                        trait_key=trait_key,
                        confidence=confidence,
                        source="master_hypothesis",
                    )
        
        return {"acknowledged": True, "type": "hypothesis_correlation"}
    
    async def _handle_profile_insight(
        self,
        payload: Dict[str, Any],
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Handle a profile insight from Master Scout."""
        insight = payload.get("insight", {})
        
        if session_id:
            session = self._session_manager.get_session(session_id)
            if session:
                session.add_master_insight("master_scout", insight)
        
        return {"acknowledged": True, "type": "profile_insight"}
    
    def _get_status(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Get current agent status for orchestrator."""
        status = {
            "agent": self.name,
            "version": self.version,
            "active_sessions": len(self._session_manager.list_sessions()),
        }
        
        if session_id:
            summary = self._session_manager.get_session_summary(session_id)
            if summary:
                status["session"] = summary
        
        return status
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session entirely.
        
        Args:
            session_id: The session to clear
        
        Returns:
            True if session was cleared
        """
        cleared = self._session_manager.clear_session(session_id)
        if cleared:
            logger.info(f"[GenesisProfilerAgent] Cleared session: {session_id}")
        return cleared
    
    def restore_session(
        self,
        session_id: str,
        session_state_dict: Dict[str, Any],
    ) -> bool:
        """
        Restore a session from a saved state.
        
        This allows resuming a saved profile from where it left off.
        
        Args:
            session_id: New session ID to use
            session_state_dict: The saved GenesisState dictionary
        
        Returns:
            True if session was restored successfully
        """
        try:
            self._session_manager.restore_session(session_id, session_state_dict)
            logger.info(f"[GenesisProfilerAgent] Restored session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"[GenesisProfilerAgent] Failed to restore session: {e}")
            return False
    
    def _auto_save_session(self, session_id: str, state: GenesisState) -> None:
        """
        Auto-save session to persistent storage.
        
        Called periodically during profiling to enable crash recovery.
        
        Args:
            session_id: The session to save
            state: Current GenesisState
        """
        try:
            from ..storage import get_profile_storage
            storage = get_profile_storage()
            storage.save_session(session_id, state.to_dict())
        except Exception as e:
            # Non-fatal - just log the error
            logger.warning(f"[GenesisProfilerAgent] Auto-save failed: {e}")
    
    def _dict_to_agent_output(self, result: Dict[str, Any]) -> AgentOutput:
        """
        Convert internal dict response to AgentOutput Pydantic model.
        
        This ensures contract compliance with BaseAgent.execute() signature.
        """
        # Extract components and phase for visualizationData
        components = result.get('components', [])
        phase = result.get('phase', 'awakening')
        
        # Build visualizationData structure
        visualization_data = {
            'components': components,
            'phase': phase,
        }
        
        # Include any additional visualization metadata
        for key in ['questionIndex', 'totalQuestions', 'overallProgress', 'overallTotal', 'voice', 'error']:
            if key in result:
                visualization_data[key] = result[key]
        
        # Build calculation dict with all phase/progress info
        calculation = {
            'phase': phase,
            'questionIndex': result.get('questionIndex', 0),
            'totalQuestions': result.get('totalQuestions', 5),
            'overallProgress': result.get('overallProgress', 0),
            'overallTotal': result.get('overallTotal', 18),
            'voice': result.get('voice', 'natural'),
            'sophistication_level': result.get('sophistication_level', 'casual'),
            'sophistication_score': result.get('sophistication_score', 0.0),
            'profile_complete': result.get('profile_complete', False),
        }
        
        # Include any extra calculation data from result
        if result.get('calculation'):
            calculation.update(result['calculation'])
        
        return AgentOutput(
            interpretationSeed=result.get('interpretationSeed', ''),
            method=result.get('method', 'genesis_profiler'),
            confidence=result.get('confidence', 0.5),
            calculation=calculation,
            correlations=result.get('correlations'),
            visualizationData=visualization_data,
        )
    
    async def execute(
        self,
        input_data: Union[Dict[str, Any], AgentInput],
        model: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgentOutput:
        """
        Execute a single turn of the Genesis profiling conversation.
        
        Args:
            input_data: The AgentInput containing user message and context (dict or Pydantic model)
            model: The model to use (from user's model switcher selection)
            session_id: Unique session identifier for state tracking
        
        Returns:
            AgentOutput Pydantic model with interpretation and UI components
        """
        if not self._initialized:
            await self.initialize()
        
        # Use selected model or fall back to config default
        from ..core.config import settings
        active_model = model if model else settings.PRIMARY_MODEL
        
        # Handle both dict and Pydantic model inputs
        if hasattr(input_data, 'context'):
            # It's a Pydantic AgentInput model
            context = input_data.context
            user_message = context.userQuery if context and context.userQuery else ""
            input_session_id = getattr(input_data, 'session_id', None)
        else:
            # It's a dict
            context = input_data.get("context", {})
            user_message = context.get("userQuery", "") if isinstance(context, dict) else ""
            input_session_id = input_data.get("session_id")
        
        session_id = session_id or input_session_id or "default"
        session = self._session_manager.get_or_create_session(session_id)
        
        # Store the selected model in session for sub-components to use
        session.active_model = active_model
        
        state = GenesisState.from_dict(session.genesis_state_dict)
        
        is_init = is_initialization_request(user_message)
        
        logger.info(
            f"[GenesisProfilerAgent] Execute - session={session_id[:8]}... "
            f"phase={state.phase.value} is_init={is_init} "
            f"responses={len(state.responses)} model={active_model}"
        )
        
        try:
            if is_init and len(state.responses) == 0:
                result = await self._generate_opening(state, session)
            else:
                result = await self._process_response(user_message, state, session)
            
            self._session_manager.update_session(
                session_id=session_id,
                genesis_state_dict=state.to_dict(),
            )
            
            # Auto-save session for crash recovery
            self._auto_save_session(session_id, state)
            
            await self._emit_insights_to_swarm(state, session_id, session)
            
            # Convert dict to AgentOutput for contract compliance
            return self._dict_to_agent_output(result)
            
        except Exception as e:
            logger.error(f"[GenesisProfilerAgent] Execute error: {e}", exc_info=True)
            error_result = self._create_error_response(str(e), state.phase.value)
            return self._dict_to_agent_output(error_result)
    
    async def _generate_opening(
        self,
        state: GenesisState,
        session: GenesisSession,
    ) -> Dict[str, Any]:
        """
        Generate the opening message for a fresh session.
        
        Uses the Natural voice layer by default for a casual, approachable
        first interaction. The opening should feel like meeting a friendly
        new acquaintance, not being interrogated by an oracle.
        """
        # Get voice - will return Natural voice by default (sophistication is 0)
        voice = session.face.get_voice(
            context={"phase": "awakening", "is_opening": True},
            history=[]
        )
        
        voice_id = voice.identity.id
        
        logger.info(f"[GenesisProfilerAgent] Opening with voice: {voice_id}")
        
        # Build opening message - Natural voice will make it casual
        # If Natural voice is active, use natural opening
        if voice_id == "natural":
            opening_message = self._get_natural_opening()
        else:
            # Use generate_next_turn for deeper voices
            opening = self._core.generate_next_turn(state=state, voice=voice)
            opening_message = voice.transform(opening.message)
        
        # Convert to dict format
        components = []
        
        # Add text component with opening message
        components.append({
            "type": "text",
            "props": {
                "content": opening_message,
                "variant": "question" if voice_id == "natural" else "oracle",
            },
        })
        
        # For Natural voice, suggest easy component (slider or choice)
        # to make the first interaction very accessible
        if voice_id == "natural":
            # Start with a simple question that's easy to answer
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Just say what's on your mind...",
                    "minLength": 5,  # Very low barrier for first response
                    "maxLength": 2000,
                },
            })
        else:
            # Deeper voices get standard input
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Share what comes to mind...",
                    "minLength": 20,
                    "maxLength": 2000,
                },
            })
        
        # Add progress indicator with accurate values
        awakening_target = PHASE_TARGETS.get(GenesisPhase.AWAKENING, 3)
        total_expected = sum(PHASE_TARGETS.values())
        
        components.append({
            "type": "progress",
            "props": {
                "phase": "awakening",
                "phaseIndex": 0,
                "totalPhases": len(PHASE_TARGETS),
                "questionIndex": 0,
                "totalQuestions": awakening_target,
                "overallProgress": 0,
                "overallTotal": total_expected,
            },
        })
        
        # Track the current question for response matching
        state.current_question = opening_message
        
        return {
            "interpretationSeed": opening_message,
            "method": "genesis_profiler",
            "confidence": 1.0,
            "components": components,
            "phase": "awakening",
            "questionIndex": 0,
            "totalQuestions": awakening_target,
            "overallProgress": 0,
            "overallTotal": total_expected,
            "voice": voice_id,
            "sophistication_level": "casual",  # Always casual at opening
        }
    
    def _get_natural_opening(self) -> str:
        """
        Get a casual, natural opening message.
        
        These are designed to feel like meeting a friendly new person,
        not entering a spiritual consultation.
        """
        import random
        
        openings = [
            "Hey! So, what made you want to try this out?",
            
            "Hey there! So tell me - what's been on your mind lately?",
            
            "Hi! I'm curious - what brings you here today?",
            
            "Hey! Before we dive in, I'm just curious - what are you hoping to figure out?",
            
            "Hi there! So... what's going on with you?",
        ]
        
        return random.choice(openings)
    
    async def _process_response(
        self,
        user_message: str,
        state: GenesisState,
        session: GenesisSession,
    ) -> Dict[str, Any]:
        """
        Process a user response and generate the next interaction.
        
        This method now integrates the Natural layer:
        1. Analyzes user sophistication after each response
        2. Tracks when sophistication threshold is crossed
        3. Transforms generated questions through Natural voice
        4. Selects appropriate UI components based on question type
        """
        current_phase = state.phase  # Keep as GenesisPhase enum
        current_phase_value = current_phase.value  # String for logs/metadata
        
        # Step 0: ANALYZE USER SOPHISTICATION
        # This updates the Face's understanding of the user's depth
        sophistication_metrics = session.face.analyze_user_response(user_message)
        sophistication_level = session.face.sophistication_level
        
        logger.info(
            f"[GenesisProfilerAgent] Sophistication: {sophistication_level} "
            f"(score={sophistication_metrics.overall_score:.2f})"
        )
        
        # Step 1: Silent profiling - detect patterns
        signals = await self._profiler.analyze(user_message, state)
        
        # Step 2: Update hypotheses based on signals
        for signal in signals:
            self._hypothesis_engine.process_signal(signal)
        
        # Step 3: Record the response
        state.add_response(
            phase=current_phase,
            question=state.current_question or "unknown",
            response=user_message,
        )
        
        # Step 4: Add to conversation memory
        state.memory.add_turn(
            role="user",
            content=user_message,
            metadata={
                "phase": current_phase_value, 
                "signals": len(signals),
                "sophistication": sophistication_level,
                "sophistication_score": sophistication_metrics.overall_score,
            },
        )
        
        # Step 5: Check for phase transition FIRST
        should_advance = self._should_advance_phase(state)
        if should_advance:
            phase_changed = state.advance_question(questions_per_phase=PHASE_TARGETS.get(state.phase, 3))
            if phase_changed:
                logger.info(f"[GenesisProfilerAgent] Phase transition: {current_phase_value} → {state.phase.value}")
        
        # Step 6: CHECK FOR PROFILE COMPLETION
        if state.profile_complete:
            logger.info(f"[GenesisProfilerAgent] Profile complete! Generating Digital Twin...")
            return await self._generate_completion_response(state, session)
        
        # Step 7: Check if we should probe for hypothesis confirmation
        pending_probe = self._hypothesis_engine.get_priority_probe()
        
        if pending_probe and pending_probe.confidence < 0.8:
            result = await self._generate_probe(pending_probe, state, session)
        else:
            result = await self._generate_next_question(state, session, signals)
        
        # Step 8: Add sophistication info to result
        result["sophistication_level"] = sophistication_level
        result["sophistication_score"] = sophistication_metrics.overall_score
        
        # Step 9: If sophistication threshold crossed, notify swarm
        if session.face.is_threshold_crossed():
            result["sophistication_threshold_crossed"] = True
            # Will emit signal in _emit_insights_to_swarm
        
        # Add phase transition info if phase changed
        if should_advance and state.phase.value != current_phase_value:
            result["phase_transition"] = {
                "from": current_phase_value,
                "to": state.phase.value,
            }
        
        return result
    
    async def _generate_completion_response(
        self,
        state: GenesisState,
        session: GenesisSession,
    ) -> Dict[str, Any]:
        """
        Generate the final completion response with Digital Twin delivery.
        
        This is called when profiling is complete. It:
        1. Exports the full Digital Twin
        2. Generates a personalized completion message
        3. Sends the Digital Twin to Master Scout for storage
        4. Broadcasts profile readiness to all agents
        5. Returns the completion UI components
        """
        # Step 1: Export the Digital Twin
        digital_twin = self._core.export_digital_twin(state)
        
        logger.info(
            f"[GenesisProfilerAgent] Digital Twin exported "
            f"(completion={digital_twin.get('completion', 0):.0%})"
        )
        
        # Step 2: Get voice for completion message
        voice = session.face.get_voice(
            context={"phase": "activation", "is_completion": True},
            history=[],
        )
        
        # Step 3: Generate completion message with voice personality
        completion_message = await self._generate_twin_summary_message(
            digital_twin, state, voice
        )
        
        # Step 4: Send Digital Twin to Master Scout
        await self._swarm.send_digital_twin(
            session_id=state.session_id,
            digital_twin=digital_twin,
        )
        
        # Step 5: Broadcast profile readiness to all agents
        await self._swarm.broadcast_profile_ready(
            session_id=state.session_id,
            digital_twin_summary=digital_twin,
        )
        
        # Step 6: Build completion UI components
        components = self._build_completion_components(
            digital_twin, completion_message, voice.identity.id
        )
        
        return {
            "interpretationSeed": completion_message,
            "method": "genesis_profiler",
            "confidence": 1.0,
            "components": components,
            "phase": "complete",
            "profile_complete": True,
            "digital_twin": digital_twin,
            "voice": voice.identity.id,
        }
    
    async def _generate_twin_summary_message(
        self,
        digital_twin: Dict[str, Any],
        state: GenesisState,
        voice: Any,
    ) -> str:
        """
        Generate a personalized completion message summarizing the Digital Twin.
        
        Uses the LLM to weave together the discovered traits into
        a meaningful, voice-appropriate message.
        """
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from ..core.config import settings
        
        # Extract key findings
        energetic = digital_twin.get("energetic_signature", {})
        psychological = digital_twin.get("psychological_profile", {})
        
        hd_type = energetic.get("hd_type") or "a unique"
        energy = energetic.get("energy_pattern") or "dynamic"
        jung = psychological.get("jung_dominant") or "intuitive"
        gift = psychological.get("core_gift") or "authentic self-expression"
        
        # Build context for completion message
        profile_context = f"""
Digital Twin Summary:
- Human Design Type: {hd_type}
- Energy Pattern: {energy}
- Dominant Cognitive Function: {jung}
- Core Gift: {gift}
- Profile Completion: {digital_twin.get('completion', 0):.0%}

Conversation Summary:
- Total exchanges: {len(state.responses)}
- Phases completed: AWAKENING → EXCAVATION → MAPPING → SYNTHESIS → ACTIVATION
- Key insights discovered: {len(state.insights)}
"""
        
        # Get voice system prompt for personality
        voice_prompt = voice.get_system_prompt(ConversationPhase.ACTIVATION)
        
        prompt = f"""{voice_prompt}

CRITICAL MOMENT: You are delivering the completed Digital Twin to the user.
This is a sacred moment of recognition - they should feel SEEN.

{profile_context}

Generate a completion message that:
1. Celebrates the journey they've completed
2. Reflects back their core essence in 2-3 sentences
3. Names their unique gift with reverence
4. Ends with a bridge to what comes next

Keep it under 150 words. Make it feel like a coronation, not a report.
Speak in your voice ({voice.identity.name})."""

        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.PRIMARY_MODEL,
                temperature=0.7,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            
            response = await llm.ainvoke([
                SystemMessage(content="You are delivering a sacred moment of recognition."),
                HumanMessage(content=prompt),
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"[GenesisProfilerAgent] Completion message error: {e}")
            # Fallback message
            return (
                f"Your journey through the Genesis profiling is complete. "
                f"You are a {hd_type} with a {energy} energy signature. "
                f"Your gift of {gift} shines through your {jung} way of seeing. "
                f"The Sovereign system now knows you deeply."
            )
    
    def _build_completion_components(
        self,
        digital_twin: Dict[str, Any],
        completion_message: str,
        voice_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Build the UI components for profile completion.
        
        IMPORTANT: Component format must match frontend ComponentDefinition interface.
        - Regular components use: {type, props: {...}} OR {type, content, ...}
        - Completion components use root-level fields: {type, digital_twin, steps, ...}
        
        The frontend reads:
        - digitalTwinComp?.digital_twin (expects DigitalTwinData at root)
        - activationStepsComp?.steps (expects ActivationStep[] at root)
        - completionTransitionComp?.transition_type
        """
        energetic = digital_twin.get("energetic_signature", {})
        psychological = digital_twin.get("psychological_profile", {})
        
        return [
            # Main completion message - uses props for consistency with other text components
            {
                "type": "text",
                "content": completion_message,
                "variant": "completion",
                "animate": True,
            },
            
            # Digital Twin card - frontend reads digital_twin at root level
            {
                "type": "digital_twin_card",
                "digital_twin": {
                    "energetic_signature": energetic,
                    "psychological_profile": psychological,
                    "biological_markers": digital_twin.get("biological_markers", {}),
                    "archetypes": digital_twin.get("archetypes", {}),
                    "session_insights": digital_twin.get("session_insights", []),
                    "completion_percentage": digital_twin.get("completion", 0),
                    "created_at": digital_twin.get("created_at"),
                    "summary": completion_message,
                },
            },
            
            # Activation steps - frontend reads steps at root level
            {
                "type": "activation_steps",
                "steps": self._generate_activation_steps(digital_twin),
            },
            
            # Transition to main app - frontend reads transition_type at root
            {
                "type": "completion_transition",
                "transition_type": "reveal",
                "title": "Your Sovereign Journey Begins",
                "message": (
                    "Your Digital Twin is now active and will guide personalized "
                    "experiences across the entire Sovereign system. "
                    "The main app experience is coming soon."
                ),
                "cta_text": "Continue to Dashboard",
                "cta_action": "navigate_dashboard",
            },
            
            # Progress indicator - uses standard ComponentDefinition fields
            {
                "type": "progress",
                "phase": "complete",
                "current": 5,
                "total": 5,
            },
        ]
    
    def _generate_activation_steps(
        self,
        digital_twin: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Generate personalized activation steps based on the Digital Twin.
        
        These are the first actionable steps the user can take based on
        their unique profile.
        """
        energetic = digital_twin.get("energetic_signature", {}) or {}
        psychological = digital_twin.get("psychological_profile", {}) or {}
        
        # Safely get string values with fallback
        hd_type = (energetic.get("hd_type") or "").lower()
        energy = (energetic.get("energy_pattern") or "").lower()
        
        # Base steps for everyone
        steps = []
        step_id = 1
        
        # HD Type specific steps
        if hd_type == "projector":
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "🎯",
                "title": "Wait for Recognition",
                "description": (
                    "Practice noticing when you're being invited vs. initiating. "
                    "Your power comes from being seen first."
                ),
                "priority": "high",
                "category": "Strategy",
                "estimated_time": "Ongoing practice",
            })
            step_id += 1
        elif hd_type == "generator":
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "⚡",
                "title": "Honor Your Sacral Response",
                "description": (
                    "Before committing to anything, check your gut. "
                    "That 'uh-huh' or 'nuh-uh' is your guide."
                ),
                "priority": "high",
                "category": "Strategy",
                "estimated_time": "Ongoing practice",
            })
            step_id += 1
        elif hd_type == "manifestor":
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "📢",
                "title": "Inform Before Acting",
                "description": (
                    "Your power to initiate is immense. Let others know "
                    "what you're creating - it smooths your path."
                ),
                "priority": "high",
                "category": "Strategy",
                "estimated_time": "Before each action",
            })
            step_id += 1
        elif hd_type == "reflector":
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "🌙",
                "title": "Wait a Lunar Cycle",
                "description": (
                    "Major decisions benefit from 28 days of reflection. "
                    "Sample the experience, don't rush."
                ),
                "priority": "high",
                "category": "Strategy",
                "estimated_time": "28 days",
            })
            step_id += 1
        else:
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "🧭",
                "title": "Follow Your Strategy",
                "description": (
                    "Your unique design has a strategy. "
                    "Let us help you discover and embody it."
                ),
                "priority": "high",
                "category": "Discovery",
                "estimated_time": "Ongoing",
            })
            step_id += 1
        
        # Energy pattern steps
        if "depleted" in energy:
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "🔋",
                "title": "Prioritize Rest",
                "description": (
                    "Your energy signature suggests a need for restoration. "
                    "Schedule non-negotiable rest periods."
                ),
                "priority": "high",
                "category": "Energy",
                "estimated_time": "Daily",
            })
            step_id += 1
        elif "wave" in energy:
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "🌊",
                "title": "Ride Your Emotional Wave",
                "description": (
                    "Your energy moves in waves. Don't make decisions at peaks "
                    "or valleys - wait for clarity."
                ),
                "priority": "medium",
                "category": "Energy",
                "estimated_time": "Ongoing awareness",
            })
            step_id += 1
        
        # Core gift step
        core_gift = psychological.get("core_gift")
        if core_gift:
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "⭐",
                "title": f"Express Your Gift: {core_gift.title()}",
                "description": (
                    f"Your unique gift of {core_gift} is ready to shine. "
                    "Look for one opportunity today to express it."
                ),
                "priority": "medium",
                "category": "Growth",
                "estimated_time": "Daily practice",
            })
            step_id += 1
        else:
            steps.append({
                "id": f"activation-{step_id}",
                "icon": "⭐",
                "title": "Discover Your Gift",
                "description": (
                    "Your unique gift is emerging. Pay attention to what "
                    "comes naturally to you that others find valuable."
                ),
                "priority": "medium",
                "category": "Discovery",
                "estimated_time": "Ongoing awareness",
            })
            step_id += 1
        
        return steps
    
    async def _generate_probe(
        self,
        hypothesis: Any,
        state: GenesisState,
        session: GenesisSession,
    ) -> Dict[str, Any]:
        """Generate a probing question to confirm a hypothesis."""
        voice = session.face.get_voice(
            context={"phase": state.phase.value},
            history=[],
        )
        
        probe_response = await self._core.generate_probe(
            hypothesis=hypothesis,
            state=state,
            voice=voice,
        )
        
        # Use the GenesisResponse components directly
        components = probe_response.components if probe_response.components else []
        
        # Add progress indicator
        phase_index = list(GenesisPhase).index(state.phase)
        components.append({
            "type": "progress",
            "props": {
                "phase": state.phase.value,
                "phaseIndex": phase_index,
                "totalPhases": 5,
                "questionIndex": len(state.responses),
                "totalQuestions": 5,
            },
        })
        
        return {
            "interpretationSeed": probe_response.message,
            "method": "genesis_profiler",
            "confidence": hypothesis.confidence,
            "components": components,
            "phase": state.phase.value,
            "questionIndex": len(state.responses),
            "probing": True,
            "trait": hypothesis.trait_name,
        }
    
    async def _generate_next_question(
        self,
        state: GenesisState,
        session: GenesisSession,
        signals: List[Signal],
    ) -> Dict[str, Any]:
        """
        Generate the next conversational question.
        
        This method now:
        1. Gets the appropriate voice (Natural or deeper based on sophistication)
        2. Generates the question using the deeper framework
        3. TRANSFORMS through Natural layer if sophistication is low
        4. Selects appropriate UI components (sliders, choices, text)
        """
        # Get voice - Natural or deeper based on sophistication
        voice = session.face.get_voice(
            context={"phase": state.phase.value},
            history=[],
        )
        
        voice_id = voice.identity.id
        sophistication_level = session.face.sophistication_level
        
        logger.info(
            f"[GenesisProfilerAgent] Question generation with voice: {voice_id}, "
            f"sophistication: {sophistication_level}"
        )
        
        # Get master insights for context
        master_insights = []
        if session.master_hypothesis_insights:
            master_insights.extend(session.master_hypothesis_insights[-3:])
        if session.master_scout_insights:
            master_insights.extend(session.master_scout_insights[-3:])
        
        # Generate the question using Core (may use deeper voice prompts)
        question_response = await self._core.generate_question(
            state=state,
            voice=voice,
            signals=signals,
            master_insights=master_insights,
        )
        
        # TRANSFORM through Natural layer if we're in casual mode
        final_message = question_response.message
        if voice_id == "natural" and sophistication_level in ["casual", "warming_up"]:
            # Apply Natural voice transformation to make it casual
            final_message = voice.transform(question_response.message, context={
                "phase": state.phase.value,
                "sophistication": sophistication_level,
            })
        
        # Build components with smart UI selection
        components = self._build_smart_components(
            question_response, 
            state, 
            voice_id,
            sophistication_level,
        )
        
        # Add progress indicator with accurate phase info
        phase_index = list(GenesisPhase).index(state.phase)
        phase_target = PHASE_TARGETS.get(state.phase, 5)
        phase_responses = len(state.get_phase_responses(state.phase.value))
        total_expected = sum(PHASE_TARGETS.values())  # Total across all phases
        
        components.append({
            "type": "progress",
            "props": {
                "phase": state.phase.value,
                "phaseIndex": phase_index,
                "totalPhases": len(PHASE_TARGETS),
                "questionIndex": phase_responses,  # Questions in current phase
                "totalQuestions": phase_target,  # Target for current phase
                "overallProgress": len(state.responses),  # Total responses so far
                "overallTotal": total_expected,  # Total expected across all phases
            },
        })
        
        # Update state
        state.current_question = final_message
        
        state.memory.add_turn(
            role="assistant",
            content=final_message,
            metadata={
                "phase": state.phase.value, 
                "voice": voice_id,
                "sophistication": sophistication_level,
            },
        )
        
        return {
            "interpretationSeed": final_message,
            "method": "genesis_profiler",
            "confidence": question_response.confidence,
            "components": components,
            "phase": state.phase.value,
            "questionIndex": phase_responses,
            "totalQuestions": phase_target,
            "overallProgress": len(state.responses),
            "overallTotal": total_expected,
            "voice": voice_id,
            "sophistication_level": sophistication_level,
        }
    
    def _build_smart_components(
        self,
        question_response: Any,
        state: GenesisState,
        voice_id: str,
        sophistication_level: str,
    ) -> List[Dict[str, Any]]:
        """
        Build UI components with smart selection based on question type.
        
        For Natural voice (casual mode), prefer easy-to-answer components:
        - Sliders for "how much" or "to what degree" questions
        - Choices for "which one" or "A vs B" questions
        - Short text input for simple questions
        
        For sophisticated users, allow longer text inputs.
        """
        components = []
        
        # Get the transformed message
        message = question_response.message
        if voice_id == "natural" and sophistication_level in ["casual", "warming_up"]:
            from .genesis.face import VoiceRegistry
            natural_voice = VoiceRegistry.get("natural")
            if natural_voice:
                message = natural_voice.transform(message, context={
                    "phase": state.phase.value,
                    "sophistication": sophistication_level,
                })
        
        # Add the question text
        components.append({
            "type": "text",
            "props": {
                "content": message,
                "variant": "question" if voice_id == "natural" else "oracle",
            },
        })
        
        # If the response already has specific components, use them
        if question_response.components:
            for comp in question_response.components:
                if comp.get("type") != "text":  # Avoid duplicate text
                    components.append({
                        "type": comp.get("type", "text"),
                        "props": comp.get("props", comp),
                    })
            return components
        
        # Otherwise, intelligently select component based on question type
        # and sophistication level
        question_type = self._infer_question_type(message)
        
        if voice_id == "natural" and sophistication_level == "casual":
            # Very easy to answer - prefer choices/sliders
            if question_type == "spectrum":
                components.append({
                    "type": "slider",
                    "props": {
                        "min": 1,
                        "max": 10,
                        "step": 1,
                        "labels": {"1": "Not at all", "10": "Completely"},
                    },
                })
            elif question_type == "binary":
                components.append({
                    "type": "choice",
                    "props": {
                        "options": [
                            {"label": "Yes, definitely", "value": "yes"},
                            {"label": "Not really", "value": "no"},
                            {"label": "It's complicated", "value": "mixed"},
                        ],
                        "allowMultiple": False,
                    },
                })
            else:
                # Even for open questions, keep min length low
                components.append({
                    "type": "input",
                    "props": {
                        "placeholder": "Just say what comes to mind...",
                        "minLength": 5,
                        "maxLength": 1000,
                    },
                })
        elif sophistication_level == "warming_up":
            # User is opening up - can handle more
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Share what comes to mind...",
                    "minLength": 10,
                    "maxLength": 1500,
                },
            })
        else:
            # Sophisticated or deeper voice - fuller input
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Share your thoughts...",
                    "minLength": 20,
                    "maxLength": 2000,
                },
            })
        
        return components
    
    def _infer_question_type(self, message: str) -> str:
        """
        Infer the type of question to select appropriate component.
        
        Returns:
            - "spectrum" for how much/to what degree questions
            - "binary" for yes/no, this or that questions
            - "open" for exploratory questions
        """
        message_lower = message.lower()
        
        # Spectrum indicators
        spectrum_patterns = [
            "how much", "to what degree", "on a scale", "how often",
            "how strongly", "how comfortable", "how important",
            "rate ", "level of",
        ]
        for pattern in spectrum_patterns:
            if pattern in message_lower:
                return "spectrum"
        
        # Binary indicators
        binary_patterns = [
            " or ", "do you ", "are you ", "have you ", "would you ",
            "is it ", "does ", "yes or no", "true or false",
        ]
        for pattern in binary_patterns:
            if pattern in message_lower:
                return "binary"
        
        return "open"
    
    def _build_question_components(
        self,
        question: Dict[str, Any],
        state: GenesisState,
    ) -> List[Dict[str, Any]]:
        """Build UI components for a standard question."""
        phase_index = list(GenesisPhase).index(state.phase)
        
        components = [
            {
                "type": "progress",
                "props": {
                    "phase": state.phase.value,
                    "phaseIndex": phase_index,
                    "totalPhases": 5,
                    "questionIndex": len(state.responses),
                    "totalQuestions": question.get("total_questions", 5),
                },
            },
            {
                "type": "text",
                "props": {
                    "content": question["message"],
                    "variant": question.get("variant", "body"),
                },
            },
        ]
        
        question_type = question.get("type", "open")
        
        if question_type == "choice" and question.get("options"):
            components.append({
                "type": "choice",
                "props": {
                    "options": question["options"],
                    "allowMultiple": question.get("allow_multiple", False),
                },
            })
        elif question_type == "slider":
            components.append({
                "type": "slider",
                "props": {
                    "min": question.get("min", 1),
                    "max": question.get("max", 10),
                    "step": question.get("step", 1),
                    "labels": question.get("labels", {}),
                },
            })
        else:
            components.append({
                "type": "input",
                "props": {
                    "placeholder": question.get(
                        "placeholder", 
                        "Share your thoughts..."
                    ),
                    "minLength": question.get("min_length", 20),
                    "maxLength": question.get("max_length", 2000),
                },
            })
        
        return components
    
    def _build_probe_components(
        self,
        probe: Dict[str, Any],
        state: GenesisState,
    ) -> List[Dict[str, Any]]:
        """Build UI components for a hypothesis probe."""
        phase_index = list(GenesisPhase).index(state.phase)
        
        components = [
            {
                "type": "progress",
                "props": {
                    "phase": state.phase.value,
                    "phaseIndex": phase_index,
                    "totalPhases": 5,
                    "questionIndex": len(state.responses),
                    "totalQuestions": 5,
                },
            },
            {
                "type": "text",
                "props": {
                    "content": probe["message"],
                    "variant": "probe",
                },
            },
        ]
        
        probe_type = probe.get("probe_type", "binary")
        
        if probe_type == "binary":
            components.append({
                "type": "choice",
                "props": {
                    "options": probe.get("options", ["Yes", "No"]),
                    "style": "binary",
                },
            })
        elif probe_type == "slider":
            components.append({
                "type": "slider",
                "props": {
                    "min": probe.get("min", 1),
                    "max": probe.get("max", 10),
                    "step": 1,
                    "labels": probe.get(
                        "labels", 
                        {"1": "Not at all", "10": "Completely"}
                    ),
                },
            })
        elif probe_type == "cards":
            components.append({
                "type": "choice",
                "props": {
                    "options": probe.get("options", []),
                    "style": "cards",
                    "allowMultiple": False,
                },
            })
        else:
            components.append({
                "type": "input",
                "props": {
                    "placeholder": "Share more...",
                    "minLength": 10,
                },
            })
        
        return components
    
    def _should_advance_phase(self, state: GenesisState) -> bool:
        """
        Determine if we should advance to the next phase.
        
        Uses the actual count of responses in the current phase,
        compared to the target for that phase.
        """
        target = PHASE_TARGETS.get(state.phase, 5)
        phase_responses = state.get_phase_responses(state.phase.value)
        current_count = len(phase_responses)
        
        logger.debug(
            f"[GenesisProfilerAgent] Phase check: {state.phase.value} - "
            f"{current_count}/{target} responses"
        )
        
        return current_count >= target
    
    async def _emit_insights_to_swarm(
        self,
        state: GenesisState,
        session_id: str,
        session: Optional[Any] = None,
    ) -> None:
        """
        Emit detected insights to SwarmBus for Master agents.
        
        This now includes sophistication signals so all agents can
        adapt their communication style based on user depth.
        """
        try:
            confirmed = self._hypothesis_engine.get_confirmed_hypotheses()
            completion = state.rubric.get_completion_percentage()
            
            # Use the swarm handler's notify_masters method
            await self._swarm.notify_masters(
                session_id=session_id,
                hypotheses=[h.to_dict() for h in confirmed] if confirmed else [],
                phase=state.phase.value,
                completion=completion,
                signals=None,  # Could pass recent signals here if needed
            )
            
            # Emit sophistication signal if session is available
            if session and hasattr(session, 'face'):
                sophistication_signal = session.face.get_sophistication_signal()
                
                # Broadcast to all agents
                await self._swarm.broadcast_sophistication_signal(
                    session_id=session_id,
                    sophistication_signal=sophistication_signal,
                )
                
                # Special notification if threshold was just crossed
                if sophistication_signal.get('threshold_crossed'):
                    await self._swarm.notify_sophistication_threshold_crossed(
                        session_id=session_id,
                        sophistication_signal=sophistication_signal,
                    )
                
        except Exception as e:
            logger.warning(f"[GenesisProfilerAgent] Swarm emission error: {e}")
    
    def _create_error_response(
        self,
        error_message: str,
        phase: str,
    ) -> Dict[str, Any]:
        """Create an error response that keeps the conversation going."""
        # Use Natural voice for error messages - keep it casual and friendly
        error_text = (
            "Hmm, something got a bit mixed up on my end. "
            "No worries though! Let's just keep going. "
            "What were you saying?"
        )
        
        return {
            "interpretationSeed": error_text,
            "method": "genesis_profiler",
            "confidence": 0.5,
            "components": [
                {
                    "type": "text",
                    "props": {
                        "content": error_text,
                        "variant": "body",
                    },
                },
                {
                    "type": "input",
                    "props": {
                        "placeholder": "Continue sharing...",
                        "minLength": 10,
                    },
                },
            ],
            "phase": phase,
            "error": error_message,
        }
    
    async def stream(
        self,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the execution for real-time response.
        
        Args:
            input_data: The AgentInput
            session_id: Session identifier
        
        Yields:
            Chunks of the response
        """
        result = await self.execute(input_data, session_id)
        yield result


# ============================================================================
# MODULE-LEVEL SINGLETON
# ============================================================================

_genesis_agent: Optional[GenesisProfilerAgent] = None


def get_genesis_agent() -> GenesisProfilerAgent:
    """
    Get or create the Genesis Profiler agent singleton.
    
    Returns:
        The GenesisProfilerAgent instance
    """
    global _genesis_agent
    if _genesis_agent is None:
        _genesis_agent = GenesisProfilerAgent()
    return _genesis_agent


async def initialize_genesis_agent() -> GenesisProfilerAgent:
    """
    Initialize the Genesis agent with async components.
    
    This should be called during application startup.
    
    Returns:
        The initialized GenesisProfilerAgent instance
    """
    agent = get_genesis_agent()
    await agent.initialize()
    return agent