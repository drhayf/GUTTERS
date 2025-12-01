"""
Nutrition Schema - Data Types and Trait Definitions

This module defines all data structures and trait schemas for the
Nutrition domain. These are the "nouns" of the nutrition system.

Key Types:
- FoodEntry: A single food item with nutrients
- MealEntry: A collection of foods in a meal
- NutrientProfile: Macro and micronutrient breakdown
- DietaryPreference: User's dietary preferences/restrictions

Schema Design:
- All types are dataclasses with to_dict() for serialization
- Trait schemas define what the domain tracks
- Validation is built into the types

@module NutritionSchema
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class MealType(str, Enum):
    """Types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DRINK = "drink"
    SUPPLEMENT = "supplement"
    OTHER = "other"


class DietType(str, Enum):
    """Dietary preference types."""
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low_carb"
    MEDITERRANEAN = "mediterranean"
    WHOLE30 = "whole30"
    INTERMITTENT_FASTING = "intermittent_fasting"
    CUSTOM = "custom"


class AllergenType(str, Enum):
    """Common allergens."""
    GLUTEN = "gluten"
    DAIRY = "dairy"
    EGGS = "eggs"
    NUTS = "nuts"
    PEANUTS = "peanuts"
    SOY = "soy"
    FISH = "fish"
    SHELLFISH = "shellfish"
    SESAME = "sesame"
    SULFITES = "sulfites"
    OTHER = "other"


class FoodCategory(str, Enum):
    """Food categories."""
    PROTEIN = "protein"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    GRAIN = "grain"
    DAIRY = "dairy"
    FAT = "fat"
    SUGAR = "sugar"
    BEVERAGE = "beverage"
    PROCESSED = "processed"
    SUPPLEMENT = "supplement"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class NutrientUnit(str, Enum):
    """Units for nutrients."""
    GRAMS = "g"
    MILLIGRAMS = "mg"
    MICROGRAMS = "mcg"
    KILOCALORIES = "kcal"
    KILOJOULES = "kj"
    MILLILITERS = "ml"
    PERCENT = "%"
    IU = "IU"


# =============================================================================
# NUTRIENT TYPES
# =============================================================================

@dataclass
class MacroNutrients:
    """
    Macronutrient breakdown.
    
    All values in grams unless otherwise noted.
    """
    calories: float = 0.0          # kcal
    protein: float = 0.0           # g
    carbohydrates: float = 0.0     # g
    fat: float = 0.0               # g
    fiber: float = 0.0             # g
    sugar: float = 0.0             # g
    saturated_fat: float = 0.0     # g
    trans_fat: float = 0.0         # g
    cholesterol: float = 0.0       # mg
    sodium: float = 0.0            # mg
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carbohydrates": self.carbohydrates,
            "fat": self.fat,
            "fiber": self.fiber,
            "sugar": self.sugar,
            "saturated_fat": self.saturated_fat,
            "trans_fat": self.trans_fat,
            "cholesterol": self.cholesterol,
            "sodium": self.sodium,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MacroNutrients":
        return cls(
            calories=data.get("calories", 0.0),
            protein=data.get("protein", 0.0),
            carbohydrates=data.get("carbohydrates", 0.0),
            fat=data.get("fat", 0.0),
            fiber=data.get("fiber", 0.0),
            sugar=data.get("sugar", 0.0),
            saturated_fat=data.get("saturated_fat", 0.0),
            trans_fat=data.get("trans_fat", 0.0),
            cholesterol=data.get("cholesterol", 0.0),
            sodium=data.get("sodium", 0.0),
        )
    
    def __add__(self, other: "MacroNutrients") -> "MacroNutrients":
        """Add two macro profiles together."""
        return MacroNutrients(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbohydrates=self.carbohydrates + other.carbohydrates,
            fat=self.fat + other.fat,
            fiber=self.fiber + other.fiber,
            sugar=self.sugar + other.sugar,
            saturated_fat=self.saturated_fat + other.saturated_fat,
            trans_fat=self.trans_fat + other.trans_fat,
            cholesterol=self.cholesterol + other.cholesterol,
            sodium=self.sodium + other.sodium,
        )


