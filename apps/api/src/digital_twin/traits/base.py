"""
Trait Base Classes - The Atomic Unit of Identity

This module defines the Trait class and related structures:
- Trait: A single characteristic with value, confidence, and provenance
- TraitSource: Where a trait value came from
- TraitChange: Record of a change to a trait
- TraitValue: Typed value container

Traits are the fundamental building blocks of the Digital Twin.
Every piece of information about the user is stored as a Trait.

@module TraitBase
"""

from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from enum import Enum

from .categories import TraitCategory, TraitFramework, ConfidenceThreshold


# =============================================================================
# TRAIT VALUE
# =============================================================================

class TraitValueType(str, Enum):
    """The data type of a trait value."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"            # One of predefined options
    LIST = "list"            # Array of values
    OBJECT = "object"        # Complex nested structure
    RANGE = "range"          # Numeric range (min, max)
    SCALE = "scale"          # Position on a scale (0-1)


@dataclass
class TraitValue:
    """
    Container for a trait's value with type information.
    
    Supports various value types and provides serialization.
    """
    value: Any
    value_type: TraitValueType = TraitValueType.STRING
    unit: Optional[str] = None        # For numbers (e.g., "kg", "hours")
    scale_min: Optional[float] = None  # For scales
    scale_max: Optional[float] = None
    enum_options: Optional[List[str]] = None  # For enums
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "value": self.value,
            "type": self.value_type.value,
        }
        if self.unit:
            result["unit"] = self.unit
        if self.scale_min is not None:
            result["scale_min"] = self.scale_min
        if self.scale_max is not None:
            result["scale_max"] = self.scale_max
        if self.enum_options:
            result["enum_options"] = self.enum_options
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraitValue":
        return cls(
            value=data["value"],
            value_type=TraitValueType(data.get("type", "string")),
            unit=data.get("unit"),
            scale_min=data.get("scale_min"),
            scale_max=data.get("scale_max"),
            enum_options=data.get("enum_options"),
        )
    
    @classmethod
    def string(cls, value: str) -> "TraitValue":
        """Create a string trait value."""
        return cls(value=value, value_type=TraitValueType.STRING)
    
    @classmethod
    def number(cls, value: float, unit: Optional[str] = None) -> "TraitValue":
        """Create a numeric trait value."""
        return cls(value=value, value_type=TraitValueType.NUMBER, unit=unit)
    
    @classmethod
    def boolean(cls, value: bool) -> "TraitValue":
        """Create a boolean trait value."""
        return cls(value=value, value_type=TraitValueType.BOOLEAN)
    
    @classmethod
    def scale(cls, value: float, min_val: float = 0.0, max_val: float = 1.0) -> "TraitValue":
        """Create a scale trait value."""
        return cls(
            value=value, 
            value_type=TraitValueType.SCALE,
            scale_min=min_val,
            scale_max=max_val
        )
    
    @classmethod
    def enum(cls, value: str, options: List[str]) -> "TraitValue":
        """Create an enum trait value."""
        return cls(value=value, value_type=TraitValueType.ENUM, enum_options=options)


# =============================================================================
# TRAIT SOURCE
# =============================================================================

class SourceType(str, Enum):
    """How the trait was detected/entered."""
    USER_INPUT = "user_input"        # User directly stated
    AI_DETECTED = "ai_detected"      # AI pattern detection
    CALCULATED = "calculated"        # Calculated from birth data
    IMPORTED = "imported"            # Imported from external source
    INFERRED = "inferred"            # Inferred from other traits
    SENSOR = "sensor"                # From device sensor (HealthKit, etc.)
    MANUAL = "manual"                # Manually entered by user
    SYSTEM = "system"                # System-generated


@dataclass
class TraitSource:
    """
    Provenance information for a trait value.
    
    Tracks WHERE a trait value came from and HOW it was obtained.
    This is crucial for:
    - Confidence weighting (user input > AI detection)
    - Conflict resolution (newer sources may override older)
    - Audit trail (understanding why we believe something)
    """
    source_id: str                   # Unique identifier for this source
    source_agent: str                # Which agent provided this (e.g., "genesis.profiler")
    source_type: SourceType          # How it was obtained
    confidence: float                # Source's confidence (0.0-1.0)
    evidence: List[str]              # Supporting evidence
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_agent": self.source_agent,
            "source_type": self.source_type.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraitSource":
        return cls(
            source_id=data["source_id"],
            source_agent=data["source_agent"],
            source_type=SourceType(data["source_type"]),
            confidence=data["confidence"],
            evidence=data.get("evidence", []),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_agent(
        cls,
        agent_id: str,
        confidence: float,
        evidence: Optional[List[str]] = None,
        source_type: SourceType = SourceType.AI_DETECTED,
    ) -> "TraitSource":
        """Create a source from an agent detection."""
        return cls(
            source_id=str(uuid4())[:8],
            source_agent=agent_id,
            source_type=source_type,
            confidence=confidence,
            evidence=evidence or [],
        )
    
    @classmethod
    def from_user(cls, evidence: Optional[List[str]] = None) -> "TraitSource":
        """Create a source from user input."""
        return cls(
            source_id=str(uuid4())[:8],
            source_agent="user",
            source_type=SourceType.USER_INPUT,
            confidence=1.0,  # User input is highest confidence
            evidence=evidence or ["User stated directly"],
        )


# =============================================================================
# TRAIT CHANGE
# =============================================================================

class ChangeType(str, Enum):
    """Type of change to a trait."""
    CREATED = "created"
    UPDATED = "updated"
    CONFIDENCE_BOOST = "confidence_boost"
    CONFIDENCE_DECREASE = "confidence_decrease"
    EVIDENCE_ADDED = "evidence_added"
    SOURCE_ADDED = "source_added"
    ARCHIVED = "archived"
    RESTORED = "restored"


@dataclass
class TraitChange:
    """
    Record of a change to a trait.
    
    Enables:
    - Full audit trail of trait evolution
    - Understanding how the profile changed over time
    - Undo/rollback capabilities
    - Evolution insights ("Your confidence in X has grown")
    """
    change_id: str = field(default_factory=lambda: str(uuid4())[:8])
    change_type: ChangeType = ChangeType.UPDATED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # What changed
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    old_confidence: Optional[float] = None
    new_confidence: Optional[float] = None
    
    # Who made the change
    source: Optional[TraitSource] = None
    
    # Context
    reason: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "old_value": self.old_value,
            "new_value": self.new_value,
            "old_confidence": self.old_confidence,
            "new_confidence": self.new_confidence,
            "source": self.source.to_dict() if self.source else None,
            "reason": self.reason,
            "session_id": self.session_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraitChange":
        return cls(
            change_id=data["change_id"],
            change_type=ChangeType(data["change_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            old_confidence=data.get("old_confidence"),
            new_confidence=data.get("new_confidence"),
            source=TraitSource.from_dict(data["source"]) if data.get("source") else None,
            reason=data.get("reason"),
            session_id=data.get("session_id"),
        )


# =============================================================================
# TRAIT CONFIDENCE
# =============================================================================

@dataclass
class TraitConfidence:
    """
    Aggregated confidence for a trait from multiple sources.
    
    When multiple sources report the same trait, we aggregate their
    confidence using a weighted formula that considers:
    - Source type (user input > AI detection > inference)
    - Recency (newer sources may be more relevant)
    - Evidence quality (more evidence = higher weight)
    """
    value: float                      # Aggregated confidence (0.0-1.0)
    source_count: int = 1             # Number of contributing sources
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Breakdown
    user_confidence: Optional[float] = None      # From user input
    ai_confidence: Optional[float] = None        # From AI detection
    calculated_confidence: Optional[float] = None # From calculation
    
    @property
    def level(self) -> str:
        """Get human-readable confidence level."""
        return ConfidenceThreshold.get_level_name(self.value)
    
    @property
    def needs_probing(self) -> bool:
        """Check if more probing is needed."""
        return ConfidenceThreshold.needs_probing(self.value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "level": self.level,
            "source_count": self.source_count,
            "last_updated": self.last_updated.isoformat(),
            "user_confidence": self.user_confidence,
            "ai_confidence": self.ai_confidence,
            "calculated_confidence": self.calculated_confidence,
        }


# =============================================================================
# THE TRAIT CLASS
# =============================================================================

@dataclass
class Trait:
    """
    The atomic unit of identity - a single characteristic with full provenance.
    
    A Trait represents ONE piece of understanding about the user:
    - What we know (value)
    - How sure we are (confidence)
    - Where it came from (sources)
    - How it's categorized (category, domain, frameworks)
    - How it's changed over time (history)
    
    Example traits:
    - "hd_type": "Generator" (confidence: 0.95, category: ENERGY)
    - "decision_style": "intuitive" (confidence: 0.72, category: COGNITION)
    - "morning_person": False (confidence: 0.85, category: RHYTHM)
    """
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""                    # Unique name within domain (e.g., "hd_type")
    display_name: Optional[str] = None  # Human-readable name
    description: Optional[str] = None   # What this trait means
    
    # Classification
    domain: str = "general"           # Which domain owns this (e.g., "genesis", "health")
    category: TraitCategory = TraitCategory.DETECTED
    frameworks: Set[TraitFramework] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    
    # Value
    value: Any = None                 # The actual value
    value_type: TraitValueType = TraitValueType.STRING
    unit: Optional[str] = None        # For numeric values
    
    # Confidence
    confidence: float = 0.5           # Aggregated confidence (0.0-1.0)
    confidence_detail: Optional[TraitConfidence] = None
    
    # Provenance
    sources: List[TraitSource] = field(default_factory=list)
    primary_source: Optional[str] = None  # ID of main source
    
    # Temporal
    first_detected: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # History
    history: List[TraitChange] = field(default_factory=list)
    version: int = 1
    
    # Status
    is_verified: bool = False         # User has confirmed
    is_archived: bool = False         # No longer active
    
    # ==========================================================================
    # METHODS
    # ==========================================================================
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()
        if not self.confidence_detail:
            self.confidence_detail = TraitConfidence(value=self.confidence)
    
    @property
    def path(self) -> str:
        """Get the full path for this trait (domain.name)."""
        return f"{self.domain}.{self.name}"
    
    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        return ConfidenceThreshold.get_level_name(self.confidence)
    
    @property
    def needs_probing(self) -> bool:
        """Check if this trait needs more verification."""
        return not self.is_verified and ConfidenceThreshold.needs_probing(self.confidence)
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high enough to trust."""
        return self.confidence >= ConfidenceThreshold.HIGH
    
    def add_source(
        self,
        source: TraitSource,
        new_value: Optional[Any] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Add a new source that supports this trait.
        
        If the source provides a new value, the trait value is updated.
        Confidence is recalculated based on all sources.
        """
        old_value = self.value
        old_confidence = self.confidence
        
        # Add the source
        self.sources.append(source)
        
        # Update value if provided
        if new_value is not None:
            self.value = new_value
        
        # Recalculate confidence
        self._recalculate_confidence()
        
        # Record the change
        change_type = ChangeType.SOURCE_ADDED
        if new_value is not None and new_value != old_value:
            change_type = ChangeType.UPDATED
        elif self.confidence > old_confidence:
            change_type = ChangeType.CONFIDENCE_BOOST
        
        self.history.append(TraitChange(
            change_type=change_type,
            old_value=old_value if new_value is not None else None,
            new_value=new_value,
            old_confidence=old_confidence,
            new_confidence=self.confidence,
            source=source,
            session_id=session_id,
        ))
        
        self.last_updated = datetime.utcnow()
        self.version += 1
    
    def add_evidence(
        self,
        evidence: str,
        source_agent: str = "system",
        confidence_boost: float = 0.05,
        session_id: Optional[str] = None,
    ) -> None:
        """Add evidence that supports this trait value."""
        old_confidence = self.confidence
        
        # Find or create a source for this agent
        for source in self.sources:
            if source.source_agent == source_agent:
                source.evidence.append(evidence)
                source.confidence = min(1.0, source.confidence + confidence_boost)
                break
        else:
            # Create new source
            self.sources.append(TraitSource.from_agent(
                agent_id=source_agent,
                confidence=confidence_boost,
                evidence=[evidence],
            ))
        
        # Recalculate
        self._recalculate_confidence()
        
        # Record
        self.history.append(TraitChange(
            change_type=ChangeType.EVIDENCE_ADDED,
            old_confidence=old_confidence,
            new_confidence=self.confidence,
            reason=evidence,
            session_id=session_id,
        ))
        
        self.last_updated = datetime.utcnow()
    
    def add_contradiction(
        self,
        evidence: str,
        source_agent: str = "system",
        confidence_penalty: float = 0.10,
        session_id: Optional[str] = None,
    ) -> None:
        """Add contradicting evidence that weakens this trait."""
        old_confidence = self.confidence
        
        # Reduce confidence
        self.confidence = max(0.0, self.confidence - confidence_penalty)
        
        # Record in history
        self.history.append(TraitChange(
            change_type=ChangeType.CONFIDENCE_DECREASE,
            old_confidence=old_confidence,
            new_confidence=self.confidence,
            reason=f"[CONTRADICTION] {evidence}",
            session_id=session_id,
        ))
        
        self.last_updated = datetime.utcnow()
    
    def verify(self, session_id: Optional[str] = None) -> None:
        """Mark this trait as user-verified."""
        if not self.is_verified:
            old_confidence = self.confidence
            self.is_verified = True
            self.confidence = min(1.0, self.confidence + 0.15)
            
            self.history.append(TraitChange(
                change_type=ChangeType.CONFIDENCE_BOOST,
                old_confidence=old_confidence,
                new_confidence=self.confidence,
                reason="User verified",
                source=TraitSource.from_user(["User confirmed this trait"]),
                session_id=session_id,
            ))
            
            self.last_updated = datetime.utcnow()
    
    def _recalculate_confidence(self) -> None:
        """Recalculate aggregated confidence from all sources."""
        if not self.sources:
            return
        
        # Weight by source type
        weights = {
            SourceType.USER_INPUT: 1.0,
            SourceType.CALCULATED: 0.95,
            SourceType.MANUAL: 0.9,
            SourceType.AI_DETECTED: 0.8,
            SourceType.SENSOR: 0.85,
            SourceType.INFERRED: 0.7,
            SourceType.IMPORTED: 0.75,
            SourceType.SYSTEM: 0.6,
        }
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        user_conf = None
        ai_conf = None
        calc_conf = None
        
        for source in self.sources:
            weight = weights.get(source.source_type, 0.5)
            weighted_confidence += source.confidence * weight
            total_weight += weight
            
            if source.source_type == SourceType.USER_INPUT:
                user_conf = source.confidence
            elif source.source_type == SourceType.AI_DETECTED:
                ai_conf = max(ai_conf or 0, source.confidence)
            elif source.source_type == SourceType.CALCULATED:
                calc_conf = source.confidence
        
        # Calculate final confidence
        if total_weight > 0:
            self.confidence = min(1.0, weighted_confidence / total_weight)
        
        # Update confidence detail
        self.confidence_detail = TraitConfidence(
            value=self.confidence,
            source_count=len(self.sources),
            user_confidence=user_conf,
            ai_confidence=ai_conf,
            calculated_confidence=calc_conf,
        )
    
    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "domain": self.domain,
            "category": self.category.value,
            "frameworks": [f.value for f in self.frameworks],
            "tags": list(self.tags),
            "value": self.value,
            "value_type": self.value_type.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_detail": self.confidence_detail.to_dict() if self.confidence_detail else None,
            "sources": [s.to_dict() for s in self.sources],
            "primary_source": self.primary_source,
            "first_detected": self.first_detected.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "history_count": len(self.history),
            "version": self.version,
            "is_verified": self.is_verified,
            "is_archived": self.is_archived,
            "path": self.path,
        }
    
    def to_summary(self) -> Dict[str, Any]:
        """Get a condensed summary for context injection."""
        return {
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence,
            "verified": self.is_verified,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trait":
        """Create from dictionary."""
        trait = cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            domain=data.get("domain", "general"),
            category=TraitCategory(data.get("category", "detected")),
            value=data.get("value"),
            value_type=TraitValueType(data.get("value_type", "string")),
            unit=data.get("unit"),
            confidence=data.get("confidence", 0.5),
            version=data.get("version", 1),
            is_verified=data.get("is_verified", False),
            is_archived=data.get("is_archived", False),
        )
        
        # Parse frameworks
        for fw in data.get("frameworks", []):
            try:
                trait.frameworks.add(TraitFramework(fw))
            except ValueError:
                pass
        
        # Parse tags
        trait.tags = set(data.get("tags", []))
        
        # Parse sources
        for source_data in data.get("sources", []):
            trait.sources.append(TraitSource.from_dict(source_data))
        
        # Parse timestamps
        if "first_detected" in data:
            trait.first_detected = datetime.fromisoformat(data["first_detected"])
        if "last_updated" in data:
            trait.last_updated = datetime.fromisoformat(data["last_updated"])
        
        return trait
    
    # ==========================================================================
    # FACTORY METHODS
    # ==========================================================================
    
    @classmethod
    def create(
        cls,
        name: str,
        value: Any,
        domain: str,
        source_agent: str,
        confidence: float = 0.5,
        category: TraitCategory = TraitCategory.DETECTED,
        frameworks: Optional[List[TraitFramework]] = None,
        evidence: Optional[List[str]] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "Trait":
        """
        Factory method for creating a new trait.
        
        Usage:
            trait = Trait.create(
                name="hd_type",
                value="Generator",
                domain="genesis",
                source_agent="genesis.profiler",
                confidence=0.85,
                category=TraitCategory.ENERGY,
                frameworks=[TraitFramework.HUMAN_DESIGN],
                evidence=["User mentioned responding to things"],
            )
        """
        trait = cls(
            name=name,
            display_name=display_name,
            description=description,
            domain=domain,
            category=category,
            value=value,
            confidence=confidence,
        )
        
        if frameworks:
            trait.frameworks = set(frameworks)
        
        # Add initial source
        trait.sources.append(TraitSource.from_agent(
            agent_id=source_agent,
            confidence=confidence,
            evidence=evidence,
        ))
        
        trait.primary_source = trait.sources[0].source_id
        
        # Initial history entry
        trait.history.append(TraitChange(
            change_type=ChangeType.CREATED,
            new_value=value,
            new_confidence=confidence,
            source=trait.sources[0],
        ))
        
        return trait
