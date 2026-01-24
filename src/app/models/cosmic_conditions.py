"""
GUTTERS Cosmic Conditions Model

Stores current and historical cosmic conditions from tracking modules.
Solar activity, lunar phases, planetary transits, etc.
"""

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class CosmicConditions(Base):
    """
    Real-time and historical cosmic conditions.

    Populated by tracking modules (solar, lunar, planetary_transits).
    Used for synthesis and correlation analysis.

    condition_type values:
    - "solar": Solar activity (KP index, flares, storms)
    - "lunar": Moon phase, sign, void-of-course
    - "planetary": Transits, retrogrades, aspects

    Example data for solar condition:
    {
        "kp_index": 5.2,
        "solar_wind_speed": 450,
        "storm_level": "G1",
        "flare_activity": "M-class"
    }
    """

    __tablename__ = "cosmic_conditions"
    __table_args__ = (
        CheckConstraint("condition_type IN ('solar', 'lunar', 'planetary', 'other')", name="check_condition_type"),
        Index("ix_cosmic_conditions_type_timestamp", "condition_type", "timestamp"),
        Index("ix_cosmic_conditions_timestamp", "timestamp"),
    )

    # Primary key
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    # Non-nullable fields WITHOUT defaults (must come first for dataclass ordering)
    condition_type: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(100))

    # Fields WITH defaults (must come after non-default fields)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
