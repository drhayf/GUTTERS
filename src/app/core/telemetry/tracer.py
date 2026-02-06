"""
GUTTERS Telemetry Tracer

Records system events for observability and debugging.
All events are stored in Redis with 24-hour TTL.

Example:
    >>> from src.app.core.telemetry.tracer import get_tracer
    >>> tracer = get_tracer()
    >>> tracer.record_event(packet)
    >>> events = await tracer.get_trace("trace-123")
"""
import json
import time

import redis.asyncio as redis

from ...core.config import settings
from ...protocol.packet import Packet


class Tracer:
    """
    Event tracer for system observability.

    Records all events to Redis for debugging and monitoring.
    Each trace groups related events together.
    """

    TTL_SECONDS = 86400  # 24 hours

    def __init__(self):
        """Initialize tracer (call initialize() to connect to Redis)."""
        self.redis_client: redis.Redis | None = None

    async def initialize(self) -> None:
        """Connect to Redis."""
        self.redis_client = redis.Redis(
            host=settings.REDIS_CACHE_HOST,
            port=settings.REDIS_CACHE_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
        )

    async def cleanup(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def record_event(self, packet: Packet) -> None:
        """
        Record an event packet to Redis.

        Storage key: trace:{trace_id}:event:{timestamp}
        TTL: 24 hours

        Args:
            packet: Event packet to record
        """
        if not self.redis_client:
            await self.initialize()

        trace_id = packet.trace_id or "unknown"
        timestamp = packet.timestamp or time.time()

        # Create Redis key
        key = f"trace:{trace_id}:event:{timestamp}"

        # Serialize packet
        data = json.dumps(packet.to_dict())

        # Store with TTL
        await self.redis_client.set(key, data, ex=self.TTL_SECONDS)

        # Also add to trace index (sorted set for ordering)
        index_key = f"trace:{trace_id}:index"
        await self.redis_client.zadd(index_key, {key: timestamp})
        await self.redis_client.expire(index_key, self.TTL_SECONDS)

    async def get_trace(self, trace_id: str) -> list[Packet]:
        """
        Retrieve all events for a trace, sorted by timestamp.

        Args:
            trace_id: Trace ID to retrieve

        Returns:
            List of Packet objects, sorted by timestamp
        """
        if not self.redis_client:
            await self.initialize()

        # Get all event keys for this trace
        index_key = f"trace:{trace_id}:index"
        event_keys = await self.redis_client.zrange(index_key, 0, -1)

        if not event_keys:
            # Fallback: scan for keys (slower but works if index missing)
            pattern = f"trace:{trace_id}:event:*"
            event_keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                event_keys.append(key)

        # Retrieve and parse events
        packets = []
        for key in event_keys:
            data = await self.redis_client.get(key)
            if data:
                try:
                    packet_dict = json.loads(data)
                    packets.append(Packet.from_dict(packet_dict))
                except (json.JSONDecodeError, Exception):
                    pass

        # Sort by timestamp
        packets.sort(key=lambda p: p.timestamp or 0)

        return packets

    async def get_active_modules(self) -> list[str]:
        """
        Get list of modules that have been active in the last 5 minutes.

        Scans recent events to identify active modules.

        Returns:
            List of active module names
        """
        if not self.redis_client:
            await self.initialize()

        # Current time and 5 minutes ago
        now = time.time()
        five_min_ago = now - 300

        active_modules = set()

        # Scan for recent event keys
        pattern = "trace:*:event:*"
        async for key in self.redis_client.scan_iter(match=pattern):
            # Extract timestamp from key
            parts = key.split(":")
            if len(parts) >= 4:
                try:
                    ts = float(parts[-1])
                    if ts >= five_min_ago:
                        # Get the event data
                        data = await self.redis_client.get(key)
                        if data:
                            packet_dict = json.loads(data)
                            source = packet_dict.get("source", "")
                            if source and source != "system":
                                active_modules.add(source)
                except (ValueError, json.JSONDecodeError):
                    pass

        return sorted(active_modules)

    async def get_recent_events(self, limit: int = 100) -> list[Packet]:
        """
        Get most recent events across all traces.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent Packet objects
        """
        if not self.redis_client:
            await self.initialize()

        events = []
        pattern = "trace:*:event:*"

        async for key in self.redis_client.scan_iter(match=pattern):
            data = await self.redis_client.get(key)
            if data:
                try:
                    packet_dict = json.loads(data)
                    events.append(Packet.from_dict(packet_dict))
                except (json.JSONDecodeError, Exception):
                    pass

            if len(events) >= limit * 2:  # Get extra for sorting
                break

        # Sort by timestamp (newest first)
        events.sort(key=lambda p: p.timestamp or 0, reverse=True)

        return events[:limit]


# Singleton instance
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """
    Get the singleton Tracer instance.

    Returns:
        Global Tracer instance

    Example:
        >>> tracer = get_tracer()
        >>> await tracer.record_event(packet)
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
