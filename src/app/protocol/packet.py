"""
GUTTERS Event Packet

Dataclass for event messages passed through the event bus.

All events in GUTTERS use this standardized packet format for consistency
and traceability across the distributed module system.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Packet:
    """
    Standardized event packet for GUTTERS event bus.

    Attributes:
        trace_id: Unique identifier for this event (auto-generated)
        source: Module or system that emitted the event (e.g., "astrology", "synthesis")
        event_type: Event constant from protocol.events (e.g., USER_CREATED)
        payload: Event-specific data (dict, flexible structure)
        timestamp: When event was created (auto-generated, UTC)
        user_id: User this event relates to (None for system events)

    Example:
        >>> from src.app.protocol import Packet, USER_CREATED
        >>> from src.app.models.user_profile import UserProfile
        >>> packet = Packet(
        ...     source="auth_service",
        ...     event_type=USER_CREATED,
        ...     payload={"email": "user@example.com"},
        ...     user_id=UUID("...")
        ... )
    """

    source: str
    event_type: str
    payload: dict[str, Any]
    user_id: str | None = None
    trace_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate packet after initialization."""
        if not self.source:
            raise ValueError("Packet source cannot be empty")
        if not self.event_type:
            raise ValueError("Packet event_type cannot be empty")
        if not isinstance(self.payload, dict):
            raise ValueError("Packet payload must be a dict")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert packet to dictionary for serialization.

        Returns:
            Dictionary representation with ISO format timestamps and string UUIDs
        """
        return {
            "trace_id": str(self.trace_id),
            "source": self.source,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "user_id": str(self.user_id) if self.user_id else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Packet":
        """
        Create packet from dictionary (for deserialization).
        Intelligently returns subclasses based on event_type.
        """
        event_type = data.get("event_type")

        # Polymorphic deserialization
        from src.app.protocol import events

        if event_type == events.PROGRESSION_EXPERIENCE_GAIN:
            return ProgressionPacket.from_dict(data)

        return cls._base_from_dict(data)

    @classmethod
    def _base_from_dict(cls, data: dict[str, Any]) -> "Packet":
        """Internal helper for base field deserialization without polymorphism."""
        return cls(
            trace_id=UUID(data["trace_id"]) if isinstance(data.get("trace_id"), str) else data.get("trace_id", uuid4()),
            source=data["source"],
            event_type=data["event_type"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("timestamp"), str)
            else data.get("timestamp", datetime.now(UTC)),
            user_id=str(data["user_id"]) if data.get("user_id") else None,
        )


@dataclass
class ProgressionPacket(Packet):
    """
    Standardized experience gain packet for the evolution engine.
    """

    amount: int = 0
    reason: str = "Insight Integration"
    category: str = "SYNC"  # e.g., "INTELLECT", "VITALITY", "SYNC"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({"amount": self.amount, "reason": self.reason, "category": self.category})
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressionPacket":
        base = cls._base_from_dict(data)
        return cls(
            source=base.source,
            event_type=base.event_type,
            payload=base.payload,
            user_id=base.user_id,
            trace_id=base.trace_id,
            timestamp=base.timestamp,
            amount=data.get("amount", 0),
            reason=data.get("reason", "Insight Integration"),
            category=data.get("category", "SYNC"),
        )
