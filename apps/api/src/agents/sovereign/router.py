"""
Sovereign Router - Agent Delegation & SwarmBus Integration

This module implements the "Nervous System" connections for the Sovereign Agent,
enabling it to:

1. DISCOVER - Find agents with specific capabilities
2. DELEGATE - Route specialized tasks to domain agents
3. COLLECT - Gather responses from multiple agents
4. ESCALATE - Handle complex cross-domain requests

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         ┌─────────────────────────┐
                         │    SOVEREIGN ROUTER     │
                         ├─────────────────────────┤
                         │                         │
                         │   ┌─────────────────┐  │
                         │   │  Agent Registry  │  │
                         │   │  • Discovery     │  │
                         │   │  • Capabilities  │  │
                         │   └───────┬─────────┘  │
                         │           │            │
                         │   ┌───────▼─────────┐  │
                         │   │    SwarmBus     │  │
                         │   │  • Direct Send  │  │
                         │   │  • Broadcast    │  │
                         │   │  • Collect      │  │
                         │   └───────┬─────────┘  │
                         │           │            │
                    ┌────┴───────────┴─────┐      │
                    ▼          ▼           ▼      │
              ┌─────────┐ ┌─────────┐ ┌─────────┐│
              │ Genesis │ │ Vision  │ │ Nutrition│
              └─────────┘ └─────────┘ └─────────┘│
                         │                         │
                         └─────────────────────────┘

@module SovereignRouter
"""

from typing import Optional, Any, Dict, List, Callable, Awaitable
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
    PacketPriority,
    AgentCapability,
    create_packet,
)
from ...core.swarm_bus import (
    SwarmBus,
    SwarmEnvelope,
    AgentTier,
    RoutingPattern,
    get_bus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DELEGATION TYPES
# =============================================================================

class DelegationType(str, Enum):
    """Type of delegation to another agent."""
    DIRECT = "direct"           # Single agent, single task
    PARALLEL = "parallel"       # Multiple agents, same task
    SEQUENTIAL = "sequential"   # Chain of agents
    COLLECT = "collect"         # Gather from multiple, synthesize


@dataclass
class DelegationRequest:
    """A request to delegate work to another agent."""
    id: str = field(default_factory=lambda: str(uuid4()))
    delegation_type: DelegationType = DelegationType.DIRECT
    
    # Target specification (one of these)
    target_agent: Optional[str] = None        # Specific agent ID
    target_capability: Optional[AgentCapability] = None  # Find by capability
    target_domain: Optional[str] = None       # All in domain
    
    # The task
    task_description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    
    # Execution settings
    priority: PacketPriority = PacketPriority.NORMAL
    timeout_seconds: int = 30
    expects_response: bool = True
    
    # Context to pass
    session_id: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DelegationResult:
    """Result of a delegation."""
    request_id: str
    success: bool
    
    # Single response
    response: Optional[Dict[str, Any]] = None
    
    # Multiple responses (for COLLECT)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    agent_id: Optional[str] = None
    agent_ids: List[str] = field(default_factory=list)
    execution_time_ms: float = 0
    
    # Error info
    error: Optional[str] = None


# =============================================================================
# AGENT REGISTRY
# =============================================================================

@dataclass
class RegisteredAgent:
    """Information about a registered agent."""
    agent_id: str
    tier: AgentTier
    domain: Optional[str]
    capabilities: List[AgentCapability]
    description: str = ""
    is_active: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)


