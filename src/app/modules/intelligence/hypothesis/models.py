"""
Hypothesis module for general theories.

DISTINCTION FROM GENESIS:
- This module generates HIGH-LEVEL theories (e.g., "User is solar-sensitive")
- Genesis has FIELD-SPECIFIC hypotheses (e.g., "birth_time candidates: 2pm, 3pm")
- These work together: Hypothesis theories inform Genesis refinement
"""

from pydantic import BaseModel, Field, ConfigDict, computed_field
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .confidence import EvidenceRecord, ConfidenceSnapshot


class HypothesisType(str, Enum):
    """Type of theory-based hypothesis."""

    BIRTH_TIME = "birth_time"  # Refines uncertain birth time
    RISING_SIGN = "rising_sign"  # Predicts rising sign
    COSMIC_SENSITIVITY = "cosmic_sensitivity"  # Solar/lunar sensitivity
    TEMPORAL_PATTERN = "temporal_pattern"  # Time-based patterns
    TRANSIT_EFFECT = "transit_effect"  # Transit correlations
    THEME_CORRELATION = "theme_correlation"  # Theme-based patterns
    CYCLICAL_PATTERN = "cyclical_pattern"  # 52-day magi period patterns


class HypothesisStatus(str, Enum):
    """Lifecycle status of theory."""

    FORMING = "forming"  # < 0.60 confidence
    TESTING = "testing"  # 0.60-0.85 confidence
    CONFIRMED = "confirmed"  # > 0.85 confidence
    REJECTED = "rejected"  # Evidence contradicts
    STALE = "stale"  # No new data in 60 days


