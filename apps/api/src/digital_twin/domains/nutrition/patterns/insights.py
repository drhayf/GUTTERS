"""
Insight Generation

Generates actionable insights from nutrition data.

Uses detected patterns, trends, and goals to create
personalized recommendations.

@module InsightGenerator
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .detector import PatternDetector, DietaryPattern, PatternType
from .trends import TrendAnalyzer, NutritionTrend, TrendDirection
from ..schema import DietaryPreference

logger = logging.getLogger(__name__)


# =============================================================================
# INSIGHT TYPES
# =============================================================================

class InsightCategory(str, Enum):
    """Categories of insights."""
    ACHIEVEMENT = "achievement"      # Positive accomplishment
    RECOMMENDATION = "recommendation"  # Suggested improvement
    WARNING = "warning"              # Potential concern
    OBSERVATION = "observation"      # Neutral observation
    GOAL_PROGRESS = "goal_progress"  # Progress toward goals


class InsightPriority(str, Enum):
    """Priority level of insights."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NutritionInsight:
    """A nutrition insight or recommendation."""
    category: InsightCategory
    priority: InsightPriority
    title: str
    description: str
    
    # Action to take
    action: Optional[str] = None
    
    # Source of insight
    source_pattern: Optional[str] = None
    source_trend: Optional[str] = None
    
    # Icon for UI
    icon: str = "💡"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "source_pattern": self.source_pattern,
            "source_trend": self.source_trend,
            "icon": self.icon,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# INSIGHT GENERATOR
# =============================================================================

