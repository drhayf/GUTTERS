# Weighted Confidence Model - Architectural Analysis

## Executive Summary

**Current State:** Linear confidence scoring with equal weight for all evidence types  
**Proposed State:** Weighted confidence model with differentiated evidence strength, recency decay, and source reliability  
**Primary Goal:** More accurate hypothesis confidence reflecting real-world evidence quality

---

## Current Linear Confidence System

### Architecture (As Implemented)

Located in: `src/app/modules/intelligence/hypothesis/models.py`

```python
class Hypothesis(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0 scale
    evidence_count: int = Field(default=0)
    contradictions: int = Field(default=0)
    supporting_evidence: List[dict] = Field(default_factory=list)
```

**Status Thresholds:**
- `FORMING`: < 0.60 confidence
- `TESTING`: 0.60 - 0.85 confidence  
- `CONFIRMED`: > 0.85 confidence
- `REJECTED`: Evidence contradicts (negative confidence)
- `STALE`: No new data in 60 days

### Current Confidence Calculation

**Simple Linear Model:**
```
confidence = base_confidence + (evidence_count * increment_per_evidence)
```

**Limitations:**
1. **No Evidence Type Differentiation**: Journal entry = Cosmic event = User response (all equal)
2. **No Recency Weighting**: Evidence from 90 days ago counts same as today
3. **No Source Reliability**: System-generated evidence treated same as user-validated
4. **No Confidence Decay**: Stale hypotheses remain high confidence until flagged
5. **Linear Growth**: Doesn't model diminishing returns (10th piece of evidence as valuable as 1st)

### Update Flow (Current)

```python
class HypothesisUpdate(BaseModel):
    timestamp: datetime
    evidence_type: str  # "journal_entry", "cosmic_event", "user_response"
    evidence_data: dict
    confidence_before: float
    confidence_after: float
    reasoning: str
```

Evidence types are **labeled but not weighted**.

---

## Proposed Weighted Confidence Model

### Core Principles

1. **Evidence Type Hierarchy**: Different evidence types carry different weights
2. **Recency Decay**: Older evidence contributes less to current confidence
3. **Source Reliability**: System inferences vs user confirmations weighted differently
4. **Diminishing Returns**: Additional evidence has decreasing marginal impact
5. **Contradiction Amplification**: Contradictions penalized more heavily than support boosts

### Evidence Type Weights

```python
class EvidenceWeight:
    """Evidence type base weights (0.0 - 1.0)"""
    
    # Tier 1: Direct User Input (Highest Weight)
    USER_CONFIRMATION = 1.0          # "Yes, I am Virgo rising"
    USER_EXPLICIT_FEEDBACK = 0.95    # "That sounds right"
    BIRTH_TIME_PROVIDED = 1.0        # User supplies missing data
    
    # Tier 2: Strong Behavioral Evidence
    JOURNAL_ENTRY = 0.75             # User writes about experience
    TRACKING_DATA_MATCH = 0.70       # Tracked symptom aligns with prediction
    COSMIC_EVENT_CORRELATION = 0.65  # User state matches cosmic timing
    
    # Tier 3: Pattern-Based Inference
    OBSERVER_PATTERN = 0.50          # Statistical pattern detected
    TRANSIT_CORRELATION = 0.50       # Transit timing matches behavior
    THEME_ALIGNMENT = 0.45           # Journal theme matches period theme
    
    # Tier 4: System Inference (Lower Weight)
    MODULE_SUGGESTION = 0.30         # Module proposes hypothesis
    COSMIC_CALCULATION = 0.25        # Pure astrological calculation
    
    # Contradictions (Negative Weights)
    USER_REJECTION = -1.5            # "No, that's wrong"
    STRONG_COUNTER_EVIDENCE = -1.0   # Pattern contradicts hypothesis
    WEAK_COUNTER_EVIDENCE = -0.5     # Slight mismatch
```

### Recency Decay Function

**Exponential Decay Model:**

```python
def calculate_recency_multiplier(evidence_age_days: int, half_life_days: int = 30) -> float:
    """
    Calculate recency multiplier using exponential decay.
    
    Args:
        evidence_age_days: Days since evidence was recorded
        half_life_days: Days for evidence value to decay to 50%
    
    Returns:
        Multiplier between 0.1 and 1.0 (minimum floor to prevent zero)
    
    Examples:
        Age 0 days: 1.00x (full weight)
        Age 30 days: 0.50x (half weight)
        Age 60 days: 0.25x (quarter weight)
        Age 90 days: 0.125x (eighth weight)
        Age 180+ days: 0.10x (floor)
    """
    decay_rate = np.log(2) / half_life_days
    multiplier = np.exp(-decay_rate * evidence_age_days)
    return max(0.1, multiplier)  # Floor at 10% to prevent complete devaluation
```

