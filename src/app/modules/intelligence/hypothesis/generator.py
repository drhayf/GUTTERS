"""
Hypothesis generation engine.

Reads Observer patterns and generates testable theories.

Uses WeightedConfidenceCalculator for initial confidence computation
instead of hard-coded formulas.
"""

import uuid
from datetime import UTC, datetime
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.app.core.events.bus import get_event_bus
from src.app.protocol.events import HYPOTHESIS_GENERATED

from .confidence import (
    ConfidenceThresholds,
    EvidenceRecord,
    EvidenceType,
    WeightedConfidenceCalculator,
)
from .models import Hypothesis, HypothesisStatus, HypothesisType


class HypothesisGenerator:
    """Generate theories from Observer patterns."""

    def __init__(self, llm):
        self.llm = llm
        self.event_bus = get_event_bus()
        self.calculator = WeightedConfidenceCalculator()

    async def _ensure_event_bus(self):
        """Ensure event bus is initialized."""
        if not self.event_bus.redis_client:
            await self.event_bus.initialize()

    async def _get_magi_context(self, user_id: int) -> dict | None:
        """
        Fetch magi chronos context for temporal_context field.

        Returns dict with period card, planetary ruler, theme, guidance,
        plus I-Ching hexagram data from Council of Systems.
        Returns None if unable to fetch (fails gracefully).
        """
        try:
            from src.app.core.state.chronos import get_chronos_manager
            chronos_manager = get_chronos_manager()
            chronos_state = await chronos_manager.get_user_chronos(user_id)

            context = {}

            if chronos_state:
                context = {
                    "period_card": chronos_state.get("current_card", {}).get("name"),
                    "period_day": 52 - (chronos_state.get("days_remaining", 0) or 0),
                    "period_total": 52,
                    "planetary_ruler": chronos_state.get("current_planet"),
                    "theme": chronos_state.get("theme"),
                    "guidance": chronos_state.get("guidance"),
                    "period_start": chronos_state.get("period_start"),
                    "period_end": chronos_state.get("period_end"),
                    "progress_percent": round(
                        ((52 - (chronos_state.get("days_remaining", 0) or 0)) / 52) * 100, 2
                    ),
                }

            # Add I-Ching hexagram from Council of Systems
            try:
                from src.app.modules.intelligence.council import get_council_service
                council = get_council_service()
                hexagram = council.get_current_hexagram()

                if hexagram:
                    context["sun_gate"] = hexagram.sun_gate
                    context["sun_line"] = hexagram.sun_line
                    context["sun_gate_name"] = hexagram.sun_gate_name
                    context["sun_gene_key_gift"] = hexagram.sun_gene_key_gift
                    context["earth_gate"] = hexagram.earth_gate
            except Exception as e:
                print(f"[HypothesisGenerator] Council context not available: {e}")

            return context if context else None

        except Exception as e:
            print(f"[HypothesisGenerator] Failed to fetch magi context: {e}")

        return None

    async def generate_from_patterns(
        self,
        user_id: int,
        patterns: List[dict]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses from Observer patterns.

        Args:
            user_id: User ID
            patterns: List of Observer findings

        Returns:
            List of generated hypotheses
        """
        await self._ensure_event_bus()

        # Fetch magi context once for all hypotheses in this batch
        temporal_context = await self._get_magi_context(user_id)

        hypotheses = []

        for pattern in patterns:
            hypothesis = None

            # Solar sensitivity hypothesis
            if pattern.get('pattern_type') == 'solar_symptom':
                hypothesis = self._generate_solar_sensitivity_hypothesis(
                    user_id,
                    pattern,
                    temporal_context
                )

            # Lunar pattern hypothesis
            elif pattern.get('pattern_type') == 'lunar_phase':
                hypothesis = self._generate_lunar_pattern_hypothesis(
                    user_id,
                    pattern,
                    temporal_context
                )

            # Temporal pattern hypothesis
            elif pattern.get('pattern_type') == 'day_of_week':
                hypothesis = self._generate_temporal_hypothesis(
                    user_id,
                    pattern,
                    temporal_context
                )

            # Transit correlation hypothesis
            elif pattern.get('pattern_type') == 'transit_theme':
                hypothesis = self._generate_transit_hypothesis(
                    user_id,
                    pattern,
                    temporal_context
                )

            if hypothesis:
                hypotheses.append(hypothesis)

                # Publish event
                await self.event_bus.publish(
                    HYPOTHESIS_GENERATED,
                    {
                        "user_id": hypothesis.user_id,
                        "hypothesis_id": hypothesis.id,
                        "hypothesis_type": hypothesis.hypothesis_type.value,
                        "confidence": hypothesis.confidence,
                        "generated_at": hypothesis.generated_at.isoformat()
                    }
                )

        return hypotheses

    def _generate_solar_sensitivity_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about solar sensitivity."""

        # Extract pattern details
        correlation = pattern.get('correlation', 0)
        symptom = pattern.get('symptom', 'symptoms')
        data_points = pattern.get('data_points', 0)

        # Use WeightedConfidenceCalculator for initial confidence
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=data_points,
            correlation=correlation,
            source="observer_solar"
        )

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence,
            contradictions=0,
            days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        # Create hypothesis ID
        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "solar_symptom",
                "correlation": correlation,
                "p_value": pattern.get('p_value', 0),
                "data_points": data_points,
                "symptom": symptom,
            },
            source="observer_solar",
            reasoning=(
                f"Observer detected solar-symptom correlation (r={correlation:.2f}) "
                f"across {data_points} data points"
            ),
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
            claim=f"User is electromagnetically sensitive, experiencing {symptom} during geomagnetic storms",
            predicted_value="Sensitive to solar activity (Kp > 5)",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "observer_pattern",
                "correlation": correlation,
                "p_value": pattern.get('p_value', 0),
                "data_points": data_points,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_lunar_pattern_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about lunar patterns."""

        phase = pattern.get('phase', 'unknown')
        mood_diff = pattern.get('mood_diff', 0)
        energy_diff = pattern.get('energy_diff', 0)
        data_points = pattern.get('data_points', 0)
        pattern_confidence = pattern.get('confidence', 0.5)

        # Use WeightedConfidenceCalculator for initial confidence
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.COSMIC_CORRELATION,
            data_points=data_points,
            correlation=pattern_confidence,
            source="observer_lunar"
        )

        # Determine claim based on pattern
        if mood_diff < -1.5:
            claim = f"User experiences mood drops during {phase} moon phase"
            predicted_value = f"Low mood during {phase}"
        elif mood_diff > 1.5:
            claim = f"User experiences mood elevation during {phase} moon phase"
            predicted_value = f"High mood during {phase}"
        elif energy_diff < -1.5:
            claim = f"User experiences energy depletion during {phase} moon phase"
            predicted_value = f"Low energy during {phase}"
        else:
            claim = f"User experiences energy peaks during {phase} moon phase"
            predicted_value = f"High energy during {phase}"

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence,
            contradictions=0,
            days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        # Create hypothesis ID
        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.COSMIC_CORRELATION,
            data={
                "pattern_type": "lunar_phase",
                "phase": phase,
                "mood_diff": mood_diff,
                "energy_diff": energy_diff,
                "data_points": data_points,
                "pattern_confidence": pattern_confidence,
            },
            source="observer_lunar",
            reasoning=f"Observer detected lunar {phase} phase correlation with mood/energy patterns",
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
            claim=claim,
            predicted_value=predicted_value,
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "observer_pattern",
                "phase": phase,
                "mood_diff": mood_diff,
                "energy_diff": energy_diff,
                "data_points": data_points,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_temporal_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about time-based patterns."""

        day = pattern.get('day', 'unknown')
        mood_diff = pattern.get('mood_diff', 0)
        data_points = pattern.get('data_points', 0)
        pattern_confidence = pattern.get('confidence', 0.5)

        # Use WeightedConfidenceCalculator for initial confidence
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=data_points,
            correlation=pattern_confidence,
            source="observer"
        )

        if mood_diff < 0:
            claim = f"User consistently experiences mood drops on {day}s"
            predicted_value = f"Low mood on {day}"
        else:
            claim = f"User consistently experiences mood elevation on {day}s"
            predicted_value = f"High mood on {day}"

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence,
            contradictions=0,
            days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        # Create hypothesis ID
        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "day_of_week",
                "day": day,
                "mood_diff": mood_diff,
                "data_points": data_points,
                "pattern_confidence": pattern_confidence,
            },
            source="observer",
            reasoning=f"Observer detected consistent {day} patterns in mood data",
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.TEMPORAL_PATTERN,
            claim=claim,
            predicted_value=predicted_value,
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "observer_pattern",
                "day": day,
                "mood_diff": mood_diff,
                "data_points": data_points,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_transit_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about transit effects."""

        transit = pattern.get('transit', 'unknown')
        theme = pattern.get('theme', 'unknown')
        frequency = pattern.get('frequency', 0)
        data_points = pattern.get('data_points', 0)

        # Use WeightedConfidenceCalculator for initial confidence
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.TRANSIT_ALIGNMENT,
            data_points=data_points or frequency,
            correlation=min(frequency * 0.1, 0.9) if frequency else 0.5,
            source="observer_transit"
        )

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence,
            contradictions=0,
            days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        # Create hypothesis ID
        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.TRANSIT_ALIGNMENT,
            data={
                "pattern_type": "transit_theme",
                "transit": transit,
                "theme": theme,
                "frequency": frequency,
                "data_points": data_points,
            },
            source="observer_transit",
            reasoning=f"Observer detected theme '{theme}' correlating with {transit} transit",
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.TRANSIT_EFFECT,
            claim=f"User experiences {theme} themes when {transit} is active",
            predicted_value=f"{theme} during {transit}",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "observer_pattern",
                "transit": transit,
                "theme": theme,
                "frequency": frequency,
                "data_points": data_points,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    async def generate_from_cyclical_patterns(
        self,
        user_id: int,
        patterns: List[dict]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses from cyclical magi period patterns.

        Cyclical patterns are detected across 52-day planetary periods
        and can spawn hypotheses about:
        - Period-specific sensitivities (e.g., "anxiety during Mercury periods")
        - Inter-period mood variance (e.g., "mood higher during Jupiter")
        - Theme alignment (e.g., "communication focus during Mercury")
        - Cross-year evolution (e.g., "Saturn periods improving over time")

        Args:
            user_id: User ID
            patterns: List of cyclical pattern dicts from Observer

        Returns:
            List of generated hypotheses
        """
        await self._ensure_event_bus()

        # Fetch magi context once for all hypotheses
        temporal_context = await self._get_magi_context(user_id)

        hypotheses = []

        for pattern in patterns:
            hypothesis = None
            pattern_type = pattern.get('pattern_type', '')

            # Period-specific symptom hypothesis
            if pattern_type == 'period_specific_symptom':
                hypothesis = self._generate_period_symptom_hypothesis(
                    user_id, pattern, temporal_context
                )

            # Inter-period mood variance hypothesis
            elif pattern_type in ['inter_period_mood_variance', 'inter_period_energy_variance']:
                hypothesis = self._generate_period_variance_hypothesis(
                    user_id, pattern, temporal_context
                )

            # Theme alignment hypothesis
            elif pattern_type == 'theme_alignment':
                hypothesis = self._generate_theme_alignment_hypothesis(
                    user_id, pattern, temporal_context
                )

            # Cross-year evolution hypothesis
            elif pattern_type == 'cross_year_evolution':
                hypothesis = self._generate_evolution_hypothesis(
                    user_id, pattern, temporal_context
                )

            if hypothesis:
                hypotheses.append(hypothesis)

                # Publish event
                await self.event_bus.publish(
                    HYPOTHESIS_GENERATED,
                    {
                        "user_id": hypothesis.user_id,
                        "hypothesis_id": hypothesis.id,
                        "hypothesis_type": hypothesis.hypothesis_type.value,
                        "confidence": hypothesis.confidence,
                        "source": "cyclical_pattern",
                        "pattern_type": pattern_type,
                        "generated_at": hypothesis.generated_at.isoformat()
                    }
                )

        return hypotheses

    def _generate_period_symptom_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about period-specific symptoms."""

        planet = pattern.get('planet', 'Unknown')
        symptom = pattern.get('symptom', 'symptoms')
        occurrence_rate = pattern.get('occurrence_rate', 0)
        fold_increase = pattern.get('fold_increase', 1)
        p_value = pattern.get('p_value', 0)
        confidence = pattern.get('confidence', 0.5)
        supporting_periods = pattern.get('supporting_periods', 0)

        # Use WeightedConfidenceCalculator for initial confidence
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=supporting_periods * 10,  # Approximate entries per period
            correlation=confidence,
            source="observer_cyclical"
        )

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence, contradictions=0, days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "period_specific_symptom",
                "planet": planet,
                "symptom": symptom,
                "occurrence_rate": occurrence_rate,
                "fold_increase": fold_increase,
                "p_value": p_value,
                "supporting_periods": supporting_periods,
            },
            source="observer_cyclical",
            reasoning=(
                f"Cyclical detector found {symptom} occurs {occurrence_rate*100:.0f}% "
                f"during {planet} periods ({fold_increase:.1f}x baseline)"
            ),
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.CYCLICAL_PATTERN,
            claim=f"User experiences {symptom} during {planet} periods ({fold_increase:.1f}x more than baseline)",
            predicted_value=f"{symptom} during {planet}",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "cyclical_pattern",
                "pattern_type": "period_specific_symptom",
                "planet": planet,
                "symptom": symptom,
                "occurrence_rate": occurrence_rate,
                "fold_increase": fold_increase,
                "supporting_periods": supporting_periods,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_period_variance_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about inter-period mood/energy variance."""

        planet_high = pattern.get('planet_high', 'Unknown')
        planet_low = pattern.get('planet_low', 'Unknown')
        metric = pattern.get('metric', 'mood_score')
        high_value = pattern.get('high_value', 0)
        low_value = pattern.get('low_value', 0)
        difference = pattern.get('difference', 0)
        p_value = pattern.get('p_value', 0)
        confidence = pattern.get('confidence', 0.5)
        supporting_periods = pattern.get('supporting_periods', 0)

        metric_label = "Mood" if "mood" in metric else "Energy"

        # Use WeightedConfidenceCalculator
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=supporting_periods * 10,
            correlation=confidence,
            source="observer_cyclical"
        )

        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence, contradictions=0, days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        hypothesis_id = str(uuid.uuid4())

        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "inter_period_variance",
                "planet_high": planet_high,
                "planet_low": planet_low,
                "metric": metric,
                "high_value": high_value,
                "low_value": low_value,
                "difference": difference,
                "p_value": p_value,
                "supporting_periods": supporting_periods,
            },
            source="observer_cyclical",
            reasoning=(
                f"ANOVA detected significant {metric_label} variance: {planet_high} "
                f"({high_value:.1f}) vs {planet_low} ({low_value:.1f})"
            ),
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.CYCLICAL_PATTERN,
            claim=(
                f"User's {metric_label.lower()} is significantly higher during "
                f"{planet_high} periods ({high_value:.1f}) compared to {planet_low} "
                f"periods ({low_value:.1f})"
            ),
            predicted_value=f"Higher {metric_label.lower()} during {planet_high}",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "cyclical_pattern",
                "pattern_type": "inter_period_variance",
                "planet_high": planet_high,
                "planet_low": planet_low,
                "metric": metric,
                "high_value": high_value,
                "low_value": low_value,
                "difference": difference,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_theme_alignment_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about theme alignment patterns."""

        planet = pattern.get('planet', 'Unknown')
        period_theme = pattern.get('period_theme', 'unknown themes')
        alignment_score = pattern.get('alignment_score', 0)
        confidence = pattern.get('confidence', 0.5)
        supporting_periods = pattern.get('supporting_periods', 0)

        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=supporting_periods * 5,
            correlation=confidence,
            source="observer_cyclical"
        )

        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence, contradictions=0, days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        hypothesis_id = str(uuid.uuid4())

        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "theme_alignment",
                "planet": planet,
                "period_theme": period_theme,
                "alignment_score": alignment_score,
                "supporting_periods": supporting_periods,
            },
            source="observer_cyclical",
            reasoning=(
                f"Journal content during {planet} periods aligns with themes "
                f"'{period_theme}' ({alignment_score:.0%} alignment)"
            ),
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.THEME_CORRELATION,
            claim=(
                f"User's journal content naturally aligns with {planet} period themes "
                f"({period_theme}) during those periods"
            ),
            predicted_value=f"Theme alignment: {period_theme}",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "cyclical_pattern",
                "pattern_type": "theme_alignment",
                "planet": planet,
                "period_theme": period_theme,
                "alignment_score": alignment_score,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    def _generate_evolution_hypothesis(
        self,
        user_id: int,
        pattern: dict,
        temporal_context: dict | None = None
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about cross-year evolution patterns."""

        planet = pattern.get('planet', 'Unknown')
        metric = pattern.get('metric', 'mood_score')
        trend_direction = pattern.get('trend_direction', 'stable')
        slope = pattern.get('slope', 0)
        r_squared = pattern.get('r_squared', 0)
        years_tracked = pattern.get('years_tracked', 0)
        confidence = pattern.get('confidence', 0.5)

        metric_label = "Mood" if "mood" in metric else "Energy"

        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data_points=years_tracked * 7,  # ~7 periods per year
            correlation=confidence,
            source="observer_cyclical"
        )

        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence, contradictions=0, days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        hypothesis_id = str(uuid.uuid4())

        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.OBSERVER_PATTERN,
            data={
                "pattern_type": "cross_year_evolution",
                "planet": planet,
                "metric": metric,
                "trend_direction": trend_direction,
                "slope": slope,
                "r_squared": r_squared,
                "years_tracked": years_tracked,
            },
            source="observer_cyclical",
            reasoning=(
                f"Linear regression shows {metric_label.lower()} during {planet} "
                f"periods is {trend_direction} over {years_tracked} years "
                f"(slope={slope:.2f}, R²={r_squared:.2f})"
            ),
            position=0,
            magi_context=temporal_context
        )

        # Craft claim based on trend direction
        if trend_direction == 'increasing':
            claim = (
                f"User is becoming more resilient during {planet} periods - "
                f"{metric_label.lower()} improving year over year"
            )
        elif trend_direction == 'decreasing':
            claim = (
                f"User may be experiencing increased sensitivity during {planet} "
                f"periods - {metric_label.lower()} declining year over year"
            )
        else:
            claim = f"User's experience during {planet} periods remains stable across years"

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.CYCLICAL_PATTERN,
            claim=claim,
            predicted_value=f"{trend_direction} {metric_label.lower()} during {planet}",
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "cyclical_pattern",
                "pattern_type": "cross_year_evolution",
                "planet": planet,
                "metric": metric,
                "trend_direction": trend_direction,
                "slope": slope,
                "r_squared": r_squared,
                "years_tracked": years_tracked,
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )

    async def generate_birth_time_hypothesis(
        self,
        user_id: int,
        personality_traits: List[str],
        life_events: List[dict]
    ) -> Hypothesis:
        """
        Generate hypothesis about likely birth time / rising sign.

        Uses LLM to analyze personality traits and life events to predict rising sign.
        """
        # Fetch magi context for this hypothesis
        temporal_context = await self._get_magi_context(user_id)

        traits_text = "\n".join([f"- {trait}" for trait in personality_traits])
        events_text = "\n".join([f"- {event['description']} (age {event['age']})" for event in life_events])

        prompt = f"""Based on these personality traits and life events, predict the most likely rising sign:

**Personality Traits:**
{traits_text}

**Life Events:**
{events_text}

Analyze which rising sign best matches these characteristics. Consider:
1. Outer persona and first impressions
2. Approach to new situations
3. Physical appearance themes
4. Life path milestones

Respond with JSON:
{{
    "rising_sign": "Virgo",
    "confidence": 0.68,
    "reasoning": "Organizational traits, attention to detail, and methodical approach suggest Virgo rising..."
}}
"""

        response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert astrologer skilled at rising sign prediction."),
            HumanMessage(content=prompt)
        ])

        # Parse response
        import json
        import re

        # Attempt to extract JSON if LLM included conversational text
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            # Fallback if parsing fails
            result = {"rising_sign": "Unknown", "confidence": 0.5, "reasoning": "Analysis failed"}

        # Use calculator for initial confidence, adjusting LLM confidence
        data_points = len(personality_traits) + len(life_events)
        llm_confidence = result.get('confidence', 0.5)

        # Use WeightedConfidenceCalculator - LLM suggestion is MODULE_SUGGESTION type
        initial_confidence = self.calculator.calculate_initial_confidence(
            evidence_type=EvidenceType.MODULE_SUGGESTION,
            data_points=data_points,
            correlation=llm_confidence,
            source="genesis"
        )

        # Determine status using thresholds
        status_str = ConfidenceThresholds.get_status_for_confidence(
            initial_confidence,
            contradictions=0,
            days_since_evidence=0
        )
        status = HypothesisStatus(status_str)

        # Create hypothesis ID
        hypothesis_id = str(uuid.uuid4())

        # Create initial evidence record
        initial_evidence = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=EvidenceType.MODULE_SUGGESTION,
            data={
                "analysis_type": "personality_analysis",
                "traits": personality_traits,
                "life_events": life_events,
                "llm_confidence": llm_confidence,
                "llm_reasoning": result.get('reasoning', "Analyzed personality traits"),
            },
            source="genesis",
            reasoning=(
                f"LLM personality analysis suggests {result['rising_sign']} rising sign "
                f"(LLM confidence: {llm_confidence:.0%})"
            ),
            position=0,
            magi_context=temporal_context
        )

        return Hypothesis(
            id=hypothesis_id,
            user_id=user_id,
            hypothesis_type=HypothesisType.RISING_SIGN,
            claim=f"User's rising sign is likely {result['rising_sign']} based on personality and life patterns",
            predicted_value=result['rising_sign'],
            confidence=initial_confidence,
            evidence_count=1,
            contradictions=0,
            based_on_patterns=[],
            supporting_evidence=[{
                "type": "personality_analysis",
                "traits": personality_traits,
                "life_events": life_events,
                "reasoning": result.get('reasoning', "Analyzed personality traits"),
                "timestamp": datetime.now(UTC).isoformat()
            }],
            evidence_records=[initial_evidence.model_dump(mode="json")],
            status=status,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            last_evidence_at=datetime.now(UTC),
            last_recalculation=datetime.now(UTC),
            temporal_context=temporal_context
        )
