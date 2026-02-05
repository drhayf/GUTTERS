import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import RecurrenceType, QuestStatus, Quest, QuestSource
from src.app.modules.intelligence.tools.library.quests import (
    get_create_quest_tool,
    get_list_quests_tool,
    get_complete_quest_tool,
)
from src.app.modules.infrastructure.push.service import notification_service
from src.app.models.push import PushSubscription

# Fixtures are assumed from conftest.py (db, test_user)


@pytest.mark.asyncio
async def test_quest_lifecycle_with_source(db: AsyncSession, test_user):
    # Mock Redis pool for ARQ
    with patch("src.app.modules.features.quests.manager.create_pool") as mock_create_pool:
        mock_redis = MagicMock()

        async def get_redis(*args, **kwargs):
            return mock_redis

        mock_create_pool.side_effect = get_redis

        async def async_enqueue(*args, **kwargs):
            return "job-123"

        mock_redis.enqueue_job.side_effect = async_enqueue

        async def async_close():
            pass

        mock_redis.close.side_effect = async_close

        # 1. Create Quest (User Source)
        quest = await QuestManager.create_quest(
            db=db, user_id=test_user.id, title="User Quest", recurrence=RecurrenceType.ONCE, source=QuestSource.USER
        )
        assert quest.source == QuestSource.USER
        assert quest.job_id == "job-123"

        # 2. Update Quest (Change Recurrence -> Cancel Job -> New Job)
        # Mock Job abort
        mock_job_abort = AsyncMock()
        with patch("src.app.modules.features.quests.manager.Job") as mock_job_cls:
            mock_job_cls.return_value.abort = mock_job_abort

            updated_quest = await QuestManager.update_quest(db=db, quest_id=quest.id, recurrence=RecurrenceType.DAILY)

            assert updated_quest.recurrence == RecurrenceType.DAILY
            # Verify abort called (for old job "job-123")
            # Note: logic calls _cancel_job which instantiates Job(job_id) and calls abort()
            assert mock_job_cls.called

            # Verify enqueue called again (for new job) - enqueue_job mock should have been called twice total
            assert mock_redis.enqueue_job.call_count == 2

        # 3. Delete Quest
        with patch("src.app.modules.features.quests.manager.Job") as mock_job_cls:
            mock_job_cls.return_value.abort = mock_job_abort
            await QuestManager.delete_quest(db, quest.id)
            # Should be gone
            stmt = select(Quest).where(Quest.id == quest.id)
            res = await db.execute(stmt)
            assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_quest_tool_agent_source(db: AsyncSession, test_user):
    with patch("src.app.modules.features.quests.manager.create_pool") as mock_create_pool:
        mock_redis = MagicMock()

        async def get_redis(*args, **kwargs):
            return mock_redis

        mock_create_pool.side_effect = get_redis

        async def async_enqueue(*args, **kwargs):
            return "job-123"

        mock_redis.enqueue_job.side_effect = async_enqueue

        async def async_close():
            pass

        mock_redis.close.side_effect = async_close

        create_tool = get_create_quest_tool(test_user.id, db)

        # 1. Create via Tool (Should be Agent Source)
        # Tool input doesn't accept source, so it defaults to Agent inside the function
        result = await create_tool.ainvoke({"title": "Agent Directed Quest", "recurrence": "daily"})
        assert "created successfully" in result

        # Verify DB
        stmt = select(Quest).where(Quest.title == "Agent Directed Quest")
        res = await db.execute(stmt)
        quest = res.scalar_one()
        assert quest.source == QuestSource.AGENT


@pytest.mark.asyncio
async def test_push_notification_service(db: AsyncSession, test_user):
    # Setup Subscription
    sub = PushSubscription(
        user_id=test_user.id, endpoint="https://fcm.googleapis.com/fcm/send/test", p256dh="test_key", auth="test_auth"
    )
    db.add(sub)
    await db.commit()

    # Mock pywebpush
    with patch("src.app.modules.infrastructure.push.service.webpush") as mock_webpush:
        res = await notification_service.send_to_user(db=db, user_id=test_user.id, title="Test", body="Body")
        # Verify logic
        # We might have other users/subs from other tests if DB not isolated perfectly (though pytest-asyncio usually handles this).
        # Let's just assert our mocked call happened at least once.
        assert mock_webpush.called
        assert res["success"] >= 1
