import pytest
import pytest_asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.app.models.insight import ReflectionPrompt, JournalEntry, PromptPhase, PromptStatus
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.insight.manager import InsightManager
from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
from src.app.modules.intelligence.tools.library.journal import get_tool as get_journal_tool


# Mocks
class MockLLM:
    async def ainvoke(self, messages):
        class Response:
            content = "This is a mocked reflection question based on high KP."

        return Response()


class MockNotificationService:
    def __init__(self):
        self.sent = []

    async def send_notification(self, user_id, title, body, data, db):
        self.sent.append({"user_id": user_id, "title": title, "body": body, "data": data})


@pytest.fixture
def mock_managers(monkeypatch):
    """Mock LLM and Notification Service."""
    mock_llm = MockLLM()
    mock_notify = MockNotificationService()

    # Patch get_premium_llm in manager
    monkeypatch.setattr("src.app.modules.intelligence.insight.manager.get_premium_llm", lambda: mock_llm)

    return mock_notify


@pytest_asyncio.fixture
async def ensure_profile(db: AsyncSession, test_user):
    """Ensure UserProfile exists for the test_user."""
    stmt = select(UserProfile).where(UserProfile.user_id == test_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        try:
            profile = UserProfile(user_id=test_user.id, data={})
            db.add(profile)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Race condition, assume created

    return test_user


@pytest_asyncio.fixture
async def cleanup_insight_data(db: AsyncSession):
    """Cleanup data before/after tests."""
    await db.execute(delete(JournalEntry))
    await db.execute(delete(ReflectionPrompt))
    await db.commit()
    yield
    await db.execute(delete(JournalEntry))
    await db.execute(delete(ReflectionPrompt))
    await db.commit()


@pytest.mark.asyncio
async def test_insight_flow_solar_peak(db: AsyncSession, cleanup_insight_data, mock_managers, ensure_profile):
    """
    Test Phase 11 Flow:
    1. Seed Observer Pattern (Solar Sensitivity)
    2. Simulate COSMIC_UPDATE (Kp=8) -> Trigger PEAK phase
    3. Verify ReflectionPrompt created
    4. Verify Notification sent
    5. Verify Journal Entry creation with Prompt Link
    """
    user_id = ensure_profile.id

    # Setup Manager with mocked notification
    manager = InsightManager()
    manager.notification_service = mock_managers

    # 1. Seed Observer Pattern
    storage = ObserverFindingStorage()
    await storage.store_finding(
        user_id,
        {
            "pattern_type": "solar_symptom",
            "symptom": "fatigue",
            "correlation": 0.85,
            "confidence": 0.9,
            "finding": "User reports fatigue when Kp > 5",
        },
        db,
    )

    # 2. Simulate Trigger (PEAK Phase)
    cosmic_data = {
        "kp_index": 8,
        "moon_phase": "Waxing",
    }

    prompts = await manager.evaluate_cosmic_triggers(user_id, cosmic_data, db)

    assert len(prompts) == 1
    prompt = prompts[0]

    assert prompt.user_id == user_id
    assert prompt.topic == "solar_sensitivity"
    assert prompt.event_phase == PromptPhase.PEAK
    assert prompt.status == PromptStatus.PENDING
    assert prompt.trigger_context["value"] == 8.0

    # 3. Verify Notification
    assert len(mock_managers.sent) == 1
    notif = mock_managers.sent[0]
    assert "Cosmic Reflection (Peak)" in notif["title"]
    assert str(prompt.id) in notif["data"]["url"]

    # 4. Anti-Spam Check
    # Trigger again immediately
    prompts_2 = await manager.evaluate_cosmic_triggers(user_id, cosmic_data, db)
    assert len(prompts_2) == 0  # Should be blocked by 18h cooldown

    # 5. Log Journal Entry via Tool (Answering the prompt)
    tool = get_journal_tool(user_id, db)
    result = await tool.coroutine(content="I am indeed feeling very tired today.", mood_score=4, prompt_id=prompt.id)

    assert result["status"] == "success"
    entry_id = result["entry_id"]

    # Verify DB Linkage
    stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
    res = await db.execute(stmt)
    entry = res.scalar_one()

    assert entry.prompt_id == prompt.id
    assert entry.context_snapshot["value"] == 8.0  # Context copied from prompt

    # Verify Prompt Status Updated
    await db.refresh(prompt)
    assert prompt.status == PromptStatus.ANSWERED


@pytest.mark.asyncio
async def test_insight_lunar_anticipation(db: AsyncSession, cleanup_insight_data, mock_managers, ensure_profile):
    """Test Predictive Trigger for Lunar Anticipation."""
    user_id = ensure_profile.id
    manager = InsightManager()
    manager.notification_service = mock_managers

    storage = ObserverFindingStorage()
    await storage.store_finding(
        user_id,
        {
            "pattern_type": "lunar_phase",
            "phase": "Full",
            "finding": "User gets anxious during Full Moon",
            "confidence": 0.9,
        },
        db,
    )

    # Simulate Predictive Trigger (24h before Full Moon)
    cosmic_data = {
        "moon_event_type": "anticipation",
        "moon_phase_name": "Full",  # Approaching Full
        "time_until": 24,
    }

    prompts = await manager.evaluate_cosmic_triggers(user_id, cosmic_data, db)

    assert len(prompts) == 1
    prompt = prompts[0]
    assert prompt.event_phase == PromptPhase.ANTICIPATION
    assert prompt.topic == "lunar_pattern"

    # Verify Notification Title
    assert "Cosmic Reflection (Anticipation)" in mock_managers.sent[0]["title"]
