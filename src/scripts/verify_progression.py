import asyncio
import math
from datetime import datetime, UTC
from sqlalchemy import select
from src.app.core.db.database import local_session
from src.app.models import User, PlayerStats, Quest, QuestLog
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import QuestDifficulty, QuestCategory, QuestStatus


async def verify_progression():
    print("[*] Starting Phase 12 Progression Verification...")

    async with local_session() as db:
        # 1. Fetch test user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("[!] No user found for testing. Please ensure database is seeded.")
            return

        print(f"[*] Testing with User ID: {user.id}")

        # 2. Verify PlayerStats Initialization
        stats_stmt = select(PlayerStats).where(PlayerStats.user_id == user.id)
        stats = (await db.execute(stats_stmt)).scalar_one_or_none()

        if not stats:
            print("[*] Initializing PlayerStats...")
            stats = PlayerStats(user_id=user.id)
            db.add(stats)
            await db.commit()
            await db.refresh(stats)

        initial_xp = stats.experience_points
        initial_level = stats.level
        print(f"[*] Initial State: Level {initial_level}, XP {initial_xp}, Rank {stats.rank}")

        # 3. Test Quest Creation & XP Reward
        print("[*] Creating test Daily Quest (HARD)...")
        quest = await QuestManager.create_quest(
            db=db,
            user_id=user.id,
            title="Verification Quest",
            description="Testing XP Rewards",
            category=QuestCategory.DAILY,
            difficulty=QuestDifficulty.HARD,
        )
        print(f"[*] Quest created: XP Base Reward = {quest.xp_reward}")

        # Create log
        log = QuestLog(quest_id=quest.id, status=QuestStatus.PENDING, scheduled_for=datetime.now(UTC))
        db.add(log)
        await db.commit()
        await db.refresh(log)

        # 4. Test Completion & XP Multipliers
        stats.streak_count = 10
        await db.commit()

        print("[*] Completing Quest (Should have 1.2x streak multiplier)...")
        # Note: QuestManager.complete_quest handles commit
        await QuestManager.complete_quest(db, log.id)

        await db.refresh(stats)
        xp_gain = stats.experience_points - initial_xp
        expected_xp = int(50 * 1.2)  # Hard=50, Streak=1.2

        print(f"[*] XP Gained: {xp_gain} (Expected: {expected_xp})")
        if xp_gain == expected_xp:
            print("[OK] XP Calculation with multiplier passed.")
        else:
            print(f"[FAIL] XP calculation mismatch! {xp_gain} != {expected_xp}")

        # 5. Check Rank Logic
        print(f"[*] Current Rank: {stats.rank}")

        # 6. Cleanup
        await db.delete(log)
        await db.delete(quest)
        await db.commit()
        print("[*] Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(verify_progression())
