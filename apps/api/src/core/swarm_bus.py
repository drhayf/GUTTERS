"""
The Swarm Bus - Neural Network for Agent Communication

This module implements the central nervous system of the Sovereign Swarm - a 
sophisticated pub/sub message bus that enables real-time, bidirectional 
communication between ALL agents in the system.

Architecture Philosophy:
━━━━━━━━━━━━━━━━━━━━━━━━━
The SwarmBus is NOT a simple message queue. It is an intelligent routing 
system that understands:
- Agent hierarchies (Master → Domain → Sub-agent)
- Message priorities (Critical → High → Normal → Low → Batch)
- Routing patterns (Direct, Broadcast, Escalation, Delegation)
- Message lifecycle (Pending → Delivered → Acknowledged → Completed)

Communication Patterns:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. DIRECT: Point-to-point (Agent A → Agent B)
2. BROADCAST: One-to-many (Agent A → All agents matching criteria)
3. ESCALATION: Child → Parent (Sub-agent → Master for help)
4. DELEGATION: Parent → Child (Master → Sub-agent for specialized work)
5. FANOUT: One → All in domain (Master → All Genesis sub-agents)
6. COLLECT: Many → One (Aggregate responses from multiple agents)

Message Lifecycle:
━━━━━━━━━━━━━━━━━━━━━━━━━
    ┌─────────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
    │ PENDING │───►│ DELIVERED │───►│ ACKNOWLEDGED │───►│ COMPLETED │
    └─────────┘    └───────────┘    └──────────────┘    └───────────┘
         │              │                   │
         ▼              ▼                   ▼
    ┌─────────┐    ┌───────────┐    ┌──────────────┐
    │ EXPIRED │    │  FAILED   │    │   REJECTED   │
    └─────────┘    └───────────┘    └──────────────┘

Thread Safety:
━━━━━━━━━━━━━━━━━━━━━━━━━
The SwarmBus is designed for concurrent async operations:
- Uses asyncio.Queue for thread-safe message passing
- Maintains locks around subscription modifications
- Supports parallel message processing with configurable workers
"""

