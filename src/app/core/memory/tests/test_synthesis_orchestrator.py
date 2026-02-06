"""
Integration Tests for SynthesisOrchestrator

Tests using REAL components to verify synthesis lifecycle management.
Validates trigger evaluation, background/foreground synthesis, and memory updates.
"""
from datetime import datetime

import pytest
from sqlalchemy import select

from src.app.core.db.database import local_session
from src.app.core.memory import SynthesisTrigger
from src.app.models.user_profile import UserProfile

# =============================================================================
# Should Synthesize Tests
# =============================================================================

@pytest.mark.asyncio
async def test_should_synthesize_no_synthesis(orchestrator, test_user_id, cleanup_test_cache):
    """Should synthesize when no synthesis exists."""
    result = await orchestrator.should_synthesize(
        user_id=test_user_id,
        trigger=SynthesisTrigger.USER_REQUESTED
    )

    assert result is True, "Should synthesize when no synthesis exists"


@pytest.mark.asyncio
async def test_should_synthesize_critical_trigger(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Should synthesize on critical triggers even with valid synthesis."""
    # Create valid synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Valid synthesis",
        themes=["test"],
        modules_included=["astrology"]
    )

    # Check critical trigger
    result = await orchestrator.should_synthesize(
        user_id=test_user_id,
        trigger=SynthesisTrigger.MODULE_CALCULATED
    )

    assert result is True, "Critical triggers should always synthesize"


@pytest.mark.asyncio
async def test_should_not_synthesize_non_critical(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Should NOT synthesize on non-critical triggers with valid synthesis."""
    # Create valid synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Valid synthesis",
        themes=["test"],
        modules_included=["astrology"]
    )

    # Check non-critical trigger (future tracking trigger)
    result = await orchestrator.should_synthesize(
        user_id=test_user_id,
        trigger=SynthesisTrigger.LUNAR_PHASE_CHANGE
    )

    assert result is False, "Non-critical triggers should skip synthesis when valid exists"


# =============================================================================
# Trigger Synthesis Tests
# =============================================================================

@pytest.mark.asyncio
async def test_trigger_synthesis_foreground(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Test foreground (blocking) synthesis."""

    print(f"Testing foreground synthesis for user {test_user_id}...")

    # Seed some module data
    async with local_session() as db:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user_id))
        profile = result.scalar_one()
        profile.data = {"astrology": {"sun": "leo"}}
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(profile, 'data')
        await db.commit()

    # Trigger synthesis and wait for result
    result = await orchestrator.trigger_synthesis(
        user_id=test_user_id,
        trigger_type=SynthesisTrigger.USER_REQUESTED,
        background=False  # Wait for completion
    )

    # Should return synthesis result
    assert result is not None, "Foreground synthesis should return result"
    assert "synthesis" in result, "Result should contain synthesis text"
    assert "themes" in result, "Result should contain themes"
    assert "modules_included" in result, "Result should contain modules list"

    print(f"Synthesis created with {len(result['modules_included'])} modules")
    print(f"Themes: {result['themes']}")

    # Verify it was cached in memory
    cached = await memory.get_master_synthesis(test_user_id)
    assert cached is not None, "Synthesis should be cached"
    assert cached["validity"] == "valid"


@pytest.mark.asyncio
async def test_trigger_synthesis_uses_cache(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Test that synthesis uses cache when not needed."""

    # Create valid cached synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Cached synthesis",
        themes=["cached"],
        modules_included=["astrology"]
    )

    # Trigger with non-critical trigger
    result = await orchestrator.trigger_synthesis(
        user_id=test_user_id,
        trigger_type=SynthesisTrigger.LUNAR_PHASE_CHANGE,
        background=False
    )

    # Should return cached synthesis
    assert result is not None
    assert result["synthesis"] == "Cached synthesis"


