"""
Master Scout - Cross-Domain Pattern & Profile Coordinator

This module implements the MASTER-tier scout that aggregates patterns,
profiles, and user insights from ALL domains into a unified Digital Twin.

Architecture Position:
━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────┐
    │   ORCHESTRATOR  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  MASTER SCOUT   │  ◄── THIS MODULE
    │  (Digital Twin) │
    └────────┬────────┘
             │
    ┌────────┴────────┬───────────────┬───────────────┐
    ▼                 ▼               ▼               ▼
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ GENESIS │     │ VISION  │     │ FINANCE │     │ HEALTH  │
│ profiler│     │ scanner │     │ tracker │     │ monitor │
└─────────┘     └─────────┘     └─────────┘     └─────────┘

Responsibilities:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. AGGREGATE: Collect pattern detections from all domain profilers
2. UNIFY: Build a coherent Digital Twin from disparate insights
3. DETECT MACRO-PATTERNS: Find patterns that span multiple domains
4. MAINTAIN COHERENCE: Ensure the Digital Twin remains consistent
5. PROVIDE CONTEXT: Supply cross-domain context to requesting agents
6. TRACK EVOLUTION: Monitor how the user profile changes over time

The Digital Twin:
━━━━━━━━━━━━━━━━━━━━━━━━━
The Digital Twin is a living, evolving representation of the user:
- Personality traits (Jungian functions, Human Design type)
- Behavioral patterns (energy cycles, decision-making style)
- Health indicators (sleep, stress, nutrition)
- Financial patterns (spending, saving, risk tolerance)
- Relationship dynamics (communication style, attachment)
- Life domains (career, relationships, health, growth)

Cross-Domain Pattern Examples:
━━━━━━━━━━━━━━━━━━━━━━━━━
- "Night Owl Productivity": Late sleep + morning fog + afternoon creativity
- "Stress Spending Cycle": High cortisol + impulsive purchases + guilt pattern
- "Social Recharge Pattern": Introversion + selective socializing + energy restoration
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
from collections import defaultdict
import asyncio
import logging
import json

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
    PatternPayload,
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

class ProfileDomain(str, Enum):
    """Domains of the Digital Twin profile."""
    PERSONALITY = "personality"
    BEHAVIOR = "behavior"
    HEALTH = "health"
    FINANCE = "finance"
    RELATIONSHIPS = "relationships"
    CAREER = "career"
    GROWTH = "growth"
    ENERGY = "energy"
    COGNITION = "cognition"
    EMOTION = "emotion"


class PatternStrength(str, Enum):
    """How strongly a pattern manifests."""
    DOMINANT = "dominant"    # Core defining trait
    STRONG = "strong"        # Very noticeable
    MODERATE = "moderate"    # Regular occurrence
    EMERGING = "emerging"    # Starting to show
    LATENT = "latent"        # Rarely appears


@dataclass
class ProfileTrait:
    """
    A single trait in the Digital Twin profile.
    
    Traits are the atomic units of the profile - individual 
    characteristics that together form the complete picture.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Identity
    name: str = ""
    domain: ProfileDomain = ProfileDomain.PERSONALITY
    category: str = ""  # Sub-category within domain
    
    # Value
    value: Any = None  # Could be string, number, list, etc.
    value_type: str = "string"
    
    # Confidence
    confidence: float = 0.5
    source_count: int = 0  # How many sources contributed
    
    # Sources
    source_domains: Set[str] = field(default_factory=set)
    source_packets: List[str] = field(default_factory=list)
    
    # Timestamps
    first_detected: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Framework associations
    frameworks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain.value,
            "category": self.category,
            "value": self.value,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "source_domains": list(self.source_domains),
            "first_detected": self.first_detected.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "frameworks": self.frameworks,
        }


