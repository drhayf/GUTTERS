"""
Sovereign Memory - Contextual Awareness System

This module implements the "Memory Palace" of the Sovereign Agent - the system
that maintains awareness of:

1. DIGITAL TWIN - The user's complete profile and preferences
2. CONVERSATION - Recent conversation history and context
3. MODULE STATE - Current state of all enabled modules
4. SESSION STATE - Ephemeral state for the current session
5. SYSTEM STATE - Agent registry, capabilities, configuration

The Memory provides a unified interface for the Cortex to access all
contextual information without knowing the underlying storage details.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌────────────────────────────┐
                    │     SOVEREIGN MEMORY       │
                    ├────────────────────────────┤
                    │                            │
    Digital Twin ◄──┤  ┌────────────────────┐   │
                    │  │   Memory Layers     │   │
    Conversation ◄──┤  │  • L0: Working      │   │
                    │  │  • L1: Session      │   │
    Module State ◄──┤  │  • L2: Persistent   │   │
                    │  │  • L3: Archival     │   │
    System Info ◄───┤  └────────────────────┘   │
                    │                            │
                    │  ┌────────────────────┐   │
                    │  │   Context Builder   │   │
                    │  │  • Relevance Filter │   │
                    │  │  • Token Budget     │   │
                    │  │  • Priority Rank    │   │
                    │  └────────────────────┘   │
                    │                            │
                    └────────────────────────────┘

@module SovereignMemory
"""

from typing import Optional, Any, Dict, List, Tuple, Callable, Deque, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import asyncio

from ...shared.protocol import AgentCapability

logger = logging.getLogger(__name__)


# =============================================================================
# MEMORY LAYERS
# =============================================================================

class MemoryLayer(str, Enum):
    """Layers of memory with different retention characteristics."""
    WORKING = "working"       # Current turn only (immediate context)
    SESSION = "session"       # Current session (conversation history)
    PERSISTENT = "persistent" # Stored in AsyncStorage (preferences, profile)
    ARCHIVAL = "archival"     # Long-term storage (Supabase/Vector)


@dataclass
class MemoryEntry:
    """A single entry in memory."""
    key: str
    value: Any
    layer: MemoryLayer
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


# =============================================================================
# CONVERSATION MEMORY
# =============================================================================

@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    components: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_message(self) -> Dict[str, str]:
        """Convert to LangChain message format."""
        return {
            "role": self.role,
            "content": self.content,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "components": self.components,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
        }


