from __future__ import annotations

"""
Chat session models.

Supports Master Chat + Branch Sessions architecture.
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone as dt_timezone
from enum import Enum

from src.app.core.db.database import Base


class SessionType(str, Enum):
    """Types of chat sessions."""

    MASTER = "master"
    JOURNAL = "journal"
    NUTRITION = "nutrition"
    FINANCE = "finance"
    DREAM_LOG = "dream_log"


class MessageRole(str, Enum):
    """Message roles in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.app.models.user import User


class ChatSession(Base):
    """
    Chat session (Master or Branch).
    """

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    conversation_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    contribute_to_memory: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(dt_timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt_timezone.utc),
        onupdate=lambda: datetime.now(dt_timezone.utc),
    )

    # Relationships
    # Relationships
    user = relationship("User", back_populates="chat_sessions", lazy="select")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="select",
    )


class ChatMessage(Base):
    """
    Message within a chat session.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(dt_timezone.utc))

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages", lazy="select")
