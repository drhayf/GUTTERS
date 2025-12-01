"""
Trend Analysis

Analyzes nutrition trends over time.

@module TrendAnalyzer
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging

from ..tracker.history import MealHistory, get_history

logger = logging.getLogger(__name__)


# =============================================================================
# TREND TYPES
# =============================================================================

class TrendDirection(str, Enum):
    """Direction of a trend."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VARIABLE = "variable"


class TrendType(str, Enum):
    """Types of nutrition trends."""
    CALORIE = "calorie"
    PROTEIN = "protein"
    CARBS = "carbs"
    FAT = "fat"
    FIBER = "fiber"
    MEAL_COUNT = "meal_count"
    VARIETY = "variety"


@dataclass
class NutritionTrend:
    """A detected nutrition trend."""
    trend_type: TrendType
    direction: TrendDirection
    magnitude: float                     # Percent change
    description: str
    
    # Data points
    values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    
    # Stats
    current_avg: float = 0.0
    previous_avg: float = 0.0
    percent_change: float = 0.0
    
    # Time period
    days_analyzed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_type": self.trend_type.value,
            "direction": self.direction.value,
            "magnitude": self.magnitude,
            "description": self.description,
            "values": self.values,
            "dates": self.dates,
            "current_avg": self.current_avg,
            "previous_avg": self.previous_avg,
            "percent_change": self.percent_change,
            "days_analyzed": self.days_analyzed,
        }


# =============================================================================
# TREND ANALYZER
# =============================================================================

class TrendAnalyzer:
    """
    Analyzes nutrition trends over time.
    
    Compares recent data (e.g., last 7 days) to previous period
    to identify changes in eating patterns.
    """
    
    def __init__(self, history: Optional[MealHistory] = None):
        self._history = history or get_history()
    
    async def analyze_all_trends(
        self,
        recent_days: int = 7,
        compare_days: int = 7
    ) -> List[NutritionTrend]:
        """
        Analyze all nutrition trends.
        
        Compares last `recent_days` to the previous `compare_days`.
        """
        trends = []
        
        # Calorie trend
        calorie_trend = await self.analyze_calorie_trend(recent_days, compare_days)
        if calorie_trend:
            trends.append(calorie_trend)
        
        # Protein trend
        protein_trend = await self.analyze_macro_trend(
            "protein", recent_days, compare_days
        )
        if protein_trend:
            trends.append(protein_trend)
        
        # Fiber trend
        fiber_trend = await self.analyze_macro_trend(
            "fiber", recent_days, compare_days
        )
        if fiber_trend:
            trends.append(fiber_trend)
        
        return trends
    
    async def analyze_calorie_trend(
        self,
        recent_days: int = 7,
        compare_days: int = 7
    ) -> Optional[NutritionTrend]:
        """Analyze calorie intake trend."""
        end = date.today()
        recent_start = end - timedelta(days=recent_days - 1)
        compare_start = recent_start - timedelta(days=compare_days)
        compare_end = recent_start - timedelta(days=1)
        
        # Get daily values
        recent_values = []
        recent_dates = []
        current = recent_start
        while current <= end:
            nutrients = self._history.get_daily_nutrients(current)
            if nutrients.macros.calories > 0:
                recent_values.append(nutrients.macros.calories)
                recent_dates.append(current.isoformat())
            current += timedelta(days=1)
        
        compare_values = []
        current = compare_start
        while current <= compare_end:
            nutrients = self._history.get_daily_nutrients(current)
            if nutrients.macros.calories > 0:
                compare_values.append(nutrients.macros.calories)
            current += timedelta(days=1)
        
        if not recent_values or not compare_values:
            return None
        
        # Calculate averages
        recent_avg = sum(recent_values) / len(recent_values)
        compare_avg = sum(compare_values) / len(compare_values)
        
        # Calculate percent change
        if compare_avg > 0:
            pct_change = ((recent_avg - compare_avg) / compare_avg) * 100
        else:
            pct_change = 0
        
        # Determine direction
        if abs(pct_change) < 5:
            direction = TrendDirection.STABLE
            description = "Your calorie intake has been stable."
        elif pct_change > 10:
            direction = TrendDirection.INCREASING
            description = f"Your calorie intake increased {abs(pct_change):.0f}% this week."
        elif pct_change < -10:
            direction = TrendDirection.DECREASING
            description = f"Your calorie intake decreased {abs(pct_change):.0f}% this week."
        else:
            direction = TrendDirection.VARIABLE
            description = f"Your calorie intake changed by {pct_change:+.0f}% this week."
        
        return NutritionTrend(
            trend_type=TrendType.CALORIE,
            direction=direction,
            magnitude=abs(pct_change),
            description=description,
            values=recent_values,
            dates=recent_dates,
            current_avg=recent_avg,
            previous_avg=compare_avg,
            percent_change=pct_change,
            days_analyzed=recent_days + compare_days,
        )
    
    async def analyze_macro_trend(
        self,
        macro: str,
        recent_days: int = 7,
        compare_days: int = 7
    ) -> Optional[NutritionTrend]:
        """Analyze a specific macro trend."""
        end = date.today()
        recent_start = end - timedelta(days=recent_days - 1)
        compare_start = recent_start - timedelta(days=compare_days)
        compare_end = recent_start - timedelta(days=1)
        
        # Get daily values
        recent_values = []
        current = recent_start
        while current <= end:
            nutrients = self._history.get_daily_nutrients(current)
            val = getattr(nutrients.macros, macro, 0)
            if val > 0:
                recent_values.append(val)
            current += timedelta(days=1)
        
        compare_values = []
        current = compare_start
        while current <= compare_end:
            nutrients = self._history.get_daily_nutrients(current)
            val = getattr(nutrients.macros, macro, 0)
            if val > 0:
                compare_values.append(val)
            current += timedelta(days=1)
        
        if not recent_values or not compare_values:
            return None
        
        # Calculate averages
        recent_avg = sum(recent_values) / len(recent_values)
        compare_avg = sum(compare_values) / len(compare_values)
        
        if compare_avg > 0:
            pct_change = ((recent_avg - compare_avg) / compare_avg) * 100
        else:
            pct_change = 0
        
        # Map macro to trend type
        trend_type_map = {
            "protein": TrendType.PROTEIN,
            "carbohydrates": TrendType.CARBS,
            "fat": TrendType.FAT,
            "fiber": TrendType.FIBER,
        }
        trend_type = trend_type_map.get(macro, TrendType.CALORIE)
        
        # Determine direction
        if abs(pct_change) < 10:
            direction = TrendDirection.STABLE
            description = f"Your {macro} intake has been stable."
        elif pct_change > 0:
            direction = TrendDirection.INCREASING
            description = f"Your {macro} intake increased {abs(pct_change):.0f}%."
        else:
            direction = TrendDirection.DECREASING
            description = f"Your {macro} intake decreased {abs(pct_change):.0f}%."
        
        return NutritionTrend(
            trend_type=trend_type,
            direction=direction,
            magnitude=abs(pct_change),
            description=description,
            values=recent_values,
            current_avg=recent_avg,
            previous_avg=compare_avg,
            percent_change=pct_change,
            days_analyzed=recent_days + compare_days,
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def analyze_trends(
    recent_days: int = 7,
    compare_days: int = 7
) -> List[NutritionTrend]:
    """Convenience function to analyze all trends."""
    analyzer = TrendAnalyzer()
    return await analyzer.analyze_all_trends(recent_days, compare_days)