**Rationale:**
- Recent evidence more relevant to current state
- User behavior evolves over time
- Cosmic cycles change (new transits, different periods)
- Prevents ancient evidence dominating confidence

### Source Reliability Factors

```python
class SourceReliability:
    """Reliability multipliers for evidence sources"""
    
    # User-originated (Most Reliable)
    DIRECT_USER_INPUT = 1.0          # User typed/selected explicitly
    USER_TRACKED_DATA = 0.95         # User recorded in tracking module
    
    # System-observed (Reliable)
    JOURNAL_ANALYSIS = 0.85          # NLP analysis of journal content
    OBSERVER_CORRELATION = 0.80      # Statistical pattern detection
    
    # System-inferred (Moderate Reliability)
    MODULE_INFERENCE = 0.70          # Module's educated guess
    COSMIC_TIMING = 0.60             # Pure astrological calculation
    
    # Uncertain
    INCOMPLETE_DATA = 0.40           # Missing context or partial data
```

### Weighted Confidence Formula

```python
def calculate_weighted_confidence(
    hypothesis: Hypothesis,
    evidence_list: List[EvidenceRecord],
    current_date: datetime
) -> float:
    """
    Calculate weighted confidence score.
    
    Formula:
        confidence = base + Σ(weight × recency × reliability × diminishing_factor)
    
    Returns:
        Float between 0.0 and 1.0
    """
    base_confidence = 0.20  # Starting point for new hypotheses
    
    total_weighted_score = 0.0
    evidence_count = 0
    
    for evidence in evidence_list:
        # Get evidence type weight
        evidence_weight = get_evidence_weight(evidence.type)
        
        # Calculate recency multiplier
        age_days = (current_date - evidence.timestamp).days
        recency = calculate_recency_multiplier(age_days)
        
        # Apply source reliability
        reliability = get_source_reliability(evidence.source)
        
        # Diminishing returns factor
        # Each additional evidence has decreasing marginal value
        diminishing_factor = 1.0 / (1.0 + (evidence_count * 0.1))
        
        # Combined weighted contribution
        contribution = evidence_weight * recency * reliability * diminishing_factor
        total_weighted_score += contribution
        
        evidence_count += 1
    
    # Normalize to 0-1 scale
    # Use sigmoid function to ensure bounds
    raw_confidence = base_confidence + (total_weighted_score * 0.15)
    normalized_confidence = 1.0 / (1.0 + np.exp(-5 * (raw_confidence - 0.5)))
    
    return np.clip(normalized_confidence, 0.0, 1.0)
```

### Enhanced Evidence Record Model

```python
class EvidenceRecord(BaseModel):
    """Enhanced evidence record for weighted confidence"""
    
    id: str
    hypothesis_id: str
    user_id: int
    
    # Core evidence data
    type: str  # "journal_entry", "user_confirmation", etc.
    data: dict
    
    # Weighting factors
    base_weight: float = Field(description="Evidence type base weight")
    source_reliability: float = Field(description="Source reliability factor")
    recency_multiplier: float = Field(description="Age-based decay multiplier")
    diminishing_factor: float = Field(description="Position-based diminishing returns")
    
    # Computed contribution
    effective_weight: float = Field(
        description="Final weighted contribution to confidence"
    )
    
    # Metadata
    timestamp: datetime
    source: str = Field(description="Where evidence came from")
    reasoning: str = Field(description="Why this evidence supports/contradicts")
    
    # Contradiction handling
    is_contradiction: bool = False
    contradiction_strength: float = Field(default=1.0, ge=0.0, le=1.0)
```

---

## Integration Points

### 1. HypothesisGenerator Integration

**File:** `src/app/modules/intelligence/hypothesis/generator.py`

**Current:**
```python
hypothesis = Hypothesis(
    confidence=0.45,  # Hard-coded initial confidence
    evidence_count=len(patterns),
    supporting_evidence=[...]
)
```

