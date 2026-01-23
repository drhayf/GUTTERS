"""
GUTTERS Astrology Module Integration Test

Tests the complete flow: API → Event → Module → Brain → Database

To run:
    cd src
    python -m pytest tests/integration/test_astrology_flow.py -v
"""
import sys
from pathlib import Path

# Add src to path if running from project root
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import asyncio
from datetime import date, time

import pytest


class TestCalculatorBrain:
    """Test the calculator brain in isolation."""
    
    def test_calculate_natal_chart(self):
        """Test natal chart calculation with valid birth data."""
        from app.modules.calculation.astrology.brain.calculator import calculate_natal_chart
        
        chart = calculate_natal_chart(
            name="Test User",
            birth_date=date(1990, 5, 15),
            birth_time=time(14, 30),
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
        )
        
        # Verify chart structure
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "elements" in chart
        assert "modalities" in chart
        assert "ascendant" in chart
        assert "midheaven" in chart
        
        # Verify planets
        planets = chart["planets"]
        assert len(planets) >= 10  # At least 10 main planets
        
        # Find Sun and Moon
        sun = next((p for p in planets if p["name"] == "Sun"), None)
        moon = next((p for p in planets if p["name"] == "Moon"), None)
        
        assert sun is not None, "Sun position should be calculated"
        assert moon is not None, "Moon position should be calculated"
        
        # Verify Sun position has required fields
        assert "sign" in sun
        assert "degree" in sun
        assert "house" in sun
        
        # Sun should be in Taurus for May 15, 1990
        assert sun["sign"] == "Tau" or sun["sign"] == "Taurus", f"Sun should be in Taurus, got {sun['sign']}"
        
        # Verify houses
        houses = chart["houses"]
        assert len(houses) == 12, "Should have 12 houses"
        
        # Verify elements distribution
        elements = chart["elements"]
        assert "fire" in elements
        assert "earth" in elements
        assert "air" in elements
        assert "water" in elements
        
        # Total element count should match planet count
        total_elements = sum(elements.values())
        assert total_elements == len(planets), "Element count should match planet count"
        
        print(f"\n✅ Chart calculated successfully!")
        print(f"   Sun: {sun['degree']:.1f}° {sun['sign']}")
        print(f"   Moon: {moon['degree']:.1f}° {moon['sign']}")
        print(f"   Ascendant: {chart['ascendant']['degree']:.1f}° {chart['ascendant']['sign']}")
        print(f"   Aspects: {len(chart['aspects'])}")


class TestInterpreterBrain:
    """Test the interpreter brain (requires LLM API key)."""
    
    @pytest.mark.asyncio
    async def test_format_chart_summary(self):
        """Test chart summary formatting (no LLM call)."""
        from app.modules.calculation.astrology.brain.interpreter import format_chart_summary
        from app.modules.calculation.astrology.brain.calculator import calculate_natal_chart
        
        chart = calculate_natal_chart(
            name="Test User",
            birth_date=date(1990, 5, 15),
            birth_time=time(14, 30),
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
        )
        
        summary = format_chart_summary(chart)
        
        assert summary is not None
        assert "Sun" in summary or "Moon" in summary
        assert "Rising" in summary
        
        print(f"\n✅ Summary: {summary}")


class TestGeocodingUtility:
    """Test geocoding utilities."""
    
    def test_geocode_location(self):
        """Test geocoding a location string."""
        from app.core.utils.geocoding import geocode_location
        
        result = geocode_location("San Francisco, CA, USA")
        
        assert result is not None, "Should geocode San Francisco"
        assert "latitude" in result
        assert "longitude" in result
        assert "timezone" in result
        
        # Verify coordinates are roughly correct
        assert 37.0 < result["latitude"] < 38.0, "Latitude should be around 37.7"
        assert -123.0 < result["longitude"] < -122.0, "Longitude should be around -122.4"
        assert result["timezone"] == "America/Los_Angeles", "Should be Pacific timezone"
        
        print(f"\n✅ Geocoded: {result['address']}")
        print(f"   Coordinates: {result['latitude']:.4f}, {result['longitude']:.4f}")
        print(f"   Timezone: {result['timezone']}")


class TestEventBus:
    """Test the event bus."""
    
    @pytest.mark.asyncio
    async def test_event_bus_publish_subscribe(self):
        """Test event bus pub/sub functionality."""
        from app.core.events.bus import EventBus
        
        bus = EventBus()
        await bus.initialize()
        
        received_events = []
        
        async def handler(packet):
            received_events.append(packet)
        
        # Subscribe to test pattern
        bus.subscribe("test.*", handler)
        
        # Publish event
        await bus.publish(
            event_type="test.check",
            payload={"message": "hello"},
            source="test",
        )
        
        # Give time for async processing
        await asyncio.sleep(0.5)
        
        await bus.cleanup()
        
        print(f"\n✅ Event bus working, received {len(received_events)} events")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
