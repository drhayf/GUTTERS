"""
Sovereign Integrations - Deep System Connections

This module provides the REAL connections from the Sovereign Agent to ALL
system components. This is the nervous system that makes the Sovereign Agent
truly omniscient.

Integration Points:
━━━━━━━━━━━━━━━━━━━━

1. HRM (Hierarchical Reasoning Model)
   - Deep reasoning for complex queries
   - Multi-step reasoning chains
   - Hypothesis verification

2. LLM Factory
   - Multi-model orchestration
   - Model selection by task type
   - Fallback handling

3. SwarmBus
   - Agent discovery and communication
   - Message passing to all agents
   - Parallel execution

4. Genesis System
   - Session management
   - Digital Twin access
   - Profiling state

5. Master Agents
   - MasterHypothesisEngine - hypothesis coordination
   - MasterScout - profile aggregation

6. Orchestrator
   - Complex routing decisions
   - Multi-agent coordination

@module SovereignIntegrations
"""

from typing import Optional, Any, Dict, List, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4
import logging
import asyncio

from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    AgentCapability,
    PacketPriority,
    AgentHierarchyTier,
    create_packet,
)
from ...core.config import settings
from ...core.hrm import get_hrm, HierarchicalReasoningModel, ReasoningState
from ...core.llm_factory import LLMFactory, get_llm_factory
from ...core.swarm_bus import SwarmBus, SwarmEnvelope, get_bus, AgentTier, RoutingPattern
from ...core.orchestrator import Orchestrator, get_orchestrator

logger = logging.getLogger(__name__)


# =============================================================================
# HRM INTEGRATION
# =============================================================================

class HRMIntegration:
    """
    Integration with the Hierarchical Reasoning Model.
    
    Provides deep reasoning capabilities:
    - Multi-step reasoning chains
    - Hypothesis generation and verification
    - Confidence scoring
    - Reasoning traces
    """
    
    def __init__(self):
        self._hrm = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize HRM connection."""
        if self._initialized:
            return
        
        self._hrm = get_hrm()
        self._initialized = True
        logger.info("[HRMIntegration] Connected to HRM")
    
    @property
    def enabled(self) -> bool:
        """Check if HRM is enabled."""
        return self._hrm is not None and self._hrm.enabled
    
    async def deep_reason(
        self,
        query: str,
        context: Dict[str, Any],
        thinking_level: str = "high",
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform deep reasoning on a query.
        
        Args:
            query: The question or problem to reason about
            context: Relevant context (Digital Twin, module data, etc.)
            thinking_level: "low" for quick, "high" for thorough
            max_depth: Maximum reasoning depth
        
        Returns:
            Dict with:
            - conclusion: The reasoned answer
            - confidence: 0.0-1.0 confidence score
            - reasoning_trace: List of reasoning steps
            - hypotheses: Any generated hypotheses
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.enabled:
            logger.warning("[HRMIntegration] HRM not enabled, using direct response")
            return {
                "conclusion": None,
                "confidence": 0.0,
                "reasoning_trace": [],
                "hypotheses": [],
                "hrm_used": False,
            }
        
        try:
            # Build config override from parameters
            config_override = {}
            if thinking_level:
                config_override["thinking_level"] = thinking_level
            if max_depth:
                config_override["max_reasoning_depth"] = max_depth
            
            # Run HRM with query and optional overrides
            result = await self._hrm.reason(
                query=query,
                max_depth=max_depth,
                config_override=config_override if config_override else None,
            )
            
            return {
                "conclusion": result.get("answer"),
                "confidence": result.get("confidence", 0.0) if "confidence" in result else (1.0 if result.get("hrm_validated") else 0.5),
                "reasoning_trace": result.get("reasoning_trace", []),
                "hypotheses": result.get("hypotheses", []),
                "processing_time_ms": int((result.get("processing_time", 0)) * 1000) if "processing_time" in result else None,
                "hrm_used": result.get("hrm_validated", False),
                "depth": result.get("depth", 0),
            }
            
        except Exception as e:
            logger.error(f"[HRMIntegration] Reasoning error: {e}")
            return {
                "conclusion": None,
                "confidence": 0.0,
                "reasoning_trace": [],
                "hypotheses": [],
                "error": str(e),
                "hrm_used": False,
            }
    
    async def verify_hypothesis(
        self,
        hypothesis: str,
        evidence: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify a hypothesis against evidence.
        
        Args:
            hypothesis: The hypothesis to verify
            evidence: List of evidence statements
            context: Additional context
        
        Returns:
            Dict with verification result, confidence, reasoning
        """
        if not self.enabled:
            return {"verified": None, "confidence": 0.0, "reason": "HRM not enabled"}
        
        query = f"""
        Hypothesis: {hypothesis}
        
        Evidence:
        {chr(10).join(f'- {e}' for e in evidence)}
        
        Determine if the hypothesis is supported, refuted, or inconclusive based on the evidence.
        """
        
        result = await self.deep_reason(query, context, thinking_level="high")
        
        # Parse conclusion
        conclusion = result.get("conclusion", "").lower()
        verified = None
        if "supported" in conclusion or "confirmed" in conclusion:
            verified = True
        elif "refuted" in conclusion or "rejected" in conclusion:
            verified = False
        
        return {
            "verified": verified,
            "confidence": result.get("confidence", 0.0),
            "reason": result.get("conclusion"),
            "reasoning_trace": result.get("reasoning_trace", []),
        }


