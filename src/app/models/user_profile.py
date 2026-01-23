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

from ..core.db.database import Base

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
    __table_args__ = (
        Index("ix_user_profile_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    
    # Relationship back to user
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        default=None,
        init=False,
    )
    
    # JSONB containing all module profile data
    data: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default_factory=lambda: datetime.now(UTC),
        init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        default=None,
        init=False
    )
