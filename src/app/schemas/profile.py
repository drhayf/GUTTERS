"""
GUTTERS Profile Schemas

Pydantic schemas for birth data input, validation, and profile responses.
These schemas ensure accurate data for cosmic calculations.
"""
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BirthDataInput(BaseModel):
    """
    User-provided birth data for cosmic profile calculation.
    
    Birth time is optional but recommended for accurate calculations.
    Location will be geocoded to get coordinates and timezone.
    
    Example:
        {
            "name": "John Doe",
            "birth_date": "1990-05-15",
            "birth_time": "14:30:00",
            "birth_location": "San Francisco, CA, USA"
        }
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(
        min_length=1, 
        max_length=100,
        description="User's full name"
    )
    birth_date: date = Field(
        description="Birth date (YYYY-MM-DD)"
    )
    birth_time: time | None = Field(
        default=None,
        description="Birth time (HH:MM:SS). Optional but recommended for accurate house placements."
    )
    birth_location: str = Field(
        min_length=1,
        max_length=255,
        description="Birth location (city, state/country). Will be geocoded."
    )
    timezone: str | None = Field(
        default=None,
        description="IANA timezone (e.g., 'America/New_York'). Auto-detected if not provided."
    )
    
    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Ensure birth date is not in the future."""
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        # Reasonable minimum date (ephemeris typically starts ~1800)
        if v.year < 1800:
            raise ValueError("Birth date must be after 1800")
        return v
    
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        """Validate timezone format if provided."""
        if v is None:
            return v
        # Basic validation - should contain '/'
        if "/" not in v and v not in ("UTC", "GMT"):
            raise ValueError(
                "Timezone must be in IANA format (e.g., 'America/New_York', 'Europe/London')"
            )
        return v


class BirthDataComplete(BirthDataInput):
    """
    Complete birth data with geocoded coordinates and timezone.
    
    Used internally after geocoding the user's birth location.
    All fields required for accurate cosmic calculations.
    """
    birth_latitude: float = Field(
        ge=-90,
        le=90,
        description="Birth location latitude in decimal degrees"
    )
    birth_longitude: float = Field(
        ge=-180,
        le=180,
        description="Birth location longitude in decimal degrees"
    )
    birth_timezone: str = Field(
        description="IANA timezone for birth location (e.g., 'America/Los_Angeles')"
    )
    birth_location_formatted: str = Field(
        description="Geocoded address (normalized/formatted)"
    )
    
    @property
    def has_birth_time(self) -> bool:
        """Check if exact birth time is known"""
        return self.birth_time is not None
    
    @property
    def accuracy_level(self) -> str:
        """Determine calculation accuracy level"""
        return "full" if self.has_birth_time else "solar"
    
    @property
    def missing_fields(self) -> list[str]:
        """List fields that affect calculation accuracy"""
        missing = []
        if self.birth_time is None:
            missing.append("birth_time")
        return missing


class UserProfileRead(BaseModel):
    """
    User cosmic profile read schema.
    
    Contains all calculated module profiles as JSONB fields.
    Each module adds its section during profile calculation.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    
    # Module profile data (from JSONB)
    # Each module contributes its own section
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="All module profile data"
    )
    
    created_at: datetime
    updated_at: datetime | None = None
    
    # Convenience accessors for common modules
    @property
    def natal_chart(self) -> dict[str, Any] | None:
        """Get astrology natal chart data."""
        return self.data.get("astrology")
    
    @property
    def human_design(self) -> dict[str, Any] | None:
        """Get Human Design profile data."""
        return self.data.get("human_design")
    
    @property
    def numerology(self) -> dict[str, Any] | None:
        """Get numerology calculations."""
        return self.data.get("numerology")
    
    @property
    def vedic_astrology(self) -> dict[str, Any] | None:
        """Get Vedic astrology data."""
        return self.data.get("vedic_astrology")
    
    @property
    def gene_keys(self) -> dict[str, Any] | None:
        """Get Gene Keys profile."""
        return self.data.get("gene_keys")


class UserProfileCreate(BaseModel):
    """Schema for creating a new user profile."""
    user_id: int
    data: dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile data."""
    data: dict[str, Any] | None = None


class BirthDataUpdate(BaseModel):
    """Schema for updating birth data (partial updates allowed)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str | None = Field(default=None, min_length=1, max_length=100)
    birth_date: date | None = None
    birth_time: time | None = None
    birth_location: str | None = Field(default=None, min_length=1, max_length=255)
    birth_latitude: float | None = Field(default=None, ge=-90, le=90)
    birth_longitude: float | None = Field(default=None, ge=-180, le=180)
    birth_timezone: str | None = None
