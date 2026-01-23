"""
GUTTERS Query Module Schemas

Data models for profile queries and responses.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request to query the user's profile."""
    
    question: str = Field(
        description="The user's question about their cosmic profile",
        min_length=3,
        max_length=1000
    )
    model: str | None = Field(
        default=None,
        description="Optional model override. If not provided, uses user preference or default."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why do I struggle with authority figures?",
                "model": None
            }
        }


class QueryResponse(BaseModel):
    """Response to a profile query."""
    
    question: str = Field(description="Original question")
    answer: str = Field(description="Generated answer")
    modules_consulted: list[str] = Field(
        description="Modules whose data was used to answer"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the answer (0-1)"
    )
    model_used: str = Field(description="LLM model used")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why do I struggle with authority figures?",
                "answer": "Your Saturn placement combined with your Projector type suggests...",
                "modules_consulted": ["astrology", "human_design"],
                "confidence": 0.85,
                "model_used": "anthropic/claude-3.5-sonnet",
                "generated_at": "2024-01-23T10:30:00Z"
            }
        }