@dataclass
class MicroNutrients:
    """
    Micronutrient breakdown.
    
    Vitamins and minerals with their amounts.
    All values in mg unless noted.
    """
    # Vitamins (in mg or mcg)
    vitamin_a: float = 0.0         # mcg RAE
    vitamin_c: float = 0.0         # mg
    vitamin_d: float = 0.0         # mcg
    vitamin_e: float = 0.0         # mg
    vitamin_k: float = 0.0         # mcg
    vitamin_b1: float = 0.0        # mg (thiamine)
    vitamin_b2: float = 0.0        # mg (riboflavin)
    vitamin_b3: float = 0.0        # mg (niacin)
    vitamin_b6: float = 0.0        # mg
    vitamin_b12: float = 0.0       # mcg
    folate: float = 0.0            # mcg
    
    # Minerals (in mg)
    calcium: float = 0.0
    iron: float = 0.0
    magnesium: float = 0.0
    phosphorus: float = 0.0
    potassium: float = 0.0
    zinc: float = 0.0
    selenium: float = 0.0          # mcg
    copper: float = 0.0
    manganese: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "vitamin_a": self.vitamin_a,
            "vitamin_c": self.vitamin_c,
            "vitamin_d": self.vitamin_d,
            "vitamin_e": self.vitamin_e,
            "vitamin_k": self.vitamin_k,
            "vitamin_b1": self.vitamin_b1,
            "vitamin_b2": self.vitamin_b2,
            "vitamin_b3": self.vitamin_b3,
            "vitamin_b6": self.vitamin_b6,
            "vitamin_b12": self.vitamin_b12,
            "folate": self.folate,
            "calcium": self.calcium,
            "iron": self.iron,
            "magnesium": self.magnesium,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "zinc": self.zinc,
            "selenium": self.selenium,
            "copper": self.copper,
            "manganese": self.manganese,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MicroNutrients":
        return cls(**{k: data.get(k, 0.0) for k in cls.__dataclass_fields__})


@dataclass
class NutrientProfile:
    """
    Complete nutrient profile combining macros and micros.
    """
    macros: MacroNutrients = field(default_factory=MacroNutrients)
    micros: MicroNutrients = field(default_factory=MicroNutrients)
    
    # Serving info
    serving_size: float = 100.0    # grams
    serving_unit: str = "g"
    servings: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "macros": self.macros.to_dict(),
            "micros": self.micros.to_dict(),
            "serving_size": self.serving_size,
            "serving_unit": self.serving_unit,
            "servings": self.servings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NutrientProfile":
        return cls(
            macros=MacroNutrients.from_dict(data.get("macros", {})),
            micros=MicroNutrients.from_dict(data.get("micros", {})),
            serving_size=data.get("serving_size", 100.0),
            serving_unit=data.get("serving_unit", "g"),
            servings=data.get("servings", 1.0),
        )
    
    def scale_to_servings(self, servings: float) -> "NutrientProfile":
        """Scale nutrients to a number of servings."""
        scale = servings / self.servings if self.servings > 0 else 0
        
        new_macros = MacroNutrients(
            **{k: v * scale for k, v in self.macros.to_dict().items()}
        )
        new_micros = MicroNutrients(
            **{k: v * scale for k, v in self.micros.to_dict().items()}
        )
        
        return NutrientProfile(
            macros=new_macros,
            micros=new_micros,
            serving_size=self.serving_size,
            serving_unit=self.serving_unit,
            servings=servings,
        )


# =============================================================================
# FOOD ENTRY
# =============================================================================

