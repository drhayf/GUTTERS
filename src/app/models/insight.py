from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.database import Base


class PromptStatus(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    DISMISSED = "dismissed"


class PromptPhase(str, Enum):
    ANTICIPATION = "anticipation"
    PEAK = "peak"
    INTEGRATION = "integration"
    NONE = "none"  # For non-phased triggers


class JournalSource(str, Enum):
    USER = "user"
    SYSTEM = "system"
    PROMPT = "prompt_response"


class ReflectionPrompt(Base):
    """
    AI-generated reflection prompts triggered by cosmic/behavioral events.
    """

    __tablename__ = "reflection_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String, index=True, nullable=False)  # e.g. 'solar_storm', 'full_moon'

    # Context snapshot that triggered this
    trigger_context: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Temporal Gradient Awareness
    event_phase: Mapped[PromptPhase] = mapped_column(String, default=PromptPhase.NONE)

    status: Mapped[PromptStatus] = mapped_column(String, default=PromptStatus.PENDING, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship to journal entry (response)
    response_entry: Mapped[Optional["JournalEntry"]] = relationship(
        "JournalEntry", back_populates="prompt", uselist=False
    )


class JournalEntry(Base):
    """
    User journal entries.
    Now a proper SQL model instead of UserProfile JSON.
    """

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-10
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)

    # Link to the prompt if this was a response
    prompt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reflection_prompts.id"), nullable=True)

    # Snapshot of cosmic/system context at time of writing (for validation later)
    context_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(UTC), default=lambda: datetime.now(UTC)
    )

    prompt: Mapped[Optional["ReflectionPrompt"]] = relationship("ReflectionPrompt", back_populates="response_entry")

    # Source of entry (User vs System)
    source: Mapped[JournalSource] = mapped_column(String, default=JournalSource.USER)
