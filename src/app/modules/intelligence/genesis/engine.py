"""
Genesis Hypothesis Engine

Central orchestrator for the refinement lifecycle:
uncertainty → hypothesis → probe → confirmation → recalculation.
"""

import logging
from datetime import datetime
from typing import Optional

from ....core.events.bus import get_event_bus
from ....protocol.events import (
    GENESIS_CONFIDENCE_UPDATED,
    GENESIS_FIELD_CONFIRMED,
    GENESIS_UNCERTAINTY_DECLARED,
    MODULE_PROFILE_CALCULATED,
)
from ....protocol.genesis_payloads import (
    GenesisFieldConfirmedPayload,
    GenesisUncertaintyPayload,
)
from ....protocol.packet import Packet
from ..hypothesis.models import Hypothesis as TheoryHypothesis
from ..hypothesis.storage import HypothesisStorage
from .hypothesis import Hypothesis
from .persistence import get_genesis_persistence
from .probes import ProbeGenerator, ProbePacket, ProbeResponse, ProbeType
from .registry import UncertaintyRegistry
from .strategies import StrategyRegistry
from .uncertainty import AlignmentDiscrepancy, UncertaintyDeclaration, UncertaintyField

logger = logging.getLogger(__name__)


class GenesisEngine:
    """
    Central engine for hypothesis refinement.

    Manages the full lifecycle:
    1. Convert uncertainties → hypotheses
    2. Select highest priority hypothesis
    3. Generate conversational probes
    4. Process responses and update confidence
    5. Detect confirmations and trigger recalculation

    Usage:
        engine = GenesisEngine()
        await engine.initialize()

        # After module calculates probabilistically
        hypotheses = await engine.initialize_from_uncertainties(declarations)

        # Get next probe
        hypothesis = await engine.select_next_hypothesis(user_id)
        probe = await engine.generate_probe(hypothesis)

        # Process response
        await engine.process_response(probe.id, response)

        # Check confirmations
        confirmations = await engine.check_confirmations(user_id)
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self.persistence = get_genesis_persistence()
        self.probe_generator = ProbeGenerator()

        # Active hypotheses by user_id -> hypothesis_id -> Hypothesis
        self._hypotheses: dict[int, dict[str, Hypothesis]] = {}

        # Active probes by probe_id
        self._probes: dict[str, ProbePacket] = {}

        self._initialized = False

    # =========================================================================
    # Initialization
    # =========================================================================

    async def initialize(self) -> None:
        """
        Initialize engine and set up event subscriptions.

        Call during application startup.
        """
        if self._initialized:
            return

        # Initialize strategy registry
        StrategyRegistry.initialize_defaults()

        # Initialize uncertainty registry
        UncertaintyRegistry.initialize_default_extractors()

        # Subscribe to events
        await self._setup_subscriptions()

        self._initialized = True
        logger.info("GenesisEngine initialized")

    async def _setup_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        await self.event_bus.subscribe(MODULE_PROFILE_CALCULATED, self._handle_module_calculated)
        await self.event_bus.subscribe(GENESIS_UNCERTAINTY_DECLARED, self._handle_uncertainty_declared)

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    async def initialize_from_uncertainties(self, declarations: list[UncertaintyDeclaration]) -> list[Hypothesis]:
        """
        Convert uncertainty declarations into trackable hypotheses.

        For each field with multiple candidates, creates one hypothesis
        per candidate value.

        Args:
            declarations: Uncertainty declarations from modules

        Returns:
            List of created hypotheses
        """
        hypotheses = []

        for decl in declarations:
            user_id = decl.user_id
            session_id = decl.session_id

            # Fetch magi context once per declaration
            temporal_context = await self._get_magi_context(user_id)

            # Initialize user's hypothesis dict if needed
            if user_id not in self._hypotheses:
                self._hypotheses[user_id] = {}

            for field in decl.fields:
                for candidate, confidence in field.candidates.items():
                    hyp = Hypothesis(
                        field=field.field,
                        module=decl.module,
                        suspected_value=candidate,
                        user_id=user_id,
                        session_id=session_id,
                        confidence=confidence,
                        initial_confidence=confidence,
                        confidence_threshold=field.confidence_threshold,
                        temporal_context=temporal_context,
                    )

                    self._hypotheses[user_id][hyp.id] = hyp
                    hypotheses.append(hyp)

        if hypotheses:
            logger.info(f"Created {len(hypotheses)} hypotheses for user {hypotheses[0].user_id}")

            # Update StateTracker
            try:
                from ....core.state.tracker import get_state_tracker

                tracker = get_state_tracker()
                all_fields = list({h.field for h in hypotheses})
                await tracker.update_genesis_status(
                    user_id=hypotheses[0].user_id, hypothesis_count=len(hypotheses), fields_uncertain=all_fields
                )
            except Exception as e:
                logger.warning(f"Failed to update StateTracker: {e}")

        return hypotheses

    async def select_next_hypothesis(self, user_id: int) -> Hypothesis | None:
        """
        Select highest priority hypothesis that needs probing.

        Priority factors (from Hypothesis.priority):
        - Close to threshold = high priority
        - Core field = boost
        - Few probes attempted = boost
        - Evidence ratio = boost

        Args:
            user_id: User to select hypothesis for

        Returns:
            Highest priority hypothesis, or None if none need probing
        """
        user_hypotheses = self._hypotheses.get(user_id, {})

        # Filter to those needing probing
        candidates = [h for h in user_hypotheses.values() if h.needs_probing]

        if not candidates:
            return None

        # Sort by priority (descending)
        candidates.sort(key=lambda h: h.priority, reverse=True)

        return candidates[0]

    async def generate_probe(self, hypothesis: Hypothesis, preferred_type: ProbeType | None = None) -> ProbePacket:
        """
        Generate a conversational probe for this hypothesis.

        Args:
            hypothesis: Hypothesis to probe
            preferred_type: Preferred probe type (optional)

        Returns:
            ProbePacket ready to present to user
        """
        # Get applicable strategies
        strategies = StrategyRegistry.get_strategies_for_field(hypothesis.field)
        unused_strategies = hypothesis.get_unused_strategies([s.strategy_name for s in strategies])

        if not unused_strategies:
            # All strategies exhausted, pick least recently used
            unused_strategies = [strategies[0].strategy_name] if strategies else ["default"]

        # Select strategy
        strategy_name = unused_strategies[0]
        strategy = StrategyRegistry.get_strategy(strategy_name)

        # Determine probe type
        probe_type = preferred_type or (strategy.probe_type if strategy else ProbeType.BINARY_CHOICE)

        # Generate prompt from strategy
        strategy_prompt = strategy.generate_prompt(hypothesis) if strategy else None

        # Generate probe
        probe = await self.probe_generator.generate_probe(
            hypothesis=hypothesis,
            strategy_name=strategy_name,
            probe_type=probe_type,
            strategy_prompt=strategy_prompt,
        )

        # Store probe
        self._probes[probe.id] = probe

        # Mark hypothesis as probed
        hypothesis.mark_probed(strategy_name)

        return probe

    async def process_response(self, probe_id: str, response: ProbeResponse) -> list[Hypothesis]:
        """
        Process user's response to a probe.

        Updates confidence for all hypotheses related to this field
        based on the response mappings.

        Args:
            probe_id: ID of the probe being responded to
            response: User's response

        Returns:
            All hypotheses whose confidence was updated
        """
        probe = self._probes.get(probe_id)
        if not probe:
            logger.warning(f"Probe {probe_id} not found")
            return []

        # Get the hypothesis that was being probed
        primary_hyp = None
        for user_hyps in self._hypotheses.values():
            if probe.hypothesis_id in user_hyps:
                primary_hyp = user_hyps[probe.hypothesis_id]
                break

        if not primary_hyp:
            logger.warning(f"Hypothesis {probe.hypothesis_id} not found")
            return []

        updated_hypotheses = []
        user_hypotheses = self._hypotheses.get(primary_hyp.user_id, {})

        # Determine response key based on type
        response_key = self._get_response_key(response)

        # Update confidence for all hypotheses of this field
        for hyp in user_hypotheses.values():
            if hyp.field != probe.field:
                continue

            delta = self._calculate_confidence_delta(probe, response, response_key, hyp.suspected_value)

            if delta != 0:
                old_confidence = hyp.confidence
                hyp.update_confidence(delta)

                # Add evidence/contradiction
                if delta > 0:
                    hyp.add_evidence(f"Probe {probe.strategy_used}: +{delta:.2f}")
                else:
                    hyp.add_contradiction(f"Probe {probe.strategy_used}: {delta:.2f}")

                updated_hypotheses.append(hyp)

                # Emit confidence update event
                await self._emit_confidence_updated(hyp, old_confidence, hyp.confidence)

        return updated_hypotheses

    async def check_confirmations(self, user_id: int) -> list[tuple[Hypothesis, str]]:
        """
        Check if any hypotheses have reached confirmation threshold.

        For each hypothesis at or above threshold:
        1. Mark as resolved
        2. Refute competing hypotheses for same field
        3. Emit GENESIS_FIELD_CONFIRMED event

        Args:
            user_id: User to check confirmations for

        Returns:
            List of (hypothesis, confirmed_value) tuples
        """
        confirmations = []
        user_hypotheses = self._hypotheses.get(user_id, {})

        # Group by field
        fields: dict[str, list[Hypothesis]] = {}
        for hyp in user_hypotheses.values():
            if hyp.field not in fields:
                fields[hyp.field] = []
            fields[hyp.field].append(hyp)

        # Check each field for confirmation
        for field_name, field_hyps in fields.items():
            for hyp in field_hyps:
                if hyp.resolved:
                    continue

                if hyp.confidence >= hyp.confidence_threshold:
                    # Confirm this hypothesis
                    hyp.resolve("confirmed")
                    confirmations.append((hyp, hyp.suspected_value))

                    # Refute competing hypotheses
                    for other in field_hyps:
                        if other.id != hyp.id and not other.resolved:
                            other.resolve("superseded")

                    # Emit event
                    await self._emit_field_confirmed(hyp)

                    logger.info(f"Confirmed {field_name}={hyp.suspected_value} with confidence {hyp.confidence:.2f}")

                    # Only one confirmation per field
                    break

        return confirmations

    # =========================================================================
    # Event Handlers
    # =========================================================================

    async def _handle_module_calculated(self, packet: Packet) -> None:
        """
        Handle MODULE_PROFILE_CALCULATED events.

        Extracts uncertainties from the calculation result and
        creates hypotheses.
        """
        try:
            module_name = packet.payload.get("module_name")
            user_id = packet.payload.get("user_id")
            profile_data = packet.payload.get("profile_data", {})
            session_id = packet.payload.get("session_id", "default")

            if not module_name or not user_id:
                return

            # Extract uncertainties using registry
            declarations = await UncertaintyRegistry.extract_all(
                results={module_name: profile_data},
                user_id=user_id,
                session_id=session_id,
            )

            if declarations:
                # Create hypotheses
                await self.initialize_from_uncertainties(declarations)

                # Emit uncertainty declared event
                for decl in declarations:
                    await self.event_bus.publish(
                        GENESIS_UNCERTAINTY_DECLARED,
                        GenesisUncertaintyPayload.from_declaration(decl).model_dump(),
                        source="genesis.engine",
                        user_id=str(user_id),
                    )

        except Exception as e:
            logger.error(f"Error handling module calculated: {e}")

    async def _handle_uncertainty_declared(self, packet: Packet) -> None:
        """Handle GENESIS_UNCERTAINTY_DECLARED events."""
        try:
            payload = GenesisUncertaintyPayload(**packet.payload)

            # Reconstruct declaration
            declaration = UncertaintyDeclaration(
                module=payload.module,
                user_id=payload.user_id,
                session_id=payload.session_id,
                fields=[UncertaintyField(**f) for f in payload.fields],
                source_accuracy=payload.source_accuracy,
                declared_at=datetime.fromisoformat(payload.declared_at),
            )

            # Initialize hypotheses if not already done
            user_hyps = self._hypotheses.get(payload.user_id, {})
            if not any(h.module == payload.module for h in user_hyps.values()):
                await self.initialize_from_uncertainties([declaration])

        except Exception as e:
            logger.error(f"Error handling uncertainty declared: {e}")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_response_key(self, response: ProbeResponse) -> str:
        """Get response key for mapping lookup."""
        if response.response_type == ProbeType.BINARY_CHOICE:
            return str(response.selected_option)
        elif response.response_type == ProbeType.SLIDER:
            # Map slider to low/mid/high
            if response.slider_value <= 3:
                return "low"
            elif response.slider_value <= 7:
                return "mid"
            else:
                return "high"
        elif response.response_type == ProbeType.CONFIRMATION:
            return "yes" if response.confirmed else "no"
        else:
            return "default"

    def _calculate_confidence_delta(
        self, probe: ProbePacket, response: ProbeResponse, response_key: str, candidate: str
    ) -> float:
        """Calculate confidence delta for a candidate based on response."""
        if not probe.confidence_mappings:
            # No mappings, use small default
            return 0.05 if response_key in ("0", "yes", "low") else -0.02

        return probe.get_confidence_delta(response_key, candidate)

    async def _emit_confidence_updated(
        self, hypothesis: Hypothesis, old_confidence: float, new_confidence: float
    ) -> None:
        """Emit confidence update event."""
        await self.event_bus.publish(
            GENESIS_CONFIDENCE_UPDATED,
            {
                "user_id": hypothesis.user_id,
                "session_id": hypothesis.session_id,
                "field": hypothesis.field,
                "module": hypothesis.module,
                "candidate": hypothesis.suspected_value,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
            },
            source="genesis.engine",
            user_id=str(hypothesis.user_id),
        )

    async def _emit_field_confirmed(self, hypothesis: Hypothesis) -> None:
        """Emit field confirmed event."""
        payload = GenesisFieldConfirmedPayload(
            user_id=hypothesis.user_id,
            session_id=hypothesis.session_id,
            field=hypothesis.field,
            module=hypothesis.module,
            confirmed_value=hypothesis.suspected_value,
            confidence=hypothesis.confidence,
            trigger_recalculation=True,
        )

        await self.event_bus.publish(
            GENESIS_FIELD_CONFIRMED,
            payload.model_dump(),
            source="genesis.engine",
            user_id=str(hypothesis.user_id),
        )

        # Update StateTracker
        try:
            from ....core.state.tracker import get_state_tracker

            tracker = get_state_tracker()
            await tracker.update_field_confirmed(
                user_id=hypothesis.user_id, field=hypothesis.field, confirmed_value=hypothesis.suspected_value
            )
        except Exception as e:
            logger.warning(f"Failed to update StateTracker for confirmation: {e}")

    # =========================================================================
    # Alignment Audit (MAGI Integration)
    # =========================================================================

    async def audit_alignment(
        self, user_id: int, text: str, source_type: str = "journal_entry", db=None
    ) -> Optional["AlignmentDiscrepancy"]:
        """
        Audit user text against the current MAGI period for alignment discrepancies.

        Compares the emotional/thematic energy in user-provided text against
        what the MAGI system predicts for their current planetary period.
        High discrepancies may indicate:
        - Shadow work opportunities
        - Resistance to period energy
        - External circumstances overriding cosmic weather

        Args:
            user_id: User whose alignment to audit
            text: Journal entry, chat message, or reflection response
            source_type: Type of source text ("journal_entry", "chat_message", etc.)
            db: Optional database session

        Returns:
            AlignmentDiscrepancy if discrepancy detected, None if aligned or error
        """
        import json

        from langchain_core.messages import HumanMessage, SystemMessage

        from ....core.llm import get_premium_llm
        from .uncertainty import AlignmentDiscrepancy

        logger.info(f"[GenesisEngine] Auditing alignment for user {user_id}")

        try:
            # 1. Get current MAGI state for user
            # We need the user's birth date to get their cardology state
            # Try to get from ChronosStateManager first (cached)
            from ....core.state.chronos import get_chronos_manager
            chronos = get_chronos_manager()

            cached_state = await chronos.get_current_state(user_id)

            if not cached_state or not cached_state.get("current_state"):
                logger.warning(f"No MAGI state found for user {user_id}, skipping alignment audit")
                return None

            current_state = cached_state.get("current_state", {})
            period_planet = current_state.get("current_planet", "Unknown")
            current_card = current_state.get("current_card", {})
            period_card = current_card.get("name") or current_card.get("card", "Unknown")

            # Get expected energy for the period
            planetary_themes = {
                "Mercury": "communication, learning, quick thinking, mental activity, adaptability",
                "Venus": "relationships, love, beauty, harmony, pleasure, values",
                "Mars": "action, energy, courage, competition, drive, assertion",
                "Jupiter": "expansion, abundance, optimism, luck, wisdom, growth",
                "Saturn": "discipline, structure, responsibility, lessons, limitations, mastery",
                "Uranus": "innovation, change, rebellion, awakening, freedom, surprise",
                "Neptune": "intuition, dreams, spirituality, illusion, transcendence, creativity",
                "Long Range": "karmic themes, destiny patterns, life lessons, long-term trends",
                "Pluto": "transformation, power, rebirth, shadow work, regeneration, depth",
                "Result": "culmination, outcomes, harvest, completion, integration"
            }
            script_energy = planetary_themes.get(period_planet, "general life energy")

            # 2. Use LLM to analyze the text and score alignment
            llm = get_premium_llm()

            system_prompt = """You are an analyst comparing a person's reported experience
