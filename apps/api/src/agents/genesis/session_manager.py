"""
Genesis Session Manager - Stateful Session Orchestration

This module manages all Genesis profiling sessions with thread-safe
state persistence and lifecycle management.

Responsibilities:
    - Create/retrieve/clear sessions
    - Serialize/deserialize GenesisState
    - Track session metadata (created, last_activity)
    - Store Master agent insights per session
    - Provide session summaries for debugging

Design Principles:
    - Thread-safe for concurrent sessions
    - Lazy initialization (sessions created on demand)
    - Clean separation from conversation logic
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .state import GenesisState, GenesisPhase
from .face import FaceOrchestrator, FaceFactory

logger = logging.getLogger(__name__)


@dataclass
class GenesisSession:
    """
    Complete session state for a Genesis profiling conversation.
    
    Stores both the core GenesisState (serialized for LangGraph)
    and additional metadata for session management.
    """
    session_id: str
    genesis_state_dict: Dict[str, Any] = field(default_factory=dict)
    face: FaceOrchestrator = field(default_factory=FaceFactory.create_default)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # Active model selected by user (from model switcher)
    active_model: Optional[str] = None
    
    # Master agent insights (received from SwarmBus)
    master_hypothesis_insights: list[Dict[str, Any]] = field(default_factory=list)
    master_scout_insights: list[Dict[str, Any]] = field(default_factory=list)
    
    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    @property
    def phase(self) -> str:
        """Get current phase from state dict."""
        return self.genesis_state_dict.get("phase", "awakening")
    
    @property
    def completion(self) -> float:
        """Get completion percentage from state dict."""
        rubric = self.genesis_state_dict.get("rubric", {})
        return rubric.get("completion_percentage", 0.0)
    
    def add_master_insight(self, source: str, insight: Dict[str, Any]) -> None:
        """Add an insight from a Master agent."""
        entry = {
            "source": source,
            "payload": insight,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if "hypothesis" in source.lower():
            self.master_hypothesis_insights.append(entry)
        elif "scout" in source.lower():
            self.master_scout_insights.append(entry)
        
        logger.debug(f"[Session {self.session_id}] Added insight from {source}")
    
    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of this session for debugging."""
        return {
            "session_id": self.session_id,
            "phase": self.phase,
            "completion": self.completion,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "master_insights": {
                "hypothesis": len(self.master_hypothesis_insights),
                "scout": len(self.master_scout_insights),
            },
            "voice": self.face.current_voice.identity.id if self.face.current_voice else "unknown",
        }


class GenesisSessionManager:
    """
    Manages all Genesis profiling sessions.
    
    Provides a clean interface for session lifecycle management,
    keeping this concern separate from conversation logic.
    
    Thread Safety:
        Uses a simple dict which is safe for the typical async
        single-threaded FastAPI context. For multi-process
        deployments, consider Redis or database-backed sessions.
    """
    
    def __init__(self):
        """Initialize the session store."""
        self._sessions: Dict[str, GenesisSession] = {}
        logger.info("[GenesisSessionManager] Initialized")
    
    def get_or_create_session(self, session_id: str) -> GenesisSession:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            The session (existing or newly created)
        """
        if session_id not in self._sessions:
            # Create fresh session
            session = GenesisSession(
                session_id=session_id,
                genesis_state_dict=GenesisState(session_id=session_id).to_dict(),
            )
            self._sessions[session_id] = session
            logger.info(f"[GenesisSessionManager] Created session: {session_id}")
        
        session = self._sessions[session_id]
        session.touch()
        return session
    
    def get_session(self, session_id: str) -> Optional[GenesisSession]:
        """
        Get an existing session without creating.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            The session if it exists, None otherwise
        """
        session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session
    
    def update_session(
        self,
        session_id: str,
        genesis_state_dict: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> bool:
        """
        Update session state.
        
        Args:
            session_id: Unique session identifier
            genesis_state_dict: New state dict from LangGraph
            **kwargs: Additional fields to update
        
        Returns:
            True if session was updated, False if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"[GenesisSessionManager] Update failed - session not found: {session_id}")
            return False
        
        if genesis_state_dict is not None:
            session.genesis_state_dict = genesis_state_dict
        
        session.touch()
        logger.debug(f"[GenesisSessionManager] Updated session: {session_id}")
        return True
    
    def clear_session(self, session_id: str) -> bool:
        """
        Remove a session entirely.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            True if session was cleared, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"[GenesisSessionManager] Cleared session: {session_id}")
            return True
        
        logger.debug(f"[GenesisSessionManager] Clear - session not found: {session_id}")
        return False
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of session state for debugging.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Summary dict if session exists, None otherwise
        """
        session = self._sessions.get(session_id)
        if session:
            return session.to_summary()
        return None
    
    def list_sessions(self) -> list[Dict[str, Any]]:
        """
        List all active sessions with summaries.
        
        Returns:
            List of session summaries
        """
        return [s.to_summary() for s in self._sessions.values()]
    
    def restore_session(
        self,
        session_id: str,
        session_state_dict: Dict[str, Any],
    ) -> GenesisSession:
        """
        Restore a session from a saved state dictionary.
        
        This is used when loading a saved profile to resume the conversation
        from where it left off.
        
        Args:
            session_id: New session ID to use
            session_state_dict: The saved GenesisState as a dict
        
        Returns:
            The restored session
        """
        # Parse timestamps if they're strings
        created_at = session_state_dict.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()
        
        # Create session with restored state
        session = GenesisSession(
            session_id=session_id,
            genesis_state_dict=session_state_dict,
            created_at=created_at,
        )
        
        self._sessions[session_id] = session
        logger.info(
            f"[GenesisSessionManager] Restored session: {session_id} "
            f"(phase: {session.phase}, completion: {session.completion:.0f}%)"
        )
        
        return session
    
    def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions that have been inactive too long.
        
        Args:
            max_age_hours: Maximum inactivity before cleanup
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        stale_ids = []
        
        for session_id, session in self._sessions.items():
            age_hours = (now - session.last_activity).total_seconds() / 3600
            if age_hours > max_age_hours:
                stale_ids.append(session_id)
        
        for session_id in stale_ids:
            del self._sessions[session_id]
        
        if stale_ids:
            logger.info(f"[GenesisSessionManager] Cleaned up {len(stale_ids)} stale sessions")
        
        return len(stale_ids)
