import logging
import math
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db.database import local_session
from src.app.core.events.bus import get_event_bus
from src.app.models.progression import PlayerStats
from src.app.protocol import events
from src.app.protocol.packet import ProgressionPacket, Packet

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """
    Centralized Progression Engine for rank and XP math.

    Handles:
    1. XP accumulation from ProgressionPackets.
    2. Level-up logic and Rank thresholds.
    3. Temporal snapshots for progression history.
    """

    def __init__(self):
        self.bus = get_event_bus()

    async def initialize(self):
        """Register listener for experience gain."""
        await self.bus.subscribe(events.PROGRESSION_EXPERIENCE_GAIN, self.handle_experience_gain)

    async def handle_experience_gain(self, packet: ProgressionPacket):
        """
        Process experience gain events.
        """
        # DEBUG LOG
        print(
            f"DEBUG: EvolutionEngine received XP packet for user {packet.user_id}. Amount: {getattr(packet, 'amount', 'unset')}"
        )

        user_id = packet.user_id
        if not user_id:
            print("DEBUG: No user_id in packet")
            return

        # Packet source mapping for XP gain logic
        # For now, use explicit payload if from_dict didn't map correctly
        amount = getattr(packet, "amount", 10)
        reason = getattr(packet, "reason", "Insight Integration")
        category = getattr(packet, "category", "SYNC")

        print(f"DEBUG: Processing XP. Amount: {amount}, Reason: {reason}")

        # If the packet was received as a generic Packet, try to extract from payload
        if not hasattr(packet, "amount") and packet.payload:
            amount = packet.payload.get("amount", amount)
            reason = packet.payload.get("reason", reason)
            category = packet.payload.get("category", category)

        async with local_session() as db:
            # 1. Update PlayerStats
            stmt = select(PlayerStats).where(PlayerStats.user_id == int(user_id))
            result = await db.execute(stmt)
            stats = result.scalar_one_or_none()

            if not stats:
                stats = PlayerStats(user_id=int(user_id))
                db.add(stats)

            # Handle NULL values from existing database rows
            if stats.experience_points is None:
                stats.experience_points = 0
            if stats.level is None:
                stats.level = 1

            old_level = stats.level
            stats.experience_points += amount

            # Check Level Up (Loop for Power Leveling)
            leveled_up = False
            while True:
                # Threshold: XP = Level * 1000 * 1.5^(Level-1)
                next_level_threshold = int(stats.level * 1000 * math.pow(1.5, stats.level - 1))

                if stats.experience_points >= next_level_threshold:
                    stats.level += 1
                    leveled_up = True
                    logger.info(f"EvolutionEngine: Power Leveling! User {user_id} -> Level {stats.level}")
                else:
                    break

            # 2. Update History Snapshot (JSONB)
            history_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "amount": amount,
                "reason": reason,
                "category": category,
                "new_total": stats.experience_points,
                "level": stats.level,
            }

            # Ensure stats.sync_history is a list AND clone it to force SQLAlchemy update
            current_history = list(stats.sync_history) if stats.sync_history else []

            # Keep last 50 entries for temporal analysis
            current_history.append(history_entry)
            if len(current_history) > 50:
                current_history = current_history[-50:]

            stats.sync_history = current_history

            await db.commit()
            await db.refresh(stats)

            # 3. Emit Level Up if occurred
            if leveled_up:
                activity_trace = {
                    "title": "System Evolution",
                    "description": f"User reached Level {stats.level} (Rank {stats.rank})",
                    "milestones": [f"Rank: {stats.rank}", f"Level: {old_level} -> {stats.level}"],
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                await self.bus.publish(
                    events.EVOLUTION_LEVEL_UP,
                    {
                        "old_level": old_level,
                        "new_level": stats.level,
                        "rank": stats.rank,
                        "activity_trace": activity_trace,
                    },
                    user_id=str(user_id),
                )
                logger.info(f"EvolutionEngine: USER {user_id} LEVELED UP to {stats.level} ({stats.rank})")

            # 4. Sync to UserProfile (Observability)
            from src.app.models.user_profile import UserProfile

            stmt = select(UserProfile).where(UserProfile.user_id == int(user_id))
            result = await db.execute(stmt)
            profile = result.scalar_one_or_none()

            if profile:
                p_data = dict(profile.data or {})
                p_data["progression"] = {
                    "level": stats.level,
                    "rank": stats.rank,
                    "sync_rate": stats.sync_rate,
                    "xp": stats.experience_points,
                    "history": stats.sync_history,
                    "updated_at": datetime.now(UTC).isoformat(),
                }
                profile.data = p_data
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(profile, "data")
                await db.commit()


# Singleton
_evolution_engine: EvolutionEngine | None = None


def get_evolution_engine() -> EvolutionEngine:
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = EvolutionEngine()
    return _evolution_engine
