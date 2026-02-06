from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.events.bus import get_event_bus
from src.app.core.memory.active_memory import get_active_memory
from src.app.core.state.tracker import get_state_tracker
from src.app.models.progression import PlayerStats
from src.app.models.user import User
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import QuestCategory, QuestDifficulty
from src.app.protocol import events


@pytest.mark.asyncio
async def test_progression_engine_high_fidelity(db: AsyncSession, test_user: User):
    """
    High-Fidelity Service Integration Test for the Progression Engine.

    Verifies:
    1. Infrastructure: Real DB, Real Redis (EventBus/Memory).
    2. Logic: Quest -> XP -> Level Up -> Evolution Event.
    3. State: StateTracker correctly identifies progression domain.
    """
    # 1. Initialize Singletons (Standard Mandate)
    bus = get_event_bus()
    await bus.initialize()

    memory = get_active_memory()
    await memory.initialize()

    # Clean slate for test user
    await memory.redis_client.flushdb()

    # 2. Setup PlayerStats
    stmt = select(PlayerStats).where(PlayerStats.user_id == test_user.id)
    stats = (await db.execute(stmt)).scalar_one_or_none()
    if not stats:
        stats = PlayerStats(user_id=test_user.id, level=1, experience_points=0)
        db.add(stats)
        await db.commit()
        await db.refresh(stats)
    else:
        # Reset stats for deterministic test
        stats.level = 1
        stats.experience_points = 0
        stats.sync_rate = 0.0
        await db.commit()
        await db.refresh(stats)

    # 3. Create a Quest
    quest = await QuestManager.create_quest(
        db=db,
        user_id=test_user.id,
        title="Evolution Test Quest",
        description="Verify Quest -> XP flow",
        category=QuestCategory.MISSION,
        difficulty=QuestDifficulty.HARD,  # 50 XP base
    )

    # 4. Create and Complete QuestLog
    log = await QuestManager.create_log(db, quest.id, datetime.now(UTC))

    # Capture event bus emissions
    evolution_events = []

    async def capture_evolution(payload):
        evolution_events.append(payload)

    await bus.subscribe(events.EVOLUTION_LEVEL_UP, capture_evolution)

    # 5. Complete Quest (Should Gain XP)
    # We need to gain enough XP to level up.
    # Level 1 threshold: 1 * 1000 * 1.5^0 = 1000 XP
    # Let's set XP close to threshold to trigger level up with one quest
    stats.experience_points = 960
    await db.commit()

    print(f"[*] Completing quest. Current XP: {stats.experience_points}, Level: {stats.level}")
    await QuestManager.complete_quest(db, log.id)

    # Allow time for EventBus propagation
    import asyncio

    await asyncio.sleep(0.5)

    await db.refresh(stats)
    print(f"[*] After completion. XP: {stats.experience_points}, Level: {stats.level}")

    # 6. Assertions - Core Logic
    assert stats.experience_points >= 1010  # 960 + 50 (no multiplier here as streak is 0)
    assert stats.level == 2

    # 7. Assertions - Event Fidelity
    assert len(evolution_events) == 1
    event = evolution_events[0]
    assert event.payload["old_level"] == 1
    assert event.payload["new_level"] == 2
    assert event.payload["rank"] == "E"
    assert event.user_id == str(test_user.id)
    assert event.payload["activity_trace"]["title"] == "System Evolution"

    # 8. Assertions - StateTracker (Maximum Scrutiny)
    tracker = get_state_tracker()
    status = await tracker.get_profile_state(test_user.id)

    # Level 2, Rank E, and Sync Rate > 0 (if updated)
    # Note: complete_quest doesn't update sync_rate (done in daily_reset)
    # But PlayerStats has rank E for level 2.
    progression_domain = status["domains"]["progression"]
    assert progression_domain["confidence"] >= 0.66  # level and rank filled

    print("[OK] High-Fidelity Progression Integration Test Passed.")