@dataclass
class FoodEntry:
    """
    A single food item entry.
    
    This is the atomic unit of nutrition tracking.
    Can be detected from image, searched, or manually entered.
    """
    # Identity
    food_id: str = ""                      # Unique ID
    name: str = ""                         # Display name
    description: str = ""                  # Optional description
    
    # Categorization
    category: FoodCategory = FoodCategory.UNKNOWN
    tags: List[str] = field(default_factory=list)
    
    # Nutrition
    nutrients: NutrientProfile = field(default_factory=NutrientProfile)
    
    # Quantity consumed
    quantity: float = 1.0
    quantity_unit: str = "serving"
    
    # Source of data
    source: str = "manual"                 # manual, image, database, barcode
    source_id: Optional[str] = None        # ID from source database
    confidence: float = 1.0                # How confident in this data
    
    # Image reference (if from photo)
    image_url: Optional[str] = None
    
    # Allergens
    allergens: List[AllergenType] = field(default_factory=list)
    
    # Timestamps
    logged_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "food_id": self.food_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "tags": self.tags,
            "nutrients": self.nutrients.to_dict(),
            "quantity": self.quantity,
            "quantity_unit": self.quantity_unit,
            "source": self.source,
            "source_id": self.source_id,
            "confidence": self.confidence,
            "image_url": self.image_url,
            "allergens": [a.value for a in self.allergens],
            "logged_at": self.logged_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FoodEntry":
        return cls(
            food_id=data.get("food_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=FoodCategory(data.get("category", "unknown")),
            tags=data.get("tags", []),
            nutrients=NutrientProfile.from_dict(data.get("nutrients", {})),
            quantity=data.get("quantity", 1.0),
            quantity_unit=data.get("quantity_unit", "serving"),
            source=data.get("source", "manual"),
            source_id=data.get("source_id"),
            confidence=data.get("confidence", 1.0),
            image_url=data.get("image_url"),
            allergens=[AllergenType(a) for a in data.get("allergens", [])],
            logged_at=datetime.fromisoformat(data["logged_at"]) if "logged_at" in data else datetime.now(),
        )
    
    def get_total_nutrients(self) -> NutrientProfile:
        """Get nutrients scaled to quantity consumed."""
        return self.nutrients.scale_to_servings(self.quantity)


# =============================================================================
# MEAL ENTRY
# =============================================================================

@dataclass
class MealEntry:
    """
    A meal containing multiple food items.
    
    Represents a discrete eating occasion.
    """
    # Identity
    meal_id: str = ""
    name: Optional[str] = None             # Optional custom name
    
    # Classification
    meal_type: MealType = MealType.OTHER
    
    # Contents
    foods: List[FoodEntry] = field(default_factory=list)
    
    # Timing
    eaten_at: datetime = field(default_factory=datetime.now)
    duration_minutes: Optional[int] = None
    
    # Context
    location: Optional[str] = None         # home, restaurant, work
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None
    hunger_level: Optional[int] = None     # 1-10
    satisfaction: Optional[int] = None     # 1-10
    
    # Notes
    notes: str = ""
    
    # Image
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "meal_id": self.meal_id,
            "name": self.name,
            "meal_type": self.meal_type.value,
            "foods": [f.to_dict() for f in self.foods],
            "eaten_at": self.eaten_at.isoformat(),
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "mood_before": self.mood_before,
            "mood_after": self.mood_after,
            "hunger_level": self.hunger_level,
            "satisfaction": self.satisfaction,
            "notes": self.notes,
            "image_url": self.image_url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MealEntry":
        return cls(
            meal_id=data.get("meal_id", ""),
            name=data.get("name"),
            meal_type=MealType(data.get("meal_type", "other")),
            foods=[FoodEntry.from_dict(f) for f in data.get("foods", [])],
            eaten_at=datetime.fromisoformat(data["eaten_at"]) if "eaten_at" in data else datetime.now(),
            duration_minutes=data.get("duration_minutes"),
            location=data.get("location"),
            mood_before=data.get("mood_before"),
            mood_after=data.get("mood_after"),
            hunger_level=data.get("hunger_level"),
            satisfaction=data.get("satisfaction"),
            notes=data.get("notes", ""),
            image_url=data.get("image_url"),
        )
    
    def get_total_nutrients(self) -> NutrientProfile:
        """Get combined nutrients for all foods in meal."""
        if not self.foods:
            return NutrientProfile()
        
        total_macros = MacroNutrients()
        for food in self.foods:
            food_nutrients = food.get_total_nutrients()
            total_macros = total_macros + food_nutrients.macros
        
        return NutrientProfile(macros=total_macros)
    
    def get_food_count(self) -> int:
        """Get number of foods in meal."""
        return len(self.foods)
    
    def get_total_calories(self) -> float:
        """Get total calories for meal."""
        return self.get_total_nutrients().macros.calories


# =============================================================================
# DIETARY PREFERENCE
# =============================================================================

@dataclass
class DietaryPreference:
    """
    User's dietary preferences and restrictions.
    
    This is a trait that persists in the Digital Twin.
    """
    # Diet type
    diet_type: DietType = DietType.OMNIVORE
    
    # Allergies and intolerances
    allergies: List[AllergenType] = field(default_factory=list)
    intolerances: List[str] = field(default_factory=list)
    
    # Preferences
    avoid_foods: List[str] = field(default_factory=list)
    preferred_foods: List[str] = field(default_factory=list)
    
    # Goals
    calorie_target: Optional[int] = None
    protein_target: Optional[int] = None    # grams
    carb_target: Optional[int] = None       # grams
    fat_target: Optional[int] = None        # grams
    
    # Eating schedule
    meals_per_day: int = 3
    eating_window_start: Optional[str] = None  # "08:00"
    eating_window_end: Optional[str] = None    # "20:00"
    
    # Other
    vegetable_servings_target: int = 5
    water_glasses_target: int = 8
    
    # Confidence in these settings
    confidence: float = 1.0
    source: str = "stated"                 # stated, detected, calculated
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "diet_type": self.diet_type.value,
            "allergies": [a.value for a in self.allergies],
            "intolerances": self.intolerances,
            "avoid_foods": self.avoid_foods,
            "preferred_foods": self.preferred_foods,
            "calorie_target": self.calorie_target,
            "protein_target": self.protein_target,
            "carb_target": self.carb_target,
            "fat_target": self.fat_target,
            "meals_per_day": self.meals_per_day,
            "eating_window_start": self.eating_window_start,
            "eating_window_end": self.eating_window_end,
            "vegetable_servings_target": self.vegetable_servings_target,
            "water_glasses_target": self.water_glasses_target,
            "confidence": self.confidence,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DietaryPreference":
        return cls(
            diet_type=DietType(data.get("diet_type", "omnivore")),
            allergies=[AllergenType(a) for a in data.get("allergies", [])],
            intolerances=data.get("intolerances", []),
            avoid_foods=data.get("avoid_foods", []),
            preferred_foods=data.get("preferred_foods", []),
            calorie_target=data.get("calorie_target"),
            protein_target=data.get("protein_target"),
            carb_target=data.get("carb_target"),
            fat_target=data.get("fat_target"),
            meals_per_day=data.get("meals_per_day", 3),
            eating_window_start=data.get("eating_window_start"),
            eating_window_end=data.get("eating_window_end"),
            vegetable_servings_target=data.get("vegetable_servings_target", 5),
            water_glasses_target=data.get("water_glasses_target", 8),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "stated"),
        )


