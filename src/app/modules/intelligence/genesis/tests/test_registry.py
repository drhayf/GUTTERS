"""
Tests for Uncertainty Registry

Verifies that the registry correctly manages extractors
and extracts uncertainties from multiple modules.
"""

from unittest.mock import AsyncMock, patch

import pytest

from ..declarations.astrology import AstrologyUncertaintyExtractor
from ..declarations.human_design import HumanDesignUncertaintyExtractor
from ..registry import UncertaintyRegistry


class TestUncertaintyRegistry:
    """Test suite for UncertaintyRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        UncertaintyRegistry.reset()
        yield
        UncertaintyRegistry.reset()

    def test_register_extractor(self):
        """Should register an extractor."""
        extractor = AstrologyUncertaintyExtractor()
        UncertaintyRegistry.register(extractor)

        assert "astrology" in UncertaintyRegistry.list_registered()

    def test_register_multiple_extractors(self):
        """Should register multiple extractors."""
        UncertaintyRegistry.register(AstrologyUncertaintyExtractor())
        UncertaintyRegistry.register(HumanDesignUncertaintyExtractor())

        registered = UncertaintyRegistry.list_registered()
        assert "astrology" in registered
        assert "human_design" in registered

    def test_get_extractor(self):
        """Should retrieve registered extractor."""
        extractor = AstrologyUncertaintyExtractor()
        UncertaintyRegistry.register(extractor)

        retrieved = UncertaintyRegistry.get_extractor("astrology")
        assert retrieved is extractor

    def test_get_nonexistent_extractor(self):
        """Should return None for unregistered module."""
        result = UncertaintyRegistry.get_extractor("nonexistent")
        assert result is None

    def test_unregister_extractor(self):
        """Should remove extractor from registry."""
        UncertaintyRegistry.register(AstrologyUncertaintyExtractor())
        assert "astrology" in UncertaintyRegistry.list_registered()

        result = UncertaintyRegistry.unregister("astrology")
        assert result is True
        assert "astrology" not in UncertaintyRegistry.list_registered()

    def test_initialize_default_extractors(self):
        """Should register all default extractors."""
        UncertaintyRegistry.initialize_default_extractors()

        registered = UncertaintyRegistry.list_registered()
        assert "astrology" in registered
        assert "human_design" in registered

    def test_initialize_is_idempotent(self):
        """Should only initialize once."""
        UncertaintyRegistry.initialize_default_extractors()
        UncertaintyRegistry.initialize_default_extractors()  # Should be no-op

        # Still should have same extractors
        assert len(UncertaintyRegistry.list_registered()) == 2


class TestExtractAll:
    """Test extract_all functionality."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Setup registry with extractors."""
        UncertaintyRegistry.reset()
        UncertaintyRegistry.register(AstrologyUncertaintyExtractor())
        UncertaintyRegistry.register(HumanDesignUncertaintyExtractor())
        yield
        UncertaintyRegistry.reset()

    @pytest.fixture
    def mock_results(self):
        """Mock calculation results from multiple modules."""
        return {
            "astrology": {
                "accuracy": "probabilistic",
                "rising_probabilities": [
                    {"sign": "Leo", "probability": 0.25, "hours_count": 6, "confidence": "low"},
                    {"sign": "Virgo", "probability": 0.75, "hours_count": 18, "confidence": "high"},
                ],
            },
            "human_design": {
                "accuracy": "probabilistic",
                "type_probabilities": [
                    {"value": "Generator", "probability": 0.90, "sample_count": 22, "confidence": "high"},
                    {"value": "Projector", "probability": 0.10, "sample_count": 2, "confidence": "low"},
                ],
            },
            "numerology": {
                "life_path": 7,
                "expression": 5,
                # Numerology has no uncertainties
            }
        }

    @pytest.mark.asyncio
    async def test_extract_all_modules(self, mock_results):
        """Should extract uncertainties from all registered modules."""
        with patch.object(UncertaintyRegistry, '_update_state_tracker', new_callable=AsyncMock):
            declarations = await UncertaintyRegistry.extract_all(
                results=mock_results,
                user_id=42,
                session_id="test-session"
            )

        # Should have 2 declarations (astrology + human_design)
        assert len(declarations) == 2

        modules = [d.module for d in declarations]
        assert "astrology" in modules
        assert "human_design" in modules

    @pytest.mark.asyncio
    async def test_extract_skips_unregistered_modules(self, mock_results):
        """Should skip modules without registered extractors."""
        # Numerology is in results but has no extractor
        with patch.object(UncertaintyRegistry, '_update_state_tracker', new_callable=AsyncMock):
            declarations = await UncertaintyRegistry.extract_all(
                results=mock_results,
                user_id=42,
                session_id="test-session"
            )

        # Should not have numerology
        modules = [d.module for d in declarations]
        assert "numerology" not in modules

    @pytest.mark.asyncio
    async def test_extract_handles_errors_gracefully(self):
        """Should continue extraction if one module fails."""
        # Create a result that will cause astrology to fail
        bad_results = {
            "astrology": None,  # Will raise error when accessing
            "human_design": {
                "accuracy": "probabilistic",
                "type_probabilities": [
                    {"value": "Generator", "probability": 0.90, "sample_count": 22, "confidence": "high"},
                ],
            }
        }

        with patch.object(UncertaintyRegistry, '_update_state_tracker', new_callable=AsyncMock):
            # Should not raise, should continue with human_design
            declarations = await UncertaintyRegistry.extract_all(
                results=bad_results,
                user_id=42,
                session_id="test-session"
            )

        # Should have at least human_design
        assert len(declarations) >= 1
