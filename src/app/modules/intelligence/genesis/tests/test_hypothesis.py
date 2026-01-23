"""
Tests for Hypothesis Model

Verifies hypothesis creation, priority calculation, and state management.
"""

import pytest
from datetime import datetime, timezone

from ..hypothesis import Hypothesis, CORE_FIELDS


class TestHypothesisCreation:
    """Test hypothesis creation and defaults."""
    
    def test_create_basic_hypothesis(self):
        """Should create hypothesis with required fields."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=42,
            session_id="test-session",
        )
        
        assert hyp.field == "rising_sign"
        assert hyp.module == "astrology"
        assert hyp.suspected_value == "Virgo"
        assert hyp.user_id == 42
        assert hyp.id is not None
        assert len(hyp.id) == 8
    
    def test_default_confidence_values(self):
        """Should initialize with correct defaults."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Projector",
            user_id=1,
            session_id="s",
        )
        
        assert hyp.confidence == 0.0
        assert hyp.initial_confidence == 0.0
        assert hyp.confidence_threshold == 0.80
        assert hyp.probes_attempted == 0
        assert hyp.max_probes == 3
        assert not hyp.resolved
    
    def test_create_with_initial_confidence(self):
        """Should accept initial confidence."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Leo",
            user_id=1,
            session_id="s",
            confidence=0.125,
            initial_confidence=0.125,
        )
        
        assert hyp.confidence == 0.125
        assert hyp.initial_confidence == 0.125


class TestHypothesisPriority:
    """Test priority calculation."""
    
    def test_high_confidence_high_priority(self):
        """Hypothesis close to threshold should have high priority."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            confidence=0.75,  # Close to 0.80 threshold
        )
        
        assert hyp.priority >= 0.6  # High priority
    
    def test_core_field_boost(self):
        """Core fields should get priority boost."""
        core_hyp = Hypothesis(
            field="rising_sign",  # Core field
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            confidence=0.3,
        )
        
        non_core_hyp = Hypothesis(
            field="house_placements",  # Not core
            module="astrology",
            suspected_value="variable",
            user_id=1,
            session_id="s",
            confidence=0.3,
        )
        
        assert core_hyp.priority > non_core_hyp.priority
    
    def test_resolved_hypothesis_zero_priority(self):
        """Resolved hypotheses should have zero priority."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            confidence=0.5,
            resolved=True,
        )
        
        assert hyp.priority == 0.0
    
    def test_fresh_hypothesis_priority_boost(self):
        """Hypotheses with fewer probes should have higher priority."""
        fresh = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.4,
            probes_attempted=0,
        )
        
        probed = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Projector",
            user_id=1,
            session_id="s",
            confidence=0.4,
            probes_attempted=2,
        )
        
        assert fresh.priority > probed.priority


class TestNeedsProbing:
    """Test needs_probing computed property."""
    
    def test_needs_probing_default(self):
        """Fresh hypothesis needs probing."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
        )
        
        assert hyp.needs_probing is True
    
    def test_resolved_doesnt_need_probing(self):
        """Resolved hypothesis doesn't need probing."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            resolved=True,
        )
        
        assert hyp.needs_probing is False
    
    def test_confirmed_doesnt_need_probing(self):
        """Hypothesis at threshold doesn't need probing."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            confidence=0.85,  # Above 0.80 threshold
        )
        
        assert hyp.needs_probing is False
    
    def test_max_probes_doesnt_need_probing(self):
        """Hypothesis at max probes doesn't need probing."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
            probes_attempted=3,
            max_probes=3,
        )
        
        assert hyp.needs_probing is False


class TestConfidenceUpdates:
    """Test confidence update methods."""
    
    def test_update_confidence_positive(self):
        """Should increase confidence by delta."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.5,
        )
        
        new_conf = hyp.update_confidence(0.15)
        
        assert new_conf == 0.65
        assert hyp.confidence == 0.65
    
    def test_update_confidence_negative(self):
        """Should decrease confidence by delta."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.5,
        )
        
        new_conf = hyp.update_confidence(-0.2)
        
        assert new_conf == 0.3
        assert hyp.confidence == 0.3
    
    def test_confidence_clamped_at_one(self):
        """Confidence should not exceed 1.0."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.9,
        )
        
        new_conf = hyp.update_confidence(0.5)
        
        assert new_conf == 1.0
        assert hyp.confidence == 1.0
    
    def test_confidence_clamped_at_zero(self):
        """Confidence should not go below 0.0."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.1,
        )
        
        new_conf = hyp.update_confidence(-0.5)
        
        assert new_conf == 0.0
        assert hyp.confidence == 0.0


class TestEvidenceTracking:
    """Test evidence and contradiction tracking."""
    
    def test_add_evidence(self):
        """Should add evidence to list."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
        )
        
        hyp.add_evidence("Morning routine matches Virgo")
        
        assert len(hyp.evidence) == 1
        assert "Virgo" in hyp.evidence[0]
    
    def test_add_contradiction(self):
        """Should add contradiction to list."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
        )
        
        hyp.add_contradiction("Energy pattern doesn't match")
        
        assert len(hyp.contradictions) == 1
    
    def test_evidence_affects_priority(self):
        """More evidence should boost priority."""
        with_evidence = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=1,
            session_id="s",
            confidence=0.4,
            evidence=["Evidence 1", "Evidence 2"],
        )
        
        no_evidence = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Projector",
            user_id=1,
            session_id="s",
            confidence=0.4,
        )
        
        assert with_evidence.priority > no_evidence.priority


class TestResolution:
    """Test hypothesis resolution."""
    
    def test_resolve_confirmed(self):
        """Should mark as confirmed."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
        )
        
        hyp.resolve("confirmed")
        
        assert hyp.resolved is True
        assert hyp.resolution_method == "confirmed"
    
    def test_resolve_refuted(self):
        """Should mark as refuted."""
        hyp = Hypothesis(
            field="rising_sign",
            module="astrology",
            suspected_value="Virgo",
            user_id=1,
            session_id="s",
        )
        
        hyp.resolve("refuted")
        
        assert hyp.resolved is True
        assert hyp.resolution_method == "refuted"


class TestSerialization:
    """Test storage serialization."""
    
    def test_to_storage_dict(self):
        """Should serialize to dict for JSONB storage."""
        hyp = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=42,
            session_id="sess-123",
            confidence=0.65,
        )
        
        data = hyp.to_storage_dict()
        
        assert data["field"] == "type"
        assert data["module"] == "human_design"
        assert data["user_id"] == 42
        assert isinstance(data["created_at"], str)  # ISO format
    
    def test_from_storage_dict(self):
        """Should deserialize from dict."""
        original = Hypothesis(
            field="type",
            module="human_design",
            suspected_value="Generator",
            user_id=42,
            session_id="sess-123",
            confidence=0.65,
        )
        
        data = original.to_storage_dict()
        restored = Hypothesis.from_storage_dict(data)
        
        assert restored.field == original.field
        assert restored.user_id == original.user_id
        assert restored.confidence == original.confidence
