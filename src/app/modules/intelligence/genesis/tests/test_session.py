"""
Tests for Genesis Session Management

Verifies session lifecycle, probe ordering, and completion detection.
"""

import pytest
from datetime import datetime

from ..session import GenesisSession, GenesisSessionManager
from ..engine import GenesisEngine
from ..hypothesis import Hypothesis
from ..uncertainty import UncertaintyDeclaration, UncertaintyField
from ..probes import ProbeResponse, ProbeType


class TestGenesisSession:
    """Test GenesisSession model."""
    
    def test_create_session(self):
        """Should create session with defaults."""
        session = GenesisSession(
            user_id=42,
            probing_queue=["h1", "h2", "h3"]
        )
        
        assert session.user_id == 42
        assert session.state == "active"
        assert len(session.probing_queue) == 3
        assert session.total_probes_sent == 0
    
    def test_should_continue_active(self):
        """Active session with queue should continue."""
        session = GenesisSession(
            user_id=1,
            probing_queue=["h1"]
        )
        
        assert session.should_continue is True
    
    def test_should_not_continue_complete(self):
        """Complete session should not continue."""
        session = GenesisSession(
            user_id=1,
            probing_queue=["h1"],
            state="complete"
        )
        
        assert session.should_continue is False
    
    def test_should_not_continue_max_probes(self):
        """Session at max probes should not continue."""
        session = GenesisSession(
            user_id=1,
            probing_queue=["h1"],
            total_probes_sent=10,
            max_probes_per_session=10
        )
        
        assert session.should_continue is False
    
    def test_should_not_continue_empty_queue(self):
        """Session with empty queue should not continue."""
        session = GenesisSession(
            user_id=1,
            probing_queue=[]
        )
        
        assert session.should_continue is False
    
    def test_can_probe_field(self):
        """Should track field probe limits."""
        session = GenesisSession(
            user_id=1,
            fields_probed={"rising_sign": 2}
        )
        
        assert session.can_probe_field("rising_sign") is True
        session.fields_probed["rising_sign"] = 3
        assert session.can_probe_field("rising_sign") is False
    
    def test_record_probe_sent(self):
        """Should update state when probe sent."""
        session = GenesisSession(
            user_id=1,
            probing_queue=["h1"]
        )
        
        session.record_probe_sent("h1", "p1", "rising_sign")
        
        assert session.total_probes_sent == 1
        assert session.fields_probed["rising_sign"] == 1
        assert session.current_hypothesis_id == "h1"
        assert session.current_probe_id == "p1"
    
    def test_record_response(self):
        """Should update state when response received."""
        session = GenesisSession(user_id=1)
        
        session.record_response(confirmed_fields=["rising_sign"])
        
        assert session.total_responses == 1
        assert "rising_sign" in session.fields_confirmed
    
    def test_mark_complete(self):
        """Should mark session complete."""
        session = GenesisSession(user_id=1)
        
        session.mark_complete("finished")
        
        assert session.state == "complete"
        assert session.completed_at is not None
    
    def test_progress_percentage(self):
        """Should calculate progress correctly."""
        session = GenesisSession(
            user_id=1,
            total_probes_sent=5,
            max_probes_per_session=10
        )
        
        assert session.progress_percentage == 50.0


class TestGenesisSessionManager:
    """Test GenesisSessionManager."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh manager."""
        manager = GenesisSessionManager()
        manager._sessions = {}  # Reset
        return manager
    
    @pytest.fixture
    def engine_with_hypotheses(self):
        """Create engine with hypotheses."""
        engine = GenesisEngine()
        engine._hypotheses = {}
        engine._probes = {}
        
        engine._hypotheses[42] = {
            "h1": Hypothesis(
                id="h1",
                field="rising_sign",
                module="astrology",
                suspected_value="Virgo",
                user_id=42,
                session_id="s",
                confidence=0.25,
            ),
            "h2": Hypothesis(
                id="h2",
                field="rising_sign",
                module="astrology",
                suspected_value="Leo",
                user_id=42,
                session_id="s",
                confidence=0.25,
            ),
        }
        return engine
    
    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Should create new session."""
        session = await manager.create_session(42, ["h1", "h2"])
        
        assert session.user_id == 42
        assert len(session.probing_queue) == 2
        assert session.session_id in manager._sessions
    
    @pytest.mark.asyncio
    async def test_get_session(self, manager):
        """Should retrieve session by ID."""
        session = await manager.create_session(42, ["h1"])
        
        retrieved = await manager.get_session(session.session_id)
        
        assert retrieved is session
    
    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, manager, engine_with_hypotheses):
        """Should return existing active session."""
        first = await manager.create_session(42, ["h1"])
        
        retrieved, is_new = await manager.get_or_create_session(42, engine_with_hypotheses)
        
        assert retrieved is first
        assert is_new is False
    
    @pytest.mark.asyncio
    async def test_get_or_create_new(self, manager, engine_with_hypotheses):
        """Should create new session when none exists."""
        session, is_new = await manager.get_or_create_session(42, engine_with_hypotheses)
        
        assert session is not None
        assert is_new is True


class TestSessionProbeOrdering:
    """Test intelligent probe ordering."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh manager."""
        return GenesisSessionManager()
    
    @pytest.fixture
    def engine_with_priorities(self):
        """Create engine with hypotheses of different priorities."""
        engine = GenesisEngine()
        engine._hypotheses = {}
        engine._probes = {}
        
        engine._hypotheses[1] = {
            "high": Hypothesis(
                id="high",
                field="rising_sign",
                module="astrology",
                suspected_value="Virgo",
                user_id=1,
                session_id="s",
                confidence=0.70,  # Close to threshold = high priority
            ),
            "low": Hypothesis(
                id="low",
                field="rising_sign",
                module="astrology",
                suspected_value="Leo",
                user_id=1,
                session_id="s",
                confidence=0.10,  # Low confidence = lower priority
            ),
        }
        return engine
    
    @pytest.mark.asyncio
    async def test_selects_highest_priority(self, manager, engine_with_priorities):
        """Should select highest priority hypothesis."""
        session = await manager.create_session(1, ["high", "low"])
        
        probe = await manager.get_next_probe(session, engine_with_priorities)
        
        # Should have picked "high" (0.70 confidence = higher priority)
        assert probe is not None
        assert session.current_hypothesis_id == "high"
    
    @pytest.mark.asyncio
    async def test_respects_field_limit(self, manager, engine_with_priorities):
        """Should not exceed max probes per field."""
        session = await manager.create_session(1, ["high", "low"])
        session.fields_probed["rising_sign"] = 3  # At limit
        
        probe = await manager.get_next_probe(session, engine_with_priorities)
        
        # No hypotheses available (all are rising_sign)
        assert probe is None