from typing import (
    Optional, Any, Callable, Awaitable, TypeVar, Generic,
    Dict, List, Set, Tuple, Union
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4
from abc import ABC, abstractmethod
import asyncio
import logging
import weakref
from collections import defaultdict

from shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    PacketPriority,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class MessageStatus(str, Enum):
    """Lifecycle status of a message."""
    PENDING = "pending"           # Created, not yet delivered
    QUEUED = "queued"             # In delivery queue
    DELIVERED = "delivered"       # Sent to recipient(s)
    ACKNOWLEDGED = "acknowledged" # Recipient confirmed receipt
    COMPLETED = "completed"       # Fully processed
    EXPIRED = "expired"           # TTL exceeded
    FAILED = "failed"             # Delivery failed
    REJECTED = "rejected"         # Recipient rejected


class RoutingPattern(str, Enum):
    """How a message should be routed."""
    DIRECT = "direct"           # Point-to-point
    BROADCAST = "broadcast"     # To all matching subscribers
    ESCALATION = "escalation"   # Child → Parent
    DELEGATION = "delegation"   # Parent → Child
    FANOUT = "fanout"           # To all in a domain
    COLLECT = "collect"         # Aggregate from multiple
    ROUND_ROBIN = "round_robin" # Distribute across pool


class AgentTier(str, Enum):
    """Hierarchical tier of an agent."""
    ORCHESTRATOR = "orchestrator"  # The central brain
    MASTER = "master"              # Cross-domain coordinators
    DOMAIN = "domain"              # Domain managers (Genesis, Vision)
    SUB = "sub"                    # Specialized sub-agents
    WORKER = "worker"              # Ephemeral workers


# =============================================================================
# MESSAGE ENVELOPE
# =============================================================================

@dataclass
class SwarmEnvelope:
    """
    The wrapper around every message in the swarm.
    
    Contains routing metadata, lifecycle tracking, and the actual payload.
    This is what flows through the SwarmBus - agents send/receive these.
    """
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None  # For request/response pairing
    causation_id: Optional[str] = None    # What triggered this message
    
    # Routing
    source_agent_id: str = ""
    source_tier: AgentTier = AgentTier.SUB
    target_agent_id: Optional[str] = None  # None = use routing pattern
    target_tier: Optional[AgentTier] = None
    target_domain: Optional[str] = None    # e.g., "genesis", "vision"
    target_capability: Optional[str] = None  # e.g., "hypothesis", "profiling"
    routing_pattern: RoutingPattern = RoutingPattern.DIRECT
    
    # The payload
    packet: Optional[SovereignPacket] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Priority & Timing
    priority: PacketPriority = PacketPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    ttl_seconds: int = 300  # 5 minutes default
    
    # Lifecycle
    status: MessageStatus = MessageStatus.PENDING
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Response handling
    expects_response: bool = False
    response_timeout_seconds: int = 30
    responses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at if self.expires_at else False
    
    @property
    def age_seconds(self) -> float:
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    def mark_delivered(self) -> None:
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
    
    def mark_acknowledged(self) -> None:
        self.status = MessageStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
    
    def mark_completed(self, response: Optional[Dict] = None) -> None:
        self.status = MessageStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if response:
            self.responses.append(response)
    
    def mark_failed(self, error: str) -> None:
        self.status = MessageStatus.FAILED
        self.metadata["error"] = error
    
    def add_response(self, agent_id: str, response: Any) -> None:
        """Add a response from an agent (for COLLECT pattern)."""
        self.responses.append({
            "agent_id": agent_id,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "source_agent_id": self.source_agent_id,
            "source_tier": self.source_tier.value,
            "target_agent_id": self.target_agent_id,
            "target_tier": self.target_tier.value if self.target_tier else None,
            "target_domain": self.target_domain,
            "routing_pattern": self.routing_pattern.value,
            "packet": self.packet.to_dict() if self.packet else None,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "age_seconds": self.age_seconds,
            "expects_response": self.expects_response,
            "response_count": len(self.responses),
        }


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@dataclass
class Subscription:
    """
    A subscription to the SwarmBus.
    
    Agents create subscriptions to receive messages matching certain criteria.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    agent_tier: AgentTier = AgentTier.SUB
    domain: Optional[str] = None       # Filter by domain
    capability: Optional[str] = None   # Filter by capability
    
    # What this subscriber can handle
    handles_tiers: List[AgentTier] = field(default_factory=list)
    handles_patterns: List[RoutingPattern] = field(default_factory=list)
    handles_priorities: List[PacketPriority] = field(default_factory=list)
    
    # The callback
    handler: Optional[Callable[[SwarmEnvelope], Awaitable[Optional[Dict]]]] = None
    
    # Subscription state
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    
    def matches(self, envelope: SwarmEnvelope) -> bool:
        """Check if this subscription should receive the envelope."""
        if not self.active:
            return False
        
        # Direct targeting overrides filters
        if envelope.target_agent_id and envelope.target_agent_id == self.agent_id:
            return True
        
        # Check tier targeting
        if envelope.target_tier and envelope.target_tier != self.agent_tier:
            return False
        
        # Check domain filtering
        if envelope.target_domain and self.domain:
            if envelope.target_domain != self.domain:
                return False
        
        # Check capability filtering
        if envelope.target_capability and self.capability:
            if envelope.target_capability != self.capability:
                return False
        
        return True
    
    async def deliver(self, envelope: SwarmEnvelope) -> Optional[Dict]:
        """Deliver an envelope to this subscriber."""
        if not self.handler:
            logger.warning(f"[Subscription:{self.id}] No handler configured")
            return None
        
        self.message_count += 1
        self.last_message_at = datetime.utcnow()
        
        try:
            return await self.handler(envelope)
        except Exception as e:
            logger.error(f"[Subscription:{self.id}] Handler error: {e}")
            return {"error": str(e)}


# =============================================================================
# THE SWARM BUS
# =============================================================================

class SwarmBus:
    """
    The Central Nervous System of the Sovereign Swarm.
    
    A singleton that manages all inter-agent communication with:
    - Priority-based message queuing
    - Intelligent routing based on agent capabilities
    - Request/response correlation
    - Message lifecycle tracking
    - Dead letter handling for failed messages
    
    Usage:
        bus = SwarmBus.get_instance()
        
        # Subscribe to messages
        await bus.subscribe(
            agent_id="genesis.hypothesis",
            domain="genesis",
            capability="hypothesis",
            handler=my_handler,
        )
        
        # Send a message
        envelope = await bus.send(
            source_agent_id="genesis.profiler",
            target_agent_id="genesis.hypothesis",
            payload={"signal": {...}},
            priority=PacketPriority.HIGH,
        )
        
        # Escalate to parent
        await bus.escalate(
            source_agent_id="genesis.hypothesis",
            payload={"need_help": "complex_pattern"},
        )
        
        # Broadcast to domain
        await bus.broadcast(
            source_agent_id="master.hypothesis",
            target_domain="genesis",
            payload={"command": "refresh_hypotheses"},
        )
    """
    
    _instance: Optional["SwarmBus"] = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_instance(cls) -> "SwarmBus":
        """Get the singleton SwarmBus instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._initialize()
            return cls._instance
    
    @classmethod
    def get_instance_sync(cls) -> "SwarmBus":
        """Synchronous version for initialization contexts."""
        if cls._instance is None:
            cls._instance = cls()
            # Note: _initialize needs to be called separately in async context
        return cls._instance
    
    def __init__(self):
        # Subscriptions indexed by agent_id
        self._subscriptions: Dict[str, Subscription] = {}
        
        # Domain-based subscription index for fast lookups
        self._domain_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Capability-based subscription index
        self._capability_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Tier-based subscription index
        self._tier_index: Dict[AgentTier, Set[str]] = defaultdict(set)
        
        # Priority queues for message processing
        self._queues: Dict[PacketPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in PacketPriority
        }
        
        # Pending responses (correlation_id → envelope)
        self._pending_responses: Dict[str, SwarmEnvelope] = {}
        
        # Message history (for debugging/analysis)
        self._message_history: List[SwarmEnvelope] = []
        self._max_history = 1000
        
        # Dead letter queue
        self._dead_letters: List[SwarmEnvelope] = []
        self._max_dead_letters = 100
        
        # Processing state
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._worker_count = 4
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "escalations": 0,
            "broadcasts": 0,
        }
        
        # Lock for subscription modifications
        self._sub_lock = asyncio.Lock()
        
        logger.info("[SwarmBus] Initialized")
    
    async def _initialize(self) -> None:
        """Initialize the bus and start worker tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Start priority queue workers
        for i in range(self._worker_count):
            worker = asyncio.create_task(self._process_queue(i))
            self._workers.append(worker)
        
        logger.info(f"[SwarmBus] Started {self._worker_count} workers")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the bus."""
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("[SwarmBus] Shutdown complete")
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    async def subscribe(
        self,
        agent_id: str,
        handler: Callable[[SwarmEnvelope], Awaitable[Optional[Dict]]],
        agent_tier: AgentTier = AgentTier.SUB,
        domain: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> Subscription:
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_id: Unique identifier for the agent
            handler: Async function to handle incoming envelopes
            agent_tier: The agent's tier in the hierarchy
            domain: The domain this agent belongs to (e.g., "genesis")
            capability: The capability this agent provides (e.g., "hypothesis")
            
        Returns:
            The created Subscription
        """
        async with self._sub_lock:
            sub = Subscription(
                agent_id=agent_id,
                agent_tier=agent_tier,
                domain=domain,
                capability=capability,
                handler=handler,
            )
            
            self._subscriptions[agent_id] = sub
            
            # Update indices
            if domain:
                self._domain_index[domain].add(agent_id)
            if capability:
                self._capability_index[capability].add(agent_id)
            self._tier_index[agent_tier].add(agent_id)
            
            logger.info(f"[SwarmBus] Subscribed: {agent_id} (tier={agent_tier.value}, domain={domain})")
            return sub
    
    async def unsubscribe(self, agent_id: str) -> bool:
        """Unsubscribe an agent."""
        async with self._sub_lock:
            sub = self._subscriptions.pop(agent_id, None)
            if not sub:
                return False
            
            # Clean up indices
            if sub.domain and agent_id in self._domain_index[sub.domain]:
                self._domain_index[sub.domain].remove(agent_id)
            if sub.capability and agent_id in self._capability_index[sub.capability]:
                self._capability_index[sub.capability].remove(agent_id)
            if agent_id in self._tier_index[sub.agent_tier]:
                self._tier_index[sub.agent_tier].remove(agent_id)
            
            logger.info(f"[SwarmBus] Unsubscribed: {agent_id}")
            return True
    
    def get_subscription(self, agent_id: str) -> Optional[Subscription]:
        """Get a subscription by agent ID."""
        return self._subscriptions.get(agent_id)
    
    # =========================================================================
    # MESSAGE SENDING
    # =========================================================================
    
    async def send(
        self,
        source_agent_id: str,
        payload: Dict[str, Any],
        packet: Optional[SovereignPacket] = None,
        target_agent_id: Optional[str] = None,
        target_tier: Optional[AgentTier] = None,
        target_domain: Optional[str] = None,
        target_capability: Optional[str] = None,
        routing_pattern: RoutingPattern = RoutingPattern.DIRECT,
        priority: PacketPriority = PacketPriority.NORMAL,
        expects_response: bool = False,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        ttl_seconds: int = 300,
    ) -> SwarmEnvelope:
        """
        Send a message through the bus.
        
        This is the primary method for all inter-agent communication.
        
        Args:
            source_agent_id: ID of the sending agent
            payload: The message payload
            packet: Optional SovereignPacket
            target_agent_id: Specific target agent (for DIRECT)
            target_tier: Target tier (for tier-based routing)
            target_domain: Target domain (for domain-based routing)
            target_capability: Target capability (for capability-based routing)
            routing_pattern: How to route the message
            priority: Message priority
            expects_response: Whether to wait for response
            correlation_id: For request/response pairing
            causation_id: What caused this message
            ttl_seconds: Time-to-live
            
        Returns:
            The created SwarmEnvelope
        """
        # Determine source tier
        source_sub = self._subscriptions.get(source_agent_id)
        source_tier = source_sub.agent_tier if source_sub else AgentTier.SUB
        
        envelope = SwarmEnvelope(
            source_agent_id=source_agent_id,
            source_tier=source_tier,
            target_agent_id=target_agent_id,
            target_tier=target_tier,
            target_domain=target_domain,
            target_capability=target_capability,
            routing_pattern=routing_pattern,
            packet=packet,
            payload=payload,
            priority=priority,
            expects_response=expects_response,
            correlation_id=correlation_id or (str(uuid4()) if expects_response else None),
            causation_id=causation_id,
            ttl_seconds=ttl_seconds,
        )
        
        # Queue the message
        await self._queues[priority].put(envelope)
        envelope.status = MessageStatus.QUEUED
        
        self._stats["messages_sent"] += 1
        
        # If expecting response, register for correlation
        if expects_response and envelope.correlation_id:
            self._pending_responses[envelope.correlation_id] = envelope
        
        logger.debug(f"[SwarmBus] Queued: {envelope.id} ({routing_pattern.value}) → {target_agent_id or target_domain or 'broadcast'}")
        
        return envelope
    
    async def escalate(
        self,
        source_agent_id: str,
        payload: Dict[str, Any],
        reason: str = "need_help",
        priority: PacketPriority = PacketPriority.HIGH,
    ) -> SwarmEnvelope:
        """
        Escalate a message to the parent tier.
        
        Sub-agents use this to ask for help from Master agents.
        Domain agents use this to notify the Orchestrator.
        
        Args:
            source_agent_id: The escalating agent
            payload: What needs attention
            reason: Why escalating (need_help, discovery, completion)
            priority: Usually HIGH for escalations
            
        Returns:
            The created envelope
        """
        source_sub = self._subscriptions.get(source_agent_id)
        if not source_sub:
            logger.warning(f"[SwarmBus] Escalation from unknown agent: {source_agent_id}")
            source_tier = AgentTier.SUB
        else:
            source_tier = source_sub.agent_tier
        
        # Determine parent tier
        tier_hierarchy = [AgentTier.SUB, AgentTier.DOMAIN, AgentTier.MASTER, AgentTier.ORCHESTRATOR]
        try:
            current_idx = tier_hierarchy.index(source_tier)
            parent_tier = tier_hierarchy[current_idx + 1] if current_idx < len(tier_hierarchy) - 1 else AgentTier.ORCHESTRATOR
        except ValueError:
            parent_tier = AgentTier.MASTER
        
        self._stats["escalations"] += 1
        
        return await self.send(
            source_agent_id=source_agent_id,
            payload={
                "escalation": True,
                "reason": reason,
                **payload,
            },
            target_tier=parent_tier,
            target_domain=source_sub.domain if source_sub else None,
            routing_pattern=RoutingPattern.ESCALATION,
            priority=priority,
        )
    
    async def delegate(
        self,
        source_agent_id: str,
        target_capability: str,
        payload: Dict[str, Any],
        target_domain: Optional[str] = None,
        expects_response: bool = True,
    ) -> SwarmEnvelope:
        """
        Delegate a task to a sub-agent with a specific capability.
        
        Master agents use this to distribute work.
        
        Args:
            source_agent_id: The delegating agent
            target_capability: What capability is needed
            payload: The task details
            target_domain: Optional specific domain
            expects_response: Whether to wait for completion
            
        Returns:
            The created envelope
        """
        return await self.send(
            source_agent_id=source_agent_id,
            payload={
                "delegation": True,
                **payload,
            },
            target_tier=AgentTier.SUB,
            target_domain=target_domain,
            target_capability=target_capability,
            routing_pattern=RoutingPattern.DELEGATION,
            expects_response=expects_response,
        )
    
    async def broadcast(
        self,
        source_agent_id: str,
        payload: Dict[str, Any],
        target_domain: Optional[str] = None,
        target_tier: Optional[AgentTier] = None,
        priority: PacketPriority = PacketPriority.NORMAL,
    ) -> SwarmEnvelope:
        """
        Broadcast a message to all matching agents.
        
        Args:
            source_agent_id: The broadcasting agent
            payload: The message
            target_domain: Optional domain filter
            target_tier: Optional tier filter
            priority: Message priority
            
        Returns:
            The created envelope
        """
        self._stats["broadcasts"] += 1
        
        return await self.send(
            source_agent_id=source_agent_id,
            payload=payload,
            target_domain=target_domain,
            target_tier=target_tier,
            routing_pattern=RoutingPattern.BROADCAST,
            priority=priority,
        )
    
    async def respond(
        self,
        original_envelope: SwarmEnvelope,
        responder_agent_id: str,
        response_payload: Dict[str, Any],
    ) -> None:
        """
        Send a response to a message that expected one.
        
        Args:
            original_envelope: The envelope being responded to
            responder_agent_id: Who is responding
            response_payload: The response data
        """
        if not original_envelope.correlation_id:
            logger.warning(f"[SwarmBus] Cannot respond - no correlation_id")
            return
        
        # Find the pending request
        pending = self._pending_responses.get(original_envelope.correlation_id)
        if pending:
            pending.add_response(responder_agent_id, response_payload)
            
            # If we have all expected responses, mark complete
            # (For COLLECT pattern, we might expect multiple)
            if original_envelope.routing_pattern != RoutingPattern.COLLECT:
                pending.mark_completed(response_payload)
                self._pending_responses.pop(original_envelope.correlation_id, None)
    
    # =========================================================================
    # MESSAGE PROCESSING
    # =========================================================================
    
    async def _process_queue(self, worker_id: int) -> None:
        """Worker task that processes messages from priority queues."""
        logger.info(f"[SwarmBus:Worker-{worker_id}] Started")
        
        while self._running:
            try:
                # Process queues in priority order
                envelope = None
                for priority in [PacketPriority.CRITICAL, PacketPriority.HIGH, 
                                PacketPriority.NORMAL, PacketPriority.LOW, PacketPriority.BATCH]:
                    try:
                        envelope = self._queues[priority].get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue
                
                if envelope is None:
                    await asyncio.sleep(0.01)  # Small sleep if no messages
                    continue
                
                # Check expiration
                if envelope.is_expired:
                    envelope.status = MessageStatus.EXPIRED
                    self._add_to_dead_letter(envelope)
                    continue
                
                # Route and deliver
                await self._route_envelope(envelope)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SwarmBus:Worker-{worker_id}] Error: {e}")
    
    async def _route_envelope(self, envelope: SwarmEnvelope) -> None:
        """Route an envelope to appropriate subscribers."""
        recipients = self._find_recipients(envelope)
        
        if not recipients:
            logger.warning(f"[SwarmBus] No recipients for: {envelope.id}")
            envelope.mark_failed("no_recipients")
            self._add_to_dead_letter(envelope)
            return
        
        # Deliver to all recipients
        delivery_count = 0
        for agent_id in recipients:
            sub = self._subscriptions.get(agent_id)
            if not sub:
                continue
            
            try:
                envelope.mark_delivered()
                response = await sub.deliver(envelope)
                delivery_count += 1
                
                if response and envelope.expects_response:
                    await self.respond(envelope, agent_id, response)
                    
            except Exception as e:
                logger.error(f"[SwarmBus] Delivery to {agent_id} failed: {e}")
        
        if delivery_count > 0:
            self._stats["messages_delivered"] += 1
            self._add_to_history(envelope)
        else:
            envelope.mark_failed("delivery_failed")
            self._stats["messages_failed"] += 1
            self._add_to_dead_letter(envelope)
    
    def _find_recipients(self, envelope: SwarmEnvelope) -> Set[str]:
        """Find all agents that should receive this envelope."""
        recipients: Set[str] = set()
        
        # Direct targeting
        if envelope.target_agent_id:
            if envelope.target_agent_id in self._subscriptions:
                recipients.add(envelope.target_agent_id)
            return recipients
        
        # Tier-based routing
        if envelope.target_tier:
            recipients.update(self._tier_index.get(envelope.target_tier, set()))
        
        # Domain-based filtering
        if envelope.target_domain:
            domain_agents = self._domain_index.get(envelope.target_domain, set())
            if recipients:
                recipients &= domain_agents  # Intersection
            else:
                recipients.update(domain_agents)
        
        # Capability-based filtering
        if envelope.target_capability:
            capable_agents = self._capability_index.get(envelope.target_capability, set())
            if recipients:
                recipients &= capable_agents
            else:
                recipients.update(capable_agents)
        
        # For escalation, find parent
        if envelope.routing_pattern == RoutingPattern.ESCALATION:
            parent_tier = envelope.target_tier or AgentTier.MASTER
            tier_agents = self._tier_index.get(parent_tier, set())
            
            # Prefer same-domain parent
            if envelope.target_domain:
                domain_parents = tier_agents & self._domain_index.get(envelope.target_domain, set())
                if domain_parents:
                    recipients = domain_parents
                else:
                    recipients = tier_agents
            else:
                recipients = tier_agents
        
        # Filter by subscription match
        return {r for r in recipients if self._subscriptions[r].matches(envelope)}
    
    def _add_to_history(self, envelope: SwarmEnvelope) -> None:
        """Add envelope to history, maintaining max size."""
        self._message_history.append(envelope)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
    
    def _add_to_dead_letter(self, envelope: SwarmEnvelope) -> None:
        """Add failed envelope to dead letter queue."""
        self._dead_letters.append(envelope)
        if len(self._dead_letters) > self._max_dead_letters:
            self._dead_letters.pop(0)
    
    # =========================================================================
    # QUERY & STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        return {
            **self._stats,
            "subscriptions": len(self._subscriptions),
            "domains": list(self._domain_index.keys()),
            "capabilities": list(self._capability_index.keys()),
            "pending_responses": len(self._pending_responses),
            "dead_letters": len(self._dead_letters),
            "queue_sizes": {p.value: q.qsize() for p, q in self._queues.items()},
        }
    
    def get_agents_by_domain(self, domain: str) -> List[str]:
        """Get all agent IDs in a domain."""
        return list(self._domain_index.get(domain, set()))
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get all agent IDs with a capability."""
        return list(self._capability_index.get(capability, set()))
    
    def get_agents_by_tier(self, tier: AgentTier) -> List[str]:
        """Get all agent IDs at a tier."""
        return list(self._tier_index.get(tier, set()))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def get_bus() -> SwarmBus:
    """Get the global SwarmBus instance."""
    return await SwarmBus.get_instance()
