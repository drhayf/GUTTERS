import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import configure_mappers

from src.app.core.db.database import local_session
from src.app.models.chat_session import ChatMessage
from src.app.models.insight import JournalEntry

# Ensure models are loaded for SQLAlchemy
from src.app.modules.features.journal.system_journal import get_system_journalist
from src.app.protocol.packet import ProgressionPacket

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force configuration of mappers
configure_mappers()


async def verify_journalist_agent():
    logger.info("Starting Verification: Journalist Agent Fidelity...")

    user_id = 1  # Assuming user ID 1 exists

    # 1. Initialize Journalist
    journalist = get_system_journalist()
    await journalist.initialize()

    # 2. Simulate XP Event
    packet = ProgressionPacket(
        user_id=user_id,
        amount=150,
        reason="Verification Test",
        source="SYSTEM",
        event_type="XP_GAIN",
        payload={"title": "Operation: Fidelity Check", "category": "System"},
    )

    logger.info(f"Triggering XP Event for User {user_id}...")
    await journalist.handle_experience_gain(packet)

    # 3. Verify Database
    async with local_session() as db:
        # Check Journal Entry (Living Archive)
        logger.info("Verifying Living Archive (JournalEntry)...")
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user_id)
            .where(JournalEntry.source == "system")
            .order_by(JournalEntry.created_at.desc())
            .limit(1)
        )
        entry = result.scalar_one_or_none()

        if entry:
            logger.info(f"✅ Journal Entry Found! ID: {entry.id}")
            logger.info(f"   Content: {entry.content}")
            logger.info(f"   Source: {entry.source}")
            logger.info(f"   Context Snapshot: {entry.context_snapshot}")
        else:
            logger.error("❌ Journal Entry NOT found.")

        # Check Chat Message (Master Chat)
        logger.info("Verifying Master Chat (Message)...")
        # We look for the latest system_event
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.metadata_["type"].astext == "system_event")
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        msg = result.scalar_one_or_none()

        if msg:
            logger.info(f"✅ Chat Message Found! ID: {msg.id}")
            logger.info(f"   Role: {msg.role}")
            logger.info(f"   Metadata: {msg.metadata_}")

            # Verify Schema
            meta = msg.metadata_
            if meta.get("title") == "Operation: Fidelity Check" and meta.get("icon") == "zap":
                logger.info("✅ Schema Contract Verified.")
            else:
                logger.warning("⚠️ Schema Contract Mismatch.")
        else:
            logger.error("❌ Chat Message NOT found.")


if __name__ == "__main__":
    asyncio.run(verify_journalist_agent())