# =============================================================================
# LLM FACTORY INTEGRATION
# =============================================================================

class LLMFactoryIntegration:
    """
    Integration with the LLM Factory for multi-model orchestration.
    
    Provides:
    - Model selection by task type
    - Automatic fallback
    - Cost optimization
    - Capability routing
    """
    
    def __init__(self):
        self._factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize LLM Factory connection."""
        if self._initialized:
            return
        
        self._factory = get_llm_factory()
        self._initialized = True
        logger.info("[LLMFactoryIntegration] Connected to LLM Factory")
    
    def get_model_for_task(self, task_type: str) -> str:
        """
        Get the best model for a task type.
        
        Task types:
        - "conversation": General chat (fast model)
        - "reasoning": Complex reasoning (primary model)
        - "synthesis": Cross-domain synthesis (synthesis model)
        - "pattern_detection": Quick pattern analysis (fast model)
        - "generation": Creative generation (primary model)
        """
        if not self._factory:
            return settings.PRIMARY_MODEL
        
        task_model_map = {
            "conversation": self._factory.fast_model,
            "reasoning": self._factory.primary_model,
            "synthesis": self._factory.synthesis_model,
            "pattern_detection": self._factory.fast_model,
            "generation": self._factory.primary_model,
        }
        
        return task_model_map.get(task_type, self._factory.primary_model)
    
    async def get_llm(
        self,
        task_type: str = "conversation",
        temperature: float = 0.7,
        override_model: Optional[str] = None,
    ):
        """
        Get an LLM instance for a task.
        
        Args:
            task_type: Type of task (determines model selection)
            temperature: Generation temperature
            override_model: Optional specific model override
        
        Returns:
            LLM instance ready for use
        """
        if not self._initialized:
            await self.initialize()
        
        model = override_model or self.get_model_for_task(task_type)
        
        return self._factory.get_llm(
            model=model,
            temperature=temperature,
        )
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models by provider."""
        if not self._factory:
            return {}
        return self._factory.get_available_models()


# =============================================================================
# SWARM BUS INTEGRATION
# =============================================================================

