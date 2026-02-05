"""
GUTTERS Event Bus

Redis pub/sub event bus for module communication.

Provides simple publish/subscribe pattern for event-driven architecture.
Modules can publish events and subscribe to patterns to react to system changes.
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any

import redis.asyncio as redis

from ...core.config import settings
from ...protocol.packet import Packet
from ..telemetry.tracer import get_tracer


class EventBus:
    """
    Redis-based pub/sub event bus.

    Supports pattern matching for flexible event subscriptions.
    All events are transmitted as Packet instances serialized to JSON.

    Example:
        >>> bus = EventBus()
        >>> await bus.initialize()
        >>>
        >>> # Subscribe to all module events
        >>> async def handle_module_event(packet: Packet):
        ...     print(f"Module event: {packet.event_type}")
        >>>
        >>> bus.subscribe("module.*", handle_module_event)
        >>>
        >>> # Publish an event
        >>> await bus.publish("module.initialized", {"module_name": "astrology"})
    """

    def __init__(self):
        """Initialize event bus (call initialize() to connect to Redis)."""
        self.redis_client: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
        self.handlers: dict[str, list[Callable]] = {}
        self._listener_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """
        Connect to Redis and start listening for events.

        Should be called during application startup.
        """
        # Connect to Redis with password (for Redis Cloud)
        self.redis_client = redis.Redis(
            host=settings.REDIS_CACHE_HOST,
            port=settings.REDIS_CACHE_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
            ssl=settings.REDIS_CACHE_SSL,
        )
        self.pubsub = self.redis_client.pubsub()

        # Start background listener
        self._listener_task = asyncio.create_task(self._listen())

    async def cleanup(self) -> None:
        """
        Disconnect from Redis and stop listening.

        Should be called during application shutdown.
        """
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

    async def subscribe(self, pattern: str, handler: Callable[[Packet], Any]) -> None:
        """
        Subscribe to events matching a pattern.

        Args:
            pattern: Event pattern to match (e.g., "module.*", "cosmic.storm.*")
            handler: Async callable that receives Packet instances

        Example:
            >>> async def on_user_created(packet: Packet):
            ...     user_id = packet.payload["user_id"]
            ...     await initialize_user_profile(user_id)
            >>>
            >>> await bus.subscribe("user.created", on_user_created)
        """
        if pattern not in self.handlers:
            self.handlers[pattern] = []
            # Dynamically subscribe if listening has started
            if self.pubsub:
                await self.pubsub.psubscribe(pattern)

        self.handlers[pattern].append(handler)

    async def publish_packet(self, packet: Packet) -> None:
        """
        Publish a Packet instance directly to the bus.
        """
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        # Record event for observability
        try:
            tracer = get_tracer()
            await tracer.record_event(packet)
        except Exception:
            pass

        # Serialize and publish
        message = json.dumps(packet.to_dict())
        await self.redis_client.publish(packet.event_type, message)

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "system",
        user_id: str | None = None,
    ) -> None:
        """
        Publish an event to the bus.
        Delegates to publish_packet for unified tracing and serialization.
        """
        packet = Packet(
            source=source,
            event_type=event_type,
            payload=payload,
            user_id=user_id,
        )
        await self.publish_packet(packet)

    async def _listen(self) -> None:
        """
        Background task that listens for Redis messages.
        """
        if not self.pubsub:
            return

        while not self.handlers:
            await asyncio.sleep(0.1)

        # Listen for messages
        try:
            while True:
                if not self.pubsub or not self.pubsub.connection:
                    await asyncio.sleep(0.1)
                    continue

                try:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                except Exception as e:
                    if "connection not set" in str(e):
                        await asyncio.sleep(0.1)
                        continue
                    raise e

                if message:
                    try:
                        # Deserialize packet
                        msg_data = message["data"]
                        if isinstance(msg_data, bytes):
                            msg_data = msg_data.decode("utf-8")

                        data = json.loads(msg_data)
                        packet = Packet.from_dict(data)

                        # Find matching handlers
                        channel = message["channel"]
                        handlers = self.handlers.get(channel, [])

                        for pattern, p_handlers in self.handlers.items():
                            if pattern != channel and self._match_pattern(pattern, channel):
                                handlers.extend(p_handlers)

                        # Invoke handlers
                        for handler in handlers:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(packet)
                                else:
                                    handler(packet)
                            except Exception as e:
                                print(f"Error in event handler: {e}")

                    except Exception as e:
                        print(f"Error processing event message: {e}")

                await asyncio.sleep(0.01)  # Yield
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Listener loop error: {e}")

    def _match_pattern(self, pattern: str, channel: str) -> bool:
        """Simple pattern matching for module.* style patterns."""
        if "*" not in pattern:
            return pattern == channel

        import re

        regex = pattern.replace(".", "\\.").replace("*", ".*")
        return bool(re.match(f"^{regex}$", channel))


# Singleton instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the singleton EventBus instance.

    Returns:
        Global EventBus instance

    Example:
        >>> from src.app.core.events.bus import get_event_bus
        >>> bus = get_event_bus()
        >>> await bus.publish("user.created", {"user_id": "123"})
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
