"""
Hypothesis Updater Service.

Manages hypothesis lifecycle:
- Adding new evidence
- Recalculating confidence
- Status transitions
- Event emission
- Persistence

This is the central service for updating hypotheses with new evidence
and managing their evolution over time.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Hypothesis, HypothesisStatus
from .confidence import (
    EvidenceType,
    EvidenceRecord,
    WeightedConfidenceCalculator,
    ConfidenceThresholds,
)
from .storage import HypothesisStorage
from src.app.core.events.bus import get_event_bus
from src.app.protocol.events import (
    HYPOTHESIS_UPDATED,
    HYPOTHESIS_CONFIRMED,
    HYPOTHESIS_THRESHOLD_CROSSED,
    HYPOTHESIS_REJECTED,
    HYPOTHESIS_STALE,
    HYPOTHESIS_EVIDENCE_ADDED,
)

logger = logging.getLogger(__name__)


class HypothesisUpdater:
    """
    Service for updating hypothesis confidence with new evidence.
    
    Responsibilities:
    1. Add evidence records to hypotheses
    2. Recalculate weighted confidence
    3. Manage status transitions
    4. Emit events on significant changes
    5. Persist changes to storage
    
    Thread-safe for concurrent use.
    """
    
    def __init__(
        self,
        storage: Optional[HypothesisStorage] = None,
        calculator: Optional[WeightedConfidenceCalculator] = None
    ):
        """
        Initialize updater with dependencies.
        
        Args:
            storage: Optional storage instance (created if not provided)
            calculator: Optional calculator instance (created if not provided)
        """
        self.storage = storage or HypothesisStorage()
        self.calculator = calculator or WeightedConfidenceCalculator()
        self.event_bus = get_event_bus()
    
    async def _ensure_event_bus(self) -> None:
        """Ensure event bus is initialized."""
        if not self.event_bus.redis_client:
            await self.event_bus.initialize()
    
    async def add_evidence(
        self,
        hypothesis_id: str,
        user_id: int,
        evidence_type: EvidenceType,
        data: Dict[str, Any],
        source: str,
        reasoning: str,
        db: AsyncSession,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Hypothesis]:
        """
        Add new evidence to a hypothesis and recalculate confidence.
        
        This is the primary method for updating hypotheses with new evidence.
        
        Args:
            hypothesis_id: ID of hypothesis to update
            user_id: User ID
            evidence_type: Type of evidence being added
            data: Evidence data payload
            source: Where evidence came from
            reasoning: Why this evidence matters
            db: Database session
            magi_context: Optional magi chronos state
        
        Returns:
            Updated Hypothesis or None if not found
        
        Raises:
            ValueError: If hypothesis not found
        """
        await self._ensure_event_bus()
        
        # Get hypothesis
        hypotheses = await self.storage.get_hypotheses(user_id)
        hypothesis = next((h for h in hypotheses if h.id == hypothesis_id), None)
        
        if not hypothesis:
            logger.warning(f"Hypothesis {hypothesis_id} not found for user {user_id}")
            return None
        
        # Store previous state for event
        old_confidence = hypothesis.confidence
        old_status = hypothesis.status
        
        # Create evidence record
        position = len(hypothesis.evidence_records)
        evidence_record = EvidenceRecord.create(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=evidence_type,
            data=data,
            source=source,
            reasoning=reasoning,
            position=position,
            magi_context=magi_context
        )
        
        # Add to hypothesis
        hypothesis.add_evidence_record(evidence_record.model_dump(mode="json"))
        
        # Recalculate confidence
        updated_hypothesis = await self._recalculate_confidence(hypothesis, db)
        
        # Emit events if significant change
        await self._emit_update_events(
            updated_hypothesis,
            old_confidence,
            old_status,
            evidence_record.id,
            evidence_record=evidence_record.model_dump(mode="json")
        )
        
        return updated_hypothesis
    
    async def add_user_feedback(
        self,
        hypothesis_id: str,
        user_id: int,
        feedback_type: str,
        comment: Optional[str],
        db: AsyncSession,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Hypothesis]:
        """
        Process user feedback (confirmation/rejection) as evidence.
        
        User feedback carries highest weight in the system.
        
        Args:
            hypothesis_id: ID of hypothesis
            user_id: User ID
            feedback_type: "confirm", "reject", "unsure", "partially"
            comment: Optional user comment
            db: Database session
            magi_context: Optional magi chronos state
        
        Returns:
            Updated Hypothesis or None if not found
        """
        # Map feedback to evidence type
        feedback_map = {
            "confirm": EvidenceType.USER_CONFIRMATION,
            "reject": EvidenceType.USER_REJECTION,
            "partially": EvidenceType.USER_EXPLICIT_FEEDBACK,
            "unsure": EvidenceType.USER_EXPLICIT_FEEDBACK,
        }
        
        evidence_type = feedback_map.get(feedback_type, EvidenceType.USER_EXPLICIT_FEEDBACK)
        
        # Build reasoning
        if feedback_type == "confirm":
            reasoning = f"User confirmed hypothesis is accurate"
            if comment:
                reasoning += f": {comment}"
        elif feedback_type == "reject":
            reasoning = f"User rejected hypothesis as inaccurate"
            if comment:
                reasoning += f": {comment}"
        elif feedback_type == "partially":
            reasoning = f"User indicated hypothesis is partially accurate"
            if comment:
                reasoning += f": {comment}"
        else:
            reasoning = f"User provided feedback: {feedback_type}"
            if comment:
                reasoning += f" - {comment}"
        
        return await self.add_evidence(
            hypothesis_id=hypothesis_id,
            user_id=user_id,
            evidence_type=evidence_type,
            data={
                "feedback_type": feedback_type,
                "comment": comment,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            source="user_feedback",
            reasoning=reasoning,
            db=db,
            magi_context=magi_context
        )
    
    async def add_journal_evidence(
        self,
        hypothesis: Hypothesis,
        journal_entry: Dict[str, Any],
        relevance_score: float,
        matching_keywords: List[str],
        db: AsyncSession,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Hypothesis]:
        """
        Add journal entry as supporting evidence.
        
        Called when a journal entry is detected to be relevant to a hypothesis.
        
        Args:
            hypothesis: Hypothesis to update
            journal_entry: Journal entry data
            relevance_score: How relevant (0-1)
            matching_keywords: Keywords that matched
            db: Database session
            magi_context: Optional magi chronos state
        
        Returns:
            Updated Hypothesis
        """
        # Determine evidence type based on relevance
        if relevance_score > 0.8:
            evidence_type = EvidenceType.JOURNAL_ENTRY
        elif relevance_score > 0.5:
            evidence_type = EvidenceType.THEME_ALIGNMENT
        else:
            evidence_type = EvidenceType.MODULE_SUGGESTION
        
        reasoning = f"Journal entry aligns with hypothesis (relevance: {relevance_score:.0%})"
        if matching_keywords:
            reasoning += f" - keywords: {', '.join(matching_keywords[:5])}"
        
        return await self.add_evidence(
            hypothesis_id=hypothesis.id,
            user_id=hypothesis.user_id,
            evidence_type=evidence_type,
            data={
                "entry_id": journal_entry.get("id"),
                "content_preview": journal_entry.get("content", "")[:200],
                "mood_score": journal_entry.get("mood_score"),
                "relevance_score": relevance_score,
                "matching_keywords": matching_keywords,
            },
            source="journal_analysis",
            reasoning=reasoning,
            db=db,
            magi_context=magi_context
        )
    
    async def add_pattern_evidence(
        self,
        hypothesis: Hypothesis,
        pattern: Dict[str, Any],
        db: AsyncSession,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Hypothesis]:
        """
        Add Observer pattern as evidence.
        
        Called when Observer detects a pattern relevant to a hypothesis.
        
        Args:
            hypothesis: Hypothesis to update
            pattern: Observer pattern data
            db: Database session
            magi_context: Optional magi chronos state
        
        Returns:
            Updated Hypothesis
        """
        pattern_type = pattern.get("pattern_type", "unknown")
        
        # Map pattern type to evidence type
        pattern_evidence_map = {
            "solar_symptom": EvidenceType.COSMIC_CORRELATION,
            "lunar_phase": EvidenceType.COSMIC_CORRELATION,
            "transit_theme": EvidenceType.TRANSIT_ALIGNMENT,
            "day_of_week": EvidenceType.OBSERVER_PATTERN,
            "cyclical": EvidenceType.CYCLICAL_PATTERN,
        }
        
        evidence_type = pattern_evidence_map.get(
            pattern_type, 
            EvidenceType.OBSERVER_PATTERN
        )
        
        correlation = pattern.get("correlation", 0)
        p_value = pattern.get("p_value", 1.0)
        
        reasoning = f"Observer detected {pattern_type} pattern"
        if correlation:
            reasoning += f" (r={correlation:.2f}, p={p_value:.3f})"
        
        return await self.add_evidence(
            hypothesis_id=hypothesis.id,
            user_id=hypothesis.user_id,
            evidence_type=evidence_type,
            data={
                "pattern_type": pattern_type,
                "correlation": correlation,
                "p_value": p_value,
                "data_points": pattern.get("data_points"),
                "finding": pattern.get("finding"),
            },
            source=f"observer_{pattern_type}",
            reasoning=reasoning,
            db=db,
            magi_context=magi_context
        )
    
    async def add_cyclical_pattern_evidence(
        self,
        hypothesis: Hypothesis,
        cyclical_pattern: Dict[str, Any],
        db: AsyncSession,
        magi_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Hypothesis]:
        """
        Add cyclical pattern as high-fidelity evidence.
        
        Cyclical patterns represent recurring experiences across 52-day magi periods.
        They carry higher weight because they're validated across multiple occurrences.
        
        Args:
            hypothesis: Hypothesis to update
            cyclical_pattern: CyclicalPattern data from Observer
            db: Database session
            magi_context: Optional current magi chronos state
        
        Returns:
            Updated Hypothesis with cyclical evidence
        """
        pattern_type = cyclical_pattern.get("pattern_type", "unknown")
        period_card = cyclical_pattern.get("period_card", "Unknown")
        planetary_ruler = cyclical_pattern.get("planetary_ruler", "Unknown")
        confidence = cyclical_pattern.get("confidence", 0)
        observation_count = cyclical_pattern.get("observation_count", 0)
        pattern_id = cyclical_pattern.get("pattern_id", cyclical_pattern.get("id", ""))
        
        # Cyclical patterns are high-quality evidence
        evidence_type = EvidenceType.CYCLICAL_PATTERN
        
        # Build comprehensive reasoning
        reasoning = (
            f"Cyclical pattern detected: {pattern_type} during {planetary_ruler} periods "
            f"({period_card}). Based on {observation_count} observations "
            f"with {confidence:.0%} confidence."
        )
        
        # Add to hypothesis
        updated_hypothesis = await self.add_evidence(
            hypothesis_id=hypothesis.id,
            user_id=hypothesis.user_id,
            evidence_type=evidence_type,
            data={
                "pattern_type": pattern_type,
                "period_card": period_card,
                "planetary_ruler": planetary_ruler,
                "pattern_confidence": confidence,
                "observation_count": observation_count,
                "pattern_id": pattern_id,
                "description": cyclical_pattern.get("description", ""),
                "symptoms": cyclical_pattern.get("symptoms", []),
                "variance_analysis": cyclical_pattern.get("variance_analysis", {}),
            },
            source="observer_cyclical",
            reasoning=reasoning,
            db=db,
            magi_context=magi_context
        )
        
        if updated_hypothesis:
            # Track period correlation
            updated_hypothesis.track_period_evidence(planetary_ruler)
            
            # Add cyclical pattern correlation
            if pattern_id:
                updated_hypothesis.add_cyclical_pattern_correlation(pattern_id)
            
            # Persist additional fields
            await self.storage.store_hypothesis(updated_hypothesis, db)
            
            logger.info(
                f"Added cyclical pattern evidence to hypothesis {hypothesis.id}: "
                f"{pattern_type} in {planetary_ruler}"
            )
        
        return updated_hypothesis
    
    async def correlate_hypothesis_with_period(
        self,
        hypothesis: Hypothesis,
        magi_context: Dict[str, Any],
        db: AsyncSession
    ) -> Hypothesis:
        """
        Update hypothesis with current magi period and hexagram correlation.
        
        Should be called when adding evidence to track which planetary periods
        AND which I-Ching gates contribute most to a hypothesis.
        
        Args:
            hypothesis: Hypothesis to update
            magi_context: Current magi chronos state (includes cardology + hexagram)
            db: Database session
        
        Returns:
            Updated hypothesis with period and hexagram tracking
        """
        if not magi_context:
            return hypothesis
        
        # ===== CARDOLOGY (MACRO PERIOD) =====
        planetary_ruler = magi_context.get("planetary_ruler")
        period_card = magi_context.get("period_card")
        
        # Track evidence during this period
        if planetary_ruler:
            hypothesis.track_period_evidence(planetary_ruler)
        
        # If hypothesis doesn't have origin period set, set it now
        if not hypothesis.magi_period_card and period_card:
            hypothesis.magi_period_card = period_card
        if not hypothesis.magi_planetary_ruler and planetary_ruler:
            hypothesis.magi_planetary_ruler = planetary_ruler
        
        # ===== I-CHING HEXAGRAM (MICRO PERIOD) =====
        hexagram = magi_context.get("hexagram")
        if hexagram:
            sun_gate = hexagram.get("sun_gate")
            earth_gate = hexagram.get("earth_gate")
            sun_line = hexagram.get("sun_line")
            earth_line = hexagram.get("earth_line")
            
            # Track hexagram evidence correlation (gate + line)
            if sun_gate:
                hypothesis.track_hexagram_evidence(
                    sun_gate, 
                    earth_gate,
                    sun_line,
                    earth_line
                )
            
            # Store origin hexagram if not set
            if not hasattr(hypothesis, 'origin_hexagram') or not hypothesis.origin_hexagram:
                hypothesis.origin_hexagram = {
                    "sun_gate": sun_gate,
                    "earth_gate": earth_gate,
                    "sun_line": sun_line,
                    "earth_line": earth_line,
                }
        
        # Persist
        await self.storage.store_hypothesis(hypothesis, db)
        
        return hypothesis
    
    async def _recalculate_confidence(
        self,
        hypothesis: Hypothesis,
        db: AsyncSession
    ) -> Hypothesis:
        """
        Recalculate hypothesis confidence from evidence records.
        
        Args:
            hypothesis: Hypothesis to recalculate
            db: Database session
        
        Returns:
            Updated hypothesis
        """
        # Parse evidence records
        evidence_records = [
            EvidenceRecord(**record)
            for record in hypothesis.evidence_records
        ]
        
        # Calculate new confidence
        new_confidence = self.calculator.calculate_confidence(evidence_records)
        
        # Get breakdown for caching
        breakdown = self.calculator.get_confidence_breakdown(evidence_records)
        
        # Create snapshot
        snapshot = self.calculator.create_snapshot(
            evidence_records,
            trigger="evidence_added",
            evidence_id=evidence_records[-1].id if evidence_records else None,
            status=hypothesis.status.value
        )
        
        # Update hypothesis
        hypothesis.confidence = new_confidence
        hypothesis.confidence_breakdown = breakdown
        hypothesis.last_recalculation = datetime.now(timezone.utc)
        hypothesis.add_confidence_snapshot(snapshot.model_dump(mode="json"))
        
        # Update status based on new confidence
        hypothesis.update_status_from_confidence()
        
        # Update evidence records with recency-adjusted weights
        hypothesis.evidence_records = [
            record.model_dump(mode="json")
            for record in evidence_records
        ]
        
        # Persist
        await self.storage.store_hypothesis(hypothesis, db)
        
        logger.info(
            f"Recalculated hypothesis {hypothesis.id}: "
            f"confidence={new_confidence:.2f}, status={hypothesis.status.value}"
        )
        
        return hypothesis
    
    async def recalculate_all_user_hypotheses(
        self,
        user_id: int,
        db: AsyncSession
    ) -> List[Hypothesis]:
        """
        Recalculate confidence for all user hypotheses.
        
        Useful for applying recency decay or after bulk updates.
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            List of updated hypotheses
        """
        hypotheses = await self.storage.get_hypotheses(user_id)
        
        updated = []
        for hypothesis in hypotheses:
            updated_hypothesis = await self._recalculate_confidence(hypothesis, db)
            updated.append(updated_hypothesis)
        
        return updated
    
    async def _emit_update_events(
        self,
        hypothesis: Hypothesis,
        old_confidence: float,
        old_status: HypothesisStatus,
        evidence_id: str,
        evidence_record: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit events for hypothesis updates.
        
        Events:
        - HYPOTHESIS_UPDATED: Always emitted on update
        - HYPOTHESIS_CONFIRMED: When status transitions to CONFIRMED
        - HYPOTHESIS_THRESHOLD_CROSSED: When crossing significance thresholds
        - HYPOTHESIS_REJECTED: When status transitions to REJECTED
        - HYPOTHESIS_STALE: When status transitions to STALE
        - HYPOTHESIS_EVIDENCE_ADDED: When new evidence is added
        
        Args:
            hypothesis: Updated hypothesis
            old_confidence: Previous confidence
            old_status: Previous status
            evidence_id: ID of triggering evidence
            evidence_record: Optional evidence record details
        """
        confidence_delta = hypothesis.confidence - old_confidence
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Always emit update event
        await self.event_bus.publish(
            HYPOTHESIS_UPDATED,
            {
                "user_id": hypothesis.user_id,
                "hypothesis_id": hypothesis.id,
                "hypothesis_type": hypothesis.hypothesis_type.value,
                "confidence_before": old_confidence,
                "confidence_after": hypothesis.confidence,
                "confidence_delta": confidence_delta,
                "status_before": old_status.value,
                "status_after": hypothesis.status.value,
                "evidence_id": evidence_id,
                "timestamp": timestamp
            }
        )
        
        # Emit evidence added event if record provided
        if evidence_record:
            await self.event_bus.publish(
                HYPOTHESIS_EVIDENCE_ADDED,
                {
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "evidence_id": evidence_record.get("id", evidence_id),
                    "evidence_type": evidence_record.get("evidence_type", "unknown"),
                    "source": evidence_record.get("source", "unknown"),
                    "weight": evidence_record.get("effective_weight", 0),
                    "is_contradiction": evidence_record.get("is_contradiction", False),
                    "confidence_before": old_confidence,
                    "confidence_after": hypothesis.confidence,
                    "timestamp": timestamp
                }
            )
        
        # Detect and emit threshold crossing events
        await self._emit_threshold_events(
            hypothesis, old_confidence, old_status, evidence_id, timestamp
        )
    
    async def _emit_threshold_events(
        self,
        hypothesis: Hypothesis,
        old_confidence: float,
        old_status: HypothesisStatus,
        evidence_id: str,
        timestamp: str
    ) -> None:
        """
        Emit events for threshold crossings.
        
        Thresholds:
        - FORMING_MAX (0.60): Transition to TESTING
        - CONFIRMED_MIN (0.85): Transition to CONFIRMED
        - REJECTION_THRESHOLD (0.20): Transition to REJECTED
        """
        # Only emit if status changed
        if old_status == hypothesis.status:
            return
        
        # Determine threshold type
        threshold_type = None
        
        if old_status == HypothesisStatus.FORMING and hypothesis.status == HypothesisStatus.TESTING:
            threshold_type = "testing_entered"
        elif old_status == HypothesisStatus.TESTING and hypothesis.status == HypothesisStatus.CONFIRMED:
            threshold_type = "confirmed_entered"
        elif old_status == HypothesisStatus.TESTING and hypothesis.status == HypothesisStatus.FORMING:
            threshold_type = "testing_exited"
        elif hypothesis.status == HypothesisStatus.REJECTED:
            threshold_type = "rejected"
        elif hypothesis.status == HypothesisStatus.STALE:
            threshold_type = "stale"
        
        if threshold_type:
            await self.event_bus.publish(
                HYPOTHESIS_THRESHOLD_CROSSED,
                {
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_type": hypothesis.hypothesis_type.value,
                    "threshold_type": threshold_type,
                    "old_confidence": old_confidence,
                    "new_confidence": hypothesis.confidence,
                    "old_status": old_status.value,
                    "new_status": hypothesis.status.value,
                    "evidence_id": evidence_id,
                    "timestamp": timestamp
                }
            )
            
            logger.info(
                f"Hypothesis threshold crossed: {hypothesis.id} "
                f"{old_status.value} -> {hypothesis.status.value} "
                f"(threshold: {threshold_type})"
            )
        
        # Emit confirmation event on status transition to CONFIRMED
        if (
            old_status != HypothesisStatus.CONFIRMED and
            hypothesis.status == HypothesisStatus.CONFIRMED
        ):
            await self.event_bus.publish(
                HYPOTHESIS_CONFIRMED,
                {
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_type": hypothesis.hypothesis_type.value,
                    "claim": hypothesis.claim,
                    "predicted_value": hypothesis.predicted_value,
                    "final_confidence": hypothesis.confidence,
                    "evidence_count": hypothesis.evidence_count,
                    "timestamp": timestamp
                }
            )
            
            logger.info(
                f"Hypothesis CONFIRMED: {hypothesis.id} - "
                f"{hypothesis.claim} (confidence: {hypothesis.confidence:.2f})"
            )
        
        # Emit rejection event
        if (
            old_status != HypothesisStatus.REJECTED and
            hypothesis.status == HypothesisStatus.REJECTED
        ):
            await self.event_bus.publish(
                HYPOTHESIS_REJECTED,
                {
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_type": hypothesis.hypothesis_type.value,
                    "claim": hypothesis.claim,
                    "final_confidence": hypothesis.confidence,
                    "contradiction_count": hypothesis.contradictions,
                    "rejection_reason": "Confidence dropped below rejection threshold with contradictions",
                    "timestamp": timestamp
                }
            )
            
            logger.info(
                f"Hypothesis REJECTED: {hypothesis.id} - "
                f"{hypothesis.claim} (confidence: {hypothesis.confidence:.2f}, "
                f"contradictions: {hypothesis.contradictions})"
            )
        
        # Emit stale event
        if (
            old_status != HypothesisStatus.STALE and
            hypothesis.status == HypothesisStatus.STALE
        ):
            days_since = 0
            if hypothesis.last_evidence_at:
                last_ev = hypothesis.last_evidence_at
                if last_ev.tzinfo:
                    last_ev = last_ev.replace(tzinfo=None)
                days_since = (datetime.utcnow() - last_ev).days
            
            await self.event_bus.publish(
                HYPOTHESIS_STALE,
                {
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_type": hypothesis.hypothesis_type.value,
                    "claim": hypothesis.claim,
                    "days_since_evidence": days_since,
                    "last_evidence_at": hypothesis.last_evidence_at.isoformat() 
                        if hypothesis.last_evidence_at else None,
                    "timestamp": timestamp
                }
            )
            
            logger.info(
                f"Hypothesis STALE: {hypothesis.id} - "
                f"{hypothesis.claim} ({days_since} days since evidence)"
            )
    
    async def get_relevant_hypotheses_for_journal(
        self,
        user_id: int,
        journal_content: str,
        mood_score: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[Hypothesis]:
        """
        Find hypotheses relevant to a journal entry.
        
        Uses keyword matching and semantic analysis to find hypotheses
        that might be supported by the journal entry.
        
        Args:
            user_id: User ID
            journal_content: Journal entry content
            mood_score: Optional mood score
            tags: Optional entry tags
        
        Returns:
            List of relevant hypotheses with relevance scores
        """
        hypotheses = await self.storage.get_hypotheses(user_id)
        
        relevant = []
        
        # Keywords by hypothesis type
        type_keywords = {
            "cosmic_sensitivity": [
                "headache", "migraine", "anxiety", "fatigue", "energy",
                "tired", "restless", "mood", "sleep", "storm", "magnetic"
            ],
            "temporal_pattern": [
                "monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday", "morning", "evening", "night"
            ],
            "transit_effect": [
                "retrograde", "transit", "mercury", "venus", "mars",
                "jupiter", "saturn", "uranus", "neptune", "pluto"
            ],
            "theme_correlation": [
                "theme", "period", "card", "magi", "planetary"
            ],
            "cyclical_pattern": [
                "recurring", "pattern", "cycle", "again", "always",
                "every time", "consistently"
            ]
        }
        
        content_lower = journal_content.lower()
        
        for hypothesis in hypotheses:
            # Skip rejected/stale hypotheses
            if hypothesis.status in [HypothesisStatus.REJECTED, HypothesisStatus.STALE]:
                continue
            
            # Check keyword match
            keywords = type_keywords.get(hypothesis.hypothesis_type.value, [])
            matching = [kw for kw in keywords if kw in content_lower]
            
            # Check claim/predicted value match
            claim_match = any(
                word.lower() in content_lower 
                for word in hypothesis.claim.split() 
                if len(word) > 4
            )
            
            predicted_match = hypothesis.predicted_value.lower() in content_lower
            
            # Calculate relevance
            relevance = 0.0
            if matching:
                relevance = min(len(matching) / 5, 0.5)  # Up to 0.5 from keywords
            if claim_match:
                relevance += 0.3
            if predicted_match:
                relevance += 0.2
            
            if relevance > 0.1:
                relevant.append({
                    "hypothesis": hypothesis,
                    "relevance": relevance,
                    "matching_keywords": matching
                })
        
        # Sort by relevance
        relevant.sort(key=lambda x: x["relevance"], reverse=True)
        
        return relevant


# Singleton accessor
_updater_instance: Optional[HypothesisUpdater] = None


def get_hypothesis_updater() -> HypothesisUpdater:
    """Get singleton HypothesisUpdater instance."""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = HypothesisUpdater()
    return _updater_instance
