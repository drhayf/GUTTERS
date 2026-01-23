"""
Tests for Human Design Uncertainty Extractor

Verifies that uncertainties are correctly extracted from
probabilistic Human Design calculation results.
"""

import pytest

from ..declarations.human_design import HumanDesignUncertaintyExtractor


class TestHumanDesignUncertaintyExtractor:
    """Test suite for HumanDesignUncertaintyExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return HumanDesignUncertaintyExtractor()
    
    @pytest.fixture
    def probabilistic_result(self):
        """Mock probabilistic HD result (birth time unknown)."""
        return {
            "type": "Projector",  # Best guess
            "strategy": "Wait for the invitation",
            "authority": "Splenic",
            "profile": "1/3",
            "accuracy": "probabilistic",
            "type_confidence": 0.58,
            "type_probabilities": [
                {"value": "Projector", "probability": 0.58, "sample_count": 14, "confidence": "medium"},
                {"value": "Generator", "probability": 0.33, "sample_count": 8, "confidence": "low"},
                {"value": "Manifestor", "probability": 0.08, "sample_count": 2, "confidence": "low"},
            ],
            "planet_stability": [
                {"planet": "Sun", "gate": 35, "line": 6, "stable": True},
                {"planet": "Earth", "gate": 5, "line": 6, "stable": True},
                {"planet": "Moon", "gate": 29, "line": 4, "stable": False, "variation": "Lines 3-5"},
            ]
        }
    
    @pytest.fixture
    def full_accuracy_result(self):
        """Mock full accuracy result (birth time known)."""
        return {
            "type": "Projector",
            "accuracy": "full",
            "type_probabilities": None,
        }
    
    def test_can_extract_probabilistic(self, extractor, probabilistic_result):
        """Should return True for probabilistic results."""
        assert extractor.can_extract(probabilistic_result) is True
    
    def test_cannot_extract_full_accuracy(self, extractor, full_accuracy_result):
        """Should return False for full accuracy results."""
        assert extractor.can_extract(full_accuracy_result) is False
    
    def test_extract_type_uncertainty(self, extractor, probabilistic_result):
        """Should extract type uncertainty with correct candidates."""
        declaration = extractor.extract(
            result=probabilistic_result,
            user_id=42,
            session_id="test-session-456"
        )
        
        assert declaration is not None
        assert declaration.module == "human_design"
        assert declaration.user_id == 42
        assert declaration.session_id == "test-session-456"
        assert declaration.source_accuracy == "probabilistic"
        
        # Should have type field
        type_field = declaration.get_field("type")
        assert type_field is not None
        assert "Projector" in type_field.candidates
        assert type_field.candidates["Projector"] == 0.58
        assert "Generator" in type_field.candidates
        assert type_field.candidates["Generator"] == 0.33
    
    def test_refinement_strategies_attached(self, extractor, probabilistic_result):
        """Should include refinement strategies for type."""
        declaration = extractor.extract(probabilistic_result, 42, "sess")
        
        type_field = declaration.get_field("type")
        assert len(type_field.refinement_strategies) > 0
        assert "energy_pattern" in type_field.refinement_strategies
        assert "decision_style" in type_field.refinement_strategies
    
    def test_no_declaration_for_empty_probabilities(self, extractor):
        """Should return None if no probabilities present."""
        result = {
            "accuracy": "probabilistic",
            "type_probabilities": [],
        }
        
        declaration = extractor.extract(result, 42, "sess")
        assert declaration is None
    
    def test_type_field_properties(self, extractor, probabilistic_result):
        """Test UncertaintyField computed properties for HD type."""
        declaration = extractor.extract(probabilistic_result, 42, "sess")
        type_field = declaration.get_field("type")
        
        # Current confidence should be max (Projector at 0.58)
        assert type_field.current_confidence == 0.58
        
        # Should not be confirmed (0.58 < 0.80)
        assert type_field.is_confirmed is False
        
        # Best candidate should be Projector
        assert type_field.best_candidate == "Projector"


class TestHumanDesignWithPydanticModel:
    """Test extractor with actual Pydantic model input."""
    
    def test_extract_from_pydantic_model(self):
        """Test extraction when given HumanDesignChart model."""
        try:
            from ....calculation.human_design.schemas import (
                HumanDesignChart,
                TypeProbability,
            )
            
            # Create actual Pydantic model
            chart = HumanDesignChart(
                type="Generator",
                strategy="Wait to respond",
                authority="Sacral",
                profile="3/5",
                accuracy="probabilistic",
                type_confidence=0.75,
                type_probabilities=[
                    TypeProbability(
                        value="Generator",
                        probability=0.75,
                        sample_count=18,
                        confidence="high"
                    ),
                    TypeProbability(
                        value="Manifesting Generator",
                        probability=0.25,
                        sample_count=6,
                        confidence="low"
                    ),
                ]
            )
            
            extractor = HumanDesignUncertaintyExtractor()
            declaration = extractor.extract(chart, 1, "sess")
            
            assert declaration is not None
            type_field = declaration.get_field("type")
            assert type_field.candidates["Generator"] == 0.75
            assert type_field.current_confidence == 0.75
            
        except ImportError:
            pytest.skip("HumanDesignChart schema not available")
