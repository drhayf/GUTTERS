import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select
from src.app.modules.features.chat.master_chat import MasterChatHandler
from src.app.modules.features.journal.system_journal import SystemJournalist
from src.app.modules.features.quests.manager import QuestManager
from src.app.models.chat_session import ChatSession, ChatMessage
from src.app.protocol.packet import ProgressionPacket
from src.app.modules.features.quests.models import Quest
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class ToolExecutionMock:
    tool: str
    operation: str
    input_params: dict
    result_summary: str
    latency_ms: int = 0


@dataclass
class TraceMock:
    thinking_steps: list
    tools_used: List[ToolExecutionMock]

    def model_dump(self, mode=None):
        return {"thinking_steps": self.thinking_steps, "tools_used": [t.__dict__ for t in self.tools_used]}


@dataclass
class QueryResponseMock:
    answer: str
    trace: Optional[TraceMock]
    context_used: list
    modules_consulted: list = None
    confidence: float = 1.0
    sources_used: list = None
    component: Any = None


@pytest.mark.asyncio
async def test_phase16_model_switcher_wiring(db, test_user, memory):
    """
    Verify that passing 'model_tier' to send_message correclty propagates
    to the stored message metadata, fulfilling the Model Switcher requirement.
    """
    handler = MasterChatHandler(memory)
    # Mock the QueryEngine to avoid real LLM calls, but we want to verify the wiring.
    # MasterChatHandler logic: if tier differs, it creates a NEW QueryEngine.
    # We'll just mock the answer_query return to ensure flow completes.
    mock_response = QueryResponseMock(answer="I am a premium model.", trace=None, context_used=[])

    # Mock QueryEngine with expected attributes
    # MasterChatHandler expects a QueryEngine instance with .tier and .memory attributes
    mock_engine = MagicMock()
    mock_engine.tier = "standard"  # From src.app.core.llm.config.LLMTier.STANDARD
    mock_engine.memory = memory
    mock_engine.answer_query = AsyncMock(return_value=mock_response)

    handler = MasterChatHandler(query_engine=mock_engine)

    # CASE 1: Standard Tier (Default)
    await handler.send_message(test_user.id, "Hello Standard", db, model_tier="standard")

    # CASE 2: Premium Tier
    # When tier='premium', simple flow normally creates a new engine instance.
    # We need to ensure that dynamic creation also returns our mock or handles gracefully.
    # Actually, MasterChatHandler instantiates QueryEngine(..., tier=target_tier).
    # To avoid network calls, we should patch `src.app.modules.features.chat.master_chat.QueryEngine`
    with patch("src.app.modules.features.chat.master_chat.QueryEngine") as MockResponseEngine:
        # Configure the mock instance returned by the constructor
        mock_instance = MockResponseEngine.return_value
        mock_instance.answer_query = AsyncMock(return_value=mock_response)
        # It also needs .tier and .memory for any checks?
        mock_instance.tier = "premium"

        await handler.send_message(test_user.id, "Hello Premium", db, model_tier="premium")

    # VERIFY DB PERSISTENCE
    # Check the last message for 'premium' metadata
    result = await db.execute(
        select(ChatMessage)
        .join(ChatSession)
        .where(ChatSession.user_id == test_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    msg = result.scalar_one()

    assert msg.role == "assistant"
    # The 'metadata' field in DB is JSON - in SQLAlchemy model it might be .meta or .metadata_
    # ChatMessage definition usually has `meta` or `metadata_`
    # Let's check ChatMessage definition if this fails, but usually it's `meta`.
    # Code snippet in MasterChatHandler showed `msg.meta`.
    # Wait, the MasterChatHandler used `metadata=...` in add_message.
    # The Model `ChatMessage` uses `meta`?
    # I'll check property. If it fails, I'll see AttributeError.
    # From previous viewed files, `ChatMessage` has `meta`.
    assert msg.meta["model_tier"] == "premium"
    print("\n[PASS] Model Tier 'premium' persisted in message metadata.")


@pytest.mark.asyncio
async def test_phase16_quest_injection(db, test_user, memory):
    """
    Verify that if the LLM calls 'create_quest', the MasterChatHandler:
    1. Parses the JSON output.
    2. Fetches the Quest.
    3. Injects 'QUEST_ITEM' component into message metadata.
    """
    # 1. SETUP: Create a real quest in DB so we can fetch it
    # We can use QuestManager or just direct DB insert
    quest = Quest(
        user_id=test_user.id,
        title="Test Integration Quest",
        description="Created via test",
        xp_reward=50,
        is_active=True,
    )
    db.add(quest)
    await db.commit()
    await db.refresh(quest)

    # 2. MOCK LLM RESPONSE WITH TOOL TRACE
    # We need to mock the handler in this test too
    mock_engine = MagicMock()
    mock_engine.tier = "standard"
    mock_engine.memory = memory

    handler = MasterChatHandler(query_engine=mock_engine)

    # Construct the JSON string that the tool WOULD return
    tool_output_json = json.dumps(
        {
            "status": "success",
            "quest_id": quest.id,
            "title": quest.title,
            "xp_reward": quest.xp_reward,
            "message": "Quest created.",
        }
    )

    # Create the trace object resembling a tool execution
    mock_trace = TraceMock(
        thinking_steps=[],
        tools_used=[
            ToolExecutionMock(
                tool="create_quest",
                operation="call",
                input_params={"title": "Test Quest"},
                result_summary=tool_output_json,  # THIS is what Handler parses
                latency_ms=100,
            )
        ],
    )

    mock_response = QueryResponseMock(answer="I have created the quest for you.", trace=mock_trace, context_used=[])

    handler.query_engine.answer_query = AsyncMock(return_value=mock_response)

    # 3. EXECUTE
    await handler.send_message(test_user.id, "Create a quest", db, model_tier="standard")

    # 4. VERIFY COMPONENT INJECTION
    result = await db.execute(
        select(ChatMessage)
        .join(ChatSession)
        .where(ChatSession.user_id == test_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    msg = result.scalar_one()

    assert "component" in msg.meta
    comp = msg.meta["component"]

    assert comp["component_type"] == "QUEST_ITEM"
    assert comp["data"]["id"] == quest.id
    assert comp["data"]["title"] == "Test Integration Quest"
    print(f"\n[PASS] Quest Component injected: {comp['component_id']}")


@pytest.mark.asyncio
async def test_phase16_system_event_logging(db, test_user, memory):
    """
    Verify SystemJournalist logs XP events to Master Chat with role='system_event'.
    """
    from src.app.core.events.bus import get_event_bus

    bus = get_event_bus()
    await bus.initialize()

    journalist = SystemJournalist()  # No args

    # 1. SETUP MASTER SESSION (Need one to log to)
    from src.app.modules.features.chat.session_manager import SessionManager
    from src.app.protocol import events

    session_mgr = SessionManager()
    session = await session_mgr.get_or_create_master_session(test_user.id, db)

    # 2. TRIGGER EVENT
    packet = ProgressionPacket(
        source="test_integration",
        event_type=events.PROGRESSION_EXPERIENCE_GAIN,
        payload={
            "title": "Test Event Title",
            "category": "General",
        },  # SystemJournalist looks for title/category in payload
        user_id=str(test_user.id),
        amount=100,
        reason="Test Event Reason",
        category="growth",
    )

    # Manually calling the handler to bypass EventBus async complexity in test
    # (Unit testing the handler logic, integration testing the DB write)
    await journalist.handle_experience_gain(packet)

    # 3. VERIFY DB
    # We MUST expect a new message in that session with role='system_event'
    # journalist.handle_experience_gain opens its OWN db session via async_get_db if not passed,
    # OR it uses session_manager. which uses... wait.
    # SystemJournalist.handle_experience_gain creates a fresh session?
    # Let's inspect the code in the test or trust the behavior.
    # Wait, in the code audit:
    # `await self.session_manager.add_message(..., db=db)`
    # The snippet showed it accepting `db`? NO, the snippet showed:
    # `async def handle_experience_gain(self, packet: ProgressionPacket):`
    # It does NOT take DB. It gets it internally?
    # "await self.session_manager.get_default_master_conversation(user_id, db)"
    # Where does `db` come from in `handle_experience_gain`?
    # The code snippet I viewed earlier had `db=db` usage but didn't show where `db` came from.
    # Usually event handlers instantiate their own DB session context manager.
    # So we need to query `db` (the test fixture session) to see if the commit happened.
    # But if `handle_experience_gain` uses a SEPARATE session and commits, our `db` fixture (which is an open transaction?) might not see it if isolation level is high, OR it will seeing as it's committed.
    # Postgres READ COMMITTED is default.

    # Check if handle_experience_gain is async and how it gets DB.
    # I'll optimistically assume it works or fail and fix.

    # Retrieve message
    # Use order_by and limit to fetch the most recent one, in case prior test runs left data
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .where(ChatMessage.role == "system_event")
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    msg = result.scalar_one_or_none()

    assert msg is not None
    assert "Test Event" in msg.content
    assert msg.meta["type"] == "system_event"
    assert msg.meta["xp"] == 100
    print(f"\n[PASS] System Event logged: {msg.content}")
