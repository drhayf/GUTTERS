"""
High-fidelity integration tests for Observable AI (Phase 7b).

Tests trace generation, tool tracking, and model metadata.
"""

import pytest
from sqlalchemy import select

from src.app.modules.intelligence.query.engine import QueryEngine
from src.app.core.memory import get_active_memory
from src.app.modules.features.chat.master_chat import MasterChatHandler


@pytest.mark.asyncio
async def test_query_generates_trace(seeded_user, db):
    """
    Test that Query Engine generates activity trace.

    Verification:
    - Trace has thinking steps
    - Trace has tool calls
    - Trace has model info
    - Trace has confidence score
    """
    memory = get_active_memory()
    await memory.initialize()

    engine = QueryEngine()

    response = await engine.answer_query(seeded_user, "What should I focus on today?", db, use_vector_search=True)

    # Verify trace exists
    assert response.trace is not None

    # Verify thinking steps
    assert len(response.trace.thinking_steps) > 0
    assert any("Active Memory" in step.description for step in response.trace.thinking_steps)

    # Verify tool calls
    assert len(response.trace.tools_used) > 0

    # Check Active Memory was called
    active_memory_calls = [call for call in response.trace.tools_used if call.tool == "active_memory"]
    assert len(active_memory_calls) > 0

    # Verify model info
    assert response.trace.model_info is not None
    # Depending on test env, might be unknown or actual provider
    assert response.trace.model_info.tokens_in > 0
    assert response.trace.model_info.tokens_out > 0

    # Verify confidence
    assert 0.0 <= response.trace.confidence <= 1.0


@pytest.mark.asyncio
async def test_vector_search_tracked_in_trace(seeded_user, db):
    """
    Test that vector search operations appear in trace.
    """
    from src.app.modules.intelligence.vector.embedding_service import EmbeddingService
    from src.app.models.embedding import Embedding
    from src.app.models.user_profile import UserProfile
    from src.app.core.config import settings

    # Ensure user profile exists
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == seeded_user))
    profile = result.scalar_one_or_none()
    if not profile:
        db.add(
            UserProfile(
                user_id=seeded_user, data={"journal_entries": [{"content": "I feel tired", "date": "2024-01-24"}]}
            )
        )
        await db.commit()

    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())

    # Seed an embedding manually to ensure count > 0
    # Use real embedding service if possible, or mock search if necessary.
    # But mandate says NO mocks for core logic.
    embedding_data = await service.embed_text("Test journal entry")
    db.add(
        Embedding(
            user_id=seeded_user,
            content="Test journal entry",
            embedding=embedding_data,
            content_metadata={"source": "test"},
        )
    )
    await db.commit()

    memory = get_active_memory()
    await memory.initialize()

    engine = QueryEngine()

    response = await engine.answer_query(seeded_user, "Tell me about my journal patterns", db, use_vector_search=True)

    # Verify vector search in trace
    vector_calls = [call for call in response.trace.tools_used if call.tool == "vector_search"]

    assert len(vector_calls) > 0

    # Check details
    search_call = next(c for c in vector_calls if c.operation == "hybrid_search")
    assert search_call.latency_ms >= 0
    assert "Found" in search_call.result_summary


@pytest.mark.asyncio
async def test_trace_stored_in_message_metadata(seeded_user, db):
    """
    Test that trace is stored in ChatMessage.metadata.
    """
    memory = get_active_memory()
    await memory.initialize()

    query_engine = QueryEngine()
    handler = MasterChatHandler(query_engine)

    response = await handler.send_message(seeded_user, "What should I do today?", db)

    # Verify trace in response
    assert "trace" in response
    assert response["trace"] is not None

    # Get message from database
    from src.app.models.chat_session import ChatMessage, ChatSession

    # Find master session for user
    sess_result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == seeded_user, ChatSession.session_type == "master")
    )
    session = sess_result.scalars().first()

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id, ChatMessage.role == "assistant")
        .order_by(ChatMessage.created_at.desc())
    )
    latest_message = result.scalars().first()

    # Verify trace in metadata
    assert "trace" in latest_message.meta
    assert latest_message.meta["trace"] is not None
    assert "thinking_steps" in latest_message.meta["trace"]
    assert "tools_used" in latest_message.meta["trace"]
    assert "model_info" in latest_message.meta["trace"]


@pytest.mark.asyncio
async def test_trace_latency_calculation(seeded_user, db):
    """
    Test that trace calculates total latency correctly.
    """
    memory = get_active_memory()
    await memory.initialize()

    engine = QueryEngine()

    response = await engine.answer_query(seeded_user, "Quick test for latency", db, use_vector_search=False)

    trace = response.trace

    # Verify timestamps
    assert trace.started_at is not None
    assert trace.completed_at is not None
    assert trace.completed_at > trace.started_at

    # Verify total latency
    assert trace.total_latency_ms > 0

    # Total should be at least as long as LLM call
    if trace.model_info:
        assert trace.total_latency_ms >= trace.model_info.latency_ms
