from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.database import Base


class PlayerStats(Base):
    """
    Tracks user progression, experience points, and synchronization momentum.
    Part of the "Solo Leveling" / Evolution HUD system.
    """

    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)

    level: Mapped[int] = mapped_column(Integer, default=1)
    experience_points: Mapped[int] = mapped_column(Integer, default=0)

    # 7-day Weighted Moving Average (0.0 - 1.0)
    sync_rate: Mapped[float] = mapped_column(Float, default=0.0)

    streak_count: Mapped[int] = mapped_column(Integer, default=0)

    # Stores last 7 days of raw sync scores for WMA calculation
    # Format: [{"date": "2026-01-26", "score": 0.8}, ...]
    sync_history: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(UTC), default=lambda: datetime.now(UTC)
    )

    user = relationship("User", back_populates="progression", lazy="select")

    @property
    def rank(self) -> str:
        """Derives rank from level."""
        if self.level >= 51:
            return "S"
        if self.level >= 41:
            return "A"
        if self.level >= 31:
            return "B"
        if self.level >= 21:
            return "C"
        if self.level >= 11:
            return "D"
        return "E"

    @property
    def xp_to_next_level(self) -> int:
        """Threshold formula: XP = Level * 1000 * 1.5^(Level-1)"""
        import math

        threshold = int(self.level * 1000 * math.pow(1.5, self.level - 1))
        return max(0, threshold - self.experience_points)
