import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import configure_mappers

from src.app.core.db.database import local_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_quest_data(db, user_id):
    """Clean up all existing quest data for fresh seeding."""
    from src.app.modules.features.quests.models import Quest, QuestLog

    print("[CLEANUP] Removing old quest data...")

    # Get all quest IDs for this user
    stmt = select(Quest.id).where(Quest.user_id == user_id)
    result = await db.execute(stmt)
    quest_ids = result.scalars().all()

    # Delete all quest logs for these quests
    if quest_ids:
        stmt_logs = delete(QuestLog).where(QuestLog.quest_id.in_(quest_ids))
        await db.execute(stmt_logs)

    # Delete all quests
    stmt_quests = delete(Quest).where(Quest.user_id == user_id)
    await db.execute(stmt_quests)

    await db.commit()
    print("[OK] Quest data cleaned up!")


async def seed_rich_profile():
    print("[SEED] Starting Rich Profile Simulation (Registry Fix)...")

    # CRITICAL: Import ALL models involved in relationships with User
    # to ensure SQLAlchemy Registry is complete before mapping.
    from src.app.models.insight import JournalEntry, PromptPhase, PromptStatus, ReflectionPrompt
    from src.app.models.progression import PlayerStats
    from src.app.models.user import User
    from src.app.modules.features.quests.models import (
        Quest,
        QuestCategory,
        QuestDifficulty,
        QuestLog,
        QuestSource,
        QuestStatus,
    )

    # Configure mappers NOW
    configure_mappers()

    async with local_session() as db:
        # 1. Get User
        stmt = select(User).where(User.username.in_(["drof", "testuser"]))
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            print("❌ No user found! Run the app setup first.")
            return

        print(f"[USER] Seeding for user: {user.username} ({user.id})")

        # Clean up old quest data
        await cleanup_quest_data(db, user.id)

        # --- PART 1: 7-DAY MOMENTUM BACKFILL (Direct DB) ---
        print("[HISTORY] Backfilling 7-Day History...")

        q_meditation = await get_or_create_quest(
            db, user.id, Quest, "Morning Meditation", "Start the day with alignment.", QuestCategory.DAILY
        )

        history_entries = []
        total_xp_gain = 0

        for days_ago in range(7, 0, -1):
            date_target = datetime.now(UTC) - timedelta(days=days_ago)

            # Log
            log = QuestLog(
                quest_id=q_meditation.id,
                status=QuestStatus.COMPLETED,
                scheduled_for=date_target,
                completed_at=date_target,
                notes="Felt aligned.",
            )
            db.add(log)

            # XP
            xp_amount = 10
            total_xp_gain += xp_amount

            history_entries.append(
                {
                    "timestamp": date_target.isoformat(),
                    "amount": xp_amount,
                    "reason": "Quest Completed: Morning Meditation",
                    "category": "SYNC",
                    "new_total": total_xp_gain,
                    "level": 1,
                }
            )

        # --- PART 2: COSMIC EVENT (3 Days Ago) ---
        print("[COSMIC] Seeding Cosmic Event...")
        event_date = datetime.now(UTC) - timedelta(days=3)

        prompt = ReflectionPrompt(
            user_id=user.id,
            prompt_text="The Kp Index spiked to 7 today. How did this high-energy impact your focus?",
            topic="Solar Focus Correlation",
            trigger_context={"kp_index": 7, "pattern": "solar_focus"},
            event_phase=PromptPhase.PEAK,
            status=PromptStatus.ANSWERED,
            created_at=event_date,
        )
        db.add(prompt)
        await db.flush()

        entry = JournalEntry(
            user_id=user.id,
            content="Actually felt amazing. I got through my entire backlog. High energy suits me.",
            mood_score=9,
            tags=["focus", "solar", "productive"],
            prompt_id=prompt.id,
            context_snapshot={"kp_index": 7, "moon_phase": "Waxing Gibbous"},
            created_at=event_date,
        )
        db.add(entry)

        # --- PART 3: CURRENT STATE ---
        print("[STATE] Setting Legacy State (Level 12)...")

        stmt = select(PlayerStats).where(PlayerStats.user_id == user.id)
        res = await db.execute(stmt)
        stats = res.scalar_one_or_none()
        if not stats:
            stats = PlayerStats(user_id=user.id)
            db.add(stats)

        TARGET_XP = 1050000  # Corrected from 850k based on Level 12 threshold (1.03M)
        stats.level = 12
        stats.experience_points = TARGET_XP + total_xp_gain
        stats.sync_rate = 0.87
        stats.sync_history = history_entries

        # --- PART 4: PRESENT DAY ---
        await get_or_create_quest(
            db,
            user.id,
            Quest,
            "Deep Work Session",
            "Complete 4 hours of uninterrupted coding.",
            QuestCategory.MISSION,
            QuestDifficulty.HARD,
            tags=["work", "focus"],
            source=QuestSource.AGENT,
        )

        await get_or_create_quest(
            db,
            user.id,
            Quest,
            "Gym: Leg Day",
            "Don't skip it.",
            QuestCategory.DAILY,
            QuestDifficulty.MEDIUM,
            tags=["health"],
        )

        # GET quests we just created and ensure they have pending logs
        print("[LOGS] Creating pending logs for active quests...")
        stmt = select(Quest).where(Quest.user_id == user.id)
        result = await db.execute(stmt)
        quests = result.scalars().all()

        for quest in quests:
            # Create a PENDING log for each quest
            pending_log = QuestLog(
                quest_id=quest.id,
                status=QuestStatus.PENDING,
                scheduled_for=datetime.now(UTC),
            )
            db.add(pending_log)

        await db.commit()
        print("[DONE] Rich Profile Simulation Complete!")
        print(f"   Rank: {stats.rank} (Level {stats.level})")
        print(f"   Sync Rate: {stats.sync_rate}")


async def get_or_create_quest(db, user_id, QuestModel, title, desc, category, dif=None, tags=[], source=None):
    from src.app.modules.features.quests.models import QuestDifficulty, QuestSource

    if dif is None:
        dif = QuestDifficulty.EASY
    if source is None:
        source = QuestSource.USER

    stmt = select(QuestModel).where(QuestModel.user_id == user_id, QuestModel.title == title)
    res = await db.execute(stmt)
    q = res.scalar_one_or_none()

    if not q:
        q = QuestModel(
            user_id=user_id,
            title=title,
            description=desc,
            category=category,
            difficulty=dif,
            tags=",".join(tags),
            source=source,
            is_active=True,
        )
        db.add(q)
        await db.flush()
    return q


if __name__ == "__main__":
    asyncio.run(seed_rich_profile())
