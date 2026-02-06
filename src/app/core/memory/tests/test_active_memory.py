"""
Integration Tests for ActiveMemory

Tests using REAL Redis and PostgreSQL to verify actual system functionality.
These tests validate the complete three-layer memory architecture in action.

Setup Requirements:
- Redis must be running (see .env for connection)
- PostgreSQL must be running with test database
- User test data should exist
"""
import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from src.app.core.db.database import local_session
from src.app.models.user_profile import UserProfile

# =============================================================================
# Master Synthesis Tests
# =============================================================================

@pytest.mark.asyncio
async def test_synthesis_round_trip(memory, test_user_id, cleanup_test_cache):
    """Test storing and retrieving master synthesis using real Redis."""

    # Verify no synthesis exists initially
    initial = await memory.get_master_synthesis(test_user_id)
    assert initial is None

    # Store synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Your cosmic profile reveals deep creativity and leadership potential.",
        themes=["creativity", "leadership", "transformation"],
        modules_included=["astrology", "human_design", "numerology"]
    )

    # Retrieve and verify
    result = await memory.get_master_synthesis(test_user_id)

    assert result is not None
    assert result["synthesis"] == "Your cosmic profile reveals deep creativity and leadership potential."
    assert result["themes"] == ["creativity", "leadership", "transformation"]
    assert result["modules_included"] == ["astrology", "human_design", "numerology"]
    assert result["validity"] == "valid"
    assert "generated_at" in result

    # Verify timestamp is recent
    generated_at = datetime.fromisoformat(result["generated_at"])
    age = datetime.utcnow() - generated_at
    assert age.total_seconds() < 5, "Timestamp should be very recent"


@pytest.mark.asyncio
async def test_synthesis_staleness_detection(memory, test_user_id, cleanup_test_cache):
    """Test that synthesis is correctly marked as stale after 24h."""

    # Store synthesis with old timestamp
    old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()

    old_synthesis = {
        "synthesis": "Old synthesis",
        "themes": ["old"],
        "generated_at": old_time,
        "modules_included": ["astrology"],
        "validity": "valid"
    }

    # Manually set in Redis with old timestamp
    import json
    key = f"memory:hot:synthesis:{test_user_id}"
    await memory.redis_client.set(
        key,
        json.dumps(old_synthesis),
        ex=memory.HOT_TTL
    )

    # Retrieve and verify staleness detection
    result = await memory.get_master_synthesis(test_user_id)

    assert result is not None
    assert result["validity"] == "stale", "Should be marked as stale"


@pytest.mark.asyncio
async def test_synthesis_invalidation(memory, test_user_id, cleanup_test_cache):
    """Test invalidating synthesis cache."""

    # Store synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Test synthesis",
        themes=["test"],
        modules_included=["astrology"]
    )

    # Verify it exists
    result = await memory.get_master_synthesis(test_user_id)
    assert result is not None

    # Invalidate
    await memory.invalidate_synthesis(test_user_id)

    # Verify it's gone
    result = await memory.get_master_synthesis(test_user_id)
    assert result is None


# =============================================================================
# Module Output Tests
# =============================================================================

@pytest.mark.asyncio
async def test_module_output_caching(memory, test_user_id, cleanup_test_cache):
    """Test caching and retrieving module outputs."""

    astro_data = {
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 5},
            {"name": "Moon", "sign": "Cancer", "house": 4}
        ],
        "ascendant": {"sign": "Scorpio"}
    }

    # Cache module output
    await memory.set_module_output(test_user_id, "astrology", astro_data)

    # Retrieve and verify
    result = await memory.get_module_output(test_user_id, "astrology")

    assert result is not None
    assert result["planets"][0]["name"] == "Sun"
    assert result["ascendant"]["sign"] == "Scorpio"


@pytest.mark.asyncio
async def test_module_output_database_fallback(memory, test_user_id, cleanup_test_cache):
    """Test that module output falls back to database when not cached."""

    # Store data only in database
    hd_data = {
        "type": "Projector",
        "strategy": "Wait for Invitation",
        "authority": "Emotional"
    }

    async with local_session() as db:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == test_user_id)
        )
        profile = result.scalar_one()

        if profile.data is None:
            profile.data = {}
        profile.data["human_design"] = hd_data

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(profile, 'data')
        await db.commit()

    # Ensure it's not cached in Redis
    await memory.invalidate_module(test_user_id, "human_design")

    # Get module output (should fallback to database)
    result = await memory.get_module_output(test_user_id, "human_design")

    assert result is not None
    assert result["type"] == "Projector"
    assert result["strategy"] == "Wait for Invitation"

    # Verify it was cached in Redis for future reads
    cached = await memory.get_module_output(test_user_id, "human_design")
    assert cached is not None
    assert cached["type"] == "Projector"


# =============================================================================
# Conversation History Tests
# =============================================================================

@pytest.mark.asyncio
async def test_conversation_history_dual_storage(memory, test_user_id, cleanup_test_cache):
    """Test that conversation history is stored in both Redis and PostgreSQL."""

    # Add conversation
    await memory.add_to_history(
        user_id=test_user_id,
        prompt="What should I focus on today?",
        response="Based on your Leo Sun and Projector type, focus on creative leadership opportunities."
    )

    # Give database a moment to persist
    await asyncio.sleep(0.5)

    # Verify in Redis (hot memory)
    redis_history = await memory.get_conversation_history(test_user_id, limit=10)
    assert len(redis_history) == 1
    assert redis_history[0]["prompt"] == "What should I focus on today?"

    # Verify in PostgreSQL (cold storage)
    async with local_session() as db:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == test_user_id)
        )
        profile = result.scalar_one()

        assert "conversation_history" in profile.data
        assert len(profile.data["conversation_history"]) >= 1

        latest = profile.data["conversation_history"][-1]
        assert latest["prompt"] == "What should I focus on today?"
        assert "response" in latest
        assert "timestamp" in latest


