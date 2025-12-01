"""
Event Bus - Real-Time Event Distribution

The ProfileEventBus is the central hub for all Digital Twin events.
It provides:
- Async event emission
- Subscriber management with filters
- Priority-based delivery
- Event history for debugging

Usage:
    bus = await get_event_bus()
    
    # Subscribe to events
    async def my_handler(event: ProfileEvent):
        print(f"Got event: {event.event_type}")
    
    bus.subscribe(my_handler, filter=EventFilter(domains=["genesis"]))
    
    # Emit events
    await bus.emit(TraitAddedEvent(trait=my_trait))

@module EventBus
"""

from typing import (
    Any, Dict, List, Optional, Set, Callable, Awaitable,
    TypeVar, Generic, Union
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from uuid import uuid4
import asyncio
import logging
import weakref

from .types import ProfileEvent, EventType, EventPriority

logger = logging.getLogger(__name__)

# Type for event handlers
EventHandler = Callable[[ProfileEvent], Awaitable[None]]


# =============================================================================
# EVENT FILTER
# =============================================================================

@dataclass
class EventFilter:
    """
    Filter to select which events a subscriber receives.
    
    All conditions must match (AND logic).
    Empty lists/sets mean "any".
    """
    # Filter by event type
    event_types: Set[EventType] = field(default_factory=set)
    
    # Filter by domain
    domains: Set[str] = field(default_factory=set)
    
    # Filter by trait name (prefix matching)
    trait_prefixes: Set[str] = field(default_factory=set)
    
    # Filter by priority
    min_priority: Optional[EventPriority] = None
    
    # Filter by identity
    identity_id: Optional[str] = None
    
    # Filter by session
    session_id: Optional[str] = None
    
    def matches(self, event: ProfileEvent) -> bool:
        """Check if an event matches this filter."""
        # Event type filter
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Domain filter
        if self.domains:
            event_domain = event.payload.get("domain") or event.payload.get("path", "").split(".")[0]
            if event_domain and event_domain not in self.domains:
                return False
        
        # Trait prefix filter
        if self.trait_prefixes:
            trait_path = event.payload.get("path", "")
            if trait_path and not any(trait_path.startswith(p) for p in self.trait_prefixes):
                return False
        
        # Priority filter
        if self.min_priority:
            priority_order = {
                EventPriority.CRITICAL: 0,
                EventPriority.HIGH: 1,
                EventPriority.NORMAL: 2,
                EventPriority.LOW: 3,
            }
            if priority_order.get(event.priority, 2) > priority_order.get(self.min_priority, 2):
                return False
        
        # Identity filter
        if self.identity_id and event.identity_id != self.identity_id:
            return False
        
        # Session filter
        if self.session_id and event.session_id != self.session_id:
            return False
        
        return True


# =============================================================================
# EVENT SUBSCRIBER
# =============================================================================

@dataclass
class EventSubscriber:
    """
    A registered event subscriber.
    
    Contains the handler and filter for matching events.
    """
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    handler: Optional[EventHandler] = None
    filter: EventFilter = field(default_factory=EventFilter)
    
    # Stats
    events_received: int = 0
    last_event_at: Optional[datetime] = None
    errors: int = 0
    
    # State
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    async def handle(self, event: ProfileEvent) -> bool:
        """
        Handle an event if it matches the filter.
        
        Returns True if handled successfully.
        """
        if not self.is_active:
            return False
        
        if not self.filter.matches(event):
            return False
        
        if self.handler is None:
            return False
        
        try:
            await self.handler(event)
            self.events_received += 1
            self.last_event_at = datetime.utcnow()
            return True
        except Exception as e:
            self.errors += 1
            logger.error(f"[EventBus] Subscriber {self.name} error: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "events_received": self.events_received,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
            "errors": self.errors,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# EVENT BUS
# =============================================================================

class ProfileEventBus:
    """
    The central event distribution system for the Digital Twin.
    
    Features:
    - Async event emission with priority queuing
    - Subscriber management with filters
    - Event history for debugging
    - Stats tracking
    
    The bus is a singleton - use get_event_bus() to access it.
    """
    
    def __init__(self, history_size: int = 100):
        # Subscribers
        self._subscribers: Dict[str, EventSubscriber] = {}
        
        # Event queue for async processing
        self._queue: asyncio.Queue[ProfileEvent] = asyncio.Queue()
        
        # Event history (ring buffer)
        self._history: deque[ProfileEvent] = deque(maxlen=history_size)
        self._history_size = history_size
        
        # Processing
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Stats
        self._stats = {
            "events_emitted": 0,
            "events_delivered": 0,
            "delivery_failures": 0,
            "started_at": None,
        }
        
        logger.info("[ProfileEventBus] Initialized")
    
    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    
    async def start(self) -> None:
        """Start the event processor."""
        if self._running:
            return
        
        self._running = True
        self._stats["started_at"] = datetime.utcnow()
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("[ProfileEventBus] Started event processor")
    
    async def stop(self) -> None:
        """Stop the event processor."""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[ProfileEventBus] Stopped")
    
    async def _process_events(self) -> None:
        """Background task that processes queued events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._deliver_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ProfileEventBus] Processor error: {e}")
    
    # -------------------------------------------------------------------------
    # Subscription
    # -------------------------------------------------------------------------
    
    def subscribe(
        self,
        handler: EventHandler,
        name: Optional[str] = None,
        filter: Optional[EventFilter] = None,
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            handler: Async function to call when event matches
            name: Optional name for debugging
            filter: Optional filter to select events
        
        Returns:
            Subscriber ID (for unsubscribing)
        """
        subscriber = EventSubscriber(
            name=name or f"subscriber_{len(self._subscribers)}",
            handler=handler,
            filter=filter or EventFilter(),
        )
        
        self._subscribers[subscriber.id] = subscriber
        logger.debug(f"[ProfileEventBus] Subscribed: {subscriber.name} ({subscriber.id})")
        
        return subscriber.id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscriber_id: ID returned from subscribe()
        
        Returns:
            True if found and removed
        """
        if subscriber_id in self._subscribers:
            subscriber = self._subscribers.pop(subscriber_id)
            logger.debug(f"[ProfileEventBus] Unsubscribed: {subscriber.name}")
            return True
        return False
    
    def get_subscribers(self) -> List[Dict[str, Any]]:
        """Get info about all subscribers."""
        return [sub.to_dict() for sub in self._subscribers.values()]
    
    # -------------------------------------------------------------------------
    # Emission
    # -------------------------------------------------------------------------
    
    async def emit(self, event: ProfileEvent) -> None:
        """
        Emit an event to all matching subscribers.
        
        For CRITICAL priority, delivers synchronously.
        For other priorities, queues for async delivery.
        """
        self._stats["events_emitted"] += 1
        self._history.append(event)
        
        if event.priority == EventPriority.CRITICAL:
            # Deliver immediately, synchronously
            await self._deliver_event(event)
        else:
            # Queue for async delivery
            await self._queue.put(event)
    
    def emit_sync(self, event: ProfileEvent) -> None:
        """
        Emit an event synchronously (non-async context).
        
        Creates a task to deliver the event.
        """
        self._stats["events_emitted"] += 1
        self._history.append(event)
        
        # Schedule delivery
        asyncio.create_task(self._deliver_event(event))
    
    async def _deliver_event(self, event: ProfileEvent) -> None:
        """Deliver an event to all matching subscribers."""
        logger.debug(f"[ProfileEventBus] Delivering: {event.event_type.value}")
        
        # Parallel delivery to all subscribers
        tasks = []
        for subscriber in self._subscribers.values():
            if subscriber.is_active:
                tasks.append(subscriber.handle(event))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            delivered = sum(1 for r in results if r is True)
            failed = sum(1 for r in results if isinstance(r, Exception))
            
            self._stats["events_delivered"] += delivered
            self._stats["delivery_failures"] += failed
    
    # -------------------------------------------------------------------------
    # Query
    # -------------------------------------------------------------------------
    
    def get_history(
        self,
        limit: Optional[int] = None,
        event_type: Optional[EventType] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent event history."""
        events = list(self._history)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if limit:
            events = events[-limit:]
        
        return [e.to_dict() for e in events]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "subscriber_count": len(self._subscribers),
            "history_size": len(self._history),
            "is_running": self._running,
        }


# =============================================================================
# SINGLETON
# =============================================================================

_event_bus: Optional[ProfileEventBus] = None


async def get_event_bus() -> ProfileEventBus:
    """Get the singleton event bus instance."""
    global _event_bus
    
    if _event_bus is None:
        _event_bus = ProfileEventBus()
        await _event_bus.start()
    
    return _event_bus


def get_event_bus_sync() -> ProfileEventBus:
    """Get the event bus synchronously (may not be started)."""
    global _event_bus
    
    if _event_bus is None:
        _event_bus = ProfileEventBus()
    
    return _event_bus
