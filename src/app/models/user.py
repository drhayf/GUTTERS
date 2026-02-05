from __future__ import annotations
import uuid as uuid_pkg
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from src.app.core.db.database import Base

if TYPE_CHECKING:
    from .user_profile import UserProfile
    from .embedding import Embedding
    from .chat_session import ChatSession
    from .progression import PlayerStats
    from src.app.modules.features.quests.models import Quest


class User(Base):
    """
    User model with GUTTERS birth data for cosmic calculations.

    Birth data is required for:
    - Natal chart calculations (astrology, Vedic, Chinese)
    - Human Design chart generation
    - Numerology calculations
    - All time-sensitive cosmic analysis
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    name: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)

    profile_image_url: Mapped[str] = mapped_column(String, default="https://profileimageurl.com")
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default=uuid7, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    tier_id: Mapped[int | None] = mapped_column(ForeignKey("tier.id"), index=True, default=None)

    # Relationship to user's progression and gamification stats
    progression = relationship(
        "PlayerStats", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="select"
    )

    # Relationship to user's cosmic profile
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Vector embeddings for semantic search
    embeddings = relationship(
        "Embedding",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Chat Sessions (Master + Branch)
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # GUTTERS Birth Data Fields
    birth_date: Mapped[date | None] = mapped_column(Date, default=None)
    birth_time: Mapped[time | None] = mapped_column(Time, default=None)
    birth_location: Mapped[str | None] = mapped_column(String(255), default=None)
    birth_latitude: Mapped[float | None] = mapped_column(Float, default=None)
    birth_longitude: Mapped[float | None] = mapped_column(Float, default=None)
    birth_timezone: Mapped[str | None] = mapped_column(String(50), default=None)

    push_subscriptions = relationship(
        "PushSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    quests = relationship("Quest", back_populates="user", cascade="all, delete-orphan", lazy="select")