**Proposed:**
```python
from .confidence import WeightedConfidenceCalculator

calculator = WeightedConfidenceCalculator()

hypothesis = Hypothesis(
    confidence=calculator.calculate_initial_confidence(
        evidence_type="observer_pattern",
        evidence_records=initial_evidence,
        source="Observer.detect_solar_correlations"
    ),
    evidence_count=len(patterns),
    supporting_evidence=[...]
)
```

### 2. Observer Pattern Detection Integration

**File:** `src/app/modules/intelligence/observer/observer.py`

**Current:**
```python
if abs(correlation) >= self.correlation_threshold and p_value < 0.05:
    pattern = {
        "pattern_type": "solar_symptom",
        "correlation": correlation,
        # ...
    }
```

**Proposed:**
```python
if abs(correlation) >= self.correlation_threshold and p_value < 0.05:
    evidence_record = EvidenceRecord(
        type="observer_pattern",
        data={"correlation": correlation, "p_value": p_value},
        base_weight=EvidenceWeight.OBSERVER_PATTERN,  # 0.50
        source_reliability=SourceReliability.OBSERVER_CORRELATION,  # 0.80
        timestamp=datetime.now(UTC),
        source="Observer.detect_solar_correlations"
    )
```

### 3. Journal Entry Integration

**File:** `src/app/api/v1/insights.py` (Journal POST endpoint)

**Current:**
```python
# Journal entry created, no hypothesis update
entry = JournalEntry(content=content, mood_score=mood_score)
db.add(entry)
await db.commit()
```

**Proposed:**
```python
# Journal entry created
entry = JournalEntry(content=content, mood_score=mood_score)
db.add(entry)
await db.commit()

# Check for relevant hypotheses
relevant_hypotheses = await hypothesis_storage.get_active_hypotheses(user_id)

for hypothesis in relevant_hypotheses:
    if _journal_supports_hypothesis(entry, hypothesis):
        evidence_record = EvidenceRecord(
            type="journal_entry",
            data={"entry_id": entry.id, "mood_score": mood_score},
            base_weight=EvidenceWeight.JOURNAL_ENTRY,  # 0.75
            source_reliability=SourceReliability.JOURNAL_ANALYSIS,  # 0.85
            timestamp=entry.created_at,
            source="JournalAPI.create_entry"
        )
        
        await hypothesis_updater.add_evidence(hypothesis.id, evidence_record)
```

### 4. User Feedback Integration

**NEW Endpoint:** `POST /api/v1/intelligence/hypothesis/{hypothesis_id}/feedback`

```python
@router.post("/hypothesis/{hypothesis_id}/feedback")
async def submit_hypothesis_feedback(
    hypothesis_id: str,
    feedback: HypothesisFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Allow user to confirm/reject hypotheses.
    
    Feedback types:
    - "confirm": User agrees with hypothesis
    - "reject": User disagrees
    - "unsure": User doesn't know
    - "partially": Partially accurate
    """
    
    if feedback.type == "confirm":
        evidence_record = EvidenceRecord(
            type="user_confirmation",
            data={"feedback": feedback.comment},
            base_weight=EvidenceWeight.USER_CONFIRMATION,  # 1.0
            source_reliability=SourceReliability.DIRECT_USER_INPUT,  # 1.0
            timestamp=datetime.now(UTC),
            source="User.explicit_feedback"
        )
    elif feedback.type == "reject":
        evidence_record = EvidenceRecord(
            type="user_rejection",
            data={"feedback": feedback.comment},
            base_weight=EvidenceWeight.USER_REJECTION,  # -1.5 (negative!)
            source_reliability=SourceReliability.DIRECT_USER_INPUT,
            timestamp=datetime.now(UTC),
            source="User.explicit_rejection",
            is_contradiction=True,
            contradiction_strength=1.0
        )
    
    await hypothesis_updater.add_evidence(hypothesis_id, evidence_record)
    
    # Recalculate confidence
    updated_hypothesis = await hypothesis_updater.recalculate_confidence(hypothesis_id)
    
    return {"hypothesis": updated_hypothesis, "new_confidence": updated_hypothesis.confidence}
```

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)

**Create New Module:** `src/app/modules/intelligence/hypothesis/confidence.py`

