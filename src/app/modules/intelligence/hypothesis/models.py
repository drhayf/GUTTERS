"""
Hypothesis module for general theories.

DISTINCTION FROM GENESIS:
- This module generates HIGH-LEVEL theories (e.g., "User is solar-sensitive")
- Genesis has FIELD-SPECIFIC hypotheses (e.g., "birth_time candidates: 2pm, 3pm")
- These work together: Hypothesis theories inform Genesis refinement
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, UTC
from typing import Optional, List
from enum import Enum


class HypothesisType(str, Enum):
    """Type of theory-based hypothesis."""

    BIRTH_TIME = "birth_time"  # Refines uncertain birth time
    RISING_SIGN = "rising_sign"  # Predicts rising sign
    COSMIC_SENSITIVITY = "cosmic_sensitivity"  # Solar/lunar sensitivity
    TEMPORAL_PATTERN = "temporal_pattern"  # Time-based patterns
    TRANSIT_EFFECT = "transit_effect"  # Transit correlations
    THEME_CORRELATION = "theme_correlation"  # Theme-based patterns


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

    # Supporting data
    based_on_patterns: List[str] = Field(default_factory=list, description="Observer pattern IDs")
    supporting_evidence: List[dict] = Field(default_factory=list, description="Evidence for theory")

    # Status
    status: HypothesisStatus = Field(default=HypothesisStatus.FORMING)

    # Metadata
    generated_at: datetime
    last_updated: datetime
    last_evidence_at: Optional[datetime] = None

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
            }
        }
    )


class HypothesisUpdate(BaseModel):
    """Record of a theory confidence update."""

    timestamp: datetime
    evidence_type: str  # "journal_entry", "cosmic_event", "user_response"
    evidence_data: dict
    confidence_before: float
    confidence_after: float
    reasoning: str