against their expected astrological period energy.

Analyze the provided text and determine:
1. The dominant emotional/thematic energy expressed (reported_energy)
2. How well it aligns with the expected period energy (0.0 = perfect alignment, 1.0 = complete opposition)

Respond in JSON format:
{
    "reported_energy": "brief description of detected themes/energy",
    "discrepancy_score": 0.0-1.0,
    "reasoning": "brief explanation of alignment or discrepancy"
}"""

            user_msg = f"""Expected Period Energy ({period_planet}): {script_energy}

User's Text:
\"\"\"
{text[:1000]}
\"\"\"

Analyze the alignment between the expected energy and what the user is expressing."""

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])

            # Parse LLM response
            response_text = response.content.strip()
            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            analysis = json.loads(response_text)

            reported_energy = analysis.get("reported_energy", "unclear")
            discrepancy_score = float(analysis.get("discrepancy_score", 0.0))

            logger.info(
                f"[GenesisEngine] Alignment audit for user {user_id}: "
                f"score={discrepancy_score:.2f}, period={period_planet}"
            )

            # 3. Only create discrepancy record if significant
            if discrepancy_score < 0.5:
                logger.debug(f"User {user_id} is reasonably aligned with {period_planet} energy")
                return None

            # 4. Create AlignmentDiscrepancy
            discrepancy = AlignmentDiscrepancy(
                user_id=user_id,
                script_energy=script_energy,
                period_planet=period_planet,
                period_card=period_card,
                reported_energy=reported_energy,
                source_text=text[:500],  # Truncate for storage
                source_type=source_type,
                discrepancy_score=discrepancy_score,
            )

            # 5. If highly significant, trigger hypothesis creation
            if discrepancy.is_significant:
                logger.info(
                    f"[GenesisEngine] High alignment discrepancy ({discrepancy_score:.2f}) "
                    f"for user {user_id} - creating hypothesis"
                )
                await self._create_alignment_hypothesis(discrepancy)

            return discrepancy

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM alignment analysis: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in alignment audit for user {user_id}: {e}")
            return None

    async def _create_alignment_hypothesis(self, discrepancy: "AlignmentDiscrepancy") -> None:
        """
        Create a Genesis hypothesis from a significant alignment discrepancy.

        This allows the system to probe the user about why their experience
        doesn't match the expected period energy.
        """

        context = discrepancy.to_hypothesis_context()

        # Fetch magi context for this alignment hypothesis
        temporal_context = await self._get_magi_context(discrepancy.user_id)

        # Create a hypothesis to investigate the discrepancy
        hyp = Hypothesis(
            field=f"alignment_{discrepancy.period_planet.lower()}",
            module="cardology",
            suspected_value=f"shadow_{discrepancy.period_planet.lower()}",
            user_id=discrepancy.user_id,
            session_id=f"alignment_audit_{discrepancy.detected_at.timestamp()}",
            confidence=discrepancy.discrepancy_score,
            initial_confidence=discrepancy.discrepancy_score,
            confidence_threshold=0.85,  # Higher threshold for alignment hypotheses
            temporal_context=temporal_context,
        )

        # Store additional context in hypothesis
        hyp.metadata = {
            "type": "alignment_discrepancy",
            "script_energy": discrepancy.script_energy,
            "reported_energy": discrepancy.reported_energy,
            "source_type": discrepancy.source_type,
            "question": context["question"],
        }

        # Add to hypotheses
        if discrepancy.user_id not in self._hypotheses:
            self._hypotheses[discrepancy.user_id] = {}

        self._hypotheses[discrepancy.user_id][hyp.id] = hyp

        # Mark discrepancy as having generated hypothesis
        discrepancy.hypothesis_generated = True
        discrepancy.hypothesis_id = hyp.id

        logger.info(
            f"[GenesisEngine] Created alignment hypothesis {hyp.id} "
            f"for user {discrepancy.user_id}: {context['question'][:100]}..."
        )

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_hypotheses_for_user(self, user_id: int) -> list[Hypothesis]:
        """Get all hypotheses for a user."""
        return list(self._hypotheses.get(user_id, {}).values())

    def get_active_hypotheses(self, user_id: int) -> list[Hypothesis]:
        """Get unresolved hypotheses for a user."""
        return [h for h in self._hypotheses.get(user_id, {}).values() if not h.resolved]

    def get_confirmed_hypotheses(self, user_id: int) -> list[Hypothesis]:
        """Get confirmed hypotheses for a user."""
        return [
            h for h in self._hypotheses.get(user_id, {}).values() if h.resolved and h.resolution_method == "confirmed"
        ]

    async def get_hypothesis_for_field(self, user_id: int, field: str) -> Optional[TheoryHypothesis]:
        """
        Get best theory from Hypothesis module for uncertain field.

        This queries the Hypothesis module for high-level theories that can
        inform Genesis's field-specific refinement strategies.
        """
        storage = HypothesisStorage()
        hypotheses = await storage.get_hypotheses(user_id, min_confidence=0.60)

        # Map field to theory hypothesis type
        field_map = {"rising_sign": "rising_sign", "birth_time": "birth_time"}

        hypothesis_type = field_map.get(field)
        if not hypothesis_type:
            return None

        relevant = [h for h in hypotheses if h.hypothesis_type.value == hypothesis_type]

        if not relevant:
            return None

        # Return highest confidence theory
        return max(relevant, key=lambda h: h.confidence)


# Singleton instance
_engine: GenesisEngine | None = None


def get_genesis_engine() -> GenesisEngine:
    """Get or create the Genesis engine singleton."""
    global _engine
    if _engine is None:
        _engine = GenesisEngine()
    return _engine


async def initialize_genesis_engine() -> GenesisEngine:
    """Initialize the Genesis engine (call at startup)."""
    engine = get_genesis_engine()
    await engine.initialize()
    return engine
