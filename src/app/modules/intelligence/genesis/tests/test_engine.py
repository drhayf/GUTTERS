"""
Tests for Genesis Engine

Verifies lifecycle methods and hypothesis management.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ..engine import GenesisEngine
from ..hypothesis import Hypothesis
from ..uncertainty import UncertaintyDeclaration, UncertaintyField


class TestHypothesisCreation:
    """Test initialize_from_uncertainties."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        engine = GenesisEngine()
        return engine

    @pytest.fixture
    def sample_declaration(self):
        """Create sample uncertainty declaration."""
        return UncertaintyDeclaration(
            module="astrology",
            user_id=42,
            session_id="test-session",
            source_accuracy="probabilistic",
            fields=[
                UncertaintyField(
                    field="rising_sign",
                    module="astrology",
                    candidates={
                        "Leo": 0.25,
                        "Virgo": 0.25,
                        "Libra": 0.25,
                        "Scorpio": 0.25,
                    },
                    confidence_threshold=0.80,
                    refinement_strategies=["morning_routine", "first_impression"],
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_creates_hypotheses_from_uncertainties(
        self, engine, sample_declaration
    ):
        """Should create one hypothesis per candidate."""
        hypotheses = await engine.initialize_from_uncertainties([sample_declaration])

        assert len(hypotheses) == 4  # 4 candidates

        values = {h.suspected_value for h in hypotheses}
        assert values == {"Leo", "Virgo", "Libra", "Scorpio"}

    @pytest.mark.asyncio
    async def test_hypothesis_inherits_confidence(
        self, engine, sample_declaration
    ):
        """Hypotheses should have initial confidence from candidate."""
        hypotheses = await engine.initialize_from_uncertainties([sample_declaration])

        for hyp in hypotheses:
            assert hyp.confidence == 0.25
            assert hyp.initial_confidence == 0.25

    @pytest.mark.asyncio
    async def test_hypotheses_stored_by_user(self, engine, sample_declaration):
        """Hypotheses should be stored under user_id."""
        await engine.initialize_from_uncertainties([sample_declaration])

        user_hyps = engine.get_hypotheses_for_user(42)
        assert len(user_hyps) == 4


class TestHypothesisSelection:
    """Test select_next_hypothesis."""

    @pytest.fixture
    def engine_with_hypotheses(self):
        """Create engine with pre-populated hypotheses."""
        engine = GenesisEngine()
        engine._hypotheses[42] = {
            "h1": Hypothesis(
                id="h1",
                field="rising_sign",
                module="astrology",
                suspected_value="Virgo",
                user_id=42,
                session_id="s",
                confidence=0.70,  # High - close to threshold
            ),
            "h2": Hypothesis(
                id="h2",
                field="rising_sign",
                module="astrology",
                suspected_value="Leo",
                user_id=42,
                session_id="s",
                confidence=0.25,  # Low
            ),
            "h3": Hypothesis(
                id="h3",
                field="rising_sign",
                module="astrology",
                suspected_value="Libra",
                user_id=42,
                session_id="s",
                confidence=0.85,  # Already confirmed (above threshold)
            ),
        }
        return engine

    @pytest.mark.asyncio
    async def test_selects_highest_priority(self, engine_with_hypotheses):
        """Should select hypothesis closest to threshold."""
        hyp = await engine_with_hypotheses.select_next_hypothesis(42)

        # h1 has 0.70 confidence - highest priority among those needing probing
        assert hyp is not None
        assert hyp.id == "h1"

    @pytest.mark.asyncio
    async def test_skips_confirmed_hypotheses(self, engine_with_hypotheses):
        """Should not select hypotheses above threshold."""
        hyp = await engine_with_hypotheses.select_next_hypothesis(42)

        # h3 has 0.85 (above 0.80), should be skipped
        assert hyp.id != "h3"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_candidates(self):
        """Should return None when no hypotheses need probing."""
        engine = GenesisEngine()
        engine._hypotheses[42] = {
            "h1": Hypothesis(
                id="h1",
                field="rising_sign",
                module="astrology",
                suspected_value="Virgo",
                user_id=42,
                session_id="s",
                confidence=0.90,  # Above threshold
            ),
        }

        hyp = await engine.select_next_hypothesis(42)

        assert hyp is None


class TestConfirmationDetection:
    """Test check_confirmations."""

    @pytest.fixture
    def engine_with_confirmed(self):
        """Create engine with hypothesis above threshold."""
        engine = GenesisEngine()
        engine.event_bus = MagicMock()
        engine.event_bus.publish = AsyncMock()

        engine._hypotheses[42] = {
            "h1": Hypothesis(
                id="h1",
                field="rising_sign",
                module="astrology",
                suspected_value="Virgo",
                user_id=42,
                session_id="s",
                confidence=0.85,  # Above threshold
            ),
            "h2": Hypothesis(
                id="h2",
                field="rising_sign",
                module="astrology",
                suspected_value="Leo",
                user_id=42,
                session_id="s",
                confidence=0.15,  # Below threshold
            ),
        }
        return engine

    @pytest.mark.asyncio
    async def test_detects_confirmation(self, engine_with_confirmed):
        """Should detect hypothesis at/above threshold."""
        confirmations = await engine_with_confirmed.check_confirmations(42)

        assert len(confirmations) == 1
        hyp, value = confirmations[0]
        assert value == "Virgo"
        assert hyp.resolved is True
        assert hyp.resolution_method == "confirmed"

    @pytest.mark.asyncio
    async def test_supersedes_competing_hypotheses(self, engine_with_confirmed):
        """Should mark other hypotheses for same field as superseded."""
        await engine_with_confirmed.check_confirmations(42)

        # Leo hypothesis should be superseded
        leo_hyp = engine_with_confirmed._hypotheses[42]["h2"]
        assert leo_hyp.resolved is True
        assert leo_hyp.resolution_method == "superseded"

    @pytest.mark.asyncio
    async def test_emits_confirmation_event(self, engine_with_confirmed):
        """Should emit GENESIS_FIELD_CONFIRMED event."""
        await engine_with_confirmed.check_confirmations(42)

        engine_with_confirmed.event_bus.publish.assert_called()


class TestQueryMethods:
    """Test hypothesis query methods."""

    @pytest.fixture
    def populated_engine(self):
        """Create engine with various hypothesis states."""
        engine = GenesisEngine()
        engine._hypotheses[42] = {
            "active": Hypothesis(
                id="active",
                field="type",
                module="human_design",
                suspected_value="Generator",
                user_id=42,
                session_id="s",
                confidence=0.50,
            ),
            "confirmed": Hypothesis(
                id="confirmed",
                field="type",
                module="human_design",
                suspected_value="Projector",
                user_id=42,
                session_id="s",
                confidence=0.85,
                resolved=True,
                resolution_method="confirmed",
            ),
            "refuted": Hypothesis(
                id="refuted",
                field="type",
                module="human_design",
                suspected_value="Manifestor",
                user_id=42,
                session_id="s",
                resolved=True,
                resolution_method="refuted",
            ),
        }
        return engine

    def test_get_all_hypotheses(self, populated_engine):
        """Should return all hypotheses for user."""
        all_hyps = populated_engine.get_hypotheses_for_user(42)
        assert len(all_hyps) == 3

    def test_get_active_hypotheses(self, populated_engine):
        """Should return only unresolved hypotheses."""
        active = populated_engine.get_active_hypotheses(42)
        assert len(active) == 1
        assert active[0].id == "active"

    def test_get_confirmed_hypotheses(self, populated_engine):
        """Should return only confirmed hypotheses."""
        confirmed = populated_engine.get_confirmed_hypotheses(42)
        assert len(confirmed) == 1
        assert confirmed[0].id == "confirmed"
