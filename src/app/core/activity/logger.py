"""
GUTTERS Activity Logger

Logs LLM activity for observability and thought process transparency.
Stores call details, reasoning, and tool usage.

Example:
    >>> from src.app.core.activity.logger import get_activity_logger
    >>> logger = get_activity_logger()
    >>> await logger.log_llm_call(
    ...     trace_id="trace-123",
    ...     model_id="xiaomi/mimo-v2-flash:free",
    ...     prompt="Interpret this chart...",
    ...     response="Based on the positions...",
    ...     tools_called=["calculate_natal_chart"],
    ...     reasoning="Analyzing planetary aspects..."
    ... )
"""
import json
import time
from typing import Any

import redis.asyncio as redis

from ...core.config import settings


class ActivityLogger:
    """
    Logs LLM activity for observability.
    
    Records prompts, responses, tool calls, and reasoning
    for debugging and transparency.
    """
    
    TTL_SECONDS = 86400  # 24 hours
    
    def __init__(self):
        """Initialize logger (call initialize() to connect to Redis)."""
        self.redis_client: redis.Redis | None = None
    
    async def initialize(self) -> None:
        """Connect to Redis."""
        self.redis_client = redis.Redis(
            host=settings.REDIS_CACHE_HOST,
            port=settings.REDIS_CACHE_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
        )
    
    async def cleanup(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def log_llm_call(
        self,
        trace_id: str,
        model_id: str,
        prompt: str,
        response: str,
        tools_called: list[str] | None = None,
        reasoning: str | None = None,
        duration_ms: float | None = None,
        tokens_used: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an LLM call for observability.
        
        Args:
            trace_id: Trace ID to associate with
            model_id: Model ID used (e.g., "xiaomi/mimo-v2-flash:free")
            prompt: The prompt sent to LLM
            response: The response received
            tools_called: List of tool names called
            reasoning: Optional reasoning/thought process
            duration_ms: Optional call duration in milliseconds
            tokens_used: Optional token count
            metadata: Optional additional metadata
        """
        if not self.redis_client:
            await self.initialize()
        
        timestamp = time.time()
        
        # Build activity record
        activity = {
            "timestamp": timestamp,
            "trace_id": trace_id,
            "model_id": model_id,
            "prompt": prompt,
            "response": response,
            "tools_called": tools_called or [],
            "reasoning": reasoning,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
            "metadata": metadata or {},
        }
        
        # Store in Redis
        key = f"activity:{trace_id}:llm:{timestamp}"
        await self.redis_client.set(key, json.dumps(activity), ex=self.TTL_SECONDS)
        
        # Add to trace index
        index_key = f"activity:{trace_id}:index"
        await self.redis_client.zadd(index_key, {key: timestamp})
        await self.redis_client.expire(index_key, self.TTL_SECONDS)
    
    async def get_activity(self, trace_id: str) -> list[dict[str, Any]]:
        """
        Retrieve all LLM activity for a trace.
        
        Args:
            trace_id: Trace ID to retrieve
            
        Returns:
            List of activity records, sorted by timestamp
        """
        if not self.redis_client:
            await self.initialize()
        
        # Get all activity keys for this trace
        index_key = f"activity:{trace_id}:index"
        activity_keys = await self.redis_client.zrange(index_key, 0, -1)
        
        if not activity_keys:
            # Fallback: scan for keys
            pattern = f"activity:{trace_id}:llm:*"
            activity_keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                activity_keys.append(key)
        
        # Retrieve and parse activities
        activities = []
        for key in activity_keys:
            data = await self.redis_client.get(key)
            if data:
                try:
                    activities.append(json.loads(data))
                except json.JSONDecodeError:
                    pass
        
        # Sort by timestamp
        activities.sort(key=lambda a: a.get("timestamp", 0))
        
        return activities
    
    async def get_recent_activity(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get most recent LLM activity across all traces.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent activity records
        """
        if not self.redis_client:
            await self.initialize()
        
        activities = []
        pattern = "activity:*:llm:*"
        
        async for key in self.redis_client.scan_iter(match=pattern):
            data = await self.redis_client.get(key)
            if data:
                try:
                    activities.append(json.loads(data))
                except json.JSONDecodeError:
                    pass
            
            if len(activities) >= limit * 2:
                break
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
        
        return activities[:limit]
    
    async def log_activity(
        self,
        trace_id: str,
        agent: str,
        activity_type: str,
        details: dict[str, Any],
    ) -> None:
        """
        Log a general activity for observability.
        
        More flexible than log_llm_call - can log any type of activity.
        
        Args:
            trace_id: Trace ID to associate with
            agent: Agent/module name (e.g., "genesis.engine", "astrology.calculator")
            activity_type: Type of activity (e.g., "probe_generated", "confidence_updated")
            details: Activity-specific details
        """
        if not self.redis_client:
            await self.initialize()
        
        timestamp = time.time()
        
        activity = {
            "timestamp": timestamp,
            "trace_id": trace_id,
            "agent": agent,
            "activity_type": activity_type,
            "details": details,
        }
        
        # Store in Redis
        key = f"activity:{trace_id}:{agent}:{timestamp}"
        await self.redis_client.set(key, json.dumps(activity), ex=self.TTL_SECONDS)
        
        # Add to trace index
        index_key = f"activity:{trace_id}:index"
        await self.redis_client.zadd(index_key, {key: timestamp})
        await self.redis_client.expire(index_key, self.TTL_SECONDS)
        
        # Also add to agent-specific index for filtering
        agent_index = f"activity_by_agent:{agent}"
        await self.redis_client.zadd(agent_index, {key: timestamp})
        await self.redis_client.expire(agent_index, self.TTL_SECONDS)
    
    async def get_activities_by_agent(
        self,
        agent: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get activities for a specific agent."""
        if not self.redis_client:
            await self.initialize()
        
        index_key = f"activity_by_agent:{agent}"
        activity_keys = await self.redis_client.zrange(index_key, -limit, -1, desc=True)
        
        activities = []
        for key in activity_keys:
            data = await self.redis_client.get(key)
            if data:
                try:
                    activities.append(json.loads(data))
                except json.JSONDecodeError:
                    pass
        
        return activities


# Singleton instance
_activity_logger: ActivityLogger | None = None


def get_activity_logger() -> ActivityLogger:
    """
    Get the singleton ActivityLogger instance.
    
    Returns:
        Global ActivityLogger instance
        
    Example:
        >>> logger = get_activity_logger()
        >>> await logger.log_llm_call(...)
    """
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger()
    return _activity_logger
