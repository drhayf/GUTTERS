"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COUNCIL INTEGRATION LAYER                                 ║
║                                                                              ║
║   Bridges CouncilService with ChronosStateManager for unified state          ║
║   management. Ensures Redis caching, database persistence, and event         ║
║   emission work seamlessly across both systems.                              ║
║                                                                              ║
║   Usage:                                                                     ║
║       from src.app.modules.intelligence.council import get_council_integration║
║       integration = get_council_integration()                                ║
║       synthesis = await integration.get_unified_synthesis(user_id)           ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Cache keys
COUNCIL_SYNTHESIS_PREFIX = "council:synthesis:"
COUNCIL_TTL = 3600  # 1 hour - synthesis is computed fresh periodically


# =============================================================================
# UNIFIED SYNTHESIS MODEL
# =============================================================================

class UnifiedCosmicState(BaseModel):
    """
    Complete unified cosmic state combining Cardology and I-Ching.

    This is the "Master Cosmic Context" injected into LLM prompts.
    """

    # === Cardology (Macro) ===
    birth_card: dict[str, Any] | None = None
    current_planet: str | None = None
    current_card: dict[str, Any] | None = None
    period_theme: str | None = None
    period_guidance: str | None = None
    days_remaining: int | None = None

    # === I-Ching (Micro) ===
    sun_gate: int | None = None
    sun_line: int | None = None
    sun_gate_name: str | None = None
    sun_gene_key_gift: str | None = None
    sun_gene_key_shadow: str | None = None
    earth_gate: int | None = None
    earth_gate_name: str | None = None
    earth_gene_key_gift: str | None = None
    polarity_theme: str | None = None

    # === Council Synthesis ===
    resonance_score: float | None = None
    resonance_type: str | None = None
    dominant_element: str | None = None
    synthesis_guidance: list[str] = Field(default_factory=list)
    macro_symbol: str | None = None
    micro_symbol: str | None = None

    # === Metadata ===
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cache_source: str = "fresh"  # "redis" or "fresh"

    def to_llm_context(self) -> str:
        """
        Format as structured context for LLM injection.

        Returns:
            Formatted string for prompt injection
        """
        lines = ["## COUNCIL OF SYSTEMS - COSMIC COORDINATES"]

        # Cardology section
        lines.append("\n### Macro Cycle (Cardology - 52 Day Period)")
        if self.birth_card:
            card_name = f"{self.birth_card.get('rank_name', '')} of {self.birth_card.get('suit', '')}"
            lines.append(f"Birth Card (Core Identity): {card_name}")
        if self.current_planet:
            card_display = self.current_card.get("name", "Unknown") if self.current_card else "Unknown"
            lines.append(f"Current Period: {self.current_planet} (Card: {card_display})")
        if self.days_remaining is not None:
            lines.append(f"Days Remaining: {self.days_remaining}")
        if self.period_theme:
            lines.append(f"Theme: {self.period_theme}")
        if self.period_guidance:
            lines.append(f"Guidance: {self.period_guidance}")

        # I-Ching section
        lines.append("\n### Micro Cycle (I-Ching - Daily Gate)")
        if self.sun_gate:
            lines.append(f"Sun Gate: {self.sun_gate}.{self.sun_line} - {self.sun_gate_name}")
            lines.append(f"Gene Key: {self.sun_gene_key_shadow} → {self.sun_gene_key_gift}")
        if self.earth_gate:
            lines.append(f"Earth Gate: {self.earth_gate} - {self.earth_gate_name} ({self.earth_gene_key_gift})")
        if self.polarity_theme:
            lines.append(f"Polarity Theme: {self.polarity_theme}")

        # Council synthesis
        lines.append("\n### Cross-System Resonance")
        if self.resonance_score is not None:
            lines.append(f"Resonance: {self.resonance_type} ({self.resonance_score:.0%})")
        if self.dominant_element:
            lines.append(f"Dominant Element: {self.dominant_element}")
        if self.synthesis_guidance:
            lines.append("Today's Guidance:")
            for g in self.synthesis_guidance[:3]:
                lines.append(f"  • {g}")

        return "\n".join(lines)


# =============================================================================
# COUNCIL INTEGRATION SERVICE
# =============================================================================

