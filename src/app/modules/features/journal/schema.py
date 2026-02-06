"""
Journal entry schema.

This defines what Journal Module (Phase 7) WILL produce.
For now, we use this schema for deterministic seed data in tests.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class JournalEntry(BaseModel):
    """
    Schema for journal entries stored in UserProfile.data['journal_entries'].

    When Journal Module is built (Phase 7), it will produce this exact structure.
    """
    id: str = Field(description="UUID for this entry")
    timestamp: datetime = Field(description="When entry was created")
    text: str = Field(description="Entry content")
    mood_score: int = Field(ge=1, le=10, description="Mood rating 1-10")
    energy_score: int = Field(ge=1, le=10, description="Energy rating 1-10")
    tags: list[str] = Field(default_factory=list, description="Tags like 'anxiety', 'headache'")
    themes: list[str] = Field(default_factory=list, description="Themes like 'work', 'health'")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-15T14:30:00Z",
                "text": "Felt anxious during team meeting. Had headache in afternoon.",
                "mood_score": 4,
                "energy_score": 5,
                "tags": ["anxiety", "headache", "work"],
                "themes": ["work", "health"]
            }
        }