# =============================================================================
# NUTRITION SCHEMA (Trait Definitions)
# =============================================================================

class NutritionSchema:
    """
    Schema definitions for all Nutrition domain traits.
    
    This class provides the trait schema that gets registered
    with the domain's DomainSchema.
    """
    
    @staticmethod
    def get_trait_schemas() -> List[Dict[str, Any]]:
        """
        Get all trait schemas for the Nutrition domain.
        
        These define what traits the domain can store.
        """
        return [
            # Dietary preferences
            {
                "name": "dietary_preference",
                "display_name": "Dietary Preference",
                "description": "User's diet type and eating preferences",
                "value_type": "object",
                "category": "preference",
                "is_required": False,
                "priority": 100,
            },
            {
                "name": "allergies",
                "display_name": "Food Allergies",
                "description": "Known food allergies",
                "value_type": "list",
                "category": "health",
                "is_required": False,
                "priority": 95,
            },
            {
                "name": "calorie_target",
                "display_name": "Daily Calorie Target",
                "description": "Target daily calorie intake",
                "value_type": "number",
                "unit": "kcal",
                "category": "goal",
                "is_required": False,
                "priority": 90,
            },
            
            # Detected patterns
            {
                "name": "eating_pattern",
                "display_name": "Eating Pattern",
                "description": "Detected eating habits and patterns",
                "value_type": "string",
                "enum_options": ["regular", "irregular", "grazer", "meal-skipper", "late-eater"],
                "category": "detected",
                "is_required": False,
                "priority": 85,
            },
            {
                "name": "macro_balance",
                "display_name": "Macronutrient Balance",
                "description": "Typical macro ratio pattern",
                "value_type": "string",
                "enum_options": ["balanced", "high-protein", "high-carb", "high-fat", "low-calorie"],
                "category": "detected",
                "is_required": False,
                "priority": 80,
            },
            {
                "name": "food_variety_score",
                "display_name": "Food Variety Score",
                "description": "How varied the diet is (0-100)",
                "value_type": "number",
                "scale_min": 0,
                "scale_max": 100,
                "category": "detected",
                "is_required": False,
                "priority": 75,
            },
            
            # Goals
            {
                "name": "nutrition_goals",
                "display_name": "Nutrition Goals",
                "description": "User's nutrition-related goals",
                "value_type": "list",
                "category": "goal",
                "is_required": False,
                "priority": 88,
            },
            
            # Historical stats
            {
                "name": "avg_daily_calories",
                "display_name": "Average Daily Calories",
                "description": "Rolling average of daily calorie intake",
                "value_type": "number",
                "unit": "kcal",
                "category": "calculated",
                "is_required": False,
                "priority": 70,
            },
            {
                "name": "meal_consistency_score",
                "display_name": "Meal Consistency",
                "description": "How consistent meal timing is (0-100)",
                "value_type": "number",
                "scale_min": 0,
                "scale_max": 100,
                "category": "calculated",
                "is_required": False,
                "priority": 65,
            },
            
            # Food preferences (detected)
            {
                "name": "favorite_foods",
                "display_name": "Favorite Foods",
                "description": "Most frequently consumed foods",
                "value_type": "list",
                "category": "detected",
                "is_required": False,
                "priority": 60,
            },
            {
                "name": "avoided_foods",
                "display_name": "Avoided Foods",
                "description": "Foods that are avoided",
                "value_type": "list",
                "category": "detected",
                "is_required": False,
                "priority": 55,
            },
        ]
