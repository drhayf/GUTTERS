"""
Genesis Uncertainty Models

Core Pydantic models for declaring uncertainties in calculation results.
Modules use these to communicate what they're uncertain about and how
those uncertainties can be refined through conversation.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UncertaintyField(BaseModel):
    """
    A single uncertain field from a calculation module.
    
    Represents one piece of data that the module couldn't determine
    with certainty (e.g., rising sign when birth time is unknown).
    
    Example:
        UncertaintyField(
            field="rising_sign",
            module="astrology",
            candidates={"Leo": 0.25, "Virgo": 0.25, "Libra": 0.25, "Scorpio": 0.25},
            confidence_threshold=0.80,
            refinement_strategies=["morning_routine", "first_impression"]
        )
    """
    
    field: str = Field(
        description="Field name (e.g., 'rising_sign', 'type')"
    )
    module: str = Field(
        description="Module that owns this field (e.g., 'astrology', 'human_design')"
    )
    candidates: dict[str, float] = Field(
        description="Possible values with probability scores (must sum to ~1.0)"
    )
    confidence_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Confidence level at which to consider the field confirmed"
    )
    refinement_strategies: list[str] = Field(
        default_factory=list,
        description="Strategy names that can refine this uncertainty"
    )
    
    @property
    def current_confidence(self) -> float:
        """Highest confidence among all candidates."""
        return max(self.candidates.values()) if self.candidates else 0.0
    
    @property
    def is_confirmed(self) -> bool:
        """True if current confidence meets threshold."""
        return self.current_confidence >= self.confidence_threshold
    
    @property
    def best_candidate(self) -> str | None:
        """Candidate with highest probability."""
        if not self.candidates:
            return None
        return max(self.candidates, key=self.candidates.get)


class UncertaintyDeclaration(BaseModel):
    """
    Complete uncertainty declaration from a calculation module.
    
    Aggregates all uncertain fields from a single module's calculation,
    along with session tracking and persistence metadata.
    
    Example:
        UncertaintyDeclaration(
            module="astrology",
            user_id=42,
            session_id="conv-abc123",
            fields=[rising_sign_uncertainty],
            source_accuracy="probabilistic",
            declared_at=datetime.now(),
            last_updated=datetime.now()
        )
    """
    
    module: str = Field(
        description="Module name that produced this declaration"
    )
    user_id: int = Field(
        description="User ID (FK to User model)"
    )
    session_id: str = Field(
        description="Conversation/session ID for tracking refinement context"
    )
    fields: list[UncertaintyField] = Field(
        default_factory=list,
        description="All uncertain fields from this module"
    )
    source_accuracy: Literal["probabilistic", "partial", "solar"] = Field(
        description="Accuracy level of the source calculation"
    )
    declared_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this declaration was first created"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this declaration was last modified"
    )
    stored_in_profile: bool = Field(
        default=False,
        description="Whether this has been persisted to UserProfile.data"
    )
    
    @property
    def has_uncertainties(self) -> bool:
        """True if there are any uncertain fields."""
        return len(self.fields) > 0
    
    @property
    def unconfirmed_fields(self) -> list[UncertaintyField]:
        """Fields that haven't reached confirmation threshold."""
        return [f for f in self.fields if not f.is_confirmed]
    
    @property
    def confirmed_fields(self) -> list[UncertaintyField]:
        """Fields that have reached confirmation threshold."""
        return [f for f in self.fields if f.is_confirmed]
    
    def get_field(self, field_name: str) -> UncertaintyField | None:
        """Get a specific field by name."""
        for field in self.fields:
            if field.field == field_name:
                return field
        return None
    
    def update_field_confidence(
        self, 
        field_name: str, 
        new_candidates: dict[str, float]
    ) -> bool:
        """
        Update confidence scores for a specific field.
        
        Returns True if field was found and updated.
        """
        field = self.get_field(field_name)
        if field:
            field.candidates = new_candidates
            self.last_updated = datetime.utcnow()
            return True
        return False
    
    def to_storage_dict(self) -> dict:
        """
        Convert to dictionary for storage in UserProfile.data.
        
        Serializes datetime objects to ISO format for JSON storage.
        """
        return {
            "module": self.module,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "fields": [f.model_dump() for f in self.fields],
            "source_accuracy": self.source_accuracy,
            "declared_at": self.declared_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "stored_in_profile": True,  # Will be true after storage
        }
    
    @classmethod
    def from_storage_dict(cls, data: dict) -> "UncertaintyDeclaration":
        """Reconstruct from stored dictionary."""
        return cls(
            module=data["module"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            fields=[UncertaintyField(**f) for f in data["fields"]],
            source_accuracy=data["source_accuracy"],
            declared_at=datetime.fromisoformat(data["declared_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            stored_in_profile=data.get("stored_in_profile", True),
        )
