import logging
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db.database import local_session
from src.app.core.events.bus import get_event_bus
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.evolution.refiner import get_evolution_refiner
from src.app.modules.intelligence.genesis.persistence import get_genesis_persistence
from src.app.protocol import events

logger = logging.getLogger(__name__)


class GenesisSemanticListener:
    """
    Listens for evolution events and refines Genesis profile certainties.

    This listener implements "Semantic Evolution" by delegating deep analysis
    to the EvolutionRefiner.
    """

    def __init__(self):
        self.bus = get_event_bus()
        self.persistence = get_genesis_persistence()
        self.refiner = get_evolution_refiner()

    async def initialize(self):
        """Register listeners for semantic refinement."""
        await self.bus.subscribe(events.QUEST_COMPLETED, self.handle_quest_completed)
        await self.bus.subscribe(events.EVOLUTION_LEVEL_UP, self.handle_level_up)
        await self.bus.subscribe(events.COSMIC_STORM_DETECTED, self.handle_cosmic_event)
        # transit_exact is emitted by TransitTracker
        await self.bus.subscribe("transit_exact", self.handle_cosmic_event)

    async def handle_quest_completed(self, packet: Any):
        """
        Refine profile when a quest is completed (Daily Refinement).
        """
        payload = packet.payload
        user_id = packet.user_id
        if not user_id:
            return

        quest_id = payload.get("quest_id")

        async with local_session() as db:
            from src.app.modules.features.quests.models import Quest, QuestCategory, QuestDifficulty

            result = await db.execute(select(Quest).where(Quest.id == quest_id))
            quest = result.scalar_one_or_none()
            if not quest:
                return

            # Throttling: Only refine significant evolution events
            should_refine = quest.difficulty in [
                QuestDifficulty.MEDIUM,
                QuestDifficulty.HARD,
                QuestDifficulty.ELITE,
            ] or quest.category in [QuestCategory.MISSION, QuestCategory.REFLECTION]

            if should_refine:
                await self._run_semantic_refinement(
                    user_id=int(user_id),
                    context_title=quest.title,
                    context_desc=quest.description or "",
                    db=db,
                    is_ascension=False,
                )
            else:
                logger.info(f"GenesisListener: Skipping refinement for insignificant quest: {quest.title}")

    async def handle_level_up(self, packet: Any):
        """
        Refine profile when a level up occurs (Ascension/Premium Refinement).
        """
        user_id = packet.user_id
        if not user_id:
            return

        payload = packet.payload
        new_level = payload.get("new_level")
        rank = payload.get("rank")

        async with local_session() as db:
            await self._run_semantic_refinement(
                user_id=int(user_id),
                context_title=f"Evolution Ascension: Level {new_level}",
                context_desc=f"User reached Rank {rank}. Evaluate overarching behavioral alignment.",
                db=db,
                is_ascension=True,
            )

    async def handle_cosmic_event(self, packet: Any):
        """
        Refine profile during significant cosmic weather.
        """
        user_id = packet.user_id
        if not user_id:
            return  # Environmental XP is often system-wide but here we expect a user_id

        event_type = packet.event_type
        await self._run_semantic_refinement(
            user_id=int(user_id),
            context_title=f"Cosmic Alignment: {event_type}",
            context_desc=str(packet.payload),
            db=None,  # Will open its own session if needed for profile
            is_ascension=False,
        )

    async def _run_semantic_refinement(
        self, user_id: int, context_title: str, context_desc: str, db: Optional[AsyncSession], is_ascension: bool
    ):
        """Internal coordinator for semantic refinement."""
        close_session = False
        if db is None:
            db = local_session()
            close_session = True

        try:
            # 1. Fetch Profile context
            result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            profile = result.scalar_one_or_none()
            if not profile:
                return

            journal_entries = profile.data.get("journal_entries", [])[-3:]
            journal_text = " | ".join([e.get("text", "") for e in journal_entries])

            # 2. Find Candidates to refine
            uncertainties = await self.persistence.get_all_from_profile(user_id, db)
            if not uncertainties:
                return

            for declaration in uncertainties:
                for field in declaration.unconfirmed_fields:
                    # For ascension, we might refine multiple, for daily just the best candidate of one field
                    best_candidate = field.best_candidate
                    if not best_candidate:
                        continue

                    # 3. Call Refiner (Multi-tier)
                    refinement = await self.refiner.refine_semantic_alignment(
                        user_id=user_id,
                        field_name=field.field,
                        candidate_value=best_candidate,
                        context_title=context_title,
                        context_desc=context_desc,
                        journal_text=journal_text,
                        is_ascension=is_ascension,
                    )

                    # 4. Apply refinement
                    if refinement.confidence_delta != 0:
                        old_conf = field.candidates[best_candidate]
                        new_conf = max(0.0, min(1.0, old_conf + refinement.confidence_delta))
                        field.candidates[best_candidate] = round(new_conf, 3)

                        # Store insight
                        p_data = dict(profile.data or {})
                        if "evolution_insights" not in p_data:
                            p_data["evolution_insights"] = []

                        p_data["evolution_insights"].append(
                            {
                                "timestamp": datetime.now(UTC).isoformat(),
                                "field": field.field,
                                "insight": refinement.evolution_insight,
                                "delta": refinement.confidence_delta,
                                "model": refinement.model_used,
                            }
                        )
                        profile.data = p_data

                        # Confirmation check
                        if new_conf >= 0.9:
                            logger.info(
                                f"Genesis: Field {field.field} confirmed for user {user_id} via Semantic Evolution."
                            )

                        # 5. Activity Trace with high fidelity
                        await self.bus.publish(
                            "system.evolution.trace",
                            {
                                "title": "Semantic Evolution",
                                "description": refinement.evolution_insight,
                                "metadata": {
                                    "field": field.field,
                                    "confidence": new_conf,
                                    "delta": refinement.confidence_delta,
                                    "model_used": refinement.model_used,
                                    "alignment_score": refinement.alignment_score,
                                    "reasoning": refinement.reasoning,
                                    "tokens": {"in": refinement.tokens_in, "out": refinement.tokens_out},
                                },
                            },
                            user_id=str(user_id),
                        )

            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(profile, "data")
            await db.commit()

        except Exception as e:
            logger.error(f"GenesisSemanticListener Error: {e}")
        finally:
            if close_session:
                await db.close()


# Singleton
_genesis_listener: GenesisSemanticListener | None = None


def get_genesis_listener() -> GenesisSemanticListener:
    global _genesis_listener
    if _genesis_listener is None:
        _genesis_listener = GenesisSemanticListener()
    return _genesis_listener
