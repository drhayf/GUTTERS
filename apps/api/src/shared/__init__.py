"""
Shared modules for cross-agent communication and system-wide protocols.

This package contains:
- protocol.py: The Universal "Sovereign Packet" schema for inter-agent communication
- memory.py: RAG/Vector memory interface (future)
- tools.py: Shared tool definitions for generative UI

Enhanced Protocol (v2.0):
- Bidirectional communication (request/response)
- Escalation paths (child → parent)
- Delegation patterns (parent → child)
- Cross-domain coordination
- Subscription-based messaging
"""

from .protocol import (
    # Core Packet
    SovereignPacket,
    
    # Classification Enums
    InsightType,
    TargetLayer,
    AgentCapability,
    ProbeType,
    ConfidenceLevel,
    PacketPriority,
    
    # Bidirectional Communication Enums
    MessageType,
    RoutingIntent,
    EscalationReason,
    AgentHierarchyTier,
    
    # Voice & Expression
    VoiceId,
    VoiceConfig,
    ExpressionHint,
    
    # Payloads
    ProbePayload,
    HypothesisPayload,
    PatternPayload,
    SynthesisPayload,
    ToolCallPayload,
    AlertPayload,
    EscalationPayload,
    DelegationPayload,
    CrossDomainRequestPayload,
    BroadcastPayload,
    SubscriptionPayload,
    ResponsePayload,
    
    # Factory Functions - Core
    create_packet,
    create_probe_packet,
    create_hypothesis_packet,
    create_insight_packet,
    create_synthesis_packet,
    create_tool_call_packet,
    create_alert_packet,
    
    # Factory Functions - Bidirectional
    create_escalation_packet,
    create_delegation_packet,
    create_cross_domain_request,
    create_broadcast_packet,
    create_response_packet,
    create_subscription_packet,
)

__all__ = [
    # Core
    "SovereignPacket",
    "InsightType", 
    "TargetLayer",
    "AgentCapability",
    "ProbeType",
    "ConfidenceLevel",
    "PacketPriority",
    
    # Bidirectional
    "MessageType",
    "RoutingIntent",
    "EscalationReason",
    "AgentHierarchyTier",
    
    # Voice
    "VoiceId",
    "VoiceConfig",
    "ExpressionHint",
    
    # Payloads
    "ProbePayload",
    "HypothesisPayload",
    "PatternPayload",
    "SynthesisPayload",
    "ToolCallPayload",
    "AlertPayload",
    "EscalationPayload",
    "DelegationPayload",
    "CrossDomainRequestPayload",
    "BroadcastPayload",
    "SubscriptionPayload",
    "ResponsePayload",
    
    # Factory Functions
    "create_packet",
    "create_probe_packet",
    "create_hypothesis_packet",
    "create_insight_packet",
    "create_synthesis_packet",
    "create_tool_call_packet",
    "create_alert_packet",
    "create_escalation_packet",
    "create_delegation_packet",
    "create_cross_domain_request",
    "create_broadcast_packet",
    "create_response_packet",
    "create_subscription_packet",
]
