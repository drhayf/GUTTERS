from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.app.core.db.database import Base


class QuestStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RecurrenceType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Cron expression


class QuestSource(str, Enum):
    USER = "user"
    AGENT = "agent"


class QuestCategory(str, Enum):
    DAILY = "daily"
    MISSION = "mission"
    REFLECTION = "reflection"


class QuestDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ELITE = "elite"


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Solo Leveling Metadata
    category: Mapped[QuestCategory] = mapped_column(String, default=QuestCategory.DAILY)
    difficulty: Mapped[QuestDifficulty] = mapped_column(String, default=QuestDifficulty.EASY)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)

    # Link to the AI insight that birthed this quest
    insight_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reflection_prompts.id"), nullable=True)

    # Source Tracking
    source: Mapped[QuestSource] = mapped_column(String, default=QuestSource.USER)

    # Scheduling
    recurrence: Mapped[RecurrenceType] = mapped_column(String, default=RecurrenceType.ONCE)
    cron_expression: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    job_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ARQ Job ID for the next occurrence

    tags: Mapped[str] = mapped_column(String, default="")  # Comma separated

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(UTC), default=lambda: datetime.now(UTC)
    )

    logs: Mapped[list["QuestLog"]] = relationship(
        "QuestLog", back_populates="quest", cascade="all, delete-orphan", lazy="select"
    )
    user = relationship("User", back_populates="quests", lazy="select")


class QuestLog(Base):
    __tablename__ = "quest_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"), index=True)

    status: Mapped[QuestStatus] = mapped_column(String, default=QuestStatus.PENDING)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    quest: Mapped["Quest"] = relationship("Quest", back_populates="logs", lazy="select")