```python
"""
Weighted confidence calculation system.

Components:
- EvidenceWeight enum
- SourceReliability enum  
- WeightedConfidenceCalculator class
- EvidenceRecord model
"""

class WeightedConfidenceCalculator:
    """Main calculator class"""
    
    def calculate_confidence(
        self,
        hypothesis: Hypothesis,
        evidence_records: List[EvidenceRecord]
    ) -> float:
        """Calculate weighted confidence score"""
        pass
    
    def add_evidence(
        self,
        hypothesis: Hypothesis,
        new_evidence: EvidenceRecord
    ) -> Hypothesis:
        """Add new evidence and recalculate confidence"""
        pass
    
    def decay_confidence(
        self,
        hypothesis: Hypothesis,
        current_date: datetime
    ) -> float:
        """Apply recency decay to all evidence"""
        pass
```

**Add to Hypothesis Model:**

```python
class Hypothesis(BaseModel):
    # ... existing fields ...
    
    evidence_records: List[EvidenceRecord] = Field(
        default_factory=list,
        description="Weighted evidence records"
    )
    
    confidence_history: List[ConfidenceSnapshot] = Field(
        default_factory=list,
        description="Historical confidence values"
    )
    
    def get_confidence_breakdown(self) -> Dict[str, Any]:
        """Return detailed breakdown of confidence contributors"""
        return {
            "total": self.confidence,
            "by_evidence_type": {...},
            "by_source": {...},
            "recent_vs_old": {...},
            "top_contributors": [...]
        }
```

### Phase 2: Integration (Week 3-4)

1. **Update HypothesisGenerator** to use WeightedConfidenceCalculator
2. **Update Observer** to create EvidenceRecord objects
3. **Update Journal API** to trigger hypothesis updates
4. **Add user feedback endpoint**

### Phase 3: Migration (Week 5)

**Database Migration:** `alembic revision -m "add_weighted_confidence_fields"`

```python
def upgrade():
    # Add evidence_records JSONB column to hypothesis table
    op.add_column('hypothesis',
        sa.Column('evidence_records', JSONB, nullable=True, default=[])
    )
    
    # Add confidence_history JSONB column
    op.add_column('hypothesis',
        sa.Column('confidence_history', JSONB, nullable=True, default=[])
    )
    
    # Migrate existing data: Convert supporting_evidence to evidence_records
    # with default weights and recency factors
```

**Migration Script:** `scripts/migrate_linear_to_weighted_confidence.py`

```python
async def migrate_existing_hypotheses():
    """
    Convert existing linear confidence hypotheses to weighted model.
    
    Strategy:
    1. Read all existing hypotheses
    2. Convert supporting_evidence list to EvidenceRecord objects
    3. Assign default weights based on evidence_type field
    4. Recalculate confidence using weighted model
    5. Store confidence_history snapshot
    """
    pass
```

### Phase 4: Testing & Validation (Week 6)

**Unit Tests:** `tests/modules/intelligence/hypothesis/test_weighted_confidence.py`

```python
def test_evidence_weight_hierarchy():
    """User confirmation should outweigh system inference"""
    pass

def test_recency_decay():
    """90-day old evidence should have lower multiplier"""
    pass

def test_diminishing_returns():
    """10th evidence should contribute less than 1st"""
    pass

def test_contradiction_penalty():
    """Contradictions should reduce confidence more than support increases it"""
    pass
```

**Integration Tests:** `tests/modules/intelligence/test_hypothesis_lifecycle.py`

```python
async def test_journal_entry_updates_hypothesis():
    """Journal entry matching hypothesis should increase confidence"""
    pass

async def test_user_rejection_reduces_confidence():
    """User explicitly rejecting hypothesis should strongly reduce confidence"""
    pass
```

---

## Benefits of Weighted Model

### 1. Accuracy Improvements

| Scenario | Linear Model | Weighted Model |
|----------|--------------|----------------|
| User confirms hypothesis | +0.10 confidence | +0.25 confidence |
| 90-day old Observer pattern | +0.10 confidence | +0.01 confidence |
| Recent journal entry | +0.10 confidence | +0.15 confidence |
| User rejection | -0.10 confidence | -0.40 confidence |

### 2. Hypothesis Ranking Quality

**Before (Linear):**
- Hypothesis A: 0.75 confidence (10 old system inferences)
- Hypothesis B: 0.50 confidence (2 recent user confirmations)
- **Result:** System picks A despite B being user-validated

**After (Weighted):**
- Hypothesis A: 0.48 confidence (10 × 0.25 weight × 0.2 recency = low)
- Hypothesis B: 0.82 confidence (2 × 1.0 weight × 1.0 recency = high)
- **Result:** System correctly prioritizes user-validated hypothesis

### 3. Stale Hypothesis Detection