class ConversationBuffer:
    """
    Manages conversation history with intelligent summarization.
    
    Features:
    - Rolling window of recent messages
    - Automatic summarization of older messages
    - Token budget management
    - Relevance-based pruning
    """
    
    def __init__(
        self,
        max_turns: int = 50,
        max_tokens: int = 8000,
        summary_threshold: int = 20,
    ):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
        
        self.turns: deque[ConversationTurn] = deque(maxlen=max_turns)
        self.summaries: List[str] = []
        self._token_count: int = 0
    
    def add_turn(self, role: str, content: str, **metadata) -> None:
        """Add a new conversation turn."""
        turn = ConversationTurn(
            role=role,
            content=content,
            metadata=metadata,
        )
        self.turns.append(turn)
        
        # Check if we need to summarize
        if len(self.turns) >= self.summary_threshold:
            self._maybe_summarize()
    
    def add_tool_call(self, tool_name: str, params: Dict, result: Dict) -> None:
        """Add a tool call to the most recent assistant turn."""
        if self.turns and self.turns[-1].role == "assistant":
            self.turns[-1].tool_calls.append({
                "tool": tool_name,
                "params": params,
                "result": result,
            })
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation as a list of messages."""
        turns = list(self.turns)
        if limit:
            turns = turns[-limit:]
        return [turn.to_message() for turn in turns]
    
    def get_context_string(self, max_chars: int = 4000) -> str:
        """Get conversation as a formatted string within char limit."""
        parts = []
        
        # Include summaries first
        if self.summaries:
            parts.append("Previous conversation summary:")
            parts.extend(self.summaries)
            parts.append("")
        
        # Include recent turns
        parts.append("Recent conversation:")
        for turn in self.turns:
            prefix = "User:" if turn.role == "user" else "Assistant:"
            parts.append(f"{prefix} {turn.content}")
        
        result = "\n".join(parts)
        
        # Truncate if needed
        if len(result) > max_chars:
            result = result[-max_chars:]
            result = "..." + result[result.find("\n"):]
        
        return result
    
    def _maybe_summarize(self) -> None:
        """Summarize older turns if buffer is getting large."""
        # In full implementation, this would use the LLM to summarize
        # For now, we just track that summarization would occur
        pass
    
    def clear(self) -> None:
        """Clear all conversation history."""
        self.turns.clear()
        self.summaries.clear()


# =============================================================================
# MODULE STATE CACHE
# =============================================================================

@dataclass
class ModuleState:
    """Cached state for a module."""
    module_id: str
    capability: AgentCapability
    enabled: bool
    last_synced: datetime
    data: Dict[str, Any]
    summary: Optional[str] = None


class ModuleStateCache:
    """
    Cache for module states with automatic refresh.
    
    Maintains awareness of what's happening in each enabled module.
    """
    
    def __init__(self, stale_threshold_seconds: int = 300):
        self._states: Dict[str, ModuleState] = {}
        self.stale_threshold = stale_threshold_seconds
    
    def update(self, module_id: str, capability: AgentCapability, data: Dict, summary: Optional[str] = None) -> None:
        """Update a module's cached state."""
        self._states[module_id] = ModuleState(
            module_id=module_id,
            capability=capability,
            enabled=True,
            last_synced=datetime.utcnow(),
            data=data,
            summary=summary,
        )
    
    def get(self, module_id: str) -> Optional[ModuleState]:
        """Get a module's state."""
        return self._states.get(module_id)
    
    def get_all(self) -> List[ModuleState]:
        """Get all module states."""
        return list(self._states.values())
    
    def get_stale(self) -> List[ModuleState]:
        """Get modules that need refresh."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.stale_threshold)
        return [s for s in self._states.values() if s.last_synced < cutoff]
    
    def get_summary(self) -> str:
        """Get a summary of all module states."""
        if not self._states:
            return "No module data cached."
        
        parts = []
        for state in self._states.values():
            if state.summary:
                parts.append(f"• {state.module_id}: {state.summary}")
        
        return "\n".join(parts) if parts else "Modules active but no summaries available."


# =============================================================================
# SOVEREIGN MEMORY
# =============================================================================

class SovereignMemory:
    """
    The complete memory system for the Sovereign Agent.
    
    Provides unified access to:
    - Digital Twin profile data
    - Conversation history
    - Module states
    - System configuration
    
    Usage:
        memory = SovereignMemory()
        
        # Store values
        memory.set("user_preference", "dark_mode", layer=MemoryLayer.PERSISTENT)
        
        # Retrieve values
        value = memory.get("user_preference")
        
        # Build context for LLM
        context = memory.build_context(max_tokens=4000)
    """
    
    def __init__(self):
        # Core stores
        self._entries: Dict[str, MemoryEntry] = {}
        self._digital_twin: Dict[str, Any] = {}
        self._enabled_capabilities: Set[AgentCapability] = set()
        
        # Conversation
        self.conversation = ConversationBuffer()
        
        # Module cache
        self.modules = ModuleStateCache()
        
        # Session metadata
        self.session_id: Optional[str] = None
        self.session_started: Optional[datetime] = None
        self.turn_count: int = 0
    
    # -------------------------------------------------------------------------
    # Basic Memory Operations
    # -------------------------------------------------------------------------
    
    def set(
        self,
        key: str,
        value: Any,
        layer: MemoryLayer = MemoryLayer.SESSION,
        ttl_seconds: Optional[int] = None,
        **metadata,
    ) -> None:
        """Store a value in memory."""
        self._entries[key] = MemoryEntry(
            key=key,
            value=value,
            layer=layer,
            ttl_seconds=ttl_seconds,
            metadata=metadata,
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory."""
        entry = self._entries.get(key)
        if entry is None:
            return default
        if entry.is_expired:
            del self._entries[key]
            return default
        entry.touch()
        return entry.value
    
    def delete(self, key: str) -> bool:
        """Remove a value from memory."""
        if key in self._entries:
            del self._entries[key]
            return True
        return False
    
    def get_layer(self, layer: MemoryLayer) -> Dict[str, Any]:
        """Get all entries in a memory layer."""
        return {
            k: v.value
            for k, v in self._entries.items()
            if v.layer == layer and not v.is_expired
        }
    
    # -------------------------------------------------------------------------
    # Digital Twin
    # -------------------------------------------------------------------------
    
    def load_digital_twin(self, data: Dict[str, Any]) -> None:
        """Load the Digital Twin profile."""
        self._digital_twin = data
        logger.info(f"[SovereignMemory] Loaded Digital Twin with {len(data)} top-level keys")
    
    def get_digital_twin(self) -> Dict[str, Any]:
        """Get the full Digital Twin."""
        return self._digital_twin.copy()
    
    def get_digital_twin_field(self, path: str, default: Any = None) -> Any:
        """Get a field from Digital Twin using dot notation."""
        value = self._digital_twin
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
    
    def update_digital_twin(self, path: str, value: Any) -> None:
        """Update a field in the Digital Twin."""
        keys = path.split(".")
        target = self._digital_twin
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
    
    def get_human_design_summary(self) -> str:
        """Get a summary of the user's Human Design."""
        hd = self._digital_twin.get("human_design", {})
        if not hd:
            return "Human Design profile not yet determined."
        
        parts = []
        if hd.get("type"):
            parts.append(f"Type: {hd['type']}")
        if hd.get("authority"):
            parts.append(f"Authority: {hd['authority']}")
        if hd.get("profile"):
            parts.append(f"Profile: {hd['profile']}")
        if hd.get("strategy"):
            parts.append(f"Strategy: {hd['strategy']}")
        
        return ", ".join(parts) if parts else "Human Design data incomplete."
    
    def get_essence_statement(self) -> Optional[str]:
        """Get the user's essence statement."""
        return self._digital_twin.get("essence_statement")
    
    # -------------------------------------------------------------------------
    # Capabilities
    # -------------------------------------------------------------------------
    
    def load_capabilities(self, capabilities: List[AgentCapability]) -> None:
        """Load enabled capabilities."""
        self._enabled_capabilities = set(capabilities)
        logger.info(f"[SovereignMemory] Loaded {len(capabilities)} capabilities")
    
    def get_enabled_capabilities(self) -> Set[AgentCapability]:
        """Get all enabled capabilities."""
        return self._enabled_capabilities.copy()
    
    def is_capability_enabled(self, capability: AgentCapability) -> bool:
        """Check if a capability is enabled."""
        return capability in self._enabled_capabilities
    
    # -------------------------------------------------------------------------
    # Session
    # -------------------------------------------------------------------------
    
    def start_session(self, session_id: str) -> None:
        """
        Start or resume a session.
        
        If the session_id matches the current session, continues without reset.
        If it's a new session_id, resets all working memory.
        """
        # Check if this is the same session - if so, continue without reset
        if self.session_id == session_id:
            logger.debug(f"[SovereignMemory] Continuing session: {session_id}")
            return
        
        # New session - reset state
        logger.info(f"[SovereignMemory] Starting new session: {session_id}")
        self.session_id = session_id
        self.session_started = datetime.utcnow()
        self.turn_count = 0
        self.conversation.clear()
        
        # Clear working memory
        working_keys = [k for k, v in self._entries.items() if v.layer == MemoryLayer.WORKING]
        for key in working_keys:
            del self._entries[key]
    
    def increment_turn(self) -> int:
        """Increment and return the turn count."""
        self.turn_count += 1
        return self.turn_count
    
    # -------------------------------------------------------------------------
    # Context Building
    # -------------------------------------------------------------------------
    
    def build_context(self, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Build a complete context object for the Cortex.
        
        This gathers all relevant information the LLM needs:
        - User profile summary
        - Enabled capabilities
        - Recent conversation
        - Module summaries
        - Session state
        """
        # Estimate tokens per section
        budget = {
            "profile": int(max_tokens * 0.2),
            "conversation": int(max_tokens * 0.5),
            "modules": int(max_tokens * 0.2),
            "session": int(max_tokens * 0.1),
        }
        
        context = {
            # User Profile
            "has_profile": bool(self._digital_twin),
            "human_design": self.get_human_design_summary(),
            "essence": self.get_essence_statement(),
            "archetypes": self._digital_twin.get("archetypes", {}),
            
            # Capabilities
            "enabled_capabilities": [c.value for c in self._enabled_capabilities],
            
            # Conversation
            "conversation_history": self.conversation.get_context_string(
                max_chars=budget["conversation"] * 4  # ~4 chars per token
            ),
            
            # Modules
            "module_summary": self.modules.get_summary(),
            
            # Session
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "session_duration_minutes": (
                (datetime.utcnow() - self.session_started).total_seconds() / 60
                if self.session_started else 0
            ),
        }
        
        return context
    
    def build_system_prompt_context(self) -> str:
        """Build context for inclusion in the system prompt."""
        parts = []
        
        # User identity
        if self._digital_twin:
            parts.append("USER PROFILE:")
            parts.append(f"  Human Design: {self.get_human_design_summary()}")
            if essence := self.get_essence_statement():
                parts.append(f"  Essence: {essence}")
            parts.append("")
        
        # Enabled modules
        parts.append("ENABLED MODULES:")
        for cap in self._enabled_capabilities:
            parts.append(f"  • {cap.value.replace('_', ' ').title()}")
        parts.append("")
        
        # Module states
        if module_summary := self.modules.get_summary():
            parts.append("MODULE STATE:")
            parts.append(module_summary)
            parts.append("")
        
        return "\n".join(parts)
