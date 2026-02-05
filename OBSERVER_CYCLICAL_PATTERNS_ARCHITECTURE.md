# Observer Cyclical Pattern Detection - Architectural Analysis

## Executive Summary

**Current State:** Observer detects correlations across arbitrary time windows (30-90 days)  
**Proposed State:** Add 52-day cyclical pattern detection aligned with magi chronos periods  
**Primary Goal:** Discover recurring patterns tied to planetary period cycles (e.g., "Mercury period fatigue", "Jupiter period productivity")

---

## Current Observer Pattern Detection

### Architecture (As Implemented)

Located in: `src/app/modules/intelligence/observer/observer.py`

**Current Detection Types:**

1. **Solar Correlations** - `detect_solar_correlations()`
   - Minimum: 30 days, 10 journal entries
   - Pattern: Kp index vs reported symptoms
   - Method: Pearson correlation (r ≥ 0.6, p < 0.05)

2. **Lunar Correlations** - `detect_lunar_correlations()`
   - Minimum: 60 days, 15 journal entries
   - Pattern: Moon phase vs mood/energy
   - Method: Group analysis (New/Waxing/Full/Waning)

3. **Transit Correlations** - `detect_transit_correlations()`
   - Minimum: 90 days, 20 journal entries
   - Pattern: Specific transits vs user events
   - Method: Event co-occurrence analysis

**Correlation Threshold:** `self.correlation_threshold = 0.6`

### Current Workflow

```python
# 1. Collect data over time window
solar_events = await self._get_solar_history(user_id, db, days=30)
journal_entries = await self._get_journal_entries(user_id, db, days=30)

# 2. Align datasets by timestamp
symptom_scores = self._align_symptom_scores(journal_entries, solar_events, "headache")

# 3. Calculate correlation
correlation, p_value = stats.pearsonr(kp_values, symptom_scores)

# 4. Test significance
if abs(correlation) >= 0.6 and p_value < 0.05:
    # Pattern detected
```

### Limitations

1. **No Period Awareness**: Patterns detected across arbitrary time windows, not magi periods
2. **No Cycle Repetition**: Can't detect "same symptom every Mercury period"
3. **No Period Comparison**: Can't compare "Mercury periods vs Jupiter periods"
4. **No Temporal Context**: Patterns lack magi chronos state (period card, planet, theme)
5. **No Longitudinal Analysis**: Can't track pattern evolution across multiple yearly cycles

**Gap:** Current Observer sees correlations **within** periods, but not **across** periods or **between** period types.

---

## Proposed: 52-Day Cyclical Pattern Detection

### Core Concept

**Period-to-Period Analysis:** Group user data by 52-day magi periods, then detect patterns that:
1. **Recur across multiple periods** (e.g., fatigue every Mercury period)
2. **Vary by period type** (e.g., high energy during Jupiter, low during Saturn)
3. **Evolve over yearly cycles** (e.g., Mercury sensitivity increasing year-over-year)

### Magi Period Structure (Recap)

From `src/app/modules/intelligence/cardology/kernel.py`:

```python
# 7 periods per year, each 52 days (364 total)
planet_order = [
    Planet.MERCURY,   # Days 1-52   (Birthday + 52 days)
    Planet.VENUS,     # Days 53-104
    Planet.MARS,      # Days 105-156
    Planet.JUPITER,   # Days 157-208
    Planet.SATURN,    # Days 209-260
    Planet.URANUS,    # Days 261-312
    Planet.NEPTUNE    # Days 313-365 (remainder)
]

# Each period has:
- planet: Ruling planet
- direct_card: Birth card for this period
- start_date, end_date: Date boundaries
- theme: Period guidance (from magi context)
- guidance: Actionable advice
```

### New Detection Type: Cyclical Patterns

**New Class:** `CyclicalPatternDetector`

```python
class CyclicalPatternDetector:
    """
    Detect recurring patterns aligned with 52-day magi periods.
    
    Detects:
    - Period-specific patterns (e.g., "anxiety every Mercury period")
    - Inter-period differences (e.g., "mood 2x higher in Jupiter vs Saturn")
    - Cross-year evolution (e.g., "Mercury sensitivity worsening")
    - Period card alignment (e.g., "low energy when period card is 7♠")
    """
    
    MIN_PERIODS_FOR_PATTERN = 3  # Need at least 3 periods of same type
    MIN_JOURNAL_ENTRIES_PER_PERIOD = 5
    SIGNIFICANCE_THRESHOLD = 0.70  # Correlation across periods
```

---

## Pattern Detection Types

### 1. Period-Specific Symptom Patterns

**Question:** "Do certain symptoms recur during specific planetary periods?"

