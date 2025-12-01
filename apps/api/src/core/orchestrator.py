"""
The Sovereign Orchestrator - The Central Brain of the Swarm

This module implements the "Master Router" using LangGraph - the intelligent
coordinator that receives all incoming requests and routes them to the appropriate
sub-agents based on intent analysis.

Enhanced with SwarmBus Integration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The Orchestrator now sits atop the SwarmBus, enabling:
- Real-time inter-agent communication
- Escalation handling from Master agents
- Cross-domain coordination
- Event-driven architecture

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                         ┌──────────────┐                                 │
│                         │  SWARM BUS   │                                 │
│                         └──────┬───────┘                                 │
│  ┌─────────────┐    ┌──────────▼────────┐    ┌─────────────┐            │
│  │   INTAKE    │───►│   ROUTER          │───►│  DISPATCH   │            │
│  │  (Receive)  │    │  (Decide + Bus)   │    │  (Execute)  │            │
│  └─────────────┘    └───────────────────┘    └─────────────┘            │
│         │                     │                     │                    │
│         ▼                     ▼                     ▼                    │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐            │
│  │   MASTER    │       │   MASTER    │       │   DOMAIN    │            │
│  │  HYPOTHESIS │       │   SCOUT     │       │   AGENTS    │            │
│  └─────────────┘       └─────────────┘       └─────────────┘            │
│         │                     │                     │                    │
│         └─────────────────────┴─────────────────────┘                    │
│                               ▼                                          │
│                        ┌─────────────┐                                   │
│                        │  SYNTHESIZE │                                   │
│                        │  (Combine)  │                                   │
│                        └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────┘

The Orchestrator operates on SovereignPackets exclusively. It:
1. Receives user messages wrapped in packets
2. Analyzes intent to determine which sub-agent should handle
3. Routes to the appropriate agent (Genesis, Vision, Logic, etc.)
4. Handles escalations from Master agents via SwarmBus
5. Collects responses and synthesizes if needed
6. Emits the final response packet

LangGraph enables:
- Stateful multi-turn conversations
- Conditional routing based on intent
- Parallel execution of multiple agents
- Human-in-the-loop when needed
"""

from typing import TypedDict, Annotated, Literal, Optional, Any, Sequence
from datetime import datetime
import operator
import logging
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    PacketPriority,
    MessageType,
    EscalationReason,
    AgentHierarchyTier,
    create_packet,
    create_alert_packet,
)
from core.config import settings, HRMConfig
from core.hrm import HierarchicalReasoningModel
from core.swarm_bus import SwarmBus, SwarmEnvelope, AgentTier, get_bus

logger = logging.getLogger(__name__)

# =============================================================================
# STATE DEFINITIONS
# =============================================================================

