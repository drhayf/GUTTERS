"""
GUTTERS - Hypothesis Module

Hypothesis generation and testing system that proposes and validates
theories about cosmic influences.

Weighted Confidence System:
- EvidenceType: Classification of evidence types with semantic meaning
- EvidenceWeight: Base weights for each evidence type (0.25-1.0)
- SourceReliability: Source reliability multipliers (0.40-1.0)
- EvidenceRecord: Immutable evidence records with computed weights
- ConfidenceSnapshot: Point-in-time confidence snapshots
- WeightedConfidenceCalculator: Main calculation engine
- ConfidenceThresholds: Standard threshold configuration

Services:
- HypothesisGenerator: Generate hypotheses from Observer patterns
- HypothesisUpdater: Add evidence and recalculate confidence
- HypothesisStorage: Persist hypotheses to database
"""

# Core models
# Weighted confidence system
from .confidence import (
    ConfidenceSnapshot,
    ConfidenceThresholds,
    EvidenceRecord,
    EvidenceType,
    EvidenceWeight,
    SourceReliability,
    WeightedConfidenceCalculator,
)

# Services
from .generator import HypothesisGenerator
from .models import (
    Hypothesis,
    HypothesisStatus,
    HypothesisType,
)
from .storage import HypothesisStorage
from .updater import HypothesisUpdater, get_hypothesis_updater

__all__ = [
    # Models
    "Hypothesis",
    "HypothesisType",
    "HypothesisStatus",
    # Confidence system
    "EvidenceType",
    "EvidenceWeight",
    "SourceReliability",
    "EvidenceRecord",
    "ConfidenceSnapshot",
    "WeightedConfidenceCalculator",
    "ConfidenceThresholds",
    # Services
    "HypothesisGenerator",
    "HypothesisUpdater",
    "get_hypothesis_updater",
    "HypothesisStorage",
]