class CouncilIntegration:
    """
    Integration layer that bridges CouncilService with ChronosStateManager.

    Provides:
    - Unified state retrieval (Cardology + I-Ching + Synthesis)
    - Redis caching for computed synthesis
    - Event coordination between systems
    - LLM context formatting

    This is the recommended entry point for getting cosmic context.
    """

    def __init__(self):
        """Initialize integration (services are lazy-loaded)."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize integration services."""
        self._initialized = True
        logger.info("[CouncilIntegration] Initialized")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        logger.info("[CouncilIntegration] Cleaned up")

    # =========================================================================
    # UNIFIED STATE RETRIEVAL
    # =========================================================================

    async def get_unified_state(
        self,
        user_id: int,
        birth_date: str | date | None = None,
        force_refresh: bool = False
    ) -> UnifiedCosmicState:
        """
        Get unified cosmic state from all systems.

        Retrieves from Redis cache if available, otherwise computes fresh.
        Combines:
        - Cardology state from ChronosStateManager
        - I-Ching hexagram from CouncilService
        - Cross-system synthesis from Council of Systems

        Args:
            user_id: User ID for personalized state
            birth_date: Birth date (required for Cardology if not cached)
            force_refresh: Skip cache and recalculate

        Returns:
            UnifiedCosmicState with all cosmic coordinates
        """
        from src.app.core.memory.active_memory import get_active_memory

        memory = get_active_memory()
        cache_key = f"{COUNCIL_SYNTHESIS_PREFIX}{user_id}"

        # Check cache first (unless force refresh)
        if not force_refresh and memory.redis_client:
            try:
                cached = await memory.redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    data["cache_source"] = "redis"
                    return UnifiedCosmicState(**data)
            except Exception as e:
                logger.warning(f"[CouncilIntegration] Cache read error: {e}")

        # Compute fresh state
        state = await self._compute_unified_state(user_id, birth_date)

        # Cache the result
        if memory.redis_client:
            try:
                await memory.redis_client.setex(
                    cache_key,
                    COUNCIL_TTL,
                    state.model_dump_json()
                )
            except Exception as e:
                logger.warning(f"[CouncilIntegration] Cache write error: {e}")

        return state

    async def _compute_unified_state(
        self,
        user_id: int,
        birth_date: str | date | None = None
    ) -> UnifiedCosmicState:
        """
        Compute unified state from all systems.

        This is the core computation that aggregates:
        1. ChronosStateManager for Cardology (52-day periods)
        2. CouncilService for I-Ching (daily gates)
        3. Council of Systems for cross-system synthesis
        """
        from src.app.core.state.chronos import get_chronos_manager
        from src.app.modules.intelligence.council import get_council_service

        chronos = get_chronos_manager()
        council = get_council_service()

        # === CARDOLOGY (via ChronosStateManager) ===
        cardology_state = await chronos.get_user_chronos(user_id, birth_date)

        # === I-CHING (via CouncilService) ===
        hexagram = council.get_current_hexagram()

        # === COUNCIL SYNTHESIS ===
        # Parse birth_date for synthesis if available
        bd = None
        if birth_date:
            if isinstance(birth_date, str):
                bd = date.fromisoformat(birth_date)
            else:
                bd = birth_date

        synthesis = council.get_council_synthesis(birth_date=bd)

        # Build unified state
        return UnifiedCosmicState(
            # Cardology
            birth_card=cardology_state.get("birth_card") if cardology_state else None,
            current_planet=cardology_state.get("current_planet") if cardology_state else None,
            current_card=cardology_state.get("current_card") if cardology_state else None,
            period_theme=cardology_state.get("theme") if cardology_state else None,
            period_guidance=cardology_state.get("guidance") if cardology_state else None,
            days_remaining=cardology_state.get("days_remaining") if cardology_state else None,

            # I-Ching
            sun_gate=hexagram.sun_gate,
            sun_line=hexagram.sun_line,
            sun_gate_name=hexagram.sun_gate_name,
            sun_gene_key_gift=hexagram.sun_gene_key_gift,
            sun_gene_key_shadow=hexagram.sun_gene_key_shadow,
            earth_gate=hexagram.earth_gate,
            earth_gate_name=hexagram.earth_gate_name,
            earth_gene_key_gift=hexagram.earth_gene_key_gift,
            polarity_theme=hexagram.polarity_theme,

            # Council Synthesis
            resonance_score=synthesis.resonance_score,
            resonance_type=synthesis.resonance_type,
            dominant_element=synthesis.dominant_element,
            synthesis_guidance=synthesis.guidance,
            macro_symbol=synthesis.macro_symbol,
            micro_symbol=synthesis.micro_symbol,

            cache_source="fresh"
        )

    async def invalidate_cache(self, user_id: int) -> None:
        """Invalidate cached synthesis for a user."""
        from src.app.core.memory.active_memory import get_active_memory

        memory = get_active_memory()
        if memory.redis_client:
            await memory.redis_client.delete(f"{COUNCIL_SYNTHESIS_PREFIX}{user_id}")
            logger.info(f"[CouncilIntegration] Invalidated cache for user {user_id}")

    # =========================================================================
    # LLM CONTEXT FORMATTING
    # =========================================================================

    async def get_llm_context(
        self,
        user_id: int,
        birth_date: str | date | None = None
    ) -> str:
        """
        Get formatted cosmic context for LLM prompt injection.

        Args:
            user_id: User ID
            birth_date: Birth date for Cardology calculations

        Returns:
            Formatted string ready for prompt injection
        """
        state = await self.get_unified_state(user_id, birth_date)
        return state.to_llm_context()

    async def get_magi_context_dict(
        self,
        user_id: int,
        birth_date: str | date | None = None
    ) -> dict[str, Any]:
        """
        Get cosmic context as a dictionary for flexible use.

        Args:
            user_id: User ID
            birth_date: Birth date for Cardology calculations

        Returns:
            Dictionary with all cosmic coordinates
        """
        state = await self.get_unified_state(user_id, birth_date)
        return state.model_dump()

    # =========================================================================
    # EVENT COORDINATION
    # =========================================================================

    async def check_and_emit_transitions(
        self,
        user_id: int,
        birth_date: str | date | None = None
    ) -> dict[str, bool]:
        """
        Check for cosmic transitions and emit appropriate events.

        Coordinates between:
        - ChronosStateManager (period shifts)
        - CouncilService (gate transitions)

        Args:
            user_id: User ID
            birth_date: Birth date for Cardology refresh

        Returns:
            Dict indicating which transitions occurred:
            {"period_shift": bool, "gate_shift": bool, "resonance_shift": bool}
        """
        from src.app.core.state.chronos import get_chronos_manager
        from src.app.modules.intelligence.council import get_council_service

        chronos = get_chronos_manager()
        council = get_council_service()

        transitions = {
            "period_shift": False,
            "gate_shift": False,
            "resonance_shift": False
        }

        # Check Cardology period (via ChronosManager - handles its own events)
        if birth_date:
            old_state = await chronos.get_user_chronos(user_id)
            new_state = await chronos.refresh_user_chronos(user_id, birth_date)

            if old_state and new_state:
                if old_state.get("current_planet") != new_state.get("current_planet"):
                    transitions["period_shift"] = True

        # Check I-Ching gate (via CouncilService)
        gate_transition = await council.check_gate_transition(user_id)
        if gate_transition:
            transitions["gate_shift"] = True
            # Event emission handled in check_gate_transition

        # Invalidate synthesis cache if any transition occurred
        if any(transitions.values()):
            await self.invalidate_cache(user_id)

        return transitions

    # =========================================================================
    # JOURNAL ENTRY GENERATION
    # =========================================================================

    async def generate_cosmic_journal_entry(
        self,
        user_id: int,
        entry_type: str = "daily_synthesis"
    ) -> dict[str, Any] | None:
        """
        Generate a cosmic journal entry based on current state.

        Args:
            user_id: User ID
            entry_type: Type of entry ("daily_synthesis", "gate_transition", "resonance_shift")

        Returns:
            Generated journal entry dict or None
        """
        from src.app.modules.intelligence.council import get_council_service
        from src.app.modules.intelligence.council.journal_generator import get_journal_generator

        council = get_council_service()
        generator = get_journal_generator()

        hexagram = council.get_current_hexagram()
        synthesis = council.get_council_synthesis()

        if entry_type == "daily_synthesis":
            entry = generator.generate_daily_synthesis_entry(synthesis, hexagram)
            return entry.model_dump() if entry else None

        # Other entry types would be generated from transition data
        # which requires the actual transition context
        return None


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_council_integration: CouncilIntegration | None = None


def get_council_integration() -> CouncilIntegration:
    """
    Get the singleton CouncilIntegration instance.

    Example:
        >>> from src.app.modules.intelligence.council.integration import get_council_integration
        >>> integration = get_council_integration()
        >>> state = await integration.get_unified_state(user_id=123)
    """
    global _council_integration
    if _council_integration is None:
        _council_integration = CouncilIntegration()
    return _council_integration