class InsightGenerator:
    """
    Generates nutrition insights from patterns and trends.
    
    Combines:
    - Detected patterns
    - Trend analysis
    - User goals and preferences
    
    To produce actionable, personalized insights.
    """
    
    def __init__(
        self,
        preferences: Optional[DietaryPreference] = None
    ):
        self._preferences = preferences
        self._pattern_detector = PatternDetector()
        self._trend_analyzer = TrendAnalyzer()
    
    async def generate_insights(
        self,
        days: int = 30,
        max_insights: int = 5
    ) -> List[NutritionInsight]:
        """
        Generate insights from recent nutrition data.
        
        Returns up to `max_insights` insights, prioritized by importance.
        """
        insights = []
        
        # Get patterns and trends
        patterns = await self._pattern_detector.detect_all_patterns(days)
        trends = await self._trend_analyzer.analyze_all_trends()
        
        # Generate insights from patterns
        for pattern in patterns:
            insight = self._insight_from_pattern(pattern)
            if insight:
                insights.append(insight)
        
        # Generate insights from trends
        for trend in trends:
            insight = self._insight_from_trend(trend)
            if insight:
                insights.append(insight)
        
        # Add goal-based insights
        if self._preferences:
            goal_insights = self._generate_goal_insights()
            insights.extend(goal_insights)
        
        # Sort by priority and limit
        priority_order = {
            InsightPriority.HIGH: 0,
            InsightPriority.MEDIUM: 1,
            InsightPriority.LOW: 2,
        }
        insights.sort(key=lambda i: priority_order[i.priority])
        
        return insights[:max_insights]
    
    def _insight_from_pattern(
        self,
        pattern: DietaryPattern
    ) -> Optional[NutritionInsight]:
        """Generate insight from a detected pattern."""
        
        # Eating schedule patterns
        if pattern.pattern_type == PatternType.EATING_SCHEDULE:
            if pattern.name == "Meal Skipper":
                return NutritionInsight(
                    category=InsightCategory.WARNING,
                    priority=InsightPriority.HIGH,
                    title="Irregular Eating Pattern",
                    description=pattern.description,
                    action="Try to eat at least 3 meals per day for better energy.",
                    source_pattern=pattern.pattern_type.value,
                    icon="⚠️",
                )
            elif pattern.name == "Regular Eater":
                return NutritionInsight(
                    category=InsightCategory.ACHIEVEMENT,
                    priority=InsightPriority.LOW,
                    title="Consistent Eating Schedule",
                    description="You maintain a regular eating pattern.",
                    source_pattern=pattern.pattern_type.value,
                    icon="✅",
                )
        
        # Macro balance patterns
        elif pattern.pattern_type == PatternType.MACRO_BALANCE:
            if pattern.name == "Low Calorie":
                return NutritionInsight(
                    category=InsightCategory.WARNING,
                    priority=InsightPriority.MEDIUM,
                    title="Low Calorie Intake",
                    description=pattern.description,
                    action="Ensure you're eating enough to meet your energy needs.",
                    source_pattern=pattern.pattern_type.value,
                    icon="📉",
                )
            elif pattern.name == "Balanced":
                return NutritionInsight(
                    category=InsightCategory.ACHIEVEMENT,
                    priority=InsightPriority.LOW,
                    title="Balanced Macros",
                    description="Your macronutrient balance is well-proportioned.",
                    source_pattern=pattern.pattern_type.value,
                    icon="⚖️",
                )
        
        # Variety patterns
        elif pattern.pattern_type == PatternType.VARIETY:
            if pattern.name == "Repetitive Diet":
                return NutritionInsight(
                    category=InsightCategory.RECOMMENDATION,
                    priority=InsightPriority.MEDIUM,
                    title="Limited Food Variety",
                    description=pattern.description,
                    action="Try introducing new foods to improve nutrient diversity.",
                    source_pattern=pattern.pattern_type.value,
                    icon="🔄",
                )
            elif pattern.name == "Varied Diet":
                return NutritionInsight(
                    category=InsightCategory.ACHIEVEMENT,
                    priority=InsightPriority.LOW,
                    title="Great Food Variety",
                    description="You eat a diverse range of foods.",
                    source_pattern=pattern.pattern_type.value,
                    icon="🌈",
                )
        
        return None
    
    def _insight_from_trend(
        self,
        trend: NutritionTrend
    ) -> Optional[NutritionInsight]:
        """Generate insight from a detected trend."""
        
        if trend.direction == TrendDirection.STABLE:
            return None  # No insight for stable trends
        
        # Significant calorie changes
        if trend.trend_type.value == "calorie":
            if trend.direction == TrendDirection.INCREASING and trend.magnitude > 15:
                return NutritionInsight(
                    category=InsightCategory.OBSERVATION,
                    priority=InsightPriority.MEDIUM,
                    title="Calorie Intake Increasing",
                    description=trend.description,
                    action="Check if this aligns with your goals.",
                    source_trend=trend.trend_type.value,
                    icon="📈",
                )
            elif trend.direction == TrendDirection.DECREASING and trend.magnitude > 15:
                return NutritionInsight(
                    category=InsightCategory.OBSERVATION,
                    priority=InsightPriority.MEDIUM,
                    title="Calorie Intake Decreasing",
                    description=trend.description,
                    source_trend=trend.trend_type.value,
                    icon="📉",
                )
        
        # Protein trends
        elif trend.trend_type.value == "protein":
            if trend.direction == TrendDirection.INCREASING:
                return NutritionInsight(
                    category=InsightCategory.ACHIEVEMENT,
                    priority=InsightPriority.LOW,
                    title="Protein Intake Improving",
                    description=trend.description,
                    source_trend=trend.trend_type.value,
                    icon="💪",
                )
        
        return None
    
    def _generate_goal_insights(self) -> List[NutritionInsight]:
        """Generate insights based on user goals."""
        insights = []
        
        if not self._preferences:
            return insights
        
        # Check calorie target
        if self._preferences.calorie_target:
            insights.append(NutritionInsight(
                category=InsightCategory.GOAL_PROGRESS,
                priority=InsightPriority.LOW,
                title="Calorie Goal Set",
                description=f"Your daily target is {self._preferences.calorie_target} calories.",
                icon="🎯",
            ))
        
        return insights


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def generate_insights(
    preferences: Optional[DietaryPreference] = None,
    days: int = 30,
    max_insights: int = 5
) -> List[NutritionInsight]:
    """Convenience function to generate insights."""
    generator = InsightGenerator(preferences)
    return await generator.generate_insights(days, max_insights)