**Example:**
- User reports headaches during 4 out of 5 Mercury periods
- User has high anxiety during 3 out of 4 Saturn periods
- User feels energized during every Jupiter period

**Detection Method:**

```python
async def detect_period_specific_symptoms(
    self,
    user_id: int,
    db: AsyncSession
) -> List[CyclicalPattern]:
    """
    Detect symptoms that recur during specific planetary periods.
    
    Algorithm:
    1. Fetch all journal entries with symptom tracking
    2. Group entries by magi period (using period_start/period_end dates)
    3. For each period type (Mercury, Venus, etc.):
       - Calculate symptom frequency within that period
       - Compare to baseline symptom frequency
       - Test for statistical significance
    4. Report patterns meeting threshold
    """
    
    # 1. Group journal entries by period
    periods = await self._get_user_periods(user_id, db)
    entries_by_period = {}
    
    for period in periods:
        entries = await self._get_journal_entries_in_range(
            user_id, 
            db,
            start=period.start_date,
            end=period.end_date
        )
        entries_by_period[period] = entries
    
    # 2. Group periods by planet type
    periods_by_planet = defaultdict(list)
    for period, entries in entries_by_period.items():
        periods_by_planet[period.planet].append({
            'period': period,
            'entries': entries
        })
    
    patterns = []
    
    # 3. For each symptom, test for planet-specific correlation
    symptoms = ['headache', 'anxiety', 'fatigue', 'insomnia', 'mood_low']
    
    for symptom in symptoms:
        for planet, period_data in periods_by_planet.items():
            if len(period_data) < self.MIN_PERIODS_FOR_PATTERN:
                continue
            
            # Calculate symptom occurrence rate within this planet's periods
            symptom_rates = []
            for pd in period_data:
                entries = pd['entries']
                if len(entries) < self.MIN_JOURNAL_ENTRIES_PER_PERIOD:
                    continue
                
                symptom_count = sum(
                    1 for e in entries 
                    if symptom in e.get('symptoms', [])
                )
                rate = symptom_count / len(entries)
                symptom_rates.append(rate)
            
            if not symptom_rates:
                continue
            
            # Calculate baseline symptom rate (all periods)
            all_entries = [
                e for pd in entries_by_period.values() 
                for e in pd
            ]
            baseline_rate = sum(
                1 for e in all_entries 
                if symptom in e.get('symptoms', [])
            ) / len(all_entries)
            
            # Test: Are symptom rates during this planet significantly higher?
            avg_rate = np.mean(symptom_rates)
            
            # Statistical test: One-sample t-test
            t_stat, p_value = stats.ttest_1samp(symptom_rates, baseline_rate)
            
            # Significant pattern?
            if p_value < 0.05 and avg_rate > baseline_rate * 1.5:
                patterns.append(CyclicalPattern(
                    pattern_type='period_specific_symptom',
                    planet=planet,
                    symptom=symptom,
                    occurrence_rate=avg_rate,
                    baseline_rate=baseline_rate,
                    fold_increase=avg_rate / baseline_rate,
                    confidence=1 - p_value,
                    supporting_periods=len(symptom_rates),
                    finding=f"User reports {symptom} {avg_rate*100:.0f}% of the time during {planet.value} periods (baseline: {baseline_rate*100:.0f}%)"
                ))
    
    return patterns
```

**Output Example:**

```python
CyclicalPattern(
    pattern_type='period_specific_symptom',
    planet=Planet.MERCURY,
    symptom='headache',
    occurrence_rate=0.62,  # 62% of Mercury period entries mention headache
    baseline_rate=0.18,    # 18% baseline across all periods
    fold_increase=3.4,     # 3.4x more frequent
    confidence=0.96,       # p=0.04, high confidence
    supporting_periods=4,  # Detected across 4 Mercury periods
    finding="User reports headache 62% of the time during Mercury periods (baseline: 18%)"
)
```

### 2. Inter-Period Mood Variance

**Question:** "Does user mood/energy differ systematically between planetary periods?"

**Example:**
- Mood score averages 7.2 during Jupiter periods, 4.1 during Saturn periods
- Energy levels 2x higher during Mars periods than Neptune periods
- Anxiety lowest during Venus periods

**Detection Method:**

