"""
The Sovereign Protocol - Universal Inter-Agent Communication Schema

This module defines the "Nervous System" of Project Sovereign - the standardized
packet format that ALL agents use to communicate with each other and the Orchestrator.

╔══════════════════════════════════════════════════════════════════════════════╗
║                      HYBRID SWARM ARCHITECTURE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  The Sovereign Swarm combines the BEST of both architectures:                ║
║                                                                              ║
║  1. ORCHESTRATOR-CENTRIC (Control & State)                                   ║
║     • Single source of truth for Digital Twin state                          ║
║     • User request routing and intent classification                         ║
║     • Final synthesis and response generation                                ║
║     • LangGraph workflow for stateful conversations                          ║
║                                                                              ║
║  2. SWARMBUS (Parallel Processing & Scalability)                             ║
║     • Async message passing for non-blocking operations                      ║
║     • Priority-based queuing (Critical → High → Normal → Low → Batch)        ║
║     • Domain-based routing (genesis, vision, logic, memory)                  ║
║     • Capability-based discovery (profiling, hypothesis, synthesis)          ║
║     • Easy agent registration via subscribe/unsubscribe                      ║
║                                                                              ║
║  Key Principle: "Orchestrator DECIDES, SwarmBus EXECUTES"                    ║
║     • Orchestrator receives user requests & decides what to do               ║
║     • SwarmBus enables parallel agent execution                              ║
║     • Results flow back through bus → Orchestrator → User                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Communication Patterns:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. DIRECT: Point-to-point (Agent A → Agent B)
2. BROADCAST: One-to-many (Orchestrator → All genesis.* agents)
3. ESCALATION: Child → Parent (genesis.profiler → genesis → orchestrator)
4. DELEGATION: Parent → Child (Orchestrator → genesis.hypothesis)
5. FANOUT: One → Domain (master.hypothesis → all genesis.*)
6. COLLECT: Gather from many (Request → Multiple agents → Aggregate)

The Fractal Pattern:
━━━━━━━━━━━━━━━━━━━━━━━━━
Agent Hierarchy (4 Tiers):
  └─ ORCHESTRATOR (Tier 0) - The central brain, makes all routing decisions
       └─ MASTER (Tier 1) - Cross-domain coordinators (MasterHypothesis, MasterScout)
            └─ DOMAIN (Tier 2) - Domain managers (Genesis, Vision, Logic)
                 └─ SUB (Tier 3) - Specialized workers (Profiler, Hypothesis Engine)

Routing Philosophy:
  • WITHIN domain: Direct calls or shared state (fast, simple)
  • ACROSS domains: Via Orchestrator or SwarmBus (decoupled, scalable)
  • ESCALATION: Always goes UP the hierarchy
  • DELEGATION: Always goes DOWN the hierarchy

Scalability & Extensibility:
━━━━━━━━━━━━━━━━━━━━━━━━━
Adding a new agent:
  1. Create agent class with execute() method
  2. Subscribe to SwarmBus with domain + capability
  3. That's it! Orchestrator will route to you based on capability

The SwarmBus provides:
  • Auto-discovery via capability registration
  • Priority queues for load management
  • Message lifecycle tracking
  • Dead letter handling for failures
  • Statistics and monitoring
"""

from typing import Any, Optional, Literal, Union, List
from enum import Enum
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS - The Vocabulary of the Swarm
# =============================================================================

class InsightType(str, Enum):
    """
    The classification of information flowing through the system.
    
    Each type triggers different handling in the Orchestrator:
    - PATTERN: Detected behavioral/psychological pattern (triggers Hypothesis Engine)
    - FACT: Verified data point (stored directly to profile)
    - SUGGESTION: Recommendation for action (may require user confirmation)
    - QUESTION: Probe for more information (triggers UI component generation)
    - HYPOTHESIS: Unverified suspicion (needs probing to confirm)
    - SYNTHESIS: Combined insight from multiple sources (high-value, store prominently)
    - ALERT: Urgent finding requiring immediate attention
    - TOOL_CALL: Request to invoke a specific tool/capability
    """
    PATTERN = "Pattern"
    FACT = "Fact"
    SUGGESTION = "Suggestion"
    QUESTION = "Question"
    HYPOTHESIS = "Hypothesis"
    SYNTHESIS = "Synthesis"
    ALERT = "Alert"
    TOOL_CALL = "ToolCall"


class TargetLayer(str, Enum):
    """
    Where in the hierarchy this packet should be routed.
    
    The Fractal Swarm has layers:
    - ORCHESTRATOR: The master coordinator (receives all cross-agent traffic)
    - GENESIS: The profiling/onboarding layer
    - VISION: Image analysis and food scanning
    - LOGIC: The HRM deep reasoning engine
    - MEMORY: Long-term storage and retrieval (Supabase/Vector)
    - UI: Frontend rendering layer (generative components)
    - USER: Direct user communication
    """
    ORCHESTRATOR = "Orchestrator"
    GENESIS = "Genesis"
    VISION = "Vision"
    LOGIC = "Logic"
    MEMORY = "Memory"
    UI = "UI"
    USER = "User"


