"""
GUTTERS Active Working Memory

Redis-backed memory cache for current synthesized state, cosmic conditions,
and other frequently accessed data.

This is the "hot" cache layer for GUTTERS - fast access to current state
without hitting the database. Used for synthesis results, cosmic tracking data,
and module outputs that need to be quickly accessible.

Three-Layer Memory Architecture:
    HOT MEMORY (Redis, 24h TTL):
        - Master synthesis
        - Last 10 conversations
        - Active session context

    WARM MEMORY (Redis, 7d TTL):
        - Module outputs (astrology, human_design, etc.)
        - User preferences

    COLD STORAGE (PostgreSQL):
        - UserProfile.data (permanent storage)
        - Full conversation history (last 1000)
"""

from __future__ import annotations
import json
import logging
import datetime as dt
from typing import Any, Type, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from ...core.config import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


# Singleton instance
_active_memory: ActiveMemory | None = None


class ActiveMemory:
    """
    Redis-backed active memory cache with three-layer architecture.

    Provides fast access to current system state with automatic TTL management.
    Supports both raw values and Pydantic model serialization.

    Memory layers:
        - HOT: Master synthesis, conversation history (24h TTL, <1ms reads)
        - WARM: Module outputs, preferences (7d TTL, <5ms reads)
        - COLD: PostgreSQL fallback (50-200ms reads)

    Example:
        >>> from src.app.core.memory.active_memory import get_active_memory
        >>>
        >>> memory = get_active_memory()
        >>> await memory.initialize()
        >>>
        >>> # Fast context retrieval
        >>> context = await memory.get_full_context(user_id=1)
        >>>
        >>> # Store synthesis
        >>> await memory.set_master_synthesis(1, "synthesis text", ["theme1"], ["astrology"])
    """

    # TTL constants
    HOT_TTL = 86400  # 24 hours (hot memory)
    WARM_TTL = 604800  # 7 days (warm memory)
    HISTORY_LIMIT = 10  # Keep last 10 conversations in Redis
    DB_HISTORY_LIMIT = 1000  # Keep last 1000 in PostgreSQL

    def __init__(self):
        """Initialize active memory (call initialize() to connect to Redis)."""
        self.redis_client: redis.Redis | None = None

    async def initialize(self) -> None:
        """
        Connect to Redis.

        Should be called during application startup.
        """
        self.redis_client = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)

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

    # =========================================================================
    # MASTER SYNTHESIS (Hot Memory)
    # =========================================================================

    async def get_master_synthesis(self, user_id: int) -> dict | None:
        """
        Get current master synthesis from hot memory.

        Returns synthesis with validity check - marks as 'stale' if >24h old.

        Args:
            user_id: User ID

        Returns:
            Synthesis dict with keys: synthesis, themes, generated_at,
            modules_included, validity. None if not found.

        Example:
            >>> synthesis = await memory.get_master_synthesis(user_id=1)
            >>> if synthesis and synthesis['validity'] == 'valid':
            ...     print(synthesis['synthesis'])
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:hot:synthesis:{user_id}"
        data = await self.get(key)

        if not data:
            return None

        # Check if stale (>24h old)
        try:
            generated_at = dt.datetime.fromisoformat(data["generated_at"])
            age = dt.datetime.now(dt.timezone.utc) - generated_at

            if age > dt.timedelta(hours=24):
                data["validity"] = "stale"
            else:
                data["validity"] = "valid"
        except (KeyError, ValueError):
            data["validity"] = "unknown"

        return data

    async def set_master_synthesis(
        self,
        user_id: int,
        synthesis: str,
        themes: list[str],
        modules_included: list[str],
        count_confirmed_theories: int = 0,
    ) -> None:
        """
        Store master synthesis in hot memory.

        Args:
            user_id: User ID
            synthesis: Synthesized text
            themes: List of identified themes
            modules_included: Modules that contributed to synthesis

        Example:
            >>> await memory.set_master_synthesis(
            ...     user_id=1,
            ...     synthesis="Your cosmic profile reveals...",
            ...     themes=["creativity", "leadership"],
            ...     modules_included=["astrology", "human_design"]
            ... )
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:hot:synthesis:{user_id}"

        data = {
            "synthesis": synthesis,
            "themes": themes,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "modules_included": modules_included,
            "count_confirmed_theories": count_confirmed_theories,
            "validity": "valid",
        }

        await self.set(key, data, ttl=self.HOT_TTL)
        logger.info(f"Stored master synthesis for user {user_id} with {len(modules_included)} modules")

    # =========================================================================
    # MODULE OUTPUTS (Warm Memory)
    # =========================================================================

    async def get_module_output(self, user_id: int, module_name: str) -> dict | None:
        """
        Get specific module's output from warm memory.

        Falls back to PostgreSQL (cold storage) if not cached.
        Automatically caches the result for future reads.

        Args:
            user_id: User ID
            module_name: Module name (astrology, human_design, numerology)

        Returns:
            Module output dict or None if not found

        Example:
            >>> astro = await memory.get_module_output(1, "astrology")
            >>> print(astro['planets'])
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:warm:module:{user_id}:{module_name}"
        data = await self.get(key)

        if data:
            return data

        # Fall back to database (cold storage)
        try:
            from sqlalchemy import select
            from ...core.db.database import async_get_db
            from ...models.user_profile import UserProfile

            async for db in async_get_db():
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
                profile = result.scalar_one_or_none()

                if profile and profile.data and module_name in profile.data:
                    module_data = profile.data[module_name]

                    # Cache for future reads
                    await self.set_module_output(user_id, module_name, module_data)

                    logger.debug(f"Cached {module_name} from database for user {user_id}")
                    return module_data
                break
        except Exception as e:
            logger.error(f"Failed to get module {module_name} from database: {e}")

        return None

    async def set_module_output(self, user_id: int, module_name: str, data: dict) -> None:
        """
        Cache module output in warm memory.

        Args:
            user_id: User ID
            module_name: Module name
            data: Module output data

        Example:
            >>> await memory.set_module_output(1, "astrology", astro_data)
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:warm:module:{user_id}:{module_name}"
        await self.set(key, data, ttl=self.WARM_TTL)

    # =========================================================================
    # CONVERSATION HISTORY (Dual Storage: Redis + PostgreSQL)
    # =========================================================================

    async def add_to_history(self, user_id: int, prompt: str, response: str) -> None:
        """
        Add prompt/response to conversation history.

        Stores in BOTH:
        - Redis: Last 10 conversations (fast access for LLM)
        - PostgreSQL: All conversations (permanent, last 1000)

        Args:
            user_id: User ID
            prompt: User's question/prompt
            response: System's response

        Example:
            >>> await memory.add_to_history(
            ...     user_id=1,
            ...     prompt="What should I focus on today?",
            ...     response="Based on your chart..."
            ... )
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        entry = {"prompt": prompt, "response": response, "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()}

        # 1. Add to Redis (hot memory, keep last 10)
        key = f"memory:hot:history:{user_id}"
        await self.redis_client.lpush(key, json.dumps(entry))
        await self.redis_client.ltrim(key, 0, self.HISTORY_LIMIT - 1)
        await self.redis_client.expire(key, self.HOT_TTL)

        # 2. Persist to PostgreSQL (permanent storage)
        await self._persist_history_to_database(user_id, entry)

    async def _persist_history_to_database(self, user_id: int, entry: dict) -> None:
        """Persist conversation entry to PostgreSQL (cold storage)."""
        try:
            from sqlalchemy import select
            from sqlalchemy.orm import make_transient
            from ...core.db.database import local_session
            from ...models.user_profile import UserProfile

            async with local_session() as db:
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
                profile = result.scalar_one_or_none()

                if profile:
                    if profile.data is None:
                        profile.data = {}

                    if "conversation_history" not in profile.data:
                        profile.data["conversation_history"] = []

                    profile.data["conversation_history"].append(entry)

                    # Trim to last 1000 entries
                    if len(profile.data["conversation_history"]) > self.DB_HISTORY_LIMIT:
                        profile.data["conversation_history"] = profile.data["conversation_history"][
                            -self.DB_HISTORY_LIMIT :
                        ]

                    # Force SQLAlchemy to detect JSONB change
                    from sqlalchemy.orm.attributes import flag_modified

                    flag_modified(profile, "data")

                    await db.commit()
                    logger.debug(f"Persisted conversation to database for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to persist conversation history: {e}")

    async def get_conversation_history(self, user_id: int, limit: int = 10) -> list[dict]:
        """
        Get recent conversation history from hot memory.

        Args:
            user_id: User ID
            limit: Maximum entries to return (default: 10)

        Returns:
            List of conversation entries (newest first)

        Example:
            >>> history = await memory.get_conversation_history(1, limit=5)
            >>> for entry in history:
            ...     print(entry['prompt'])
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:hot:history:{user_id}"

        # Ensure limit doesn't exceed our stored amount
        limit = min(limit, self.HISTORY_LIMIT)

        history_raw = await self.redis_client.lrange(key, 0, limit - 1)

        history = []
        for h in history_raw:
            try:
                history.append(json.loads(h))
            except json.JSONDecodeError:
                continue

        return history

    # =========================================================================
    # USER PREFERENCES (Dual Storage: Redis + PostgreSQL)
    # =========================================================================

    async def get_user_preferences(self, user_id: int) -> dict:
        """
        Get user preferences from warm memory.

        Falls back to PostgreSQL if not cached, then returns defaults
        if not found anywhere.

        Args:
            user_id: User ID

        Returns:
            User preferences dict

        Example:
            >>> prefs = await memory.get_user_preferences(user_id=1)
            >>> print(prefs['llm_model'])
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        # Try Redis first (fast)
        key = f"memory:warm:preferences:{user_id}"
        cached = await self.get(key)

        if cached:
            return cached

        # Try PostgreSQL (cold storage)
        try:
            from sqlalchemy import select
            from ...core.db.database import async_get_db
            from ...models.user_profile import UserProfile

            async for db in async_get_db():
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
                profile = result.scalar_one_or_none()

                if profile and profile.data and "preferences" in profile.data:
                    prefs = profile.data["preferences"]

                    # Cache for future reads
                    await self.set(key, prefs, ttl=self.WARM_TTL)

                    return prefs
                break
        except Exception as e:
            logger.error(f"Failed to get preferences from database: {e}")

        # Return defaults
        return {"llm_model": "anthropic/claude-3.5-sonnet", "synthesis_schedule": "daily", "synthesis_time": "08:00"}

    async def set_user_preference(self, user_id: int, pref_key: str, value: Any) -> None:
        """
        Update a single user preference.

        Updates in BOTH Redis (cache) and PostgreSQL (permanent).

        Args:
            user_id: User ID
            pref_key: Preference key (e.g., "llm_model")
            value: Preference value

        Example:
            >>> await memory.set_user_preference(1, "llm_model", "anthropic/claude-opus-4.5")
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        # Get current preferences
        prefs = await self.get_user_preferences(user_id)
        prefs[pref_key] = value

        # 1. Update in Redis (cache)
        redis_key = f"memory:warm:preferences:{user_id}"
        await self.set(redis_key, prefs, ttl=self.WARM_TTL)

        # 2. Persist to PostgreSQL
        try:
            from sqlalchemy import select
            from ...core.db.database import local_session
            from ...models.user_profile import UserProfile

            async with local_session() as db:
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
                profile = result.scalar_one_or_none()

                if profile:
                    if profile.data is None:
                        profile.data = {}

                    if "preferences" not in profile.data:
                        profile.data["preferences"] = {}

                    profile.data["preferences"][pref_key] = value

                    # Force SQLAlchemy to detect JSONB change
                    from sqlalchemy.orm.attributes import flag_modified

                    flag_modified(profile, "data")

                    await db.commit()
                    logger.debug(f"Persisted preference {pref_key} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to persist preference: {e}")

    # =========================================================================
    # CONTEXT ASSEMBLY
    # =========================================================================

    async def get_full_context(self, user_id: int) -> dict:
        """
        Assemble complete context for LLM.

        This is what the LLM sees - everything about the user assembled
        from hot and warm memory layers.

        Args:
            user_id: User ID

        Returns:
            Complete context dict with keys:
            - synthesis: Master synthesis (or None)
            - modules: Dict of module outputs
            - history: Recent conversation history
            - preferences: User preferences
            - assembled_at: Timestamp

        Example:
            >>> context = await memory.get_full_context(user_id=1)
            >>> print(context['synthesis']['themes'])
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        # Get master synthesis (hot memory)
        synthesis = await self.get_master_synthesis(user_id)

        # Get all module outputs (warm memory)
        modules: dict[str, Any] = {}
        for module_name in ["astrology", "human_design", "numerology"]:
            output = await self.get_module_output(user_id, module_name)
            if output:
                modules[module_name] = output

        # Get recent history (hot memory)
        history = await self.get_conversation_history(user_id, limit=5)

        # Get user preferences (warm memory)
        preferences = await self.get_user_preferences(user_id)

        return {
            "synthesis": synthesis,
            "modules": modules,
            "history": history,
            "preferences": preferences,
            "assembled_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

    # =========================================================================
    # CACHE INVALIDATION
    # =========================================================================

    async def invalidate_synthesis(self, user_id: int) -> None:
        """
        Invalidate (clear) cached synthesis for a user.

        Forces re-generation on next access.

        Args:
            user_id: User ID

        Example:
            >>> await memory.invalidate_synthesis(user_id=1)
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:hot:synthesis:{user_id}"
        await self.delete(key)
        logger.info(f"Invalidated synthesis cache for user {user_id}")

    async def invalidate_module(self, user_id: int, module_name: str) -> None:
        """
        Invalidate (clear) cached module output.

        Forces re-read from database on next access.

        Args:
            user_id: User ID
            module_name: Module to invalidate

        Example:
            >>> await memory.invalidate_module(1, "astrology")
        """
        if not self.redis_client:
            raise RuntimeError("ActiveMemory not initialized. Call initialize() first.")

        key = f"memory:warm:module:{user_id}:{module_name}"
        await self.delete(key)
        logger.debug(f"Invalidated {module_name} cache for user {user_id}")


def get_active_memory() -> ActiveMemory:
    """
    Get the singleton ActiveMemory instance.

    Returns:
        Global ActiveMemory instance

    Example:
        >>> from src.app.core.memory.active_memory import get_active_memory
        >>> memory = get_active_memory()
        >>> await memory.initialize()
        >>> await memory.set("key", "value")
    """
    global _active_memory
    if _active_memory is None:
        _active_memory = ActiveMemory()
    return _active_memory
