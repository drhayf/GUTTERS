"""
GUTTERS Active Working Memory

Redis-backed memory cache for current synthesized state, cosmic conditions,
and other frequently accessed data.

This is the "hot" cache layer for GUTTERS - fast access to current state
without hitting the database. Used for synthesis results, cosmic tracking data,
and module outputs that need to be quickly accessible.
"""
import json
from typing import Any, Type, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from ...core.config import settings

T = TypeVar("T", bound=BaseModel)


class ActiveMemory:
    """
    Redis-backed active memory cache.
    
    Provides fast access to current system state with automatic TTL management.
    Supports both raw values and Pydantic model serialization.
    
    Example:
        >>> from app.core.memory.active_memory import get_active_memory
        >>> 
        >>> memory = get_active_memory()
        >>> await memory.initialize()
        >>> 
        >>> # Store raw data
        >>> await memory.set("cosmic:kp_index", 5.2, ttl=300)
        >>> kp = await memory.get("cosmic:kp_index")
        >>> 
        >>> # Store Pydantic models
        >>> synthesis = SynthesisResult(user_id=user_id, insights=[...])
        >>> await memory.set_json(f"synthesis:{user_id}", synthesis, ttl=3600)
        >>> cached = await memory.get_json(f"synthesis:{user_id}", SynthesisResult)
    """
    
    def __init__(self):
        """Initialize active memory (call initialize() to connect to Redis)."""
        self.redis_client: redis.Redis | None = None
    
    async def initialize(self) -> None:
        """
        Connect to Redis.
        
        Should be called during application startup.
        """
        redis_url = f"redis://{settings.REDIS_CACHE_HOST}:{settings.REDIS_CACHE_PORT}"
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async def cleanup(self) -> None:
        """
        Disconnect from Redis.
        
        Should be called during application shutdown.
        """
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Any | None:
        """
        Get a value from memory.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
            
        Example:
            >>> kp_index = await memory.get("cosmic:kp_index")
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")
        
        value = await self.redis_client.get(key)
        
        if value is None:
            return None
        
        # Try to parse as JSON, fall back to raw string
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Store a value in memory.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON-serialized if not a string)
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Example:
            >>> await memory.set("cosmic:kp_index", 5.2, ttl=300)
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")
        
        # Serialize value
        if isinstance(value, str):
            serialized = value
        else:
            serialized = json.dumps(value)
        
        await self.redis_client.set(key, serialized, ex=ttl)
    
    async def delete(self, key: str) -> None:
        """
        Delete a value from memory.
        
        Args:
            key: Cache key to delete
            
        Example:
            >>> await memory.delete("synthesis:user_123")
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")
        
        await self.redis_client.delete(key)
    
    async def get_json(self, key: str, model: Type[T]) -> T | None:
        """
        Get a Pydantic model from memory.
        
        Args:
            key: Cache key
            model: Pydantic model class to deserialize into
            
        Returns:
            Pydantic model instance or None if not found
            
        Example:
            >>> synthesis = await memory.get_json(
            ...     f"synthesis:{user_id}",
            ...     SynthesisResult
            ... )
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")
        
        value = await self.redis_client.get(key)
        
        if value is None:
            return None
        
        # Parse JSON and validate with Pydantic
        data = json.loads(value)
        return model.model_validate(data)
    
    async def set_json(self, key: str, value: BaseModel, ttl: int = 3600) -> None:
        """
        Store a Pydantic model in memory.
        
        Args:
            key: Cache key
            value: Pydantic model instance to store
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Example:
            >>> synthesis = SynthesisResult(user_id=user_id, insights=[...])
            >>> await memory.set_json(
            ...     f"synthesis:{user_id}",
            ...     synthesis,
            ...     ttl=3600
            ... )
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")
        
        # Serialize Pydantic model to JSON
        serialized = value.model_dump_json()
        await self.redis_client.set(key, serialized, ex=ttl)


# Singleton instance
_active_memory: ActiveMemory | None = None


def get_active_memory() -> ActiveMemory:
    """
    Get the singleton ActiveMemory instance.
    
    Returns:
        Global ActiveMemory instance
        
    Example:
        >>> from app.core.memory.active_memory import get_active_memory
        >>> memory = get_active_memory()
        >>> await memory.initialize()
        >>> await memory.set("key", "value")
    """
    global _active_memory
    if _active_memory is None:
        _active_memory = ActiveMemory()
    return _active_memory
