"""
Genesis Hypothesis Model

A hypothesis represents a candidate value for an uncertain field,
being refined through conversational probing.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


# Core fields that get priority boost during probing
CORE_FIELDS = {"rising_sign", "type", "profile", "authority"}


class Hypothesis(BaseModel):
    """
    A candidate value being refined through conversation.
    
    Each uncertain field (e.g., rising_sign) spawns multiple hypotheses,
    one per candidate value. Genesis probes hypotheses to update
    confidence until one reaches the confirmation threshold.
    
    Example:
        Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=42,
            session_id="conv-123",
            confidence=0.125,
            initial_confidence=0.125
        )
    """
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    field: str = Field(description="Which field this hypothesizes (e.g., 'rising_sign')")
    module: str = Field(description="Which module owns this field (e.g., 'astrology')")
    suspected_value: str = Field(description="The candidate value (e.g., 'Virgo')")
    user_id: int = Field(description="User this hypothesis belongs to")
    session_id: str = Field(description="Conversation/session ID")
    
    # Confidence tracking
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current confidence (0.0-1.0)"
    )
    initial_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Starting confidence from probabilistic calculation"
    )
    confidence_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Confidence at which to confirm"
    )
    
    # Evidence tracking
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence from responses"
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Contradicting evidence from responses"
    )
    
    # Probing state
    probes_attempted: int = Field(
        default=0,
        ge=0,
        description="Number of probes sent for this hypothesis"
    )
    max_probes: int = Field(
        default=3,
        ge=1,
        description="Maximum probes before giving up"
    )
    last_probed: datetime | None = Field(
        default=None,
        description="When last probe was sent"
    )
    strategies_used: list[str] = Field(
        default_factory=list,
        description="Which refinement strategies have been used"
    )
    
    # Resolution state
    resolved: bool = Field(
        default=False,
        description="Whether this hypothesis has been resolved"
    )
    resolution_method: Literal["confirmed", "refuted", "timeout", "superseded"] | None = Field(
        default=None,
        description="How this hypothesis was resolved"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Temporal Context - captures magi chronos state at generation time
    temporal_context: dict | None = Field(
        default=None,
        description="Magi chronos state when hypothesis was generated (period card, planetary ruler, theme, guidance)"
    )
    
    # =========================================================================
    # Computed Properties
    # =========================================================================
    
    @computed_field
    @property
    def needs_probing(self) -> bool:
        """Check if this hypothesis needs more verification."""
        if self.resolved:
            return False
        if self.confidence >= self.confidence_threshold:
            return False
        if self.probes_attempted >= self.max_probes:
            return False
        return True
    
    @computed_field
    @property
    def confidence_gap(self) -> float:
        """How far from confirmation threshold."""
        return self.confidence_threshold - self.confidence
    
    @computed_field
    @property
    def priority(self) -> float:
        """
        Calculate priority for probing (0.0-1.0, higher = probe first).
        
        Priority factors:
        1. Close to threshold (0.6-0.8) = high priority (almost there!)
        2. Core field = boost priority
        3. Few probes attempted = boost (fresh hypothesis)
        4. Evidence ratio = boost if more evidence than contradictions
        """
        if self.resolved or not self.needs_probing:
            return 0.0
        
        priority = 0.0
        
        # Factor 1: Closeness to threshold (max 0.4)
        # Higher confidence = closer to confirmation = higher priority
        if self.confidence >= 0.6:
            priority += 0.4  # Very close, high priority
        elif self.confidence >= 0.4:
            priority += 0.3
        elif self.confidence >= 0.2:
            priority += 0.2
        else:
            priority += 0.1
        
        # Factor 2: Core field boost (max 0.2)
        if self.field in CORE_FIELDS:
            priority += 0.2
        
        # Factor 3: Fresh hypothesis boost (max 0.2)
        probe_ratio = 1 - (self.probes_attempted / self.max_probes)
        priority += 0.2 * probe_ratio
        
        # Factor 4: Evidence ratio boost (max 0.2)
        total_evidence = len(self.evidence) + len(self.contradictions)
        if total_evidence > 0:
            evidence_ratio = len(self.evidence) / total_evidence
            priority += 0.2 * evidence_ratio
        
        return min(priority, 1.0)
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def add_evidence(self, evidence: str) -> None:
        """Add supporting evidence."""
        self.evidence.append(evidence)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_contradiction(self, contradiction: str) -> None:
        """Add contradicting evidence."""
        self.contradictions.append(contradiction)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_confidence(self, delta: float) -> float:
        """
        Adjust confidence by delta.
        
        Args:
            delta: Amount to add (positive) or subtract (negative)
            
        Returns:
            New confidence value
        """
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        self.updated_at = datetime.now(timezone.utc)
        return self.confidence
    
    def mark_probed(self, strategy_name: str) -> None:
        """Record that a probe was attempted."""
        self.probes_attempted += 1
        self.last_probed = datetime.now(timezone.utc)
        if strategy_name not in self.strategies_used:
            self.strategies_used.append(strategy_name)
        self.updated_at = datetime.now(timezone.utc)
    
    def resolve(
        self, 
        method: Literal["confirmed", "refuted", "timeout", "superseded"]
    ) -> None:
        """Mark hypothesis as resolved."""
        self.resolved = True
        self.resolution_method = method
        self.updated_at = datetime.now(timezone.utc)
    
    def get_unused_strategies(self, available: list[str]) -> list[str]:
        """Get strategies that haven't been used yet."""
        return [s for s in available if s not in self.strategies_used]
    
    def to_storage_dict(self) -> dict:
        """Convert for JSONB storage."""
        return {
            **self.model_dump(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_probed": self.last_probed.isoformat() if self.last_probed else None,
        }
    
    @classmethod
    def from_storage_dict(cls, data: dict) -> "Hypothesis":
        """Reconstruct from storage."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("last_probed"):
            data["last_probed"] = datetime.fromisoformat(data["last_probed"])
        return cls(**data)
