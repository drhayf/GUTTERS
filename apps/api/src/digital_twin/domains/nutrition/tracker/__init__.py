"""
Nutrition Tracker - Meal Tracking Sub-Module

Handles meal logging, history, and statistics:
- Meal CRUD operations
- Historical analysis
- Statistics and trends

Architecture (Fractal):
━━━━━━━━━━━━━━━━━━━━━━━━━
tracker/
├── __init__.py      # Exports
├── meals.py         # Meal CRUD
├── history.py       # Historical queries
└── stats.py         # Statistics

@module NutritionTracker
"""

from .meals import (
    MealTracker,
    add_meal,
    get_meal,
    update_meal,
    delete_meal,
)
from .history import (
    MealHistory,
    get_meals_for_date,
    get_meals_in_range,
)
from .stats import (
    NutritionStats,
    get_daily_stats,
    get_weekly_stats,
)

__all__ = [
    "MealTracker",
    "add_meal",
    "get_meal",
    "update_meal",
    "delete_meal",
    "MealHistory",
    "get_meals_for_date",
    "get_meals_in_range",
    "NutritionStats",
    "get_daily_stats",
    "get_weekly_stats",
]