```python
async def detect_inter_period_mood_patterns(
    self,
    user_id: int,
    db: AsyncSession
) -> List[CyclicalPattern]:
    """
    Compare mood/energy across different planetary periods.
    
    Algorithm:
    1. Group journal entries by period
    2. Calculate average mood/energy per period type
    3. Perform ANOVA to test for significant differences
    4. Identify which period types differ most
    """
    
    # 1. Group entries by period and extract mood scores
    periods_by_planet = await self._group_entries_by_planet(user_id, db)
    
    mood_by_planet = {}
    energy_by_planet = {}
    
    for planet, period_data in periods_by_planet.items():
        moods = []
        energies = []
        
        for pd in period_data:
            for entry in pd['entries']:
                if 'mood_score' in entry:
                    moods.append(entry['mood_score'])
                if 'energy_score' in entry:
                    energies.append(entry['energy_score'])
        
        if moods:
            mood_by_planet[planet] = moods
        if energies:
            energy_by_planet[planet] = energies
    
    patterns = []
    
    # 2. ANOVA test: Are mood differences across planets significant?
    if len(mood_by_planet) >= 3:
        f_stat, p_value = stats.f_oneway(*mood_by_planet.values())
        
        if p_value < 0.05:
            # Significant differences exist
            # Find highest and lowest mood planets
            avg_moods = {
                planet: np.mean(moods) 
                for planet, moods in mood_by_planet.items()
            }
            
            highest_planet = max(avg_moods, key=avg_moods.get)
            lowest_planet = min(avg_moods, key=avg_moods.get)
            
            highest_mood = avg_moods[highest_planet]
            lowest_mood = avg_moods[lowest_planet]
            
            patterns.append(CyclicalPattern(
                pattern_type='inter_period_mood_variance',
                planet_high=highest_planet,
                planet_low=lowest_planet,
                metric='mood_score',
                high_value=highest_mood,
                low_value=lowest_mood,
                difference=highest_mood - lowest_mood,
                confidence=1 - p_value,
                finding=f"Mood significantly higher during {highest_planet.value} periods (avg {highest_mood:.1f}) vs {lowest_planet.value} periods (avg {lowest_mood:.1f})"
            ))
    
    # Repeat for energy
    if len(energy_by_planet) >= 3:
        f_stat, p_value = stats.f_oneway(*energy_by_planet.values())
        
        if p_value < 0.05:
            avg_energies = {
                planet: np.mean(energies) 
                for planet, energies in energy_by_planet.items()
            }
            
            highest_planet = max(avg_energies, key=avg_energies.get)
            lowest_planet = min(avg_energies, key=avg_energies.get)
            
            patterns.append(CyclicalPattern(
                pattern_type='inter_period_energy_variance',
                planet_high=highest_planet,
                planet_low=lowest_planet,
                metric='energy_score',
                high_value=avg_energies[highest_planet],
                low_value=avg_energies[lowest_planet],
                difference=avg_energies[highest_planet] - avg_energies[lowest_planet],
                confidence=1 - p_value,
                finding=f"Energy significantly higher during {highest_planet.value} periods vs {lowest_planet.value} periods"
            ))
    
    return patterns
```

**Output Example:**

```python
CyclicalPattern(
    pattern_type='inter_period_mood_variance',
    planet_high=Planet.JUPITER,
    planet_low=Planet.SATURN,
    metric='mood_score',
    high_value=7.2,
    low_value=4.1,
    difference=3.1,
    confidence=0.98,  # p=0.02
    finding="Mood significantly higher during Jupiter periods (avg 7.2) vs Saturn periods (avg 4.1)"
)
```

### 3. Theme Alignment Patterns

**Question:** "Do journal entries align with magi period themes?"

**Example:**
- During Mercury periods (theme: "communication"), user journals about work meetings 3x more
- During Venus periods (theme: "relationships"), user journals about love/friendships
- During Mars periods (theme: "action"), user journals about exercise/projects

**Detection Method:**

```python
async def detect_theme_alignment_patterns(
    self,
    user_id: int,
    db: AsyncSession
) -> List[CyclicalPattern]:
    """
    Detect alignment between journal content and period themes.
    
    Algorithm:
    1. Group journal entries by period
    2. For each period, extract themes from magi context
    3. Use NLP to analyze journal content topics
    4. Calculate semantic similarity between journal topics and period theme
    5. Test if similarity is higher than random baseline
    """
    
    # 1. Group entries by period with context
    periods_with_entries = await self._get_periods_with_entries(user_id, db)
    
    patterns = []
    
    # 2. For each period, analyze theme alignment
    for period_data in periods_with_entries:
        period = period_data['period']
        entries = period_data['entries']
        
        # Get magi theme for this period
        magi_theme = period_data['context_snapshot'].get('magi', {}).get('theme')
        if not magi_theme:
            continue
        
        # Extract journal topics using NLP
        journal_topics = []
        for entry in entries:
            topics = await self._extract_topics_from_text(entry['content'])
            journal_topics.extend(topics)
        
        if not journal_topics:
            continue
        
        # Calculate semantic similarity
        # (Could use embeddings, keyword matching, or LLM classification)
        similarity_scores = []
        for topic in journal_topics:
            score = self._calculate_semantic_similarity(topic, magi_theme)
            similarity_scores.append(score)
        
        avg_similarity = np.mean(similarity_scores)
        
        # Compare to baseline (random period-topic pairs)
        baseline_similarity = 0.30  # Empirically determined
        
        if avg_similarity > baseline_similarity * 1.5:
            patterns.append(CyclicalPattern(
                pattern_type='theme_alignment',
                planet=period.planet,
                period_theme=magi_theme,
                alignment_score=avg_similarity,
                baseline_score=baseline_similarity,
                confidence=min(avg_similarity / baseline_similarity, 1.0),
                finding=f"Journal content during {period.planet.value} period strongly aligns with theme '{magi_theme}' (score: {avg_similarity:.2f} vs baseline {baseline_similarity:.2f})"
            ))
    
    return patterns
```

