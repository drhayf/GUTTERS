import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import configure_mappers

from src.app.core.db.database import local_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_evolution_logic():
    print("🧪 Starting Tabula Rasa Evolution Verification...")

    # --- 1. IMPORTS (Complete Registry Fix) ---

    # Insight Models
    from src.app.models.progression import PlayerStats
    from src.app.models.user import User

    # Quest Models
    # Protocol & Engine
    from src.app.modules.intelligence.evolution.engine import get_evolution_engine
    from src.app.protocol import events
    from src.app.protocol.packet import ProgressionPacket

    configure_mappers()

    async with local_session() as db:
        # --- 2. GET USER ---
        stmt = select(User).where(User.username.in_(["drof", "testuser"]))
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            print("❌ No user found.")
            return

        print(f"👤 Testing on user: {user.username} ({user.id})")

        # --- 3. GET STATS ---
        stmt = select(PlayerStats).where(PlayerStats.user_id == user.id)
        res = await db.execute(stmt)
        stats = res.scalar_one_or_none()
        if not stats:
            stats = PlayerStats(user_id=user.id)
            db.add(stats)

        # --- 4. TABULA RASA (WIPE) ---
        print("🧹 Wiping Stats to Level 1...")
        stats.level = 1
        stats.experience_points = 0
        # Don't wipe history entirely, just reset numerical state for level calculation test
        await db.commit()
        await db.refresh(stats)
        print(f"   State: Level {stats.level}, XP {stats.experience_points}")

        # --- 5. INJECT RAW XP (1.05M) ---
        # 1.05M is enough for Level 12 -> 13+ transition if starting from scratch?
        # Level 12 threshold ~1.03M.
        TARGET_XP = 1050000
        stats.experience_points = TARGET_XP
        await db.commit()
        print(f"💉 Injected {TARGET_XP} XP (Raw). Level is still {stats.level}. Engine check pending...")

        # --- 6. TRIGGER EVOLUTION ENGINE ---
        print("⚙️ Triggering Evolution Engine (Power Leveling)...")

        packet = ProgressionPacket(
            user_id=user.id,
            source="legacy_injection",
            event_type=events.PROGRESSION_EXPERIENCE_GAIN,
            payload={
                "amount": 0,  # Zero gain, just trigger check logic
                "reason": "Evolution Verification",
                "category": "SYSTEM",
            },
        )

        from src.app.core.events.bus import get_event_bus

        bus = get_event_bus()
        try:
            await bus.initialize()
            print("✅ EventBus Initialized.")
        except Exception as e:
            print(f"⚠️ EventBus Init Failed: {e}. Mocking publish.")

            # Simple mock if redis fails
            async def mock_publish(*args, **kwargs):
                print(f"   [MOCK BUS] Published: {args[0] if args else 'Event'}")

            bus.publish = mock_publish

        engine = get_evolution_engine()

        # This calling the method directly bypasses the Event Bus but tests the internal logic (which has the new while loop)
        await engine.handle_experience_gain(packet)

        # --- 7. VERIFY RESULT ---
        await db.refresh(stats)
        print("✅ Evolution Check Complete.")
        print(f"   Final Level: {stats.level}")
        print(f"   Rank: {stats.rank}")

        # Expected: Level > 1.
        # 1.05M XP should be Level 12 or 13.
        # Threshold L12 = 1.03M.
        # Threshold L13 = 13 * 1000 * 1.5^12 = 13*1000*129.7 = 1.6M
        # So should be Level 12.

        if stats.level >= 12:
            print("🎉 SUCCESS: User Power Leveled correctly based on XP!")
        else:
            print(f"❌ FAILURE: User stuck at Level {stats.level}.")


if __name__ == "__main__":
    asyncio.run(verify_evolution_logic())
