"""
High-Fidelity Integration Tests for Quest System.
Tests the complete quest visibility flow with REAL database and API serialization.

No mocks for core logic. Verifies:
1. Quest creation with proper enum handling
2. Pending log creation (immediate feedback)
3. API serialization (QuestRead validators)
4. Dashboard visibility (view=tasks)
5. Control Room visibility (view=definitions)
"""


import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.quests import QuestRead
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import (
    Quest,
    QuestDifficulty,
    QuestLog,
    QuestSource,
    QuestStatus,
    RecurrenceType,
)


@pytest.mark.asyncio
async def test_quest_creation_with_string_recurrence(db: AsyncSession, test_user):
    """
    Test that QuestManager handles string recurrence from API.
    HIGH FIDELITY: Uses real database, verifies persistent data.
    """
    user_id = test_user.id

    # Create quest with string recurrence (from API)
    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Morning Meditation",
        description="Daily mindfulness practice",
        recurrence="daily",  # String from API, not Enum
        difficulty=1,  # Easy
        tags=["meditation", "daily"],
        source=QuestSource.USER,
    )

    # Verify quest created in database
    stmt = select(Quest).where(Quest.id == quest.id)
    result = await db.execute(stmt)
    db_quest = result.scalar_one()

    assert db_quest.title == "Morning Meditation"
    assert db_quest.recurrence == RecurrenceType.DAILY  # Should be converted to Enum
    assert db_quest.user_id == user_id
    assert db_quest.is_active is True
    assert db_quest.source == QuestSource.USER
    assert db_quest.difficulty == QuestDifficulty.EASY


@pytest.mark.asyncio
async def test_quest_creates_pending_log_immediately(db: AsyncSession, test_user):
    """
    Test that create_quest immediately creates a PENDING log.
    HIGH FIDELITY: Verifies immediate feedback without race conditions.
    """
    user_id = test_user.id

    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Test Quest",
        recurrence="once",
        difficulty=2,  # Medium
        tags=["test"],
        source=QuestSource.USER,
    )

    # Verify pending log exists immediately
    stmt = select(QuestLog).where(QuestLog.quest_id == quest.id).where(QuestLog.status == QuestStatus.PENDING)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()

    assert log is not None, "QuestLog should exist immediately after creation"
    assert log.status == QuestStatus.PENDING
    assert log.quest_id == quest.id


@pytest.mark.asyncio
async def test_get_pending_logs_returns_logs_with_quest(db: AsyncSession, test_user):
    """
    Test that get_pending_logs returns QuestLog with eager-loaded Quest.
    HIGH FIDELITY: Verifies no MissingGreenlet errors in async serialization.
    """
    user_id = test_user.id

    # Create quest
    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Daily Stand-up",
        recurrence="daily",
        difficulty=1,
        tags=["work"],
        source=QuestSource.USER,
    )

    # Get pending logs
    logs = await QuestManager.get_pending_logs(db, user_id)

    assert len(logs) > 0

    # Find the specific log for our quest (may be multiple from other tests)
    log = None
    for l in logs:
        if l.quest_id == quest.id:
            log = l
            break

    assert log is not None, f"Could not find log for quest {quest.id}"

    # Verify log.quest is accessible (no lazy loading issues)
    assert log.quest is not None
    assert log.quest.id == quest.id
    assert log.quest.title == "Daily Stand-up"
    assert log.quest.recurrence == RecurrenceType.DAILY


@pytest.mark.asyncio
async def test_quest_read_serializes_enums_to_lowercase(db: AsyncSession, test_user):
    """
    Test that QuestRead validators properly serialize Enum objects to lowercase strings.
    HIGH FIDELITY: Verifies API response format exactly matches frontend expectations.
    """
    user_id = test_user.id

    # Create quest
    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Study Session",
        recurrence="weekly",
        difficulty=3,  # Hard
        tags=["learning"],
        source=QuestSource.AGENT,
    )

    # Serialize through QuestRead (as the API does)
    quest_read = QuestRead(
        id=quest.id,
        title=quest.title,
        description=quest.description,
        recurrence=quest.recurrence,  # Enum from DB
        cron_expression=quest.cron_expression,
        difficulty=quest.difficulty,  # QuestDifficulty Enum
        tags=quest.tags,
        is_active=quest.is_active,
        source=quest.source,  # QuestSource Enum
        job_id=quest.job_id,
        log_id=None,
        status=None,
    )

    # Verify serialization
    assert isinstance(quest_read.recurrence, str)
    assert quest_read.recurrence == "weekly"

    assert isinstance(quest_read.source, str)
    assert quest_read.source == "agent"

    assert isinstance(quest_read.difficulty, int)
    assert quest_read.difficulty == 3  # Hard = 3