class OrchestratorState(TypedDict):
    """
    The shared state passed through all nodes in the Orchestrator graph.
    
    This state accumulates information as it flows through the system:
    - messages: The conversation history
    - packets: All SovereignPackets emitted during this turn
    - current_intent: What the user is trying to do
    - active_agent: Which sub-agent is currently handling
    - session_id: The user's session identifier
    - user_profile: Accumulated knowledge about the user
    - pending_probes: Unanswered questions awaiting user response
    - hrm_config: Configuration for deep reasoning
    - escalations: Pending escalations from Master agents
    - bus_events: Events received from the SwarmBus
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    packets: Annotated[list[dict], operator.add]
    current_intent: Optional[str]
    active_agent: Optional[str]
    session_id: str
    user_profile: dict[str, Any]
    pending_probes: list[dict]
    hrm_config: Optional[dict]
    conversation_turn: int
    escalations: list[dict]
    bus_events: list[dict]


class IntentClassification(BaseModel):
    """The result of intent analysis."""
    intent: Literal[
        "profiling",      # User is going through Genesis profiling
        "question",       # User is asking a question
        "food_analysis",  # User wants to analyze food/nutrition
        "reflection",     # User is sharing thoughts/feelings
        "command",        # User is giving a specific command
        "continuation",   # User is continuing previous conversation
        "unknown",        # Can't determine intent
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    target_agent: str  # Which agent should handle this
    reasoning: str


# =============================================================================
# ORCHESTRATOR NODE FUNCTIONS
# =============================================================================

async def intake_node(state: OrchestratorState) -> dict:
    """
    The Intake Node - First stop for all incoming messages.
    
    Responsibilities:
    1. Extract the user's message from state
    2. Log the incoming request
    3. Prepare context for intent analysis
    """
    logger.info(f"[Orchestrator:Intake] Processing turn {state['conversation_turn']}")
    
    # Get the latest message
    messages = state.get('messages', [])
    if not messages:
        logger.warning("[Orchestrator:Intake] No messages in state")
        return {}
    
    latest_message = messages[-1]
    logger.debug(f"[Orchestrator:Intake] Message: {latest_message.content[:100]}...")
    
    return {
        "conversation_turn": state.get('conversation_turn', 0) + 1,
    }


async def router_node(state: OrchestratorState) -> dict:
    """
    The Router Node - The Brain's decision maker.
    
    Analyzes the user's message and determines:
    1. What is the user's intent?
    2. Which sub-agent should handle this?
    3. Does this need HRM deep reasoning?
    
    Uses a lightweight LLM call for intent classification.
    """
    logger.info("[Orchestrator:Router] Analyzing intent...")
    
    messages = state.get('messages', [])
    if not messages:
        return {"current_intent": "unknown", "active_agent": "genesis"}
    
    latest_message = messages[-1]
    user_profile = state.get('user_profile', {})
    pending_probes = state.get('pending_probes', [])
    
    # Check if we're in an active profiling session
    if pending_probes:
        # User is responding to a probe
        logger.info("[Orchestrator:Router] Detected probe response")
        return {
            "current_intent": "profiling",
            "active_agent": "genesis.hypothesis",
        }
    
    # Check user profile state
    profile_complete = user_profile.get('profile_complete', False)
    current_phase = user_profile.get('phase', 'awakening')
    
    if not profile_complete and current_phase in ['awakening', 'excavation', 'mapping', 'synthesis', 'activation']:
        # Still in profiling flow
        logger.info(f"[Orchestrator:Router] Continuing profiling in phase: {current_phase}")
        return {
            "current_intent": "profiling",
            "active_agent": "genesis.core",
        }
    
    # Intent analysis for general messages
    intent_prompt = f"""Analyze the user's message and determine their intent.

User Message: "{latest_message.content}"

User Profile State:
- Profile Complete: {profile_complete}
- Current Phase: {current_phase}
- Known Traits: {list(user_profile.get('traits', {}).keys())}

Available Agents:
- genesis.core: Initial profiling and onboarding
- genesis.profiler: Archetype detection and analysis
- genesis.hypothesis: Probe generation for trait verification
- vision.analyzer: Image and food analysis
- logic.hrm: Deep reasoning and synthesis

