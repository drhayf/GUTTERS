"""
Nutrition Domain - Main Domain Implementation

The Nutrition domain is a SUB-DOMAIN under Health that provides
complete nutrition tracking and analysis capabilities.

This is the REFERENCE IMPLEMENTATION for the fractal domain pattern.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    NutritionDomain
    ├── FoodAnalyzer        (analyzer/)
    │   ├── ImageFoodAnalyzer
    │   ├── NutrientCalculator
    │   └── HealthScorer
    ├── MealTracker         (tracker/)
    │   ├── Meals CRUD
    │   ├── History
    │   └── Stats
    ├── PatternDetector     (patterns/)
    │   ├── Detector
    │   ├── Trends
    │   └── Insights
    └── Integration         (SwarmBus, Events, Digital Twin)

@module NutritionDomain
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..base import BaseDomain, DomainSchema, TraitSchema
from ..registry import DomainRegistry
from ..core_types import (
    DomainType,
    DomainCapability,
    DomainMetadata,
    DomainDependency,
    SubDomainConfig,
    CoreDomainId,
    OptionalDomainId,
)
from ...traits import TraitCategory, TraitFramework

from .schema import (
    FoodEntry,
    MealEntry,
    NutrientProfile,
    DietaryPreference,
    NutritionSchema,
)

logger = logging.getLogger(__name__)


# =============================================================================
# NUTRITION CONFIG
# =============================================================================

@dataclass
class NutritionConfig:
    """
    Configuration for the Nutrition domain.
    """
    # Feature toggles
    enable_image_analysis: bool = True
    enable_pattern_detection: bool = True
    enable_trend_analysis: bool = True
    enable_insights: bool = True
    
    # Tracking settings
    auto_log_photos: bool = False
    remind_to_log: bool = True
    reminder_times: List[str] = field(default_factory=lambda: ["12:00", "19:00"])
    
    # Analysis settings
    pattern_detection_days: int = 30
    trend_analysis_days: int = 14
    
    # Goals
    calorie_target: Optional[int] = None
    protein_target: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_image_analysis": self.enable_image_analysis,
            "enable_pattern_detection": self.enable_pattern_detection,
            "enable_trend_analysis": self.enable_trend_analysis,
            "enable_insights": self.enable_insights,
            "auto_log_photos": self.auto_log_photos,
            "remind_to_log": self.remind_to_log,
            "reminder_times": self.reminder_times,
            "pattern_detection_days": self.pattern_detection_days,
            "trend_analysis_days": self.trend_analysis_days,
            "calorie_target": self.calorie_target,
            "protein_target": self.protein_target,
        }


# =============================================================================
# NUTRITION DOMAIN
# =============================================================================

@DomainRegistry.register
class NutritionDomain(BaseDomain):
    """
    Nutrition Domain - Complete nutrition tracking and analysis.
    
    This is a SUB-DOMAIN under Health that provides:
    - Food logging (manual, image, barcode)
    - Meal tracking and history
    - Nutrient calculation
    - Pattern detection
    - Trend analysis
    - Personalized insights
    
    The domain integrates with:
    - Digital Twin (for trait storage)
    - SwarmBus (for inter-agent communication)
    - Health Domain (parent container)
    - Genesis (for user profile context)
    """
    
    # -------------------------------------------------------------------------
    # Domain Identity
    # -------------------------------------------------------------------------
    
    domain_id = OptionalDomainId.NUTRITION
    display_name = "Nutrition"
    description = "Track meals, analyze nutrients, and get personalized insights"
    icon = "🥗"
    version = "1.0.0"
    priority = 75  # High priority sub-domain
    
    # Classification
    domain_type = DomainType.SUB
    
    # Parent relationship
    sub_domain_config = SubDomainConfig(
        parent_domain_id=CoreDomainId.HEALTH,
        trait_prefix="nutrition_",
        inherits_capabilities=True,
        inherits_permissions=True,
        visible_to_parent=True,
        auto_initialize=True,
        shared_event_bus=True,
    )
    
    # Capabilities
    capabilities = {
        DomainCapability.READ_TRAITS,
        DomainCapability.WRITE_TRAITS,
        DomainCapability.PROCESS_IMAGES,
        DomainCapability.DETECT_PATTERNS,
        DomainCapability.GENERATE_INSIGHTS,
        DomainCapability.CALCULATE,
        DomainCapability.RECOMMEND,
    }
    
    # Dependencies
    dependencies = [
        DomainDependency(
            domain_id=CoreDomainId.HEALTH,
            dependency_type="required",
            reason="Parent container domain"
        ),
        DomainDependency(
            domain_id=CoreDomainId.GENESIS,
            dependency_type="optional",
            reason="User profile for personalization"
        ),
    ]
    
    # Frameworks
    frameworks = [TraitFramework.HEALTH_METRICS]
    
    def __init__(self):
        super().__init__()
        self._config = NutritionConfig()
        self._preferences: Optional[DietaryPreference] = None
        
        # Sub-module instances (lazy-loaded)
        self._analyzer = None
        self._tracker = None
        self._pattern_detector = None
        self._trend_analyzer = None
        self._insight_generator = None
    
    # -------------------------------------------------------------------------
    # Schema Definition
    # -------------------------------------------------------------------------
    
    def get_schema(self) -> DomainSchema:
        """
        Return the schema for the Nutrition domain.
        """
        schema = DomainSchema(domain_id=self.domain_id)
        
        # Add all nutrition trait schemas
        for trait_def in NutritionSchema.get_trait_schemas():
            schema.add_trait(TraitSchema(
                name=trait_def["name"],
                display_name=trait_def["display_name"],
                description=trait_def.get("description", ""),
                value_type=trait_def.get("value_type", "string"),
                category=TraitCategory(trait_def.get("category", "health")),
                is_required=trait_def.get("is_required", False),
                priority=trait_def.get("priority", 50),
            ))
        
        return schema
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def initialize(self) -> None:
        """Initialize the Nutrition domain."""
        super().initialize()
        
        # Register with parent Health domain
        self._register_with_parent()
        
        logger.info(f"[NutritionDomain] Initialized v{self.version}")
    
    def _register_with_parent(self) -> None:
        """Register with the Health parent domain."""
        try:
            from ..health import HealthDomain
            import asyncio
            
            async def _register():
                # Health domain registration will happen through the domain registry
                # This is a placeholder for future parent-child wiring
                pass
            
            # Try to register (may fail if Health not initialized yet)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(_register())
                else:
                    loop.run_until_complete(_register())
            except RuntimeError:
                # Event loop not available, will register later
                pass
                
        except ImportError:
            logger.warning("[NutritionDomain] Health domain not available")
    
    # -------------------------------------------------------------------------
    # Sub-Module Access (Lazy Loading)
    # -------------------------------------------------------------------------
    
    @property
    def analyzer(self):
        """Get the food analyzer."""
        if self._analyzer is None:
            from .analyzer import FoodAnalyzer
            self._analyzer = FoodAnalyzer()
        return self._analyzer
    
    @property
    def tracker(self):
        """Get the meal tracker."""
        if self._tracker is None:
            from .tracker import MealTracker
            self._tracker = MealTracker()
        return self._tracker
    
    @property
    def pattern_detector(self):
        """Get the pattern detector."""
        if self._pattern_detector is None:
            from .patterns import PatternDetector
            self._pattern_detector = PatternDetector()
        return self._pattern_detector
    
    @property
    def trend_analyzer(self):
        """Get the trend analyzer."""
        if self._trend_analyzer is None:
            from .patterns import TrendAnalyzer
            self._trend_analyzer = TrendAnalyzer()
        return self._trend_analyzer
    
    @property
    def insight_generator(self):
        """Get the insight generator."""
        if self._insight_generator is None:
            from .patterns import InsightGenerator
            self._insight_generator = InsightGenerator(self._preferences)
        return self._insight_generator
    
    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------
    
    async def analyze_food_image(
        self,
        image_data: bytes,
        image_type: str = "jpeg"
    ):
        """
        Analyze food from an image.
        
        Uses Gemini Vision to detect foods and calculate nutrients.
        """
        if not self._config.enable_image_analysis:
            raise ValueError("Image analysis is disabled")
        
        result = await self.analyzer.analyze_from_image(image_data, image_type)
        
        # Emit event if successful
        if result.success and result.foods:
            await self._emit_food_detected_event(result.foods)
        
        return result
    
    async def log_meal(
        self,
        foods: List[FoodEntry],
        meal_type: str = "other",
        **kwargs
    ) -> MealEntry:
        """
        Log a meal with foods.
        """
        from .schema import MealType
        
        mt = MealType(meal_type) if isinstance(meal_type, str) else meal_type
        meal = await self.tracker.add_meal(foods, mt, **kwargs)
        
        # Record to Digital Twin
        await self._record_meal_to_twin(meal)
        
        return meal
    
    async def get_today_meals(self) -> List[MealEntry]:
        """Get all meals from today."""
        return await self.tracker.get_today_meals()
    
    async def detect_patterns(self) -> List:
        """Detect dietary patterns."""
        if not self._config.enable_pattern_detection:
            return []
        
        patterns = await self.pattern_detector.detect_all_patterns(
            days=self._config.pattern_detection_days
        )
        
        # Update traits based on patterns
        for pattern in patterns:
            await self._update_trait_from_pattern(pattern)
        
        return patterns
    
    async def analyze_trends(self) -> List:
        """Analyze nutrition trends."""
        if not self._config.enable_trend_analysis:
            return []
        
        return await self.trend_analyzer.analyze_all_trends(
            recent_days=self._config.trend_analysis_days // 2,
            compare_days=self._config.trend_analysis_days // 2
        )
    
    async def generate_insights(self, max_insights: int = 5) -> List:
        """Generate personalized nutrition insights."""
        if not self._config.enable_insights:
            return []
        
        return await self.insight_generator.generate_insights(
            days=self._config.pattern_detection_days,
            max_insights=max_insights
        )
    
    async def get_daily_summary(self, date=None) -> Dict[str, Any]:
        """Get nutrition summary for a day."""
        from datetime import date as date_type
        from .tracker.stats import get_daily_stats
        
        target_date = date or date_type.today()
        stats = get_daily_stats(target_date, self._config.calorie_target)
        
        return {
            "date": target_date.isoformat(),
            "stats": stats.to_dict(),
            "meals": [m.to_dict() for m in await self.tracker.get_today_meals()],
        }
    
    # -------------------------------------------------------------------------
    # Digital Twin Integration
    # -------------------------------------------------------------------------
    
    async def _record_meal_to_twin(self, meal: MealEntry) -> None:
        """Record meal to Digital Twin."""
        try:
            from ... import get_digital_twin_core
            
            twin = await get_digital_twin_core()
            await twin.set(
                path=f"nutrition.meals.{meal.meal_id}",
                value=meal.to_dict(),
                source="nutrition_domain",
                confidence=1.0,
            )
        except Exception as e:
            logger.error(f"[NutritionDomain] Failed to record meal: {e}")
    
    async def _update_trait_from_pattern(self, pattern) -> None:
        """Update Digital Twin traits from detected pattern."""
        try:
            from ... import get_digital_twin_core
            from .patterns.detector import PatternType
            
            twin = await get_digital_twin_core()
            
            # Map patterns to traits
            if pattern.pattern_type == PatternType.EATING_SCHEDULE:
                await twin.set(
                    path="nutrition.eating_pattern",
                    value=pattern.name.lower().replace(" ", "_"),
                    source="pattern_detector",
                    confidence=pattern.confidence,
                )
            elif pattern.pattern_type == PatternType.MACRO_BALANCE:
                await twin.set(
                    path="nutrition.macro_balance",
                    value=pattern.name.lower().replace(" ", "_"),
                    source="pattern_detector",
                    confidence=pattern.confidence,
                )
                
        except Exception as e:
            logger.error(f"[NutritionDomain] Failed to update trait: {e}")
    
    async def _emit_food_detected_event(self, foods: List[FoodEntry]) -> None:
        """Emit event when foods are detected."""
        try:
            from ...events import get_event_bus, EventType
            
            bus = await get_event_bus()
            await bus.emit(
                event_type=EventType.TRAIT_ADDED,
                data={
                    "domain": self.domain_id,
                    "foods": [f.to_dict() for f in foods],
                    "count": len(foods),
                },
                source="nutrition_domain",
            )
        except Exception as e:
            logger.debug(f"[NutritionDomain] Event bus not available: {e}")
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    def get_config(self) -> NutritionConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, **kwargs) -> NutritionConfig:
        """Update configuration."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self._config
    
    def set_preferences(self, preferences: DietaryPreference) -> None:
        """Set user dietary preferences."""
        self._preferences = preferences
        
        # Update config from preferences
        if preferences.calorie_target:
            self._config.calorie_target = preferences.calorie_target
        if preferences.protein_target:
            self._config.protein_target = preferences.protein_target
    
    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------
    
    def get_metadata(self) -> DomainMetadata:
        """Get domain metadata."""
        return DomainMetadata(
            domain_id=self.domain_id,
            display_name=self.display_name,
            description=self.description,
            domain_type=DomainType.SUB,
            icon=self.icon,
            version=self.version,
            priority=self.priority,
            capabilities=self.capabilities,
            dependencies=self.dependencies,
            sub_domain_config=self.sub_domain_config,
            is_core=False,
            category="health",
            tags=["nutrition", "food", "diet", "health"],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert domain state to dictionary."""
        base = super().to_dict()
        base.update({
            "config": self._config.to_dict(),
            "preferences": self._preferences.to_dict() if self._preferences else None,
            "parent_domain": self.sub_domain_config.parent_domain_id,
        })
        return base


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_nutrition_domain_instance: Optional[NutritionDomain] = None


async def get_nutrition_domain() -> NutritionDomain:
    """Get the Nutrition domain instance."""
    global _nutrition_domain_instance
    if _nutrition_domain_instance is None:
        registry = DomainRegistry.get(OptionalDomainId.NUTRITION)
        if registry:
            _nutrition_domain_instance = registry
        else:
            _nutrition_domain_instance = NutritionDomain()
            _nutrition_domain_instance.initialize()
    return _nutrition_domain_instance
