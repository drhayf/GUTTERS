import logging
from datetime import datetime, UTC
from typing import Dict, Any

from sqlalchemy import select

from src.app.core.events.bus import get_event_bus
from src.app.protocol import events
from src.app.protocol.packet import ProgressionPacket
from src.app.core.db.database import local_session
from src.app.modules.features.chat.session_manager import SessionManager
from src.app.modules.intelligence.journalist.engine import JournalistEngine
from src.app.models.insight import JournalEntry, JournalSource
from src.app.core.memory.active_memory import get_active_memory
from src.app.models.progression import PlayerStats

logger = logging.getLogger(__name__)


class SystemJournalist:
    """
    Listens to system events (Quest Completion, Level Up) and writes entries to the System Journal.
    Integrates with JournalistEngine (LLM) for high-fidelity logs.
    """

    def __init__(self):
        self.bus = get_event_bus()
        self.session_manager = SessionManager()
        self.engine = JournalistEngine()
        self.memory = get_active_memory()

    async def initialize(self):
        """Register listeners."""
        await self.bus.subscribe(events.PROGRESSION_EXPERIENCE_GAIN, self.handle_experience_gain)
        await self.bus.subscribe(events.EVOLUTION_LEVEL_UP, self.handle_level_up)
        # Ensure memory is initialized
        if not self.memory.redis_client:
            await self.memory.initialize()

    async def _get_context_snapshot(self, user_id: int, db) -> Dict[str, Any]:
        """Allow Journalist to see the world state including magi chronos context."""
        rank = "E"
        sync = 0.0
        kp = 0

        # 1. Get Player Context
        try:
            result = await db.execute(select(PlayerStats).where(PlayerStats.user_id == user_id))
            stats = result.scalar_one_or_none()
            if stats:
                rank = stats.rank
                sync = stats.sync_rate * 100  # Convert to percentage
        except Exception as e:
            logger.warning(f"Could not fetch PlayerStats for context: {e}")

        # 2. Get Cosmic Context
        try:
            kp_raw = await self.memory.get("cosmic:kp_index")
            if kp_raw:
                kp = float(kp_raw)
        except Exception:
            pass

        context = {
            "rank": rank,
            "sync_rate": int(sync),
            "kp_index": kp,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 3. Inject Magi Chronos Context (Critical for cyclical pattern detection)
        try:
            from src.app.core.state.chronos import get_chronos_manager
            chronos_manager = get_chronos_manager()
            chronos_state = await chronos_manager.get_user_chronos(user_id)

            if chronos_state:
                context["magi"] = {
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
        except Exception as e:
            logger.warning(f"[SystemJournalist] Could not inject magi context: {e}")

        return context

    async def _save_to_living_archive(self, user_id: int, content: str, context: Dict[str, Any], db):
        """Save to the official JournalEntry table."""
        try:
            entry = JournalEntry(
                user_id=user_id,
                content=content,
                source=JournalSource.SYSTEM,
                context_snapshot=context,
                created_at=datetime.now(UTC),
            )
            db.add(entry)
            await db.commit()
            await db.refresh(entry)
            logger.info(f"SystemJournalist: Saved System Entry for User {user_id}")

            # Notify System (Notifications, Achievements, etc.)
            await self.bus.publish(
                events.JOURNAL_ENTRY_CREATED,
                {
                    "entry_id": entry.id,
                    "user_id": user_id,
                    "title": "System Log",  # Generic title for system entries for now, or could parse
                    "source": "system",
                },
                user_id=str(user_id),
            )

        except Exception as e:
            logger.error(f"Failed to save System Entry to Archive: {e}")

    async def handle_experience_gain(self, packet: ProgressionPacket):
        """
        Log quest completion and XP gain using LLM.
        """
        try:
            user_id = getattr(packet, "user_id", None)
            if not user_id:
                if hasattr(packet, "payload") and packet.payload:
                    user_id = packet.payload.get("user_id")

            if user_id:
                user_id = int(user_id)
            else:
                return

            # Extract Data
            amount = getattr(packet, "amount", 0)
            payload = getattr(packet, "payload", {})
            title = payload.get("title", "Unknown Activity")

            async with local_session() as db:
                # 1. Build Context
                context = await self._get_context_snapshot(user_id, db)

                # 2. Generate Log (LLM)
                flavor_text = await self.engine.generate_log_entry(
                    event_type="QUEST_COMPLETE", title=title, context=context, details={"xp": amount}
                )

                # 3. Save to Living Archive (JournalEntry)
                await self._save_to_living_archive(user_id, flavor_text, context, db)

                # 4. Post to Master Chat (Strict Schema Metadata)
                master_session = await self.session_manager.get_default_master_conversation(user_id, db)
                if master_session:
                    # Construct strict metadata payload for Frontend
                    metadata = {
                        "type": "system_event",
                        "event_type": "xp_gain",
                        "title": title,
                        "amount": amount,
                        "icon": "zap",
                        "flavor_text": flavor_text,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    # Content is fallback/accessible text
                    # Frontend will use metadata to render the "Game Log" UI
                    await self.session_manager.add_message(
                        session_id=master_session.id,
                        role="system_event",
                        content=f"SYSTEM EVENT: {title} (+{amount} XP)",
                        metadata=metadata,
                        db=db,
                    )

        except Exception as e:
            logger.error(f"SystemJournalist Error (XP): {e}", exc_info=True)

    async def handle_level_up(self, payload: Dict[str, Any], user_id: str):
        """
        Log Level Up events.
        """
        try:
            uid = int(user_id)
            new_level = payload.get("new_level", "?")

            async with local_session() as db:
                context = await self._get_context_snapshot(uid, db)

                # LLM Log
                flavor_text = await self.engine.generate_log_entry(
                    event_type="LEVEL_UP",
                    title=f"Ascended to Level {new_level}",
                    context=context,
                    details={"level": new_level},
                )

                await self._save_to_living_archive(uid, flavor_text, context, db)

                # Chat
                master_session = await self.session_manager.get_default_master_conversation(uid, db)
                if master_session:
                    metadata = {
                        "type": "system_event",
                        "event_type": "level_up",
                        "title": f"Level Up: {new_level}",
                        "amount": 0,
                        "icon": "star",
                        "flavor_text": flavor_text,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    await self.session_manager.add_message(
                        session_id=master_session.id,
                        role="system_event",
                        content=f"LEVEL UP: {new_level}",
                        metadata=metadata,
                        db=db,
                    )

        except Exception as e:
            logger.error(f"SystemJournalist Error (LevelUp): {e}")


# Singleton
_journalist: SystemJournalist = None


def get_system_journalist() -> SystemJournalist:
    global _journalist
    if not _journalist:
        _journalist = SystemJournalist()
    return _journalist
