"""
Pattern Detection

Detects dietary patterns from meal history.

Patterns Detected:
- Eating schedule (regular, irregular, grazer, etc.)
- Macro balance (high-protein, high-carb, balanced, etc.)
- Food preferences (favorite foods, avoided foods)
- Meal timing (early riser, late eater, etc.)

@module PatternDetector
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging

from ..schema import MealEntry, MealType, FoodCategory, NutrientProfile
from ..tracker.history import MealHistory, get_history

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERN TYPES
# =============================================================================

class PatternType(str, Enum):
    """Types of dietary patterns."""
    EATING_SCHEDULE = "eating_schedule"
    MACRO_BALANCE = "macro_balance"
    FOOD_PREFERENCE = "food_preference"
    MEAL_TIMING = "meal_timing"
    CALORIE_PATTERN = "calorie_pattern"
    VARIETY = "variety"


@dataclass
class DietaryPattern:
    """A detected dietary pattern."""
    pattern_type: PatternType
    name: str                            # e.g., "High Protein Diet"
    description: str
    confidence: float                    # 0.0 to 1.0
    
    # Supporting data
    evidence: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Time period analyzed
    days_analyzed: int = 0
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "name": self.name,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metrics": self.metrics,
            "days_analyzed": self.days_analyzed,
            "detected_at": self.detected_at.isoformat(),
        }


# =============================================================================
# PATTERN DETECTOR
# =============================================================================

class PatternDetector:
    """
    Detects dietary patterns from meal history.
    
    Analyzes eating habits over time to identify:
    - Consistent patterns (regular meals, balanced diet)
    - Potential issues (skipping meals, imbalanced macros)
    - Preferences (favorite foods, avoided foods)
    """
    
    def __init__(self, history: Optional[MealHistory] = None):
        self._history = history or get_history()
    
    async def detect_all_patterns(
        self,
        days: int = 30
    ) -> List[DietaryPattern]:
        """Detect all patterns from the last N days."""
        patterns = []
        
        # Detect each pattern type
        schedule = await self.detect_eating_schedule(days)
        if schedule:
            patterns.append(schedule)
        
        macro = await self.detect_macro_balance(days)
        if macro:
            patterns.append(macro)
        
        timing = await self.detect_meal_timing(days)
        if timing:
            patterns.append(timing)
        
        variety = await self.detect_variety_pattern(days)
        if variety:
            patterns.append(variety)
        
        return patterns
    
    async def detect_eating_schedule(
        self,
        days: int = 30
    ) -> Optional[DietaryPattern]:
        """
        Detect eating schedule pattern.
        
        Patterns:
        - regular: Consistent 3 meals/day
        - irregular: Inconsistent meal count
        - grazer: Many small meals (5+)
        - meal_skipper: Frequently misses meals
        """
        meals_per_day = []
        end = date.today()
        
        for i in range(days):
            d = end - timedelta(days=i)
            meals = self._history.get_meals_for_date(d)
            if meals:  # Only count days with data
                meals_per_day.append(len(meals))
        
        if len(meals_per_day) < 7:
            return None  # Not enough data
        
        avg_meals = sum(meals_per_day) / len(meals_per_day)
        variance = sum((m - avg_meals) ** 2 for m in meals_per_day) / len(meals_per_day)
        
        # Determine pattern
        if avg_meals >= 4.5:
            pattern_name = "Grazer"
            description = "You tend to eat many small meals throughout the day."
        elif avg_meals < 2:
            pattern_name = "Meal Skipper"
            description = "You frequently skip meals. Consider more consistent eating."
        elif variance < 0.5:
            pattern_name = "Regular Eater"
            description = "You have a consistent eating schedule."
        else:
            pattern_name = "Irregular Eater"
            description = "Your meal patterns vary significantly day to day."
        
        confidence = min(0.95, len(meals_per_day) / days)
        
        return DietaryPattern(
            pattern_type=PatternType.EATING_SCHEDULE,
            name=pattern_name,
            description=description,
            confidence=confidence,
            evidence=[
                f"Average {avg_meals:.1f} meals per day",
                f"Analyzed {len(meals_per_day)} days with data",
            ],
            metrics={
                "avg_meals_per_day": avg_meals,
                "variance": variance,
            },
            days_analyzed=days,
        )
    
    async def detect_macro_balance(
        self,
        days: int = 30
    ) -> Optional[DietaryPattern]:
        """
        Detect macro balance pattern.
        
        Patterns:
        - balanced: ~30% protein, ~40% carbs, ~30% fat
        - high_protein: >35% protein
        - high_carb: >55% carbs
        - high_fat: >40% fat (keto-like)
        - low_calorie: Consistently under 1500 cal/day
        """
        avg_nutrients = self._history.get_average_daily_nutrients(days)
        
        if avg_nutrients.macros.calories < 100:
            return None  # Not enough data
        
        # Calculate percentages
        cal = avg_nutrients.macros.calories
        protein_cal = avg_nutrients.macros.protein * 4
        carb_cal = avg_nutrients.macros.carbohydrates * 4
        fat_cal = avg_nutrients.macros.fat * 9
        
        total_macro_cal = protein_cal + carb_cal + fat_cal
        if total_macro_cal == 0:
            return None
        
        protein_pct = protein_cal / total_macro_cal
        carb_pct = carb_cal / total_macro_cal
        fat_pct = fat_cal / total_macro_cal
        
        # Determine pattern
        if protein_pct > 0.35:
            pattern_name = "High Protein"
            description = f"Your diet is {protein_pct*100:.0f}% protein - above average."
        elif carb_pct > 0.55:
            pattern_name = "High Carb"
            description = f"Your diet is {carb_pct*100:.0f}% carbohydrates."
        elif fat_pct > 0.40:
            pattern_name = "High Fat"
            description = f"Your diet is {fat_pct*100:.0f}% fat - similar to keto."
        elif cal < 1500:
            pattern_name = "Low Calorie"
            description = f"Averaging {cal:.0f} calories/day - on the lower end."
        else:
            pattern_name = "Balanced"
            description = "Your macronutrient balance is well-proportioned."
        
        return DietaryPattern(
            pattern_type=PatternType.MACRO_BALANCE,
            name=pattern_name,
            description=description,
            confidence=0.85,
            evidence=[
                f"Protein: {protein_pct*100:.1f}%",
                f"Carbs: {carb_pct*100:.1f}%",
                f"Fat: {fat_pct*100:.1f}%",
                f"Avg calories: {cal:.0f}/day",
            ],
            metrics={
                "protein_pct": protein_pct,
                "carb_pct": carb_pct,
                "fat_pct": fat_pct,
                "avg_calories": cal,
            },
            days_analyzed=days,
        )
    
    async def detect_meal_timing(
        self,
        days: int = 30
    ) -> Optional[DietaryPattern]:
        """
        Detect meal timing pattern.
        
        Patterns:
        - early_bird: First meal before 8am
        - late_starter: First meal after 11am
        - late_eater: Last meal after 9pm
        - consistent_timer: Consistent meal times
        """
        times = self._history.get_eating_times(days)
        
        # Get breakfast times
        breakfast_times = times.get(MealType.BREAKFAST, [])
        dinner_times = times.get(MealType.DINNER, [])
        
        if not breakfast_times and not dinner_times:
            return None
        
        # Analyze first meal timing
        if breakfast_times:
            avg_breakfast = sum(breakfast_times) / len(breakfast_times)
            
            if avg_breakfast < 8:
                pattern_name = "Early Bird"
                description = f"You typically start eating around {avg_breakfast:.0f}:00."
            elif avg_breakfast > 11:
                pattern_name = "Late Starter"
                description = f"Your first meal is usually after {avg_breakfast:.0f}:00."
            else:
                pattern_name = "Standard Schedule"
                description = "Your meal timing is typical."
        else:
            pattern_name = "Unknown"
            description = "Not enough breakfast data to analyze timing."
        
        # Check for late eating
        if dinner_times:
            avg_dinner = sum(dinner_times) / len(dinner_times)
            if avg_dinner > 21:
                pattern_name = "Late Eater"
                description = f"Your last meal is often around {avg_dinner:.0f}:00."
        
        return DietaryPattern(
            pattern_type=PatternType.MEAL_TIMING,
            name=pattern_name,
            description=description,
            confidence=0.75,
            evidence=[
                f"Analyzed {len(breakfast_times)} breakfasts",
                f"Analyzed {len(dinner_times)} dinners",
            ],
            metrics={
                "avg_breakfast_hour": sum(breakfast_times) / len(breakfast_times) if breakfast_times else None,
                "avg_dinner_hour": sum(dinner_times) / len(dinner_times) if dinner_times else None,
            },
            days_analyzed=days,
        )
    
    async def detect_variety_pattern(
        self,
        days: int = 30
    ) -> Optional[DietaryPattern]:
        """
        Detect food variety pattern.
        
        Patterns:
        - varied: Many unique foods
        - repetitive: Same foods frequently
        - category_focused: Heavy on one category
        """
        end = date.today()
        start = end - timedelta(days=days - 1)
        meals = self._history.get_meals_in_range(start, end)
        
        if not meals:
            return None
        
        # Count unique foods
        food_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        
        for meal in meals:
            for food in meal.foods:
                name = food.name.lower()
                food_counts[name] = food_counts.get(name, 0) + 1
                category_counts[food.category.value] = category_counts.get(food.category.value, 0) + 1
        
        total_foods = sum(food_counts.values())
        unique_foods = len(food_counts)
        
        if total_foods == 0:
            return None
        
        variety_ratio = unique_foods / total_foods
        
        # Determine pattern
        if variety_ratio > 0.5:
            pattern_name = "Varied Diet"
            description = "You eat a wide variety of different foods."
        elif variety_ratio < 0.2:
            # Find most repeated food
            most_common = max(food_counts.items(), key=lambda x: x[1])
            pattern_name = "Repetitive Diet"
            description = f"You tend to eat the same foods. {most_common[0]} appears {most_common[1]} times."
        else:
            pattern_name = "Moderate Variety"
            description = "You have a reasonable variety in your diet."
        
        return DietaryPattern(
            pattern_type=PatternType.VARIETY,
            name=pattern_name,
            description=description,
            confidence=0.8,
            evidence=[
                f"{unique_foods} unique foods from {total_foods} total",
                f"Variety ratio: {variety_ratio:.1%}",
            ],
            metrics={
                "unique_foods": unique_foods,
                "total_foods": total_foods,
                "variety_ratio": variety_ratio,
                "category_breakdown": category_counts,
            },
            days_analyzed=days,
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def detect_patterns(days: int = 30) -> List[DietaryPattern]:
    """Convenience function to detect all patterns."""
    detector = PatternDetector()
    return await detector.detect_all_patterns(days)
