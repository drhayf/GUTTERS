import asyncio
import logging
from datetime import datetime, UTC
from sqlalchemy import select, func
from unittest.mock import MagicMock, AsyncMock, patch

from src.app.core.db.database import local_session
from src.app.core.events.bus import get_event_bus
from src.app.modules.intelligence.insight.manager import InsightManager
from src.app.modules.infrastructure.push.service import NotificationService
from src.app.models.user_profile import UserProfile
from src.app.models.progression import PlayerStats
from src.app.modules.features.quests.models import QuestLog
from src.app.protocol import events

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SystemAudit")


async def golden_thread_check():
    """
    Verify the path: COSMIC_UPDATE -> InsightManager -> NotificationRouter
    """
    print("\n[AUDIT] === Golden Thread Check ===")

    # 1. Mock dependencies
    # We want to verify InsightManager reacts to cosmic_update and creates a prompt
    # triggering notification using NotificationService.

    # Mock NotificationService to avoid actual push but verify call
    mock_notify_service = AsyncMock(spec=NotificationService)

    # Instantiate Manager with mocked service
    # We need to monkeypatch the notify service instance inside the class or instance we use

    insight_manager = InsightManager()
    insight_manager.notification_service = mock_notify_service

    # Mock DB (Real DB connection is preferred for schema check but for logic flow we can mock
    # OR we use real DB and rollback. Let's use real DB for comprehensive test but handle cleanup.)
    # Actually, let's use a real DB session to verify constraints, but we might pollute data.
    # We will use 'dry-run' via rollback at end or just verify reading.

    # Since we can't easily intercept the event bus in a script without recreating the app context,
    # we will test the InsightManager method directly with a simulated payload.

    user_id = 1  # Assuming default seeded user exists

    # Simulated High Activity Payload
    cosmic_data = {
        "kp_index": 8,  # Storm
        "moon_phase": "Full Moon",
        "moon_event_type": "peak",
    }

    async with local_session() as db:
        target_user_id = 78
        print(f"[INFO] Targeted Audit for User ID {target_user_id}...")

        # Fetch UserProfile by user_id (FK), not PK
        stmt = select(UserProfile).where(UserProfile.user_id == target_user_id)
        result = await db.execute(stmt)
        user_profile = result.scalar_one_or_none()

        if not user_profile:
            print(f"[FAIL] UserProfile for User {target_user_id} not found.")
            # Fallback to finding ANY user if 78 is missing
            print("[INFO] Falling back to first available user...")
            result = await db.execute(select(UserProfile))
            user_profile = result.scalars().first()
            if not user_profile:
                print("[FAIL] No users found in DB. Seed data missing?")
                return
            target_user_id = user_profile.user_id
            print(f"[INFO] Using Fallback User ID {target_user_id}")

        print(f"[INFO] Found UserProfile for User {target_user_id}. Proceeding with Golden Thread.")

        # We don't need to re-fetch user if we have profile, but let's keep consistent
        user_id = target_user_id

        print("[INFO] Simulating COSMIC_UPDATE (Kp=8, Full Moon)...")

        # We need to trick the manager into finding 'patterns' or bypassing pattern check
        # Since pattern finding relies on ObserverFindingStorage and real DB data,
        # we might need to mock the observer storage return values

        mock_findings = [
            {"finding": "User sleeps poorly during storms", "confidence": 0.85, "pattern_type": "solar_sensitivity"},
            {
                "finding": "User has high energy during Full Moon",
                "confidence": 0.7,
                "pattern_type": "lunar_phase",
                "phase": "Full Moon",
            },
        ]

        insight_manager.observer_storage = AsyncMock()
        insight_manager.observer_storage.get_findings.return_value = mock_findings

        # We also need to bypass cooldown check
        insight_manager._should_trigger = AsyncMock(return_value=True)

        # Mock LLM to avoid API costs and determinism
        insight_manager.llm = AsyncMock()
        insight_manager.llm.ainvoke.return_value = MagicMock(content="Reflection: How does the storm affect your rest?")

        # Mock event emission to avoid bus errors in script
        insight_manager._emit_prompt_event = AsyncMock()

        # ACT: Evaluate Triggers
        prompts = await insight_manager.evaluate_cosmic_triggers(user_id, cosmic_data, db)

        # ASSERT
        if prompts:
            print(f"[PASS] InsightManager generated {len(prompts)} prompts from cosmic triggers.")
            print(f"[INFO] Prompt 1 Topic: {prompts[0].topic}")

            # Verify Notification Service called
            # call_args for send_notification: user_id, title, body, data, db
            if mock_notify_service.send_notification.called:
                print("[PASS] NotificationService.send_notification was called.")
                args = mock_notify_service.send_notification.call_args
                print(f"[INFO] Notification Title: {args.kwargs.get('title')}")
            else:
                print("[FAIL] NotificationService was NOT called.")

            # Verify Event Emission call
            if insight_manager._emit_prompt_event.called:
                print("[PASS] REFLECTION_PROMPT_GENERATED event emission attempted.")
            else:
                print("[FAIL] Event emission NOT attempted.")

        else:
            print("[FAIL] No prompts generated. Check logic or mock data.")