### 4. Cross-Year Evolution Patterns

**Question:** "Do patterns intensify, weaken, or shift across multiple yearly cycles?"

**Example:**
- Mercury sensitivity increasing: Year 1 (30% symptom rate) → Year 2 (55%) → Year 3 (72%)
- Jupiter productivity declining: Year 1 (high energy) → Year 2 (moderate) → Year 3 (low)
- Saturn periods becoming easier to navigate over time

**Detection Method:**

```python
async def detect_cross_year_evolution(
    self,
    user_id: int,
    db: AsyncSession
) -> List[CyclicalPattern]:
    """
    Track pattern evolution across multiple yearly cycles.
    
    Requires: At least 2 full yearly cycles of data (104+ weeks)
    
    Algorithm:
    1. Group periods by year and planet type
    2. Calculate metric (e.g., symptom rate) for each year
    3. Perform linear regression to detect trend
    4. Report patterns with significant trend (increasing/decreasing)
    """
    
    # 1. Group periods by year
    periods_by_year = await self._group_periods_by_year(user_id, db)
    
    if len(periods_by_year) < 2:
        return []  # Need at least 2 years
    
    patterns = []
    
    # 2. For each planet, track metrics across years
    for planet in Planet:
        metric_by_year = {}
        
        for year, periods in periods_by_year.items():
            planet_periods = [p for p in periods if p['period'].planet == planet]
            
            if not planet_periods:
                continue
            
            # Calculate metric (e.g., average mood)
            moods = []
            for pd in planet_periods:
                for entry in pd['entries']:
                    if 'mood_score' in entry:
                        moods.append(entry['mood_score'])
            
            if moods:
                metric_by_year[year] = np.mean(moods)
        
        if len(metric_by_year) < 2:
            continue
        
        # 3. Linear regression: Is there a trend?
        years = list(metric_by_year.keys())
        values = list(metric_by_year.values())
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
        
        # Significant trend?
        if p_value < 0.05 and abs(slope) > 0.5:
            trend_direction = 'increasing' if slope > 0 else 'decreasing'
            
            patterns.append(CyclicalPattern(
                pattern_type='cross_year_evolution',
                planet=planet,
                metric='mood_score',
                trend_direction=trend_direction,
                slope=slope,
                r_squared=r_value**2,
                confidence=1 - p_value,
                years_tracked=len(years),
                finding=f"Mood during {planet.value} periods {trend_direction} across {len(years)} years (slope: {slope:.2f}, R²: {r_value**2:.2f})"
            ))
    
    return patterns
```

---

## Data Model

### CyclicalPattern Model

```python
@dataclass
class CyclicalPattern:
    """
    A detected cyclical pattern aligned with magi periods.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    pattern_type: str  # 'period_specific_symptom', 'inter_period_mood_variance', etc.
    
    # Period context
    planet: Optional[Planet] = None
    planet_high: Optional[Planet] = None  # For comparison patterns
    planet_low: Optional[Planet] = None
    
    # Metrics
    metric: Optional[str] = None  # 'mood_score', 'energy_score', 'symptom_rate'
    metric_value: Optional[float] = None
    baseline_value: Optional[float] = None
    
    # Statistical significance
    confidence: float  # 0-1 scale
    p_value: Optional[float] = None
    supporting_periods: int  # Number of periods supporting pattern
    
    # Human-readable finding
    finding: str
    
    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    first_occurrence: Optional[date] = None
    last_occurrence: Optional[date] = None
    
    # Hypothesis generation
    spawned_hypothesis_id: Optional[str] = None  # Link to generated hypothesis
```

### Database Schema

**New Table:** `observer_cyclical_patterns`

