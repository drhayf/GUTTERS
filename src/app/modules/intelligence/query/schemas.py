from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from ..trace.models import ActivityTrace
from ..generative_ui.models import ComponentSpec


class QueryRequest(BaseModel):
    """Request to query the user's profile."""

    question: str = Field(description="The user's question about their cosmic profile", min_length=3, max_length=1000)
    model: str | None = Field(
        default=None, description="Optional model override. If not provided, uses user preference or default."
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"question": "Why do I struggle with authority figures?", "model": None}}
    )


class QueryResponse(BaseModel):
    """Response to a profile query with trace data."""

    question: str = Field(description="Original question")
    answer: str = Field(description="Generated answer")
    modules_consulted: list[str] = Field(description="Modules whose data was used to answer")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the answer (0-1)")
    model_used: str = Field(description="LLM model used")
    sources_used: int = Field(default=0, description="Number of external sources/embeddings used")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace: Optional[ActivityTrace] = Field(default=None, description="Observable AI activity trace")
    component: Optional[ComponentSpec] = Field(default=None, description="Interactive UI component")
