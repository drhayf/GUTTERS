"""
Activity trace models for Observable AI.

Tracks thinking steps, tool usage, and model metadata.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    """Types of tools the AI can use."""

    ACTIVE_MEMORY = "active_memory"
    VECTOR_SEARCH = "vector_search"
    OBSERVER = "observer"
    HYPOTHESIS = "hypothesis"
    TRACKING_SOLAR = "tracking_solar"
    TRACKING_LUNAR = "tracking_lunar"
    TRACKING_TRANSIT = "tracking_transit"
    SYNTHESIS = "synthesis"
    GENESIS = "genesis"
    DATABASE = "database"
    CALCULATOR = "calculator"


class ToolCall(BaseModel):
    """Record of a tool being called."""

    tool: ToolType
    operation: str  # "get_master_synthesis", "search", etc.
    latency_ms: int
    result_summary: str  # "Found 3 entries", "Pattern #42", etc.
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModelInfo(BaseModel):
    """Information about the LLM used."""

    provider: str  # "anthropic", "openai", "openrouter"
    model: str  # "claude-3.5-sonnet", "gpt-4", etc.
    temperature: float
    max_tokens: Optional[int] = None
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_estimate_usd: Optional[float] = None


class ThinkingStep(BaseModel):
    """A step in the AI's reasoning process."""

    step: int
    description: str  # "Checking Active Memory...", "Analyzing patterns..."
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActivityTrace(BaseModel):
    """
    Complete trace of AI activity for a single query.

    This is stored in ChatMessage.metadata['trace'] for transparency.
    """

    trace_id: str
    thinking_steps: list[ThinkingStep] = Field(default_factory=list)
    tools_used: list[ToolCall] = Field(default_factory=list)
    model_info: Optional[ModelInfo] = None
    total_latency_ms: int = 0
    confidence: float = Field(ge=0.0, le=1.0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
