"""
Hypothesis tracking and confidence updates.

Monitors new data (journal entries, cosmic events, user responses)
and updates hypothesis confidence accordingly.
"""

import datetime as dt
from typing import List, Optional, Tuple

from .models import Hypothesis, HypothesisStatus, HypothesisType, HypothesisUpdate


class HypothesisTracker:
    """Track hypotheses and update confidence as evidence accumulates."""

    def __init__(self):
        self.confidence_increment = 0.05  # How much to increase per supporting evidence
        self.confidence_decrement = 0.10  # How much to decrease per contradiction

    async def update_from_new_data(
        self,
        hypothesis: Hypothesis,
        new_data: dict,
        data_type: str  # "journal_entry", "cosmic_event", "user_response"
    ) -> Tuple[Hypothesis, Optional[HypothesisUpdate]]:
        """
        Update hypothesis confidence based on new data.

        Args:
            hypothesis: Current theory hypothesis
            new_data: New evidence data
            data_type: Type of evidence

        Returns:
            (Updated hypothesis, Update record or None)
        """
        # EDGE CASE 1: Stale data (evidence from >60 days ago)
        evidence_date_str = new_data.get('timestamp')
        if evidence_date_str:
            try:
                evidence_date = dt.datetime.fromisoformat(evidence_date_str.replace('Z', '+00:00'))
                if dt.datetime.now(dt.UTC) - evidence_date > dt.timedelta(days=60):
                    return hypothesis, None
            except ValueError:
                pass # Fallback to continuing if date format invalid

        # EDGE CASE 2: Duplicate evidence
        for existing_evidence in hypothesis.supporting_evidence:
            if existing_evidence.get('data') == new_data and existing_evidence.get('type') == data_type:
                return hypothesis, None

        # EDGE CASE 4: Rejection after too many contradictions
        if hypothesis.status == HypothesisStatus.REJECTED:
            return hypothesis, None

        confidence_before = hypothesis.confidence

        # Determine if data supports or contradicts hypothesis
        # In a real scenario, this would involve more complex LLM or logic-based evaluation
        supports = await self._evaluate_evidence(hypothesis, new_data, data_type)

        reasoning = ""
        if supports is True:
            # Supporting evidence
            hypothesis.confidence = min(hypothesis.confidence + self.confidence_increment, 1.0)
            hypothesis.evidence_count += 1
            hypothesis.supporting_evidence.append({
                "timestamp": dt.datetime.now(dt.UTC).isoformat(),
                "type": data_type,
                "data": new_data,
                "supports": True
            })
            reasoning = f"New {data_type} supports theory: {hypothesis.claim}"

        elif supports is False:
            # Contradictory evidence
            hypothesis.confidence = max(hypothesis.confidence - self.confidence_decrement, 0.0)
            hypothesis.contradictions += 1
            hypothesis.supporting_evidence.append({
                "timestamp": dt.datetime.now(dt.UTC).isoformat(),
                "type": data_type,
                "data": new_data,
                "supports": False
            })
            reasoning = f"New {data_type} contradicts theory: {hypothesis.claim}"

        if supports is None:
            # Neutral / unclear
            return hypothesis, None

        # Update status based on new confidence
        hypothesis.status = self._determine_status(hypothesis.confidence, hypothesis.contradictions)
        hypothesis.last_updated = dt.datetime.now(dt.UTC)
        hypothesis.last_evidence_at = dt.datetime.now(dt.UTC)

        # Create update record
        update = HypothesisUpdate(
            timestamp=dt.datetime.now(dt.UTC),
            evidence_type=data_type,
            evidence_data=new_data,
            confidence_before=confidence_before,
            confidence_after=hypothesis.confidence,
            reasoning=reasoning
        )

        return hypothesis, update

    async def _evaluate_evidence(
        self,
        hypothesis: Hypothesis,
        new_data: dict,
        data_type: str
    ) -> Optional[bool]:
        """
        Evaluate if new data supports hypothesis.

        Returns:
            True if supports, False if contradicts, None if unclear
        """
        # Solar sensitivity hypothesis
        if (
            hypothesis.hypothesis_type == HypothesisType.COSMIC_SENSITIVITY
            and "solar" in hypothesis.predicted_value.lower()
        ):
            if data_type == "cosmic_event":
                kp_index = new_data.get('kp_index', 0)
                if kp_index >= 5:  # Storm day
                    return True
                elif kp_index < 3: # Very quiet day, could be contradiction if symptom reported
                    return None # Unclear without symptom data

            elif data_type == "journal_entry":
                text = new_data.get('text', '').lower()
                symptoms = ['headache', 'fatigue', 'anxiety', 'brain fog', 'exhausted', 'tired']
                has_symptom = any(symptom in text for symptom in symptoms)

                # In production, we'd check if today was a storm day
                # For this implementation, we assume if the user reported a symptom, it supports
                return has_symptom

        # Lunar pattern hypothesis
        elif (
            hypothesis.hypothesis_type == HypothesisType.COSMIC_SENSITIVITY
            and "moon" in hypothesis.predicted_value.lower()
        ):
            if data_type == "journal_entry":
                mood_score = new_data.get('mood_score', 5)
                energy_score = new_data.get('energy_score', 5)
                lunar_phase = new_data.get('lunar_phase', 'unknown')

                predicted_phase_match = any(
                    word.lower() in lunar_phase.lower()
                    for word in hypothesis.predicted_value.split()
                )

                if predicted_phase_match:
                    if "low mood" in hypothesis.predicted_value.lower():
                        return mood_score < 5
                    elif "high mood" in hypothesis.predicted_value.lower():
                        return mood_score > 6
                    elif "low energy" in hypothesis.predicted_value.lower():
                        return energy_score < 5
                    elif "high energy" in hypothesis.predicted_value.lower():
                        return energy_score > 6

        # Temporal pattern hypothesis
        elif hypothesis.hypothesis_type == HypothesisType.TEMPORAL_PATTERN:
            if data_type == "journal_entry":
                mood_score = new_data.get('mood_score', 5)
                entry_day = new_data.get('day_of_week', '').capitalize()

                if not entry_day and 'timestamp' in new_data:
                    try:
                        timestamp_dt = dt.datetime.fromisoformat(new_data['timestamp'].replace('Z', '+00:00'))
                        entry_day = timestamp_dt.strftime('%A')
                    except ValueError:
                        pass

                predicted_day = hypothesis.predicted_value.split()[-1].capitalize()

                if entry_day == predicted_day:
                    if "low mood" in hypothesis.predicted_value.lower():
                        return mood_score < 5
                    elif "high mood" in hypothesis.predicted_value.lower():
                        return mood_score > 6

        return None  # Unclear

    def _determine_status(self, confidence: float, contradictions: int) -> HypothesisStatus:
        """Determine theory status from confidence and contradictions."""
        if contradictions >= 5 and confidence < 0.40:
            return HypothesisStatus.REJECTED

        if confidence >= 0.85:
            return HypothesisStatus.CONFIRMED
        elif confidence >= 0.60:
            return HypothesisStatus.TESTING
        else:
            return HypothesisStatus.FORMING

    async def check_stale_hypotheses(
        self,
        hypotheses: List[Hypothesis]
    ) -> List[Hypothesis]:
        """Mark theories as stale if no new evidence in 60 days."""
        stale_threshold = dt.datetime.now(dt.UTC) - dt.timedelta(days=60)

        for hypothesis in hypotheses:
            if hypothesis.last_evidence_at and hypothesis.last_evidence_at < stale_threshold:
                if hypothesis.status not in [HypothesisStatus.CONFIRMED, HypothesisStatus.REJECTED]:
                    hypothesis.status = HypothesisStatus.STALE

        return hypotheses
