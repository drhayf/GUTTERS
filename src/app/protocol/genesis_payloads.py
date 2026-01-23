"""
Genesis Event Payload Schemas

Typed Pydantic models for Genesis event payloads.
These ensure type safety when publishing/consuming Genesis events.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GenesisUncertaintyPayload(BaseModel):
    """
    Payload for GENESIS_UNCERTAINTY_DECLARED event.
    
    Published when a module declares uncertainties after calculation.
    """
    user_id: int = Field(description="User ID")
    session_id: str = Field(description="Conversation/session ID")
    module: str = Field(description="Module that declared uncertainties")
    fields: list[dict[str, Any]] = Field(
        description="Serialized UncertaintyField objects"
    )
    source_accuracy: str = Field(description="Source calculation accuracy level")
    declared_at: str = Field(description="ISO datetime when declared")
    
    @classmethod
    def from_declaration(cls, declaration: Any) -> "GenesisUncertaintyPayload":
        """Create payload from UncertaintyDeclaration."""
        return cls(
            user_id=declaration.user_id,
            session_id=declaration.session_id,
            module=declaration.module,
            fields=[f.model_dump() for f in declaration.fields],
            source_accuracy=declaration.source_accuracy,
            declared_at=declaration.declared_at.isoformat(),
        )


class GenesisRefinementRequestedPayload(BaseModel):
    """
    Payload for GENESIS_REFINEMENT_REQUESTED event.
    
    Published when Genesis prepares a refinement probe for conversation.
    """
    user_id: int = Field(description="User ID")
    session_id: str = Field(description="Conversation/session ID")
    field: str = Field(description="Field being refined (e.g., 'rising_sign')")
    module: str = Field(description="Module that owns the field")
    strategy: str = Field(description="Refinement strategy being used")
    probe_question: str = Field(description="Question to ask the user")


class GenesisConfidenceUpdatedPayload(BaseModel):
    """
    Payload for GENESIS_CONFIDENCE_UPDATED event.
    
    Published when field confidence changes after refinement.
    """
    user_id: int = Field(description="User ID")
    session_id: str = Field(description="Conversation/session ID")
    field: str = Field(description="Field that was updated")
    module: str = Field(description="Module that owns the field")
    candidate: str = Field(description="Candidate whose confidence changed")
    old_confidence: float = Field(ge=0.0, le=1.0, description="Previous confidence")
    new_confidence: float = Field(ge=0.0, le=1.0, description="New confidence")


class GenesisFieldConfirmedPayload(BaseModel):
    """
    Payload for GENESIS_FIELD_CONFIRMED event.
    
    Published when a field reaches confirmation threshold.
    Modules should subscribe to this to trigger recalculation.
    """
    user_id: int = Field(description="User ID")
    session_id: str = Field(description="Conversation/session ID")
    field: str = Field(description="Field that was confirmed")
    module: str = Field(description="Module that owns the field")
    confirmed_value: str = Field(description="The confirmed value")
    confidence: float = Field(ge=0.0, le=1.0, description="Confirmation confidence")
    trigger_recalculation: bool = Field(
        default=True,
        description="Whether modules should recalculate with confirmed data"
    )
    
    # Additional context for recalculation
    refinement_source: str = Field(
        default="conversation",
        description="How the confirmation was achieved"
    )
    confirmed_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO datetime of confirmation"
    )
