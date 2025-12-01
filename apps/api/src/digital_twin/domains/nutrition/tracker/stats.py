"""
Nutrition Statistics

Calculates and aggregates nutrition statistics.

@module NutritionStats
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import logging

from ..schema import MealEntry, MealType, NutrientProfile, MacroNutrients
from .history import MealHistory, get_history

logger = logging.getLogger(__name__)


# =============================================================================
# STAT TYPES
# =============================================================================

@dataclass
class DailyStats:
    """Statistics for a single day."""
    date: date
    
    # Meal counts
    total_meals: int = 0
    meal_breakdown: Dict[str, int] = field(default_factory=dict)
    
    # Nutrients
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fat: float = 0.0
    total_fiber: float = 0.0
    
    # Targets (if set)
    calorie_target: Optional[float] = None
    calorie_variance: Optional[float] = None
    
    # Foods
    total_foods: int = 0
    unique_foods: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "total_meals": self.total_meals,
            "meal_breakdown": self.meal_breakdown,
            "total_calories": self.total_calories,
            "total_protein": self.total_protein,
            "total_carbs": self.total_carbs,
            "total_fat": self.total_fat,
            "total_fiber": self.total_fiber,
            "calorie_target": self.calorie_target,
            "calorie_variance": self.calorie_variance,
            "total_foods": self.total_foods,
            "unique_foods": self.unique_foods,
        }


@dataclass
class WeeklyStats:
    """Statistics for a week."""
    start_date: date
    end_date: date
    
    # Daily stats
    daily_stats: List[DailyStats] = field(default_factory=list)
    
    # Averages
    avg_daily_calories: float = 0.0
    avg_daily_protein: float = 0.0
    avg_daily_carbs: float = 0.0
    avg_daily_fat: float = 0.0
    avg_daily_fiber: float = 0.0
    
    # Totals
    total_meals: int = 0
    total_foods: int = 0
    
    # Patterns
    days_tracked: int = 0
    most_common_foods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "daily_stats": [d.to_dict() for d in self.daily_stats],
            "avg_daily_calories": self.avg_daily_calories,
            "avg_daily_protein": self.avg_daily_protein,
            "avg_daily_carbs": self.avg_daily_carbs,
            "avg_daily_fat": self.avg_daily_fat,
            "avg_daily_fiber": self.avg_daily_fiber,
            "total_meals": self.total_meals,
            "total_foods": self.total_foods,
            "days_tracked": self.days_tracked,
            "most_common_foods": self.most_common_foods,
        }


# =============================================================================
# NUTRITION STATS
# =============================================================================

class NutritionStats:
    """
    Calculates nutrition statistics.
    
    Uses MealHistory for data access.
    """
    
    def __init__(self, history: Optional[MealHistory] = None):
        self._history = history or get_history()
    
    def get_daily_stats(
        self,
        target_date: date,
        calorie_target: Optional[float] = None
    ) -> DailyStats:
        """Calculate stats for a single day."""
        meals = self._history.get_meals_for_date(target_date)
        
        # Meal counts
        meal_breakdown = {}
        for meal in meals:
            mt = meal.meal_type.value
            meal_breakdown[mt] = meal_breakdown.get(mt, 0) + 1
        
        # Nutrients
        total_macros = MacroNutrients()
        food_names = set()
        total_foods = 0
        
        for meal in meals:
            meal_nutrients = meal.get_total_nutrients()
            total_macros = total_macros + meal_nutrients.macros
            
            for food in meal.foods:
                food_names.add(food.name.lower())
                total_foods += 1
        
        # Calorie variance
        variance = None
        if calorie_target:
            variance = ((total_macros.calories - calorie_target) / calorie_target) * 100
        
        return DailyStats(
            date=target_date,
            total_meals=len(meals),
            meal_breakdown=meal_breakdown,
            total_calories=total_macros.calories,
            total_protein=total_macros.protein,
            total_carbs=total_macros.carbohydrates,
            total_fat=total_macros.fat,
            total_fiber=total_macros.fiber,
            calorie_target=calorie_target,
            calorie_variance=variance,
            total_foods=total_foods,
            unique_foods=len(food_names),
        )
    
    def get_weekly_stats(
        self,
        end_date: Optional[date] = None
    ) -> WeeklyStats:
        """Calculate stats for the past week."""
        end = end_date or date.today()
        start = end - timedelta(days=6)
        
        # Get daily stats
        daily = []
        current = start
        while current <= end:
            day_stats = self.get_daily_stats(current)
            daily.append(day_stats)
            current += timedelta(days=1)
        
        # Calculate averages (only from days with data)
        days_with_data = [d for d in daily if d.total_meals > 0]
        days_tracked = len(days_with_data)
        
        if days_tracked > 0:
            avg_calories = sum(d.total_calories for d in days_with_data) / days_tracked
            avg_protein = sum(d.total_protein for d in days_with_data) / days_tracked
            avg_carbs = sum(d.total_carbs for d in days_with_data) / days_tracked
            avg_fat = sum(d.total_fat for d in days_with_data) / days_tracked
            avg_fiber = sum(d.total_fiber for d in days_with_data) / days_tracked
        else:
            avg_calories = avg_protein = avg_carbs = avg_fat = avg_fiber = 0.0
        
        # Totals
        total_meals = sum(d.total_meals for d in daily)
        total_foods = sum(d.total_foods for d in daily)
        
        # Most common foods
        common_foods = self._history.get_most_eaten_foods(days=7, limit=5)
        most_common = [name for name, _ in common_foods]
        
        return WeeklyStats(
            start_date=start,
            end_date=end,
            daily_stats=daily,
            avg_daily_calories=avg_calories,
            avg_daily_protein=avg_protein,
            avg_daily_carbs=avg_carbs,
            avg_daily_fat=avg_fat,
            avg_daily_fiber=avg_fiber,
            total_meals=total_meals,
            total_foods=total_foods,
            days_tracked=days_tracked,
            most_common_foods=most_common,
        )
    
    def get_streak(self) -> int:
        """Get current tracking streak (consecutive days with logged meals)."""
        current = date.today()
        streak = 0
        
        while True:
            meals = self._history.get_meals_for_date(current)
            if meals:
                streak += 1
                current -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_macro_trends(
        self,
        days: int = 30
    ) -> Dict[str, List[float]]:
        """Get daily macro values for trend visualization."""
        end = date.today()
        start = end - timedelta(days=days - 1)
        
        calories = []
        protein = []
        carbs = []
        fat = []
        
        current = start
        while current <= end:
            nutrients = self._history.get_daily_nutrients(current)
            calories.append(nutrients.macros.calories)
            protein.append(nutrients.macros.protein)
            carbs.append(nutrients.macros.carbohydrates)
            fat.append(nutrients.macros.fat)
            current += timedelta(days=1)
        
        return {
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_stats: Optional[NutritionStats] = None


def get_stats() -> NutritionStats:
    """Get nutrition stats instance."""
    global _stats
    if _stats is None:
        _stats = NutritionStats()
    return _stats


def get_daily_stats(
    target_date: date,
    calorie_target: Optional[float] = None
) -> DailyStats:
    """Get daily stats."""
    return get_stats().get_daily_stats(target_date, calorie_target)


def get_weekly_stats(end_date: Optional[date] = None) -> WeeklyStats:
    """Get weekly stats."""
    return get_stats().get_weekly_stats(end_date)
