"""
Insight Listener Module.

Subscribes to system events and triggers the InsightManager to generate
proactive reflection prompts, journal entries, and notifications.

Event Handlers:
- cosmic_update: Solar/Lunar/Transit triggers
- MAGI_PERIOD_SHIFT: 52-day planetary period transitions
- CYCLICAL_PATTERN_*: Observer cyclical pattern detection events
"""

import logging
from typing import Any
from sqlalchemy import select
from src.app.core.events.bus import get_event_bus
from src.app.core.db.database import async_get_db
from src.app.modules.intelligence.insight.manager import InsightManager
from src.app.protocol.events import (
    MAGI_PERIOD_SHIFT,
    CYCLICAL_PATTERN_DETECTED,
    CYCLICAL_PATTERN_CONFIRMED,
    CYCLICAL_PATTERN_EVOLUTION,
    CYCLICAL_THEME_ALIGNMENT,
)

logger = logging.getLogger(__name__)


async def handle_cosmic_update(payload: dict[str, Any]):
    """
    Handle COSMIC_UPDATE event.
    Trigger InsightManager to evaluate potential reflection prompts for ALL users.
    """
    manager = InsightManager()

    # 1. Get DB session
    async for db in async_get_db():
        user_id = payload.get("user_id")

        # 2. Case: Global Event (No specific user_id)
        if not user_id:
            logger.info("Insight Engine reacting to GLOBAL COSMIC_UPDATE")
            # Fetch all active users
            from src.app.models.user import User

            stmt = select(User.id).where(User.is_deleted == False)
            result = await db.execute(stmt)
            user_ids = result.scalars().all()

            for uid in user_ids:
                try:
                    # Note: We could parallelize this with asyncio.gather,
                    # but for now we'll do them sequentially to avoid overloading DB/LLM.
                    # Ideally this triggers an arq job per user.
                    await manager.evaluate_cosmic_triggers(uid, payload, db)
                except Exception as e:
                    logger.error(f"Error evaluating insights for user {uid}: {e}")

        # 3. Case: Targeted Event
        else:
            logger.info(f"Insight Engine reacting to targeted COSMIC_UPDATE for user {user_id}")
            try:
                await manager.evaluate_cosmic_triggers(user_id, payload, db)
            except Exception as e:
                logger.error(f"Error evaluating insight triggers: {e}")


async def handle_magi_period_shift(payload: dict[str, Any]):
    """
    Handle MAGI_PERIOD_SHIFT event.
    
    When a user's 52-day planetary period changes, generate a reflection prompt
    to help them transition into the new energy.
    
    Payload:
        user_id: int
        old_planet: str (e.g., "Mercury")
        new_planet: str (e.g., "Venus")
        old_card: str (e.g., "King of Clubs")
        new_card: str (e.g., "9 of Hearts")
    """
    manager = InsightManager()
    user_id = payload.get("user_id")
    
    if not user_id:
        logger.warning("MAGI_PERIOD_SHIFT received without user_id")
        return
    
    logger.info(
        f"[InsightListener] MAGI Period shift for user {user_id}: "
        f"{payload.get('old_planet')} → {payload.get('new_planet')}"
    )
    
    async for db in async_get_db():
        try:
            await manager.generate_period_transition_prompt(user_id, payload, db)
        except Exception as e:
            logger.error(f"Error generating period transition prompt for user {user_id}: {e}")


async def register_insight_listeners():
    """Register listeners for insight engine."""
    bus = get_event_bus()
    # Assuming the event name string is 'cosmic_update' or similar.
    # Let's use a constant if possible, or string literal.
    await bus.subscribe("cosmic_update", handle_cosmic_update)
    
    # Subscribe to MAGI period shifts for Cardology integration
    await bus.subscribe(MAGI_PERIOD_SHIFT, handle_magi_period_shift)
    logger.info("[InsightListener] Registered MAGI_PERIOD_SHIFT listener")
    
    # Subscribe to Cyclical Pattern events from Observer
    await bus.subscribe(CYCLICAL_PATTERN_DETECTED, handle_cyclical_pattern_detected)
    await bus.subscribe(CYCLICAL_PATTERN_CONFIRMED, handle_cyclical_pattern_confirmed)
    await bus.subscribe(CYCLICAL_PATTERN_EVOLUTION, handle_cyclical_pattern_evolution)
    await bus.subscribe(CYCLICAL_THEME_ALIGNMENT, handle_cyclical_theme_alignment)
    logger.info("[InsightListener] Registered Cyclical Pattern listeners")


# =============================================================================
# CYCLICAL PATTERN EVENT HANDLERS
# =============================================================================