```sql
CREATE TABLE observer_cyclical_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES user(id),
    pattern_type VARCHAR(50) NOT NULL,
    
    -- Period context
    planet VARCHAR(20),  -- 'MERCURY', 'VENUS', etc.
    planet_high VARCHAR(20),
    planet_low VARCHAR(20),
    
    -- Metrics
    metric VARCHAR(50),
    metric_value FLOAT,
    baseline_value FLOAT,
    
    -- Statistical
    confidence FLOAT NOT NULL,
    p_value FLOAT,
    supporting_periods INTEGER,
    
    -- Finding
    finding TEXT NOT NULL,
    
    -- Metadata
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_occurrence DATE,
    last_occurrence DATE,
    
    -- Hypothesis link
    spawned_hypothesis_id UUID REFERENCES hypothesis(id),
    
    -- Index for queries
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_planet (user_id, planet),
    INDEX idx_pattern_type (pattern_type),
    INDEX idx_confidence (confidence)
);
```

---

## Integration Points

### 1. Observer Module Integration

**File:** `src/app/modules/intelligence/observer/observer.py`

```python
class Observer:
    # ... existing methods ...
    
    def __init__(self):
        self.correlation_threshold = 0.6
        self.cyclical_detector = CyclicalPatternDetector()  # NEW
    
    async def run_full_analysis(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Run all Observer pattern detection methods.
        """
        results = {
            'solar': await self.detect_solar_correlations(user_id, db),
            'lunar': await self.detect_lunar_correlations(user_id, db),
            'transit': await self.detect_transit_correlations(user_id, db),
            'cyclical': await self.cyclical_detector.detect_all_patterns(user_id, db)  # NEW
        }
        return results
```

### 2. ChronosStateManager Integration

**File:** `src/app/core/state/chronos.py`

```python
class ChronosStateManager:
    # ... existing methods ...
    
    async def get_period_history(
        self,
        user_id: int,
        num_periods: int = 7
    ) -> List[PeriodSnapshot]:
        """
        NEW: Get historical period data for cyclical analysis.
        
        Returns:
            List of periods with start/end dates, planet, card, theme
        """
        # Reconstruct past periods from birth date + cardology
        user_profile = await self._get_user_profile(user_id)
        birth_date = user_profile.data.get('birth_date')
        birth_card = user_profile.data.get('cardology', {}).get('birth_card')
        
        periods = []
        current_date = datetime.now(UTC).date()
        
        for i in range(num_periods):
            # Calculate period boundaries going backwards
            period_end = current_date - timedelta(days=i * 52)
            period_start = period_end - timedelta(days=51)
            
            # Determine which planet/card this was
            period_info = calculate_period_at_date(birth_date, birth_card, period_start)
            
            periods.append(PeriodSnapshot(
                planet=period_info.planet,
                card=period_info.direct_card,
                start_date=period_start,
                end_date=period_end,
                theme=period_info.theme,
                guidance=period_info.guidance
            ))
        
        return periods
```

### 3. Hypothesis Generation Integration

**File:** `src/app/modules/intelligence/hypothesis/generator.py`

```python
async def generate_from_cyclical_patterns(
    self,
    user_id: int,
    cyclical_patterns: List[CyclicalPattern],
    db: AsyncSession
) -> List[Hypothesis]:
    """
    NEW: Generate hypotheses from detected cyclical patterns.
    
    Example:
    - Pattern: "Headaches 3x more frequent during Mercury periods"
    - Hypothesis: "User is Mercury-sensitive (communication-related stress triggers)"
    """
    
    hypotheses = []
    
    for pattern in cyclical_patterns:
        if pattern.pattern_type == 'period_specific_symptom':
            # Generate sensitivity hypothesis
            hypothesis = Hypothesis(
                id=str(uuid.uuid4()),
                user_id=user_id,
                hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
                claim=f"User experiences {pattern.symptom} during {pattern.planet.value} periods",
                predicted_value=f"{pattern.planet.value}_sensitivity",
                confidence=pattern.confidence * 0.8,  # Slightly conservative
                evidence_count=pattern.supporting_periods,
                based_on_patterns=[pattern.id],
                supporting_evidence=[{
                    'type': 'cyclical_pattern',
                    'pattern_id': pattern.id,
                    'finding': pattern.finding
                }],
                status=HypothesisStatus.TESTING,
                generated_at=datetime.now(UTC),
                last_updated=datetime.now(UTC),
                temporal_context=await self._get_magi_context(user_id)
            )
            
            hypotheses.append(hypothesis)
            
            # Link pattern to hypothesis
            pattern.spawned_hypothesis_id = hypothesis.id
    
    return hypotheses
```

### 4. API Integration

**NEW Endpoint:** `GET /api/v1/intelligence/patterns/cyclical`

