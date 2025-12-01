"""
Nutrition Analyzer - Food Analysis Sub-Module

This sub-module handles all food analysis operations:
- Image-based food detection (using Gemini Vision)
- Nutrient calculation and lookup
- Health scoring for meals

Architecture (Fractal - can be extended):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
analyzer/
├── __init__.py       # Exports
├── image.py          # Image analysis (Gemini Vision)
├── nutrients.py      # Nutrient calculation
└── scoring.py        # Health scoring

Each file can be extended or replaced independently.

@module NutritionAnalyzer
"""

from .image import (
    ImageFoodAnalyzer,
    FoodDetectionResult,
    analyze_food_image,
)
from .nutrients import (
    NutrientCalculator,
    NutrientLookup,
    calculate_nutrients,
)
from .scoring import (
    HealthScorer,
    MealScore,
    DailyScore,
    score_meal,
)

# Convenience class that combines all analyzers
class FoodAnalyzer:
    """
    Unified food analyzer combining image, nutrient, and scoring.
    
    This is the main entry point for food analysis operations.
    """
    
    def __init__(self):
        self._image_analyzer = ImageFoodAnalyzer()
        self._nutrient_calc = NutrientCalculator()
        self._health_scorer = HealthScorer()
    
    async def analyze_from_image(
        self, 
        image_data: bytes,
        image_type: str = "jpeg"
    ) -> "AnalysisResult":
        """
        Analyze food from an image.
        
        Uses Gemini Vision to detect food, then calculates nutrients
        and health scores.
        """
        # Detect food from image
        detection = await self._image_analyzer.analyze(image_data, image_type)
        
        if not detection.foods:
            return AnalysisResult(
                success=False,
                error="No food detected in image"
            )
        
        # Calculate nutrients for each detected food
        for food in detection.foods:
            nutrients = await self._nutrient_calc.calculate(food)
            food.nutrients = nutrients
        
        # Score the meal
        score = await self._health_scorer.score_foods(detection.foods)
        
        return AnalysisResult(
            success=True,
            foods=detection.foods,
            total_nutrients=self._nutrient_calc.sum_nutrients(detection.foods),
            health_score=score,
            confidence=detection.confidence,
        )
    
    async def calculate_nutrients(
        self,
        food_name: str,
        quantity: float = 1.0,
        unit: str = "serving"
    ) -> "AnalysisResult":
        """Calculate nutrients for a named food."""
        nutrients = await self._nutrient_calc.lookup_and_calculate(
            food_name, quantity, unit
        )
        
        score = await self._health_scorer.score_nutrients(nutrients)
        
        return AnalysisResult(
            success=True,
            total_nutrients=nutrients,
            health_score=score,
            confidence=0.8,  # Lookup confidence
        )


# Analysis result type
from dataclasses import dataclass, field
from typing import List, Optional, Any
from ..schema import FoodEntry, NutrientProfile


@dataclass
class AnalysisResult:
    """Result of food analysis."""
    success: bool = True
    error: Optional[str] = None
    
    # Detected foods
    foods: List[FoodEntry] = field(default_factory=list)
    
    # Combined nutrients
    total_nutrients: Optional[NutrientProfile] = None
    
    # Health assessment
    health_score: Optional[float] = None
    health_notes: List[str] = field(default_factory=list)
    
    # Confidence in analysis
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "error": self.error,
            "foods": [f.to_dict() for f in self.foods],
            "total_nutrients": self.total_nutrients.to_dict() if self.total_nutrients else None,
            "health_score": self.health_score,
            "health_notes": self.health_notes,
            "confidence": self.confidence,
        }


__all__ = [
    "FoodAnalyzer",
    "AnalysisResult",
    "ImageFoodAnalyzer",
    "FoodDetectionResult",
    "analyze_food_image",
    "NutrientCalculator",
    "NutrientLookup",
    "calculate_nutrients",
    "HealthScorer",
    "MealScore",
    "DailyScore",
    "score_meal",
]