async def handle_cyclical_pattern_detected(payload: dict[str, Any]):
    """
    Handle CYCLICAL_PATTERN_DETECTED event.
    
    When the Observer detects a new cyclical pattern, evaluate if it warrants
    a reflection prompt or proactive journal entry.
    
    Payload:
        user_id: int
        pattern_id: str
        pattern_type: str (period_symptom, variance, theme_alignment, evolution)
        period_card: str
        planetary_ruler: str
        confidence: float
        observation_count: int
        description: str
    """
    manager = InsightManager()
    user_id = payload.get("user_id")
    
    if not user_id:
        logger.warning("CYCLICAL_PATTERN_DETECTED received without user_id")
        return
    
    pattern_type = payload.get("pattern_type", "unknown")
    confidence = payload.get("confidence", 0)
    period_card = payload.get("period_card", "Unknown")
    
    logger.info(
        f"[InsightListener] Cyclical pattern detected for user {user_id}: "
        f"{pattern_type} in {period_card} (confidence: {confidence:.2f})"
    )
    
    # Only generate prompts for patterns with meaningful confidence
    if confidence < 0.5:
        logger.debug(f"Skipping low-confidence pattern ({confidence:.2f})")
        return
    
    async for db in async_get_db():
        try:
            await manager.generate_cyclical_pattern_prompt(
                user_id=user_id,
                pattern_data=payload,
                prompt_type="detected",
                db=db
            )
        except Exception as e:
            logger.error(f"Error generating cyclical pattern prompt for user {user_id}: {e}")


async def handle_cyclical_pattern_confirmed(payload: dict[str, Any]):
    """
    Handle CYCLICAL_PATTERN_CONFIRMED event.
    
    When a cyclical pattern reaches high confidence and is confirmed,
    generate a synthesis journal entry and notify the user.
    
    Payload:
        user_id: int
        pattern_id: str
        pattern_type: str
        period_card: str
        planetary_ruler: str
        confidence: float (>= 0.85)
        observation_count: int
        description: str
        evidence_summary: list
    """
    manager = InsightManager()
    user_id = payload.get("user_id")
    
    if not user_id:
        logger.warning("CYCLICAL_PATTERN_CONFIRMED received without user_id")
        return
    
    pattern_type = payload.get("pattern_type", "unknown")
    period_card = payload.get("period_card", "Unknown")
    confidence = payload.get("confidence", 0)
    
    logger.info(
        f"[InsightListener] Cyclical pattern CONFIRMED for user {user_id}: "
        f"{pattern_type} in {period_card} (confidence: {confidence:.2f})"
    )
    
    async for db in async_get_db():
        try:
            # Generate high-fidelity synthesis journal entry
            await manager.generate_cyclical_synthesis_entry(
                user_id=user_id,
                pattern_data=payload,
                db=db
            )
            
            # Also generate a reflection prompt for conscious integration
            await manager.generate_cyclical_pattern_prompt(
                user_id=user_id,
                pattern_data=payload,
                prompt_type="confirmed",
                db=db
            )
        except Exception as e:
            logger.error(f"Error handling confirmed cyclical pattern for user {user_id}: {e}")


async def handle_cyclical_pattern_evolution(payload: dict[str, Any]):
    """
    Handle CYCLICAL_PATTERN_EVOLUTION event.
    
    When the Observer detects evolution in a pattern across years,
    generate a deep insight about long-term growth.
    
    Payload:
        user_id: int
        pattern_id: str
        period_card: str
        planetary_ruler: str
        years_analyzed: list[int]
        mood_trajectory: str (improving, declining, stable, volatile)
        theme_evolution: dict
        confidence: float
    """
    manager = InsightManager()
    user_id = payload.get("user_id")
    
    if not user_id:
        logger.warning("CYCLICAL_PATTERN_EVOLUTION received without user_id")
        return
    
    mood_trajectory = payload.get("mood_trajectory", "stable")
    years = payload.get("years_analyzed", [])
    period_card = payload.get("period_card", "Unknown")
    
    logger.info(
        f"[InsightListener] Cyclical pattern EVOLUTION for user {user_id}: "
        f"{period_card} over {len(years)} years, trajectory: {mood_trajectory}"
    )
    
    async for db in async_get_db():
        try:
            await manager.generate_cyclical_evolution_insight(
                user_id=user_id,
                evolution_data=payload,
                db=db
            )
        except Exception as e:
            logger.error(f"Error generating evolution insight for user {user_id}: {e}")


async def handle_cyclical_theme_alignment(payload: dict[str, Any]):
    """
    Handle CYCLICAL_THEME_ALIGNMENT event.
    
    When journal themes consistently align with planetary guidance,
    acknowledge the user's alignment with cosmic rhythms.
    
    Payload:
        user_id: int
        pattern_id: str
        period_card: str
        planetary_ruler: str
        period_theme: str
        journal_themes: list[str]
        alignment_score: float
        observation_count: int
    """
    manager = InsightManager()
    user_id = payload.get("user_id")
    
    if not user_id:
        logger.warning("CYCLICAL_THEME_ALIGNMENT received without user_id")
        return
    
    alignment_score = payload.get("alignment_score", 0)
    period_card = payload.get("period_card", "Unknown")
    planetary_ruler = payload.get("planetary_ruler", "Unknown")
    
    logger.info(
        f"[InsightListener] Theme alignment detected for user {user_id}: "
        f"{period_card}/{planetary_ruler} alignment score: {alignment_score:.2f}"
    )
    
    # Only notify for strong alignment
    if alignment_score < 0.7:
        return
    
    async for db in async_get_db():
        try:
            await manager.generate_theme_alignment_acknowledgment(
                user_id=user_id,
                alignment_data=payload,
                db=db
            )
        except Exception as e:
            logger.error(f"Error generating theme alignment acknowledgment for user {user_id}: {e}")