class ProbeType(str, Enum):
    """
    Types of UI probes the Hypothesis Engine can request.
    
    Each probe type maps to a specific Generative UI component:
    - BINARY_CHOICE: Two mutually exclusive options (A vs B)
    - SLIDER: Continuous scale (1-10, low-high)
    - TEXT_INPUT: Free-form text response
    - MULTIPLE_CHOICE: Select from N options
    - CONFIRMATION: Yes/No verification of a hypothesis
    - REFLECTION: Open-ended introspection prompt
    - CARD_SELECTION: Visual archetype/category selection
    """
    BINARY_CHOICE = "binary_choice"
    SLIDER = "slider"
    TEXT_INPUT = "text_input"
    MULTIPLE_CHOICE = "multiple_choice"
    CONFIRMATION = "confirmation"
    REFLECTION = "reflection"
    CARD_SELECTION = "card_selection"


class AgentCapability(str, Enum):
    """
    Capabilities that agents can advertise in their manifests.
    Used by Orchestrator for intelligent routing.
    """
    PROFILING = "profiling"
    ARCHETYPES = "archetypes"
    HUMAN_DESIGN = "human_design"
    GENE_KEYS = "gene_keys"
    ASTROLOGY = "astrology"
    NUMEROLOGY = "numerology"
    VISION = "vision"
    FOOD_ANALYSIS = "food_analysis"
    HEALTH_METRICS = "health_metrics"
    FINANCE = "finance"
    JOURNALING = "journaling"
    SYNTHESIS = "synthesis"
    HRM_REASONING = "hrm_reasoning"


class ConfidenceLevel(str, Enum):
    """
    Human-readable confidence thresholds.
    Used to determine when to probe vs. when to store.
    """
    CERTAIN = "certain"        # >= 0.95 - Store as fact
    HIGH = "high"              # >= 0.80 - Store with note
    MODERATE = "moderate"      # >= 0.60 - One more probe
    LOW = "low"                # >= 0.40 - Multiple probes needed
    SPECULATION = "speculation" # < 0.40 - Hypothesis only


class PacketPriority(str, Enum):
    """
    Priority levels for packet processing.
    Higher priority packets are processed first in the queue.
    """
    CRITICAL = "critical"  # Immediate processing (alerts, errors)
    HIGH = "high"          # User-facing responses
    NORMAL = "normal"      # Standard agent communication
    LOW = "low"            # Background processing
    BATCH = "batch"        # Can be batched with others


class MessageType(str, Enum):
    """
    The communication pattern for a message.
    
    Enables bidirectional and multi-party communication patterns:
    - REQUEST: Expects a response (has correlation_id)
    - RESPONSE: Reply to a request (references correlation_id)
    - EVENT: Fire-and-forget notification
    - BROADCAST: One-to-many announcement
    - ESCALATION: Child → Parent for help
    - DELEGATION: Parent → Child for work
    - SUBSCRIPTION: Agent subscribing to packet types
    - HEARTBEAT: Keep-alive for long-running operations
    """
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"
    ESCALATION = "escalation"
    DELEGATION = "delegation"
    SUBSCRIPTION = "subscription"
    HEARTBEAT = "heartbeat"


class RoutingIntent(str, Enum):
    """
    How the packet should be routed.
    
    Works with MessageType to determine routing behavior:
    - DIRECT: Point-to-point (specific target_agent)
    - DOMAIN: All agents in a domain
    - CAPABILITY: All agents with a capability
    - TIER: All agents at a hierarchy level
    - TOPIC: Subscription-based (agents opted in)
    """
    DIRECT = "direct"
    DOMAIN = "domain"
    CAPABILITY = "capability"
    TIER = "tier"
    TOPIC = "topic"


class EscalationReason(str, Enum):
    """
    Why a sub-agent is escalating to its parent.
    
    Helps the parent understand what kind of help is needed:
    - NEED_DECISION: Can't decide between options
    - NEED_CONTEXT: Missing information from other domains
    - CONFIDENCE_LOW: Hypothesis needs cross-domain validation
    - DISCOVERY: Found something significant to report
    - COMPLETION: Task completed, reporting results
    - STUCK: Can't make progress
    - CONFLICT: Detected conflicting information
    """
    NEED_DECISION = "need_decision"
    NEED_CONTEXT = "need_context"
    CONFIDENCE_LOW = "confidence_low"
    DISCOVERY = "discovery"
    COMPLETION = "completion"
    STUCK = "stuck"
    CONFLICT = "conflict"


