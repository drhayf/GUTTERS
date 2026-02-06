"""
Weighted Confidence System for Hypothesis Module.

This module provides sophisticated confidence calculation that weighs evidence
based on type, source reliability, recency, and diminishing returns.

Architecture:
- EvidenceType: Enumeration of evidence categories
- EvidenceWeight: Base weights for each evidence type
- SourceReliability: Reliability multipliers by source
- EvidenceRecord: Immutable record of weighted evidence
- ConfidenceSnapshot: Historical confidence snapshot
- WeightedConfidenceCalculator: Main calculation engine

Key Improvements over Linear Model:
1. Evidence type differentiation (user input > system inference)
2. Recency decay (exponential decay with 30-day half-life)
3. Source reliability factors
4. Diminishing returns (logarithmic saturation)
5. Contradiction amplification (2x penalty vs support)

Author: GUTTERS Intelligence Module
"""

import logging
import math
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: Evidence Type Classification
# ============================================================================

class EvidenceType(str, Enum):
    """
    Classification of evidence types with semantic meaning.

    Hierarchy (highest to lowest reliability):
    1. Direct user input (confirmations, explicit feedback)
    2. User-observed data (journal entries, tracking)
    3. Pattern-based inference (Observer correlations)
    4. System inference (module calculations)
    """

    # Tier 1: Direct User Input (Highest Weight)
    USER_CONFIRMATION = "user_confirmation"
    USER_EXPLICIT_FEEDBACK = "user_explicit_feedback"
    BIRTH_DATA_PROVIDED = "birth_data_provided"

    # Tier 2: User-Observed Data
    JOURNAL_ENTRY = "journal_entry"
    TRACKING_DATA_MATCH = "tracking_data_match"
    MOOD_SCORE_ALIGNMENT = "mood_score_alignment"
    SYMPTOM_REPORT = "symptom_report"

    # Tier 3: Pattern-Based Inference
    OBSERVER_PATTERN = "observer_pattern"
    COSMIC_CORRELATION = "cosmic_correlation"
    TRANSIT_ALIGNMENT = "transit_alignment"
    THEME_ALIGNMENT = "theme_alignment"
    CYCLICAL_PATTERN = "cyclical_pattern"

    # Tier 4: System Inference (Lower Weight)
    MODULE_SUGGESTION = "module_suggestion"
    COSMIC_CALCULATION = "cosmic_calculation"
    GENESIS_REFINEMENT = "genesis_refinement"

    # Contradictory Evidence
    USER_REJECTION = "user_rejection"
    COUNTER_PATTERN = "counter_pattern"
    MISMATCH_EVIDENCE = "mismatch_evidence"


class EvidenceWeight:
    """
    Base weights for each evidence type.

    Scale: 0.0 to 1.0 for supporting evidence
           Negative values for contradictions

    Weights are calibrated based on:
    - Evidence reliability
    - User agency (direct input weighted higher)
    - Statistical foundation (patterns with p-values)
    """

    WEIGHTS: Dict[EvidenceType, float] = {
        # Tier 1: Direct User Input (0.90 - 1.00)
        EvidenceType.USER_CONFIRMATION: 1.00,
        EvidenceType.USER_EXPLICIT_FEEDBACK: 0.95,
        EvidenceType.BIRTH_DATA_PROVIDED: 1.00,

        # Tier 2: User-Observed Data (0.65 - 0.80)
        EvidenceType.JOURNAL_ENTRY: 0.75,
        EvidenceType.TRACKING_DATA_MATCH: 0.70,
        EvidenceType.MOOD_SCORE_ALIGNMENT: 0.72,
        EvidenceType.SYMPTOM_REPORT: 0.68,

        # Tier 3: Pattern-Based Inference (0.45 - 0.60)
        EvidenceType.OBSERVER_PATTERN: 0.55,
        EvidenceType.COSMIC_CORRELATION: 0.50,
        EvidenceType.TRANSIT_ALIGNMENT: 0.52,
        EvidenceType.THEME_ALIGNMENT: 0.48,
        EvidenceType.CYCLICAL_PATTERN: 0.58,

        # Tier 4: System Inference (0.25 - 0.40)
        EvidenceType.MODULE_SUGGESTION: 0.35,
        EvidenceType.COSMIC_CALCULATION: 0.30,
        EvidenceType.GENESIS_REFINEMENT: 0.40,

        # Contradictions (Negative - amplified penalty)
        EvidenceType.USER_REJECTION: -1.50,
        EvidenceType.COUNTER_PATTERN: -0.80,
        EvidenceType.MISMATCH_EVIDENCE: -0.50,
    }

    @classmethod
    def get_weight(cls, evidence_type: EvidenceType) -> float:
        """Get base weight for evidence type."""
        return cls.WEIGHTS.get(evidence_type, 0.30)

    @classmethod
    def is_contradiction(cls, evidence_type: EvidenceType) -> bool:
        """Check if evidence type is contradictory."""
        return cls.get_weight(evidence_type) < 0


