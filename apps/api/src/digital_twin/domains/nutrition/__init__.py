"""
Nutrition Domain - Complete Sub-Domain Implementation

The Nutrition domain is a CORE SUB-DOMAIN under Health that provides:
- Food logging and analysis
- Dietary pattern detection
- Nutritional insights
- Meal planning suggestions
- Food-mood correlations

This is the REFERENCE IMPLEMENTATION demonstrating the fractal
extensibility pattern. Every component is modular and can be
extended infinitely.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────────────────────────────────────────────────┐
    │                    NUTRITION DOMAIN                         │
    │              (Sub-domain of Health)                         │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                   CORE                               │   │
    │  │  • NutritionDomain class                             │   │
    │  │  • Schema definitions                                │   │
    │  │  • Trait management                                  │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
    │  │   FOOD      │ │   MEAL      │ │  DIETARY    │   ...     │
    │  │  ANALYZER   │ │  TRACKER    │ │  PATTERNS   │           │
    │  │             │ │             │ │             │           │
    │  │ • Image AI  │ │ • Logging   │ │ • Detection │           │
    │  │ • Nutrients │ │ • History   │ │ • Trends    │           │
    │  │ • Scoring   │ │ • Stats     │ │ • Insights  │           │
    │  └─────────────┘ └─────────────┘ └─────────────┘           │
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                 INTEGRATIONS                         │   │
    │  │  • Food databases (USDA, OpenFoodFacts)              │   │
    │  │  • Photo analysis (Gemini Vision)                    │   │
    │  │  • Recipe APIs                                       │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Module Structure (Fractal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
nutrition/
├── __init__.py         # Domain registration & exports
├── domain.py           # Main NutritionDomain class
├── schema.py           # Trait schemas & validation
├── analyzer/           # Food analysis sub-module
│   ├── __init__.py
│   ├── image.py        # Image-based food detection
│   ├── nutrients.py    # Nutrient calculation
│   └── scoring.py      # Health scoring
├── tracker/            # Meal tracking sub-module
│   ├── __init__.py
│   ├── meals.py        # Meal CRUD
│   ├── history.py      # Historical analysis
│   └── stats.py        # Statistics
├── patterns/           # Pattern detection sub-module
│   ├── __init__.py
│   ├── detector.py     # Pattern detection
│   ├── trends.py       # Trend analysis
│   └── insights.py     # Insight generation
└── integrations/       # External integrations
    ├── __init__.py
    ├── food_db.py      # Food database clients
    ├── vision.py       # Vision AI integration
    └── recipes.py      # Recipe APIs

@module NutritionDomain
"""

# Re-export all public interfaces
from .domain import (
    NutritionDomain,
    NutritionConfig,
    get_nutrition_domain,
)
from .schema import (
    NutritionSchema,
    FoodEntry,
    MealEntry,
    NutrientProfile,
    DietaryPreference,
)
from .analyzer import (
    FoodAnalyzer,
    NutrientCalculator,
    HealthScorer,
    AnalysisResult,
)
from .tracker import (
    MealTracker,
    MealHistory,
    NutritionStats,
)
from .patterns import (
    PatternDetector,
    TrendAnalyzer,
    InsightGenerator,
    DietaryPattern,
    NutritionInsight,
)

__all__ = [
    # Domain
    "NutritionDomain",
    "NutritionConfig",
    "get_nutrition_domain",
    # Schema
    "NutritionSchema",
    "FoodEntry",
    "MealEntry",
    "NutrientProfile",
    "DietaryPreference",
    # Analyzer
    "FoodAnalyzer",
    "NutrientCalculator",
    "HealthScorer",
    "AnalysisResult",
    # Tracker
    "MealTracker",
    "MealHistory",
    "NutritionStats",
    # Patterns
    "PatternDetector",
    "TrendAnalyzer",
    "InsightGenerator",
    "DietaryPattern",
    "NutritionInsight",
]
