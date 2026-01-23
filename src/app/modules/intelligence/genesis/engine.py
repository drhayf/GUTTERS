"""
Genesis Hypothesis Engine

Central orchestrator for the refinement lifecycle:
uncertainty → hypothesis → probe → confirmation → recalculation.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from .hypothesis import Hypothesis
from .probes import ProbeGenerator, ProbePacket, ProbeResponse, ProbeType
from .uncertainty import UncertaintyDeclaration, UncertaintyField
from .persistence import GenesisPersistence, get_genesis_persistence
from .registry import UncertaintyRegistry
from .strategies import StrategyRegistry

from ....core.events.bus import get_event_bus
from ....protocol.events import (
    MODULE_PROFILE_CALCULATED,
    GENESIS_UNCERTAINTY_DECLARED,
    GENESIS_FIELD_CONFIRMED,
    GENESIS_CONFIDENCE_UPDATED,
)
from ....protocol.genesis_payloads import (
    GenesisUncertaintyPayload,
    GenesisFieldConfirmedPayload,
    GenesisConfidenceUpdatedPayload,
)
from ....protocol.packet import Packet


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
        self._setup_subscriptions()
        
        self._initialized = True
        logger.info("GenesisEngine initialized")
    
    def _setup_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        self.event_bus.subscribe(
            MODULE_PROFILE_CALCULATED,
            self._handle_module_calculated
        )
        self.event_bus.subscribe(
            GENESIS_UNCERTAINTY_DECLARED,
            self._handle_uncertainty_declared
        )
    
    # =========================================================================
    # Lifecycle Methods
    # =========================================================================
    
    async def initialize_from_uncertainties(
        self,
        declarations: list[UncertaintyDeclaration]
    ) -> list[Hypothesis]:
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
                    )
                    
                    self._hypotheses[user_id][hyp.id] = hyp
                    hypotheses.append(hyp)
        
        if hypotheses:
            logger.info(
                f"Created {len(hypotheses)} hypotheses for user {hypotheses[0].user_id}"
            )
            
            # Update StateTracker
            try:
                from ....core.state.tracker import get_state_tracker
                tracker = get_state_tracker()
                all_fields = list(set(h.field for h in hypotheses))
                await tracker.update_genesis_status(
                    user_id=hypotheses[0].user_id,
                    hypothesis_count=len(hypotheses),
                    fields_uncertain=all_fields
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
        candidates = [
            h for h in user_hypotheses.values()
            if h.needs_probing
        ]
        
        if not candidates:
            return None
        
        # Sort by priority (descending)
        candidates.sort(key=lambda h: h.priority, reverse=True)
        
        return candidates[0]
    
    async def generate_probe(
        self,
        hypothesis: Hypothesis,
        preferred_type: ProbeType | None = None
    ) -> ProbePacket:
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
        unused_strategies = hypothesis.get_unused_strategies(
            [s.strategy_name for s in strategies]
        )
        
        if not unused_strategies:
            # All strategies exhausted, pick least recently used
            unused_strategies = [strategies[0].strategy_name] if strategies else ["default"]
        
        # Select strategy
        strategy_name = unused_strategies[0]
        strategy = StrategyRegistry.get_strategy(strategy_name)
        
        # Determine probe type
        probe_type = preferred_type or (
            strategy.probe_type if strategy else ProbeType.BINARY_CHOICE
        )
        
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
    
    async def process_response(
        self,
        probe_id: str,
        response: ProbeResponse
    ) -> list[Hypothesis]:
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
            
            delta = self._calculate_confidence_delta(
                probe, response, response_key, hyp.suspected_value
            )
            
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
                await self._emit_confidence_updated(
                    hyp, old_confidence, hyp.confidence
                )
        
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
                    
                    logger.info(
                        f"Confirmed {field_name}={hyp.suspected_value} "
                        f"with confidence {hyp.confidence:.2f}"
                    )
                    
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
        self,
        probe: ProbePacket,
        response: ProbeResponse,
        response_key: str,
        candidate: str
    ) -> float:
        """Calculate confidence delta for a candidate based on response."""
        if not probe.confidence_mappings:
            # No mappings, use small default
            return 0.05 if response_key in ("0", "yes", "low") else -0.02
        
        return probe.get_confidence_delta(response_key, candidate)
    
    async def _emit_confidence_updated(
        self,
        hypothesis: Hypothesis,
        old_confidence: float,
        new_confidence: float
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
                user_id=hypothesis.user_id,
                field=hypothesis.field,
                confirmed_value=hypothesis.suspected_value
            )
        except Exception as e:
            logger.warning(f"Failed to update StateTracker for confirmation: {e}")
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def get_hypotheses_for_user(self, user_id: int) -> list[Hypothesis]:
        """Get all hypotheses for a user."""
        return list(self._hypotheses.get(user_id, {}).values())
    
    def get_active_hypotheses(self, user_id: int) -> list[Hypothesis]:
        """Get unresolved hypotheses for a user."""
        return [
            h for h in self._hypotheses.get(user_id, {}).values()
            if not h.resolved
        ]
    
    def get_confirmed_hypotheses(self, user_id: int) -> list[Hypothesis]:
        """Get confirmed hypotheses for a user."""
        return [
            h for h in self._hypotheses.get(user_id, {}).values()
            if h.resolved and h.resolution_method == "confirmed"
        ]


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