class SourceReliability:
    """
    Reliability multipliers based on evidence source.

    Scale: 0.0 to 1.0

    Multiplied with base weight to get adjusted weight.
    """

    # User-originated (Most Reliable)
    DIRECT_USER_INPUT = 1.00
    USER_TRACKED_DATA = 0.95

    # System-observed (Reliable)
    JOURNAL_ANALYSIS = 0.85
    OBSERVER_CORRELATION = 0.80
    COSMIC_MODULE = 0.75

    # System-inferred (Moderate Reliability)
    MODULE_INFERENCE = 0.70
    GENESIS_INFERENCE = 0.65
    COSMIC_TIMING = 0.60

    # Uncertain / Fallback
    INCOMPLETE_DATA = 0.40
    UNKNOWN = 0.50

    SOURCE_MAP: Dict[str, float] = {
        "user": 1.00,
        "user_feedback": 1.00,
        "user_tracking": 0.95,
        "journal_api": 0.85,
        "journal_analysis": 0.85,
        "observer": 0.80,
        "observer_solar": 0.80,
        "observer_lunar": 0.78,
        "observer_transit": 0.75,
        "observer_cyclical": 0.82,
        "cosmic_module": 0.75,
        "astrology_module": 0.72,
        "cardology_module": 0.70,
        "module_inference": 0.70,
        "genesis": 0.65,
        "system": 0.60,
        "unknown": 0.50,
    }

    @classmethod
    def get_reliability(cls, source: str) -> float:
        """Get reliability multiplier for source."""
        # Normalize source name
        normalized = source.lower().replace(" ", "_").replace(".", "_")

        # Direct lookup
        if normalized in cls.SOURCE_MAP:
            return cls.SOURCE_MAP[normalized]

        # Partial match
        for key, value in cls.SOURCE_MAP.items():
            if key in normalized or normalized in key:
                return value

        return cls.UNKNOWN


# ============================================================================
# SECTION 2: Evidence Record Model
# ============================================================================

