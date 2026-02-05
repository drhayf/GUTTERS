"""
GUTTERS Chronos State Manager

Manages Redis caching and database persistence for the Chronos-Magi
time-mapping system. Provides fast access to current planetary period
state and handles background synchronization.

Architecture:
    - Redis (HOT): Current period state with 25-hour TTL
    - PostgreSQL (COLD): UserProfile.data["cardology"] for persistence

Example:
    >>> from src.app.core.state.chronos import get_chronos_manager
    >>> manager = get_chronos_manager()
    >>> state = await manager.get_user_chronos(user_id=123, birth_date="1963-12-18")
    >>> print(f"Current period: {state['current_planet']}")
"""

from __future__ import annotations
import json
import logging
from datetime import date, datetime, UTC
from typing import Any

from ...core.memory.active_memory import get_active_memory
from ...core.events.bus import EventBus, get_event_bus
from ...protocol.events import (
    MAGI_PERIOD_SHIFT,
    MAGI_YEAR_SHIFT,
    MAGI_STATE_CACHED,
    MAGI_PROFILE_CALCULATED,
    MAGI_HEXAGRAM_CHANGE,
    MAGI_COUNCIL_SYNTHESIS,
)

logger = logging.getLogger(__name__)

# Singleton instance
_chronos_manager: ChronosStateManager | None = None

# Cache key patterns
CHRONOS_KEY_PREFIX = "chronos:"
HEXAGRAM_KEY_PREFIX = "hexagram:"
CHRONOS_TTL = 90000  # 25 hours - ensures period boundary detection
HEXAGRAM_TTL = 21600  # 6 hours - matches gate transit frequency


