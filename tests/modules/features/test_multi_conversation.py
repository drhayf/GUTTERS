"""
Tests for multi-conversation Master Chat.
"""

import pytest
import pytest
import pytest_asyncio
from sqlalchemy import delete
from src.app.models.chat_session import ChatSession, SessionType


@pytest_asyncio.fixture(autouse=True)
async def cleanup_sessions(db, seeded_user):
    """Clean up sessions for the test user."""
    # Clean before
    await db.execute(delete(ChatSession).where(ChatSession.user_id == seeded_user))
    await db.commit()
    yield
    # Clean after
    await db.execute(delete(ChatSession).where(ChatSession.user_id == seeded_user))
    await db.commit()


@pytest.mark.asyncio
async def test_create_multiple_master_conversations(seeded_user, db):
    """Test that multiple master conversations can be created."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    # Create default
    default = await manager.get_default_master_conversation(seeded_user, db)
    assert default.conversation_name == "General" or default.name == "General"

    # Create work conversation
    work = await manager.create_master_conversation(seeded_user, "Work Planning", db)
    assert work.conversation_name == "Work Planning"
    assert work.session_type == SessionType.MASTER.value

    # Create health conversation
    health = await manager.create_master_conversation(seeded_user, "Health & Wellness", db)
    assert health.conversation_name == "Health & Wellness"

    # Verify all exist
    conversations = await manager.get_master_conversations(seeded_user, db, False)
    assert len(conversations) >= 3
    names = [c.conversation_name for c in conversations]
    assert "General" in names
    assert "Work Planning" in names
    assert "Health & Wellness" in names


@pytest.mark.asyncio
async def test_messages_stay_separate(seeded_user, db):
    """Test that messages in different conversations stay separate."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    # Create two conversations
    conv1 = await manager.create_master_conversation(seeded_user, "Conv 1", db)
    conv2 = await manager.create_master_conversation(seeded_user, "Conv 2", db)

    # Add messages to conv1
    await manager.add_message(conv1.id, "user", "Message in conv 1", {}, db)

    # Add messages to conv2
    await manager.add_message(conv2.id, "user", "Message in conv 2", {}, db)

    # Get histories
    hist1 = await manager.get_session_history(conv1.id, db, limit=10)
    hist2 = await manager.get_session_history(conv2.id, db, limit=10)

    # Verify separation
    assert len(hist1) == 1
    assert len(hist2) == 1
    assert hist1[0].content == "Message in conv 1"
    assert hist2[0].content == "Message in conv 2"


@pytest.mark.asyncio
async def test_cannot_delete_only_master_conversation(seeded_user, db):
    """Test that you can't delete the only master conversation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    # Get default (only master conversation)
    # Ensure ensuring default creates one if it doesn't exist
    default = await manager.get_default_master_conversation(seeded_user, db)

    # Try to delete
    with pytest.raises(ValueError, match="Cannot delete the only master conversation"):
        await manager.delete_conversation(default.id, seeded_user, db)


@pytest.mark.asyncio
async def test_search_across_conversations(seeded_user, db):
    """Test searching across multiple conversations."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    # Create conversations with messages
    conv1 = await manager.create_master_conversation(seeded_user, "Work", db)
    conv2 = await manager.create_master_conversation(seeded_user, "Health", db)

    await manager.add_message(conv1.id, "user", "I need to finish the project report", {}, db)
    await manager.add_message(conv2.id, "user", "I felt anxious today", {}, db)

    # Search for "project"
    results = await manager.search_conversations(seeded_user, "project", 10, db)

    assert len(results) >= 1
    assert any("project" in r["content"].lower() for r in results)

    # Verify it found the right conversation
    work_results = [r for r in results if r["conversation_name"] == "Work"]
    assert len(work_results) >= 1