```python
@router.get("/patterns/cyclical")
async def get_cyclical_patterns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve detected cyclical patterns for current user.
    
    Returns:
        List of CyclicalPattern objects with:
        - Pattern type
        - Planet(s) involved
        - Statistical confidence
        - Human-readable finding
        - Supporting periods
    """
    
    detector = CyclicalPatternDetector()
    patterns = await detector.detect_all_patterns(current_user.id, db)
    
    return {
        'patterns': patterns,
        'summary': {
            'total': len(patterns),
            'by_type': _group_by_type(patterns),
            'high_confidence': [p for p in patterns if p.confidence > 0.80]
        }
    }
```

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)

**Create New Module:** `src/app/modules/intelligence/observer/cyclical.py`

```python
"""
Cyclical pattern detection aligned with 52-day magi periods.

Classes:
- CyclicalPatternDetector: Main detector class
- CyclicalPattern: Pattern model
- PeriodSnapshot: Historical period data model
"""

class CyclicalPatternDetector:
    async def detect_all_patterns(self, user_id: int, db: AsyncSession) -> List[CyclicalPattern]:
        """Run all cyclical detection methods"""
        patterns = []
        
        patterns.extend(await self.detect_period_specific_symptoms(user_id, db))
        patterns.extend(await self.detect_inter_period_mood_patterns(user_id, db))
        patterns.extend(await self.detect_theme_alignment_patterns(user_id, db))
        patterns.extend(await self.detect_cross_year_evolution(user_id, db))
        
        return patterns
```

**Add Database Migration:** `alembic revision -m "add_cyclical_patterns_table"`

### Phase 2: Integration (Week 3-4)

1. **Extend ChronosStateManager** with `get_period_history()` method
2. **Integrate with Observer** main analysis workflow
3. **Connect to HypothesisGenerator** for automatic hypothesis spawning
4. **Add API endpoint** for frontend consumption

### Phase 3: Frontend Visualization (Week 5)

**New Component:** `frontend/src/features/timeline/CyclicalPatternsPanel.tsx`

```tsx
export function CyclicalPatternsPanel() {
    const { data: patterns } = useQuery({
        queryKey: ['cyclical-patterns'],
        queryFn: async () => {
            const res = await api.get('/api/v1/intelligence/patterns/cyclical')
            return res.data.patterns
        }
    })
    
    return (
        <Card>
            <CardHeader>
                <CardTitle>Cyclical Patterns</CardTitle>
                <CardDescription>
                    Recurring patterns across your magi periods
                </CardDescription>
            </CardHeader>
            <CardContent>
                {patterns.map(pattern => (
                    <PatternCard key={pattern.id} pattern={pattern} />
                ))}
            </CardContent>
        </Card>
    )
}
```

### Phase 4: Testing & Validation (Week 6)

**Unit Tests:** `tests/modules/intelligence/observer/test_cyclical_detector.py`

```python
async def test_detect_period_specific_symptoms():
    """Test symptom detection across Mercury periods"""
    pass

async def test_inter_period_mood_variance():
    """Test ANOVA for mood differences between planets"""
    pass

async def test_insufficient_data_handling():
    """Ensure graceful handling when < 3 periods available"""
    pass
```

---

## Use Cases & Examples

### Use Case 1: Mercury Period Fatigue

**Scenario:** User reports fatigue/brain fog during 4 consecutive Mercury periods

**Pattern Detected:**
```python
CyclicalPattern(
    pattern_type='period_specific_symptom',
    planet=Planet.MERCURY,
    symptom='fatigue',
    occurrence_rate=0.68,
    baseline_rate=0.22,
    fold_increase=3.1,
    confidence=0.94,
    supporting_periods=4,
    finding="User reports fatigue 68% of the time during Mercury periods (baseline: 22%)"
)
```

**Generated Hypothesis:**
```python
Hypothesis(
    hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
    claim="User experiences communication-related burnout during Mercury periods",
    predicted_value="mercury_sensitivity_high",
    confidence=0.75,
    evidence_count=4
)
```

**User Prompt:**
> "We've noticed you tend to feel fatigued during Mercury periods (communication/mental focus). This has happened 4 times in a row. Does this resonate with you?"

### Use Case 2: Jupiter vs Saturn Mood Swing

**Scenario:** User mood averages 8.1 during Jupiter periods, 3.9 during Saturn periods

**Pattern Detected:**
```python
CyclicalPattern(
    pattern_type='inter_period_mood_variance',
    planet_high=Planet.JUPITER,
    planet_low=Planet.SATURN,
    metric='mood_score',
    high_value=8.1,
    low_value=3.9,
    difference=4.2,
    confidence=0.97,
    finding="Mood significantly higher during Jupiter periods (avg 8.1) vs Saturn periods (avg 3.9)"
)
```