**Automatic Decay:**
- Confidence naturally decays as evidence ages
- No need for manual "stale" flagging after 60 days
- System naturally deprioritizes unvalidated old theories

### 4. Explainability

**User-facing confidence breakdown:**

```
Theory: "You're sensitive to solar storms"
Confidence: 72%

Top Contributors:
✅ You confirmed this matches your experience (+40%)
✅ 3 journal entries during storm periods (+25%)
✅ Observer detected correlation (r=0.68) (+15%)
⚠️ Evidence is 45 days old (50% decay applied)

Recent Evidence:
📝 Jan 15: "Headache again today" (during Kp=6 storm)
✓ Jan 12: You marked this as "accurate"
```

### 5. Genesis Integration

**Weighted confidence flows into Genesis hypothesis refinement:**

```python
# Genesis uncertain field hypotheses can use same weighted model
genesis_hypothesis = GenesisHypothesis(
    field="birth_time",
    candidates=["2:00 PM", "3:00 PM"],
    confidence=calculator.calculate_confidence(evidence_records)
)

# High-confidence Genesis hypotheses trigger user prompts
if genesis_hypothesis.confidence > 0.80:
    await prompt_user_for_confirmation(genesis_hypothesis)
```

---

## Comparison Table: Linear vs Weighted

| Feature | Linear Model | Weighted Model |
|---------|-------------|----------------|
| **Evidence Differentiation** | All equal weight | Type-specific weights |
| **Recency Consideration** | None | Exponential decay |
| **Source Reliability** | Implicit | Explicit multipliers |
| **Diminishing Returns** | Linear growth | Logarithmic saturation |
| **Contradiction Handling** | Equal to support | Amplified penalty |
| **Explainability** | Count only | Full breakdown |
| **Confidence Decay** | Manual flagging | Automatic |
| **User Feedback Impact** | +0.10 | +0.25 to +0.50 |
| **Old Evidence Impact** | Same as new | Decayed to 10% |
| **Computational Cost** | O(1) | O(n) where n=evidence count |

---

## Risks & Mitigations

### Risk 1: Over-Complexity

**Risk:** System becomes too complex to reason about  
**Mitigation:**
- Clear documentation with examples
- Confidence breakdown UI showing contribution breakdown
- Default weights calibrated through testing
- Override mechanism for edge cases

### Risk 2: Tuning Difficulty

**Risk:** Weight values need constant tweaking  
**Mitigation:**
- Start with conservative weights based on research
- A/B test weight configurations
- Collect user feedback on hypothesis quality
- Log confidence calculations for analysis

### Risk 3: Performance Degradation

**Risk:** Recalculating confidence for many hypotheses is slow  
**Mitigation:**
- Cache confidence calculations with TTL
- Only recalculate on new evidence
- Use background workers for batch updates
- Index evidence_records JSONB field

### Risk 4: Migration Bugs

**Risk:** Existing hypotheses break during migration  
**Mitigation:**
- Thorough testing on staging data
- Gradual rollout (new hypotheses only, then migrate old)
- Confidence history preservation for rollback
- Migration dry-run with reporting

---

## Success Metrics

### Quantitative

1. **Hypothesis Accuracy Rate**: % of confirmed hypotheses > 0.80 confidence
   - Target: 75% (up from estimated 55% with linear)

2. **User Validation Rate**: % of hypotheses explicitly confirmed by users
   - Target: 40% of shown hypotheses validated

3. **False Positive Rate**: % of high-confidence hypotheses user rejects
   - Target: < 15% (down from estimated 30%)

4. **Confidence Calibration**: Correlation between confidence and actual accuracy
   - Target: Pearson r > 0.70

### Qualitative

1. **User Trust**: "The system seems to understand me better"
2. **Explainability**: "I understand why the system thinks this"
3. **Responsiveness**: "The system learns from my feedback"

---

## Conclusion

The **Weighted Confidence Model** addresses fundamental limitations of the current linear system by:

1. **Differentiating evidence quality** through type-specific weights
2. **Prioritizing recent information** via exponential decay
3. **Amplifying user input** with higher reliability factors
4. **Modeling diminishing returns** for evidence saturation
5. **Enabling explainability** through contribution breakdowns

**Implementation is non-breaking:** Existing hypotheses can be migrated, and the system can run both models during transition.

**Recommendation:** Proceed with Phase 1 (Foundation) to create the calculator infrastructure, then integrate incrementally with existing modules. Monitor confidence calibration metrics throughout rollout.