class ChronosStateManager:
    """
    Manages Chronos (Cardology) state across Redis and PostgreSQL.
    
    Responsibilities:
        - Calculate and cache current planetary period to Redis
        - Persist full cardology profile to UserProfile.data
        - Detect period shifts and emit events
        - Provide fast state retrieval for query engine injection
    
    Example:
        >>> manager = get_chronos_manager()
        >>> 
        >>> # Get current state (from cache or calculate fresh)
        >>> state = await manager.get_user_chronos(user_id=1, birth_date="1963-12-18")
        >>> 
        >>> # Force refresh (recalculate and update cache)
        >>> new_state = await manager.refresh_user_chronos(user_id=1, birth_date="1963-12-18")
    """
    
    def __init__(self):
        """Initialize manager (call initialize() to connect services)."""
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Connect to required services.
        
        Should be called during application startup after Redis is ready.
        """
        self._initialized = True
        logger.info("[ChronosManager] Initialized")
    
    async def cleanup(self) -> None:
        """
        Cleanup resources.
        
        Should be called during application shutdown.
        """
        self._initialized = False
        logger.info("[ChronosManager] Cleaned up")
    
    # =========================================================================
    # Core State Operations
    # =========================================================================
    
    async def get_user_chronos(
        self, 
        user_id: int, 
        birth_date: str | date | None = None
    ) -> dict[str, Any] | None:
        """
        Get user's current Chronos state from cache or database.
        
        Checks Redis first, falls back to UserProfile.data["cardology"],
        or calculates fresh if birth_date is provided.
        
        Args:
            user_id: User ID
            birth_date: Birth date (required for fresh calculation)
        
        Returns:
            Chronos state dict or None if not available:
            {
                "birth_card": {"rank": 13, "suit": "HEARTS", "name": "King of Hearts"},
                "current_planet": "MERCURY",
                "current_card": {"rank": 13, "suit": "CLUBS", "name": "King of Clubs"},
                "period_number": 1,
                "days_remaining": 42,
                "cached_at": "2024-01-15T12:00:00Z"
            }
        """
        memory = get_active_memory()
        
        # 1. Check Redis cache first
        if memory.redis_client:
            cached = await memory.redis_client.get(f"{CHRONOS_KEY_PREFIX}{user_id}")
            if cached:
                return json.loads(cached)
        
        # 2. Fall back to database
        from ...core.db.database import async_get_db
        from ...crud.crud_user_profile import crud_user_profiles
        
        async for db in async_get_db():
            profile = await crud_user_profiles.get(db=db, user_id=user_id)
            if profile and hasattr(profile, 'data') and profile.data:
                cardology_data = profile.data.get("cardology")
                if cardology_data and cardology_data.get("current_state"):
                    # Re-cache to Redis for future fast access
                    current_state = cardology_data["current_state"]
                    if memory.redis_client:
                        await memory.redis_client.setex(
                            f"{CHRONOS_KEY_PREFIX}{user_id}",
                            CHRONOS_TTL,
                            json.dumps(current_state)
                        )
                    return current_state
        
        # 3. Calculate fresh if birth_date provided
        if birth_date:
            return await self.refresh_user_chronos(user_id, birth_date)
        
        return None
    
    async def refresh_user_chronos(
        self, 
        user_id: int, 
        birth_date: str | date,
        target_year: int | None = None
    ) -> dict[str, Any]:
        """
        Recalculate Chronos state, update cache, and persist to database.
        
        This is the primary entry point for updating user state. It:
        1. Calculates current period from CardologyModule
        2. Compares against cached state for shift detection
        3. Emits events if period or year changed
        4. Updates Redis cache with new state
        5. Persists full profile to UserProfile.data["cardology"]
        
        Args:
            user_id: User ID
            birth_date: Birth date string "YYYY-MM-DD" or date object
            target_year: Year for calculations (default: current year)
        
        Returns:
            Updated Chronos state dict
        
        Example:
            >>> state = await manager.refresh_user_chronos(
            ...     user_id=1,
            ...     birth_date="1963-12-18"
            ... )
            >>> print(f"Period {state['period_number']}: {state['current_planet']}")
        """
        from ...modules.intelligence.cardology import CardologyModule
        
        # Parse birth date
        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)
        
        year = target_year or datetime.now(UTC).year
        
        # Get previous state for comparison
        old_state = await self._get_cached_state(user_id)
        
        # Calculate current state via CardologyModule
        module = CardologyModule()
        period_info = module.get_current_period(birth_date)
        profile_data = module.calculate_profile(birth_date, year)
        
        # Build current state - mapping kernel field names to our schema
        # Kernel uses: "period" (planet name), "card", "card_name", "start", "end"
        new_state = {
            "birth_card": profile_data.get("birth_card"),
            "current_planet": period_info.get("period"),  # Kernel calls it "period"
            "current_card": {
                "card": period_info.get("card"),
                "name": period_info.get("card_name"),
            },
            "period_start": period_info.get("start"),
            "period_end": period_info.get("end"),
            "days_remaining": period_info.get("days_remaining"),
            "theme": period_info.get("theme"),
            "guidance": period_info.get("guidance"),
            "planetary_ruling_card": profile_data.get("planetary_ruling_card"),
            "year": year,
            "age": profile_data.get("age"),
            "cached_at": datetime.now(UTC).isoformat(),
        }
        
        # Detect shifts and emit events
        await self._detect_and_emit_shifts(user_id, old_state, new_state)
        
        # Update Redis cache
        await self._cache_state(user_id, new_state)
        
        # Persist to database
        await self._persist_to_profile(user_id, profile_data, new_state)
        
        logger.info(
            f"[ChronosManager] Refreshed user {user_id}: "
            f"{new_state['current_planet']} period, {new_state['current_card']['name']}"
        )
        
        return new_state
    
    # =========================================================================
    # Cache Operations
    # =========================================================================
    
    async def _get_cached_state(self, user_id: int) -> dict[str, Any] | None:
        """Get state from Redis cache."""
        memory = get_active_memory()
        if memory.redis_client:
            cached = await memory.redis_client.get(f"{CHRONOS_KEY_PREFIX}{user_id}")
            if cached:
                return json.loads(cached)
        return None
    
    async def _cache_state(self, user_id: int, state: dict[str, Any]) -> None:
        """Cache state to Redis with TTL."""
        memory = get_active_memory()
        if memory.redis_client:
            await memory.redis_client.setex(
                f"{CHRONOS_KEY_PREFIX}{user_id}",
                CHRONOS_TTL,
                json.dumps(state)
            )
            
            # Emit cache event
            bus = get_event_bus()
            if bus.redis_client:
                await bus.publish(MAGI_STATE_CACHED, {
                    "user_id": user_id,
                    "current_planet": state.get("current_planet"),
                    "current_card": state.get("current_card", {}).get("name"),
                    "ttl": CHRONOS_TTL,
                })
    
    async def invalidate_cache(self, user_id: int) -> None:
        """Remove user's Chronos state from cache."""
        memory = get_active_memory()
        if memory.redis_client:
            await memory.redis_client.delete(f"{CHRONOS_KEY_PREFIX}{user_id}")
            logger.info(f"[ChronosManager] Invalidated cache for user {user_id}")
    
    # =========================================================================
    # Shift Detection & Events
    # =========================================================================
    
    async def _detect_and_emit_shifts(
        self, 
        user_id: int, 
        old_state: dict[str, Any] | None, 
        new_state: dict[str, Any]
    ) -> None:
        """Compare states and emit events for period/year shifts."""
        bus = get_event_bus()
        if not bus.redis_client:
            return
        
        if not old_state:
            # First calculation - emit profile calculated event
            birth_card = new_state.get("birth_card", {})
            birth_card_name = f"{birth_card.get('rank_name', '')} of {birth_card.get('suit', '')}"
            await bus.publish(MAGI_PROFILE_CALCULATED, {
                "user_id": user_id,
                "birth_card": birth_card_name,
                "planetary_card": new_state.get("current_card", {}).get("name"),
                "year": new_state.get("year"),
            })
            return
        
        # Check for period shift (planet changed = new 52-day period)
        old_planet = old_state.get("current_planet")
        new_planet = new_state.get("current_planet")
        
        if old_planet and new_planet and old_planet != new_planet:
            await bus.publish(MAGI_PERIOD_SHIFT, {
                "user_id": user_id,
                "old_planet": old_planet,
                "new_planet": new_planet,
                "old_card": old_state.get("current_card", {}).get("name"),
                "new_card": new_state.get("current_card", {}).get("name"),
            })
            logger.info(
                f"[ChronosManager] Period shift for user {user_id}: "
                f"{old_planet} → {new_planet}"
            )
        
        # Check for year shift (birthday boundary)
        old_age = old_state.get("age")
        new_age = new_state.get("age")
        
        if old_age is not None and new_age is not None and old_age != new_age:
            await bus.publish(MAGI_YEAR_SHIFT, {
                "user_id": user_id,
                "old_age": old_age,
                "new_age": new_age,
                "old_planetary_card": old_state.get("planetary_ruling_card", {}).get("name"),
                "new_planetary_card": new_state.get("planetary_ruling_card", {}).get("name"),
            })
            logger.info(
                f"[ChronosManager] Year shift for user {user_id}: "
                f"age {old_age} → {new_age}"
            )
    
    # =========================================================================
    # Database Persistence
    # =========================================================================
    
    async def _persist_to_profile(
        self, 
        user_id: int, 
        profile_data: dict[str, Any],
        current_state: dict[str, Any]
    ) -> None:
        """
        Persist cardology data to UserProfile.data["cardology"].
        
        Merges with existing profile data, preserving other modules.
        """
        from ...core.db.database import async_get_db
        from ...crud.crud_user_profile import crud_user_profiles
        from datetime import datetime, UTC
        
        cardology_payload = {
            "birth_card": profile_data.get("birth_card"),
            "planetary_ruling_card": profile_data.get("planetary_ruling_card"),
            "yearly_timeline": profile_data.get("yearly_timeline"),
            "year": profile_data.get("year"),
            "age": profile_data.get("age"),
            "current_state": current_state,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        
        async for db in async_get_db():
            # Get existing profile
            profile = await crud_user_profiles.get(db=db, user_id=user_id)
            
            if profile:
                # Merge with existing data
                existing_data = profile.data or {}
                existing_data["cardology"] = cardology_payload
                
                await crud_user_profiles.update(
                    db=db,
                    object={"data": existing_data, "updated_at": datetime.now(UTC)},
                    user_id=user_id,
                )
            else:
                # Create new profile
                await crud_user_profiles.create(
                    db=db,
                    object={"user_id": user_id, "data": {"cardology": cardology_payload}},
                )
            
            logger.debug(f"[ChronosManager] Persisted cardology for user {user_id}")

    # =========================================================================
    # I-Ching / Hexagram Operations
    # =========================================================================
    
    async def get_current_hexagram(self, user_id: int | None = None) -> dict[str, Any] | None:
        """
        Get current Sun/Earth hexagram (I-Ching daily code).
        
        This is global transit data (not user-specific), but can be
        cached per-user if needed for personalized overlays.
        
        Returns:
            Dict with sun_gate, earth_gate, lines, gate info, etc.
        """
        memory = get_active_memory()
        cache_key = f"{HEXAGRAM_KEY_PREFIX}current"
        
        # Check cache first
        if memory.redis_client:
            cached = await memory.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Calculate fresh from I-Ching kernel
        try:
            from ...modules.intelligence.iching import IChingKernel, GATE_DATABASE
            
            kernel = IChingKernel()
            daily_code = kernel.get_daily_code()
            
            sun_gate = daily_code.sun_activation.gate
            earth_gate = daily_code.earth_activation.gate
            
            # Get gate info for rich context
            sun_info = GATE_DATABASE.get(sun_gate, {})
            earth_info = GATE_DATABASE.get(earth_gate, {})
            
            hexagram_state = {
                "sun_gate": sun_gate,
                "sun_line": daily_code.sun_activation.line,
                "sun_color": daily_code.sun_activation.color,
                "sun_tone": daily_code.sun_activation.tone,
                "sun_gate_name": sun_info.get("hd_name", ""),
                "sun_gene_key_gift": sun_info.get("gk_gift", ""),
                "earth_gate": earth_gate,
                "earth_line": daily_code.earth_activation.line,
                "earth_color": daily_code.earth_activation.color,
                "earth_tone": daily_code.earth_activation.tone,
                "earth_gate_name": earth_info.get("hd_name", ""),
                "earth_gene_key_gift": earth_info.get("gk_gift", ""),
                "polarity_theme": f"{sun_info.get('hd_keynote', '')} ↔ {earth_info.get('hd_keynote', '')}",
                "calculated_at": datetime.now(UTC).isoformat(),
            }
            
            # Cache result
            if memory.redis_client:
                await memory.redis_client.setex(
                    cache_key,
                    HEXAGRAM_TTL,
                    json.dumps(hexagram_state)
                )
            
            return hexagram_state
            
        except Exception as e:
            logger.error(f"[ChronosManager] Failed to calculate hexagram: {e}")
            return None
    
    async def refresh_hexagram(self, user_id: int | None = None) -> dict[str, Any] | None:
        """
        Force refresh hexagram calculation and detect gate changes.
        
        Compares new gates against cached state and emits
        MAGI_HEXAGRAM_CHANGE event if gates shifted.
        """
        memory = get_active_memory()
        cache_key = f"{HEXAGRAM_KEY_PREFIX}current"
        
        # Get old state for comparison
        old_state = None
        if memory.redis_client:
            cached = await memory.redis_client.get(cache_key)
            if cached:
                old_state = json.loads(cached)
        
        # Invalidate cache to force fresh calculation
        if memory.redis_client:
            await memory.redis_client.delete(cache_key)
        
        # Calculate fresh
        new_state = await self.get_current_hexagram(user_id)
        
        if not new_state:
            return None
        
        # Detect gate shift
        if old_state:
            old_sun = old_state.get("sun_gate")
            new_sun = new_state.get("sun_gate")
            old_earth = old_state.get("earth_gate")
            new_earth = new_state.get("earth_gate")
            
            if old_sun != new_sun or old_earth != new_earth:
                bus = get_event_bus()
                if bus.redis_client:
                    await bus.publish(MAGI_HEXAGRAM_CHANGE, {
                        "user_id": user_id or 0,
                        "old_sun_gate": old_sun,
                        "new_sun_gate": new_sun,
                        "old_earth_gate": old_earth,
                        "new_earth_gate": new_earth,
                        "sun_line": new_state.get("sun_line"),
                        "earth_line": new_state.get("earth_line"),
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    logger.info(
                        f"[ChronosManager] Hexagram shift: "
                        f"Sun {old_sun}→{new_sun}, Earth {old_earth}→{new_earth}"
                    )
        
        return new_state
    
    async def get_council_synthesis(self, user_id: int | None = None) -> dict[str, Any] | None:
        """
        Get unified synthesis from Council of Systems.
        
        Combines I-Ching micro-coordinates with Cardology macro-coordinates
        to generate cross-system resonance and guidance.
        """
        try:
            from ...modules.intelligence.synthesis.harmonic import (
                CouncilOfSystems,
                IChingAdapter,
                CardologyAdapter,
            )
            from ...modules.intelligence.iching import IChingKernel
            
            # Initialize Council
            council = CouncilOfSystems()
            kernel = IChingKernel()
            
            # Register systems
            council.register_system("I-Ching", IChingAdapter(kernel))
            council.register_system("Cardology", CardologyAdapter())
            
            # Generate synthesis
            synthesis = council.synthesize()
            
            synthesis_dict = {
                "resonance_score": synthesis.resonance_score,
                "resonance_type": synthesis.resonance_type.value if hasattr(synthesis.resonance_type, 'value') else str(synthesis.resonance_type),
                "macro_theme": synthesis.macro_theme,
                "micro_theme": synthesis.micro_theme,
                "synthesis_guidance": synthesis.synthesis_guidance,
                "quest_suggestions": synthesis.quest_suggestions,
                "elemental_profile": synthesis.elemental_profile,
                "calculated_at": datetime.now(UTC).isoformat(),
            }
            
            # Emit synthesis event
            bus = get_event_bus()
            if bus.redis_client:
                await bus.publish(MAGI_COUNCIL_SYNTHESIS, {
                    "user_id": user_id or 0,
                    "resonance_score": synthesis_dict["resonance_score"],
                    "resonance_type": synthesis_dict["resonance_type"],
                    "macro_theme": synthesis_dict["macro_theme"],
                    "micro_theme": synthesis_dict["micro_theme"],
                    "quest_suggestions": synthesis_dict["quest_suggestions"],
                })
            
            return synthesis_dict
            
        except Exception as e:
            logger.error(f"[ChronosManager] Failed to generate council synthesis: {e}")
            return None


# =============================================================================
# Singleton Access
# =============================================================================

def get_chronos_manager() -> ChronosStateManager:
    """
    Get the singleton ChronosStateManager instance.
    
    Example:
        >>> from src.app.core.state.chronos import get_chronos_manager
        >>> manager = get_chronos_manager()
        >>> state = await manager.get_user_chronos(user_id=123, birth_date="1990-01-01")
    """
    global _chronos_manager
    if _chronos_manager is None:
        _chronos_manager = ChronosStateManager()
    return _chronos_manager
