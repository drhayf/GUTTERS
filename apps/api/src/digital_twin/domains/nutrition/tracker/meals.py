"""
Meal CRUD Operations

Handles creating, reading, updating, and deleting meals.
Integrates with Digital Twin for persistence.

@module MealTracker
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import logging

from ..schema import MealEntry, FoodEntry, MealType

logger = logging.getLogger(__name__)


# =============================================================================
# MEAL TRACKER
# =============================================================================

class MealTracker:
    """
    Manages meal entries for a user.
    
    Provides CRUD operations and integrates with Digital Twin
    for persistent storage.
    
    Example:
        tracker = MealTracker(identity_id="user_123")
        meal = await tracker.add_meal(foods=[...], meal_type=MealType.LUNCH)
        meals = await tracker.get_today_meals()
    """
    
    def __init__(self, identity_id: Optional[str] = None):
        self._identity_id = identity_id
        self._meals: Dict[str, MealEntry] = {}  # In-memory cache
        self._twin = None  # Will be set when Digital Twin is available
    
    async def _get_twin(self):
        """Get Digital Twin instance lazily."""
        if self._twin is None:
            try:
                from .... import get_digital_twin_core
                self._twin = await get_digital_twin_core()
            except Exception as e:
                logger.warning(f"[MealTracker] Digital Twin not available: {e}")
        return self._twin
    
    async def add_meal(
        self,
        foods: List[FoodEntry],
        meal_type: MealType = MealType.OTHER,
        eaten_at: Optional[datetime] = None,
        name: Optional[str] = None,
        notes: str = "",
        **kwargs
    ) -> MealEntry:
        """
        Add a new meal.
        
        Args:
            foods: List of foods in the meal
            meal_type: Type of meal (breakfast, lunch, etc.)
            eaten_at: When the meal was eaten (defaults to now)
            name: Optional custom name
            notes: Optional notes
            **kwargs: Additional meal fields
        
        Returns:
            Created MealEntry
        """
        meal = MealEntry(
            meal_id=str(uuid4()),
            foods=foods,
            meal_type=meal_type,
            eaten_at=eaten_at or datetime.now(),
            name=name,
            notes=notes,
            **kwargs
        )
        
        # Store in cache
        self._meals[meal.meal_id] = meal
        
        # Persist to Digital Twin
        await self._persist_meal(meal)
        
        logger.info(f"[MealTracker] Added meal: {meal.meal_id} ({meal_type.value})")
        
        return meal
    
    async def get_meal(self, meal_id: str) -> Optional[MealEntry]:
        """Get a meal by ID."""
        # Check cache first
        if meal_id in self._meals:
            return self._meals[meal_id]
        
        # Try Digital Twin
        meal = await self._load_meal(meal_id)
        if meal:
            self._meals[meal_id] = meal
        
        return meal
    
    async def update_meal(
        self,
        meal_id: str,
        **updates
    ) -> Optional[MealEntry]:
        """
        Update a meal.
        
        Args:
            meal_id: ID of meal to update
            **updates: Fields to update
        
        Returns:
            Updated MealEntry or None if not found
        """
        meal = await self.get_meal(meal_id)
        if not meal:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(meal, key):
                setattr(meal, key, value)
        
        # Persist
        await self._persist_meal(meal)
        
        return meal
    
    async def delete_meal(self, meal_id: str) -> bool:
        """
        Delete a meal.
        
        Returns True if deleted.
        """
        if meal_id in self._meals:
            del self._meals[meal_id]
        
        # Delete from Digital Twin
        await self._delete_meal_from_twin(meal_id)
        
        logger.info(f"[MealTracker] Deleted meal: {meal_id}")
        return True
    
    async def add_food_to_meal(
        self,
        meal_id: str,
        food: FoodEntry
    ) -> Optional[MealEntry]:
        """Add a food to an existing meal."""
        meal = await self.get_meal(meal_id)
        if not meal:
            return None
        
        meal.foods.append(food)
        await self._persist_meal(meal)
        
        return meal
    
    async def remove_food_from_meal(
        self,
        meal_id: str,
        food_id: str
    ) -> Optional[MealEntry]:
        """Remove a food from a meal."""
        meal = await self.get_meal(meal_id)
        if not meal:
            return None
        
        meal.foods = [f for f in meal.foods if f.food_id != food_id]
        await self._persist_meal(meal)
        
        return meal
    
    async def get_today_meals(self) -> List[MealEntry]:
        """Get all meals from today."""
        today = datetime.now().date()
        return [
            m for m in self._meals.values()
            if m.eaten_at.date() == today
        ]
    
    async def get_recent_meals(self, limit: int = 10) -> List[MealEntry]:
        """Get most recent meals."""
        sorted_meals = sorted(
            self._meals.values(),
            key=lambda m: m.eaten_at,
            reverse=True
        )
        return sorted_meals[:limit]
    
    # -------------------------------------------------------------------------
    # Digital Twin Integration
    # -------------------------------------------------------------------------
    
    async def _persist_meal(self, meal: MealEntry) -> None:
        """Persist meal to Digital Twin."""
        twin = await self._get_twin()
        if twin:
            try:
                await twin.set(
                    path=f"nutrition.meals.{meal.meal_id}",
                    value=meal.to_dict(),
                    source="meal_tracker",
                    confidence=1.0,
                )
            except Exception as e:
                logger.error(f"[MealTracker] Failed to persist meal: {e}")
    
    async def _load_meal(self, meal_id: str) -> Optional[MealEntry]:
        """Load meal from Digital Twin."""
        twin = await self._get_twin()
        if twin:
            try:
                data = await twin.get(f"nutrition.meals.{meal_id}")
                if data:
                    return MealEntry.from_dict(data)
            except Exception as e:
                logger.error(f"[MealTracker] Failed to load meal: {e}")
        return None
    
    async def _delete_meal_from_twin(self, meal_id: str) -> None:
        """Delete meal from Digital Twin."""
        twin = await self._get_twin()
        if twin:
            try:
                await twin.delete(f"nutrition.meals.{meal_id}")
            except Exception as e:
                logger.error(f"[MealTracker] Failed to delete meal: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Module-level tracker instance
_tracker: Optional[MealTracker] = None


async def get_tracker(identity_id: Optional[str] = None) -> MealTracker:
    """Get or create meal tracker instance."""
    global _tracker
    if _tracker is None or (identity_id and _tracker._identity_id != identity_id):
        _tracker = MealTracker(identity_id)
    return _tracker


async def add_meal(
    foods: List[FoodEntry],
    meal_type: MealType = MealType.OTHER,
    **kwargs
) -> MealEntry:
    """Convenience function to add a meal."""
    tracker = await get_tracker()
    return await tracker.add_meal(foods, meal_type, **kwargs)


async def get_meal(meal_id: str) -> Optional[MealEntry]:
    """Convenience function to get a meal."""
    tracker = await get_tracker()
    return await tracker.get_meal(meal_id)


async def update_meal(meal_id: str, **updates) -> Optional[MealEntry]:
    """Convenience function to update a meal."""
    tracker = await get_tracker()
    return await tracker.update_meal(meal_id, **updates)


async def delete_meal(meal_id: str) -> bool:
    """Convenience function to delete a meal."""
    tracker = await get_tracker()
    return await tracker.delete_meal(meal_id)
