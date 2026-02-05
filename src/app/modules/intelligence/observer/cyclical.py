"""
Cyclical Pattern Detection Module.

Detects recurring patterns aligned with 52-day magi periods:
- Period-specific symptoms (e.g., headaches during Mercury periods)
- Inter-period mood variance (e.g., higher mood during Jupiter vs Saturn)
- Theme alignment (e.g., journal topics match period themes)
- Cross-year evolution (e.g., Saturn periods getting easier over time)

This extends the Observer module with period-aware pattern detection,
enabling more sophisticated hypothesis generation and predictive insights.
"""

import logging
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field
from scipy import stats
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: Enums and Constants
# ============================================================================

class Planet(str, Enum):
    """Planetary rulers for 52-day periods."""
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"


class CyclicalPatternType(str, Enum):
    """Types of cyclical patterns that can be detected."""
    PERIOD_SPECIFIC_SYMPTOM = "period_specific_symptom"
    INTER_PERIOD_MOOD_VARIANCE = "inter_period_mood_variance"
    INTER_PERIOD_ENERGY_VARIANCE = "inter_period_energy_variance"
    THEME_ALIGNMENT = "theme_alignment"
    CROSS_YEAR_EVOLUTION = "cross_year_evolution"
    PERIOD_CARD_CORRELATION = "period_card_correlation"
    # I-Ching Gate patterns (micro-cycle ~6 days per gate)
    GATE_SPECIFIC_SYMPTOM = "gate_specific_symptom"
    INTER_GATE_MOOD_VARIANCE = "inter_gate_mood_variance"
    GATE_POLARITY_PATTERN = "gate_polarity_pattern"  # Sun/Earth axis patterns
    GATE_LINE_CORRELATION = "gate_line_correlation"  # Line-specific patterns


# ============================================================================
# SECTION 2: Data Models
# ============================================================================

class PeriodSnapshot(BaseModel):
    """
    Historical snapshot of a 52-day magi period.
    
    Used for grouping journal entries and detecting cyclical patterns.
    """
    planet: Planet
    card: Optional[str] = None
    start_date: date
    end_date: date
    theme: Optional[str] = None
    guidance: Optional[str] = None
    period_number: int = 0  # 1-7 within the year
    year: int = 0
    
    class Config:
        use_enum_values = True


