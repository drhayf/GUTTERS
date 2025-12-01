"""
Health Scoring for Foods and Meals

Assigns health scores to foods, meals, and daily intake.
Uses multiple factors to compute a holistic score.

Scoring Dimensions:
- Nutrient balance (macros)
- Micronutrient coverage
- Processing level
- Variety
- Goal alignment

@module HealthScorer
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
import logging

from ..schema import (
    FoodEntry,
    MealEntry,
    NutrientProfile,
    MacroNutrients,
    FoodCategory,
    DietaryPreference,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SCORE TYPES
# =============================================================================

@dataclass
class ScoreBreakdown:
    """Breakdown of a health score into components."""
    nutrient_balance: float = 0.0      # 0-100: macro balance
    protein_adequacy: float = 0.0      # 0-100: protein intake
    fiber_score: float = 0.0           # 0-100: fiber intake
    processing_score: float = 0.0      # 0-100: whole vs processed
    variety_score: float = 0.0         # 0-100: food variety
    goal_alignment: float = 0.0        # 0-100: alignment with goals
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "nutrient_balance": self.nutrient_balance,
            "protein_adequacy": self.protein_adequacy,
            "fiber_score": self.fiber_score,
            "processing_score": self.processing_score,
            "variety_score": self.variety_score,
            "goal_alignment": self.goal_alignment,
        }


@dataclass
class MealScore:
    """Health score for a single meal."""
    overall: float = 0.0               # 0-100 overall score
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    
    # Feedback
    positives: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    
    # Metadata
    food_count: int = 0
    total_calories: float = 0.0
    scored_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "breakdown": self.breakdown.to_dict(),
            "positives": self.positives,
            "improvements": self.improvements,
            "food_count": self.food_count,
            "total_calories": self.total_calories,
            "scored_at": self.scored_at.isoformat(),
        }


@dataclass
class DailyScore:
    """Health score for a full day of eating."""
    overall: float = 0.0
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    
    # Meal scores
    meal_scores: List[MealScore] = field(default_factory=list)
    
    # Daily metrics
    total_calories: float = 0.0
    calorie_target: Optional[float] = None
    calorie_variance: float = 0.0
    
    # Daily feedback
    achievements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Date
    date: date = field(default_factory=date.today)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "breakdown": self.breakdown.to_dict(),
            "meal_scores": [m.to_dict() for m in self.meal_scores],
            "total_calories": self.total_calories,
            "calorie_target": self.calorie_target,
            "calorie_variance": self.calorie_variance,
            "achievements": self.achievements,
            "recommendations": self.recommendations,
            "date": self.date.isoformat(),
        }


# =============================================================================
# HEALTH SCORER
# =============================================================================

class HealthScorer:
    """
    Calculates health scores for foods and meals.
    
    Uses a multi-factor scoring system that considers:
    - Macronutrient balance
    - Protein adequacy
    - Fiber content
    - Processing level
    - Food variety
    - Goal alignment
    
    Scores are 0-100 where:
    - 90-100: Excellent
    - 75-89: Good
    - 60-74: Fair
    - 40-59: Needs improvement
    - 0-39: Poor
    """
    
    # Reference values for scoring
    IDEAL_MACRO_RATIOS = {
        "protein": (0.15, 0.35),      # 15-35% of calories
        "carbs": (0.45, 0.65),        # 45-65% of calories
        "fat": (0.20, 0.35),          # 20-35% of calories
    }
    
    DAILY_TARGETS = {
        "fiber": 25,                   # grams
        "protein_per_kg": 0.8,         # grams per kg body weight
        "sodium_max": 2300,            # mg
    }
    
    # Weight for each scoring dimension
    SCORE_WEIGHTS = {
        "nutrient_balance": 0.25,
        "protein_adequacy": 0.20,
        "fiber_score": 0.15,
        "processing_score": 0.15,
        "variety_score": 0.15,
        "goal_alignment": 0.10,
    }
    
    def __init__(self, preferences: Optional[DietaryPreference] = None):
        self._preferences = preferences
    
    async def score_foods(
        self,
        foods: List[FoodEntry]
    ) -> float:
        """
        Score a list of foods.
        
        Returns overall health score 0-100.
        """
        if not foods:
            return 0.0
        
        meal_score = await self.score_meal_foods(foods)
        return meal_score.overall
    
    async def score_meal_foods(
        self,
        foods: List[FoodEntry]
    ) -> MealScore:
        """
        Score a list of foods as a meal.
        
        Returns detailed MealScore.
        """
        if not foods:
            return MealScore()
        
        # Calculate combined nutrients
        total_macros = MacroNutrients()
        categories_seen = set()
        
        for food in foods:
            food_nutrients = food.get_total_nutrients()
            total_macros = total_macros + food_nutrients.macros
            categories_seen.add(food.category)
        
        # Calculate breakdown scores
        breakdown = ScoreBreakdown(
            nutrient_balance=self._score_macro_balance(total_macros),
            protein_adequacy=self._score_protein(total_macros),
            fiber_score=self._score_fiber(total_macros),
            processing_score=self._score_processing(foods),
            variety_score=self._score_variety(categories_seen),
            goal_alignment=self._score_goal_alignment(total_macros),
        )
        
        # Calculate weighted overall
        overall = sum(
            getattr(breakdown, dim) * weight
            for dim, weight in self.SCORE_WEIGHTS.items()
        )
        
        # Generate feedback
        positives, improvements = self._generate_feedback(breakdown, total_macros, foods)
        
        return MealScore(
            overall=round(overall, 1),
            breakdown=breakdown,
            positives=positives,
            improvements=improvements,
            food_count=len(foods),
            total_calories=total_macros.calories,
        )
    
    async def score_meal(self, meal: MealEntry) -> MealScore:
        """Score a MealEntry."""
        return await self.score_meal_foods(meal.foods)
    
    async def score_nutrients(self, nutrients: NutrientProfile) -> float:
        """Score a NutrientProfile directly."""
        breakdown = ScoreBreakdown(
            nutrient_balance=self._score_macro_balance(nutrients.macros),
            protein_adequacy=self._score_protein(nutrients.macros),
            fiber_score=self._score_fiber(nutrients.macros),
            processing_score=75,  # Assume moderate processing
            variety_score=50,     # Unknown variety
            goal_alignment=self._score_goal_alignment(nutrients.macros),
        )
        
        return sum(
            getattr(breakdown, dim) * weight
            for dim, weight in self.SCORE_WEIGHTS.items()
        )
    
    async def score_day(
        self,
        meals: List[MealEntry],
        calorie_target: Optional[float] = None
    ) -> DailyScore:
        """
        Score a full day of meals.
        
        Considers meal timing, total intake, variety across meals.
        """
        if not meals:
            return DailyScore()
        
        # Score each meal
        meal_scores = []
        total_macros = MacroNutrients()
        all_categories = set()
        
        for meal in meals:
            meal_score = await self.score_meal(meal)
            meal_scores.append(meal_score)
            
            for food in meal.foods:
                total_macros = total_macros + food.get_total_nutrients().macros
                all_categories.add(food.category)
        
        # Calculate daily breakdown
        breakdown = ScoreBreakdown(
            nutrient_balance=self._score_macro_balance(total_macros),
            protein_adequacy=self._score_protein(total_macros),
            fiber_score=self._score_fiber(total_macros),
            processing_score=sum(m.breakdown.processing_score for m in meal_scores) / len(meal_scores),
            variety_score=self._score_variety(all_categories),
            goal_alignment=self._score_goal_alignment(total_macros),
        )
        
        # Overall weighted score
        overall = sum(
            getattr(breakdown, dim) * weight
            for dim, weight in self.SCORE_WEIGHTS.items()
        )
        
        # Calorie variance
        target = calorie_target or (self._preferences.calorie_target if self._preferences else None)
        variance = 0.0
        if target:
            variance = ((total_macros.calories - target) / target) * 100
        
        # Generate daily feedback
        achievements, recommendations = self._generate_daily_feedback(
            breakdown, total_macros, meals, target
        )
        
        return DailyScore(
            overall=round(overall, 1),
            breakdown=breakdown,
            meal_scores=meal_scores,
            total_calories=total_macros.calories,
            calorie_target=target,
            calorie_variance=variance,
            achievements=achievements,
            recommendations=recommendations,
        )
    
    # -------------------------------------------------------------------------
    # Individual Scoring Functions
    # -------------------------------------------------------------------------
    
    def _score_macro_balance(self, macros: MacroNutrients) -> float:
        """Score macronutrient balance."""
        if macros.calories < 10:
            return 0.0
        
        # Calculate macro percentages
        protein_cal = macros.protein * 4
        carb_cal = macros.carbohydrates * 4
        fat_cal = macros.fat * 9
        total_cal = protein_cal + carb_cal + fat_cal
        
        if total_cal == 0:
            return 0.0
        
        protein_pct = protein_cal / total_cal
        carb_pct = carb_cal / total_cal
        fat_pct = fat_cal / total_cal
        
        # Score each macro
        scores = []
        
        for actual, (low, high) in [
            (protein_pct, self.IDEAL_MACRO_RATIOS["protein"]),
            (carb_pct, self.IDEAL_MACRO_RATIOS["carbs"]),
            (fat_pct, self.IDEAL_MACRO_RATIOS["fat"]),
        ]:
            if low <= actual <= high:
                scores.append(100)
            elif actual < low:
                scores.append(max(0, 100 - (low - actual) * 200))
            else:
                scores.append(max(0, 100 - (actual - high) * 200))
        
        return sum(scores) / len(scores)
    
    def _score_protein(self, macros: MacroNutrients) -> float:
        """Score protein adequacy."""
        if macros.calories < 10:
            return 0.0
        
        # Protein per 1000 calories (should be ~50-80g)
        protein_per_1000 = (macros.protein / macros.calories) * 1000
        
        if protein_per_1000 >= 50:
            return min(100, 50 + protein_per_1000)
        else:
            return max(0, protein_per_1000 * 2)
    
    def _score_fiber(self, macros: MacroNutrients) -> float:
        """Score fiber intake."""
        if macros.calories < 10:
            return 0.0
        
        # Fiber per 1000 calories (should be ~14g)
        fiber_per_1000 = (macros.fiber / macros.calories) * 1000
        target_per_1000 = 14
        
        return min(100, (fiber_per_1000 / target_per_1000) * 100)
    
    def _score_processing(self, foods: List[FoodEntry]) -> float:
        """Score processing level (prefer whole foods)."""
        if not foods:
            return 0.0
        
        # Categories that indicate whole foods
        whole_food_categories = {
            FoodCategory.PROTEIN,
            FoodCategory.VEGETABLE,
            FoodCategory.FRUIT,
            FoodCategory.GRAIN,
        }
        
        whole_count = sum(1 for f in foods if f.category in whole_food_categories)
        processed_count = sum(1 for f in foods if f.category == FoodCategory.PROCESSED)
        
        whole_ratio = whole_count / len(foods)
        processed_penalty = (processed_count / len(foods)) * 30
        
        return max(0, min(100, whole_ratio * 100 - processed_penalty))
    
    def _score_variety(self, categories: set) -> float:
        """Score food variety."""
        # More categories = more variety
        # Ideal: at least 4 different categories
        variety_count = len(categories)
        
        if variety_count >= 5:
            return 100
        elif variety_count >= 4:
            return 90
        elif variety_count >= 3:
            return 70
        elif variety_count >= 2:
            return 50
        else:
            return 25
    
    def _score_goal_alignment(self, macros: MacroNutrients) -> float:
        """Score alignment with user's goals."""
        if not self._preferences:
            return 75  # Default neutral score
        
        score = 100.0
        
        # Calorie alignment
        if self._preferences.calorie_target:
            # For a single meal, compare proportionally
            meal_target = self._preferences.calorie_target / self._preferences.meals_per_day
            if macros.calories > 0:
                variance = abs(macros.calories - meal_target) / meal_target
                score -= min(30, variance * 50)
        
        return max(0, score)
    
    # -------------------------------------------------------------------------
    # Feedback Generation
    # -------------------------------------------------------------------------
    
    def _generate_feedback(
        self,
        breakdown: ScoreBreakdown,
        macros: MacroNutrients,
        foods: List[FoodEntry]
    ) -> tuple:
        """Generate positive and improvement feedback."""
        positives = []
        improvements = []
        
        # Check each dimension
        if breakdown.protein_adequacy >= 75:
            positives.append("Good protein content")
        elif breakdown.protein_adequacy < 50:
            improvements.append("Consider adding more protein")
        
        if breakdown.fiber_score >= 75:
            positives.append("Great fiber intake")
        elif breakdown.fiber_score < 50:
            improvements.append("Add more vegetables or whole grains for fiber")
        
        if breakdown.variety_score >= 75:
            positives.append("Good food variety")
        elif breakdown.variety_score < 50:
            improvements.append("Try to include more food groups")
        
        if breakdown.processing_score >= 75:
            positives.append("Mostly whole foods")
        elif breakdown.processing_score < 50:
            improvements.append("Consider replacing processed items with whole foods")
        
        return positives, improvements
    
    def _generate_daily_feedback(
        self,
        breakdown: ScoreBreakdown,
        macros: MacroNutrients,
        meals: List[MealEntry],
        calorie_target: Optional[float]
    ) -> tuple:
        """Generate daily achievements and recommendations."""
        achievements = []
        recommendations = []
        
        # Check calorie target
        if calorie_target:
            variance = abs(macros.calories - calorie_target) / calorie_target
            if variance < 0.1:
                achievements.append("Hit your calorie target!")
            elif macros.calories < calorie_target:
                recommendations.append(f"You're {int(calorie_target - macros.calories)} calories under target")
            else:
                recommendations.append(f"You're {int(macros.calories - calorie_target)} calories over target")
        
        # Check protein
        if macros.protein >= 100:
            achievements.append("Excellent protein intake")
        
        # Check fiber
        if macros.fiber >= 25:
            achievements.append("Met your fiber goal")
        else:
            recommendations.append(f"Try to get {int(25 - macros.fiber)}g more fiber")
        
        return achievements, recommendations


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def score_meal(
    foods: List[FoodEntry],
    preferences: Optional[DietaryPreference] = None
) -> MealScore:
    """
    Convenience function to score a meal.
    
    Creates scorer and runs scoring.
    """
    scorer = HealthScorer(preferences)
    return await scorer.score_meal_foods(foods)
