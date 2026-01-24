from pydantic import BaseModel
from datetime import datetime
from typing import List

class SynthesisGeneratedPayload(BaseModel):
    """Payload for SYNTHESIS_GENERATED event."""
    user_id: int
    modules: List[str]
    patterns_detected: int
    generated_at: str

class HypothesisGeneratedPayload(BaseModel):
    """Payload for HYPOTHESIS_GENERATED event."""
    user_id: int
    hypothesis_id: str
    hypothesis_type: str
    confidence: float
    generated_at: str

class HypothesisConfirmedPayload(BaseModel):
    """Payload for HYPOTHESIS_CONFIRMED event."""
    user_id: int
    hypothesis_id: str
    hypothesis_type: str
    final_confidence: float
    confirmed_at: str

class HypothesisUpdatedPayload(BaseModel):
    """Payload for HYPOTHESIS_UPDATED event."""
    user_id: int
    hypothesis_id: str
    confidence_before: float
    confidence_after: float
    reasoning: str