**User Insight:**
> "Your mood follows a cyclical pattern: You're most optimistic during Jupiter periods (expansion, growth) and face challenges during Saturn periods (discipline, restriction). This is a natural rhythm—anticipate these shifts and plan accordingly."

### Use Case 3: Venus Period Journaling

**Scenario:** User journals about relationships 4x more during Venus periods

**Pattern Detected:**
```python
CyclicalPattern(
    pattern_type='theme_alignment',
    planet=Planet.VENUS,
    period_theme='relationships and harmony',
    alignment_score=0.82,
    baseline_score=0.28,
    confidence=0.89,
    finding="Journal content during Venus periods strongly aligns with theme 'relationships' (score: 0.82 vs baseline 0.28)"
)
```

**User Insight:**
> "You naturally tune into relationships during Venus periods—your journaling reflects this. Use these periods for deep conversations, conflict resolution, and strengthening bonds."

### Use Case 4: Saturn Periods Getting Easier

**Scenario:** User's Saturn period mood improving year-over-year

**Pattern Detected:**
```python
CyclicalPattern(
    pattern_type='cross_year_evolution',
    planet=Planet.SATURN,
    metric='mood_score',
    trend_direction='increasing',
    slope=1.2,
    r_squared=0.78,
    confidence=0.91,
    years_tracked=3,
    finding="Mood during Saturn periods increasing across 3 years (slope: 1.2, R²: 0.78)"
)
```

**User Insight:**
> "Your relationship with Saturn periods has evolved! Year 1: avg mood 3.5. Year 2: 4.7. Year 3: 5.9. You're learning to work with restriction and discipline. This growth is significant."

---

## Benefits of Cyclical Pattern Detection

### 1. Period-Aware Insights

| Current Observer | Cyclical Detector |
|------------------|-------------------|
| "You're sensitive to solar storms" | "You're sensitive to solar storms **during Mercury periods specifically**" |
| "Your mood varies with moon phase" | "Your mood is 2x higher during **Jupiter periods** regardless of moon phase" |
| "Headaches correlate with Kp index" | "Mercury periods trigger headaches **even without solar activity**—it's the period itself" |

### 2. Predictive Power

**Current:** "You had headaches last week"  
**Cyclical:** "Mercury period starts in 3 days—based on past patterns, prepare for potential communication stress and headaches"

### 3. Hypothesis Quality

**Current Hypothesis:**
- "User is solar-sensitive" (generic)

**Cyclical-Informed Hypothesis:**
- "User is Mercury-period-sensitive with solar storms as amplifying factor" (specific)
- Evidence: 4 Mercury periods, 3 with headaches, 2 with concurrent solar storms

### 4. User Empowerment

**Timeline View Enhanced:**
```
Mercury Period (Jan 15 - Mar 7):
⚠️ Pattern Alert: You've reported fatigue in 4 out of 5 past Mercury periods
📊 This period: 2 headache entries, 1 low-energy day
💡 Recommendation: Schedule lighter workload during next Mercury period
```

### 5. Longitudinal Growth Tracking

**Cross-Year Dashboard:**
```
Your Saturn Period Evolution:
Year 1 (2023): Avg mood 3.5, 8 difficult days
Year 2 (2024): Avg mood 4.7, 5 difficult days
Year 3 (2025): Avg mood 5.9, 2 difficult days

✅ Progress: You've developed resilience to Saturn's challenges
```

---

## Technical Considerations

### Data Requirements

**Minimum Data for Detection:**

| Pattern Type | Min Periods | Min Entries | Min Time |
|-------------|-------------|-------------|----------|
| Period-specific symptom | 3 of same planet | 15 total | 9 months |
| Inter-period mood | 3 different planets | 30 total | 9 months |
| Theme alignment | 3 of same planet | 15 total | 9 months |
| Cross-year evolution | 2 years of 1 planet | 50 total | 2 years |

**Graceful Degradation:**
- If insufficient data: Return empty list with explanatory message
- If partial data: Return patterns with lower confidence + "needs more data" flag

### Performance Optimization

**Challenges:**
- Grouping journal entries by period requires date range queries
- Cross-year analysis needs to process 2+ years of data
- Statistical tests (ANOVA, regression) computationally expensive

**Optimizations:**
1. **Cache period boundaries** in Redis (TTL: 24hr)
2. **Precompute period groupings** during nightly batch job
3. **Index journal entries** by created_at for fast range queries
4. **Materialize views** for frequently-accessed aggregations
5. **Async execution** with background workers (Celery)

