"""
Event Types - All Digital Twin Events

Defines all event types that can be emitted by the Digital Twin system.
Each event carries the relevant data for that change type.

@module EventTypes
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4

from ..traits import Trait, TraitChange


class EventType(str, Enum):
    """Types of events that can be emitted."""
    # Trait events
    TRAIT_ADDED = "trait_added"
    TRAIT_UPDATED = "trait_updated"
    TRAIT_REMOVED = "trait_removed"
    TRAIT_VERIFIED = "trait_verified"
    TRAIT_CONFIDENCE_CHANGED = "trait_confidence_changed"
    
    # Domain events
    DOMAIN_REGISTERED = "domain_registered"
    DOMAIN_UNREGISTERED = "domain_unregistered"
    DOMAIN_DATA_CHANGED = "domain_data_changed"
    
    # Identity events
    IDENTITY_LOADED = "identity_loaded"
    IDENTITY_SAVED = "identity_saved"
    IDENTITY_CREATED = "identity_created"
    IDENTITY_MERGED = "identity_merged"
    
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_CONTEXT_UPDATED = "session_context_updated"
    
    # Query events
    QUERY_EXECUTED = "query_executed"
    
    # System events
    TWIN_INITIALIZED = "twin_initialized"
    TWIN_RESET = "twin_reset"
    SYNC_REQUESTED = "sync_requested"
    SYNC_COMPLETED = "sync_completed"


class EventPriority(str, Enum):
    """Priority of event delivery."""
    CRITICAL = "critical"   # Delivered immediately, blocks
    HIGH = "high"           # Delivered ASAP
    NORMAL = "normal"       # Standard delivery
    LOW = "low"             # Can be batched


@dataclass
class ProfileEvent:
    """
    Base class for all Digital Twin events.
    
    Contains common metadata and the event payload.
    """
    # Identity
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.TRAIT_UPDATED
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Source
    source_agent: str = "system"
    identity_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Priority
    priority: EventPriority = EventPriority.NORMAL
    
    # Payload - override in subclasses
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "identity_id": self.identity_id,
            "session_id": self.session_id,
            "priority": self.priority.value,
            "payload": self.payload,
        }


# =============================================================================
# TRAIT EVENTS
# =============================================================================

@dataclass
class TraitAddedEvent(ProfileEvent):
    """Emitted when a new trait is added to the Digital Twin."""
    event_type: EventType = field(default=EventType.TRAIT_ADDED)
    
    # Trait data
    trait: Optional[Trait] = None
    domain: str = ""
    trait_name: str = ""
    trait_value: Any = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.trait:
            self.domain = self.trait.domain
            self.trait_name = self.trait.name
            self.trait_value = self.trait.value
            self.confidence = self.trait.confidence
            self.payload = {
                "trait": self.trait.to_summary(),
                "path": self.trait.path,
            }


@dataclass
class TraitUpdatedEvent(ProfileEvent):
    """Emitted when an existing trait is updated."""
    event_type: EventType = field(default=EventType.TRAIT_UPDATED)
    
    # Trait data
    trait: Optional[Trait] = None
    change: Optional[TraitChange] = None
    domain: str = ""
    trait_name: str = ""
    old_value: Any = None
    new_value: Any = None
    old_confidence: Optional[float] = None
    new_confidence: Optional[float] = None
    
    def __post_init__(self):
        if self.trait:
            self.domain = self.trait.domain
            self.trait_name = self.trait.name
            self.new_value = self.trait.value
            self.new_confidence = self.trait.confidence
            self.payload = {
                "trait": self.trait.to_summary(),
                "path": self.trait.path,
                "change": self.change.to_dict() if self.change else None,
            }


@dataclass
class TraitRemovedEvent(ProfileEvent):
    """Emitted when a trait is removed/archived."""
    event_type: EventType = field(default=EventType.TRAIT_REMOVED)
    
    domain: str = ""
    trait_name: str = ""
    trait_path: str = ""
    reason: Optional[str] = None
    
    def __post_init__(self):
        self.trait_path = f"{self.domain}.{self.trait_name}"
        self.payload = {
            "path": self.trait_path,
            "reason": self.reason,
        }


# =============================================================================
# DOMAIN EVENTS
# =============================================================================

@dataclass
class DomainRegisteredEvent(ProfileEvent):
    """Emitted when a new domain is registered."""
    event_type: EventType = field(default=EventType.DOMAIN_REGISTERED)
    
    domain_id: str = ""
    domain_name: str = ""
    domain_icon: str = ""
    trait_count: int = 0
    
    def __post_init__(self):
        self.payload = {
            "domain_id": self.domain_id,
            "domain_name": self.domain_name,
            "domain_icon": self.domain_icon,
            "trait_count": self.trait_count,
        }


# =============================================================================
# IDENTITY EVENTS
# =============================================================================

@dataclass
class IdentityLoadedEvent(ProfileEvent):
    """Emitted when an identity is loaded from storage."""
    event_type: EventType = field(default=EventType.IDENTITY_LOADED)
    priority: EventPriority = field(default=EventPriority.HIGH)
    
    identity_version: int = 0
    trait_count: int = 0
    domain_count: int = 0
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        self.payload = {
            "identity_id": self.identity_id,
            "version": self.identity_version,
            "trait_count": self.trait_count,
            "domain_count": self.domain_count,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class IdentitySavedEvent(ProfileEvent):
    """Emitted when an identity is saved to storage."""
    event_type: EventType = field(default=EventType.IDENTITY_SAVED)
    
    identity_version: int = 0
    trait_count: int = 0
    save_location: str = ""
    
    def __post_init__(self):
        self.payload = {
            "identity_id": self.identity_id,
            "version": self.identity_version,
            "trait_count": self.trait_count,
            "save_location": self.save_location,
        }


# =============================================================================
# SESSION EVENTS
# =============================================================================

@dataclass
class SessionStartedEvent(ProfileEvent):
    """Emitted when a new session starts."""
    event_type: EventType = field(default=EventType.SESSION_STARTED)
    priority: EventPriority = field(default=EventPriority.HIGH)
    
    is_new_identity: bool = False
    is_resuming: bool = False
    
    def __post_init__(self):
        self.payload = {
            "identity_id": self.identity_id,
            "session_id": self.session_id,
            "is_new_identity": self.is_new_identity,
            "is_resuming": self.is_resuming,
        }


@dataclass
class SessionEndedEvent(ProfileEvent):
    """Emitted when a session ends."""
    event_type: EventType = field(default=EventType.SESSION_ENDED)
    
    duration_seconds: float = 0.0
    traits_added: int = 0
    traits_updated: int = 0
    
    def __post_init__(self):
        self.payload = {
            "session_id": self.session_id,
            "duration_seconds": self.duration_seconds,
            "traits_added": self.traits_added,
            "traits_updated": self.traits_updated,
        }
