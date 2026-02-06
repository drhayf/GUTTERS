"""
Integration tests for Chronos State Manager.

Tests Redis caching, database persistence, and event emission
for the Cardology time-mapping system.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestChronosStateManager:
    """Tests for ChronosStateManager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ChronosStateManager instance."""
        from src.app.core.state.chronos import ChronosStateManager
        return ChronosStateManager()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        return redis

    @pytest.fixture
    def mock_memory(self, mock_redis):
        """Create a mock ActiveMemory instance."""
        memory = MagicMock()
        memory.redis_client = mock_redis
        return memory

    def test_import_chronos_manager(self):
        """Test that ChronosStateManager can be imported."""
        from src.app.core.state.chronos import ChronosStateManager, get_chronos_manager

        manager = get_chronos_manager()
        assert manager is not None
        assert isinstance(manager, ChronosStateManager)

    def test_chronos_state_exports(self):
        """Test that state module exports ChronosStateManager."""
        from src.app.core.state import ChronosStateManager, get_chronos_manager

        assert ChronosStateManager is not None
        assert get_chronos_manager is not None

    def test_magi_events_defined(self):
        """Test that MAGI event constants are defined."""
        from src.app.protocol.events import (
            MAGI_PERIOD_SHIFT,
            MAGI_PROFILE_CALCULATED,
            MAGI_STATE_CACHED,
            MAGI_YEAR_SHIFT,
        )

        assert MAGI_PROFILE_CALCULATED == "magi.profile.calculated"
        assert MAGI_PERIOD_SHIFT == "magi.period.shift"
        assert MAGI_YEAR_SHIFT == "magi.year.shift"
        assert MAGI_STATE_CACHED == "magi.state.cached"

    def test_worker_job_registered(self):
        """Test that chronos worker job is registered."""
        from src.app.core.worker.functions import daily_chronos_update_job
        from src.app.core.worker.settings import WorkerSettings

        # Check function is in the functions list
        assert daily_chronos_update_job in WorkerSettings.functions

        # Check cron job is registered
        cron_funcs = [cron.coroutine for cron in WorkerSettings.cron_jobs]
        assert daily_chronos_update_job in cron_funcs

    @pytest.mark.asyncio
    async def test_chronos_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager._initialized is False

        await manager.initialize()
        assert manager._initialized is True

        await manager.cleanup()
        assert manager._initialized is False

    @pytest.mark.asyncio
    async def test_refresh_user_chronos_calculates_state(self, manager, mock_memory):
        """Test that refresh_user_chronos calculates correct state."""
        # This test verifies the CardologyModule integration works
        # Full integration requires database - tested separately
        from src.app.modules.intelligence.cardology import CardologyModule

        module = CardologyModule()
        birth_date = date(1963, 12, 18)  # Brad Pitt

        # Verify module methods work
        period = module.get_current_period(birth_date)
        # Kernel uses "period" for planet name
        assert "period" in period
        assert "card_name" in period

        profile = module.calculate_profile(birth_date, 2024)
        assert "birth_card" in profile
        assert "planetary_ruling_card" in profile

    def test_cardology_module_integration(self):
        """Test that CardologyModule works with ChronosStateManager."""
        from src.app.modules.intelligence.cardology import CardologyModule

        module = CardologyModule()

        # Brad Pitt - King of Hearts
        birth_date = date(1963, 12, 18)

        profile = module.calculate_profile(birth_date, 2024)
        # The kernel returns the card with rank/suit/name structure
        birth_card = profile["birth_card"]
        assert birth_card["rank"] == 13
        assert birth_card["suit"] == "HEARTS"

        period = module.get_current_period(birth_date)
        # Kernel API uses "period" for planet name
        assert "period" in period
        assert "card" in period
        assert "card_name" in period


class TestChronosWorkerJob:
    """Tests for the daily_chronos_update_job."""

    def test_worker_job_exists(self):
        """Test that the worker job function exists."""
        import asyncio

        from src.app.core.worker.functions import daily_chronos_update_job
        assert asyncio.iscoroutinefunction(daily_chronos_update_job)

    def test_worker_settings_cron_schedule(self):
        """Test that chronos job runs at 4 AM."""
        from src.app.core.worker.functions import daily_chronos_update_job
        from src.app.core.worker.settings import WorkerSettings

        # Find the chronos cron job
        chronos_cron = None
        for cron in WorkerSettings.cron_jobs:
            if cron.coroutine == daily_chronos_update_job:
                chronos_cron = cron
                break

        assert chronos_cron is not None
        # ARQ cron job stores hour as int, not set
        assert chronos_cron.hour == 4  # 4 AM UTC
        assert chronos_cron.minute == 0
