"""
Nutrient Calculation and Lookup

Handles nutrient data lookup and calculation:
- Food database integration (USDA, OpenFoodFacts)
- Nutrient calculation from ingredients
- Portion scaling

This is a SCAFFOLD with placeholder data.
Real implementation would integrate with food databases.

@module NutrientCalculator
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from ..schema import (
    FoodEntry,
    NutrientProfile,
    MacroNutrients,
    MicroNutrients,
    FoodCategory,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PLACEHOLDER FOOD DATABASE
# =============================================================================

# This would normally come from USDA or OpenFoodFacts API
# Storing common foods with their nutrients per 100g
FOOD_DATABASE: Dict[str, Dict[str, Any]] = {
    "chicken breast": {
        "category": "protein",
        "macros": {
            "calories": 165,
            "protein": 31,
            "carbohydrates": 0,
            "fat": 3.6,
            "fiber": 0,
            "sugar": 0,
            "sodium": 74,
        },
        "serving_grams": 100,
    },
    "rice": {
        "category": "grain",
        "macros": {
            "calories": 130,
            "protein": 2.7,
            "carbohydrates": 28,
            "fat": 0.3,
            "fiber": 0.4,
            "sugar": 0,
            "sodium": 1,
        },
        "serving_grams": 100,
    },
    "broccoli": {
        "category": "vegetable",
        "macros": {
            "calories": 34,
            "protein": 2.8,
            "carbohydrates": 7,
            "fat": 0.4,
            "fiber": 2.6,
            "sugar": 1.7,
            "sodium": 33,
        },
        "serving_grams": 100,
    },
    "salmon": {
        "category": "protein",
        "macros": {
            "calories": 208,
            "protein": 20,
            "carbohydrates": 0,
            "fat": 13,
            "fiber": 0,
            "sugar": 0,
            "sodium": 59,
        },
        "serving_grams": 100,
    },
    "egg": {
        "category": "protein",
        "macros": {
            "calories": 155,
            "protein": 13,
            "carbohydrates": 1.1,
            "fat": 11,
            "fiber": 0,
            "sugar": 1.1,
            "sodium": 124,
        },
        "serving_grams": 50,  # One egg
    },
    "apple": {
        "category": "fruit",
        "macros": {
            "calories": 52,
            "protein": 0.3,
            "carbohydrates": 14,
            "fat": 0.2,
            "fiber": 2.4,
            "sugar": 10,
            "sodium": 1,
        },
        "serving_grams": 182,  # One medium apple
    },
    "avocado": {
        "category": "fat",
        "macros": {
            "calories": 160,
            "protein": 2,
            "carbohydrates": 9,
            "fat": 15,
            "fiber": 7,
            "sugar": 0.7,
            "sodium": 7,
        },
        "serving_grams": 150,  # One avocado
    },
    "oatmeal": {
        "category": "grain",
        "macros": {
            "calories": 389,
            "protein": 17,
            "carbohydrates": 66,
            "fat": 7,
            "fiber": 11,
            "sugar": 1,
            "sodium": 2,
        },
        "serving_grams": 100,
    },
}

# Default nutrients when food not found
DEFAULT_NUTRIENTS = {
    "macros": {
        "calories": 100,
        "protein": 5,
        "carbohydrates": 10,
        "fat": 5,
        "fiber": 2,
        "sugar": 3,
        "sodium": 100,
    },
    "serving_grams": 100,
}


# =============================================================================
# NUTRIENT LOOKUP
# =============================================================================

class NutrientLookup:
    """
    Looks up nutrients for foods from databases.
    
    SCAFFOLD: Uses placeholder database.
    Real implementation would query:
    - USDA FoodData Central API
    - OpenFoodFacts API
    - Local cache
    """
    
    def __init__(self):
        self._cache: Dict[str, NutrientProfile] = {}
    
    async def lookup(self, food_name: str) -> Optional[NutrientProfile]:
        """
        Look up nutrients for a food by name.
        
        Returns None if not found.
        """
        # Check cache first
        cache_key = food_name.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Search database
        profile = await self._search_database(cache_key)
        
        if profile:
            self._cache[cache_key] = profile
        
        return profile
    
    async def _search_database(self, search_term: str) -> Optional[NutrientProfile]:
        """Search the food database."""
        # Try exact match first
        if search_term in FOOD_DATABASE:
            return self._create_profile(FOOD_DATABASE[search_term])
        
        # Try partial match
        for food_name, data in FOOD_DATABASE.items():
            if search_term in food_name or food_name in search_term:
                return self._create_profile(data)
        
        return None
    
    def _create_profile(self, data: Dict[str, Any]) -> NutrientProfile:
        """Create NutrientProfile from database data."""
        macros_data = data.get("macros", {})
        
        macros = MacroNutrients(
            calories=macros_data.get("calories", 0),
            protein=macros_data.get("protein", 0),
            carbohydrates=macros_data.get("carbohydrates", 0),
            fat=macros_data.get("fat", 0),
            fiber=macros_data.get("fiber", 0),
            sugar=macros_data.get("sugar", 0),
            sodium=macros_data.get("sodium", 0),
        )
        
        return NutrientProfile(
            macros=macros,
            serving_size=data.get("serving_grams", 100),
            serving_unit="g",
            servings=1.0,
        )
    
    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, NutrientProfile]]:
        """
        Search for foods matching a query.
        
        Returns list of (name, profile) tuples.
        """
        results = []
        query_lower = query.lower()
        
        for food_name, data in FOOD_DATABASE.items():
            if query_lower in food_name:
                profile = self._create_profile(data)
                results.append((food_name, profile))
                
                if len(results) >= limit:
                    break
        
        return results


# =============================================================================
# NUTRIENT CALCULATOR
# =============================================================================

class NutrientCalculator:
    """
    Calculates nutrients for foods and meals.
    
    Handles:
    - Nutrient lookup
    - Portion scaling
    - Summing multiple foods
    """
    
    def __init__(self):
        self._lookup = NutrientLookup()
    
    async def calculate(self, food: FoodEntry) -> NutrientProfile:
        """
        Calculate nutrients for a food entry.
        
        Uses the food's existing nutrients if available,
        otherwise looks up from database.
        """
        # If food already has detailed nutrients, use them
        if food.nutrients and food.nutrients.macros.calories > 0:
            # Scale to actual quantity
            return food.get_total_nutrients()
        
        # Look up in database
        profile = await self._lookup.lookup(food.name)
        
        if profile is None:
            # Use default with warning
            logger.warning(f"[NutrientCalculator] No data for: {food.name}")
            profile = self._get_default_profile()
        
        # Scale to quantity
        return profile.scale_to_servings(food.quantity)
    
    async def lookup_and_calculate(
        self,
        food_name: str,
        quantity: float = 1.0,
        unit: str = "serving"
    ) -> NutrientProfile:
        """
        Look up a food and calculate nutrients.
        
        Args:
            food_name: Name of the food
            quantity: Number of units
            unit: Unit type (serving, cup, oz, etc.)
        
        Returns:
            NutrientProfile scaled to quantity
        """
        profile = await self._lookup.lookup(food_name)
        
        if profile is None:
            profile = self._get_default_profile()
        
        # Convert unit to serving multiplier
        multiplier = self._unit_to_multiplier(quantity, unit, profile.serving_size)
        
        return profile.scale_to_servings(multiplier)
    
    def sum_nutrients(self, foods: List[FoodEntry]) -> NutrientProfile:
        """
        Sum nutrients across multiple foods.
        
        Returns combined NutrientProfile.
        """
        if not foods:
            return NutrientProfile()
        
        total_macros = MacroNutrients()
        total_micros = MicroNutrients()
        
        for food in foods:
            food_nutrients = food.get_total_nutrients()
            total_macros = total_macros + food_nutrients.macros
        
        return NutrientProfile(macros=total_macros, micros=total_micros)
    
    def _get_default_profile(self) -> NutrientProfile:
        """Get default nutrient profile for unknown foods."""
        macros = MacroNutrients(**DEFAULT_NUTRIENTS["macros"])
        return NutrientProfile(
            macros=macros,
            serving_size=DEFAULT_NUTRIENTS["serving_grams"],
        )
    
    def _unit_to_multiplier(
        self,
        quantity: float,
        unit: str,
        base_serving_grams: float
    ) -> float:
        """
        Convert a quantity and unit to a serving multiplier.
        
        SCAFFOLD: Basic conversion. Real implementation would
        have comprehensive unit conversion tables.
        """
        unit_lower = unit.lower()
        
        # Gram-based units
        gram_equivalents = {
            "g": 1,
            "gram": 1,
            "grams": 1,
            "kg": 1000,
            "oz": 28.35,
            "ounce": 28.35,
            "lb": 453.6,
            "pound": 453.6,
        }
        
        if unit_lower in gram_equivalents:
            total_grams = quantity * gram_equivalents[unit_lower]
            return total_grams / base_serving_grams
        
        # Volume-based (approximate)
        volume_grams = {
            "cup": 240,
            "cups": 240,
            "tbsp": 15,
            "tablespoon": 15,
            "tsp": 5,
            "teaspoon": 5,
            "ml": 1,
            "l": 1000,
            "liter": 1000,
        }
        
        if unit_lower in volume_grams:
            total_grams = quantity * volume_grams[unit_lower]
            return total_grams / base_serving_grams
        
        # Default: assume "serving" means 1x base serving
        return quantity


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def calculate_nutrients(
    food_name: str,
    quantity: float = 1.0,
    unit: str = "serving"
) -> NutrientProfile:
    """
    Convenience function to calculate nutrients.
    
    Creates calculator and runs calculation.
    """
    calc = NutrientCalculator()
    return await calc.lookup_and_calculate(food_name, quantity, unit)
