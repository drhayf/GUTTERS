"""
GUTTERS System Configuration Model

Database-driven configuration for modules, AI prompts, and system parameters.
No hardcoded configurations - everything loaded from this table.
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class SystemConfiguration(Base):
    """
    Module and system configuration storage.
    
    Used to store:
    - Module-specific settings (orbs, thresholds, parameters)
    - AI prompt templates
    - Feature flags
    - Dynamic configuration that shouldn't be hardcoded
    
    Example config for astrology module:
    {
        "orb_tolerance": 8,
        "house_system": "placidus",
        "aspect_types": ["conjunction", "opposition", "trine", "square", "sextile"],
        "include_asteroids": false
    }
    """
    __tablename__ = "system_configuration"
    __table_args__ = (
        Index("ix_system_configuration_module_name", "module_name", unique=True),
        Index("ix_system_configuration_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    # Module identifier (unique)
    module_name: Mapped[str] = mapped_column(String(100), unique=True)
    
    # JSONB configuration data
    config: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    
    # AI prompt template (optional)
    prompt_template: Mapped[str | None] = mapped_column(Text, default=None)
    
    # Version for optimistic locking
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Active flag for enabling/disabling modules
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