class EvidenceRecord(BaseModel):
    """
    Immutable record of weighted evidence for a hypothesis.

    Captures:
    - What the evidence is (type, data)
    - Where it came from (source)
    - When it was recorded (timestamp)
    - How it contributes to confidence (weights)
    - Why it matters (reasoning)

    Once created, evidence records are immutable. New evidence
    creates new records rather than modifying existing ones.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str = Field(description="Parent hypothesis ID")
    user_id: int

    # Core evidence data
    evidence_type: EvidenceType
    data: Dict[str, Any] = Field(default_factory=dict)

    # Weighting factors (computed at creation)
    base_weight: float = Field(description="Evidence type base weight")
    source_reliability: float = Field(description="Source reliability multiplier")
    recency_multiplier: float = Field(default=1.0, description="Age-based decay")
    position_factor: float = Field(default=1.0, description="Diminishing returns factor")

    # Computed contribution
    effective_weight: float = Field(description="Final weighted contribution")

    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    source: str = Field(description="Evidence origin")
    reasoning: str = Field(description="Why this evidence matters")

    # Contradiction handling
    is_contradiction: bool = Field(default=False)
    contradiction_strength: float = Field(default=1.0, ge=0.0, le=1.0)

    # Context at time of evidence
    magi_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Chronos state when evidence was recorded"
    )

    class Config:
        frozen = False  # Allow updates for recency recalculation

    @classmethod
    def create(
        cls,
        hypothesis_id: str,
        user_id: int,
        evidence_type: EvidenceType,
        data: Dict[str, Any],
        source: str,
        reasoning: str,
        position: int = 0,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> "EvidenceRecord":
        """
        Factory method to create evidence record with computed weights.

        Args:
            hypothesis_id: Parent hypothesis ID
            user_id: User ID
            evidence_type: Type of evidence
            data: Evidence data payload
            source: Origin of evidence
            reasoning: Why this evidence matters
            position: Position in evidence sequence (for diminishing returns)
            magi_context: Optional magi chronos state

        Returns:
            Fully computed EvidenceRecord
        """
        # Get base weight
        base_weight = EvidenceWeight.get_weight(evidence_type)

        # Get source reliability
        source_reliability = SourceReliability.get_reliability(source)

        # Position-based diminishing returns
        # Formula: 1 / (1 + 0.1 * position)
        # Position 0: 1.0, Position 5: 0.67, Position 10: 0.50
        position_factor = 1.0 / (1.0 + 0.1 * position)

        # Recency starts at 1.0 (recalculated when needed)
        recency_multiplier = 1.0

        # Compute effective weight
        is_contradiction = base_weight < 0

        if is_contradiction:
            # Contradictions: Apply amplification (2x penalty)
            effective_weight = base_weight * source_reliability * 2.0
        else:
            effective_weight = (
                base_weight *
                source_reliability *
                recency_multiplier *
                position_factor
            )

        return cls(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=evidence_type,
            data=data,
            base_weight=base_weight,
            source_reliability=source_reliability,
            recency_multiplier=recency_multiplier,
            position_factor=position_factor,
            effective_weight=effective_weight,
            source=source,
            reasoning=reasoning,
            is_contradiction=is_contradiction,
            magi_context=magi_context
        )


# ============================================================================
# SECTION 3: Confidence Snapshot
# ============================================================================

class ConfidenceSnapshot(BaseModel):
    """
    Point-in-time confidence snapshot for history tracking.

    Allows visualization of confidence evolution over time
    and debugging of confidence calculation.
    """

    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    confidence: float = Field(ge=0.0, le=1.0)

    # What triggered this snapshot
    trigger: str = Field(description="What caused confidence update")
    evidence_id: Optional[str] = Field(default=None)

    # Breakdown at this point
    total_evidence_count: int
    supporting_count: int
    contradiction_count: int

    # Weighted sums
    weighted_support: float
    weighted_contradiction: float

    # Status at snapshot
    status: str = Field(description="Hypothesis status at this point")


# ============================================================================
# SECTION 4: Weighted Confidence Calculator
# ============================================================================

class WeightedConfidenceCalculator:
    """
    Main confidence calculation engine.

    Implements:
    - Weighted evidence aggregation
    - Exponential recency decay
    - Diminishing returns
    - Contradiction amplification
    - Confidence normalization (sigmoid)

    Thread-safe and stateless.
    """

    # Configuration
    BASE_CONFIDENCE = 0.20  # Starting point for new hypotheses
    HALF_LIFE_DAYS = 30  # Evidence value halves every 30 days
    RECENCY_FLOOR = 0.10  # Minimum recency multiplier
    CONFIDENCE_SCALE = 0.12  # Sigmoid scaling factor

    def __init__(
        self,
        half_life_days: int = 30,
        recency_floor: float = 0.10
    ):
        """
        Initialize calculator with configurable parameters.

        Args:
            half_life_days: Days for evidence to decay to 50%
            recency_floor: Minimum recency multiplier (prevents zero)
        """
        self.half_life_days = half_life_days
        self.recency_floor = recency_floor
        self.decay_rate = math.log(2) / self.half_life_days

    def calculate_recency_multiplier(
        self,
        evidence_timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate recency multiplier using exponential decay.

        Formula: e^(-λt) where λ = ln(2) / half_life

        Args:
            evidence_timestamp: When evidence was recorded
            current_time: Reference time (default: now)

        Returns:
            Multiplier between recency_floor and 1.0

        Examples:
            Age 0 days: 1.00
            Age 30 days: 0.50
            Age 60 days: 0.25
            Age 90 days: 0.125
            Age 180+ days: 0.10 (floor)
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Ensure timezone-naive comparison
        if evidence_timestamp.tzinfo:
            evidence_timestamp = evidence_timestamp.replace(tzinfo=None)
        if current_time.tzinfo:
            current_time = current_time.replace(tzinfo=None)

        age_days = (current_time - evidence_timestamp).days

        if age_days <= 0:
            return 1.0

        multiplier = math.exp(-self.decay_rate * age_days)
        return max(self.recency_floor, multiplier)

    def update_evidence_recency(
        self,
        evidence_records: List[EvidenceRecord],
        current_time: Optional[datetime] = None
    ) -> List[EvidenceRecord]:
        """
        Update recency multipliers for all evidence records.

        Modifies records in-place and returns them.

        Args:
            evidence_records: List of evidence records
            current_time: Reference time for decay calculation

        Returns:
            Updated evidence records with new recency values
        """
        for record in evidence_records:
            new_recency = self.calculate_recency_multiplier(
                record.timestamp,
                current_time
            )

            # Update recency and recalculate effective weight
            record.recency_multiplier = new_recency

            if record.is_contradiction:
                record.effective_weight = (
                    record.base_weight *
                    record.source_reliability *
                    2.0  # Contradiction amplification
                )
            else:
                record.effective_weight = (
                    record.base_weight *
                    record.source_reliability *
                    record.recency_multiplier *
                    record.position_factor
                )

        return evidence_records

    def calculate_confidence(
        self,
        evidence_records: List[EvidenceRecord],
        update_recency: bool = True
    ) -> float:
        """
        Calculate weighted confidence from evidence records.

        Algorithm:
        1. Update recency multipliers if requested
        2. Sum positive contributions (support)
        3. Sum negative contributions (contradictions)
        4. Apply sigmoid normalization
        5. Clamp to [0.0, 1.0]

        Args:
            evidence_records: List of evidence records
            update_recency: Whether to update recency first

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not evidence_records:
            return self.BASE_CONFIDENCE

        if update_recency:
            self.update_evidence_recency(evidence_records)

        # Sum contributions
        total_weighted_score = sum(
            record.effective_weight
            for record in evidence_records
        )

        # Apply base confidence
        raw_confidence = self.BASE_CONFIDENCE + (total_weighted_score * self.CONFIDENCE_SCALE)

        # Sigmoid normalization: 1 / (1 + e^(-5 * (x - 0.5)))
        # This maps raw confidence to [0, 1] smoothly
        normalized = 1.0 / (1.0 + math.exp(-5 * (raw_confidence - 0.5)))

        # Clamp to valid range
        return max(0.0, min(1.0, normalized))

    def calculate_initial_confidence(
        self,
        evidence_type: EvidenceType,
        data_points: int = 1,
        correlation: Optional[float] = None,
        source: str = "system"
    ) -> float:
        """
        Calculate initial confidence for newly generated hypothesis.

        Used when hypothesis is first created from Observer patterns.

        Args:
            evidence_type: Type of initial evidence
            data_points: Number of supporting data points
            correlation: Optional correlation coefficient
            source: Evidence source

        Returns:
            Initial confidence score
        """
        base_weight = EvidenceWeight.get_weight(evidence_type)
        reliability = SourceReliability.get_reliability(source)

        # Adjust for data points (diminishing returns)
        data_factor = math.log(1 + data_points) / math.log(11)  # Log scale, capped

        # Adjust for correlation strength if provided
        correlation_factor = 1.0
        if correlation is not None:
            correlation_factor = min(abs(correlation), 1.0)

        raw_confidence = (
            self.BASE_CONFIDENCE +
            base_weight * reliability * data_factor * correlation_factor * 0.5
        )

        # Cap initial confidence at 0.75 (requires more evidence to confirm)
        return max(0.0, min(0.75, raw_confidence))

    def get_confidence_breakdown(
        self,
        evidence_records: List[EvidenceRecord]
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown of confidence contributors.

        Returns human-readable breakdown for transparency.

        Args:
            evidence_records: List of evidence records

        Returns:
            Dictionary with breakdown details
        """
        if not evidence_records:
            return {
                "total_confidence": self.BASE_CONFIDENCE,
                "evidence_count": 0,
                "supporting_count": 0,
                "contradiction_count": 0,
                "by_evidence_type": {},
                "by_source": {},
                "top_contributors": [],
                "recency_impact": 0.0,
            }

        # Update recency for accurate breakdown
        self.update_evidence_recency(evidence_records)

        # Counts
        supporting = [r for r in evidence_records if not r.is_contradiction]
        contradictions = [r for r in evidence_records if r.is_contradiction]

        # Group by type
        by_type: Dict[str, float] = {}
        for record in evidence_records:
            type_key = record.evidence_type.value
            by_type[type_key] = by_type.get(type_key, 0) + record.effective_weight

        # Group by source
        by_source: Dict[str, float] = {}
        for record in evidence_records:
            by_source[record.source] = (
                by_source.get(record.source, 0) + record.effective_weight
            )

        # Top contributors (sorted by absolute effective weight)
        sorted_records = sorted(
            evidence_records,
            key=lambda r: abs(r.effective_weight),
            reverse=True
        )
        top_contributors = [
            {
                "id": r.id,
                "type": r.evidence_type.value,
                "contribution": round(r.effective_weight, 4),
                "reasoning": r.reasoning[:100],
                "age_days": (datetime.utcnow() - r.timestamp.replace(tzinfo=None)).days
                    if r.timestamp.tzinfo else (datetime.utcnow() - r.timestamp).days,
            }
            for r in sorted_records[:5]
        ]

        # Recency impact (average recency multiplier)
        avg_recency = sum(r.recency_multiplier for r in evidence_records) / len(evidence_records)
        recency_impact = 1.0 - avg_recency  # How much recency has reduced weights

        return {
            "total_confidence": self.calculate_confidence(evidence_records, update_recency=False),
            "evidence_count": len(evidence_records),
            "supporting_count": len(supporting),
            "contradiction_count": len(contradictions),
            "weighted_support": sum(r.effective_weight for r in supporting),
            "weighted_contradiction": sum(abs(r.effective_weight) for r in contradictions),
            "by_evidence_type": {k: round(v, 4) for k, v in by_type.items()},
            "by_source": {k: round(v, 4) for k, v in by_source.items()},
            "top_contributors": top_contributors,
            "recency_impact": round(recency_impact, 2),
            "average_age_days": round(
                sum(
                    (datetime.utcnow() - r.timestamp.replace(tzinfo=None)).days
                    if r.timestamp.tzinfo
                    else (datetime.utcnow() - r.timestamp).days
                    for r in evidence_records
                ) / len(evidence_records),
                1
            ),
        }

    def create_snapshot(
        self,
        evidence_records: List[EvidenceRecord],
        trigger: str,
        evidence_id: Optional[str] = None,
        status: str = "forming"
    ) -> ConfidenceSnapshot:
        """
        Create confidence snapshot at current point.

        Args:
            evidence_records: Current evidence records
            trigger: What triggered this snapshot
            evidence_id: Optional triggering evidence ID
            status: Current hypothesis status

        Returns:
            ConfidenceSnapshot capturing current state
        """
        breakdown = self.get_confidence_breakdown(evidence_records)

        return ConfidenceSnapshot(
            confidence=breakdown["total_confidence"],
            trigger=trigger,
            evidence_id=evidence_id,
            total_evidence_count=breakdown["evidence_count"],
            supporting_count=breakdown["supporting_count"],
            contradiction_count=breakdown["contradiction_count"],
            weighted_support=breakdown["weighted_support"],
            weighted_contradiction=breakdown["weighted_contradiction"],
            status=status
        )


# ============================================================================
# SECTION 5: Confidence Thresholds
# ============================================================================

class ConfidenceThresholds:
    """
    Standard threshold configuration for hypothesis status transitions.
    """

    FORMING_MAX = 0.60  # Below this: FORMING
    TESTING_MAX = 0.85  # 0.60-0.85: TESTING
    CONFIRMED_MIN = 0.85  # Above this: CONFIRMED
    REJECTION_THRESHOLD = 0.20  # Below this with contradictions: REJECTED
    STALE_DAYS = 60  # Days without evidence: STALE

    @classmethod
    def get_status_for_confidence(
        cls,
        confidence: float,
        contradictions: int = 0,
        days_since_evidence: int = 0
    ) -> str:
        """
        Determine hypothesis status based on confidence and metadata.

        Args:
            confidence: Current confidence score
            contradictions: Number of contradictory evidence
            days_since_evidence: Days since last evidence

        Returns:
            Status string: 'forming', 'testing', 'confirmed', 'rejected', 'stale'
        """
        # Check for stale first
        if days_since_evidence >= cls.STALE_DAYS:
            return "stale"

        # Check for rejection
        if confidence < cls.REJECTION_THRESHOLD and contradictions > 0:
            return "rejected"

        # Standard thresholds
        if confidence >= cls.CONFIRMED_MIN:
            return "confirmed"
        elif confidence >= cls.FORMING_MAX:
            return "testing"
        else:
            return "forming"


# ============================================================================
# SECTION 6: Module Exports
# ============================================================================

__all__ = [
    "EvidenceType",
    "EvidenceWeight",
    "SourceReliability",
    "EvidenceRecord",
    "ConfidenceSnapshot",
    "WeightedConfidenceCalculator",
    "ConfidenceThresholds",
]
