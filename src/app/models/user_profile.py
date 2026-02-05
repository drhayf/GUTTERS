"""
GUTTERS User Profile Model

Stores all calculated cosmic profiles for a user in JSONB format.
Each module contributes to this profile during synthesis.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.database import Base

if TYPE_CHECKING:
    from .user import User


class UserProfile(Base):
    """
    Aggregated cosmic profile data for a user.

    The data field stores all module calculations and preferences:
    {
        "preferences": {
            "llm_model": "anthropic/claude-3.5-sonnet",
            "llm_temperature": 0.7
        },
        "astrology": {...},
        "human_design": {...},
        "numerology": {...},
        "synthesis": {...},
        ...
    }

    Each module updates its section during profile calculation.
    """

    __tablename__ = "user_profile"
    __table_args__ = (Index("ix_user_profile_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    # Relationship back to user
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        lazy="select",
    )

    # JSONB containing all module profile data
    data: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    def get_notification_preference(self, category: str) -> bool:
        """
        Check if user has enabled notifications for a specific category.
        Defaults to True (Opt-out model) if preference is missing.
        Categories: 'solar', 'lunar', 'quests', 'progression'
        """
        if not self.data:
            return True

        preferences = self.data.get("preferences", {})
        if not preferences:
            return True

        notifications = preferences.get("notifications", {})
        # Smart Default: If key logic is missing, return True
        return notifications.get(category, True)