@pytest.mark.asyncio
async def test_get_active_quests_for_control_room(db: AsyncSession, test_user):
    """
    Test that get_active_quests returns user's definitions for Control Room.
    HIGH FIDELITY: Only shows is_active=True quests for the current user.
    """
    user_id = test_user.id

    # Create active and inactive quests
    active_quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Active Quest",
        recurrence="daily",
        difficulty=1,
        tags=["active"],
        source=QuestSource.USER,
    )

    inactive_quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Inactive Quest",
        recurrence="once",
        difficulty=1,
        tags=["inactive"],
        source=QuestSource.USER,
    )

    # Deactivate the second quest
    await QuestManager.update_quest(db, inactive_quest.id, is_active=False)

    # Get active quests
    active = await QuestManager.get_active_quests(db, user_id)

    # Verify only active quests returned
    active_ids = {q.id for q in active}
    assert active_quest.id in active_ids
    assert inactive_quest.id not in active_ids


@pytest.mark.asyncio
async def test_quest_create_accepts_mixed_case_recurrence(db: AsyncSession, test_user):
    """
    Test that recurrence from frontend (mixed case) is normalized.
    """
    user_id = test_user.id

    # Frontend sends "DAILY" (uppercase from form)
    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Test Case",
        recurrence="DAILY",  # Uppercase from form
        difficulty=1,
        tags=[],
        source=QuestSource.USER,
    )

    # Verify stored as correct Enum
    stmt = select(Quest).where(Quest.id == quest.id)
    result = await db.execute(stmt)
    db_quest = result.scalar_one()

    assert db_quest.recurrence == RecurrenceType.DAILY


@pytest.mark.asyncio
async def test_quest_read_difficulty_mapping(db: AsyncSession, test_user):
    """
    Test that QuestRead maps QuestDifficulty Enum to integer 1-4.
    """
    user_id = test_user.id

    for difficulty_int, difficulty_enum in [
        (1, QuestDifficulty.EASY),
        (2, QuestDifficulty.MEDIUM),
        (3, QuestDifficulty.HARD),
        (4, QuestDifficulty.ELITE),
    ]:
        quest = await QuestManager.create_quest(
            db=db,
            user_id=user_id,
            title=f"Test {difficulty_enum.value}",
            recurrence="once",
            difficulty=difficulty_int,
            tags=[],
            source=QuestSource.USER,
        )

        # Serialize
        quest_read = QuestRead(
            id=quest.id,
            title=quest.title,
            recurrence=quest.recurrence,
            difficulty=quest.difficulty,  # Enum from DB
            tags=quest.tags,
            is_active=quest.is_active,
            source=quest.source,
        )

        assert quest_read.difficulty == difficulty_int


@pytest.mark.asyncio
async def test_quest_visibility_isolation_by_user(db: AsyncSession, test_user):
    """
    Test that Quest visibility is isolated per user.
    HIGH FIDELITY: Ensures user1's quest doesn't appear in user2's dashboard.
    """
    # Create second user
    import uuid

    from src.app.core.security import get_password_hash
    from src.app.models.user import User

    unique_id = str(uuid.uuid4())[:8]
    user2 = User(
        name="User Two",
        username=f"testuser2_{unique_id}",
        email=f"test2_{unique_id}@example.com",
        hashed_password=get_password_hash("password123"),
    )
    db.add(user2)
    await db.commit()
    await db.refresh(user2)

    # Create quests for both users
    quest1 = await QuestManager.create_quest(
        db=db,
        user_id=test_user.id,
        title="User1 Quest",
        recurrence="once",
        difficulty=1,
        tags=[],
        source=QuestSource.USER,
    )

    quest2 = await QuestManager.create_quest(
        db=db,
        user_id=user2.id,
        title="User2 Quest",
        recurrence="once",
        difficulty=1,
        tags=[],
        source=QuestSource.USER,
    )

    # Get pending logs for user1
    user1_logs = await QuestManager.get_pending_logs(db, test_user.id)
    user1_quest_ids = {log.quest_id for log in user1_logs}

    # Get pending logs for user2
    user2_logs = await QuestManager.get_pending_logs(db, user2.id)
    user2_quest_ids = {log.quest_id for log in user2_logs}

    # Verify isolation
    assert quest1.id in user1_quest_ids
    assert quest1.id not in user2_quest_ids

    assert quest2.id in user2_quest_ids
    assert quest2.id not in user1_quest_ids


@pytest.mark.asyncio
async def test_quest_update_preserves_enum_types(db: AsyncSession, test_user):
    """
    Test that updating a quest preserves proper Enum types.
    """
    user_id = test_user.id

    quest = await QuestManager.create_quest(
        db=db,
        user_id=user_id,
        title="Original",
        recurrence="once",
        difficulty=1,
        tags=[],
        source=QuestSource.USER,
    )

    # Update with string recurrence
    updated = await QuestManager.update_quest(
        db=db,
        quest_id=quest.id,
        recurrence="daily",  # String
        title="Updated",
    )

    # Verify saved correctly
    assert updated.recurrence == RecurrenceType.DAILY
    assert updated.title == "Updated"

    # Verify in database
    stmt = select(Quest).where(Quest.id == quest.id)
    result = await db.execute(stmt)
    db_quest = result.scalar_one()

    assert db_quest.recurrence == RecurrenceType.DAILY
    assert db_quest.title == "Updated"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