@dataclass
class MacroPattern:
    """
    A pattern that spans multiple domains.
    
    Macro-patterns are the "big picture" insights that emerge from
    correlating patterns across different life areas.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Identity
    name: str = ""
    description: str = ""
    
    # Components
    contributing_traits: List[str] = field(default_factory=list)
    contributing_domains: Set[str] = field(default_factory=set)
    
    # Strength
    strength: PatternStrength = PatternStrength.EMERGING
    confidence: float = 0.5
    
    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    
    # Implications
    implications: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Timestamps
    first_detected: datetime = field(default_factory=datetime.utcnow)
    last_validated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "contributing_domains": list(self.contributing_domains),
            "trait_count": len(self.contributing_traits),
            "strength": self.strength.value,
            "confidence": self.confidence,
            "implications": self.implications,
            "recommendations": self.recommendations,
            "first_detected": self.first_detected.isoformat(),
            "last_validated": self.last_validated.isoformat(),
        }


@dataclass
class DigitalTwin:
    """
    The complete Digital Twin profile.
    
    This is the living, breathing representation of the user,
    built from all the insights collected across all domains.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Core profile data
    traits: Dict[str, ProfileTrait] = field(default_factory=dict)
    macro_patterns: Dict[str, MacroPattern] = field(default_factory=dict)
    
    # Indices for fast lookup
    _trait_by_domain: Dict[ProfileDomain, Set[str]] = field(default_factory=lambda: defaultdict(set))
    _trait_by_name: Dict[str, str] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Statistics
    total_insights_processed: int = 0
    domains_active: Set[str] = field(default_factory=set)
    
    def add_trait(self, trait: ProfileTrait) -> None:
        """Add or update a trait."""
        self.traits[trait.id] = trait
        self._trait_by_domain[trait.domain].add(trait.id)
        self._trait_by_name[trait.name] = trait.id
        self.last_updated = datetime.utcnow()
    
    def get_trait(self, name: str) -> Optional[ProfileTrait]:
        """Get a trait by name."""
        trait_id = self._trait_by_name.get(name)
        return self.traits.get(trait_id) if trait_id else None
    
    def get_traits_by_domain(self, domain: ProfileDomain) -> List[ProfileTrait]:
        """Get all traits in a domain."""
        trait_ids = self._trait_by_domain.get(domain, set())
        return [self.traits[tid] for tid in trait_ids if tid in self.traits]
    
    def add_macro_pattern(self, pattern: MacroPattern) -> None:
        """Add or update a macro pattern."""
        self.macro_patterns[pattern.id] = pattern
        self.last_updated = datetime.utcnow()
    
    def get_completion_percentage(self) -> Dict[str, float]:
        """Get completion percentage by domain."""
        # Expected traits per domain (rough estimates)
        expected = {
            ProfileDomain.PERSONALITY: 10,
            ProfileDomain.BEHAVIOR: 8,
            ProfileDomain.HEALTH: 6,
            ProfileDomain.FINANCE: 5,
            ProfileDomain.RELATIONSHIPS: 5,
            ProfileDomain.CAREER: 4,
            ProfileDomain.GROWTH: 4,
            ProfileDomain.ENERGY: 5,
            ProfileDomain.COGNITION: 6,
            ProfileDomain.EMOTION: 5,
        }
        
        completion = {}
        for domain, expected_count in expected.items():
            actual = len(self._trait_by_domain.get(domain, set()))
            completion[domain.value] = min(1.0, actual / expected_count)
        
        return completion
    
    def get_high_confidence_traits(self, threshold: float = 0.80) -> List[ProfileTrait]:
        """Get traits with high confidence."""
        return [t for t in self.traits.values() if t.confidence >= threshold]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "traits": {k: v.to_dict() for k, v in self.traits.items()},
            "macro_patterns": {k: v.to_dict() for k, v in self.macro_patterns.items()},
            "completion": self.get_completion_percentage(),
            "high_confidence_count": len(self.get_high_confidence_traits()),
            "total_traits": len(self.traits),
            "total_patterns": len(self.macro_patterns),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "insights_processed": self.total_insights_processed,
        }
    
    def to_summary(self) -> Dict[str, Any]:
        """Get a condensed summary suitable for context injection."""
        summary = {
            "traits": {},
            "patterns": [],
            "completion": self.get_completion_percentage(),
        }
        
        # Group high-confidence traits by domain
        for domain in ProfileDomain:
            domain_traits = self.get_traits_by_domain(domain)
            confident_traits = [t for t in domain_traits if t.confidence >= 0.70]
            if confident_traits:
                summary["traits"][domain.value] = [
                    {"name": t.name, "value": t.value, "confidence": t.confidence}
                    for t in confident_traits
                ]
        
        # Add strong macro patterns
        for pattern in self.macro_patterns.values():
            if pattern.strength in [PatternStrength.DOMINANT, PatternStrength.STRONG]:
                summary["patterns"].append({
                    "name": pattern.name,
                    "description": pattern.description,
                    "strength": pattern.strength.value,
                })
        
        return summary


# =============================================================================
# MASTER SCOUT
# =============================================================================