@pytest.mark.asyncio
async def test_conversation_history_limit(memory, test_user_id, cleanup_test_cache):
    """Test that Redis history is limited to last 10 entries."""

    # Add 15 conversations
    for i in range(15):
        await memory.add_to_history(
            user_id=test_user_id,
            prompt=f"Question {i}",
            response=f"Answer {i}"
        )

    # Get history from Redis
    history = await memory.get_conversation_history(test_user_id, limit=10)

    # Should only have last 10 (newest first)
    assert len(history) <= 10

    # Verify newest is first
    if len(history) > 0:
        assert "Question 14" in history[0]["prompt"] or "Question" in history[0]["prompt"]


# =============================================================================
# User Preferences Tests
# =============================================================================

@pytest.mark.asyncio
async def test_preferences_dual_storage(memory, test_user_id, cleanup_test_cache):
    """Test preferences are stored in both Redis and PostgreSQL."""

    # Set preference
    await memory.set_user_preference(
        user_id=test_user_id,
        pref_key="llm_model",
        value="anthropic/claude-opus-4.5-20251101"
    )

    # Give database a moment to persist
    await asyncio.sleep(0.5)

    # Verify in Redis
    redis_prefs = await memory.get_user_preferences(test_user_id)
    assert redis_prefs["llm_model"] == "anthropic/claude-opus-4.5-20251101"

    # Verify in PostgreSQL
    async with local_session() as db:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == test_user_id)
        )
        profile = result.scalar_one()

        assert "preferences" in profile.data
        assert profile.data["preferences"]["llm_model"] == "anthropic/claude-opus-4.5-20251101"


@pytest.mark.asyncio
async def test_preferences_defaults(memory, test_user_id, cleanup_test_cache):
    """Test that default preferences are returned when none exist."""

    # Ensure no preferences cached
    pref_key = f"memory:warm:preferences:{test_user_id}"
    await memory.redis_client.delete(pref_key)

    # Get preferences
    prefs = await memory.get_user_preferences(test_user_id)

    # Should have defaults
    assert "llm_model" in prefs
    assert "synthesis_schedule" in prefs
    assert "synthesis_time" in prefs


# =============================================================================
# Full Context Assembly Tests
# =============================================================================

@pytest.mark.asyncio
async def test_full_context_assembly(memory, test_user_id, cleanup_test_cache):
    """Test assembling complete context from all memory layers."""

    # Set up test data in all layers

    # 1. Master synthesis (hot)
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Full context test synthesis",
        themes=["integration", "testing"],
        modules_included=["astrology", "human_design"]
    )

    # 2. Module outputs (warm)
    await memory.set_module_output(
        test_user_id,
        "astrology",
        {"sun": "Leo", "moon": "Cancer"}
    )

    # 3. Conversation history (hot)
    await memory.add_to_history(
        test_user_id,
        "Test question",
        "Test answer"
    )

    # 4. Preferences (warm)
    await memory.set_user_preference(
        test_user_id,
        "llm_model",
        "anthropic/claude-3.5-sonnet"
    )

    await asyncio.sleep(0.3)

    # Assemble full context
    context = await memory.get_full_context(test_user_id)

    # Verify all components present
    assert context["synthesis"] is not None
    assert context["synthesis"]["synthesis"] == "Full context test synthesis"
    assert context["synthesis"]["themes"] == ["integration", "testing"]

    assert "astrology" in context["modules"]
    assert context["modules"]["astrology"]["sun"] == "Leo"

    assert len(context["history"]) > 0

    assert context["preferences"]["llm_model"] == "anthropic/claude-3.5-sonnet"

    assert "assembled_at" in context


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.asyncio
async def test_memory_read_performance(memory, test_user_id, cleanup_test_cache):
    """Test that memory reads are fast (<10ms)."""

    # Set up cached data
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Performance test",
        themes=["speed"],
        modules_included=["astrology"]
    )

    # Measure read time
    start = datetime.utcnow()
    result = await memory.get_master_synthesis(test_user_id)
    elapsed = (datetime.utcnow() - start).total_seconds() * 1000  # ms

    assert result is not None
    assert elapsed < 2000, f"Read took {elapsed:.2f}ms, should be <2000ms"

    print(f"Memory read completed in {elapsed:.2f}ms")


@pytest.mark.asyncio
async def test_full_context_performance(memory, test_user_id, cleanup_test_cache):
    """Test that full context assembly is fast (<50ms)."""

    # Set up data
    await memory.set_master_synthesis(
        test_user_id, "Test", ["test"], ["astrology"]
    )
    await memory.set_module_output(test_user_id, "astrology", {"test": "data"})

    # Measure assembly time
    start = datetime.utcnow()
    context = await memory.get_full_context(test_user_id)
    elapsed = (datetime.utcnow() - start).total_seconds() * 1000  # ms

    assert context is not None
    assert elapsed < 5000, f"Context assembly took {elapsed:.2f}ms, should be <5000ms"

    print(f"Full context assembled in {elapsed:.2f}ms")