class AgentDiscovery:
    """
    Agent discovery and registry service.
    
    Tracks all available agents and their capabilities for routing.
    """
    
    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self._by_capability: Dict[AgentCapability, List[str]] = {}
        self._by_domain: Dict[str, List[str]] = {}
    
    def register(self, agent: RegisteredAgent) -> None:
        """Register an agent."""
        self._agents[agent.agent_id] = agent
        
        # Index by capability
        for cap in agent.capabilities:
            if cap not in self._by_capability:
                self._by_capability[cap] = []
            self._by_capability[cap].append(agent.agent_id)
        
        # Index by domain
        if agent.domain:
            if agent.domain not in self._by_domain:
                self._by_domain[agent.domain] = []
            self._by_domain[agent.domain].append(agent.agent_id)
        
        logger.info(f"[AgentDiscovery] Registered: {agent.agent_id}")
    
    def find_by_capability(self, capability: AgentCapability) -> List[RegisteredAgent]:
        """Find agents with a specific capability."""
        agent_ids = self._by_capability.get(capability, [])
        return [self._agents[aid] for aid in agent_ids if self._agents.get(aid)]
    
    def find_by_domain(self, domain: str) -> List[RegisteredAgent]:
        """Find all agents in a domain."""
        agent_ids = self._by_domain.get(domain, [])
        return [self._agents[aid] for aid in agent_ids if self._agents.get(aid)]
    
    def get(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get a specific agent."""
        return self._agents.get(agent_id)
    
    def get_all(self) -> List[RegisteredAgent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def register_defaults(self) -> None:
        """Register the default system agents."""
        # Genesis domain
        self.register(RegisteredAgent(
            agent_id="genesis.core",
            tier=AgentTier.DOMAIN,
            domain="genesis",
            capabilities=[AgentCapability.PROFILING],
            description="Main profiling and onboarding agent",
        ))
        
        self.register(RegisteredAgent(
            agent_id="genesis.profiler",
            tier=AgentTier.SUB,
            domain="genesis",
            capabilities=[
                AgentCapability.PROFILING,
                AgentCapability.ARCHETYPES,
                AgentCapability.HUMAN_DESIGN,
            ],
            description="Pattern detection and archetype analysis",
        ))
        
        self.register(RegisteredAgent(
            agent_id="genesis.hypothesis",
            tier=AgentTier.SUB,
            domain="genesis",
            capabilities=[AgentCapability.PROFILING],
            description="Hypothesis generation and verification",
        ))
        
        # Vision domain (placeholder)
        self.register(RegisteredAgent(
            agent_id="vision.analyzer",
            tier=AgentTier.DOMAIN,
            domain="vision",
            capabilities=[
                AgentCapability.VISION,
                AgentCapability.FOOD_ANALYSIS,
            ],
            description="Image analysis and food scanning",
        ))
        
        # Synthesis
        self.register(RegisteredAgent(
            agent_id="synthesis.engine",
            tier=AgentTier.MASTER,
            domain="synthesis",
            capabilities=[AgentCapability.SYNTHESIS],
            description="Cross-domain insight synthesis",
        ))


# =============================================================================
# SOVEREIGN ROUTER
# =============================================================================

class SovereignRouter:
    """
    Routes requests to appropriate agents via the SwarmBus.
    
    The Router provides a high-level interface for:
    - Delegating work to domain agents
    - Collecting responses from multiple agents
    - Discovering available capabilities
    
    Usage:
        router = SovereignRouter()
        
        # Delegate to specific agent
        result = await router.delegate(DelegationRequest(
            target_agent="genesis.profiler",
            task_description="Analyze this message for patterns",
            input_data={"message": "I'm feeling tired..."},
        ))
        
        # Find and delegate by capability
        result = await router.delegate(DelegationRequest(
            target_capability=AgentCapability.FOOD_ANALYSIS,
            task_description="Analyze this food image",
            input_data={"image_url": "..."},
        ))
        
        # Collect from multiple
        result = await router.delegate(DelegationRequest(
            delegation_type=DelegationType.COLLECT,
            target_domain="genesis",
            task_description="Get all profile insights",
        ))
    """
    
    def __init__(self):
        self.discovery = AgentDiscovery()
        self._bus: Optional[SwarmBus] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the router."""
        if self._initialized:
            return
        
        # Get SwarmBus instance
        self._bus = await get_bus()
        
        # Register default agents
        self.discovery.register_defaults()
        
        # Subscribe Sovereign to the bus
        await self._bus.subscribe(
            agent_id="sovereign",
            handler=self._handle_message,
            agent_tier=AgentTier.ORCHESTRATOR,
            domain="sovereign",
            capability="omniscient",
        )
        
        self._initialized = True
        logger.info("[SovereignRouter] Initialized and subscribed to SwarmBus")
    
    async def _handle_message(self, envelope: SwarmEnvelope) -> Optional[Dict]:
        """Handle incoming messages from the SwarmBus."""
        logger.debug(f"[SovereignRouter] Received: {envelope.id} from {envelope.source_agent_id}")
        
        # For now, just acknowledge
        return {"status": "received", "envelope_id": envelope.id}
    
    async def delegate(self, request: DelegationRequest) -> DelegationResult:
        """
        Delegate a task to one or more agents.
        
        The routing strategy depends on what's specified:
        - target_agent: Direct routing
        - target_capability: Find best agent with capability
        - target_domain: Route to domain (or collect from all)
        """
        start_time = datetime.utcnow()
        
        if not self._initialized:
            await self.initialize()
        
        try:
            if request.delegation_type == DelegationType.DIRECT:
                return await self._delegate_direct(request, start_time)
            elif request.delegation_type == DelegationType.COLLECT:
                return await self._delegate_collect(request, start_time)
            else:
                return DelegationResult(
                    request_id=request.id,
                    success=False,
                    error=f"Unsupported delegation type: {request.delegation_type}",
                )
        except Exception as e:
            logger.error(f"[SovereignRouter] Delegation failed: {e}")
            return DelegationResult(
                request_id=request.id,
                success=False,
                error=str(e),
            )
    
    async def _delegate_direct(
        self,
        request: DelegationRequest,
        start_time: datetime,
    ) -> DelegationResult:
        """Delegate to a single agent."""
        
        # Determine target
        target_agent = request.target_agent
        
        if not target_agent and request.target_capability:
            # Find by capability
            agents = self.discovery.find_by_capability(request.target_capability)
            if not agents:
                return DelegationResult(
                    request_id=request.id,
                    success=False,
                    error=f"No agent found for capability: {request.target_capability}",
                )
            target_agent = agents[0].agent_id
        
        if not target_agent:
            return DelegationResult(
                request_id=request.id,
                success=False,
                error="No target specified for delegation",
            )
        
        # Create envelope
        envelope = await self._bus.send(
            source_agent_id="sovereign",
            target_agent_id=target_agent,
            payload={
                "task": request.task_description,
                "input": request.input_data,
                "session_id": request.session_id,
                "user_context": request.user_context,
            },
            priority=request.priority,
            expects_response=request.expects_response,
        )
        
        # Wait for response if needed
        if request.expects_response:
            # In full implementation, we'd await the response
            # For now, return the envelope info
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return DelegationResult(
                request_id=request.id,
                success=True,
                agent_id=target_agent,
                response={"envelope_id": envelope.id, "status": "sent"},
                execution_time_ms=execution_time,
            )
        
        return DelegationResult(
            request_id=request.id,
            success=True,
            agent_id=target_agent,
        )
    
    async def _delegate_collect(
        self,
        request: DelegationRequest,
        start_time: datetime,
    ) -> DelegationResult:
        """Collect responses from multiple agents."""
        
        # Find all target agents
        agents = []
        if request.target_domain:
            agents = self.discovery.find_by_domain(request.target_domain)
        elif request.target_capability:
            agents = self.discovery.find_by_capability(request.target_capability)
        
        if not agents:
            return DelegationResult(
                request_id=request.id,
                success=False,
                error="No agents found for collection",
            )
        
        # Send to all
        tasks = []
        for agent in agents:
            envelope = await self._bus.send(
                source_agent_id="sovereign",
                target_agent_id=agent.agent_id,
                payload={
                    "task": request.task_description,
                    "input": request.input_data,
                    "session_id": request.session_id,
                },
                priority=request.priority,
                expects_response=True,
            )
            tasks.append({"agent_id": agent.agent_id, "envelope_id": envelope.id})
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return DelegationResult(
            request_id=request.id,
            success=True,
            agent_ids=[a.agent_id for a in agents],
            responses=[{"sent": True, **t} for t in tasks],
            execution_time_ms=execution_time,
        )
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    async def delegate_to_genesis(
        self,
        task: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> DelegationResult:
        """Delegate a profiling-related task to Genesis."""
        return await self.delegate(DelegationRequest(
            target_agent="genesis.core",
            task_description=task,
            input_data=input_data,
            session_id=session_id,
        ))
    
    async def delegate_to_vision(
        self,
        task: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> DelegationResult:
        """Delegate an image/vision task."""
        return await self.delegate(DelegationRequest(
            target_capability=AgentCapability.VISION,
            task_description=task,
            input_data=input_data,
            session_id=session_id,
        ))
    
    async def synthesize_cross_domain(
        self,
        query: str,
        domains: List[str],
        session_id: Optional[str] = None,
    ) -> DelegationResult:
        """Request cross-domain synthesis."""
        return await self.delegate(DelegationRequest(
            target_capability=AgentCapability.SYNTHESIS,
            task_description=f"Synthesize insights for: {query}",
            input_data={"query": query, "domains": domains},
            session_id=session_id,
        ))
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of all available agents and their capabilities."""
        return [
            {
                "agent_id": agent.agent_id,
                "domain": agent.domain,
                "capabilities": [c.value for c in agent.capabilities],
                "description": agent.description,
                "tier": agent.tier.value,
            }
            for agent in self.discovery.get_all()
        ]
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if any agent has a specific capability."""
        return bool(self.discovery.find_by_capability(capability))
