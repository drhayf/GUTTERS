# src/app/modules/tracking/tests/test_tracking.py

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

from src.app.modules.tracking.solar.tracker import SolarTracker
from src.app.modules.tracking.lunar.tracker import LunarTracker
from src.app.modules.tracking.transits.tracker import TransitTracker
from src.app.modules.tracking.base import TrackingData
from src.app.core.memory import SynthesisTrigger

# HIGH FIDELITY STANDARDS:
# 1. Real ActiveMemory (Redis)
# 2. Real DB User (Postgres)
# 3. No mocks for core logic (only network)

@pytest.mark.asyncio
async def test_solar_tracker_integration(test_user_id, memory):
    """
    Test Solar Tracker full flow:
    1. Fetch data (mocked network, real parsing)
    2. Comparison logic
    3. Persistence to Redis
    """
    tracker = SolarTracker()
    
    # Mock only the network calls, let everything else run real
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_kp = AsyncMock()
        mock_response_kp.raise_for_status = MagicMock()
        # Realistic NOAA data snippet
        mock_response_kp.json.return_value = [
            {"time_tag": "2023-01-01T00:00:00", "kp_index": 4, "kp": "4M"},
            {"time_tag": "2023-01-01T00:01:00", "kp_index": 5, "kp": "5M"} # G1/G2 threshold
        ]
        
        mock_response_flares = AsyncMock()
        mock_response_flares.raise_for_status = MagicMock()
        mock_response_flares.json.return_value = []
        
        # Side effect for sequential calls (Kp then Flares)
        mock_get.return_value.__aenter__.side_effect = [mock_response_kp, mock_response_flares]
        
        # Execute real update
        result = await tracker.update(test_user_id)
        
        # VERIFY OUTPUT
        assert result["module"] == "solar_tracking"
        assert result["current_data"]["data"]["kp_index"] == 5.0
        assert result["current_data"]["data"]["geomagnetic_storm"] is True  # k_index >= 5
        
        # VERIFY PERSISTENCE (Real Redis)
        # Check if result was cached
        redis_key = f"tracking:solar_tracking:last_result:{test_user_id}"
        cached_result = await memory.get(redis_key)
        assert cached_result is not None
        assert cached_result["current_data"]["data"]["kp_index"] == 5.0

@pytest.mark.asyncio
async def test_lunar_tracker_high_fidelity(test_user_id, memory):
    """
    Test Lunar Tracker with REAL Skyfield calculations.
    No mocks allowed for logic.
    """
    tracker = LunarTracker()
    
    # Execute update
    result = await tracker.update(test_user_id)
    
    # VERIFY DATA INTEGRITY
    data = result["current_data"]["data"]
    assert "phase_name" in data
    assert "sign" in data
    assert "illumination" in data
    assert 0.0 <= data["illumination"] <= 1.0
    
    print(f"\n[High Fidelity] Real Moon Phase: {data['phase_name']}, Sign: {data['sign']}")
    
    # VERIFY PERSISTENCE
    redis_key = f"tracking:lunar_tracking:last_result:{test_user_id}"
    cached = await memory.get(redis_key)
    assert cached is not None
    assert cached["current_data"]["data"]["sign"] == data["sign"]

@pytest.mark.asyncio
async def test_transit_tracker_high_fidelity(test_user_id, memory):
    """
    Test Transit Tracker with REAL Swiss Ephemeris.
    Verifies aspect calculation against real natal chart.
    """
    # Pre-seed natal chart in memory (since we don't run full synthesis pipeline here)
    await memory.initialize()
    
    # Seed mock natal chart for 0 Aries Sun, 15 Taurus Moon
    mock_astrology_output = {
        "sun": {"degree": 0.0, "sign": "Aries", "absolute_degree": 0.0},
        "moon": {"degree": 15.0, "sign": "Taurus", "absolute_degree": 45.0} # 30 + 15
    }
    await memory.set_module_output(test_user_id, "astrology", mock_astrology_output)
    
    tracker = TransitTracker()
    result = await tracker.update(test_user_id)
    
    # VERIFY REAL CALCULATIONS
    assert "exact_transits" in result["comparison"]
    assert "current_positions" in result["comparison"]
    
    # VERIFY PERSISTENCE
    redis_key = f"tracking:transit_tracking:last_result:{test_user_id}"
    cached = await memory.get(redis_key)
    assert cached is not None
    assert "current_positions" in cached["comparison"]

@pytest.mark.asyncio
async def test_synthesis_trigger_integration(test_user_id, memory):
    """
    Verify that significant events trigger synthesis (mocking the orchestrator trigger only).
    """
    tracker = SolarTracker()
    
    # Mock Orchestrator trigger method ONLY, but use getter pattern
    # The code calls `get_orchestrator()`
    # We can patch 'src.app.modules.tracking.base.get_orchestrator' or 'src.app.core.memory.get_orchestrator'
    # BaseTrackingModule imports: `from app.core.memory import get_orchestrator` (Wait, did I use src.app in implementation?)
    
    # Looking at my implementation of `base.py`:
    # `from app.core.memory import get_orchestrator` (WITHOUT src)
    # This assumes `base.py` can import `app`. 
    # If standard is `src.app`, my IMPLEMENTATION might be wrong for runtime, OR
    # `src` is in path during runtime.
    
    # But for TEST, if we patch, we must match what's imported.
    # If `base.py` has `from app.core.memory...` then `src.app.modules.tracking.base.get_orchestrator` should act on it?
    # Or `app.core.memory`?
    
    # I'll try patching `src.app.core.memory.synthesis_orchestrator.SynthesisOrchestrator.trigger_synthesis`
    # This is patching the CLASS method, which affects all instances.
    
    # Patch get_orchestrator to return a mock
    # This ensures we capture calls made by the tracker
    with patch("app.core.memory.get_orchestrator", new_callable=AsyncMock) as mock_get_orch:
        mock_orch_instance = AsyncMock()
        mock_get_orch.return_value = mock_orch_instance

        # Inject condition: G5 Storm
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = [{"time_tag": "now", "kp_index": 8, "kp": "8o"}]
            
            mock_flares = AsyncMock()
            mock_flares.raise_for_status = MagicMock()
            mock_flares.json.return_value = []
            
            mock_get.return_value.__aenter__.side_effect = [mock_resp, mock_flares]
            
            # Run update
            result = await tracker.update(test_user_id)
            
            # Verify event
            assert "solar_storm" in result["significant_events"]
            
            # Verify trigger called
            assert mock_orch_instance.trigger_synthesis.called
            args = mock_orch_instance.trigger_synthesis.call_args[1] # kwargs
            assert args["trigger_type"] == SynthesisTrigger.SOLAR_STORM_DETECTED