**Execution Strategy:**
```python
# Run cyclical detection as async background task
@celery_app.task
async def run_cyclical_detection(user_id: int):
    detector = CyclicalPatternDetector()
    patterns = await detector.detect_all_patterns(user_id, db)
    
    # Store in database
    await storage.store_patterns(patterns)
    
    # Trigger hypothesis generation if high-confidence patterns found
    high_confidence = [p for p in patterns if p.confidence > 0.80]
    if high_confidence:
        await hypothesis_generator.generate_from_cyclical_patterns(
            user_id, high_confidence, db
        )
```

### Statistical Rigor

**Multiple Testing Correction:**
- When testing many symptoms across 7 planets, risk of false positives increases
- Apply Bonferroni correction: `adjusted_alpha = 0.05 / num_tests`
- Example: Testing 5 symptoms × 7 planets = 35 tests → adjusted α = 0.0014

**Minimum Effect Size:**
- Don't report patterns with tiny effect sizes even if statistically significant
- Require fold_increase ≥ 1.5 for practical significance
- Mood difference ≥ 1.5 points (on 1-10 scale)

---

## Comparison Table: Standard vs Cyclical Detection

| Feature | Standard Observer | Cyclical Detector |
|---------|-------------------|-------------------|
| **Time Window** | Arbitrary (30-90 days) | 52-day periods |
| **Pattern Types** | Solar/Lunar/Transit correlations | Period-specific, inter-period, evolution |
| **Temporal Context** | None | Planet, card, theme, guidance |
| **Recurrence Detection** | No | Yes (across multiple periods) |
| **Longitudinal Analysis** | No | Yes (cross-year trends) |
| **Minimum Data** | 30 days | 9 months (3 periods) |
| **Hypothesis Generation** | Generic sensitivity | Period-specific sensitivity |
| **Predictive Power** | Low (correlations only) | High (cyclical patterns) |
| **User Actionability** | Moderate | High (period planning) |

---

## Risks & Mitigations

### Risk 1: Data Sparsity

**Risk:** Many users won't have 3+ periods of data for 12-18 months  
**Mitigation:**
- Clearly communicate data requirements to user
- Show progress: "2/3 Mercury periods tracked—1 more needed for pattern detection"
- Provide value with standard Observer until cyclical data sufficient

### Risk 2: Overfitting

**Risk:** Detecting spurious patterns in small datasets  
**Mitigation:**
- Strict minimum data requirements (3+ periods)
- Multiple testing correction (Bonferroni)
- Effect size thresholds (fold_increase ≥ 1.5)
- Cross-validation where possible

### Risk 3: User Confirmation Bias

**Risk:** User sees pattern, unconsciously creates pattern  
**Mitigation:**
- Blind testing: Don't show detected patterns immediately
- Validate with retrospective data before showing
- Distinguish "detected pattern" from "validated pattern"
- Track false positives when user rejects pattern

### Risk 4: Performance Issues

**Risk:** Cyclical analysis on 2+ years of data is slow  
**Mitigation:**
- Background jobs (Celery)
- Materialized views
- Caching computed patterns (7-day TTL)
- Incremental updates (only recompute when new period completes)

---

## Success Metrics

### Quantitative

1. **Pattern Detection Rate**: % of users with ≥1 cyclical pattern detected
   - Target: 60% of users with 9+ months data

2. **Pattern Validation Rate**: % of detected patterns user confirms as accurate
   - Target: 70% (higher than generic Observer ~55%)

3. **Hypothesis Quality**: % of cyclical-informed hypotheses reaching CONFIRMED status
   - Target: 40% (vs 25% for generic hypotheses)

4. **User Engagement**: % of users viewing Timeline page after pattern detection
   - Target: 75% click-through rate from pattern notification

### Qualitative

1. **Pattern Usefulness**: "This pattern helps me plan my life"
2. **Self-Awareness**: "I understand my cycles better now"
3. **Empowerment**: "I can anticipate challenges before they hit"

---

## Conclusion

**Cyclical Pattern Detection** extends Observer's capabilities by:

1. **Aligning with magi chronos periods** for period-aware analysis
2. **Detecting recurrence** across multiple 52-day cycles
3. **Comparing period types** (Jupiter vs Saturn, etc.)
4. **Tracking evolution** across multiple yearly cycles
5. **Generating informed hypotheses** with period-specific context

**Implementation is additive:** Existing Observer patterns continue working, cyclical detection adds new layer when sufficient data available.

**Recommendation:** Proceed with Phase 1 (Foundation) to create detector infrastructure, then integrate with ChronosStateManager and existing Observer pipeline. Monitor pattern validation rates to refine statistical thresholds.
