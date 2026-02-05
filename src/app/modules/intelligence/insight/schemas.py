from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from src.app.models.insight import PromptPhase, PromptStatus


class TriggerContext(BaseModel):
    """Context that triggered the insight."""

    source_type: str  # 'observer', 'hypothesis', 'cosmic_event'
    source_id: Optional[str] = None
    metric: str  # 'kp_index', 'moon_phase'
    value: Any
    timestamp: datetime


class ReflectionPromptCreate(BaseModel):
    """Payload to create a prompt."""

    prompt_text: str
    topic: str
    event_phase: PromptPhase
    trigger_context: Dict[str, Any]
    expires_at: Optional[datetime] = None


class ReflectionPromptRead(BaseModel):
    """Reading a prompt."""

    id: int
    user_id: int
    prompt_text: str
    topic: str
    event_phase: PromptPhase
    status: PromptStatus
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class JournalEntryCreate(BaseModel):
    """Creating a journal entry."""

    content: str
    mood_score: Optional[int] = None
    tags: List[str] = []
    prompt_id: Optional[int] = None
