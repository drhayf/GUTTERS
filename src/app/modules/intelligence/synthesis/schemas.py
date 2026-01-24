"""
GUTTERS Synthesis Module Schemas

Data models for profile synthesis across all calculation modules.
"""

from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class SynthesisPattern(BaseModel):
    """A pattern found across multiple modules."""

    pattern_name: str = Field(description="Name of the identified pattern")
    modules_involved: list[str] = Field(description="Modules that contribute to this pattern")
    description: str = Field(description="Description of the pattern and its meaning")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this pattern (0-1)")


class UnifiedProfile(BaseModel):
    """Synthesized profile across all modules."""

    user_id: int
    modules_included: list[str] = Field(description="List of modules included in synthesis")
    synthesis: str = Field(description="Full LLM-generated synthesis text")
    themes: list[str] = Field(default_factory=list, description="Key themes identified")
    patterns: list[SynthesisPattern] = Field(default_factory=list, description="Cross-system patterns")
    model_used: str = Field(description="LLM model used for synthesis")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "modules_included": ["astrology", "human_design", "numerology"],
                "synthesis": "Your Leo Sun combined with your Projector type suggests...",
                "themes": ["leadership", "recognition", "wisdom sharing"],
                "patterns": [
                    {
                        "pattern_name": "Recognition Seeker",
                        "modules_involved": ["astrology", "human_design"],
                        "description": "Leo Sun craves recognition while Projector waits for invitation",
                        "confidence": 0.85,
                    }
                ],
                "model_used": "anthropic/claude-3.5-sonnet",
                "generated_at": "2024-01-23T10:30:00Z",
            }
        }
    )


class ModuleInsights(BaseModel):
    """Extracted insights from a single module."""

    module_name: str
    key_points: list[str] = Field(description="Key insights from this module")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw module data")


class SynthesisRequest(BaseModel):
    """Request to trigger synthesis."""

    model: str | None = Field(
        default=None, description="Optional model override. If not provided, uses user preference or default."
    )
    force_regenerate: bool = Field(default=False, description="Force regeneration even if synthesis exists")


class SynthesisResponse(BaseModel):
    """Response from synthesis endpoint."""

    status: str = Field(description="Status: 'queued', 'completed', 'error'")
    message: str | None = Field(default=None, description="Additional message")
    model: str | None = Field(default=None, description="Model being used")
    synthesis: UnifiedProfile | None = Field(default=None, description="Synthesis if completed synchronously")