class AgentHierarchyTier(str, Enum):
    """
    Hierarchical tier of an agent in the swarm.
    
    The fractal structure:
    - ORCHESTRATOR: The central brain
    - MASTER: Cross-domain coordinators (MasterHypothesisEngine, MasterScout)
    - DOMAIN: Domain managers (Genesis, Vision, Finance)
    - SUB: Specialized sub-agents (Profiler, Hypothesis, etc.)
    - WORKER: Ephemeral processing workers
    """
    ORCHESTRATOR = "orchestrator"
    MASTER = "master"
    DOMAIN = "domain"
    SUB = "sub"
    WORKER = "worker"


# =============================================================================
# PAYLOAD MODELS - Structured Data Within Packets
# =============================================================================

class ProbePayload(BaseModel):
    """Payload for probe/question packets requesting user input."""
    probe_type: ProbeType
    prompt: str
    options: Optional[list[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[Any] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # For hypothesis resolution
    resolves_trait: Optional[str] = None  # e.g., "human_design_type"
    expected_values: Optional[dict[str, str]] = None  # option -> trait value mapping


class HypothesisPayload(BaseModel):
    """Payload for hypothesis packets - unverified suspicions about the user."""
    trait_name: str  # e.g., "human_design_type", "jungian_function"
    suspected_value: str  # e.g., "Projector", "Ni"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)  # What triggered this suspicion
    contradictions: list[str] = Field(default_factory=list)  # Counter-evidence
    probes_remaining: int = 3  # How many more probes before we force a decision
    
    def confidence_level(self) -> ConfidenceLevel:
        """Convert numeric confidence to human-readable level."""
        if self.confidence >= 0.95:
            return ConfidenceLevel.CERTAIN
        elif self.confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.60:
            return ConfidenceLevel.MODERATE
        elif self.confidence >= 0.40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.SPECULATION


class PatternPayload(BaseModel):
    """Payload for detected behavioral/psychological patterns."""
    pattern_name: str
    pattern_category: str  # e.g., "energetic", "cognitive", "emotional"
    indicators: list[str]  # What signals triggered this detection
    strength: float = Field(ge=0.0, le=1.0)  # How strongly present
    framework: Optional[str] = None  # e.g., "human_design", "jungian"
    related_traits: list[str] = Field(default_factory=list)


class SynthesisPayload(BaseModel):
    """Payload for synthesized insights from multiple sources."""
    title: str
    summary: str
    source_agents: list[str]
    source_insights: list[str]  # IDs of contributing packets
    frameworks_used: list[str]
    key_findings: list[str]
    recommendations: list[str] = Field(default_factory=list)
    visualization_hint: Optional[str] = None  # Suggested UI rendering


class ToolCallPayload(BaseModel):
    """Payload for requesting tool/capability invocation."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    awaits_response: bool = True
    timeout_ms: Optional[int] = None


class AlertPayload(BaseModel):
    """Payload for urgent alerts requiring attention."""
    alert_type: Literal["error", "warning", "info", "success"]
    title: str
    message: str
    action_required: bool = False
    suggested_action: Optional[str] = None


# =============================================================================
# BIDIRECTIONAL COMMUNICATION PAYLOADS
# =============================================================================

class EscalationPayload(BaseModel):
    """
    Payload for escalation messages from child to parent agents.
    
    When a sub-agent needs help, context, or a decision from its parent,
    it creates an escalation with this payload.
    """
    reason: EscalationReason
    description: str
    
    # What the child has figured out so far
    current_state: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # What the child needs
    needs_from_parent: list[str] = Field(default_factory=list)
    
    # Options if this is a decision request
    options: Optional[list[dict[str, Any]]] = None
    recommended_option: Optional[str] = None
    
    # Context that might help
    related_packets: list[str] = Field(default_factory=list)
    frameworks_involved: list[str] = Field(default_factory=list)


class DelegationPayload(BaseModel):
    """
    Payload for delegation messages from parent to child agents.
    
    When a parent agent needs specialized work done, it delegates
    to a child with specific instructions.
    """
    task_type: str  # e.g., "analyze", "probe", "validate", "synthesize"
    instructions: str
    
    # What to work with
    input_data: dict[str, Any] = Field(default_factory=dict)
    
    # Constraints
    priority: PacketPriority = PacketPriority.NORMAL
    deadline_seconds: Optional[int] = None
    
    # Expected output
    expected_output_type: Optional[str] = None
    required_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Callback configuration
    report_progress: bool = False
    progress_interval_seconds: int = 5


class CrossDomainRequestPayload(BaseModel):
    """
    Payload for requests between sibling domains.
    
    When Genesis needs information from Vision, or Finance needs
    context from Health, they use this payload.
    """
    requesting_domain: str
    target_domain: str
    request_type: str  # e.g., "get_context", "share_insight", "validate"
    
    # What is being requested
    query: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    
    # Context from the requesting domain
    requester_context: dict[str, Any] = Field(default_factory=dict)
    
    # Response expectations
    expected_response_type: Optional[str] = None
    max_response_time_seconds: int = 30


class BroadcastPayload(BaseModel):
    """
    Payload for broadcast announcements.
    
    Used when one agent needs to notify many agents of something
    without expecting responses.
    """
    broadcast_type: Literal["announcement", "update", "alert", "discovery"]
    title: str
    message: str
    
    # Targeting
    target_domains: Optional[list[str]] = None  # None = all domains
    target_tiers: Optional[list[AgentHierarchyTier]] = None
    
    # Metadata
    importance: PacketPriority = PacketPriority.NORMAL
    expires_at: Optional[datetime] = None
    requires_acknowledgment: bool = False


class SubscriptionPayload(BaseModel):
    """
    Payload for subscription management.
    
    Agents can subscribe to receive certain types of packets
    matching specific criteria.
    """
    action: Literal["subscribe", "unsubscribe", "list"]
    
    # What to subscribe to
    insight_types: Optional[list[InsightType]] = None
    source_domains: Optional[list[str]] = None
    source_agents: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    min_confidence: Optional[float] = None
    
    # Delivery preferences
    batch_delivery: bool = False
    batch_interval_seconds: int = 60
    max_batch_size: int = 10


class ResponsePayload(BaseModel):
    """
    Payload for response messages.
    
    When responding to a request, this payload wraps the result
    along with metadata about the response.
    """
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Metadata
    processing_time_ms: Optional[int] = None
    confidence: Optional[float] = None
    
    # If partially successful
    partial_results: Optional[list[dict[str, Any]]] = None
    warnings: list[str] = Field(default_factory=list)
    
    # For continuation
    has_more: bool = False
    continuation_token: Optional[str] = None


# =============================================================================
# VOICE & EXPRESSION - The Face's Output Configuration
# =============================================================================

class VoiceId(str, Enum):
    """
    Available voice personas in the Face system.
    
    Each voice has distinct characteristics:
    - ORACLE: Ancient wisdom, symbolic, penetrating questions
    - SAGE: Calm, measured, practical wisdom
    - COMPANION: Warm, supportive, encouraging
    - CHALLENGER: Direct, provocative, pushes boundaries
    - MIRROR: Reflective, echoes back with minimal interpretation
    """
    ORACLE = "oracle"
    SAGE = "sage"
    COMPANION = "companion"
    CHALLENGER = "challenger"
    MIRROR = "mirror"


class ExpressionHint(BaseModel):
    """
    Visual expression hints for the UI layer.
    
    The Face's "micro-expressions" - how it visually communicates state.
    Maps to UI elements like pulse colors, animation speeds, etc.
    """
    pulse_color: str = Field(
        default="#00FFFF",  # Cyan default
        description="Primary color for pulsing border (hex)"
    )
    secondary_color: Optional[str] = Field(
        default=None,
        description="Secondary color for gradients (hex)"
    )
    intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Animation intensity (0=subtle, 1=dramatic)"
    )
    pulse_speed: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Pulse animation speed multiplier"
    )
    mood: str = Field(
        default="neutral",
        description="Emotional mood hint (e.g., 'curious', 'intense', 'warm', 'mysterious')"
    )


class VoiceConfig(BaseModel):
    """
    Voice configuration attached to packets.
    
    Allows packets to carry voice instructions, enabling the Face
    to modulate its voice based on content rather than just context.
    
    This implements "Adaptive Intelligence" - outputs determined by
    the SovereignPacket context, not random selection.
    """
    voice_id: VoiceId = Field(
        default=VoiceId.ORACLE,
        description="Which voice persona to use"
    )
    intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice intensity (0=gentle, 1=intense)"
    )
    warmth: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Emotional warmth (0=cool, 1=warm)"
    )
    mystery: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Cryptic vs plain speaking (0=plain, 1=cryptic)"
    )
    expression: Optional[ExpressionHint] = Field(
        default=None,
        description="Visual expression hints for UI"
    )
    
    @classmethod
    def for_insight_type(cls, insight_type: InsightType) -> "VoiceConfig":
        """
        Factory: Create voice config based on insight type.
        
        This is the "Adapter Logic" - determining output voice from packet context.
        """
        configs = {
            InsightType.PATTERN: cls(
                voice_id=VoiceId.ORACLE,
                intensity=0.6,
                mystery=0.7,
                expression=ExpressionHint(
                    pulse_color="#9B59B6",  # Purple for patterns
                    mood="mysterious",
                    intensity=0.6,
                )
            ),
            InsightType.FACT: cls(
                voice_id=VoiceId.SAGE,
                intensity=0.4,
                mystery=0.1,
                expression=ExpressionHint(
                    pulse_color="#3498DB",  # Blue for facts
                    mood="calm",
                    intensity=0.3,
                )
            ),
            InsightType.QUESTION: cls(
                voice_id=VoiceId.ORACLE,
                intensity=0.5,
                mystery=0.5,
                warmth=0.6,
                expression=ExpressionHint(
                    pulse_color="#00FFFF",  # Cyan for questions
                    mood="curious",
                    intensity=0.5,
                )
            ),
            InsightType.HYPOTHESIS: cls(
                voice_id=VoiceId.SAGE,
                intensity=0.5,
                mystery=0.4,
                expression=ExpressionHint(
                    pulse_color="#F39C12",  # Gold for hypotheses
                    mood="thoughtful",
                    intensity=0.5,
                )
            ),
            InsightType.SYNTHESIS: cls(
                voice_id=VoiceId.ORACLE,
                intensity=0.7,
                warmth=0.7,
                mystery=0.6,
                expression=ExpressionHint(
                    pulse_color="#E74C3C",  # Red for synthesis
                    mood="profound",
                    intensity=0.7,
                )
            ),
            InsightType.ALERT: cls(
                voice_id=VoiceId.CHALLENGER,
                intensity=0.8,
                warmth=0.3,
                mystery=0.1,
                expression=ExpressionHint(
                    pulse_color="#E74C3C",  # Red for alerts
                    mood="urgent",
                    intensity=0.9,
                    pulse_speed=2.0,
                )
            ),
            InsightType.SUGGESTION: cls(
                voice_id=VoiceId.COMPANION,
                intensity=0.4,
                warmth=0.8,
                mystery=0.2,
                expression=ExpressionHint(
                    pulse_color="#2ECC71",  # Green for suggestions
                    mood="encouraging",
                    intensity=0.4,
                )
            ),
        }
        return configs.get(insight_type, cls())


# =============================================================================
# THE SOVEREIGN PACKET - The Core Message Format
# =============================================================================

class SovereignPacket(BaseModel):
    """
    The Universal Communication Packet for the Sovereign Swarm.
    
    Every piece of information flowing between agents MUST be wrapped in this format.
    This ensures:
    1. Traceability: We always know where information came from
    2. Routability: The Orchestrator knows where to send it
    3. Priority: Critical insights get processed first
    4. Validation: HRM can verify reasoning before storage
    5. Consistency: All agents speak the same language
    6. Bidirectionality: Request/response correlation
    7. Cross-Domain: Sibling agents can communicate
    
    Example Flow (Escalation):
    1. genesis.hypothesis detects low-confidence pattern
    2. Emits escalation packet to master.hypothesis
    3. Master requests context from vision domain
    4. Vision responds with relevant observations
    5. Master synthesizes and delegates back to genesis
    """
    
    # ==========================================================================
    # IDENTITY
    # ==========================================================================
    packet_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Correlation for request/response pairs
    correlation_id: Optional[str] = Field(
        default=None,
        description="Links request and response packets"
    )
    causation_id: Optional[str] = Field(
        default=None,
        description="What packet caused this packet to be created"
    )
    
    # ==========================================================================
    # ROUTING
    # ==========================================================================
    source_agent: str = Field(
        ..., 
        description="The agent that created this packet (e.g., 'genesis.profiler')"
    )
    source_domain: Optional[str] = Field(
        default=None,
        description="The domain of the source agent (e.g., 'genesis')"
    )
    source_tier: AgentHierarchyTier = Field(
        default=AgentHierarchyTier.SUB,
        description="Tier of the source agent in the hierarchy"
    )
    
    target_layer: TargetLayer = Field(
        default=TargetLayer.ORCHESTRATOR,
        description="Where this packet should be routed"
    )
    target_agent: Optional[str] = Field(
        default=None,
        description="Specific target agent (for DIRECT routing)"
    )
    target_domain: Optional[str] = Field(
        default=None,
        description="Target domain (for DOMAIN routing)"
    )
    target_capability: Optional[str] = Field(
        default=None,
        description="Target capability (for CAPABILITY routing)"
    )
    
    routing_intent: RoutingIntent = Field(
        default=RoutingIntent.DIRECT,
        description="How to route this packet"
    )
    
    priority: PacketPriority = Field(
        default=PacketPriority.NORMAL,
        description="Processing priority"
    )
    
    # ==========================================================================
    # MESSAGE TYPE & CLASSIFICATION
    # ==========================================================================
    message_type: MessageType = Field(
        default=MessageType.EVENT,
        description="The communication pattern"
    )
    
    insight_type: InsightType = Field(
        ...,
        description="What kind of insight this packet represents"
    )
    
    # ==========================================================================
    # CONFIDENCE & VALIDATION
    # ==========================================================================
    confidence_score: float = Field(
        default=0.5,
        ge=0.0, 
        le=1.0,
        description="How confident the source agent is in this insight"
    )
    hrm_validated: bool = Field(
        default=False,
        description="Whether HRM has validated this insight"
    )
    hrm_reasoning_trace: Optional[str] = Field(
        default=None,
        description="If HRM validated, the reasoning trace"
    )
    
    # ==========================================================================
    # THE ACTUAL DATA
    # ==========================================================================
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="The structured data for this insight type"
    )
    
    # ==========================================================================
    # CONTEXT
    # ==========================================================================
    session_id: Optional[str] = Field(
        default=None,
        description="The user session this relates to"
    )
    parent_packet_id: Optional[str] = Field(
        default=None,
        description="If this is a response to another packet"
    )
    conversation_turn: Optional[int] = Field(
        default=None,
        description="Which turn in the conversation this relates to"
    )
    
    # ==========================================================================
    # BIDIRECTIONAL COMMUNICATION
    # ==========================================================================
    expects_response: bool = Field(
        default=False,
        description="Whether this packet expects a response"
    )
    response_timeout_seconds: int = Field(
        default=30,
        description="How long to wait for a response"
    )
    is_response: bool = Field(
        default=False,
        description="Whether this packet is a response to another"
    )
    
    # Escalation fields
    escalation_reason: Optional[EscalationReason] = Field(
        default=None,
        description="Why this is being escalated (if applicable)"
    )
    escalation_chain: list[str] = Field(
        default_factory=list,
        description="Trail of agents this has been escalated through"
    )
    
    # ==========================================================================
    # METADATA
    # ==========================================================================
    tags: list[str] = Field(
        default_factory=list,
        description="Searchable tags for this packet"
    )
    frameworks: list[str] = Field(
        default_factory=list,
        description="Which wisdom frameworks this relates to"
    )
    
    # Face Configuration (Voice & Expression)
    voice_config: Optional[VoiceConfig] = Field(
        default=None,
        description="Voice and expression configuration for the Face"
    )
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within bounds."""
        return max(0.0, min(1.0, v))
    
    def confidence_level(self) -> ConfidenceLevel:
        """Get human-readable confidence level."""
        if self.confidence_score >= 0.95:
            return ConfidenceLevel.CERTAIN
        elif self.confidence_score >= 0.80:
            return ConfidenceLevel.HIGH
        elif self.confidence_score >= 0.60:
            return ConfidenceLevel.MODERATE
        elif self.confidence_score >= 0.40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.SPECULATION
    
    def needs_probing(self) -> bool:
        """Check if this insight needs more verification."""
        if self.insight_type == InsightType.FACT:
            return False
        if self.hrm_validated and self.confidence_score >= 0.80:
            return False
        return self.confidence_score < 0.80
    
    def to_ui_component(self) -> Optional[dict[str, Any]]:
        """Convert to a generative UI component spec if applicable."""
        if self.insight_type == InsightType.QUESTION:
            probe_payload = ProbePayload(**self.payload) if self.payload else None
            if probe_payload:
                return {
                    "type": probe_payload.probe_type.value,
                    "prompt": probe_payload.prompt,
                    "options": probe_payload.options,
                    "metadata": probe_payload.metadata,
                }
        return None
    
    def with_voice_config(self, config: Optional[VoiceConfig] = None) -> "SovereignPacket":
        """
        Return a copy of this packet with voice configuration attached.
        
        If no config is provided, auto-generates based on insight_type.
        This is the "Adaptive Intelligence" in action.
        """
        if config is None:
            config = VoiceConfig.for_insight_type(self.insight_type)
        
        return self.model_copy(update={"voice_config": config})
    
    def get_expression_hint(self) -> Optional[ExpressionHint]:
        """Get the expression hint for UI rendering."""
        if self.voice_config and self.voice_config.expression:
            return self.voice_config.expression
        # Auto-generate if not set
        auto_config = VoiceConfig.for_insight_type(self.insight_type)
        return auto_config.expression
    
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "packet_id": self.packet_id,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "target_layer": self.target_layer.value,
            "priority": self.priority.value,
            "insight_type": self.insight_type.value,
            "confidence_score": self.confidence_score,
            "hrm_validated": self.hrm_validated,
            "hrm_reasoning_trace": self.hrm_reasoning_trace,
            "payload": self.payload,
            "session_id": self.session_id,
            "parent_packet_id": self.parent_packet_id,
            "conversation_turn": self.conversation_turn,
            "tags": self.tags,
            "frameworks": self.frameworks,
        }
        if self.voice_config:
            result["voice_config"] = {
                "voice_id": self.voice_config.voice_id.value,
                "intensity": self.voice_config.intensity,
                "warmth": self.voice_config.warmth,
                "mystery": self.voice_config.mystery,
            }
            if self.voice_config.expression:
                result["voice_config"]["expression"] = {
                    "pulse_color": self.voice_config.expression.pulse_color,
                    "secondary_color": self.voice_config.expression.secondary_color,
                    "intensity": self.voice_config.expression.intensity,
                    "pulse_speed": self.voice_config.expression.pulse_speed,
                    "mood": self.voice_config.expression.mood,
                }
        return result


# =============================================================================
# FACTORY FUNCTIONS - Convenient Packet Creation
# =============================================================================

def create_packet(
    source_agent: str,
    insight_type: InsightType,
    payload: dict[str, Any],
    confidence: float = 0.5,
    target_layer: TargetLayer = TargetLayer.ORCHESTRATOR,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a generic SovereignPacket with sensible defaults."""
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=target_layer,
        insight_type=insight_type,
        confidence_score=confidence,
        payload=payload,
        session_id=session_id,
        **kwargs
    )


def create_probe_packet(
    source_agent: str,
    probe_type: ProbeType,
    prompt: str,
    options: Optional[list[str]] = None,
    resolves_trait: Optional[str] = None,
    expected_values: Optional[dict[str, str]] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a packet requesting user input via UI probe."""
    probe = ProbePayload(
        probe_type=probe_type,
        prompt=prompt,
        options=options,
        resolves_trait=resolves_trait,
        expected_values=expected_values,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.UI,
        insight_type=InsightType.QUESTION,
        confidence_score=1.0,  # Probes are certain about what they're asking
        payload=probe.model_dump(),
        session_id=session_id,
        priority=PacketPriority.HIGH,
        **kwargs
    )


def create_hypothesis_packet(
    source_agent: str,
    trait_name: str,
    suspected_value: str,
    confidence: float,
    evidence: list[str],
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a packet representing an unverified hypothesis about the user."""
    hypothesis = HypothesisPayload(
        trait_name=trait_name,
        suspected_value=suspected_value,
        confidence=confidence,
        evidence=evidence,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.LOGIC,
        insight_type=InsightType.HYPOTHESIS,
        confidence_score=confidence,
        payload=hypothesis.model_dump(),
        session_id=session_id,
        **kwargs
    )


def create_insight_packet(
    source_agent: str,
    pattern_name: str,
    pattern_category: str,
    indicators: list[str],
    strength: float,
    framework: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a packet for a detected pattern/insight."""
    pattern = PatternPayload(
        pattern_name=pattern_name,
        pattern_category=pattern_category,
        indicators=indicators,
        strength=strength,
        framework=framework,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.PATTERN,
        confidence_score=strength,
        payload=pattern.model_dump(),
        session_id=session_id,
        frameworks=[framework] if framework else [],
        **kwargs
    )


def create_synthesis_packet(
    source_agent: str,
    title: str,
    summary: str,
    source_agents: list[str],
    source_insights: list[str],
    frameworks_used: list[str],
    key_findings: list[str],
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a packet for synthesized multi-source insights."""
    synthesis = SynthesisPayload(
        title=title,
        summary=summary,
        source_agents=source_agents,
        source_insights=source_insights,
        frameworks_used=frameworks_used,
        key_findings=key_findings,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.MEMORY,
        insight_type=InsightType.SYNTHESIS,
        confidence_score=0.85,  # Syntheses are generally high confidence
        payload=synthesis.model_dump(),
        session_id=session_id,
        frameworks=frameworks_used,
        priority=PacketPriority.HIGH,
        **kwargs
    )


def create_tool_call_packet(
    source_agent: str,
    tool_name: str,
    arguments: dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create a packet requesting tool invocation."""
    tool_call = ToolCallPayload(
        tool_name=tool_name,
        arguments=arguments,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.TOOL_CALL,
        confidence_score=1.0,
        payload=tool_call.model_dump(),
        session_id=session_id,
        **kwargs
    )


def create_alert_packet(
    source_agent: str,
    alert_type: Literal["error", "warning", "info", "success"],
    title: str,
    message: str,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """Create an alert packet for urgent notifications."""
    alert = AlertPayload(
        alert_type=alert_type,
        title=title,
        message=message,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_layer=TargetLayer.UI,
        insight_type=InsightType.ALERT,
        confidence_score=1.0,
        payload=alert.model_dump(),
        session_id=session_id,
        priority=PacketPriority.CRITICAL if alert_type == "error" else PacketPriority.HIGH,
        **kwargs
    )


# =============================================================================
# BIDIRECTIONAL COMMUNICATION FACTORY FUNCTIONS
# =============================================================================

def create_escalation_packet(
    source_agent: str,
    source_domain: str,
    reason: EscalationReason,
    description: str,
    current_state: dict[str, Any],
    confidence: float = 0.5,
    needs_from_parent: Optional[list[str]] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create an escalation packet for child → parent communication.
    
    Use when a sub-agent needs help, context, or a decision.
    """
    escalation = EscalationPayload(
        reason=reason,
        description=description,
        current_state=current_state,
        confidence=confidence,
        needs_from_parent=needs_from_parent or [],
    )
    return SovereignPacket(
        source_agent=source_agent,
        source_domain=source_domain,
        source_tier=AgentHierarchyTier.SUB,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.HYPOTHESIS,
        message_type=MessageType.ESCALATION,
        routing_intent=RoutingIntent.TIER,
        confidence_score=confidence,
        payload=escalation.model_dump(),
        escalation_reason=reason,
        session_id=session_id,
        priority=PacketPriority.HIGH,
        expects_response=True,
        **kwargs
    )


def create_delegation_packet(
    source_agent: str,
    source_tier: AgentHierarchyTier,
    target_domain: str,
    target_capability: str,
    task_type: str,
    instructions: str,
    input_data: dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create a delegation packet for parent → child communication.
    
    Use when a master or orchestrator needs specialized work done.
    """
    delegation = DelegationPayload(
        task_type=task_type,
        instructions=instructions,
        input_data=input_data,
    )
    return SovereignPacket(
        source_agent=source_agent,
        source_tier=source_tier,
        target_domain=target_domain,
        target_capability=target_capability,
        target_layer=TargetLayer.GENESIS,  # Will be overridden by routing
        insight_type=InsightType.TOOL_CALL,
        message_type=MessageType.DELEGATION,
        routing_intent=RoutingIntent.CAPABILITY,
        confidence_score=1.0,
        payload=delegation.model_dump(),
        session_id=session_id,
        expects_response=True,
        **kwargs
    )


def create_cross_domain_request(
    source_agent: str,
    source_domain: str,
    target_domain: str,
    request_type: str,
    query: str,
    parameters: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create a cross-domain request packet for sibling communication.
    
    Use when one domain needs information or validation from another.
    """
    cross_domain = CrossDomainRequestPayload(
        requesting_domain=source_domain,
        target_domain=target_domain,
        request_type=request_type,
        query=query,
        parameters=parameters or {},
        requester_context=context or {},
    )
    return SovereignPacket(
        source_agent=source_agent,
        source_domain=source_domain,
        target_domain=target_domain,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.QUESTION,
        message_type=MessageType.REQUEST,
        routing_intent=RoutingIntent.DOMAIN,
        confidence_score=1.0,
        payload=cross_domain.model_dump(),
        session_id=session_id,
        expects_response=True,
        correlation_id=str(uuid4()),
        **kwargs
    )


def create_broadcast_packet(
    source_agent: str,
    source_domain: str,
    broadcast_type: Literal["announcement", "update", "alert", "discovery"],
    title: str,
    message: str,
    target_domains: Optional[list[str]] = None,
    target_tiers: Optional[list[AgentHierarchyTier]] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create a broadcast packet for one-to-many communication.
    
    Use for announcements, discoveries, or alerts that multiple agents need.
    """
    broadcast = BroadcastPayload(
        broadcast_type=broadcast_type,
        title=title,
        message=message,
        target_domains=target_domains,
        target_tiers=target_tiers,
    )
    return SovereignPacket(
        source_agent=source_agent,
        source_domain=source_domain,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.ALERT if broadcast_type == "alert" else InsightType.SUGGESTION,
        message_type=MessageType.BROADCAST,
        routing_intent=RoutingIntent.DOMAIN if target_domains else RoutingIntent.TIER,
        confidence_score=1.0,
        payload=broadcast.model_dump(),
        session_id=session_id,
        expects_response=False,
        **kwargs
    )


def create_response_packet(
    original_packet: SovereignPacket,
    source_agent: str,
    success: bool,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    confidence: Optional[float] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create a response packet to a request.
    
    Use when responding to any packet with expects_response=True.
    """
    response = ResponsePayload(
        success=success,
        result=result,
        error=error,
        confidence=confidence,
    )
    return SovereignPacket(
        source_agent=source_agent,
        target_agent=original_packet.source_agent,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=original_packet.insight_type,
        message_type=MessageType.RESPONSE,
        routing_intent=RoutingIntent.DIRECT,
        confidence_score=confidence or 1.0,
        payload=response.model_dump(),
        session_id=original_packet.session_id,
        correlation_id=original_packet.correlation_id or original_packet.packet_id,
        causation_id=original_packet.packet_id,
        is_response=True,
        **kwargs
    )


def create_subscription_packet(
    source_agent: str,
    source_domain: str,
    action: Literal["subscribe", "unsubscribe", "list"],
    insight_types: Optional[list[InsightType]] = None,
    source_domains: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    min_confidence: Optional[float] = None,
    **kwargs
) -> SovereignPacket:
    """
    Create a subscription management packet.
    
    Use when an agent wants to receive certain types of packets.
    """
    subscription = SubscriptionPayload(
        action=action,
        insight_types=insight_types,
        source_domains=source_domains,
        tags=tags,
        min_confidence=min_confidence,
    )
    return SovereignPacket(
        source_agent=source_agent,
        source_domain=source_domain,
        target_layer=TargetLayer.ORCHESTRATOR,
        insight_type=InsightType.TOOL_CALL,
        message_type=MessageType.SUBSCRIPTION,
        routing_intent=RoutingIntent.DIRECT,
        confidence_score=1.0,
        payload=subscription.model_dump(),
        **kwargs
    )
