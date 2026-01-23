"""
Genesis Session Management

Tracks conversational state across multiple probes.
Provides intelligent ordering and completion detection.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .engine import GenesisEngine
from .hypothesis import Hypothesis
from .probes import ProbePacket, ProbeResponse


class GenesisSession(BaseModel):
    """
    A conversational refinement session.
    
    Tracks state across multiple probe-response cycles,
    enforces limits, and detects completion.
    """
    
    # Identity
    session_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    user_id: int
    
    # State
    state: Literal["active", "paused", "complete"] = "active"
    
    # Conversation tracking
    total_probes_sent: int = 0
    total_responses: int = 0
    current_hypothesis_id: str | None = None
    current_probe_id: str | None = None
    probing_queue: list[str] = Field(default_factory=list)
    
    # Strategy / Limits
    max_probes_per_session: int = 10
    max_probes_per_field: int = 3
    fields_probed: dict[str, int] = Field(default_factory=dict)
    
    # Completion
    target_confidence: float = 0.80
    fields_confirmed: list[str] = Field(default_factory=list)
    fields_exhausted: list[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    
    @property
    def should_continue(self) -> bool:
        """Should we continue probing?"""
        if self.state != "active":
            return False
        if self.total_probes_sent >= self.max_probes_per_session:
            return False
        if len(self.probing_queue) == 0:
            return False
        return True
    
    @property
    def progress_percentage(self) -> float:
        """Progress through session (0-100)."""
        if self.max_probes_per_session == 0:
            return 100.0
        return min(100.0, (self.total_probes_sent / self.max_probes_per_session) * 100)
    
    def can_probe_field(self, field: str) -> bool:
        """Check if field hasn't exceeded probe limit."""
        return self.fields_probed.get(field, 0) < self.max_probes_per_field
    
    def record_probe_sent(self, hypothesis_id: str, probe_id: str, field: str) -> None:
        """Track that a probe was sent."""
        self.total_probes_sent += 1
        self.fields_probed[field] = self.fields_probed.get(field, 0) + 1
        self.current_hypothesis_id = hypothesis_id
        self.current_probe_id = probe_id
        self.last_activity = datetime.now(timezone.utc)
        
        # Remove from queue if exhausted
        if not self.can_probe_field(field):
            if field not in self.fields_exhausted:
                self.fields_exhausted.append(field)
            # Remove all hypotheses for this field from queue
            self.probing_queue = [
                h_id for h_id in self.probing_queue 
                if not h_id.startswith(f"{field}:")  # Simplification
            ]
    
    def record_response(self, confirmed_fields: list[str] | None = None) -> None:
        """Track response and confirmations."""
        self.total_responses += 1
        if confirmed_fields:
            self.fields_confirmed.extend(confirmed_fields)
        self.last_activity = datetime.now(timezone.utc)
    
    def mark_complete(self, reason: str = "finished") -> None:
        """Mark session as complete."""
        self.state = "complete"
        self.completed_at = datetime.now(timezone.utc)
    
    def to_storage_dict(self) -> dict:
        """Convert for JSONB storage."""
        return {
            **self.model_dump(),
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_storage_dict(cls, data: dict) -> "GenesisSession":
        """Reconstruct from storage."""
        data = data.copy()
        data["started_at"] = datetime.fromisoformat(data["started_at"])
        data["last_activity"] = datetime.fromisoformat(data["last_activity"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


class SessionProgress(BaseModel):
    """Progress information for API response."""
    probes_sent: int
    max_probes: int
    fields_confirmed: int
    fields_remaining: int
    progress_percentage: float


class GenesisSessionManager:
    """
    Manages Genesis conversational sessions.
    
    Handles session lifecycle, intelligent probe ordering,
    and completion detection.
    """
    
    # In-memory session store (in production, use Redis)
    _sessions: dict[str, GenesisSession] = {}
    
    async def create_session(
        self,
        user_id: int,
        hypothesis_ids: list[str],
        max_probes: int = 10
    ) -> GenesisSession:
        """
        Create a new refinement session.
        
        Args:
            user_id: User ID
            hypothesis_ids: IDs of hypotheses to probe
            max_probes: Maximum probes for this session
            
        Returns:
            New GenesisSession
        """
        session = GenesisSession(
            user_id=user_id,
            probing_queue=hypothesis_ids.copy(),
            max_probes_per_session=max_probes,
        )
        
        self._sessions[session.session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> GenesisSession | None:
        """Get existing session by ID."""
        return self._sessions.get(session_id)
    
    async def get_or_create_session(
        self,
        user_id: int,
        engine: GenesisEngine
    ) -> tuple[GenesisSession, bool]:
        """
        Get existing active session or create new one.
        
        Returns:
            Tuple of (session, is_new)
        """
        # Check for existing active session
        for session in self._sessions.values():
            if session.user_id == user_id and session.state == "active":
                return session, False
        
        # Create new session from engine's hypotheses
        hypotheses = engine.get_active_hypotheses(user_id)
        if not hypotheses:
            # No active hypotheses - create empty session that completes immediately
            session = GenesisSession(
                user_id=user_id,
                state="complete",
            )
            self._sessions[session.session_id] = session
            return session, True
        
        session = await self.create_session(
            user_id=user_id,
            hypothesis_ids=[h.id for h in hypotheses]
        )
        return session, True
    
    async def get_next_probe(
        self,
        session: GenesisSession,
        engine: GenesisEngine
    ) -> ProbePacket | None:
        """
        Get next probe with smart ordering.
        
        Strategy:
        1. Get all active hypotheses from queue
        2. Filter by field probe limits
        3. Select highest priority
        4. Generate probe
        5. Update session state
        
        Returns:
            ProbePacket or None if session should end
        """
        if not session.should_continue:
            return None
        
        # Get active hypotheses
        hypotheses = engine.get_active_hypotheses(session.user_id)
        if not hypotheses:
            session.mark_complete("no_remaining_hypotheses")
            return None
        
        # Filter by queue and field limits
        candidates = [
            h for h in hypotheses
            if h.id in session.probing_queue
            and session.can_probe_field(h.field)
            and h.needs_probing
        ]
        
        if not candidates:
            # Try any hypothesis that can still be probed
            candidates = [
                h for h in hypotheses
                if session.can_probe_field(h.field)
                and h.needs_probing
            ]
        
        if not candidates:
            session.mark_complete("all_fields_exhausted")
            return None
        
        # Sort by priority and pick best
        candidates.sort(key=lambda h: h.priority, reverse=True)
        selected = candidates[0]
        
        # Generate probe
        probe = await engine.generate_probe(selected)
        
        # Update session
        session.record_probe_sent(selected.id, probe.id, selected.field)
        
        # Update queue
        if selected.id in session.probing_queue:
            session.probing_queue.remove(selected.id)
        
        return probe
    
    async def process_response(
        self,
        session: GenesisSession,
        response: ProbeResponse,
        engine: GenesisEngine
    ) -> dict:
        """
        Process response and determine next action.
        
        Returns:
            {
                "confirmations": [...],
                "next_probe": ProbePacket | None,
                "session_complete": bool,
                "summary": str | None
            }
        """
        # Process through engine
        updated = await engine.process_response(response.probe_id, response)
        
        # Check for confirmations
        confirmations = await engine.check_confirmations(session.user_id)
        confirmed_fields = [c[1] for c in confirmations]  # Extract confirmed values
        confirmed_field_names = [c[0].field for c in confirmations]
        
        # Update session
        session.record_response(confirmed_fields=confirmed_field_names)
        
        # Get next probe
        next_probe = await self.get_next_probe(session, engine)
        
        # Build response
        result = {
            "confirmations": [
                {
                    "field": hyp.field,
                    "module": hyp.module,
                    "confirmed_value": value,
                    "confidence": hyp.confidence
                }
                for hyp, value in confirmations
            ],
            "next_probe": next_probe,
            "session_complete": session.state == "complete" or next_probe is None,
            "summary": None
        }
        
        if result["session_complete"] and session.state != "complete":
            session.mark_complete("probing_finished")
            result["summary"] = await self._generate_summary(session, engine)
        
        return result
    
    async def complete_session(
        self,
        session: GenesisSession,
        engine: GenesisEngine,
        reason: str = "user_ended"
    ) -> dict:
        """
        Mark session complete and generate summary.
        """
        session.mark_complete(reason)
        summary = await self._generate_summary(session, engine)
        
        return {
            "session_id": session.session_id,
            "summary": summary,
            "fields_confirmed": session.fields_confirmed,
            "probes_sent": session.total_probes_sent,
        }
    
    async def _generate_summary(
        self,
        session: GenesisSession,
        engine: GenesisEngine
    ) -> str:
        """Generate session summary."""
        confirmed = engine.get_confirmed_hypotheses(session.user_id)
        active = engine.get_active_hypotheses(session.user_id)
        
        lines = [f"Session completed after {session.total_probes_sent} probes."]
        
        if confirmed:
            lines.append(f"\n✅ Confirmed fields:")
            for hyp in confirmed:
                lines.append(f"  • {hyp.field}: {hyp.suspected_value} ({hyp.confidence:.0%})")
        
        if active:
            lines.append(f"\n⏳ Remaining uncertain:")
            # Group by field
            fields = {}
            for hyp in active:
                if hyp.field not in fields:
                    fields[hyp.field] = []
                fields[hyp.field].append(hyp)
            
            for field, hyps in fields.items():
                best = max(hyps, key=lambda h: h.confidence)
                lines.append(f"  • {field}: best guess {best.suspected_value} ({best.confidence:.0%})")
        
        if not confirmed and not active:
            lines.append("\nNo uncertainties detected - profile is complete!")
        
        return "\n".join(lines)
    
    def get_progress(self, session: GenesisSession, engine: GenesisEngine) -> SessionProgress:
        """Get session progress for API response."""
        confirmed = engine.get_confirmed_hypotheses(session.user_id)
        active = engine.get_active_hypotheses(session.user_id)
        
        confirmed_fields = set(h.field for h in confirmed)
        remaining_fields = set(h.field for h in active if h.field not in confirmed_fields)
        
        return SessionProgress(
            probes_sent=session.total_probes_sent,
            max_probes=session.max_probes_per_session,
            fields_confirmed=len(confirmed_fields),
            fields_remaining=len(remaining_fields),
            progress_percentage=session.progress_percentage,
        )


# Singleton instance
_session_manager: GenesisSessionManager | None = None


def get_session_manager() -> GenesisSessionManager:
    """Get the singleton session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = GenesisSessionManager()
    return _session_manager