# =============================================================================
# Get or Create Synthesis Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_or_create_returns_cached(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Test get_or_create returns cached synthesis when valid."""

    # Create valid synthesis
    await memory.set_master_synthesis(
        user_id=test_user_id,
        synthesis="Existing valid synthesis",
        themes=["existing"],
        modules_included=["astrology"]
    )

    # Get or create
    result = await orchestrator.get_or_create_synthesis(test_user_id)

    assert result is not None
    assert result["synthesis"] == "Existing valid synthesis"


@pytest.mark.asyncio
async def test_get_or_create_generates_new(orchestrator, test_user_id, cleanup_test_cache):
    """Test get_or_create generates new synthesis when none exists."""

    print("Testing get_or_create generates new synthesis...")

    # Seed some module data so synthesis has something to do
    async with local_session() as db:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user_id))
        profile = result.scalar_one()
        profile.data = {"astrology": {"sun": "leo"}}
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(profile, 'data')
        await db.commit()

    # Get or create - should generate new
    result = await orchestrator.get_or_create_synthesis(test_user_id)

    assert result is not None, "Should create new synthesis"
    assert "synthesis" in result
    assert len(result.get("modules_included", [])) > 0

    print(f"Generated new synthesis with {len(result['modules_included'])} modules")


# =============================================================================
# Integration with Memory Tests
# =============================================================================

@pytest.mark.asyncio
async def test_synthesis_updates_memory(orchestrator, memory, test_user_id, cleanup_test_cache):
    """Test that synthesis properly updates memory cache."""

    # Trigger synthesis
    result = await orchestrator.trigger_synthesis(
        user_id=test_user_id,
        trigger_type=SynthesisTrigger.USER_REQUESTED,
        background=False
    )

    # Verify memory was updated
    cached = await memory.get_master_synthesis(test_user_id)

    assert cached is not None, "Memory should be updated"
    assert cached["synthesis"] == result["synthesis"]
    assert cached["themes"] == result["themes"]
    assert cached["modules_included"] == result["modules_included"]
    assert cached["validity"] == "valid"


# =============================================================================
# Trigger Enum Tests
# =============================================================================

def test_trigger_enum_values():
    """Verify all expected trigger types exist."""
    assert SynthesisTrigger.MODULE_CALCULATED.value == "module_calculated"
    assert SynthesisTrigger.GENESIS_FIELD_CONFIRMED.value == "genesis_confirmed"
    assert SynthesisTrigger.USER_REQUESTED.value == "user_requested"
    assert SynthesisTrigger.SCHEDULED.value == "scheduled"

    # Future triggers (stubbed)
    assert SynthesisTrigger.SOLAR_STORM_DETECTED.value == "solar_storm"
    assert SynthesisTrigger.LUNAR_PHASE_CHANGE.value == "lunar_phase"
    assert SynthesisTrigger.TRANSIT_EXACT.value == "transit_exact"


def test_critical_triggers_set():
    """Verify critical triggers are properly defined."""
    from src.app.core.memory.synthesis_orchestrator import CRITICAL_TRIGGERS

    assert SynthesisTrigger.MODULE_CALCULATED in CRITICAL_TRIGGERS
    assert SynthesisTrigger.GENESIS_FIELD_CONFIRMED in CRITICAL_TRIGGERS
    assert SynthesisTrigger.USER_REQUESTED in CRITICAL_TRIGGERS

    # Future triggers should NOT be critical yet
    assert SynthesisTrigger.LUNAR_PHASE_CHANGE not in CRITICAL_TRIGGERS


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.asyncio
async def test_synthesis_performance(orchestrator, test_user_id, cleanup_test_cache):
    """Test that synthesis completes in reasonable time."""

    print("Measuring synthesis performance...")

    start = datetime.utcnow()
    result = await orchestrator.trigger_synthesis(
        user_id=test_user_id,
        trigger_type=SynthesisTrigger.USER_REQUESTED,
        background=False
    )
    elapsed = (datetime.utcnow() - start).total_seconds()

    assert result is not None
    assert elapsed < 30, f"Synthesis took {elapsed:.2f}s, should be <30s"

    print(f"Synthesis completed in {elapsed:.2f}s")
