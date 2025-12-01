"""
Meal History Analysis

Provides historical queries and analysis of meal data.

@module MealHistory
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import logging

from ..schema import MealEntry, MealType, NutrientProfile, MacroNutrients

logger = logging.getLogger(__name__)


# =============================================================================
# MEAL HISTORY
# =============================================================================

class MealHistory:
    """
    Queries and analyzes meal history.
    
    Provides methods to query meals by:
    - Date/date range
    - Meal type
    - Calorie range
    - Food content
    """
    
    def __init__(self, meals: Optional[Dict[str, MealEntry]] = None):
        self._meals = meals or {}
    
    def set_meals(self, meals: Dict[str, MealEntry]) -> None:
        """Set the meals dictionary."""
        self._meals = meals
    
    def get_meals_for_date(self, target_date: date) -> List[MealEntry]:
        """Get all meals for a specific date."""
        return [
            m for m in self._meals.values()
            if m.eaten_at.date() == target_date
        ]
    
    def get_meals_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[MealEntry]:
        """Get meals within a date range (inclusive)."""
        return [
            m for m in self._meals.values()
            if start_date <= m.eaten_at.date() <= end_date
        ]
    
    def get_meals_by_type(
        self,
        meal_type: MealType,
        days: int = 30
    ) -> List[MealEntry]:
        """Get meals of a specific type from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            m for m in self._meals.values()
            if m.meal_type == meal_type and m.eaten_at >= cutoff
        ]
    
    def get_meals_with_food(
        self,
        food_name: str,
        days: int = 30
    ) -> List[MealEntry]:
        """Get meals containing a specific food."""
        cutoff = datetime.now() - timedelta(days=days)
        food_lower = food_name.lower()
        
        return [
            m for m in self._meals.values()
            if m.eaten_at >= cutoff and any(
                food_lower in f.name.lower() for f in m.foods
            )
        ]
    
    def get_daily_nutrients(
        self,
        target_date: date
    ) -> NutrientProfile:
        """Get total nutrients for a day."""
        meals = self.get_meals_for_date(target_date)
        
        total_macros = MacroNutrients()
        for meal in meals:
            meal_nutrients = meal.get_total_nutrients()
            total_macros = total_macros + meal_nutrients.macros
        
        return NutrientProfile(macros=total_macros)
    
    def get_average_daily_nutrients(
        self,
        days: int = 7
    ) -> NutrientProfile:
        """Get average daily nutrients over the last N days."""
        end = date.today()
        start = end - timedelta(days=days - 1)
        
        daily_totals = []
        current = start
        while current <= end:
            daily = self.get_daily_nutrients(current)
            if daily.macros.calories > 0:  # Only count days with data
                daily_totals.append(daily.macros)
            current += timedelta(days=1)
        
        if not daily_totals:
            return NutrientProfile()
        
        # Calculate averages
        count = len(daily_totals)
        avg_macros = MacroNutrients(
            calories=sum(m.calories for m in daily_totals) / count,
            protein=sum(m.protein for m in daily_totals) / count,
            carbohydrates=sum(m.carbohydrates for m in daily_totals) / count,
            fat=sum(m.fat for m in daily_totals) / count,
            fiber=sum(m.fiber for m in daily_totals) / count,
            sugar=sum(m.sugar for m in daily_totals) / count,
            sodium=sum(m.sodium for m in daily_totals) / count,
        )
        
        return NutrientProfile(macros=avg_macros)
    
    def get_meal_frequency(
        self,
        days: int = 30
    ) -> Dict[MealType, int]:
        """Get count of each meal type over the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        meals = [m for m in self._meals.values() if m.eaten_at >= cutoff]
        
        frequency = {mt: 0 for mt in MealType}
        for meal in meals:
            frequency[meal.meal_type] += 1
        
        return frequency
    
    def get_most_eaten_foods(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get most frequently eaten foods."""
        cutoff = datetime.now() - timedelta(days=days)
        
        food_counts: Dict[str, int] = {}
        for meal in self._meals.values():
            if meal.eaten_at >= cutoff:
                for food in meal.foods:
                    name = food.name.lower()
                    food_counts[name] = food_counts.get(name, 0) + 1
        
        sorted_foods = sorted(
            food_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_foods[:limit]
    
    def get_eating_times(
        self,
        days: int = 30
    ) -> Dict[MealType, List[int]]:
        """Get typical eating hours for each meal type."""
        cutoff = datetime.now() - timedelta(days=days)
        
        times: Dict[MealType, List[int]] = {mt: [] for mt in MealType}
        for meal in self._meals.values():
            if meal.eaten_at >= cutoff:
                times[meal.meal_type].append(meal.eaten_at.hour)
        
        return times
    
    def get_avg_eating_times(
        self,
        days: int = 30
    ) -> Dict[MealType, Optional[float]]:
        """Get average eating hour for each meal type."""
        times = self.get_eating_times(days)
        
        return {
            mt: (sum(hours) / len(hours)) if hours else None
            for mt, hours in times.items()
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_history: Optional[MealHistory] = None


def get_history() -> MealHistory:
    """Get meal history instance."""
    global _history
    if _history is None:
        _history = MealHistory()
    return _history


def get_meals_for_date(target_date: date) -> List[MealEntry]:
    """Get meals for a specific date."""
    return get_history().get_meals_for_date(target_date)


def get_meals_in_range(start_date: date, end_date: date) -> List[MealEntry]:
    """Get meals in a date range."""
    return get_history().get_meals_in_range(start_date, end_date)
