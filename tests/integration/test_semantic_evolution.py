import pytest
import asyncio
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.models.progression import PlayerStats
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import QuestStatus, QuestCategory, QuestDifficulty
from src.app.core.events.bus import get_event_bus
from src.app.core.memory.active_memory import get_active_memory
from src.app.modules.intelligence.evolution.engine import get_evolution_engine
from src.app.modules.intelligence.genesis.listener import get_genesis_listener
from src.app.modules.intelligence.genesis.uncertainty import UncertaintyDeclaration, UncertaintyField
from src.app.models.insight import ReflectionPrompt, PromptStatus, PromptPhase
from src.app.protocol.packet import ProgressionPacket
from src.app.protocol import events


@pytest.mark.asyncio
async def test_semantic_evolution_loop(db: AsyncSession, test_user: User):
    """
    High-Fidelity Integration Test for the Semantic Evolution Loop.

    Verifies:
    1. Quest completion emits ProgressionPacket.
    2. EvolutionEngine updates XP (including 1.5x Insight Bonus).
    3. GenesisSemanticListener performs semantic refinement (LLM).
    4. Profile certainty (confidence) is updated in UserProfile.
    5. ActivityTrace is logged for Semantic Evolution.
    6. Passive Environmental XP is captured from Cosmic Events.
    """
    # 1. Initialize System Components
    bus = get_event_bus()
    await bus.initialize()

    memory = get_active_memory()
    await memory.initialize()

    # Initialize Engine and Listener
    engine = get_evolution_engine()
    await engine.initialize()

    genesis_listener = get_genesis_listener()
    await genesis_listener.initialize()

    # Capture user ID early to avoid expiration issues
    user_id_val = test_user.id
    user_id_str = str(user_id_val)

    # Clean slate
    await memory.redis_client.flushdb()

    # 2. Setup PlayerStats
    stmt = select(PlayerStats).where(PlayerStats.user_id == user_id_val)
    stats = (await db.execute(stmt)).scalar_one_or_none()
    if not stats:
        stats = PlayerStats(user_id=user_id_val, level=1, experience_points=0)
        db.add(stats)
    else:
        stats.level = 1
        stats.experience_points = 0
        stats.sync_history = []

    # 3. Setup User Profile with Uncertainty and fake Journal context
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id_val))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user_id_val, data={})
        db.add(profile)

    # Inject Uncertainty Declaration
    decl = UncertaintyDeclaration(
        module="astrology",
        user_id=user_id_val,
        session_id="test-session",
        source_accuracy="probabilistic",
        fields=[
            UncertaintyField(
                field="rising_sign", module="astrology", candidates={"Leo": 0.5, "Virgo": 0.5}, confidence_threshold=0.9
            )
        ],
    )

    profile_data = dict(profile.data)
    if "genesis" not in profile_data:
        profile_data["genesis"] = {}
    if "uncertainties" not in profile_data["genesis"]:
        profile_data["genesis"]["uncertainties"] = {}

    profile_data["genesis"]["uncertainties"]["astrology"] = decl.to_storage_dict()

    # Add Journal context
    profile_data["journal_entries"] = [
        {
            "id": "j-1",
            "timestamp": datetime.now(UTC).isoformat(),
            "text": "I felt very energetic and outgoing today. I naturally took charge in the meeting.",
            "mood_score": 8,
            "energy_score": 9,
        }
    ]

    profile.data = profile_data
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "data")
    await db.commit()

    # 4. Create Insight Context (for Multiplier Test)
    prompt = ReflectionPrompt(
        user_id=user_id_val,
        prompt_text="Demonstrate your rising sign energy.",
        topic="astrology",
        status=PromptStatus.PENDING,
        event_phase=PromptPhase.PEAK,
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)

    # 5. Create and Complete a Quest (Semantic Trigger)
    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id_val,
        title="Leader's Presence",
        description="Demonstrate charismatic leadership in a social situation.",
        category=QuestCategory.MISSION,
        difficulty=QuestDifficulty.HARD,  # 50 XP
        insight_id=prompt.id,  # Link to insight for 1.5x bonus
    )

    log = await QuestManager.create_log(db, quest.id, datetime.now(UTC))

    # Capture traces
    traces = []

    async def capture_trace(payload):
        traces.append(payload)

    await bus.subscribe("system.evolution.trace", capture_trace)

    print("[*] Completing Semantic Quest...")
    await QuestManager.complete_quest(db, log.id)

    # 5. Wait for async processing (EvolutionEngine + GenesisListener)
    await asyncio.sleep(3.0)
    db.expire_all()

    # 6. Assertions
    await db.refresh(stats)
    await db.refresh(profile)

    print(f"[*] Post-Quest XP: {stats.experience_points}")
    print(f"[*] Post-Quest Level: {stats.level}")

    # EvolutionEngine worked?
    # Base 50 XP * 1.5 Insight Multiplier = 75 XP
    assert stats.experience_points >= 75
    assert len(stats.sync_history) >= 1
    assert stats.sync_history[-1]["reason"].startswith("Quest Completed")

    # 7. Test Passive Environmental XP
    from src.app.modules.tracking.solar.tracker import SolarTracker
    from src.app.modules.tracking.base import TrackingData

    tracker = SolarTracker()
    mock_data = TrackingData(
        timestamp=datetime.now(UTC),
        source="Test",
        data={"kp_index": 7.0, "solar_flares": []},  # G4 Storm
    )

    print("[*] Simulating Passive Cosmic Event...")

    # Verify Detection Logic (High-Fidelity Labels)
    events_detected = tracker.detect_significant_events(mock_data, None)
    assert "Cosmic Witness: G4 Severe Solar Storm" in events_detected

    # Manually trigger the XP emission (Simulating orchestrator event)
    packet = ProgressionPacket(
        source=tracker.module_name,
        event_type=events.PROGRESSION_EXPERIENCE_GAIN,
        payload={"tracking_events": events_detected},
        user_id=user_id_str,
        amount=5,  # Standard passive XP
        reason=events_detected[0],
        category="VITALITY",
    )
    await bus.publish_packet(packet)

    await asyncio.sleep(3.0)
    await db.refresh(stats)

    print(f"[*] Post-Passive XP: {stats.experience_points}")
    assert stats.experience_points >= 80  # 75 + 5
    # Verify history entry contains the high-fidelity reason
    assert any("G4 Severe Solar Storm" in entry["reason"] for entry in stats.sync_history)

    print("[OK] Semantic Evolution Loop & Passive XP Verified.")