async def data_integrity_check():
    """
    Verify DB State: UserProfile, Stats, QuestLogs
    """
    print("\n[AUDIT] === Data Integrity Check ===")
    async with local_session() as db:
        # Check UserProfile Preferences
        result = await db.execute(select(UserProfile))
        profiles = result.scalars().all()
        target_user_id = None

        for p in profiles:
            prefs = p.data.get("preferences", {})
            has_notifs = "notifications" in prefs
            # print(f"[CHECK] User {p.user_id}: Has Preferences? {has_notifs}")
            if not has_notifs:
                print(f"[WARN] User {p.user_id} missing notification preferences structure.")

            # Just grab the last one for detailed check
            target_user_id = p.user_id

        # Check PlayerStats
        # stats_result = await db.execute(select(PlayerStats))
        # stats = stats_result.scalars().all()
        # for s in stats:
        #    print(f"[CHECK] User {s.user_id}: Rank {s.rank} (Lvl {s.level})")

        from src.app.modules.features.quests.models import Quest, QuestLog, QuestStatus

        # 1. System-Wide Checks
        total_active_defs = await db.scalar(select(func.count(Quest.id)).where(Quest.is_active.is_(True)))
        print(f"[CHECK] SYSTEM TOTAL: Active Quest Definitions (Blueprints): {total_active_defs}")

        # 2. User-Specific Checks (Focusing on the user found in Golden Thread or last user)
        if target_user_id:
            print(f"\n[ANALYSIS] Breakdown for User {target_user_id}:")

            # Active Definitions (The "Subscriptions")
            user_defs_stmt = select(func.count(Quest.id)).where(
                Quest.user_id == target_user_id, Quest.is_active.is_(True)
            )
            user_active_defs = await db.scalar(user_defs_stmt)
            print(f"  > Active Configured Quests: {user_active_defs}")

            # Pending Logs (The "To-Do List" for today)
            user_logs_stmt = (
                select(func.count(QuestLog.id))
                .join(Quest)
                .where(Quest.user_id == target_user_id, QuestLog.status == QuestStatus.PENDING)
            )
            user_pending_logs = await db.scalar(user_logs_stmt)
            print(f"  > Pending Quest Logs (Action Items): {user_pending_logs}")

            if user_active_defs > 0 and user_pending_logs == 0:
                print("  [NOTE] You have active quest definitions but no pending logs. Did daily reset run?")
            elif user_pending_logs > user_active_defs:
                print("  [NOTE] You have more pending logs than definitions (backlog piled up).")

        # Check for detached jobs
        # result = await db.execute(select(Quest).where(Quest.is_active == True))
        # quests = result.scalars().all()
        # active_jobs = [q for q in quests if q.job_id]
        # if len(quests) > 0 and len(active_jobs) == 0:
        #      print("[WARN] Active quests exist but NONE have job_ids. Scheduler might be down.")
        # elif len(active_jobs) > 0:
        #      print(f"[PASS] Scheduler is active ({len(active_jobs)}/{len(quests)} quests have Job IDs).")


async def main():
    print("Starting Final System Audit...")
    try:
        await golden_thread_check()
        await data_integrity_check()
    except Exception as e:
        print(f"[ERROR] Audit Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
