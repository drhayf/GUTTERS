"""
Trace context manager for Observable AI.

Provides context manager for building activity traces.
"""

from contextvars import ContextVar
from typing import Optional
import uuid
from datetime import datetime, UTC

from .models import ActivityTrace, ThinkingStep, ToolCall, ToolType, ModelInfo

# Context variable to store current trace
_current_trace: ContextVar[Optional[ActivityTrace]] = ContextVar("current_trace", default=None)


class TraceContext:
    """
    Context manager for activity tracing.

    Usage:
        async with TraceContext() as trace:
            trace.think("Checking Active Memory...")
            result = await active_memory.get_synthesis(user_id)
            trace.tool_call(ToolType.ACTIVE_MEMORY, "get_synthesis", 5, "Found synthesis")

            trace.think("Generating response...")
            response = await llm.ainvoke([...])
            trace.model_call("anthropic", "claude-3.5-sonnet", 0.7, 1000, 500, 3000)

        # trace is now complete with all steps
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        if enabled:
            self.trace = ActivityTrace(
                trace_id=str(uuid.uuid4()),
                thinking_steps=[],
                tools_used=[],
                total_latency_ms=0,
                confidence=0.85,
                started_at=datetime.now(UTC),
            )
        else:
            self.trace = None

    async def __aenter__(self):
        """Start trace."""
        if self.enabled:
            _current_trace.set(self.trace)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete trace."""
        if self.enabled and self.trace:
            self.trace.completed_at = datetime.now(UTC)

            # Calculate total latency
            if self.trace.completed_at and self.trace.started_at:
                delta = self.trace.completed_at - self.trace.started_at
                self.trace.total_latency_ms = int(delta.total_seconds() * 1000)

            _current_trace.set(None)
        return False  # Don't suppress exceptions

    def think(self, description: str):
        """Add thinking step."""
        if self.enabled and self.trace:
            step = ThinkingStep(step=len(self.trace.thinking_steps) + 1, description=description)
            self.trace.thinking_steps.append(step)

    def tool_call(self, tool: ToolType, operation: str, latency_ms: int, result_summary: str, metadata: dict = None):
        """Record tool usage."""
        if self.enabled and self.trace:
            call = ToolCall(
                tool=tool,
                operation=operation,
                latency_ms=latency_ms,
                result_summary=result_summary,
                metadata=metadata or {},
            )
            self.trace.tools_used.append(call)

    def model_call(
        self,
        provider: str,
        model: str,
        temperature: float,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        cost_usd: float = None,
    ):
        """Record LLM usage."""
        if self.enabled and self.trace:
            self.trace.model_info = ModelInfo(
                provider=provider,
                model=model,
                temperature=temperature,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                cost_estimate_usd=cost_usd,
            )

    def set_confidence(self, confidence: float):
        """Set final confidence score."""
        if self.enabled and self.trace:
            self.trace.confidence = confidence

    def get_trace(self) -> Optional[ActivityTrace]:
        """Get completed trace."""
        return self.trace


def get_current_trace() -> Optional[ActivityTrace]:
    """Get current active trace (if any)."""
    return _current_trace.get()
