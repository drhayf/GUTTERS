"""
High-fidelity integration tests for Chat Architecture.

Tests Master Chat, Branch Sessions, and Journal.
"""


import pytest


@pytest.mark.asyncio
async def test_master_chat_creation(seeded_user, real_db):
    """Test Master Chat session auto-creation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    session = await manager.get_or_create_master_session(seeded_user, real_db)

    assert session.session_type == "master"
    assert session.contribute_to_memory is True
    assert session.user_id == seeded_user
    assert session.name == "Master Chat"


@pytest.mark.asyncio
async def test_journal_branch_creation(seeded_user, real_db):
    """Test Journal Branch creation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    session = await manager.create_branch_session(seeded_user, "journal", "My Journal", True, real_db)

    assert session.session_type == "journal"
    assert session.name == "My Journal"
    assert session.contribute_to_memory is True


@pytest.mark.asyncio
async def test_master_chat_conversation(seeded_user, real_db):
    """Test Master Chat conversation."""
    from src.app.core.memory import get_active_memory
    from src.app.modules.features.chat.master_chat import MasterChatHandler
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.modules.intelligence.synthesis.synthesizer import get_llm

    memory = get_active_memory()
    await memory.initialize()

    # Ensure memory is clean
    if memory.redis_client:
        await memory.redis_client.flushdb()

    query_engine = QueryEngine(get_llm(), memory)
    handler = MasterChatHandler(query_engine)

    response = await handler.send_message(seeded_user, "What should I focus on today?", real_db)

    assert response["message"] is not None
    assert len(response["message"]) > 20
    assert "modules_consulted" in response
    assert response["session_id"] is not None


@pytest.mark.asyncio
async def test_journal_entry_creation(seeded_user, real_db):
    """Test journal entry creation through chat."""
    from src.app.modules.features.chat.session_manager import SessionManager
    from src.app.modules.features.journal.journal_chat import JournalChatHandler

    # Create journal session
    manager = SessionManager()
    session = await manager.create_branch_session(seeded_user, "journal", "Test Journal", True, real_db)

    # Send journal entry
    handler = JournalChatHandler()
    response = await handler.send_message(
        seeded_user, session.id, "I felt really anxious today during the meeting. Had a headache.", real_db
    )

    assert response["metadata"].get("entry_created") is True
    assert "entry_id" in response["metadata"]

    # Verify persistence in UserProfile
    from sqlalchemy import select

    from src.app.models.user_profile import UserProfile

    result = await real_db.execute(select(UserProfile).where(UserProfile.user_id == seeded_user))
    profile = result.scalar_one()
    entries = profile.data.get("journal_entries", [])

    assert len(entries) > 0
    latest = entries[-1]
    assert "anxious" in latest["text"]


@pytest.mark.asyncio
async def test_memory_toggle(seeded_user, real_db):
    """Test memory contribution toggle."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    # Create session with memory ON
    session = await manager.create_branch_session(seeded_user, "journal", "Private Journal", True, real_db)

    assert session.contribute_to_memory is True

    # Toggle OFF
    updated = await manager.toggle_memory_contribution(session.id, False, real_db)

    assert updated.contribute_to_memory is False