class CyclicalPattern(BaseModel):
    """
    A detected cyclical pattern aligned with magi periods.
    
    Captures recurring patterns across multiple 52-day periods,
    enabling period-specific insights and predictions.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    pattern_type: CyclicalPatternType
    
    # Period context
    planet: Optional[Planet] = None
    planet_high: Optional[Planet] = None  # For comparison patterns
    planet_low: Optional[Planet] = None
    period_card: Optional[str] = None  # For card-specific patterns
    
    # I-Ching gate context (micro-cycle)
    sun_gate: Optional[int] = None  # Gate 1-64
    earth_gate: Optional[int] = None  # Polarity gate
    gate_line: Optional[int] = None  # Line 1-6
    gate_name: Optional[str] = None  # Human Design gate name
    gene_key_gift: Optional[str] = None  # Gene Keys gift frequency
    
    # Symptom/metric details
    symptom: Optional[str] = None
    metric: Optional[str] = None  # 'mood_score', 'energy_score', 'symptom_rate'
    
    # Metric values
    metric_value: Optional[float] = None
    high_value: Optional[float] = None
    low_value: Optional[float] = None
    baseline_value: Optional[float] = None
    occurrence_rate: Optional[float] = None
    fold_increase: Optional[float] = None
    difference: Optional[float] = None
    
    # Theme alignment specific
    period_theme: Optional[str] = None
    alignment_score: Optional[float] = None
    
    # Cross-year evolution specific
    trend_direction: Optional[str] = None  # 'increasing', 'decreasing', 'stable'
    slope: Optional[float] = None
    r_squared: Optional[float] = None
    years_tracked: Optional[int] = None
    
    # Statistical significance
    confidence: float = Field(ge=0.0, le=1.0)
    p_value: Optional[float] = None
    supporting_periods: int = 0  # Number of periods supporting pattern
    
    # Human-readable finding
    finding: str
    
    # Metadata
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    first_occurrence: Optional[date] = None
    last_occurrence: Optional[date] = None
    
    # Hypothesis generation
    spawned_hypothesis_id: Optional[str] = None
    
    # Data quality
    data_quality: str = "sufficient"  # 'sufficient', 'partial', 'needs_more_data'
    min_periods_needed: int = 3
    periods_available: int = 0
    
    class Config:
        use_enum_values = True


# ============================================================================
# SECTION 3: Cyclical Pattern Detector
# ============================================================================

class CyclicalPatternDetector:
    """
    Detect recurring patterns aligned with 52-day magi periods.
    
    Detects:
    - Period-specific patterns (e.g., "anxiety every Mercury period")
    - Inter-period differences (e.g., "mood 2x higher in Jupiter vs Saturn")
    - Cross-year evolution (e.g., "Mercury sensitivity worsening")
    - Period card alignment (e.g., "low energy when period card is 7♠")
    
    Thread-safe and stateless.
    """
    
    # Configuration
    MIN_PERIODS_FOR_PATTERN = 3  # Need at least 3 periods of same type
    MIN_JOURNAL_ENTRIES_PER_PERIOD = 5
    SIGNIFICANCE_THRESHOLD = 0.05  # p-value threshold
    CORRELATION_THRESHOLD = 0.70  # Correlation threshold
    MIN_FOLD_INCREASE = 1.5  # Minimum fold increase for practical significance
    MIN_MOOD_DIFFERENCE = 1.5  # Minimum mood difference (on 1-10 scale)
    PERIOD_DAYS = 52  # Days per magi period
    PERIODS_PER_YEAR = 7
    
    # Symptoms to track
    TRACKED_SYMPTOMS = [
        "headache", "migraine", "anxiety", "fatigue", "insomnia",
        "irritability", "brain_fog", "low_energy", "restlessness",
        "stress", "overwhelm", "mood_low", "motivation_low"
    ]
    
    # Themes for alignment detection
    PLANET_THEMES = {
        Planet.MERCURY: ["communication", "thinking", "learning", "writing", "meetings", "technology"],
        Planet.VENUS: ["relationships", "love", "harmony", "beauty", "art", "connection"],
        Planet.MARS: ["action", "energy", "exercise", "conflict", "competition", "drive"],
        Planet.JUPITER: ["expansion", "growth", "optimism", "luck", "travel", "opportunity"],
        Planet.SATURN: ["discipline", "structure", "restriction", "responsibility", "lessons", "boundaries"],
        Planet.URANUS: ["change", "innovation", "surprise", "freedom", "breakthrough", "technology"],
        Planet.NEPTUNE: ["intuition", "dreams", "creativity", "spirituality", "imagination", "escape"],
    }
    
    def __init__(
        self,
        min_periods: int = 3,
        min_entries_per_period: int = 5,
        significance_threshold: float = 0.05
    ):
        """
        Initialize detector with configurable thresholds.
        
        Args:
            min_periods: Minimum periods required for pattern detection
            min_entries_per_period: Minimum journal entries per period
            significance_threshold: p-value threshold for significance
        """
        self.min_periods = min_periods
        self.min_entries_per_period = min_entries_per_period
        self.significance_threshold = significance_threshold
    
    async def detect_all_patterns(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[CyclicalPattern]:
        """
        Run all cyclical detection methods.
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            List of all detected cyclical patterns
        """
        patterns = []
        
        try:
            # Get period history and journal entries
            periods = await self._get_user_periods(user_id, db)
            entries_by_period = await self._group_entries_by_period(user_id, db, periods)
            
            if not periods or not entries_by_period:
                logger.info(f"[CyclicalDetector] Insufficient data for user {user_id}")
                return []
            
            # Run all detection methods
            patterns.extend(await self.detect_period_specific_symptoms(
                user_id, periods, entries_by_period
            ))
            
            patterns.extend(await self.detect_inter_period_mood_patterns(
                user_id, periods, entries_by_period
            ))
            
            patterns.extend(await self.detect_theme_alignment_patterns(
                user_id, periods, entries_by_period
            ))
            
            patterns.extend(await self.detect_cross_year_evolution(
                user_id, periods, entries_by_period
            ))
            
            # I-CHING GATE PATTERNS (micro-cycle detection)
            patterns.extend(await self.detect_gate_specific_symptoms(
                user_id, db
            ))
            
            patterns.extend(await self.detect_gate_mood_patterns(
                user_id, db
            ))
            
            patterns.extend(await self.detect_gate_line_correlations(
                user_id, db
            ))
            
            logger.info(
                f"[CyclicalDetector] Detected {len(patterns)} patterns for user {user_id}"
            )
            
        except Exception as e:
            logger.error(f"[CyclicalDetector] Error detecting patterns for user {user_id}: {e}")
        
        return patterns
    
    async def detect_period_specific_symptoms(
        self,
        user_id: int,
        periods: list[PeriodSnapshot],
        entries_by_period: dict[str, list[dict[str, Any]]]
    ) -> list[CyclicalPattern]:
        """
        Detect symptoms that recur during specific planetary periods.
        
        Algorithm:
        1. Group periods by planet type
        2. For each symptom, calculate occurrence rate by planet
        3. Compare to baseline symptom frequency
        4. Test for statistical significance (one-sample t-test)
        
        Args:
            user_id: User ID
            periods: List of period snapshots
            entries_by_period: Journal entries grouped by period key
        
        Returns:
            List of period-specific symptom patterns
        """
        patterns = []
        
        # Group periods by planet
        periods_by_planet = self._group_periods_by_planet(periods, entries_by_period)
        
        # Calculate baseline symptom rates across all entries
        all_entries = [e for entries in entries_by_period.values() for e in entries]
        baseline_rates = self._calculate_baseline_symptom_rates(all_entries)
        
        if not all_entries:
            return []
        
        # For each symptom, test for planet-specific elevation
        for symptom in self.TRACKED_SYMPTOMS:
            baseline_rate = baseline_rates.get(symptom, 0)
            
            for planet, period_data in periods_by_planet.items():
                # Check minimum periods requirement
                if len(period_data) < self.min_periods:
                    continue
                
                # Calculate symptom occurrence rate for each period
                symptom_rates = []
                for pd in period_data:
                    entries = pd['entries']
                    if len(entries) < self.min_entries_per_period:
                        continue
                    
                    symptom_count = self._count_symptom_in_entries(entries, symptom)
                    rate = symptom_count / len(entries) if entries else 0
                    symptom_rates.append(rate)
                
                if len(symptom_rates) < self.min_periods:
                    continue
                
                avg_rate = np.mean(symptom_rates)
                
                # Skip if below baseline or no practical significance
                if avg_rate <= baseline_rate or baseline_rate == 0:
                    continue
                
                fold_increase = avg_rate / baseline_rate if baseline_rate > 0 else avg_rate * 10
                
                if fold_increase < self.MIN_FOLD_INCREASE:
                    continue
                
                # Statistical test: One-sample t-test against baseline
                try:
                    if np.std(symptom_rates) == 0:
                        continue
                    
                    t_stat, p_value = stats.ttest_1samp(symptom_rates, baseline_rate)
                    
                    if np.isnan(p_value):
                        continue
                    
                    # Significant pattern?
                    if p_value < self.significance_threshold and t_stat > 0:
                        confidence = 1 - p_value
                        
                        patterns.append(CyclicalPattern(
                            user_id=user_id,
                            pattern_type=CyclicalPatternType.PERIOD_SPECIFIC_SYMPTOM,
                            planet=planet,
                            symptom=symptom,
                            occurrence_rate=round(avg_rate, 3),
                            baseline_value=round(baseline_rate, 3),
                            fold_increase=round(fold_increase, 2),
                            confidence=round(confidence, 3),
                            p_value=round(p_value, 4),
                            supporting_periods=len(symptom_rates),
                            periods_available=len(period_data),
                            finding=f"User reports {symptom} {avg_rate*100:.0f}% of the time during {planet.value} periods (baseline: {baseline_rate*100:.0f}%, {fold_increase:.1f}x increase)"
                        ))
                        
                        logger.debug(
                            f"[CyclicalDetector] Found {symptom} pattern for {planet.value}: "
                            f"rate={avg_rate:.2f}, baseline={baseline_rate:.2f}, p={p_value:.4f}"
                        )
                
                except (ValueError, ZeroDivisionError) as e:
                    logger.warning(f"[CyclicalDetector] Statistical test error: {e}")
                    continue
        
        return patterns
    
    async def detect_inter_period_mood_patterns(
        self,
        user_id: int,
        periods: list[PeriodSnapshot],
        entries_by_period: dict[str, list[dict[str, Any]]]
    ) -> list[CyclicalPattern]:
        """
        Compare mood/energy across different planetary periods.
        
        Algorithm:
        1. Group entries by planet type
        2. Calculate average mood/energy per planet
        3. Perform ANOVA to test for significant differences
        4. Identify highest and lowest planets
        
        Args:
            user_id: User ID
            periods: List of period snapshots
            entries_by_period: Journal entries grouped by period key
        
        Returns:
            List of inter-period variance patterns
        """
        patterns = []
        
        # Group periods by planet
        periods_by_planet = self._group_periods_by_planet(periods, entries_by_period)
        
        # Extract mood and energy scores by planet
        mood_by_planet = {}
        energy_by_planet = {}
        
        for planet, period_data in periods_by_planet.items():
            moods = []
            energies = []
            
            for pd in period_data:
                for entry in pd['entries']:
                    if entry.get('mood_score') is not None:
                        moods.append(entry['mood_score'])
                    if entry.get('energy_score') is not None:
                        energies.append(entry['energy_score'])
            
            if len(moods) >= self.min_entries_per_period:
                mood_by_planet[planet] = moods
            if len(energies) >= self.min_entries_per_period:
                energy_by_planet[planet] = energies
        
        # Test mood variance with ANOVA
        if len(mood_by_planet) >= 3:
            mood_pattern = self._test_metric_variance(
                user_id, mood_by_planet, "mood_score",
                CyclicalPatternType.INTER_PERIOD_MOOD_VARIANCE
            )
            if mood_pattern:
                patterns.append(mood_pattern)
        
        # Test energy variance with ANOVA
        if len(energy_by_planet) >= 3:
            energy_pattern = self._test_metric_variance(
                user_id, energy_by_planet, "energy_score",
                CyclicalPatternType.INTER_PERIOD_ENERGY_VARIANCE
            )
            if energy_pattern:
                patterns.append(energy_pattern)
        
        return patterns
    
    def _test_metric_variance(
        self,
        user_id: int,
        metric_by_planet: dict[Planet, list[float]],
        metric_name: str,
        pattern_type: CyclicalPatternType
    ) -> Optional[CyclicalPattern]:
        """
        Test if metric varies significantly across planets using ANOVA.
        
        Args:
            user_id: User ID
            metric_by_planet: Metric values grouped by planet
            metric_name: Name of the metric
            pattern_type: Type of pattern
        
        Returns:
            CyclicalPattern if significant variance detected, None otherwise
        """
        try:
            # Check for variance in each group
            valid_groups = {
                planet: values 
                for planet, values in metric_by_planet.items()
                if len(values) >= 3 and np.std(values) > 0
            }
            
            if len(valid_groups) < 3:
                return None
            
            f_stat, p_value = stats.f_oneway(*valid_groups.values())
            
            if np.isnan(p_value) or p_value >= self.significance_threshold:
                return None
            
            # Find highest and lowest planets
            avg_metrics = {
                planet: np.mean(values)
                for planet, values in valid_groups.items()
            }
            
            highest_planet = max(avg_metrics, key=avg_metrics.get)
            lowest_planet = min(avg_metrics, key=avg_metrics.get)
            
            highest_value = avg_metrics[highest_planet]
            lowest_value = avg_metrics[lowest_planet]
            difference = highest_value - lowest_value
            
            # Check practical significance
            if difference < self.MIN_MOOD_DIFFERENCE:
                return None
            
            total_periods = sum(
                1 for planet in valid_groups
                for _ in range(len(valid_groups[planet]) // self.min_entries_per_period)
            )
            
            metric_label = "Mood" if "mood" in metric_name else "Energy"
            
            return CyclicalPattern(
                user_id=user_id,
                pattern_type=pattern_type,
                planet_high=highest_planet,
                planet_low=lowest_planet,
                metric=metric_name,
                high_value=round(highest_value, 2),
                low_value=round(lowest_value, 2),
                difference=round(difference, 2),
                confidence=round(1 - p_value, 3),
                p_value=round(p_value, 4),
                supporting_periods=total_periods,
                finding=f"{metric_label} significantly higher during {highest_planet.value} periods (avg {highest_value:.1f}) vs {lowest_planet.value} periods (avg {lowest_value:.1f})"
            )
        
        except Exception as e:
            logger.warning(f"[CyclicalDetector] ANOVA test error: {e}")
            return None
    
    async def detect_theme_alignment_patterns(
        self,
        user_id: int,
        periods: list[PeriodSnapshot],
        entries_by_period: dict[str, list[dict[str, Any]]]
    ) -> list[CyclicalPattern]:
        """
        Detect alignment between journal content and period themes.
        
        Algorithm:
        1. For each period, get the magi theme
        2. Extract keywords from journal entries
        3. Calculate keyword overlap with theme keywords
        4. Compare to baseline alignment
        
        Args:
            user_id: User ID
            periods: List of period snapshots
            entries_by_period: Journal entries grouped by period key
        
        Returns:
            List of theme alignment patterns
        """
        patterns = []
        
        # Group by planet to detect consistent theme alignment
        periods_by_planet = self._group_periods_by_planet(periods, entries_by_period)
        
        for planet, period_data in periods_by_planet.items():
            if len(period_data) < self.min_periods:
                continue
            
            theme_keywords = self.PLANET_THEMES.get(planet, [])
            if not theme_keywords:
                continue
            
            # Calculate alignment scores for each period
            alignment_scores = []
            
            for pd in period_data:
                entries = pd['entries']
                if len(entries) < 3:
                    continue
                
                # Extract content from entries
                all_content = " ".join(
                    entry.get('content', '') for entry in entries
                ).lower()
                
                if not all_content:
                    continue
                
                # Count theme keyword occurrences
                keyword_matches = sum(
                    1 for keyword in theme_keywords
                    if keyword.lower() in all_content
                )
                
                # Normalize by number of keywords
                alignment = keyword_matches / len(theme_keywords) if theme_keywords else 0
                alignment_scores.append(alignment)
            
            if len(alignment_scores) < self.min_periods:
                continue
            
            avg_alignment = np.mean(alignment_scores)
            
            # Compare to baseline (expected random alignment ~0.15)
            baseline = 0.15
            
            if avg_alignment > baseline * 1.5:
                confidence = min(avg_alignment / baseline, 1.0) * 0.9
                
                patterns.append(CyclicalPattern(
                    user_id=user_id,
                    pattern_type=CyclicalPatternType.THEME_ALIGNMENT,
                    planet=planet,
                    period_theme=", ".join(theme_keywords[:3]),
                    alignment_score=round(avg_alignment, 3),
                    baseline_value=baseline,
                    confidence=round(confidence, 3),
                    supporting_periods=len(alignment_scores),
                    finding=f"Journal content during {planet.value} periods aligns with themes '{', '.join(theme_keywords[:3])}' (alignment: {avg_alignment:.0%} vs baseline {baseline:.0%})"
                ))
        
        return patterns
    
    async def detect_cross_year_evolution(
        self,
        user_id: int,
        periods: list[PeriodSnapshot],
        entries_by_period: dict[str, list[dict[str, Any]]]
    ) -> list[CyclicalPattern]:
        """
        Track pattern evolution across multiple yearly cycles.
        
        Algorithm:
        1. Group periods by year and planet
        2. Calculate metric (e.g., average mood) for each year
        3. Perform linear regression to detect trend
        4. Report patterns with significant trend
        
        Args:
            user_id: User ID
            periods: List of period snapshots
            entries_by_period: Journal entries grouped by period key
        
        Returns:
            List of cross-year evolution patterns
        """
        patterns = []
        
        # Group periods by year
        periods_by_year = defaultdict(list)
        for period in periods:
            year = period.year
            period_key = f"{period.planet.value}_{period.start_date.isoformat()}"
            entries = entries_by_period.get(period_key, [])
            periods_by_year[year].append({
                'period': period,
                'entries': entries
            })
        
        if len(periods_by_year) < 2:
            return []  # Need at least 2 years
        
        # For each planet, track metrics across years
        for planet in Planet:
            metric_by_year = {}
            
            for year, year_periods in periods_by_year.items():
                planet_periods = [
                    p for p in year_periods
                    if p['period'].planet == planet
                ]
                
                if not planet_periods:
                    continue
                
                # Calculate average mood for this planet in this year
                moods = []
                for pd in planet_periods:
                    for entry in pd['entries']:
                        if entry.get('mood_score') is not None:
                            moods.append(entry['mood_score'])
                
                if len(moods) >= self.min_entries_per_period:
                    metric_by_year[year] = np.mean(moods)
            
            if len(metric_by_year) < 2:
                continue
            
            # Linear regression to detect trend
            years = sorted(metric_by_year.keys())
            values = [metric_by_year[y] for y in years]
            
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    range(len(years)), values
                )
                
                # Significant trend with meaningful slope?
                if p_value < self.significance_threshold and abs(slope) > 0.3:
                    trend_direction = 'increasing' if slope > 0 else 'decreasing'
                    r_squared = r_value ** 2
                    
                    patterns.append(CyclicalPattern(
                        user_id=user_id,
                        pattern_type=CyclicalPatternType.CROSS_YEAR_EVOLUTION,
                        planet=planet,
                        metric='mood_score',
                        trend_direction=trend_direction,
                        slope=round(slope, 3),
                        r_squared=round(r_squared, 3),
                        confidence=round(1 - p_value, 3),
                        p_value=round(p_value, 4),
                        years_tracked=len(years),
                        supporting_periods=len(years),
                        first_occurrence=periods[0].start_date if periods else None,
                        last_occurrence=periods[-1].end_date if periods else None,
                        finding=f"Mood during {planet.value} periods {trend_direction} across {len(years)} years (slope: {slope:.2f}, R²: {r_squared:.2f})"
                    ))
            
            except Exception as e:
                logger.warning(f"[CyclicalDetector] Regression error for {planet}: {e}")
                continue
        
        return patterns
    
    # =========================================================================
    # I-CHING GATE PATTERN DETECTION (Micro-Cycle ~6 days per gate)
    # =========================================================================
    
    async def detect_gate_specific_symptoms(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[CyclicalPattern]:
        """
        Detect symptoms that recur during specific I-Ching gates.
        
        Gates cycle approximately every 5.7 days (360° / 64 gates).
        This method groups journal entries by the Sun gate at time of entry.
        
        Algorithm:
        1. Get all journal entries with their timestamps
        2. Calculate Sun gate for each entry timestamp
        3. Group entries by gate
        4. For each symptom, calculate occurrence rate per gate
        5. Compare to baseline and test significance
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of gate-specific symptom patterns
        """
        patterns = []
        
        try:
            from src.app.modules.intelligence.iching import IChingKernel, GATE_DATABASE
            
            kernel = IChingKernel()
            
            # Get all journal entries
            entries = await self._get_all_journal_entries(user_id, db)
            if len(entries) < 50:  # Need sufficient data
                return []
            
            # Group entries by gate
            entries_by_gate: dict[int, list] = {}
            for entry in entries:
                entry_dt = entry.get("created_at") or entry.get("timestamp")
                if not entry_dt:
                    continue
                
                if isinstance(entry_dt, str):
                    entry_dt = datetime.fromisoformat(entry_dt.replace("Z", "+00:00"))
                
                try:
                    daily = kernel.get_daily_code(entry_dt)
                    gate = daily.sun_activation.gate
                    if gate not in entries_by_gate:
                        entries_by_gate[gate] = []
                    entries_by_gate[gate].append(entry)
                except Exception:
                    continue
            
            # Calculate baseline symptom rates
            baseline_rates = self._calculate_baseline_symptom_rates(entries)
            
            # For each symptom, check for gate-specific patterns
            for symptom in self.TRACKED_SYMPTOMS:
                baseline_rate = baseline_rates.get(symptom, 0)
                if baseline_rate == 0:
                    continue
                
                for gate, gate_entries in entries_by_gate.items():
                    if len(gate_entries) < 3:  # Need minimum occurrences
                        continue
                    
                    symptom_count = self._count_symptom_in_entries(gate_entries, symptom)
                    rate = symptom_count / len(gate_entries)
                    
                    # Significant elevation?
                    fold_increase = rate / baseline_rate if baseline_rate > 0 else 0
                    
                    if fold_increase >= self.MIN_FOLD_INCREASE:
                        gate_data = GATE_DATABASE.get(gate)
                        
                        patterns.append(CyclicalPattern(
                            user_id=user_id,
                            pattern_type=CyclicalPatternType.GATE_SPECIFIC_SYMPTOM,
                            sun_gate=gate,
                            gate_name=gate_data.hd_name if gate_data else f"Gate {gate}",
                            gene_key_gift=gate_data.gk_gift if gate_data else None,
                            symptom=symptom,
                            occurrence_rate=round(rate, 3),
                            baseline_value=round(baseline_rate, 3),
                            fold_increase=round(fold_increase, 2),
                            confidence=min(0.95, 0.5 + (fold_increase - 1) * 0.15),
                            supporting_periods=len(gate_entries),
                            finding=f"{symptom.title()} occurs {rate*100:.0f}% during Gate {gate} "
                                    f"({gate_data.hd_name if gate_data else 'Unknown'}), "
                                    f"{fold_increase:.1f}x baseline"
                        ))
            
        except Exception as e:
            logger.warning(f"[CyclicalDetector] Gate symptom detection error: {e}")
        
        return patterns
    
    async def detect_gate_mood_patterns(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[CyclicalPattern]:
        """
        Detect mood/energy patterns across I-Ching gates.
        
        Groups entries by gate and compares average mood/energy.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of inter-gate mood patterns
        """
        patterns = []
        
        try:
            from src.app.modules.intelligence.iching import IChingKernel, GATE_DATABASE
            
            kernel = IChingKernel()
            entries = await self._get_all_journal_entries(user_id, db)
            
            if len(entries) < 50:
                return []
            
            # Group mood scores by gate
            mood_by_gate: dict[int, list[float]] = {}
            energy_by_gate: dict[int, list[float]] = {}
            
            for entry in entries:
                entry_dt = entry.get("created_at") or entry.get("timestamp")
                mood = entry.get("mood_score")
                energy = entry.get("energy_score")
                
                if not entry_dt or (mood is None and energy is None):
                    continue
                
                if isinstance(entry_dt, str):
                    entry_dt = datetime.fromisoformat(entry_dt.replace("Z", "+00:00"))
                
                try:
                    daily = kernel.get_daily_code(entry_dt)
                    gate = daily.sun_activation.gate
                    
                    if mood is not None:
                        if gate not in mood_by_gate:
                            mood_by_gate[gate] = []
                        mood_by_gate[gate].append(float(mood))
                    
                    if energy is not None:
                        if gate not in energy_by_gate:
                            energy_by_gate[gate] = []
                        energy_by_gate[gate].append(float(energy))
                except Exception:
                    continue
            
            # Find gates with significantly different mood/energy
            all_moods = [m for moods in mood_by_gate.values() for m in moods]
            overall_mood_avg = np.mean(all_moods) if all_moods else 0
            overall_mood_std = np.std(all_moods) if all_moods else 1
            
            for gate, moods in mood_by_gate.items():
                if len(moods) < 3:
                    continue
                
                gate_avg = np.mean(moods)
                z_score = (gate_avg - overall_mood_avg) / overall_mood_std if overall_mood_std > 0 else 0
                
                # Significant deviation (|z| > 1.5)?
                if abs(z_score) > 1.5:
                    gate_data = GATE_DATABASE.get(gate)
                    direction = "higher" if z_score > 0 else "lower"
                    
                    patterns.append(CyclicalPattern(
                        user_id=user_id,
                        pattern_type=CyclicalPatternType.INTER_GATE_MOOD_VARIANCE,
                        sun_gate=gate,
                        gate_name=gate_data.hd_name if gate_data else f"Gate {gate}",
                        gene_key_gift=gate_data.gk_gift if gate_data else None,
                        metric="mood_score",
                        metric_value=round(gate_avg, 2),
                        baseline_value=round(overall_mood_avg, 2),
                        difference=round(gate_avg - overall_mood_avg, 2),
                        confidence=min(0.95, 0.5 + abs(z_score) * 0.1),
                        supporting_periods=len(moods),
                        finding=f"Mood is {direction} during Gate {gate} "
                                f"({gate_data.hd_name if gate_data else 'Unknown'}): "
                                f"avg {gate_avg:.1f} vs baseline {overall_mood_avg:.1f}"
                    ))
            
        except Exception as e:
            logger.warning(f"[CyclicalDetector] Gate mood detection error: {e}")
        
        return patterns
    
    async def detect_gate_line_correlations(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[CyclicalPattern]:
        """
        Detect patterns specific to gate lines (1-6).
        
        Each line is active for approximately ~22.5 hours.
        Lines have specific archetypes that may correlate with user experiences.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of line-specific patterns
        """
        patterns = []
        
        try:
            from src.app.modules.intelligence.iching import IChingKernel, GATE_DATABASE
            
            kernel = IChingKernel()
            
            # Get all journal entries
            entries = await self._get_all_journal_entries(user_id, db)
            if len(entries) < 100:  # Need more data for line-level patterns
                return []
            
            # Group entries by gate AND line
            entries_by_gate_line: dict[tuple[int, int], list] = {}
            for entry in entries:
                entry_dt = entry.get("created_at") or entry.get("timestamp")
                if not entry_dt:
                    continue
                
                if isinstance(entry_dt, str):
                    entry_dt = datetime.fromisoformat(entry_dt.replace("Z", "+00:00"))
                
                try:
                    daily = kernel.get_daily_code(entry_dt)
                    gate = daily.sun_activation.gate
                    line = daily.sun_activation.line
                    key = (gate, line)
                    if key not in entries_by_gate_line:
                        entries_by_gate_line[key] = []
                    entries_by_gate_line[key].append(entry)
                except Exception:
                    continue
            
            # Calculate mood distributions per line across all gates
            mood_by_line = {i: [] for i in range(1, 7)}
            
            for (gate, line), line_entries in entries_by_gate_line.items():
                moods = [e.get("mood_score") for e in line_entries if e.get("mood_score")]
                if moods:
                    mood_by_line[line].extend(moods)
            
            # Calculate overall mood average
            all_moods = [m for moods in mood_by_line.values() for m in moods]
            if not all_moods:
                return []
            
            overall_mood_avg = np.mean(all_moods)
            overall_mood_std = np.std(all_moods)
            
            # Test each line for significant deviation
            for line_num in range(1, 7):
                line_moods = mood_by_line[line_num]
                if len(line_moods) < 10:  # Need sufficient samples
                    continue
                
                line_avg = np.mean(line_moods)
                
                # Calculate z-score
                z_score = (line_avg - overall_mood_avg) / (overall_mood_std + 0.001)
                
                # Significant deviation (|z| > 1.5)?
                if abs(z_score) > 1.5:
                    from src.app.modules.intelligence.iching.kernel import LINE_ARCHETYPES
                    
                    line_archetype = LINE_ARCHETYPES.get(line_num)
                    direction = "higher" if z_score > 0 else "lower"
                    
                    patterns.append(CyclicalPattern(
                        user_id=user_id,
                        pattern_type=CyclicalPatternType.GATE_LINE_CORRELATION,
                        gate_line=line_num,
                        metric="mood_score",
                        metric_value=round(line_avg, 2),
                        baseline_value=round(overall_mood_avg, 2),
                        difference=round(line_avg - overall_mood_avg, 2),
                        confidence=min(0.95, 0.5 + abs(z_score) * 0.1),
                        supporting_periods=len(line_moods),
                        finding=f"Line {line_num} ({line_archetype.name if line_archetype else 'Unknown'}) "
                                f"shows {direction} mood: avg {line_avg:.1f} vs baseline {overall_mood_avg:.1f}. "
                                f"Theme: {line_archetype.theme if line_archetype else 'N/A'}"
                    ))
            
        except Exception as e:
            logger.warning(f"[CyclicalDetector] Line correlation detection error: {e}")
        
        return patterns
    
    async def _get_all_journal_entries(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[dict]:
        """Get all journal entries for a user."""
        from src.app.models.journal import JournalEntry
        
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user_id)
            .order_by(JournalEntry.created_at.desc())
        )
        entries = result.scalars().all()
        
        return [
            {
                "created_at": e.created_at,
                "content": e.content,
                "mood_score": e.mood_score if hasattr(e, "mood_score") else None,
                "energy_score": e.energy_score if hasattr(e, "energy_score") else None,
                "symptoms": e.symptoms if hasattr(e, "symptoms") else [],
            }
            for e in entries
        ]
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    async def _get_user_periods(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list[PeriodSnapshot]:
        """
        Get historical period data for the user.
        
        Uses cardology birth data to reconstruct past periods.
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            List of PeriodSnapshot objects
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.data:
            return []
        
        # Get birth date from profile
        birth_data = profile.data.get('birth_date') or profile.data.get('genesis', {}).get('birth_datetime')
        if not birth_data:
            return []
        
        try:
            if isinstance(birth_data, str):
                birth_date = datetime.fromisoformat(birth_data.replace('Z', '+00:00')).date()
            elif isinstance(birth_data, datetime):
                birth_date = birth_data.date()
            elif isinstance(birth_data, date):
                birth_date = birth_data
            else:
                return []
        except Exception as e:
            logger.warning(f"[CyclicalDetector] Error parsing birth date: {e}")
            return []
        
        # Generate period history
        periods = []
        current_date = datetime.now(UTC).date()
        
        # Calculate how many periods since birth
        days_since_birth = (current_date - birth_date).days
        
        # Go back up to 3 years (21 periods)
        max_periods = min(21, days_since_birth // self.PERIOD_DAYS)
        
        for i in range(max_periods):
            # Calculate period boundaries
            period_end = current_date - timedelta(days=i * self.PERIOD_DAYS)
            period_start = period_end - timedelta(days=self.PERIOD_DAYS - 1)
            
            # Skip future periods
            if period_start > current_date:
                continue
            
            # Calculate which planet rules this period
            days_from_birthday = (period_start - birth_date).days % 364
            period_number = (days_from_birthday // self.PERIOD_DAYS) % self.PERIODS_PER_YEAR
            
            planet = list(Planet)[period_number]
            year = period_start.year
            
            periods.append(PeriodSnapshot(
                planet=planet,
                start_date=period_start,
                end_date=period_end,
                period_number=period_number + 1,
                year=year
            ))
        
        return periods
    
    async def _group_entries_by_period(
        self,
        user_id: int,
        db: AsyncSession,
        periods: list[PeriodSnapshot]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Group journal entries by period.
        
        Args:
            user_id: User ID
            db: Database session
            periods: List of period snapshots
        
        Returns:
            Dictionary mapping period key to list of entries
        """
        from src.app.models.insight import JournalEntry
        
        if not periods:
            return {}
        
        # Get date range for query
        earliest = min(p.start_date for p in periods)
        latest = max(p.end_date for p in periods)
        
        # Fetch all entries in range
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user_id)
            .where(JournalEntry.created_at >= datetime.combine(earliest, datetime.min.time()))
            .where(JournalEntry.created_at <= datetime.combine(latest, datetime.max.time()))
            .order_by(JournalEntry.created_at)
        )
        entries = result.scalars().all()
        
        # Group entries by period
        entries_by_period = defaultdict(list)
        
        for entry in entries:
            entry_date = entry.created_at.date()
            
            for period in periods:
                if period.start_date <= entry_date <= period.end_date:
                    period_key = f"{period.planet.value}_{period.start_date.isoformat()}"
                    entries_by_period[period_key].append({
                        'id': entry.id,
                        'content': entry.content,
                        'mood_score': entry.mood_score,
                        'energy_score': entry.context_snapshot.get('energy_score') if entry.context_snapshot else None,
                        'tags': entry.tags or [],
                        'symptoms': self._extract_symptoms_from_entry(entry),
                        'created_at': entry.created_at.isoformat()
                    })
                    break
        
        return dict(entries_by_period)
    
    def _group_periods_by_planet(
        self,
        periods: list[PeriodSnapshot],
        entries_by_period: dict[str, list[dict[str, Any]]]
    ) -> dict[Planet, list[dict[str, Any]]]:
        """Group periods by planet type."""
        periods_by_planet = defaultdict(list)
        
        for period in periods:
            period_key = f"{period.planet.value}_{period.start_date.isoformat()}"
            entries = entries_by_period.get(period_key, [])
            
            periods_by_planet[period.planet].append({
                'period': period,
                'entries': entries
            })
        
        return dict(periods_by_planet)
    
    def _calculate_baseline_symptom_rates(
        self,
        all_entries: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate baseline symptom rates across all entries."""
        if not all_entries:
            return {}
        
        rates = {}
        for symptom in self.TRACKED_SYMPTOMS:
            count = sum(
                1 for e in all_entries
                if symptom in e.get('symptoms', [])
            )
            rates[symptom] = count / len(all_entries)
        
        return rates
    
    def _count_symptom_in_entries(
        self,
        entries: list[dict[str, Any]],
        symptom: str
    ) -> int:
        """Count occurrences of a symptom in entries."""
        return sum(
            1 for e in entries
            if symptom in e.get('symptoms', [])
        )
    
    def _extract_symptoms_from_entry(self, entry) -> list[str]:
        """Extract symptoms from a journal entry."""
        symptoms = []
        
        # Check tags
        tags = entry.tags or []
        for tag in tags:
            tag_lower = tag.lower()
            for symptom in self.TRACKED_SYMPTOMS:
                if symptom in tag_lower:
                    symptoms.append(symptom)
        
        # Check content for symptom keywords
        content = (entry.content or '').lower()
        for symptom in self.TRACKED_SYMPTOMS:
            if symptom.replace('_', ' ') in content or symptom in content:
                if symptom not in symptoms:
                    symptoms.append(symptom)
        
        return symptoms


# ============================================================================
# SECTION 4: Cyclical Pattern Storage
# ============================================================================

class CyclicalPatternStorage:
    """
    Store and retrieve cyclical patterns.
    
    Patterns are stored in UserProfile.data['cyclical_patterns'] as JSONB.
    """
    
    async def store_pattern(
        self,
        pattern: CyclicalPattern,
        db: AsyncSession
    ) -> None:
        """Store a cyclical pattern."""
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == pattern.user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return
        
        if 'cyclical_patterns' not in profile.data:
            profile.data['cyclical_patterns'] = []
        
        # Check for duplicate (same type, planet, symptom)
        existing_idx = None
        for i, p in enumerate(profile.data['cyclical_patterns']):
            if (
                p.get('pattern_type') == pattern.pattern_type.value and
                p.get('planet') == (pattern.planet.value if pattern.planet else None) and
                p.get('symptom') == pattern.symptom
            ):
                existing_idx = i
                break
        
        pattern_dict = pattern.model_dump(mode="json")
        
        if existing_idx is not None:
            profile.data['cyclical_patterns'][existing_idx] = pattern_dict
        else:
            profile.data['cyclical_patterns'].append(pattern_dict)
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(profile, "data")
        await db.commit()
    
    async def store_patterns(
        self,
        patterns: list[CyclicalPattern],
        db: AsyncSession
    ) -> None:
        """Store multiple cyclical patterns."""
        for pattern in patterns:
            await self.store_pattern(pattern, db)
    
    async def get_patterns(
        self,
        user_id: int,
        min_confidence: float = 0.0
    ) -> list[CyclicalPattern]:
        """Get cyclical patterns for a user."""
        from src.app.core.memory.active_memory import get_active_memory
        
        memory = get_active_memory()
        await memory.initialize()
        
        # Try cache first
        cached = await memory.get(f"cyclical_patterns:{user_id}")
        
        if cached:
            patterns_data = cached
        else:
            from src.app.core.db.database import local_session
            
            async with local_session() as db:
                result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                
                if not profile or 'cyclical_patterns' not in profile.data:
                    return []
                
                patterns_data = profile.data['cyclical_patterns']
                
                # Cache for 1 hour
                await memory.set(
                    f"cyclical_patterns:{user_id}",
                    patterns_data,
                    ttl=3600
                )
        
        # Parse and filter
        patterns = [CyclicalPattern(**p) for p in patterns_data]
        
        if min_confidence > 0:
            patterns = [p for p in patterns if p.confidence >= min_confidence]
        
        return patterns


# ============================================================================
# SECTION 5: Module Exports
# ============================================================================

__all__ = [
    "Planet",
    "CyclicalPatternType",
    "PeriodSnapshot",
    "CyclicalPattern",
    "CyclicalPatternDetector",
    "CyclicalPatternStorage",
]
