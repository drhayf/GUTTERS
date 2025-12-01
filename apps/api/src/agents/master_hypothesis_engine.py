"""
Master Hypothesis Engine - Cross-Domain Hypothesis Coordinator

This module implements the MASTER-tier hypothesis engine that aggregates,
correlates, and coordinates hypotheses from ALL domains in the system.

Architecture Position:
━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────┐
    │   ORCHESTRATOR  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ MASTER HYPOTHESIS│  ◄── THIS MODULE
    │     ENGINE      │
    └────────┬────────┘
             │
    ┌────────┴────────┬───────────────┬───────────────┐
    ▼                 ▼               ▼               ▼
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ GENESIS │     │ VISION  │     │ FINANCE │     │ HEALTH  │
│hypothesis│     │hypothesis│     │hypothesis│     │hypothesis│
└─────────┘     └─────────┘     └─────────┘     └─────────┘

Responsibilities:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. AGGREGATE: Collect hypotheses from all domain-level hypothesis engines
2. CORRELATE: Find cross-domain patterns (e.g., health affecting finance decisions)
3. RESOLVE CONFLICTS: When domains have contradicting hypotheses
4. ESCALATE: Send truly uncertain cases to the Orchestrator
5. DELEGATE: Request specific probes from domain agents
6. BROADCAST: Share validated insights with all domains

Cross-Domain Intelligence Examples:
━━━━━━━━━━━━━━━━━━━━━━━━━
- Genesis detects "morning fog" pattern, Vision sees late-night eating → correlate to circadian rhythm
- Finance notices impulsive spending, Health sees cortisol spike → correlate to stress response
- Genesis suspects Projector type, but Vision sees highly energetic behavior → need resolution

Escalation Criteria:
━━━━━━━━━━━━━━━━━━━━━━━━━
- Cross-domain conflict that can't be resolved
- Pattern that requires user input to validate
- Discovery of system-wide significance
- Confidence remains low after cross-domain correlation
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from enum import Enum
import asyncio
import logging

from ..shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    PacketPriority,
    MessageType,
    RoutingIntent,
    EscalationReason,
    AgentHierarchyTier,
    ConfidenceLevel,
    HypothesisPayload,
    create_escalation_packet,
    create_delegation_packet,
    create_broadcast_packet,
    create_response_packet,
)
from ..core.swarm_bus import (
    SwarmBus,
    SwarmEnvelope,
    AgentTier,
    get_bus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class HypothesisStatus(str, Enum):
    """Status of a hypothesis in the master engine."""
    PENDING = "pending"           # Just received, not yet processed
    CORRELATING = "correlating"   # Looking for cross-domain connections
    PROBING = "probing"           # Requested additional probes
    VALIDATED = "validated"       # Confirmed with high confidence
    REJECTED = "rejected"         # Disproven
    CONFLICT = "conflict"         # Contradicts another hypothesis
    ESCALATED = "escalated"       # Sent to orchestrator


@dataclass
class CrossDomainHypothesis:
    """
    A hypothesis being tracked across multiple domains.
    
    This represents a unified view of what we think we know about
    the user, aggregating evidence from multiple sources.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Core identification
    trait_name: str = ""
    trait_category: str = ""  # e.g., "personality", "health", "behavior"
    suspected_value: str = ""
    
    # Confidence tracking
    confidence: float = 0.5
    confidence_by_domain: Dict[str, float] = field(default_factory=dict)
    
    # Evidence from all domains
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Source tracking
    source_domains: Set[str] = field(default_factory=set)
    source_packets: List[str] = field(default_factory=list)
    
    # Status
    status: HypothesisStatus = HypothesisStatus.PENDING
    
    # Probing
    probes_sent: int = 0
    max_probes: int = 5
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Correlations
    correlated_hypotheses: List[str] = field(default_factory=list)
    
    def update_confidence(self) -> None:
        """Recalculate confidence based on all domain contributions."""
        if not self.confidence_by_domain:
            return
        
        # Weight by number of evidence pieces per domain
        total_weight = 0.0
        weighted_sum = 0.0
        
        for domain, conf in self.confidence_by_domain.items():
            domain_evidence = len([e for e in self.evidence if e.get("domain") == domain])
            weight = max(1, domain_evidence)
            weighted_sum += conf * weight
            total_weight += weight
        
        if total_weight > 0:
            self.confidence = weighted_sum / total_weight
        
        # Adjust for contradictions
        contradiction_penalty = len(self.contradictions) * 0.05
        self.confidence = max(0.1, self.confidence - contradiction_penalty)
        
        self.updated_at = datetime.utcnow()
    
    def add_evidence(self, domain: str, evidence: str, confidence: float) -> None:
        """Add evidence from a domain."""
        self.evidence.append({
            "domain": domain,
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.source_domains.add(domain)
        
        # Update domain confidence
        if domain in self.confidence_by_domain:
            # Weighted average with new evidence
            old_conf = self.confidence_by_domain[domain]
            self.confidence_by_domain[domain] = (old_conf + confidence) / 2
        else:
            self.confidence_by_domain[domain] = confidence
        
        self.update_confidence()
    
    def add_contradiction(self, domain: str, contradiction: str, strength: float) -> None:
        """Add contradicting evidence."""
        self.contradictions.append({
            "domain": domain,
            "contradiction": contradiction,
            "strength": strength,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.update_confidence()
    
    def confidence_level(self) -> ConfidenceLevel:
        """Get human-readable confidence level."""
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
    
    def needs_resolution(self) -> bool:
        """Check if this hypothesis needs more work."""
        return (
            self.status in [HypothesisStatus.PENDING, HypothesisStatus.CORRELATING] and
            self.confidence < 0.80 and
            self.probes_sent < self.max_probes
        )
    
    def has_conflict(self) -> bool:
        """Check if there are significant contradictions."""
        return len(self.contradictions) > 0 and any(
            c.get("strength", 0) > 0.5 for c in self.contradictions
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trait_name": self.trait_name,
            "trait_category": self.trait_category,
            "suspected_value": self.suspected_value,
            "confidence": self.confidence,
            "confidence_by_domain": self.confidence_by_domain,
            "evidence_count": len(self.evidence),
            "contradiction_count": len(self.contradictions),
            "source_domains": list(self.source_domains),
            "status": self.status.value,
            "confidence_level": self.confidence_level().value,
            "probes_sent": self.probes_sent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DomainState:
    """Tracks the state of a domain for coordination."""
    domain_name: str
    agent_id: str
    last_seen: datetime = field(default_factory=datetime.utcnow)
    hypothesis_count: int = 0
    pending_probes: int = 0
    capabilities: List[str] = field(default_factory=list)
    active: bool = True


# =============================================================================
# MASTER HYPOTHESIS ENGINE
# =============================================================================

class MasterHypothesisEngine:
    """
    The Cross-Domain Hypothesis Coordinator.
    
    This is a MASTER-tier agent that sits above domain-level hypothesis
    engines and coordinates cross-domain intelligence.
    
    Key Behaviors:
    - Receives escalations from domain hypothesis engines
    - Correlates hypotheses across domains
    - Resolves conflicts between domains
    - Escalates truly uncertain cases to Orchestrator
    - Broadcasts validated insights to all domains
    
    Usage:
        engine = MasterHypothesisEngine()
        await engine.start()
        
        # It will automatically receive and process escalations
        # via the SwarmBus subscription
        
        # Manual hypothesis submission
        await engine.submit_hypothesis(packet)
        
        # Get status
        status = engine.get_status()
    """
    
    AGENT_ID = "master.hypothesis"
    AGENT_TIER = AgentTier.MASTER
    DOMAIN = "meta"  # Meta-domain for cross-domain agents
    
    def __init__(self):
        # Hypothesis storage
        self._hypotheses: Dict[str, CrossDomainHypothesis] = {}
        
        # Trait-based index for correlation
        self._trait_index: Dict[str, Set[str]] = {}  # trait_name → hypothesis_ids
        
        # Domain tracking
        self._domains: Dict[str, DomainState] = {}
        
        # Bus integration
        self._bus: Optional[SwarmBus] = None
        self._running = False
        
        # Correlation patterns
        self._correlation_rules: List[Dict[str, Any]] = []
        
        # Statistics
        self._stats = {
            "hypotheses_received": 0,
            "hypotheses_validated": 0,
            "hypotheses_rejected": 0,
            "conflicts_resolved": 0,
            "escalations_sent": 0,
            "correlations_found": 0,
        }
        
        # Load correlation rules
        self._load_correlation_rules()
        
        logger.info(f"[{self.AGENT_ID}] Initialized")
    
    def _load_correlation_rules(self) -> None:
        """Load rules for cross-domain correlation."""
        # These rules define how hypotheses from different domains relate
        self._correlation_rules = [
            {
                "name": "energy_food_correlation",
                "description": "Correlate energy patterns with eating habits",
                "source_trait": "energy_pattern",
                "target_trait": "eating_pattern",
                "domains": ["genesis", "vision"],
                "correlation_type": "causation",
            },
            {
                "name": "stress_spending_correlation",
                "description": "Correlate stress patterns with spending behavior",
                "source_trait": "stress_pattern",
                "target_trait": "spending_pattern",
                "domains": ["health", "finance"],
                "correlation_type": "correlation",
            },
            {
                "name": "sleep_productivity_correlation",
                "description": "Correlate sleep quality with productivity",
                "source_trait": "sleep_pattern",
                "target_trait": "productivity_pattern",
                "domains": ["health", "genesis"],
                "correlation_type": "causation",
            },
            {
                "name": "personality_behavior_validation",
                "description": "Validate personality type with observed behavior",
                "source_trait": "human_design_type",
                "target_trait": "behavioral_pattern",
                "domains": ["genesis", "vision"],
                "correlation_type": "validation",
            },
        ]
    
    async def start(self) -> None:
        """Start the master hypothesis engine and subscribe to the bus."""
        if self._running:
            return
        
        self._bus = await get_bus()
        
        # Subscribe to receive escalations
        await self._bus.subscribe(
            agent_id=self.AGENT_ID,
            handler=self._handle_envelope,
            agent_tier=self.AGENT_TIER,
            domain=self.DOMAIN,
            capability="hypothesis",
        )
        
        self._running = True
        logger.info(f"[{self.AGENT_ID}] Started and subscribed to SwarmBus")
    
    async def stop(self) -> None:
        """Stop the engine and unsubscribe."""
        if not self._running:
            return
        
        if self._bus:
            await self._bus.unsubscribe(self.AGENT_ID)
        
        self._running = False
        logger.info(f"[{self.AGENT_ID}] Stopped")
    
    async def _handle_envelope(self, envelope: SwarmEnvelope) -> Optional[Dict]:
        """Handle incoming envelopes from the SwarmBus."""
        logger.debug(f"[{self.AGENT_ID}] Received envelope: {envelope.id}")
        
        packet = envelope.packet
        if not packet:
            # Handle raw payload
            if "hypothesis" in envelope.payload or "trait_name" in envelope.payload:
                return await self._handle_hypothesis_submission(envelope)
            return {"error": "No packet or valid payload"}
        
        # Route based on message type
        if envelope.routing_pattern.value == "escalation":
            return await self._handle_escalation(envelope, packet)
        elif packet.insight_type == InsightType.HYPOTHESIS:
            return await self._handle_hypothesis_packet(envelope, packet)
        elif packet.insight_type == InsightType.PATTERN:
            return await self._handle_pattern_packet(envelope, packet)
        else:
            logger.warning(f"[{self.AGENT_ID}] Unhandled packet type: {packet.insight_type}")
            return {"status": "ignored", "reason": "unhandled_type"}
    
    async def _handle_escalation(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Handle an escalation from a domain hypothesis engine."""
        logger.info(f"[{self.AGENT_ID}] Handling escalation from {packet.source_agent}")
        
        reason = packet.escalation_reason
        payload = packet.payload
        
        if reason == EscalationReason.CONFIDENCE_LOW:
            # Try cross-domain correlation to boost confidence
            return await self._correlate_and_respond(envelope, packet)
        
        elif reason == EscalationReason.CONFLICT:
            # Attempt to resolve conflict
            return await self._resolve_conflict(envelope, packet)
        
        elif reason == EscalationReason.NEED_CONTEXT:
            # Request context from other domains
            return await self._gather_cross_domain_context(envelope, packet)
        
        elif reason == EscalationReason.DISCOVERY:
            # Major discovery - broadcast to all domains
            return await self._broadcast_discovery(envelope, packet)
        
        else:
            # Escalate to orchestrator
            return await self._escalate_to_orchestrator(envelope, packet)
    
    async def _handle_hypothesis_packet(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Process an incoming hypothesis packet."""
        self._stats["hypotheses_received"] += 1
        
        # Extract hypothesis data
        trait_name = packet.payload.get("trait_name", "unknown")
        suspected_value = packet.payload.get("suspected_value", "unknown")
        confidence = packet.confidence_score
        evidence = packet.payload.get("evidence", [])
        source_domain = packet.source_domain or packet.source_agent.split(".")[0]
        
        # Find or create cross-domain hypothesis
        hypo = self._find_or_create_hypothesis(trait_name, suspected_value)
        
        # Add evidence from this domain
        for e in evidence:
            hypo.add_evidence(source_domain, e, confidence)
        
        hypo.source_packets.append(packet.packet_id)
        
        # Try correlation
        correlations = await self._find_correlations(hypo)
        if correlations:
            self._stats["correlations_found"] += len(correlations)
            hypo.correlated_hypotheses.extend([c["id"] for c in correlations])
        
        # Check if we can validate
        if hypo.confidence >= 0.80:
            hypo.status = HypothesisStatus.VALIDATED
            self._stats["hypotheses_validated"] += 1
            await self._broadcast_validation(hypo)
        elif hypo.has_conflict():
            hypo.status = HypothesisStatus.CONFLICT
        elif hypo.needs_resolution():
            hypo.status = HypothesisStatus.PROBING
            await self._request_probes(hypo)
        
        return {
            "status": "processed",
            "hypothesis_id": hypo.id,
            "confidence": hypo.confidence,
            "status_after": hypo.status.value,
        }
    
    async def _handle_pattern_packet(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Process a pattern detection packet."""
        # Convert pattern to hypothesis for tracking
        pattern_name = packet.payload.get("pattern_name", "unknown")
        pattern_category = packet.payload.get("pattern_category", "behavior")
        strength = packet.payload.get("strength", packet.confidence_score)
        
        hypo = self._find_or_create_hypothesis(pattern_name, "detected")
        hypo.trait_category = pattern_category
        
        source_domain = packet.source_domain or packet.source_agent.split(".")[0]
        indicators = packet.payload.get("indicators", [])
        
        for indicator in indicators:
            hypo.add_evidence(source_domain, indicator, strength)
        
        return {
            "status": "pattern_tracked",
            "hypothesis_id": hypo.id,
            "confidence": hypo.confidence,
        }
    
    async def _handle_hypothesis_submission(self, envelope: SwarmEnvelope) -> Dict:
        """Handle direct hypothesis submission without SovereignPacket wrapper."""
        payload = envelope.payload
        
        trait_name = payload.get("trait_name", "unknown")
        suspected_value = payload.get("suspected_value", "unknown")
        confidence = payload.get("confidence", 0.5)
        evidence = payload.get("evidence", [])
        domain = envelope.payload.get("domain", "unknown")
        
        hypo = self._find_or_create_hypothesis(trait_name, suspected_value)
        
        for e in evidence:
            if isinstance(e, str):
                hypo.add_evidence(domain, e, confidence)
            elif isinstance(e, dict):
                hypo.add_evidence(
                    e.get("domain", domain),
                    e.get("evidence", str(e)),
                    e.get("confidence", confidence)
                )
        
        return {
            "status": "submitted",
            "hypothesis_id": hypo.id,
            "confidence": hypo.confidence,
        }
    
    def _find_or_create_hypothesis(
        self, 
        trait_name: str, 
        suspected_value: str
    ) -> CrossDomainHypothesis:
        """Find existing or create new cross-domain hypothesis."""
        # Check trait index
        if trait_name in self._trait_index:
            for hypo_id in self._trait_index[trait_name]:
                hypo = self._hypotheses.get(hypo_id)
                if hypo and hypo.suspected_value == suspected_value:
                    return hypo
        
        # Create new
        hypo = CrossDomainHypothesis(
            trait_name=trait_name,
            suspected_value=suspected_value,
        )
        
        self._hypotheses[hypo.id] = hypo
        
        # Update index
        if trait_name not in self._trait_index:
            self._trait_index[trait_name] = set()
        self._trait_index[trait_name].add(hypo.id)
        
        return hypo
    
    async def _find_correlations(
        self, 
        hypo: CrossDomainHypothesis
    ) -> List[Dict[str, Any]]:
        """Find hypotheses that correlate with this one."""
        correlations = []
        
        for rule in self._correlation_rules:
            # Check if this hypothesis matches a source trait
            if hypo.trait_name != rule["source_trait"]:
                continue
            
            # Look for target trait hypotheses
            target_trait = rule["target_trait"]
            if target_trait in self._trait_index:
                for target_id in self._trait_index[target_trait]:
                    target_hypo = self._hypotheses.get(target_id)
                    if not target_hypo:
                        continue
                    
                    # Check domain overlap
                    domain_overlap = hypo.source_domains & target_hypo.source_domains
                    
                    correlations.append({
                        "id": target_id,
                        "trait_name": target_trait,
                        "correlation_type": rule["correlation_type"],
                        "rule_name": rule["name"],
                        "domain_overlap": list(domain_overlap),
                    })
        
        return correlations
    
    async def _correlate_and_respond(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Try cross-domain correlation to boost confidence."""
        trait_name = packet.payload.get("trait_name", "unknown")
        suspected_value = packet.payload.get("suspected_value", "unknown")
        
        hypo = self._find_or_create_hypothesis(trait_name, suspected_value)
        
        # Apply correlation boost
        correlations = await self._find_correlations(hypo)
        
        correlation_boost = 0.0
        for corr in correlations:
            corr_hypo = self._hypotheses.get(corr["id"])
            if corr_hypo and corr_hypo.confidence >= 0.70:
                correlation_boost += 0.05  # Small boost per correlation
        
        hypo.confidence = min(0.95, hypo.confidence + correlation_boost)
        hypo.update_confidence()
        
        return {
            "status": "correlated",
            "hypothesis_id": hypo.id,
            "new_confidence": hypo.confidence,
            "correlations_found": len(correlations),
            "boost_applied": correlation_boost,
        }
    
    async def _resolve_conflict(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Attempt to resolve conflicting hypotheses."""
        # Get the conflicting hypotheses
        conflict_data = packet.payload.get("conflict", {})
        hypothesis_a = conflict_data.get("hypothesis_a")
        hypothesis_b = conflict_data.get("hypothesis_b")
        
        if not hypothesis_a or not hypothesis_b:
            return {"status": "error", "message": "Missing conflict data"}
        
        # Resolution strategies:
        # 1. Higher confidence wins
        # 2. More evidence wins
        # 3. More domains wins
        # 4. Escalate if unclear
        
        hypo_a = self._hypotheses.get(hypothesis_a)
        hypo_b = self._hypotheses.get(hypothesis_b)
        
        if not hypo_a or not hypo_b:
            return {"status": "error", "message": "Hypotheses not found"}
        
        winner = None
        reason = ""
        
        # Compare confidence
        if abs(hypo_a.confidence - hypo_b.confidence) > 0.15:
            winner = hypo_a if hypo_a.confidence > hypo_b.confidence else hypo_b
            reason = "higher_confidence"
        # Compare evidence
        elif abs(len(hypo_a.evidence) - len(hypo_b.evidence)) > 2:
            winner = hypo_a if len(hypo_a.evidence) > len(hypo_b.evidence) else hypo_b
            reason = "more_evidence"
        # Compare domain coverage
        elif len(hypo_a.source_domains) != len(hypo_b.source_domains):
            winner = hypo_a if len(hypo_a.source_domains) > len(hypo_b.source_domains) else hypo_b
            reason = "more_domains"
        else:
            # Can't resolve - escalate
            return await self._escalate_to_orchestrator(envelope, packet)
        
        # Mark winner and loser
        winner.status = HypothesisStatus.VALIDATED
        loser = hypo_a if winner == hypo_b else hypo_b
        loser.status = HypothesisStatus.REJECTED
        
        self._stats["conflicts_resolved"] += 1
        
        return {
            "status": "resolved",
            "winner": winner.id,
            "loser": loser.id,
            "reason": reason,
        }
    
    async def _gather_cross_domain_context(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Request context from other domains."""
        needed_context = packet.payload.get("needed_context", [])
        requesting_domain = packet.source_domain or packet.source_agent.split(".")[0]
        
        if not self._bus:
            return {"status": "error", "message": "SwarmBus not available"}
        
        # Send context requests to other domains
        responses = []
        for ctx in needed_context:
            target_domain = ctx.get("domain")
            if target_domain == requesting_domain:
                continue
            
            # Request context via bus
            await self._bus.send(
                source_agent_id=self.AGENT_ID,
                target_domain=target_domain,
                payload={
                    "request_type": "context",
                    "query": ctx.get("query", ""),
                    "for_hypothesis": ctx.get("hypothesis_id"),
                },
                priority=PacketPriority.HIGH,
                expects_response=True,
            )
            responses.append(target_domain)
        
        return {
            "status": "context_requested",
            "domains_queried": responses,
        }
    
    async def _broadcast_discovery(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Broadcast a significant discovery to all domains."""
        if not self._bus:
            return {"status": "error", "message": "SwarmBus not available"}
        
        await self._bus.broadcast(
            source_agent_id=self.AGENT_ID,
            payload={
                "discovery_type": packet.payload.get("discovery_type", "insight"),
                "discovery": packet.payload.get("discovery"),
                "confidence": packet.confidence_score,
                "source_domain": packet.source_domain,
            },
            priority=PacketPriority.HIGH,
        )
        
        return {"status": "broadcast_sent"}
    
    async def _broadcast_validation(self, hypo: CrossDomainHypothesis) -> None:
        """Broadcast a validated hypothesis to all domains."""
        if not self._bus:
            return
        
        await self._bus.broadcast(
            source_agent_id=self.AGENT_ID,
            payload={
                "validation_type": "hypothesis_confirmed",
                "trait_name": hypo.trait_name,
                "confirmed_value": hypo.suspected_value,
                "confidence": hypo.confidence,
                "source_domains": list(hypo.source_domains),
            },
            priority=PacketPriority.NORMAL,
        )
    
    async def _request_probes(self, hypo: CrossDomainHypothesis) -> None:
        """Request additional probes to resolve a hypothesis."""
        if not self._bus or hypo.probes_sent >= hypo.max_probes:
            return
        
        # Determine which domains haven't contributed yet
        all_domains = set(self._domains.keys())
        missing_domains = all_domains - hypo.source_domains
        
        for domain in missing_domains:
            await self._bus.delegate(
                source_agent_id=self.AGENT_ID,
                target_capability="hypothesis",
                target_domain=domain,
                payload={
                    "task": "probe_for_hypothesis",
                    "trait_name": hypo.trait_name,
                    "suspected_value": hypo.suspected_value,
                    "current_confidence": hypo.confidence,
                },
            )
            hypo.probes_sent += 1
    
    async def _escalate_to_orchestrator(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Escalate to the orchestrator when we can't resolve."""
        if not self._bus:
            return {"status": "error", "message": "SwarmBus not available"}
        
        self._stats["escalations_sent"] += 1
        
        await self._bus.escalate(
            source_agent_id=self.AGENT_ID,
            payload={
                "original_packet": packet.as_dict() if hasattr(packet, 'as_dict') else packet.model_dump(),
                "reason": "master_cannot_resolve",
                "attempts": [
                    "cross_domain_correlation",
                    "conflict_resolution",
                    "context_gathering",
                ],
            },
            reason="stuck",
            priority=PacketPriority.HIGH,
        )
        
        return {"status": "escalated_to_orchestrator"}
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    async def submit_hypothesis(self, packet: SovereignPacket) -> Dict[str, Any]:
        """
        Submit a hypothesis directly for processing.
        
        This is an alternative to SwarmBus delivery for direct calls.
        """
        # Create a mock envelope
        envelope = SwarmEnvelope(
            source_agent_id=packet.source_agent,
            payload=packet.payload,
            packet=packet,
        )
        return await self._handle_hypothesis_packet(envelope, packet)
    
    def get_hypothesis(self, hypothesis_id: str) -> Optional[CrossDomainHypothesis]:
        """Get a hypothesis by ID."""
        return self._hypotheses.get(hypothesis_id)
    
    def get_hypotheses_by_trait(self, trait_name: str) -> List[CrossDomainHypothesis]:
        """Get all hypotheses for a trait."""
        ids = self._trait_index.get(trait_name, set())
        return [self._hypotheses[id] for id in ids if id in self._hypotheses]
    
    def get_validated_hypotheses(self) -> List[CrossDomainHypothesis]:
        """Get all validated hypotheses."""
        return [
            h for h in self._hypotheses.values()
            if h.status == HypothesisStatus.VALIDATED
        ]
    
    def get_pending_hypotheses(self) -> List[CrossDomainHypothesis]:
        """Get hypotheses still needing resolution."""
        return [
            h for h in self._hypotheses.values()
            if h.needs_resolution()
        ]
    
    def register_domain(
        self, 
        domain_name: str, 
        agent_id: str, 
        capabilities: Optional[List[str]] = None
    ) -> None:
        """Register a domain for coordination."""
        self._domains[domain_name] = DomainState(
            domain_name=domain_name,
            agent_id=agent_id,
            capabilities=capabilities or ["hypothesis"],
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the master hypothesis engine."""
        return {
            "agent_id": self.AGENT_ID,
            "running": self._running,
            "stats": self._stats,
            "hypotheses": {
                "total": len(self._hypotheses),
                "validated": len(self.get_validated_hypotheses()),
                "pending": len(self.get_pending_hypotheses()),
                "by_status": {
                    status.value: len([
                        h for h in self._hypotheses.values()
                        if h.status == status
                    ])
                    for status in HypothesisStatus
                },
            },
            "domains": {
                name: {
                    "agent_id": state.agent_id,
                    "active": state.active,
                    "last_seen": state.last_seen.isoformat(),
                }
                for name, state in self._domains.items()
            },
            "correlation_rules": len(self._correlation_rules),
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

_master_engine: Optional[MasterHypothesisEngine] = None


async def get_master_hypothesis_engine() -> MasterHypothesisEngine:
    """Get or create the singleton MasterHypothesisEngine."""
    global _master_engine
    if _master_engine is None:
        _master_engine = MasterHypothesisEngine()
        await _master_engine.start()
    return _master_engine
