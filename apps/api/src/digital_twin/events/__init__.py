"""
Event System - Real-Time Profile Synchronization

This module provides the event bus that enables real-time synchronization
between all components watching the Digital Twin.

When ANY change occurs to the Digital Twin:
1. An event is emitted through the ProfileEventBus
2. All subscribers receive the event
3. Subscribers update their local state

This ensures:
- Sovereign Agent always has current data
- Master Scout sees all domain updates
- UI components can react to changes
- No polling required - push-based updates

@module Events
"""

from .bus import (
    ProfileEventBus,
    EventSubscriber,
    EventFilter,
    get_event_bus,
)
from .types import (
    ProfileEvent,
    EventType,
    TraitAddedEvent,
    TraitUpdatedEvent,
    TraitRemovedEvent,
    DomainRegisteredEvent,
    IdentityLoadedEvent,
    IdentitySavedEvent,
    SessionStartedEvent,
    SessionEndedEvent,
)

__all__ = [
    "ProfileEventBus",
    "EventSubscriber",
    "EventFilter",
    "get_event_bus",
    "ProfileEvent",
    "EventType",
    "TraitAddedEvent",
    "TraitUpdatedEvent",
    "TraitRemovedEvent",
    "DomainRegisteredEvent",
    "IdentityLoadedEvent",
    "IdentitySavedEvent",
    "SessionStartedEvent",
    "SessionEndedEvent",
]