class SwarmBusIntegration:
    """
    Integration with the SwarmBus for agent communication.
    
    Provides:
    - Direct agent messaging
    - Broadcast messaging
    - Collect pattern (gather from multiple)
    - Escalation handling
    - Event subscription
    """
    
    def __init__(self):
        self._bus: Optional[SwarmBus] = None
        self._initialized = False
        self._handlers: Dict[str, Callable] = {}
    
    async def initialize(self) -> None:
        """Initialize SwarmBus connection."""
        if self._initialized:
            return
        
        self._bus = await get_bus()
        
        # Subscribe Sovereign to receive messages
        # Note: Sovereign is the omniscient agent, so we subscribe with a general capability
        await self._bus.subscribe(
            agent_id="sovereign.agent",
            handler=self._handle_message,
            agent_tier=AgentTier.ORCHESTRATOR,
            domain="sovereign",
            capability="omniscient",  # Single capability - Sovereign can do everything
        )
        
        self._initialized = True
        logger.info("[SwarmBusIntegration] Subscribed to SwarmBus")
    
    async def _handle_message(self, envelope: SwarmEnvelope) -> Optional[Dict[str, Any]]:
        """Handle incoming messages to the Sovereign Agent."""
        logger.info(f"[SwarmBus] Received message: {envelope.packet_type}")
        
        # Check if we have a registered handler
        handler = self._handlers.get(envelope.packet_type)
        if handler:
            return await handler(envelope)
        
        return None
    
    def register_handler(self, packet_type: str, handler: Callable) -> None:
        """Register a handler for a specific packet type."""
        self._handlers[packet_type] = handler
    
    async def send_to_agent(
        self,
        target_agent: str,
        payload: Dict[str, Any],
        expects_response: bool = True,
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to a specific agent.
        
        Args:
            target_agent: Agent ID (e.g., "genesis.profiler")
            payload: Message payload
            expects_response: Whether to wait for response
            timeout: Response timeout in seconds
        
        Returns:
            Response from the agent, or None if fire-and-forget
        """
        if not self._initialized:
            await self.initialize()
        
        envelope = self._bus.create_envelope(
            source_agent_id="sovereign.agent",
            target_agent_id=target_agent,
            payload=payload,
            expects_response=expects_response,
            routing_pattern=RoutingPattern.DIRECT,
        )
        
        if expects_response:
            return await self._bus.send_and_wait(envelope, timeout=timeout)
        else:
            await self._bus.send(envelope)
            return None
    
    async def send_to_capability(
        self,
        capability: AgentCapability,
        payload: Dict[str, Any],
        expects_response: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to an agent with a specific capability.
        
        The SwarmBus will find the best agent with that capability.
        """
        if not self._initialized:
            await self.initialize()
        
        envelope = self._bus.create_envelope(
            source_agent_id="sovereign.agent",
            target_capability=capability,
            payload=payload,
            expects_response=expects_response,
            routing_pattern=RoutingPattern.CAPABILITY,
        )
        
        if expects_response:
            return await self._bus.send_and_wait(envelope)
        else:
            await self._bus.send(envelope)
            return None
    
    async def broadcast_to_domain(
        self,
        domain: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all agents in a domain.
        
        Args:
            domain: Domain name (e.g., "genesis", "vision")
            payload: Message payload
        """
        if not self._initialized:
            await self.initialize()
        
        envelope = self._bus.create_envelope(
            source_agent_id="sovereign.agent",
            target_domain=domain,
            payload=payload,
            routing_pattern=RoutingPattern.BROADCAST,
        )
        
        await self._bus.broadcast(envelope)
    
    async def collect_from_domain(
        self,
        domain: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """
        Collect responses from all agents in a domain.
        
        Args:
            domain: Domain name
            payload: Query payload
            timeout: Collection timeout
        
        Returns:
            List of responses from all responding agents
        """
        if not self._initialized:
            await self.initialize()
        
        envelope = self._bus.create_envelope(
            source_agent_id="sovereign.agent",
            target_domain=domain,
            payload=payload,
            expects_response=True,
            routing_pattern=RoutingPattern.COLLECT,
        )
        
        return await self._bus.collect(envelope, timeout=timeout)
    
    async def escalate_to_master(
        self,
        master_agent: str,
        payload: Dict[str, Any],
        priority: PacketPriority = PacketPriority.HIGH,
    ) -> Optional[Dict[str, Any]]:
        """
        Escalate a complex task to a master agent.
        
        Master agents:
        - "master.hypothesis" - MasterHypothesisEngine
        - "master.scout" - MasterScout
        - "master.synthesis" - SynthesisEngine
        """
        if not self._initialized:
            await self.initialize()
        
        envelope = self._bus.create_envelope(
            source_agent_id="sovereign.agent",
            target_agent_id=master_agent,
            payload=payload,
            priority=priority,
            routing_pattern=RoutingPattern.ESCALATE,
            expects_response=True,
        )
        
        return await self._bus.send_and_wait(envelope)
    
    def get_registered_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents on the bus."""
        if not self._bus:
            return []
        
        # SwarmBus stores subscriptions by agent_id
        # Return list of agent info from the subscriptions
        agents = []
        for agent_id, subscription in self._bus._subscriptions.items():
            agents.append({
                "agent_id": agent_id,
                "tier": subscription.agent_tier.value if subscription.agent_tier else None,
                "domain": subscription.domain,
                "capability": subscription.capability,
            })
        return agents


# =============================================================================
# DIGITAL TWIN INTEGRATION (NEW - PRIMARY IDENTITY ACCESS)
# =============================================================================

class DigitalTwinIntegration:
    """
    Integration with the new Digital Twin system.
    
    This is the PRIMARY way the Sovereign Agent accesses identity data.
    Provides omniscient read/write access to:
    - All user traits across all domains
    - Real-time event notifications
    - Query capabilities
    - Identity management
    
    This replaces the legacy Digital Twin access through Genesis.
    """
    
    def __init__(self):
        self._twin_integration = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Digital Twin connection."""
        if self._initialized:
            return
        
        try:
            from ...digital_twin import (
                get_sovereign_twin_integration,
                SovereignDigitalTwinIntegration,
            )
            
            self._twin_integration = await get_sovereign_twin_integration()
            self._initialized = True
            logger.info("[DigitalTwinIntegration] Connected to Digital Twin (omniscient mode)")
        except Exception as e:
            logger.error(f"[DigitalTwinIntegration] Failed to initialize: {e}")
            self._initialized = True  # Prevent retry loops
    
    @property
    def ready(self) -> bool:
        """Check if Digital Twin is ready."""
        return self._twin_integration is not None
    
    async def get(self, path: str, default: Any = None) -> Any:
        """
        Get a trait value by path.
        
        Examples:
            hd_type = await integration.get("genesis.hd_type")
            energy = await integration.get("genesis.energy_pattern", "unknown")
        """
        if not self.ready:
            return default
        return await self._twin_integration.get(path, default)
    
    async def set(
        self,
        path: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "sovereign_agent"
    ) -> bool:
        """
        Set a trait value.
        
        Returns True if successful.
        """
        if not self.ready:
            return False
        
        try:
            await self._twin_integration.set(path, value, confidence, source=source)
            return True
        except Exception as e:
            logger.error(f"[DigitalTwinIntegration] Set failed: {e}")
            return False
    
    async def update_profile(self, updates: Dict[str, Any]) -> bool:
        """Batch update multiple traits."""
        if not self.ready:
            return False
        
        try:
            await self._twin_integration.update_profile(updates)
            return True
        except Exception as e:
            logger.error(f"[DigitalTwinIntegration] Batch update failed: {e}")
            return False
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get Digital Twin summary."""
        if not self.ready:
            return {}
        return await self._twin_integration.get_summary()
    
    async def export(self) -> Dict[str, Any]:
        """Export full Digital Twin."""
        if not self.ready:
            return {}
        return await self._twin_integration.export()
    
    async def query(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Query the Digital Twin.
        
        Kwargs:
            domain: Filter by domain
            category: Filter by category
            framework: Filter by framework
            min_confidence: Minimum confidence threshold
        """
        if not self.ready:
            return []
        
        return await self._twin_integration.find_traits(**kwargs)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current cached state."""
        if not self.ready:
            return {}
        
        state = self._twin_integration.get_state()
        return {
            "identity_id": state.identity.id if state.identity else None,
            "hd_type": state.hd_type,
            "jung_dominant": state.jung_dominant,
            "energy_pattern": state.energy_pattern,
            "profiling_phase": state.profiling_phase,
            "completion_percentage": state.completion_percentage,
            "trait_count": state.trait_count,
            "domains": state.domains,
        }
    
    def on_change(self, handler: Callable) -> None:
        """Register a handler for Digital Twin changes."""
        if self._twin_integration:
            self._twin_integration.on_change(handler)


# =============================================================================
# GENESIS INTEGRATION
# =============================================================================

class GenesisIntegration:
    """
    Integration with the Genesis profiling system.
    
    Provides:
    - Session state access
    - Digital Twin management
    - Profiling flow control
    - Hypothesis engine access
    """
    
    def __init__(self):
        self._session_manager = None
        self._profiler = None
        self._hypothesis_engine = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Genesis connections."""
        if self._initialized:
            return
        
        try:
            # Import here to avoid circular imports
            from ..genesis.session_manager import GenesisSessionManager
            from ..genesis.profiler import GenesisProfiler
            from ..genesis.hypothesis import HypothesisEngine
            
            self._session_manager = GenesisSessionManager()
            self._profiler = GenesisProfiler()
            self._hypothesis_engine = HypothesisEngine()
            
            self._initialized = True
            logger.info("[GenesisIntegration] Connected to Genesis")
        except ImportError as e:
            logger.warning(f"[GenesisIntegration] Could not import Genesis modules: {e}")
            self._initialized = True  # Mark as initialized to prevent retry loops
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a Genesis session by ID."""
        if not self._initialized:
            await self.initialize()
        
        if not self._session_manager:
            return None
        
        session = self._session_manager.get_session(session_id)
        if session:
            return session.to_dict()
        return None
    
    async def get_digital_twin(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the Digital Twin for a session."""
        if not self._initialized:
            await self.initialize()
        
        if not self._session_manager:
            return None
        
        session = self._session_manager.get_session(session_id)
        if session and session.digital_twin:
            return session.digital_twin.to_dict()
        return None
    
    async def get_active_hypotheses(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all active hypotheses for a session."""
        if not self._initialized:
            await self.initialize()
        
        if not self._hypothesis_engine:
            return []
        
        hypotheses = self._hypothesis_engine.get_active(session_id)
        return [h.to_dict() for h in hypotheses]
    
    async def add_hypothesis(
        self,
        session_id: str,
        trait: str,
        framework: str,
        confidence: float,
        evidence: List[str],
    ) -> Dict[str, Any]:
        """Add a new hypothesis to the session."""
        if not self._initialized:
            await self.initialize()
        
        if not self._hypothesis_engine:
            return {"success": False, "error": "Hypothesis engine not available"}
        
        hypothesis = self._hypothesis_engine.add(
            session_id=session_id,
            trait=trait,
            framework=framework,
            initial_confidence=confidence,
            evidence=evidence,
        )
        
        return {"success": True, "hypothesis": hypothesis.to_dict()}
    
    async def detect_patterns(
        self,
        message: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Use the profiler to detect patterns in a message."""
        if not self._initialized:
            await self.initialize()
        
        if not self._profiler:
            return []
        
        signals = await self._profiler.analyze(message, context)
        return [s.to_dict() for s in signals]
    
    async def get_profiling_phase(self, session_id: str) -> Optional[str]:
        """Get the current profiling phase for a session."""
        session = await self.get_session(session_id)
        if session:
            return session.get("phase")
        return None
    
    async def get_completion_percentage(self, session_id: str) -> float:
        """Get the profile completion percentage."""
        session = await self.get_session(session_id)
        if session:
            return session.get("completion_percentage", 0.0)
        return 0.0


# =============================================================================
# MASTER AGENTS INTEGRATION
# =============================================================================

class MasterAgentsIntegration:
    """
    Integration with Master-tier agents.
    
    Provides:
    - MasterHypothesisEngine: Cross-domain hypothesis correlation
    - MasterScout: Unified Digital Twin management
    - SynthesisEngine: Cross-module insight synthesis
    """
    
    def __init__(self):
        self._swarm: Optional[SwarmBusIntegration] = None
        self._initialized = False
    
    async def initialize(self, swarm: SwarmBusIntegration) -> None:
        """Initialize with SwarmBus reference."""
        self._swarm = swarm
        self._initialized = True
        logger.info("[MasterAgentsIntegration] Connected to Master Agents")
    
    async def correlate_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use MasterHypothesisEngine to correlate hypotheses across domains.
        
        Args:
            hypotheses: List of hypotheses from various sources
            context: User context (Digital Twin, etc.)
        
        Returns:
            Correlation analysis with patterns and recommendations
        """
        if not self._initialized or not self._swarm:
            return {"error": "Not initialized"}
        
        result = await self._swarm.escalate_to_master(
            master_agent="master.hypothesis",
            payload={
                "action": "correlate",
                "hypotheses": hypotheses,
                "context": context,
            },
        )
        
        return result or {"error": "No response from MasterHypothesisEngine"}
    
    async def aggregate_profile(
        self,
        session_id: str,
        sources: List[str],
    ) -> Dict[str, Any]:
        """
        Use MasterScout to aggregate profile data from multiple sources.
        
        Args:
            session_id: Session to aggregate for
            sources: List of source identifiers
        
        Returns:
            Aggregated profile data
        """
        if not self._initialized or not self._swarm:
            return {"error": "Not initialized"}
        
        result = await self._swarm.escalate_to_master(
            master_agent="master.scout",
            payload={
                "action": "aggregate",
                "session_id": session_id,
                "sources": sources,
            },
        )
        
        return result or {"error": "No response from MasterScout"}
    
    async def synthesize_insights(
        self,
        modules: List[str],
        data: Dict[str, Dict[str, Any]],
        question: str,
    ) -> Dict[str, Any]:
        """
        Use SynthesisEngine for cross-module insight synthesis.
        
        Args:
            modules: Modules to synthesize across
            data: Data from each module
            question: The synthesis question
        
        Returns:
            Synthesized insights and patterns
        """
        if not self._initialized or not self._swarm:
            return {"error": "Not initialized"}
        
        result = await self._swarm.escalate_to_master(
            master_agent="master.synthesis",
            payload={
                "action": "synthesize",
                "modules": modules,
                "data": data,
                "question": question,
            },
        )
        
        return result or {"error": "No response from SynthesisEngine"}


# =============================================================================
# ORCHESTRATOR INTEGRATION
# =============================================================================

class OrchestratorIntegration:
    """
    Integration with the main Orchestrator.
    
    The Orchestrator is the central routing brain. This integration
    allows the Sovereign Agent to:
    - Leverage orchestrator routing decisions
    - Access its state graph
    - Coordinate complex multi-agent workflows
    """
    
    def __init__(self):
        self._orchestrator = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Orchestrator connection."""
        if self._initialized:
            return
        
        self._orchestrator = await get_orchestrator()
        self._initialized = True
        logger.info("[OrchestratorIntegration] Connected to Orchestrator")
    
    async def route_request(
        self,
        request: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use the Orchestrator to route a complex request.
        
        Args:
            request: The request to route
            context: Current context
        
        Returns:
            Routing decision and result
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._orchestrator:
            return {"error": "Orchestrator not available"}
        
        return await self._orchestrator.invoke(
            user_message=request.get("message", ""),
            session_id=context.get("session_id"),
            context=context,
        )
    
    async def get_routing_suggestion(
        self,
        intent: str,
        capabilities_needed: List[AgentCapability],
    ) -> Dict[str, Any]:
        """
        Get a routing suggestion from the Orchestrator.
        
        Args:
            intent: The detected intent
            capabilities_needed: Required capabilities
        
        Returns:
            Suggested routing with agents and strategy
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._orchestrator:
            return {"error": "Orchestrator not available"}
        
        # Use invoke to get routing decision based on intent
        result = await self._orchestrator.invoke(
            user_message=intent,
            context={"capabilities_needed": [c.value for c in capabilities_needed]},
        )
        
        return {
            "intent": intent,
            "suggested_route": result.get("target_agent"),
            "reasoning": result.get("reasoning"),
        }


# =============================================================================
# UNIFIED INTEGRATION HUB
# =============================================================================

class SovereignIntegrations:
    """
    Unified integration hub for the Sovereign Agent.
    
    This is the single entry point for ALL system integrations.
    The Sovereign Agent uses this to access every part of the system.
    
    Usage:
        integrations = SovereignIntegrations()
        await integrations.initialize()
        
        # Use HRM for deep reasoning
        result = await integrations.hrm.deep_reason(query, context)
        
        # Send to an agent via SwarmBus
        response = await integrations.swarm.send_to_agent("genesis.profiler", payload)
        
        # Access Digital Twin (NEW - PRIMARY IDENTITY ACCESS)
        twin_state = integrations.digital_twin.get_state()
        hd_type = await integrations.digital_twin.get("genesis.hd_type")
        await integrations.digital_twin.set("genesis.energy_pattern", "sustainable")
        
        # Correlate with Master agents
        correlation = await integrations.masters.correlate_hypotheses(hypotheses, context)
    """
    
    def __init__(self):
        # Core integrations
        self.hrm = HRMIntegration()
        self.llm_factory = LLMFactoryIntegration()
        self.swarm = SwarmBusIntegration()
        
        # Digital Twin - PRIMARY identity access (NEW)
        self.digital_twin = DigitalTwinIntegration()
        
        # Domain integrations
        self.genesis = GenesisIntegration()
        self.masters = MasterAgentsIntegration()
        self.orchestrator = OrchestratorIntegration()
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all integrations."""
        if self._initialized:
            return
        
        logger.info("[SovereignIntegrations] Initializing all integrations...")
        
        # Initialize in dependency order
        await self.hrm.initialize()
        await self.llm_factory.initialize()
        await self.swarm.initialize()
        
        # Initialize Digital Twin (NEW - before Genesis)
        await self.digital_twin.initialize()
        
        await self.genesis.initialize()
        await self.masters.initialize(self.swarm)
        await self.orchestrator.initialize()
        
        self._initialized = True
        logger.info("[SovereignIntegrations] All integrations ready!")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        return {
            "hrm": {
                "initialized": self.hrm._initialized,
                "enabled": self.hrm.enabled,
            },
            "llm_factory": {
                "initialized": self.llm_factory._initialized,
            },
            "swarm": {
                "initialized": self.swarm._initialized,
                "agents_count": len(self.swarm.get_registered_agents()) if self.swarm._initialized else 0,
            },
            "digital_twin": {
                "initialized": self.digital_twin._initialized,
                "ready": self.digital_twin.ready,
                "state": self.digital_twin.get_state() if self.digital_twin.ready else None,
            },
            "genesis": {
                "initialized": self.genesis._initialized,
            },
            "masters": {
                "initialized": self.masters._initialized,
            },
            "orchestrator": {
                "initialized": self.orchestrator._initialized,
            },
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_integrations: Optional[SovereignIntegrations] = None


async def get_integrations() -> SovereignIntegrations:
    """Get the singleton integrations hub."""
    global _integrations
    
    if _integrations is None:
        _integrations = SovereignIntegrations()
        await _integrations.initialize()
    
    return _integrations
