"""
Tests for Council of Systems Enhancements (Phase 26.1 Quick Wins).

Tests:
- LineInterpretation dataclass
- Enhanced GateData with line interpretations
- Gate history analysis
- Context-aware guidance generation
- Line-specific API endpoints
- Observer line correlation detection
- Hypothesis line evidence tracking
- Line-specific notifications
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.modules.intelligence.council.service import CouncilService
from src.app.modules.intelligence.hypothesis.models import Hypothesis, HypothesisStatus, HypothesisType
from src.app.modules.intelligence.iching.kernel import GATE_DATABASE, LineInterpretation
from src.app.modules.intelligence.observer.cyclical import CyclicalPatternDetector, CyclicalPatternType

# =============================================================================
# SECTION 1: LineInterpretation and Enhanced GateData Tests
# =============================================================================

class TestLineInterpretation:
    """Test LineInterpretation dataclass."""

    def test_line_interpretation_creation(self):
        """Test creating a LineInterpretation."""
        line = LineInterpretation(
            number=1,
            name="Investigator",
            keynote="Foundation through Introspection",
            description="Seeks security through knowledge.",
            exaltation="Mars - Disciplined energy",
            detriment="Venus - Superficial charm"
        )

        assert line.number == 1
        assert line.name == "Investigator"
        assert "Introspection" in line.keynote
        assert "knowledge" in line.description
        assert line.exaltation is not None
        assert line.detriment is not None


class TestEnhancedGateData:
    """Test enhanced GateData with line interpretations."""

    def test_gate_1_has_line_interpretations(self):
        """Test Gate 1 has all 6 line interpretations."""
        gate_1 = GATE_DATABASE.get(1)

        assert gate_1 is not None
        assert hasattr(gate_1, 'lines')
        assert len(gate_1.lines) == 6

        # Check each line
        for line_num in range(1, 7):
            assert line_num in gate_1.lines
            line = gate_1.lines[line_num]
            assert isinstance(line, LineInterpretation)
            assert line.number == line_num
            assert line.name is not None
            assert line.keynote is not None
            assert line.description is not None

    def test_gate_1_has_harmonious_gates(self):
        """Test Gate 1 has harmonious gate relationships."""
        gate_1 = GATE_DATABASE.get(1)

        assert hasattr(gate_1, 'harmonious_gates')
        assert isinstance(gate_1.harmonious_gates, list)
        assert len(gate_1.harmonious_gates) > 0
        # Gate 1 should harmonize with Gates 8, 13, etc.
        assert 8 in gate_1.harmonious_gates
        assert 13 in gate_1.harmonious_gates

    def test_gate_1_has_challenging_gates(self):
        """Test Gate 1 has challenging gate relationships."""
        gate_1 = GATE_DATABASE.get(1)

        assert hasattr(gate_1, 'challenging_gates')
        assert isinstance(gate_1.challenging_gates, list)
        assert len(gate_1.challenging_gates) > 0
        # Gate 1 should have tension with Gates 2, 14, etc.
        assert 2 in gate_1.challenging_gates

    def test_gate_1_has_keywords(self):
        """Test Gate 1 has keywords."""
        gate_1 = GATE_DATABASE.get(1)

        assert hasattr(gate_1, 'keywords')
        assert isinstance(gate_1.keywords, list)
        assert len(gate_1.keywords) > 0
        assert "creativity" in gate_1.keywords
        assert "self-expression" in gate_1.keywords


# =============================================================================
# SECTION 2: CouncilService Enhancement Tests
# =============================================================================

class TestCouncilServiceEnhancements:
    """Test enhanced CouncilService methods."""

    def test_get_gate_info_without_line(self):
        """Test get_gate_info without line parameter."""
        service = CouncilService()
        gate_info = service.get_gate_info(1)

        assert gate_info is not None
        assert gate_info.get("gate_number") == 1
        assert "hd_name" in gate_info
        assert "gene_key_gift" in gate_info
        assert "line_interpretation" not in gate_info  # No line requested

    def test_get_gate_info_with_line(self):
        """Test get_gate_info with line parameter."""
        service = CouncilService()
        gate_info = service.get_gate_info(1, line_number=4)

        assert gate_info is not None
        assert gate_info.get("gate_number") == 1
        assert "line_interpretation" in gate_info

        line_data = gate_info["line_interpretation"]
        assert line_data["number"] == 4
        assert line_data["name"] == "Opportunist"
        assert "keynote" in line_data
        assert "description" in line_data
        assert "exaltation" in line_data
        assert "detriment" in line_data

    def test_get_gate_info_invalid_line(self):
        """Test get_gate_info with invalid line number."""
        service = CouncilService()
        gate_info = service.get_gate_info(1, line_number=7)  # Invalid line

        # Should return gate info without line data
        assert gate_info is not None
        assert "line_interpretation" not in gate_info

    @pytest.mark.asyncio
    async def test_analyze_gate_history_no_entries(self):
        """Test analyze_gate_history with no journal entries."""
        service = CouncilService()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        history = await service.analyze_gate_history(1, 13, mock_db)

        assert history is not None
        assert history["gate_number"] == 13
        assert history["occurrences"] == 0
        assert history["sample_entries"] == []

    @pytest.mark.asyncio
    async def test_analyze_gate_history_with_entries(self):
        """Test analyze_gate_history with journal entries."""
        service = CouncilService()

        # Mock journal entries during Gate 13
        mock_entries = [
            MagicMock(
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                content="Feeling introspective",
                mood_score=7.5,
                energy_score=6.0
            ),
            MagicMock(
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
                content="Listening to others",
                mood_score=8.0,
                energy_score=7.0
            ),
        ]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_entries
        mock_db.execute.return_value = mock_result

        history = await service.analyze_gate_history(1, 13, mock_db)

        assert history is not None
        assert history["gate_number"] == 13
        assert history["occurrences"] >= 2
        assert "mood_analysis" in history
        assert "energy_analysis" in history
        assert "line_distribution" in history
        assert len(history["sample_entries"]) > 0

    @pytest.mark.asyncio
    async def test_generate_context_aware_guidance_basic(self):
        """Test generate_context_aware_guidance with basic context."""
        service = CouncilService()

        mock_synthesis = MagicMock()
        mock_synthesis.resonance_type = "harmonious"
        mock_synthesis.macro_keynote = "Test theme"
        mock_synthesis.micro_keynote = "Micro theme"
        mock_synthesis.daily_code.sun_activation.gate = 13
        mock_synthesis.daily_code.sun_activation.line = 4

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        guidance = await service.generate_context_aware_guidance(1, mock_synthesis, mock_db)

        assert guidance is not None
        assert isinstance(guidance, list)
        assert len(guidance) > 0
        # Should have at least baseline guidance
        assert any("harmonious" in g.lower() for g in guidance)


# =============================================================================
# SECTION 3: Observer Line Correlation Tests
# =============================================================================

class TestObserverLineCorrelations:
    """Test Observer line-specific pattern detection."""

    @pytest.mark.asyncio
    async def test_detect_gate_line_correlations_insufficient_data(self):
        """Test line correlation detection with insufficient data."""
        detector = CyclicalPatternDetector()

        mock_db = AsyncMock()

        # Mock insufficient journal entries
        with patch.object(detector, '_get_all_journal_entries', return_value=[]):
            patterns = await detector.detect_gate_line_correlations(1, mock_db)

        assert patterns == []

    @pytest.mark.asyncio
    async def test_detect_gate_line_correlations_with_data(self):
        """Test line correlation detection with sufficient data."""
        detector = CyclicalPatternDetector()

        mock_db = AsyncMock()

        # Mock 150 journal entries across different lines
        mock_entries = []
        base_time = datetime(2024, 1, 1, tzinfo=UTC)

        for i in range(150):
            # Create entries with varying moods
            # Line 3 gets lower moods (testing martyr energy)
            entry_time = base_time + timedelta(hours=i * 4)  # ~22.5 hours per line
            mood_score = 5.0 if (i % 6) == 2 else 7.5  # Line 3 (index 2) has lower mood

            mock_entries.append({
                "created_at": entry_time,
                "mood_score": mood_score,
                "content": f"Entry {i}"
            })

        with patch.object(detector, '_get_all_journal_entries', return_value=mock_entries):
            patterns = await detector.detect_gate_line_correlations(1, mock_db)

        # Should detect at least one line correlation
        assert len(patterns) > 0

        # Check pattern structure
        pattern = patterns[0]
        assert pattern.pattern_type == CyclicalPatternType.GATE_LINE_CORRELATION
        assert pattern.gate_line is not None
        assert 1 <= pattern.gate_line <= 6
        assert pattern.metric == "mood_score"
        assert pattern.metric_value is not None
        assert pattern.baseline_value is not None


# =============================================================================
# SECTION 4: Hypothesis Line Evidence Tests
# =============================================================================

class TestHypothesisLineEvidence:
    """Test Hypothesis line-level evidence tracking."""

    def test_hypothesis_has_line_evidence_count(self):
        """Test Hypothesis model has line_evidence_count field."""
        hyp = Hypothesis(
            id="test-123",
            user_id=1,
            hypothesis_type=HypothesisType.BEHAVIORAL_PATTERN,
            claim="Test hypothesis",
            predicted_value="Test value",
            confidence=0.5,
            status=HypothesisStatus.FORMING,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC)
        )

        assert hasattr(hyp, 'line_evidence_count')
        assert isinstance(hyp.line_evidence_count, dict)
        assert len(hyp.line_evidence_count) == 0

    def test_track_hexagram_evidence_with_lines(self):
        """Test tracking hexagram evidence with line information."""
        hyp = Hypothesis(
            id="test-123",
            user_id=1,
            hypothesis_type=HypothesisType.BEHAVIORAL_PATTERN,
            claim="Test hypothesis",
            predicted_value="Test value",
            confidence=0.5,
            status=HypothesisStatus.FORMING,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC)
        )

        # Track evidence with gate and line
        hyp.track_hexagram_evidence(sun_gate=13, earth_gate=7, sun_line=4, earth_line=4)

        # Check gate-level tracking
        assert "Gate 13" in hyp.gate_evidence_count
        assert hyp.gate_evidence_count["Gate 13"] == 1
        assert "Gate 7 (Earth)" in hyp.gate_evidence_count
        assert hyp.gate_evidence_count["Gate 7 (Earth)"] == 1

        # Check line-level tracking
        assert "Gate 13.Line 4" in hyp.line_evidence_count
        assert hyp.line_evidence_count["Gate 13.Line 4"] == 1
        assert "Gate 7.Line 4 (Earth)" in hyp.line_evidence_count
        assert hyp.line_evidence_count["Gate 7.Line 4 (Earth)"] == 1

    def test_track_hexagram_evidence_multiple_calls(self):
        """Test tracking evidence across multiple calls."""
        hyp = Hypothesis(
            id="test-123",
            user_id=1,
            hypothesis_type=HypothesisType.BEHAVIORAL_PATTERN,
            claim="Test hypothesis",
            predicted_value="Test value",
            confidence=0.5,
            status=HypothesisStatus.FORMING,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC)
        )

        # Track evidence multiple times
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=4)
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=4)
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=5)

        # Check accumulation
        assert hyp.gate_evidence_count["Gate 13"] == 3
        assert hyp.line_evidence_count["Gate 13.Line 4"] == 2
        assert hyp.line_evidence_count["Gate 13.Line 5"] == 1

    def test_get_dominant_line(self):
        """Test get_dominant_line method."""
        hyp = Hypothesis(
            id="test-123",
            user_id=1,
            hypothesis_type=HypothesisType.BEHAVIORAL_PATTERN,
            claim="Test hypothesis",
            predicted_value="Test value",
            confidence=0.5,
            status=HypothesisStatus.FORMING,
            generated_at=datetime.now(UTC),
            last_updated=datetime.now(UTC)
        )

        # No evidence yet
        assert hyp.get_dominant_line() is None

        # Add evidence
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=4)
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=4)
        hyp.track_hexagram_evidence(sun_gate=13, sun_line=5)
        hyp.track_hexagram_evidence(sun_gate=7, sun_line=2)

        # Line 4 should be dominant (2 occurrences)
        assert hyp.get_dominant_line() == "Gate 13.Line 4"


# =============================================================================
# SECTION 5: Integration Tests
# =============================================================================

class TestEnhancementsIntegration:
    """Test integration of all enhancements."""

    def test_gate_1_complete_structure(self):
        """Test Gate 1 has complete enhanced structure."""
        gate_1 = GATE_DATABASE.get(1)

        # Check all enhanced fields
        assert hasattr(gate_1, 'lines')
        assert hasattr(gate_1, 'harmonious_gates')
        assert hasattr(gate_1, 'challenging_gates')
        assert hasattr(gate_1, 'keywords')

        # Check original fields still exist
        assert hasattr(gate_1, 'hd_name')
        assert hasattr(gate_1, 'gene_key_shadow')
        assert hasattr(gate_1, 'gene_key_gift')
        assert hasattr(gate_1, 'gene_key_siddhi')

    def test_gate_13_complete_structure(self):
        """Test Gate 13 has complete enhanced structure."""
        gate_13 = GATE_DATABASE.get(13)

        # Check all enhanced fields
        assert len(gate_13.lines) == 6
        assert len(gate_13.harmonious_gates) > 0
        assert len(gate_13.challenging_gates) > 0
        assert len(gate_13.keywords) > 0

        # Check specific harmonious relationships
        assert 1 in gate_13.harmonious_gates
        assert 7 in gate_13.harmonious_gates

    @pytest.mark.asyncio
    async def test_full_synthesis_with_line_data(self):
        """Test full synthesis includes line-specific data."""
        service = CouncilService()

        synthesis = service.get_council_synthesis()

        assert synthesis is not None
        assert synthesis.daily_code.sun_activation.line is not None
        assert 1 <= synthesis.daily_code.sun_activation.line <= 6

    def test_line_archetype_consistency(self):
        """Test line archetypes are consistent across gates."""
        from src.app.modules.intelligence.iching.kernel import LINE_ARCHETYPES

        # Check all 6 line archetypes exist
        assert len(LINE_ARCHETYPES) == 6

        for line_num in range(1, 7):
            archetype = LINE_ARCHETYPES[line_num]
            assert archetype.number == line_num
            assert archetype.name is not None
            assert archetype.theme is not None
            assert archetype.profile_role is not None
            assert archetype.description is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
