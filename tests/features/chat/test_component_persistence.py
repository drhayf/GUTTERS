import pytest
from unittest.mock import MagicMock, AsyncMock
from src.app.modules.features.chat.master_chat import MasterChatHandler
from src.app.models.user_profile import UserProfile
from src.app.models.chat_session import ChatMessage, ChatSession, SessionType
from datetime import datetime, UTC


@pytest.mark.asyncio
async def test_component_response_hydration(mocker):
    """
    Test that component responses stored in UserProfile
    are correctly hydrated into message history.
    """
    # 1. Mock DB and Session Manager
    mock_db = AsyncMock()

    # Mock SessionManager inside MasterChatHandler
    mock_session_manager = MagicMock()
    # Explicitly make async methods AsyncMock
    mock_session_manager.get_default_master_conversation = AsyncMock()
    mock_session_manager.get_session = AsyncMock()
    mock_session_manager.get_session_history = AsyncMock()

    mocker.patch("src.app.modules.features.chat.master_chat.SessionManager", return_value=mock_session_manager)

    # Mock Session
    mock_session = MagicMock(spec=ChatSession)
    mock_session.id = 1
    mock_session.user_id = 999
    mock_session.session_type = SessionType.MASTER.value
    mock_session_manager.get_default_master_conversation.return_value = mock_session
    mock_session_manager.get_session.return_value = mock_session
    mock_session_manager.get_session_history.return_value = []  # Default empty, overriden later

    # 2. Setup Message with Component (No response yet)
    component_id = "test-comp-123"
    message_meta = {"component": {"component_id": component_id, "type": "multi_slider", "payload": {"some": "data"}}}

    mock_message = MagicMock(spec=ChatMessage)
    mock_message.role = "assistant"
    mock_message.content = "Here is a component"
    mock_message.created_at = datetime.now(UTC)
    mock_message.meta = message_meta

    # Session manager returns this message
    mock_session_manager.get_session_history.return_value = [mock_message]

    # 3. Setup UserProfile with Saved Response
    mock_profile = MagicMock(spec=UserProfile)
    # Simulate the data structure stored by submit_component_response
    mock_profile.data = {
        "component_responses": [
            {
                "component_id": component_id,
                "component_type": "multi_slider",
                "slider_values": {"mood": 8},
                "submitted_at": "2024-01-01T12:00:00Z",
            }
        ]
    }

    # Mock DB execution to return profile
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_profile
    # execute is awaited, so it must be an AsyncMock (or return a future)
    mock_db.execute = AsyncMock(return_value=mock_result)

    # 4. Initialize Handler
    handler = MasterChatHandler(query_engine=MagicMock())

    # 5. Execute Hydration
    history = await handler.get_conversation_history(user_id=999, limit=10, db=mock_db)

    # 6. Verify Hydration
    assert len(history) == 1
    msg = history[0]

    # Debug output
    print(f"Hydrated Metadata: {msg['metadata']}")

    # Check if component has response
    assert "component" in msg["metadata"]
    assert "response" in msg["metadata"]["component"], "Hydration failed: 'response' key missing in component"

    response = msg["metadata"]["component"]["response"]
    assert response["component_id"] == component_id
    assert response["slider_values"]["mood"] == 8


@pytest.mark.asyncio
async def test_component_response_hydration_robust(mocker):
    """
    Test robust matching (whitespace/case) for component hydration.
    """
    # ... (Setup similar to above but with mismatched ID) ...
    mock_db = AsyncMock()
    mock_session_manager = MagicMock()
    # Explicitly make async methods AsyncMock
    mock_session_manager.get_default_master_conversation = AsyncMock()
    mock_session_manager.get_session = AsyncMock()
    mock_session_manager.get_session_history = AsyncMock()

    mocker.patch("src.app.modules.features.chat.master_chat.SessionManager", return_value=mock_session_manager)

    mock_session = MagicMock(spec=ChatSession)
    mock_session.id = 1
    mock_session.user_id = 999
    mock_session.session_type = SessionType.MASTER.value
    mock_session_manager.get_default_master_conversation.return_value = mock_session
    mock_session_manager.get_session.return_value = mock_session

    # Message has CLEAN ID
    clean_id = "test-uuid-123"
    message_meta = {"component": {"component_id": clean_id, "type": "vote"}}

    mock_message = MagicMock(spec=ChatMessage)
    mock_message.role = "assistant"
    mock_message.content = "Vote now"
    mock_message.created_at = datetime.now(UTC)
    mock_message.meta = message_meta

    mock_session_manager.get_session_history.return_value = [mock_message]

    # Profile has DIRTY ID (whitespace)
    dirty_id = "  test-uuid-123  "
    mock_profile = MagicMock(spec=UserProfile)
    mock_profile.data = {"component_responses": [{"component_id": dirty_id, "component_type": "vote", "vote": "yes"}]}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_profile
    mock_db.execute = AsyncMock(return_value=mock_result)

    handler = MasterChatHandler(query_engine=MagicMock())

    # Execute
    history = await handler.get_conversation_history(user_id=999, limit=10, db=mock_db)

    # Verify match happened despite whitespace
    msg = history[0]
    assert "response" in msg["metadata"]["component"]
    assert msg["metadata"]["component"]["response"]["vote"] == "yes"
