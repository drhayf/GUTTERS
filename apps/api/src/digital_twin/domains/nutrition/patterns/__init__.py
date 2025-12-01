"""
Pattern Detection and Insights Sub-Module

Detects dietary patterns and generates insights:
- Pattern detection (eating habits, preferences)
- Trend analysis
- Insight generation

Architecture (Fractal):
━━━━━━━━━━━━━━━━━━━━━━━━━
patterns/
├── __init__.py      # Exports
├── detector.py      # Pattern detection
├── trends.py        # Trend analysis
└── insights.py      # Insight generation

@module NutritionPatterns
"""

from .detector import (
    PatternDetector,
    DietaryPattern,
    detect_patterns,
)
from .trends import (
    TrendAnalyzer,
    NutritionTrend,
    analyze_trends,
)
from .insights import (
    InsightGenerator,
    NutritionInsight,
    generate_insights,
)

__all__ = [
    "PatternDetector",
    "DietaryPattern",
    "detect_patterns",
    "TrendAnalyzer",
    "NutritionTrend",
    "analyze_trends",
    "InsightGenerator",
    "NutritionInsight",
    "generate_insights",
]