Respond with JSON:
{{
    "intent": "profiling|question|food_analysis|reflection|command|continuation|unknown",
    "confidence": 0.0-1.0,
    "target_agent": "agent.name",
    "reasoning": "Brief explanation"
}}"""

    # Use fast model for intent classification
    try:
        model = ChatGoogleGenerativeAI(
            model=settings.FAST_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
        )
        
        response = await model.ainvoke([
            SystemMessage(content="You are an intent classifier. Respond only with valid JSON."),
            HumanMessage(content=intent_prompt),
        ])
        
        # Parse the response
        import json
        intent_data = json.loads(response.content)
        classification = IntentClassification(**intent_data)
        
        logger.info(f"[Orchestrator:Router] Intent: {classification.intent} -> {classification.target_agent}")
        
        return {
            "current_intent": classification.intent,
            "active_agent": classification.target_agent,
        }
        
    except Exception as e:
        logger.error(f"[Orchestrator:Router] Intent classification failed: {e}")
        # Default to Genesis for safety
        return {
            "current_intent": "continuation",
            "active_agent": "genesis.core",
        }


async def dispatch_node(state: OrchestratorState) -> dict:
    """
    The Dispatch Node - Routes to the appropriate sub-agent.
    
    Based on active_agent, this node:
    1. Prepares the context for the target agent
    2. Invokes the agent's workflow
    3. Collects the emitted packets
    """
    active_agent = state.get('active_agent', 'genesis.core')
    logger.info(f"[Orchestrator:Dispatch] Routing to: {active_agent}")
    
    # Import agents dynamically to avoid circular imports
    from agents.genesis.graph import GenesisGraph
    
    packets = []
    
    try:
        if active_agent.startswith('genesis'):
            # Route to Genesis subsystem
            genesis = GenesisGraph()
            result = await genesis.invoke({
                'messages': state['messages'],
                'session_id': state['session_id'],
                'user_profile': state['user_profile'],
                'pending_probes': state['pending_probes'],
                'hrm_config': state.get('hrm_config'),
                'sub_agent': active_agent.split('.')[-1] if '.' in active_agent else 'core',
            })
            
            packets.extend(result.get('packets', []))
            
            # Update user profile with any new information
            if result.get('user_profile'):
                state['user_profile'].update(result['user_profile'])
            
            # Update pending probes
            if result.get('pending_probes'):
                state['pending_probes'] = result['pending_probes']
                
        elif active_agent.startswith('vision'):
            # Route to Vision subsystem (placeholder)
            packet = create_alert_packet(
                source_agent="orchestrator",
                alert_type="info",
                title="Vision Module",
                message="The vision module is coming soon. For now, describe what you see.",
                session_id=state['session_id'],
            )
            packets.append(packet.as_dict())
            
        elif active_agent.startswith('logic'):
            # Route to HRM Logic Engine
            hrm_config = HRMConfig(**(state.get('hrm_config') or {}))
            hrm = HierarchicalReasoningModel(config=hrm_config)
            
            # Process through HRM
            reasoning_result = await hrm.reason(
                query=state['messages'][-1].content if state['messages'] else "",
                context=state['user_profile'],
            )
            
            packet = create_packet(
                source_agent="logic.hrm",
                insight_type=InsightType.SYNTHESIS,
                payload={
                    "reasoning": reasoning_result.get('reasoning', ''),
                    "conclusion": reasoning_result.get('conclusion', ''),
                    "confidence": reasoning_result.get('confidence', 0.5),
                },
                confidence=reasoning_result.get('confidence', 0.5),
                session_id=state['session_id'],
            )
            packets.append(packet.as_dict())
            
        else:
            # Unknown agent - default response
            logger.warning(f"[Orchestrator:Dispatch] Unknown agent: {active_agent}")
            packet = create_packet(
                source_agent="orchestrator",
                insight_type=InsightType.ALERT,
                payload={
                    "alert_type": "warning",
                    "message": f"Agent '{active_agent}' is not yet implemented.",
                },
                confidence=1.0,
                session_id=state['session_id'],
            )
            packets.append(packet.as_dict())
            
    except Exception as e:
        logger.error(f"[Orchestrator:Dispatch] Error dispatching to {active_agent}: {e}")
        packet = create_alert_packet(
            source_agent="orchestrator",
            alert_type="error",
            title="Dispatch Error",
            message=f"Failed to route to {active_agent}: {str(e)}",
            session_id=state['session_id'],
        )
        packets.append(packet.as_dict())
    
    return {"packets": packets}


async def synthesize_node(state: OrchestratorState) -> dict:
    """
    The Synthesize Node - Combines insights from multiple agents.
    
    If multiple agents contributed to this turn, this node:
    1. Collects all emitted packets
    2. Identifies patterns and contradictions
    3. Creates a unified synthesis packet
    4. Prepares the final response for the user
    """
    packets = state.get('packets', [])
    
    if len(packets) <= 1:
        # Single agent response, no synthesis needed
        return {}
    
    logger.info(f"[Orchestrator:Synthesize] Combining {len(packets)} packets")
    
    # Extract insights from packets
    insights = []
    frameworks_used = set()
    source_agents = set()
    
    for packet in packets:
        source_agents.add(packet.get('source_agent', 'unknown'))
        if packet.get('frameworks'):
            frameworks_used.update(packet['frameworks'])
        if packet.get('insight_type') in ['Pattern', 'Hypothesis', 'Fact']:
            insights.append(packet.get('payload', {}))
    
    if not insights:
        return {}
    
    # Create synthesis packet
    synthesis_packet = create_packet(
        source_agent="orchestrator.synthesizer",
        insight_type=InsightType.SYNTHESIS,
        payload={
            "title": "Multi-Agent Synthesis",
            "summary": f"Combined insights from {len(source_agents)} agents",
            "source_agents": list(source_agents),
            "frameworks_used": list(frameworks_used),
            "key_findings": [str(i) for i in insights[:5]],  # Top 5 insights
            "packet_count": len(packets),
        },
        confidence=0.85,
        session_id=state['session_id'],
    )
    
    return {"packets": [synthesis_packet.as_dict()]}


def should_synthesize(state: OrchestratorState) -> str:
    """Determine if we need to run the synthesis node."""
    packets = state.get('packets', [])
    
    # Synthesize if we have multiple packets from different agents
    if len(packets) > 1:
        agents = set(p.get('source_agent', '') for p in packets)
        if len(agents) > 1:
            return "synthesize"
    
    return "end"


# =============================================================================
# THE ORCHESTRATOR GRAPH
# =============================================================================

class Orchestrator:
    """
    The Sovereign Orchestrator - Central coordinator for all agent interactions.
    
    Enhanced with SwarmBus integration for:
    - Real-time inter-agent communication
    - Escalation handling from Master agents
    - Cross-domain coordination
    - Event-driven architecture
    
    Usage:
        orchestrator = Orchestrator()
        await orchestrator.start()  # Initialize SwarmBus connection
        result = await orchestrator.invoke({
            "messages": [HumanMessage(content="Tell me about myself")],
            "session_id": "user_123",
            "user_profile": {},
        })
    """
    
    AGENT_ID = "orchestrator"
    AGENT_TIER = AgentTier.ORCHESTRATOR
    
    def __init__(self, hrm_config: Optional[HRMConfig] = None):
        self.hrm_config = hrm_config
        self.graph = self._build_graph()
        self.compiled = self.graph.compile()
        
        # SwarmBus integration
        self._bus: Optional[SwarmBus] = None
        self._running = False
        self._escalation_queue: asyncio.Queue = asyncio.Queue()
        
        # Master agents
        self._master_hypothesis = None
        self._master_scout = None
        
        # Statistics
        self._stats = {
            "messages_processed": 0,
            "escalations_handled": 0,
            "cross_domain_requests": 0,
        }
    
    async def start(self) -> None:
        """Start the Orchestrator and connect to SwarmBus."""
        if self._running:
            return
        
        # Initialize SwarmBus
        self._bus = await get_bus()
        
        # Subscribe to receive escalations and cross-domain requests
        await self._bus.subscribe(
            agent_id=self.AGENT_ID,
            handler=self._handle_bus_envelope,
            agent_tier=self.AGENT_TIER,
            domain="orchestrator",
            capability="routing",
        )
        
        # Initialize Master agents
        from agents.master_hypothesis_engine import get_master_hypothesis_engine
        from agents.master_scout import get_master_scout
        
        self._master_hypothesis = await get_master_hypothesis_engine()
        self._master_scout = await get_master_scout()
        
        self._running = True
        logger.info(f"[{self.AGENT_ID}] Started with SwarmBus integration")
    
    async def stop(self) -> None:
        """Stop the Orchestrator and disconnect from SwarmBus."""
        if not self._running:
            return
        
        if self._bus:
            await self._bus.unsubscribe(self.AGENT_ID)
        
        if self._master_hypothesis:
            await self._master_hypothesis.stop()
        
        if self._master_scout:
            await self._master_scout.stop()
        
        self._running = False
        logger.info(f"[{self.AGENT_ID}] Stopped")
    
    async def _handle_bus_envelope(self, envelope: SwarmEnvelope) -> Optional[dict]:
        """Handle incoming envelopes from the SwarmBus."""
        logger.info(f"[{self.AGENT_ID}] Received envelope: {envelope.id}")
        
        # Check if it's an escalation
        if envelope.routing_pattern.value == "escalation":
            return await self._handle_escalation(envelope)
        
        # Check if it's a cross-domain request
        packet = envelope.packet
        if packet and packet.message_type == MessageType.REQUEST:
            return await self._handle_cross_domain_request(envelope)
        
        # Queue for later processing
        await self._escalation_queue.put(envelope.to_dict())
        
        return {"status": "queued"}
    
    async def _handle_escalation(self, envelope: SwarmEnvelope) -> dict:
        """Handle an escalation from a Master agent."""
        self._stats["escalations_handled"] += 1
        
        packet = envelope.packet
        reason = packet.escalation_reason if packet else EscalationReason.STUCK
        
        logger.info(f"[{self.AGENT_ID}] Handling escalation: {reason}")
        
        # Determine appropriate response
        if reason == EscalationReason.NEED_DECISION:
            # The Orchestrator makes the decision
            return await self._make_decision(envelope)
        
        elif reason == EscalationReason.CONFLICT:
            # Route to HRM for deep reasoning
            return await self._resolve_conflict_with_hrm(envelope)
        
        elif reason == EscalationReason.STUCK:
            # Try alternative approaches
            return await self._try_alternative_approach(envelope)
        
        else:
            # Log and acknowledge
            return {
                "status": "acknowledged",
                "action": "logged_for_review",
            }
    
    async def _handle_cross_domain_request(self, envelope: SwarmEnvelope) -> dict:
        """Handle a cross-domain request between sibling domains."""
        self._stats["cross_domain_requests"] += 1
        
        packet = envelope.packet
        if not packet:
            return {"status": "error", "message": "No packet"}
        
        source_domain = packet.source_domain
        target_domain = packet.target_domain
        
        logger.info(f"[{self.AGENT_ID}] Cross-domain: {source_domain} → {target_domain}")
        
        # Route to the target domain via SwarmBus
        if self._bus:
            await self._bus.send(
                source_agent_id=self.AGENT_ID,
                target_domain=target_domain,
                payload=packet.payload,
                priority=packet.priority,
                expects_response=packet.expects_response,
                correlation_id=packet.correlation_id,
            )
        
        return {"status": "routed", "target": target_domain}
    
    async def _make_decision(self, envelope: SwarmEnvelope) -> dict:
        """Make a decision that Master agents couldn't."""
        # Use HRM for deep reasoning on the decision
        packet = envelope.packet
        if not packet:
            return {"status": "error", "message": "No packet"}
        
        hrm_config = HRMConfig(thinking_level="high")
        hrm = HierarchicalReasoningModel(config=hrm_config)
        
        decision_context = {
            "options": packet.payload.get("options", []),
            "context": packet.payload.get("current_state", {}),
            "requesting_agent": envelope.source_agent_id,
        }
        
        result = await hrm.reason(
            query=f"Make a decision: {packet.payload.get('description', '')}",
            context=decision_context,
        )
        
        return {
            "status": "decided",
            "decision": result.get("conclusion", ""),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", ""),
        }
    
    async def _resolve_conflict_with_hrm(self, envelope: SwarmEnvelope) -> dict:
        """Use HRM to resolve a conflict."""
        packet = envelope.packet
        if not packet:
            return {"status": "error", "message": "No packet"}
        
        hrm_config = HRMConfig(thinking_level="high")
        hrm = HierarchicalReasoningModel(config=hrm_config)
        
        conflict_data = packet.payload.get("conflict", {})
        
        result = await hrm.reason(
            query=f"Resolve this conflict: {conflict_data}",
            context={"source_agent": envelope.source_agent_id},
        )
        
        return {
            "status": "resolved",
            "resolution": result.get("conclusion", ""),
            "confidence": result.get("confidence", 0.5),
        }
    
    async def _try_alternative_approach(self, envelope: SwarmEnvelope) -> dict:
        """Try alternative approaches when an agent is stuck."""
        # Broadcast to all domains asking for help
        if self._bus:
            await self._bus.broadcast(
                source_agent_id=self.AGENT_ID,
                payload={
                    "request_type": "help_needed",
                    "original_request": envelope.payload,
                    "stuck_agent": envelope.source_agent_id,
                },
                priority=PacketPriority.HIGH,
            )
        
        return {
            "status": "help_requested",
            "broadcast_sent": True,
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for the Orchestrator."""
        
        # Create the graph
        graph = StateGraph(OrchestratorState)
        
        # Add nodes
        graph.add_node("intake", intake_node)
        graph.add_node("router", router_node)
        graph.add_node("dispatch", dispatch_node)
        graph.add_node("synthesize", synthesize_node)
        
        # Define the flow
        graph.set_entry_point("intake")
        graph.add_edge("intake", "router")
        graph.add_edge("router", "dispatch")
        
        # Conditional edge for synthesis
        graph.add_conditional_edges(
            "dispatch",
            should_synthesize,
            {
                "synthesize": "synthesize",
                "end": END,
            }
        )
        graph.add_edge("synthesize", END)
        
        return graph
    
    async def invoke(
        self,
        messages: list[BaseMessage],
        session_id: str,
        user_profile: Optional[dict] = None,
        hrm_config: Optional[dict] = None,
    ) -> dict:
        """
        Process a message through the Orchestrator.
        
        Args:
            messages: The conversation history
            session_id: The user's session ID
            user_profile: Known information about the user
            hrm_config: Configuration for HRM reasoning
            
        Returns:
            dict with:
            - packets: List of SovereignPackets emitted
            - user_profile: Updated user profile
            - response: The final response text (extracted from packets)
        """
        initial_state: OrchestratorState = {
            "messages": messages,
            "packets": [],
            "current_intent": None,
            "active_agent": None,
            "session_id": session_id,
            "user_profile": user_profile or {},
            "pending_probes": [],
            "hrm_config": hrm_config,
            "conversation_turn": 0,
            "escalations": [],
            "bus_events": [],
        }
        
        try:
            # Ensure we're connected to SwarmBus
            if not self._running:
                await self.start()
            
            self._stats["messages_processed"] += 1
            
            result = await self.compiled.ainvoke(initial_state)
            
            # Extract response from packets
            response_text = ""
            for packet in result.get('packets', []):
                if packet.get('insight_type') == 'Question':
                    payload = packet.get('payload', {})
                    response_text = payload.get('prompt', '')
                    break
                elif packet.get('payload', {}).get('message'):
                    response_text = packet['payload']['message']
                    break
            
            return {
                "packets": result.get('packets', []),
                "user_profile": result.get('user_profile', {}),
                "response": response_text,
                "intent": result.get('current_intent'),
                "active_agent": result.get('active_agent'),
            }
            
        except Exception as e:
            logger.error(f"[Orchestrator] Invocation failed: {e}")
            error_packet = create_alert_packet(
                source_agent="orchestrator",
                alert_type="error",
                title="Orchestrator Error",
                message=str(e),
                session_id=session_id,
            )
            return {
                "packets": [error_packet.as_dict()],
                "user_profile": user_profile or {},
                "response": f"I encountered an error: {str(e)}",
                "intent": "error",
                "active_agent": None,
            }
    
    async def stream(
        self,
        messages: list[BaseMessage],
        session_id: str,
        user_profile: Optional[dict] = None,
        hrm_config: Optional[dict] = None,
    ):
        """
        Stream the Orchestrator's processing, yielding packets as they're emitted.
        
        Useful for real-time UI updates.
        """
        # Ensure we're connected to SwarmBus
        if not self._running:
            await self.start()
        
        initial_state: OrchestratorState = {
            "messages": messages,
            "packets": [],
            "current_intent": None,
            "active_agent": None,
            "session_id": session_id,
            "user_profile": user_profile or {},
            "pending_probes": [],
            "hrm_config": hrm_config,
            "conversation_turn": 0,
            "escalations": [],
            "bus_events": [],
        }
        
        async for event in self.compiled.astream(initial_state):
            # Yield any new packets
            for node_name, node_state in event.items():
                if isinstance(node_state, dict) and 'packets' in node_state:
                    for packet in node_state['packets']:
                        yield {
                            "type": "packet",
                            "node": node_name,
                            "packet": packet,
                        }
            
            # Yield state updates
            yield {
                "type": "state",
                "event": event,
            }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def process_message(
    message: str,
    session_id: str,
    user_profile: Optional[dict] = None,
    hrm_config: Optional[dict] = None,
    history: Optional[list[BaseMessage]] = None,
) -> dict:
    """
    Convenience function to process a single message through the Orchestrator.
    
    Args:
        message: The user's message
        session_id: Session identifier
        user_profile: Known user information
        hrm_config: HRM configuration
        history: Previous conversation messages
        
    Returns:
        The Orchestrator's response
    """
    messages = list(history) if history else []
    messages.append(HumanMessage(content=message))
    
    orchestrator = Orchestrator()
    await orchestrator.start()  # Initialize SwarmBus connection
    
    try:
        return await orchestrator.invoke(
            messages=messages,
            session_id=session_id,
            user_profile=user_profile,
            hrm_config=hrm_config,
        )
    finally:
        await orchestrator.stop()  # Clean up


# =============================================================================
# SWARM STATUS API
# =============================================================================

async def get_swarm_status() -> dict:
    """Get the status of the entire swarm including all Master agents."""
    from agents.master_hypothesis_engine import get_master_hypothesis_engine
    from agents.master_scout import get_master_scout
    
    bus = await get_bus()
    hypothesis_engine = await get_master_hypothesis_engine()
    scout = await get_master_scout()
    
    return {
        "swarm_bus": bus.get_stats(),
        "master_hypothesis_engine": hypothesis_engine.get_status(),
        "master_scout": scout.get_status(),
    }


# =============================================================================
# SINGLETON ORCHESTRATOR
# =============================================================================

_orchestrator_instance: Optional[Orchestrator] = None


async def get_orchestrator(hrm_config: Optional[HRMConfig] = None) -> Orchestrator:
    """
    Get the singleton Orchestrator instance.
    
    The Orchestrator is expensive to create and should be reused.
    This factory function ensures only one instance exists.
    
    Args:
        hrm_config: Optional HRM configuration (used only on first call)
        
    Returns:
        The singleton Orchestrator instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator(hrm_config=hrm_config)
        await _orchestrator_instance.start()
        logger.info("[Orchestrator] Singleton instance created and started")
    return _orchestrator_instance


async def shutdown_orchestrator() -> None:
    """
    Shutdown the singleton Orchestrator instance.
    
    Should be called during application shutdown.
    """
    global _orchestrator_instance
    if _orchestrator_instance is not None:
        await _orchestrator_instance.stop()
        _orchestrator_instance = None
        logger.info("[Orchestrator] Singleton instance shutdown")