class Hypothesis(BaseModel):
    """
    A testable theory about the user (TheoryHypothesis).

    Theories start with low confidence and increase as evidence accumulates.
    
    WEIGHTED CONFIDENCE SYSTEM:
    - confidence: Calculated from evidence_records using WeightedConfidenceCalculator
    - evidence_records: List of EvidenceRecord objects with weights
    - confidence_history: Snapshots for tracking evolution
    """

    id: str = Field(description="UUID for this theory")
    user_id: int
    hypothesis_type: HypothesisType

    # The claim
    claim: str = Field(description="Human-readable theory claim")
    predicted_value: str = Field(description="What the theory predicts as true")

    # Confidence tracking
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    evidence_count: int = Field(default=0, description="Number of supporting data points")
    contradictions: int = Field(default=0, description="Number of contradictory data points")

    # Supporting data (legacy - maintained for backward compatibility)
    based_on_patterns: List[str] = Field(default_factory=list, description="Observer pattern IDs")
    supporting_evidence: List[dict] = Field(default_factory=list, description="Evidence for theory")

    # Status
    status: HypothesisStatus = Field(default=HypothesisStatus.FORMING)

    # Metadata
    generated_at: datetime
    last_updated: datetime
    last_evidence_at: Optional[datetime] = None
    
    # Temporal Context - captures magi chronos state at generation time
    temporal_context: Optional[dict] = Field(
        default=None,
        description="Magi chronos state when hypothesis was generated (period card, planetary ruler, theme, guidance)"
    )
    
    # =========================================================================
    # MAGI PERIOD CORRELATION FIELDS
    # =========================================================================
    
    magi_period_card: Optional[str] = Field(
        default=None,
        description="The magi period card when this hypothesis was generated (e.g., 'King of Clubs')"
    )
    
    magi_planetary_ruler: Optional[str] = Field(
        default=None,
        description="The planetary ruler when this hypothesis was generated (e.g., 'Mercury')"
    )
    
    cyclical_pattern_correlations: List[str] = Field(
        default_factory=list,
        description="IDs of cyclical patterns that have contributed evidence to this hypothesis"
    )
    
    period_evidence_count: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of evidence added during each planetary period (e.g., {'Mercury': 3, 'Venus': 1})"
    )
    
    # =========================================================================
    # I-CHING / HEXAGRAM CORRELATION FIELDS
    # =========================================================================
    
    origin_hexagram: Optional[Dict[str, Any]] = Field(
        default=None,
        description="I-Ching hexagram (Sun/Earth gates) when hypothesis was generated"
    )
    
    gate_evidence_count: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of evidence added during each Sun gate (e.g., {'Gate 13': 5, 'Gate 7': 2})"
    )
    
    line_evidence_count: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of evidence added during specific gate lines (e.g., {'Gate 13.Line 4': 3, 'Gate 7.Line 2': 1})"
    )
    
    # =========================================================================
    # WEIGHTED CONFIDENCE SYSTEM FIELDS (New)
    # =========================================================================
    
    evidence_records: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Weighted evidence records (serialized EvidenceRecord objects)"
    )
    
    confidence_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Confidence snapshots over time (serialized ConfidenceSnapshot objects)"
    )
    
    # Confidence metadata
    last_recalculation: Optional[datetime] = Field(
        default=None,
        description="When confidence was last recalculated"
    )
    
    confidence_breakdown: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cached confidence breakdown for display"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "hypothesis_type": "rising_sign",
                "claim": "User's rising sign is likely Virgo based on organizational traits and attention to detail",
                "predicted_value": "Virgo",
                "confidence": 0.68,
                "evidence_count": 8,
                "contradictions": 1,
                "based_on_patterns": ["pattern_123", "pattern_456"],
                "status": "testing",
                "generated_at": "2025-01-15T10:00:00Z",
                "last_updated": "2025-01-20T14:30:00Z",
                "evidence_records": [],
                "confidence_history": [],
            }
        }
    )
    
    def add_evidence_record(self, evidence_record_dict: Dict[str, Any]) -> None:
        """
        Add an evidence record to the hypothesis.
        
        Args:
            evidence_record_dict: Serialized EvidenceRecord
        """
        self.evidence_records.append(evidence_record_dict)
        self.evidence_count = len([
            e for e in self.evidence_records 
            if not e.get("is_contradiction", False)
        ])
        self.contradictions = len([
            e for e in self.evidence_records 
            if e.get("is_contradiction", False)
        ])
        self.last_updated = datetime.now(UTC)
        self.last_evidence_at = datetime.now(UTC)
    
    def add_confidence_snapshot(self, snapshot_dict: Dict[str, Any]) -> None:
        """
        Add a confidence snapshot to history.
        
        Args:
            snapshot_dict: Serialized ConfidenceSnapshot
        """
        self.confidence_history.append(snapshot_dict)
        
        # Keep last 50 snapshots to prevent unbounded growth
        if len(self.confidence_history) > 50:
            self.confidence_history = self.confidence_history[-50:]
    
    def update_status_from_confidence(self) -> None:
        """
        Update status based on current confidence level.
        
        Uses ConfidenceThresholds for standard boundaries.
        """
        from .confidence import ConfidenceThresholds
        
        days_since = 0
        if self.last_evidence_at:
            last_ev = self.last_evidence_at
            if last_ev.tzinfo:
                last_ev = last_ev.replace(tzinfo=None)
            days_since = (datetime.utcnow() - last_ev).days
        
        new_status = ConfidenceThresholds.get_status_for_confidence(
            self.confidence,
            self.contradictions,
            days_since
        )
        
        self.status = HypothesisStatus(new_status)
    
    def get_top_contributors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top contributing evidence records.
        
        Args:
            limit: Maximum number to return
        
        Returns:
            List of top evidence records by effective weight
        """
        sorted_records = sorted(
            self.evidence_records,
            key=lambda r: abs(r.get("effective_weight", 0)),
            reverse=True
        )
        return sorted_records[:limit]
    
    def get_confidence_trend(self) -> str:
        """
        Analyze confidence history to determine trend.
        
        Returns:
            "increasing", "decreasing", "stable", or "volatile"
        """
        if len(self.confidence_history) < 3:
            return "stable"
        
        recent = self.confidence_history[-5:]
        confidences = [s.get("confidence", 0) for s in recent]
        
        # Calculate trend
        diffs = [
            confidences[i] - confidences[i-1] 
            for i in range(1, len(confidences))
        ]
        avg_diff = sum(diffs) / len(diffs)
        
        if avg_diff > 0.05:
            return "increasing"
        elif avg_diff < -0.05:
            return "decreasing"
        elif max(confidences) - min(confidences) > 0.15:
            return "volatile"
        else:
            return "stable"
    
    # =========================================================================
    # MAGI PERIOD CORRELATION METHODS
    # =========================================================================
    
    def track_period_evidence(self, planetary_ruler: str) -> None:
        """
        Track that evidence was added during a specific planetary period.
        
        This enables analysis of which periods contribute most to a hypothesis.
        
        Args:
            planetary_ruler: The planetary ruler during evidence addition (e.g., 'Mercury')
        """
        if not planetary_ruler:
            return
        
        if planetary_ruler not in self.period_evidence_count:
            self.period_evidence_count[planetary_ruler] = 0
        self.period_evidence_count[planetary_ruler] += 1
    
    def track_hexagram_evidence(
        self, 
        sun_gate: int, 
        earth_gate: int = None,
        sun_line: int = None,
        earth_line: int = None
    ) -> None:
        """
        Track that evidence was added during a specific I-Ching hexagram.
        
        This enables analysis of which gates and lines contribute most to a hypothesis.
        
        Args:
            sun_gate: The Sun gate during evidence addition (1-64)
            earth_gate: The Earth gate (optional, for polarity tracking)
            sun_line: The Sun line during evidence addition (1-6)
            earth_line: The Earth line (optional, for polarity tracking)
        """
        if not sun_gate:
            return
        
        # Track gate-level evidence
        gate_key = f"Gate {sun_gate}"
        if gate_key not in self.gate_evidence_count:
            self.gate_evidence_count[gate_key] = 0
        self.gate_evidence_count[gate_key] += 1
        
        # Also track Earth gate if provided
        if earth_gate:
            earth_key = f"Gate {earth_gate} (Earth)"
            if earth_key not in self.gate_evidence_count:
                self.gate_evidence_count[earth_key] = 0
            self.gate_evidence_count[earth_key] += 1
        
        # Track line-level evidence if provided
        if sun_line:
            line_key = f"Gate {sun_gate}.Line {sun_line}"
            if line_key not in self.line_evidence_count:
                self.line_evidence_count[line_key] = 0
            self.line_evidence_count[line_key] += 1
        
        if earth_gate and earth_line:
            earth_line_key = f"Gate {earth_gate}.Line {earth_line} (Earth)"
            if earth_line_key not in self.line_evidence_count:
                self.line_evidence_count[earth_line_key] = 0
            self.line_evidence_count[earth_line_key] += 1
    
    def get_dominant_gate(self) -> Optional[str]:
        """
        Get the I-Ching gate with the most evidence contributions.
        
        Returns:
            Gate identifier or None if no gate evidence tracked
        """
        if not self.gate_evidence_count:
            return None
        return max(self.gate_evidence_count, key=self.gate_evidence_count.get)
    
    def get_dominant_line(self) -> Optional[str]:
        """
        Get the gate line with the most evidence contributions.
        
        Returns:
            Line identifier (e.g., 'Gate 13.Line 4') or None if no line evidence tracked
        """
        if not self.line_evidence_count:
            return None
        return max(self.line_evidence_count, key=self.line_evidence_count.get)
    
    def add_cyclical_pattern_correlation(self, pattern_id: str) -> None:
        """
        Track that a cyclical pattern contributed evidence to this hypothesis.
        
        Args:
            pattern_id: ID of the cyclical pattern
        """
        if pattern_id and pattern_id not in self.cyclical_pattern_correlations:
            self.cyclical_pattern_correlations.append(pattern_id)
    
    def get_dominant_period(self) -> Optional[str]:
        """
        Get the planetary period with the most evidence contributions.
        
        Returns:
            Planetary ruler name or None if no period evidence tracked
        """
        if not self.period_evidence_count:
            return None
        return max(self.period_evidence_count, key=self.period_evidence_count.get)
    
    def get_period_correlation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of period correlations for display.
        
        Returns:
            Dictionary with correlation analysis
        """
        total_evidence = sum(self.period_evidence_count.values()) if self.period_evidence_count else 0
        
        return {
            "magi_period_card": self.magi_period_card,
            "magi_planetary_ruler": self.magi_planetary_ruler,
            "period_evidence_distribution": self.period_evidence_count,
            "dominant_period": self.get_dominant_period(),
            "cyclical_pattern_count": len(self.cyclical_pattern_correlations),
            "total_period_evidence": total_evidence,
        }


class HypothesisUpdate(BaseModel):
    """Record of a theory confidence update."""

    timestamp: datetime
    evidence_type: str  # "journal_entry", "cosmic_event", "user_response"
    evidence_data: dict
    confidence_before: float
    confidence_after: float
    reasoning: str
