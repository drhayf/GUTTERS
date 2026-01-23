"""
Genesis Persistence Layer

Handles storing and retrieving uncertainty declarations.
Uses dual storage:
- UserProfile.data['genesis'] for long-term persistence
- Redis cache for fast session-based access
"""

from datetime import datetime
from typing import Any

import redis.asyncio as redis

from .uncertainty import UncertaintyDeclaration


class GenesisPersistence:
    """
    Dual persistence for Genesis uncertainty data.
    
    Storage locations:
    1. UserProfile.data['genesis']['uncertainties'] - JSONB in PostgreSQL
    2. Redis cache with session_id key - for fast conversation access
    
    Usage:
        persistence = GenesisPersistence(redis_client)
        
        # Store declaration
        await persistence.store(declaration)
        
        # Retrieve for session
        decl = await persistence.get_for_session(user_id, session_id)
        
        # Retrieve all for user
        all_decls = await persistence.get_all_for_user(user_id)
    """
    
    CACHE_PREFIX = "genesis:uncertainties"
    CACHE_TTL = 3600 * 24  # 24 hours
    
    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize persistence layer.
        
        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis = redis_client
    
    # =========================================================================
    # Redis Cache Operations
    # =========================================================================
    
    def _cache_key(self, user_id: int, session_id: str) -> str:
        """Generate Redis cache key."""
        return f"{self.CACHE_PREFIX}:{user_id}:{session_id}"
    
    def _user_cache_key(self, user_id: int) -> str:
        """Generate Redis key for all user sessions."""
        return f"{self.CACHE_PREFIX}:{user_id}:*"
    
    async def cache_declaration(
        self,
        declaration: UncertaintyDeclaration
    ) -> bool:
        """
        Cache declaration in Redis for fast access.
        
        Returns True if cached successfully.
        """
        if not self.redis:
            return False
        
        try:
            key = self._cache_key(declaration.user_id, declaration.session_id)
            await self.redis.setex(
                key,
                self.CACHE_TTL,
                declaration.model_dump_json()
            )
            return True
        except Exception:
            return False
    
    async def get_cached_declaration(
        self,
        user_id: int,
        session_id: str
    ) -> UncertaintyDeclaration | None:
        """
        Get declaration from Redis cache.
        
        Returns None if not found or cache unavailable.
        """
        if not self.redis:
            return None
        
        try:
            key = self._cache_key(user_id, session_id)
            data = await self.redis.get(key)
            if data:
                return UncertaintyDeclaration.model_validate_json(data)
        except Exception:
            pass
        
        return None
    
    async def invalidate_cache(self, user_id: int, session_id: str) -> bool:
        """Remove declaration from cache."""
        if not self.redis:
            return False
        
        try:
            key = self._cache_key(user_id, session_id)
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    # =========================================================================
    # Profile Storage Operations
    # =========================================================================
    
    async def store_to_profile(
        self,
        declaration: UncertaintyDeclaration,
        db_session: Any
    ) -> bool:
        """
        Store declaration in UserProfile.data['genesis']['uncertainties'].
        
        Args:
            declaration: Declaration to store
            db_session: SQLAlchemy async session
            
        Returns:
            True if stored successfully
        """
        try:
            from sqlalchemy import select
            from ...models.user_profile import UserProfile
            
            # Get user profile
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == declaration.user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                return False
            
            # Initialize genesis section if needed
            if not profile.data:
                profile.data = {}
            if "genesis" not in profile.data:
                profile.data["genesis"] = {}
            if "uncertainties" not in profile.data["genesis"]:
                profile.data["genesis"]["uncertainties"] = {}
            
            # Store declaration under module name
            profile.data["genesis"]["uncertainties"][declaration.module] = (
                declaration.to_storage_dict()
            )
            
            # Mark as stored
            declaration.stored_in_profile = True
            
            # Trigger JSONB update
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(profile, "data")
            
            await db_session.commit()
            return True
            
        except Exception as e:
            import logging
            logging.warning(f"Failed to store declaration to profile: {e}")
            return False
    
    async def get_from_profile(
        self,
        user_id: int,
        module_name: str,
        db_session: Any
    ) -> UncertaintyDeclaration | None:
        """
        Get declaration from UserProfile.data.
        
        Args:
            user_id: User ID
            module_name: Module to get declaration for
            db_session: SQLAlchemy async session
            
        Returns:
            Declaration if found, None otherwise
        """
        try:
            from sqlalchemy import select
            from ...models.user_profile import UserProfile
            
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile or not profile.data:
                return None
            
            genesis_data = profile.data.get("genesis", {})
            uncertainties = genesis_data.get("uncertainties", {})
            module_data = uncertainties.get(module_name)
            
            if module_data:
                return UncertaintyDeclaration.from_storage_dict(module_data)
            
        except Exception as e:
            import logging
            logging.warning(f"Failed to get declaration from profile: {e}")
        
        return None
    
    async def get_all_from_profile(
        self,
        user_id: int,
        db_session: Any
    ) -> list[UncertaintyDeclaration]:
        """
        Get all declarations for a user from profile storage.
        """
        declarations = []
        
        try:
            from sqlalchemy import select
            from ...models.user_profile import UserProfile
            
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile and profile.data:
                genesis_data = profile.data.get("genesis", {})
                uncertainties = genesis_data.get("uncertainties", {})
                
                for module_name, module_data in uncertainties.items():
                    try:
                        decl = UncertaintyDeclaration.from_storage_dict(module_data)
                        declarations.append(decl)
                    except Exception:
                        continue
                        
        except Exception as e:
            import logging
            logging.warning(f"Failed to get all declarations: {e}")
        
        return declarations
    
    # =========================================================================
    # Combined Operations
    # =========================================================================
    
    async def store(
        self,
        declaration: UncertaintyDeclaration,
        db_session: Any | None = None
    ) -> bool:
        """
        Store declaration to both cache and profile.
        
        Args:
            declaration: Declaration to store
            db_session: SQLAlchemy session (required for profile storage)
            
        Returns:
            True if at least one storage succeeded
        """
        cache_success = await self.cache_declaration(declaration)
        
        profile_success = False
        if db_session:
            profile_success = await self.store_to_profile(declaration, db_session)
        
        return cache_success or profile_success
    
    async def get(
        self,
        user_id: int,
        session_id: str,
        module_name: str | None = None,
        db_session: Any | None = None
    ) -> UncertaintyDeclaration | None:
        """
        Get declaration, checking cache first then profile.
        
        Args:
            user_id: User ID
            session_id: Session ID
            module_name: Specific module (optional, for profile lookup)
            db_session: SQLAlchemy session (for profile fallback)
        """
        # Try cache first
        cached = await self.get_cached_declaration(user_id, session_id)
        if cached:
            return cached
        
        # Fall back to profile if module specified
        if db_session and module_name:
            return await self.get_from_profile(user_id, module_name, db_session)
        
        return None


# Singleton instance
_persistence: GenesisPersistence | None = None


def get_genesis_persistence() -> GenesisPersistence:
    """Get or create the Genesis persistence singleton."""
    global _persistence
    if _persistence is None:
        _persistence = GenesisPersistence()
    return _persistence


async def initialize_genesis_persistence(redis_client: redis.Redis) -> GenesisPersistence:
    """Initialize persistence with Redis client."""
    global _persistence
    _persistence = GenesisPersistence(redis_client)
    return _persistence
