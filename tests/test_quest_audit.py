"""
Quest System Audit Test.
Shows EVERY quest in the database with complete validation.
Confirms all metadata is correct for frontend consumption.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import (
    Quest,
    QuestLog,
    QuestStatus,
    RecurrenceType,
    QuestSource,
    QuestDifficulty,
)
from src.app.api.v1.quests import QuestRead


@pytest.mark.asyncio
async def test_audit_all_quests_in_system(db: AsyncSession, test_user):
    """
    AUDIT TEST: List all quests in database with complete metadata validation.
    Confirms every quest can be properly serialized for frontend components.
    """
    # 1. Get ALL quests in system
    print("\n" + "=" * 100)
    print("QUEST SYSTEM AUDIT - ALL QUESTS IN DATABASE")
    print("=" * 100)

    result = await db.execute(select(Quest))
    all_quests = result.scalars().all()

    print(f"\n[STAT] Total Quests in Database: {len(all_quests)}")

    if len(all_quests) == 0:
        print("[WARN] No quests found. Creating sample quests for audit...")

        # Create sample quests for both users
        for i in range(3):
            quest = await QuestManager.create_quest(
                db=db,
                user_id=test_user.id,
                title=f"Sample Quest {i + 1}",
                description=f"Test quest for audit {i + 1}",
                recurrence=["daily", "weekly", "once"][i],
                difficulty=(i % 4) + 1,
                tags=[f"audit", f"sample{i}"],
                source=QuestSource.USER,
            )

        # Reload quests
        result = await db.execute(select(Quest))
        all_quests = result.scalars().all()
        print(f"[SUCCESS] Created {len(all_quests)} sample quests")

    # 2. Audit each quest
    print(f"\n[REPORT] QUEST AUDIT REPORT")
    print("-" * 100)

    for idx, quest in enumerate(all_quests, 1):
        print(f"\n[Quest #{idx}] ID: {quest.id}")
        print(f"  Title: {quest.title}")
        print(f"  User ID: {quest.user_id} (Owner)")
        print(f"  Active: {quest.is_active}")

        # Validate recurrence
        print(f"  Recurrence:")
        print(f"    • Value: {quest.recurrence}")
        print(f"    • Type: {type(quest.recurrence).__name__}")
        assert isinstance(quest.recurrence, (RecurrenceType, str)), (
            f"Recurrence should be Enum or str, got {type(quest.recurrence)}"
        )
        if isinstance(quest.recurrence, RecurrenceType):
            assert hasattr(quest.recurrence, "value"), "Recurrence Enum should have .value"
            print(f"    • Enum Value: {quest.recurrence.value}")
            print(f"    [VALID] RecurrenceType")

        # Validate difficulty
        print(f"  Difficulty:")
        print(f"    • Value: {quest.difficulty}")
        print(f"    • Type: {type(quest.difficulty).__name__}")
        assert isinstance(quest.difficulty, (QuestDifficulty, str)), f"Difficulty should be Enum or str"
        if isinstance(quest.difficulty, QuestDifficulty):
            print(f"    • Enum Value: {quest.difficulty.value}")
            print(f"    ✓ Valid QuestDifficulty")

        # Validate source
        print(f"  Source:")
        print(f"    • Value: {quest.source}")
        print(f"    • Type: {type(quest.source).__name__}")
        assert isinstance(quest.source, (QuestSource, str)), f"Source should be Enum or str"
        if isinstance(quest.source, QuestSource):
            print(f"    • Enum Value: {quest.source.value}")
            print(f"    ✓ Valid QuestSource")

        # Test serialization through QuestRead (API layer)
        print(f"  \n  API Serialization Test:")
        try:
            quest_read = QuestRead(
                id=quest.id,
                title=quest.title,
                description=quest.description,
                recurrence=quest.recurrence,
                cron_expression=quest.cron_expression,
                difficulty=quest.difficulty,
                tags=quest.tags,
                is_active=quest.is_active,
                source=quest.source,
                job_id=quest.job_id,
                log_id=None,
                status=None,
            )

            api_response = quest_read.model_dump()

            # Validate frontend-compatible format
            assert isinstance(api_response["recurrence"], str), "Recurrence should serialize to string"
            assert api_response["recurrence"].islower(), (
                f"Recurrence should be lowercase, got {api_response['recurrence']}"
            )
            print(f"    ✓ recurrence: '{api_response['recurrence']}' (string, lowercase)")

            assert isinstance(api_response["source"], str), "Source should serialize to string"
            assert api_response["source"].islower(), f"Source should be lowercase, got {api_response['source']}"
            print(f"    ✓ source: '{api_response['source']}' (string, lowercase)")

            assert isinstance(api_response["difficulty"], int), "Difficulty should serialize to int"
            assert 1 <= api_response["difficulty"] <= 4, f"Difficulty should be 1-4, got {api_response['difficulty']}"
            difficulty_names = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Elite"}
            print(
                f"    ✓ difficulty: {api_response['difficulty']} ({difficulty_names.get(api_response['difficulty'], 'Unknown')})"
            )

            print(f"    [OK] API Response Format: VALID FOR FRONTEND")

        except Exception as e:
            print(f"    [ERROR] {e}")
            raise

        # Check associated logs
        result = await db.execute(select(QuestLog).where(QuestLog.quest_id == quest.id))
        logs = result.scalars().all()
        print(f"\n  Associated Logs: {len(logs)}")
        for log in logs[:3]:
            print(f"    - Log #{log.id}: status={log.status}")
        if len(logs) > 3:
            print(f"    ... and {len(logs) - 3} more")

    # 3. Group by user and summarize
    print(f"\n" + "-" * 100)
    print("[SUMMARY] BY USER")
    print("-" * 100)

    quests_by_user = {}
    for quest in all_quests:
        if quest.user_id not in quests_by_user:
            quests_by_user[quest.user_id] = []
        quests_by_user[quest.user_id].append(quest)

    for user_id, quests in sorted(quests_by_user.items()):
        active_count = sum(1 for q in quests if q.is_active)
        print(f"\n[USER] User #{user_id}:")
        print(f"   Total quests: {len(quests)}")
        print(f"   Active: {active_count}")
        print(f"   Inactive: {len(quests) - active_count}")

    # 4. Test API View Filtering (Dashboard vs Control Room)
    print(f"\n" + "-" * 100)
    print("[API] VIEW FILTERING TEST")
    print("-" * 100)

    test_user_id = test_user.id

    # Dashboard view: pending logs only
    print(f"\n[DASH] Dashboard View (view=tasks) - User #{test_user_id}:")
    pending_logs = await QuestManager.get_pending_logs(db, test_user_id)
    print(f"   Pending logs: {len(pending_logs)}")

    for log in pending_logs[:5]:
        print(f"   - Log #{log.id} -> Quest #{log.quest_id}: {log.quest.title}")
        assert log.quest is not None, "Quest should be eager-loaded"

    # Control Room view: active definitions
    print(f"\n[CTRL] Control Room View (view=definitions) - User #{test_user_id}:")
    active_quests = await QuestManager.get_active_quests(db, test_user_id)
    print(f"   Active quests: {len(active_quests)}")

    for quest in active_quests[:5]:
        print(f"   - Quest #{quest.id}: {quest.title} (recurrence={quest.recurrence}, source={quest.source})")

    # 5. Final validation
    print(f"\n" + "=" * 100)
    print("[OK] AUDIT COMPLETE: All quests validated")
    print("[OK] All serialization formats correct for frontend")
    print("[OK] All metadata present and valid")
    print("=" * 100)

    assert len(all_quests) > 0, "Should have at least one quest"
