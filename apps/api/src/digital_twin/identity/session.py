"""
Identity Session - Session Context Linked to Identity

A session represents a single interaction period with the user.
Sessions are linked to an Identity, and multiple sessions can
contribute to building the same Identity over time.

@module IdentitySession
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from enum import Enum


class SessionPhase(str, Enum):
    """Current phase of the session."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class SessionContext:
    """
    Contextual information for the current session.
    
    This is ephemeral data that exists only during the session,
    unlike Identity data which persists.
    """
    # Current conversation
    recent_messages: List[Dict[str, str]] = field(default_factory=list)
    pending_probes: List[Dict[str, Any]] = field(default_factory=list)
    current_topic: Optional[str] = None
    
    # Module states
    module_states: Dict[str, Any] = field(default_factory=dict)
    
    # UI state
    active_overlays: List[str] = field(default_factory=list)
    pending_notifications: List[Dict[str, Any]] = field(default_factory=list)
    
    # Working memory (volatile)
    working_memory: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to recent history."""
        self.recent_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep last 20 messages
        if len(self.recent_messages) > 20:
            self.recent_messages = self.recent_messages[-20:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recent_messages": self.recent_messages,
            "pending_probes": self.pending_probes,
            "current_topic": self.current_topic,
            "module_states": self.module_states,
            "active_overlays": self.active_overlays,
            "pending_notifications": self.pending_notifications,
            "working_memory": self.working_memory,
        }


@dataclass
class IdentitySession:
    """
    A session linked to an Identity.
    
    Tracks:
    - Which identity this session belongs to
    - Session duration and activity
    - Changes made during the session
    - Context for the current interaction
    """
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    identity_id: str = ""
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Phase
    phase: SessionPhase = SessionPhase.INITIALIZING
    genesis_phase: Optional[str] = None  # awakening, excavation, etc.
    
    # Activity tracking
    interaction_count: int = 0
    traits_added: int = 0
    traits_updated: int = 0
    
    # Context
    context: SessionContext = field(default_factory=SessionContext)
    
    # Auto-save
    last_saved: Optional[datetime] = None
    needs_save: bool = False
    
    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    
    def start(self) -> None:
        """Start the session."""
        self.phase = SessionPhase.ACTIVE
        self.last_activity = datetime.utcnow()
    
    def pause(self) -> None:
        """Pause the session (user backgrounded app)."""
        self.phase = SessionPhase.PAUSED
        self.last_activity = datetime.utcnow()
        self.needs_save = True
    
    def resume(self) -> None:
        """Resume a paused session."""
        self.phase = SessionPhase.ACTIVE
        self.last_activity = datetime.utcnow()
    
    def close(self) -> None:
        """End the session."""
        self.phase = SessionPhase.CLOSED
        self.ended_at = datetime.utcnow()
        self.needs_save = True
    
    # -------------------------------------------------------------------------
    # Activity
    # -------------------------------------------------------------------------
    
    def record_interaction(self) -> None:
        """Record an interaction (message, action, etc.)."""
        self.interaction_count += 1
        self.last_activity = datetime.utcnow()
        self.needs_save = True
    
    def record_trait_added(self) -> None:
        """Record that a trait was added."""
        self.traits_added += 1
        self.needs_save = True
    
    def record_trait_updated(self) -> None:
        """Record that a trait was updated."""
        self.traits_updated += 1
        self.needs_save = True
    
    def mark_saved(self) -> None:
        """Mark that the session was saved."""
        self.last_saved = datetime.utcnow()
        self.needs_save = False
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.ended_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.phase in [SessionPhase.ACTIVE, SessionPhase.PAUSED]
    
    @property
    def is_stale(self) -> bool:
        """Check if session is stale (no activity for 30 minutes)."""
        if not self.is_active:
            return False
        return (datetime.utcnow() - self.last_activity).total_seconds() > 1800
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "phase": self.phase.value,
            "genesis_phase": self.genesis_phase,
            "interaction_count": self.interaction_count,
            "traits_added": self.traits_added,
            "traits_updated": self.traits_updated,
            "context": self.context.to_dict(),
            "last_saved": self.last_saved.isoformat() if self.last_saved else None,
            "duration_seconds": self.duration_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentitySession":
        session = cls(
            id=data.get("id", str(uuid4())),
            identity_id=data.get("identity_id", ""),
            phase=SessionPhase(data.get("phase", "active")),
            genesis_phase=data.get("genesis_phase"),
            interaction_count=data.get("interaction_count", 0),
            traits_added=data.get("traits_added", 0),
            traits_updated=data.get("traits_updated", 0),
        )
        
        if "started_at" in data:
            session.started_at = datetime.fromisoformat(data["started_at"])
        if "last_activity" in data:
            session.last_activity = datetime.fromisoformat(data["last_activity"])
        if data.get("ended_at"):
            session.ended_at = datetime.fromisoformat(data["ended_at"])
        if data.get("last_saved"):
            session.last_saved = datetime.fromisoformat(data["last_saved"])
        
        return session
