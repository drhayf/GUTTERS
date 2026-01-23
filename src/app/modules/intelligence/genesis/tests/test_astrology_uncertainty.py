"""
Tests for Astrology Uncertainty Extractor

Verifies that uncertainties are correctly extracted from
probabilistic astrology calculation results.
"""

import pytest
from datetime import datetime

from ..declarations.astrology import AstrologyUncertaintyExtractor
from ..uncertainty import UncertaintyField


class TestAstrologyUncertaintyExtractor:
    """Test suite for AstrologyUncertaintyExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return AstrologyUncertaintyExtractor()
    
    @pytest.fixture
    def probabilistic_result(self):
        """Mock probabilistic astrology result (birth time unknown)."""
        return {
            "accuracy": "probabilistic",
            "rising_probabilities": [
                {"sign": "Aries", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Taurus", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Gemini", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Cancer", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Leo", "probability": 0.125, "hours_count": 3, "confidence": "low"},
                {"sign": "Virgo", "probability": 0.125, "hours_count": 3, "confidence": "low"},
                {"sign": "Libra", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Scorpio", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Sagittarius", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Capricorn", "probability": 0.042, "hours_count": 1, "confidence": "low"},
                {"sign": "Aquarius", "probability": 0.083, "hours_count": 2, "confidence": "low"},
                {"sign": "Pisces", "probability": 0.042, "hours_count": 1, "confidence": "low"},
            ],
            "planet_stability": [
                {"planet": "Sun", "sign": "Taurus", "sign_stable": True, "house_range": (1, 12), "house_stable": False},
                {"planet": "Moon", "sign": "Scorpio", "sign_stable": True, "house_range": (6, 8), "house_stable": False},
                {"planet": "Mercury", "sign": "Taurus", "sign_stable": True, "house_range": (1, 12), "house_stable": False},
            ]
        }
    
    @pytest.fixture
    def full_accuracy_result(self):
        """Mock full accuracy result (birth time known)."""
        return {
            "accuracy": "full",
            "ascendant": {"sign": "Leo", "degree": 15.5},
            "rising_probabilities": None,
        }
    
    def test_can_extract_probabilistic(self, extractor, probabilistic_result):
        """Should return True for probabilistic results."""
        assert extractor.can_extract(probabilistic_result) is True
    
    def test_cannot_extract_full_accuracy(self, extractor, full_accuracy_result):
        """Should return False for full accuracy results."""
        assert extractor.can_extract(full_accuracy_result) is False
    
    def test_extract_rising_sign_uncertainty(self, extractor, probabilistic_result):
        """Should extract rising_sign uncertainty with correct candidates."""
        declaration = extractor.extract(
            result=probabilistic_result,
            user_id=42,
            session_id="test-session-123"
        )
        
        assert declaration is not None
        assert declaration.module == "astrology"
        assert declaration.user_id == 42
        assert declaration.session_id == "test-session-123"
        assert declaration.source_accuracy == "probabilistic"
        
        # Should have rising_sign field
        rising_field = declaration.get_field("rising_sign")
        assert rising_field is not None
        assert "Leo" in rising_field.candidates
        assert rising_field.candidates["Leo"] == 0.125
        assert rising_field.confidence_threshold == 0.80
    
    def test_refinement_strategies_attached(self, extractor, probabilistic_result):
        """Should include refinement strategies for rising_sign."""
        declaration = extractor.extract(probabilistic_result, 42, "sess")
        
        rising_field = declaration.get_field("rising_sign")
        assert len(rising_field.refinement_strategies) > 0
        assert "morning_routine" in rising_field.refinement_strategies
        assert "first_impression" in rising_field.refinement_strategies
    
    def test_no_declaration_for_empty_probabilities(self, extractor):
        """Should return None if no probabilities present."""
        result = {
            "accuracy": "probabilistic",
            "rising_probabilities": [],
        }
        
        declaration = extractor.extract(result, 42, "sess")
        assert declaration is None
    
    def test_uncertainty_field_properties(self, extractor, probabilistic_result):
        """Test UncertaintyField computed properties."""
        declaration = extractor.extract(probabilistic_result, 42, "sess")
        rising_field = declaration.get_field("rising_sign")
        
        # Current confidence should be max of candidates
        assert rising_field.current_confidence == 0.125
        
        # Should not be confirmed (0.125 < 0.80)
        assert rising_field.is_confirmed is False
        
        # Best candidate should be Leo or Virgo (both 0.125)
        assert rising_field.best_candidate in ("Leo", "Virgo")


class TestAstrologyIntegration:
    """Integration tests with actual calculation results."""
    
    def test_extract_from_real_calculation_structure(self):
        """Test with realistic nested structure."""
        extractor = AstrologyUncertaintyExtractor()
        
        # Simulating what NatalChartResult.model_dump() would produce
        result = {
            "subject": {
                "name": "Test User",
                "birth_data": {"date": "1990-05-15", "time": None}
            },
            "accuracy": "probabilistic",
            "rising_confidence": 0.125,
            "rising_probabilities": [
                {"sign": "Leo", "probability": 0.25, "hours_count": 6, "confidence": "low"},
                {"sign": "Virgo", "probability": 0.25, "hours_count": 6, "confidence": "low"},
                {"sign": "Libra", "probability": 0.25, "hours_count": 6, "confidence": "low"},
                {"sign": "Scorpio", "probability": 0.25, "hours_count": 6, "confidence": "low"},
            ],
            "planet_stability": None,
            "aspect_stability": None,
        }
        
        declaration = extractor.extract(result, 1, "session-1")
        
        assert declaration is not None
        assert len(declaration.fields) == 1
        assert declaration.fields[0].field == "rising_sign"
        assert len(declaration.fields[0].candidates) == 4
