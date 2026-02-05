"""
GUTTERS Synthesis Orchestrator

Manages synthesis lifecycle:
- When to synthesize (trigger evaluation)
- What modules to include
- How to update Active Memory

Events that trigger re-synthesis:
- Module calculated (new data available)
- Genesis field confirmed (refined data)
- User requested (manual refresh)
- Scheduled (daily at user's preferred time)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import TYPE_CHECKING, Any

from .active_memory import get_active_memory

if TYPE_CHECKING:
    from .active_memory import ActiveMemory

logger = logging.getLogger(__name__)


class SynthesisTrigger(str, Enum):
    """
    Events that trigger synthesis re-generation.

    Split into:
    - IMPLEMENTED: Currently working triggers
    - STUBBED: Future tracking module triggers
    """

    # === IMPLEMENTED (exist now) ===
    MODULE_CALCULATED = "module_calculated"  # Module finished calculation
    GENESIS_FIELD_CONFIRMED = "genesis_confirmed"  # Field refined via Genesis
    USER_REQUESTED = "user_requested"  # User asked for refresh
    SCHEDULED = "scheduled"  # Daily scheduled synthesis

    # === STUBBED (for future tracking modules) ===
    SOLAR_STORM_DETECTED = "solar_storm"  # G4+ storm detected
    LUNAR_PHASE_CHANGE = "lunar_phase"  # New/full moon
    TRANSIT_EXACT = "transit_exact"  # Transit becomes exact
    JOURNAL_ENTRY_ADDED = "journal_entry"  # New journal entry
    PATTERN_DETECTED = "pattern_detected"  # Observer found pattern


# Triggers that always cause immediate re-synthesis
CRITICAL_TRIGGERS = {
    SynthesisTrigger.MODULE_CALCULATED,
    SynthesisTrigger.GENESIS_FIELD_CONFIRMED,
    SynthesisTrigger.USER_REQUESTED,
}


class SynthesisOrchestrator:
    """
    Orchestrates synthesis lifecycle.

    Decides when to re-synthesize and manages the process:
    - Evaluates trigger importance
    - Checks synthesis age and validity
    - Triggers background or foreground synthesis
    - Updates Active Memory with results

    Example:
        >>> from src.app.core.memory.synthesis_orchestrator import get_orchestrator
        >>>
        >>> orchestrator = await get_orchestrator()
        >>>
        >>> # Trigger synthesis if needed
        >>> result = await orchestrator.trigger_synthesis(
        ...     user_id=1,
        ...     trigger_type=SynthesisTrigger.MODULE_CALCULATED,
        ...     background=True
        ... )
    """

    def __init__(self, memory: ActiveMemory):
        """
        Initialize orchestrator.

        Args:
            memory: ActiveMemory instance for caching
        """
        self.memory = memory
        self.event_bus = None  # Set during startup via set_event_bus()

    def set_event_bus(self, event_bus: Any) -> None:
        """Set event bus for publishing synthesis events."""
        self.event_bus = event_bus

    async def should_synthesize(self, user_id: int, trigger: str | SynthesisTrigger) -> bool:
        """
        Determine if synthesis is needed.

        Rules:
        1. Always synthesize if no synthesis exists
        2. Synthesize if synthesis is stale (>24h old)
        3. Synthesize on critical triggers (new module, pattern detected)
        4. Don't synthesize on every prompt (too expensive)

        Args:
            user_id: User to evaluate
            trigger: What triggered this check

        Returns:
            True if synthesis should run

        Example:
            >>> if await orchestrator.should_synthesize(1, "user_requested"):
            ...     await orchestrator.trigger_synthesis(1, "user_requested")
        """
        # Get current synthesis
        synthesis = await self.memory.get_master_synthesis(user_id)

        # No synthesis exists - must create
        if not synthesis:
            logger.info(f"No synthesis exists for user {user_id}, will synthesize")
            return True

        # Stale synthesis (>24h old)
        if synthesis.get("validity") == "stale":
            logger.info(f"Synthesis is stale for user {user_id}, will re-synthesize")
            return True

        # Convert string to enum if needed
        if isinstance(trigger, str):
            try:
                trigger = SynthesisTrigger(trigger)
            except ValueError:
                logger.warning(f"Unknown trigger type: {trigger}")
                return False

        # Critical triggers always cause re-synthesis
        if trigger in CRITICAL_TRIGGERS:
            logger.info(f"Critical trigger {trigger.value} for user {user_id}, will synthesize")
            return True

        # Non-critical triggers - don't synthesize
        logger.debug(f"Non-critical trigger {trigger.value} for user {user_id}, skipping synthesis")
        return False

    async def trigger_synthesis(
        self, user_id: int, trigger_type: str | SynthesisTrigger, background: bool = True
    ) -> dict | None:
        """
        Trigger synthesis if needed.

        Args:
            user_id: User to synthesize for
            trigger_type: What triggered this (for logging)
            background: If True, queue job (don't block). If False, wait for result.

        Returns:
            Synthesis dict if background=False and synthesis ran.
            None if background=True or synthesis wasn't needed.

        Example:
            >>> # Background (non-blocking)
            >>> await orchestrator.trigger_synthesis(1, "module_calculated")
            >>>
            >>> # Foreground (blocking)
            >>> result = await orchestrator.trigger_synthesis(
            ...     1, "user_requested", background=False
            ... )
        """
        # Convert to string for logging
        trigger_str = trigger_type.value if isinstance(trigger_type, SynthesisTrigger) else trigger_type

        should_run = await self.should_synthesize(user_id, trigger_type)

        if not should_run:
            # Use existing synthesis
            logger.debug(f"Synthesis not needed for user {user_id}, returning cached")
            return await self.memory.get_master_synthesis(user_id)

        if background:
            # Queue as background job
            await self._queue_background_synthesis(user_id, trigger_str)
            return None
        else:
            # Run now (blocks)
            return await self._run_synthesis(user_id, trigger_str)

    async def _queue_background_synthesis(self, user_id: int, trigger_type: str) -> None:
        """Queue synthesis as background job."""
        try:
            # Try ARQ worker first
            from src.app.core.worker.client import get_arq_pool

            pool = await get_arq_pool()
            if pool:
                await pool.enqueue_job("synthesize_profile_job", user_id, trigger_type)
                logger.info(f"Queued synthesis job for user {user_id}, trigger: {trigger_type}")
                return
        except Exception as e:
            logger.warning(f"ARQ not available, running synthesis inline: {e}")

        # Fallback: run inline (but don't block)
        import asyncio

        asyncio.create_task(self._run_synthesis(user_id, trigger_type))

    async def _run_synthesis(self, user_id: int, trigger_type: str) -> dict:
        """
        Actually run synthesis and update memory.

        Args:
            user_id: User to synthesize
            trigger_type: What triggered this (for logging)

        Returns:
            Synthesis result dict
        """
        logger.info(f"Starting synthesis for user {user_id}, trigger: {trigger_type}")
        start_time = datetime.now(UTC)

        try:
            from ...core.db.database import local_session
            from ...modules.intelligence.synthesis import ProfileSynthesizer

            async with local_session() as db:
                synthesizer = ProfileSynthesizer()
                synthesis = await synthesizer.synthesize_profile(user_id, db)

            # Update hot memory
            await self.memory.set_master_synthesis(
                user_id, synthesis.synthesis, synthesis.themes, synthesis.modules_included
            )

            # Publish event
            if self.event_bus:
                from ...protocol.events import SYNTHESIS_COMPLETED

                await self.event_bus.publish(
                    event_type=SYNTHESIS_COMPLETED,
                    payload={
                        "user_id": user_id,
                        "trigger": trigger_type,
                        "themes": synthesis.themes,
                        "modules_included": synthesis.modules_included,
                    },
                    source="memory.synthesis_orchestrator",
                    user_id=str(user_id),
                )

            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"Synthesis complete for user {user_id} in {duration:.2f}s, modules: {synthesis.modules_included}"
            )

            return synthesis.model_dump()

        except Exception as e:
            logger.error(f"Synthesis failed for user {user_id}: {e}")
            raise

    async def get_or_create_synthesis(self, user_id: int) -> dict | None:
        """
        Get synthesis, creating if needed.

        Fast path: returns cached synthesis if valid.
        Slow path: synthesizes if no valid synthesis exists.

        Args:
            user_id: User ID

        Returns:
            Synthesis dict or None if no modules calculated
        """
        synthesis = await self.memory.get_master_synthesis(user_id)

        if synthesis and synthesis.get("validity") == "valid":
            return synthesis

        # Need to synthesize
        return await self.trigger_synthesis(user_id, trigger_type=SynthesisTrigger.SCHEDULED, background=False)


# Singleton orchestrator
_orchestrator: SynthesisOrchestrator | None = None


async def get_orchestrator() -> SynthesisOrchestrator:
    """
    Get the singleton SynthesisOrchestrator instance.

    Initializes ActiveMemory if not already done.

    Returns:
        Global SynthesisOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        memory = get_active_memory()

        # Ensure memory is initialized
        if not memory.redis_client:
            await memory.initialize()

        _orchestrator = SynthesisOrchestrator(memory)

    return _orchestrator