class MasterScout:
    """
    The Cross-Domain Profile & Pattern Coordinator.
    
    This is a MASTER-tier agent that builds and maintains the Digital Twin
    by aggregating insights from all domain profilers.
    
    Key Behaviors:
    - Receives pattern detections from all domains
    - Builds unified trait profiles
    - Detects macro-patterns across domains
    - Provides context to other agents
    - Tracks profile evolution over time
    
    Usage:
        scout = MasterScout()
        await scout.start()
        
        # It will automatically receive patterns via SwarmBus
        
        # Get the Digital Twin
        twin = scout.get_digital_twin()
        
        # Get context for an agent
        context = scout.get_context_for_agent("genesis.hypothesis")
    """
    
    AGENT_ID = "master.scout"
    AGENT_TIER = AgentTier.MASTER
    DOMAIN = "meta"
    
    def __init__(self, session_id: Optional[str] = None):
        # The Digital Twin
        self._twin = DigitalTwin(session_id=session_id)
        
        # Pattern detection rules
        self._macro_pattern_rules: List[Dict[str, Any]] = []
        
        # Bus integration
        self._bus: Optional[SwarmBus] = None
        self._running = False
        
        # Domain tracking
        self._domain_last_seen: Dict[str, datetime] = {}
        
        # Statistics
        self._stats = {
            "patterns_received": 0,
            "traits_created": 0,
            "traits_updated": 0,
            "macro_patterns_detected": 0,
            "context_requests_served": 0,
        }
        
        # Load macro pattern rules
        self._load_macro_pattern_rules()
        
        logger.info(f"[{self.AGENT_ID}] Initialized with session {session_id}")
    
    def _load_macro_pattern_rules(self) -> None:
        """Load rules for detecting macro patterns."""
        self._macro_pattern_rules = [
            {
                "name": "Night Owl Productivity",
                "description": "User is most productive in late hours, struggles with mornings",
                "required_traits": [
                    {"name": "sleep_pattern", "domain": "health", "value_contains": "late"},
                    {"name": "energy_pattern", "domain": "energy", "value_contains": "afternoon|evening"},
                ],
                "optional_traits": [
                    {"name": "morning_productivity", "domain": "behavior", "value_contains": "low"},
                ],
                "implications": [
                    "Consider scheduling important tasks for afternoon/evening",
                    "Morning routines should be gentle and low-pressure",
                ],
                "min_confidence": 0.65,
            },
            {
                "name": "Stress-Spending Cycle",
                "description": "Stress triggers impulsive spending followed by guilt",
                "required_traits": [
                    {"name": "stress_pattern", "domain": "health"},
                    {"name": "spending_pattern", "domain": "finance", "value_contains": "impulsive"},
                ],
                "optional_traits": [
                    {"name": "guilt_pattern", "domain": "emotion"},
                ],
                "implications": [
                    "Implement cooling-off period for purchases",
                    "Develop alternative stress relief strategies",
                ],
                "min_confidence": 0.60,
            },
            {
                "name": "Social Recharge Pattern",
                "description": "User needs solitude to recover from social interaction",
                "required_traits": [
                    {"name": "introversion", "domain": "personality"},
                    {"name": "social_battery", "domain": "energy", "value_contains": "drains"},
                ],
                "optional_traits": [
                    {"name": "alone_time_preference", "domain": "behavior"},
                ],
                "implications": [
                    "Schedule recovery time after social events",
                    "Quality over quantity in relationships",
                ],
                "min_confidence": 0.70,
            },
            {
                "name": "Decision Paralysis Pattern",
                "description": "User struggles with decisions, needs external input",
                "required_traits": [
                    {"name": "decision_style", "domain": "cognition", "value_contains": "external|waiting"},
                ],
                "optional_traits": [
                    {"name": "authority_type", "domain": "personality", "value_contains": "emotional|sacral"},
                ],
                "implications": [
                    "Create decision frameworks for common choices",
                    "Build trusted network for sounding board",
                ],
                "min_confidence": 0.65,
            },
        ]
    
    async def start(self) -> None:
        """Start the master scout and subscribe to the bus."""
        if self._running:
            return
        
        self._bus = await get_bus()
        
        # Subscribe to receive patterns
        await self._bus.subscribe(
            agent_id=self.AGENT_ID,
            handler=self._handle_envelope,
            agent_tier=self.AGENT_TIER,
            domain=self.DOMAIN,
            capability="profiling",
        )
        
        self._running = True
        logger.info(f"[{self.AGENT_ID}] Started and subscribed to SwarmBus")
    
    async def stop(self) -> None:
        """Stop the scout and unsubscribe."""
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
        
        # Handle context requests
        if "request_type" in envelope.payload and envelope.payload["request_type"] == "context":
            return await self._handle_context_request(envelope)
        
        if not packet:
            # Handle raw payload
            if "pattern" in envelope.payload or "trait" in envelope.payload:
                return await self._handle_raw_pattern(envelope)
            return {"error": "No packet or valid payload"}
        
        # Route based on insight type
        if packet.insight_type == InsightType.PATTERN:
            return await self._handle_pattern_packet(envelope, packet)
        elif packet.insight_type == InsightType.FACT:
            return await self._handle_fact_packet(envelope, packet)
        elif packet.insight_type == InsightType.SYNTHESIS:
            return await self._handle_synthesis_packet(envelope, packet)
        else:
            logger.debug(f"[{self.AGENT_ID}] Ignoring packet type: {packet.insight_type}")
            return {"status": "ignored"}
    
    async def _handle_pattern_packet(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Process a pattern detection packet."""
        self._stats["patterns_received"] += 1
        
        source_domain = packet.source_domain or packet.source_agent.split(".")[0]
        self._domain_last_seen[source_domain] = datetime.utcnow()
        self._twin.domains_active.add(source_domain)
        
        # Extract pattern data
        pattern_name = packet.payload.get("pattern_name", "unknown")
        pattern_category = packet.payload.get("pattern_category", "behavior")
        strength = packet.payload.get("strength", packet.confidence_score)
        indicators = packet.payload.get("indicators", [])
        framework = packet.payload.get("framework")
        
        # Map to profile domain
        domain = self._map_category_to_domain(pattern_category)
        
        # Find or create trait
        existing = self._twin.get_trait(pattern_name)
        if existing:
            # Update existing trait
            existing.confidence = (existing.confidence + strength) / 2
            existing.source_domains.add(source_domain)
            existing.source_packets.append(packet.packet_id)
            existing.source_count += 1
            existing.last_updated = datetime.utcnow()
            if framework and framework not in existing.frameworks:
                existing.frameworks.append(framework)
            self._stats["traits_updated"] += 1
        else:
            # Create new trait
            trait = ProfileTrait(
                name=pattern_name,
                domain=domain,
                category=pattern_category,
                value=packet.payload.get("suspected_value", "detected"),
                confidence=strength,
                source_count=1,
                source_domains={source_domain},
                source_packets=[packet.packet_id],
                frameworks=[framework] if framework else [],
            )
            self._twin.add_trait(trait)
            self._stats["traits_created"] += 1
        
        self._twin.total_insights_processed += 1
        
        # Check for macro patterns
        new_patterns = await self._detect_macro_patterns()
        
        return {
            "status": "processed",
            "trait_name": pattern_name,
            "domain": domain.value,
            "new_macro_patterns": len(new_patterns),
        }
    
    async def _handle_fact_packet(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Process a verified fact packet."""
        source_domain = packet.source_domain or packet.source_agent.split(".")[0]
        
        # Facts become high-confidence traits
        trait_name = packet.payload.get("trait_name", packet.payload.get("name", "unknown"))
        trait_value = packet.payload.get("value")
        category = packet.payload.get("category", "fact")
        
        domain = self._map_category_to_domain(category)
        
        trait = ProfileTrait(
            name=trait_name,
            domain=domain,
            category=category,
            value=trait_value,
            confidence=max(0.90, packet.confidence_score),
            source_count=1,
            source_domains={source_domain},
            source_packets=[packet.packet_id],
        )
        
        self._twin.add_trait(trait)
        self._stats["traits_created"] += 1
        self._twin.total_insights_processed += 1
        
        return {
            "status": "fact_recorded",
            "trait_name": trait_name,
            "confidence": trait.confidence,
        }
    
    async def _handle_synthesis_packet(
        self, 
        envelope: SwarmEnvelope, 
        packet: SovereignPacket
    ) -> Dict:
        """Process a synthesis from another master agent."""
        # Syntheses often contain multiple findings
        key_findings = packet.payload.get("key_findings", [])
        frameworks = packet.payload.get("frameworks_used", [])
        
        for finding in key_findings:
            if isinstance(finding, str):
                # Simple string finding - create trait
                trait = ProfileTrait(
                    name=f"synthesis_{uuid4().hex[:8]}",
                    domain=ProfileDomain.COGNITION,
                    category="synthesis",
                    value=finding,
                    confidence=packet.confidence_score,
                    frameworks=frameworks,
                )
                self._twin.add_trait(trait)
        
        return {"status": "synthesis_processed", "findings_count": len(key_findings)}
    
    async def _handle_raw_pattern(self, envelope: SwarmEnvelope) -> Dict:
        """Handle direct pattern submission without SovereignPacket."""
        payload = envelope.payload
        
        pattern_name = payload.get("pattern", payload.get("trait", "unknown"))
        domain_str = payload.get("domain", "behavior")
        confidence = payload.get("confidence", 0.5)
        value = payload.get("value", "detected")
        
        domain = self._map_category_to_domain(domain_str)
        
        trait = ProfileTrait(
            name=pattern_name,
            domain=domain,
            category=domain_str,
            value=value,
            confidence=confidence,
            source_domains={envelope.source_agent_id.split(".")[0]},
        )
        
        self._twin.add_trait(trait)
        
        return {"status": "raw_pattern_processed", "trait_id": trait.id}
    
    async def _handle_context_request(self, envelope: SwarmEnvelope) -> Dict:
        """Handle a request for context from another agent."""
        self._stats["context_requests_served"] += 1
        
        query = envelope.payload.get("query", "")
        requesting_agent = envelope.source_agent_id
        scope = envelope.payload.get("scope", "all")
        
        context = self.get_context_for_agent(requesting_agent, scope)
        
        return {
            "status": "context_provided",
            "context": context,
        }
    
    def _map_category_to_domain(self, category: str) -> ProfileDomain:
        """Map a category string to a ProfileDomain."""
        category_lower = category.lower()
        
        mappings = {
            "personality": ProfileDomain.PERSONALITY,
            "jungian": ProfileDomain.PERSONALITY,
            "human_design": ProfileDomain.PERSONALITY,
            "behavior": ProfileDomain.BEHAVIOR,
            "habit": ProfileDomain.BEHAVIOR,
            "health": ProfileDomain.HEALTH,
            "sleep": ProfileDomain.HEALTH,
            "nutrition": ProfileDomain.HEALTH,
            "finance": ProfileDomain.FINANCE,
            "money": ProfileDomain.FINANCE,
            "spending": ProfileDomain.FINANCE,
            "relationship": ProfileDomain.RELATIONSHIPS,
            "social": ProfileDomain.RELATIONSHIPS,
            "career": ProfileDomain.CAREER,
            "work": ProfileDomain.CAREER,
            "growth": ProfileDomain.GROWTH,
            "learning": ProfileDomain.GROWTH,
            "energy": ProfileDomain.ENERGY,
            "energetic": ProfileDomain.ENERGY,
            "cognitive": ProfileDomain.COGNITION,
            "thinking": ProfileDomain.COGNITION,
            "decision": ProfileDomain.COGNITION,
            "emotion": ProfileDomain.EMOTION,
            "emotional": ProfileDomain.EMOTION,
            "feeling": ProfileDomain.EMOTION,
        }
        
        for key, domain in mappings.items():
            if key in category_lower:
                return domain
        
        return ProfileDomain.BEHAVIOR  # Default
    
    async def _detect_macro_patterns(self) -> List[MacroPattern]:
        """Detect macro patterns based on current traits."""
        detected = []
        
        for rule in self._macro_pattern_rules:
            # Check if we already have this pattern
            if any(p.name == rule["name"] for p in self._twin.macro_patterns.values()):
                continue
            
            # Check required traits
            required_met = True
            contributing_traits = []
            contributing_domains = set()
            total_confidence = 0.0
            
            for req in rule["required_traits"]:
                trait = self._twin.get_trait(req["name"])
                if not trait:
                    required_met = False
                    break
                
                # Check value if specified
                if "value_contains" in req and trait.value:
                    import re
                    if not re.search(req["value_contains"], str(trait.value), re.IGNORECASE):
                        required_met = False
                        break
                
                contributing_traits.append(trait.id)
                contributing_domains.update(trait.source_domains)
                total_confidence += trait.confidence
            
            if not required_met:
                continue
            
            # Check optional traits
            for opt in rule.get("optional_traits", []):
                trait = self._twin.get_trait(opt["name"])
                if trait:
                    contributing_traits.append(trait.id)
                    contributing_domains.update(trait.source_domains)
                    total_confidence += trait.confidence * 0.5  # Half weight
            
            # Calculate average confidence
            avg_confidence = total_confidence / len(rule["required_traits"])
            
            if avg_confidence < rule.get("min_confidence", 0.60):
                continue
            
            # Determine strength
            if avg_confidence >= 0.90:
                strength = PatternStrength.DOMINANT
            elif avg_confidence >= 0.80:
                strength = PatternStrength.STRONG
            elif avg_confidence >= 0.70:
                strength = PatternStrength.MODERATE
            else:
                strength = PatternStrength.EMERGING
            
            # Create macro pattern
            pattern = MacroPattern(
                name=rule["name"],
                description=rule["description"],
                contributing_traits=contributing_traits,
                contributing_domains=contributing_domains,
                strength=strength,
                confidence=avg_confidence,
                implications=rule.get("implications", []),
                recommendations=rule.get("recommendations", []),
            )
            
            self._twin.add_macro_pattern(pattern)
            detected.append(pattern)
            self._stats["macro_patterns_detected"] += 1
            
            # Broadcast the discovery
            if self._bus:
                await self._bus.broadcast(
                    source_agent_id=self.AGENT_ID,
                    payload={
                        "discovery_type": "macro_pattern",
                        "pattern": pattern.to_dict(),
                    },
                    priority=PacketPriority.HIGH,
                )
        
        return detected
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get_digital_twin(self) -> DigitalTwin:
        """Get the complete Digital Twin."""
        return self._twin
    
    def get_twin_summary(self) -> Dict[str, Any]:
        """Get a condensed summary of the Digital Twin."""
        return self._twin.to_summary()
    
    def get_context_for_agent(
        self, 
        agent_id: str, 
        scope: str = "all"
    ) -> Dict[str, Any]:
        """
        Get relevant context for an agent.
        
        Filters the Digital Twin to information relevant to the
        requesting agent's domain and needs.
        """
        context = {
            "high_confidence_traits": [],
            "macro_patterns": [],
            "completion": self._twin.get_completion_percentage(),
        }
        
        # Parse agent domain
        parts = agent_id.split(".")
        agent_domain = parts[0] if len(parts) > 1 else None
        
        # Get high-confidence traits
        for trait in self._twin.get_high_confidence_traits():
            if scope == "all" or (agent_domain and agent_domain in trait.source_domains):
                context["high_confidence_traits"].append({
                    "name": trait.name,
                    "value": trait.value,
                    "domain": trait.domain.value,
                    "confidence": trait.confidence,
                })
        
        # Get relevant macro patterns
        for pattern in self._twin.macro_patterns.values():
            if pattern.strength in [PatternStrength.DOMINANT, PatternStrength.STRONG, PatternStrength.MODERATE]:
                context["macro_patterns"].append({
                    "name": pattern.name,
                    "description": pattern.description,
                    "strength": pattern.strength.value,
                    "implications": pattern.implications,
                })
        
        return context
    
    def add_trait(self, trait: ProfileTrait) -> None:
        """Manually add a trait to the Digital Twin."""
        self._twin.add_trait(trait)
        self._stats["traits_created"] += 1
    
    def get_trait(self, name: str) -> Optional[ProfileTrait]:
        """Get a trait by name."""
        return self._twin.get_trait(name)
    
    def get_traits_by_domain(self, domain: ProfileDomain) -> List[ProfileTrait]:
        """Get all traits in a domain."""
        return self._twin.get_traits_by_domain(domain)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the master scout."""
        return {
            "agent_id": self.AGENT_ID,
            "running": self._running,
            "stats": self._stats,
            "twin": {
                "total_traits": len(self._twin.traits),
                "total_patterns": len(self._twin.macro_patterns),
                "completion": self._twin.get_completion_percentage(),
                "high_confidence_count": len(self._twin.get_high_confidence_traits()),
                "domains_active": list(self._twin.domains_active),
                "insights_processed": self._twin.total_insights_processed,
            },
            "domain_activity": {
                domain: last_seen.isoformat()
                for domain, last_seen in self._domain_last_seen.items()
            },
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

_master_scout: Optional[MasterScout] = None


async def get_master_scout(session_id: Optional[str] = None) -> MasterScout:
    """Get or create the singleton MasterScout."""
    global _master_scout
    if _master_scout is None:
        _master_scout = MasterScout(session_id=session_id)
        await _master_scout.start()
    return _master_scout
