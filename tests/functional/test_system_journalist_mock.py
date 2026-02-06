from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.modules.features.journal.system_journal import SystemJournalist
from src.app.protocol import events
from src.app.protocol.packet import ProgressionPacket


@pytest.mark.asyncio
async def test_system_journalist_xp_flow():
    # 1. Mock Dependencies
    with (
        patch("src.app.modules.features.journal.system_journal.get_event_bus") as mock_get_bus,
        patch("src.app.modules.features.journal.system_journal.SessionManager") as MockSessionManager,
        patch("src.app.modules.features.journal.system_journal.get_active_memory") as mock_get_memory,
        patch("src.app.modules.features.journal.system_journal.local_session") as mock_local_session,
    ):
        # Setup Mocks
        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        mock_session_manager = AsyncMock()
        MockSessionManager.return_value = mock_session_manager

        # Mock Master Session retrieval
        mock_master = MagicMock()
        mock_master.id = 999
        mock_session_manager.get_default_master_conversation.return_value = mock_master

        mock_memory = AsyncMock()
        mock_memory.redis_client = True  # pretend initialized
        mock_memory.get.return_value = "5.0"  # Kp Index
        mock_get_memory.return_value = mock_memory

        # Mock DB Session
        mock_db = AsyncMock()
        # Mock scalar_one_or_none for PlayerStats (context)
        mock_result = MagicMock()
        mock_stats = MagicMock()
        mock_stats.rank = "A"
        mock_stats.sync_rate = 0.85
        mock_result.scalar_one_or_none.return_value = mock_stats
        mock_db.execute.return_value = mock_result

        # Mock Context Manager for local_session
        mock_local_session.return_value.__aenter__.return_value = mock_db
        mock_local_session.return_value.__aexit__.return_value = None

        # 2. Initialize Journalist
        journalist = SystemJournalist()
        # We need to mock the engine too to avoid LLM call
        journalist.engine = AsyncMock()
        journalist.engine.generate_log_entry.return_value = "Mocked LLM Log Entry: Rank A Hunter detected."

        await journalist.initialize()

        # 3. Simulate Event
        packet = ProgressionPacket(
            user_id=1,
            amount=100,
            reason="Test Quest",
            source="SYSTEM",
            event_type="XP_GAIN",
            payload={"title": "Test Title"},
        )

        await journalist.handle_experience_gain(packet)

        # 4. Assertions

        # A. Context Snapshot Retrieval
        # Should have queried PlayerStats and Memory
        mock_memory.get.assert_called_with("cosmic:kp_index")

        # B. Engine Generation
        journalist.engine.generate_log_entry.assert_called_once()
        args, kwargs = journalist.engine.generate_log_entry.call_args
        assert kwargs["event_type"] == "QUEST_COMPLETE"
        assert kwargs["title"] == "Test Title"
        assert kwargs["context"]["rank"] == "A"
        assert kwargs["context"]["kp_index"] == 5.0

        # C. Default Master Chat Post (Strict Schema Check)
        mock_session_manager.add_message.assert_called_once()
        call_kwargs = mock_session_manager.add_message.call_args[1]

        assert call_kwargs["role"] == "system_event"
        assert "Test Title" in call_kwargs["content"]

        # Check Metadata
        meta = call_kwargs["metadata"]
        assert meta["type"] == "system_event"
        assert meta["title"] == "Test Title"
        assert meta["amount"] == 100
        assert meta["flavor_text"] == "Mocked LLM Log Entry: Rank A Hunter detected."
        assert meta["icon"] == "zap"

        # D. Living Archive (DB Add)
        # Verify db.add was called with a JournalEntry
        assert mock_db.add.called

        # E. Notification Event (Journal Entry Created)
        # Verify that the event bus published the JOURNAL_ENTRY_CREATED event
        # We need to check the call args for publish
        # It's called async, so we use await_args or similar depending on mock type, but assert_called_with works for AsyncMock

        # There might be multiple publish calls (one for XP packet maybe? No, XP packet is published by QuestManager usually, here SystemJournalist acts on packet)
        # SystemJournalist only publishes the Journal Entry event here?
        # Wait, handle_experience_gain creates entry and publishes event.

        # Check if ANY call matches our expectation
        found_notification_event = False
        for call in mock_bus.publish.call_args_list:
            args, kwargs = call
            if args[0] == events.JOURNAL_ENTRY_CREATED:
                found_notification_event = True
                assert kwargs["user_id"] == "1"
                assert args[1]["source"] == "system"
                break

        assert found_notification_event, "JOURNAL_ENTRY_CREATED event was not published!"

        # Retrieve the object added
        added_obj = mock_db.add.call_args[0][0]
        # Since we can't easily import JournalEntry without triggering models...
        # We check attributes if possible, or assume success if type matches name roughly
        assert added_obj.__tablename__ == "journal_entries"
        assert added_obj.user_id == 1
        assert added_obj.source == "system"  # Mapped[JournalSource] might be string or Enum, check value used in code
        # In code: source=JournalSource.SYSTEM. If Enum, it compares by value/enum member.
        # But wait, JournalSource.SYSTEM value is likely "system" string if StrEnum, or needs check.
        # My code imported JournalSource. Let's assume it passed.
