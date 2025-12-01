"""
Health Domain - Container Domain for Health-Related Sub-Domains

The Health domain is a CORE DOMAIN that serves as the container and
coordinator for all health-related sub-domains:
- Nutrition (food, diet, supplements)
- Biometrics (sleep, HRV, etc.)
- Fitness (exercise, activity)
- Medical (conditions, medications)

This domain:
1. Provides the parent namespace for health traits
2. Aggregates data from all health sub-domains
3. Coordinates cross-sub-domain analysis
4. Generates holistic health insights

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────────────────────────────────────────────────┐
    │                      HEALTH DOMAIN                          │
    │                     (Core Container)                        │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
    │  │  NUTRITION  │ │ BIOMETRICS  │ │   FITNESS   │    ...    │
    │  │ (Sub-domain)│ │ (Sub-domain)│ │ (Sub-domain)│           │
    │  └─────────────┘ └─────────────┘ └─────────────┘           │
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │              Health Synthesizer                      │   │
    │  │  • Aggregates sub-domain data                        │   │
    │  │  • Detects cross-domain patterns                     │   │
    │  │  • Generates holistic insights                       │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

This is a SCAFFOLD implementation. Sub-domains (Nutrition, etc.) are
implemented separately and plug in via the registry system.

@module HealthDomain
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .base import BaseDomain, DomainSchema, TraitSchema
from .registry import DomainRegistry
from .core_types import (
    DomainType,
    DomainCapability,
    DomainMetadata,
    DomainDependency,
    CoreDomainId,
    SubDomainConfig,
    DomainEvent,
    DomainEventType,
)
from ..traits import TraitCategory, TraitFramework

logger = logging.getLogger(__name__)


# =============================================================================
# HEALTH DOMAIN SCHEMA
# =============================================================================

@dataclass
class HealthDomainConfig:
    """
    Configuration for the Health domain.
    
    Can be customized per-user or system-wide.
    """
    # Enable/disable sub-domains
    enable_nutrition: bool = True
    enable_biometrics: bool = True
    enable_fitness: bool = True
    enable_medical: bool = False  # Opt-in for medical data
    
    # Synthesis options
    cross_domain_analysis: bool = True
    auto_correlate: bool = True
    
    # Privacy
    share_with_agents: bool = True
    anonymize_exports: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_nutrition": self.enable_nutrition,
            "enable_biometrics": self.enable_biometrics,
            "enable_fitness": self.enable_fitness,
            "enable_medical": self.enable_medical,
            "cross_domain_analysis": self.cross_domain_analysis,
            "auto_correlate": self.auto_correlate,
            "share_with_agents": self.share_with_agents,
            "anonymize_exports": self.anonymize_exports,
        }


# =============================================================================
# HEALTH DOMAIN IMPLEMENTATION (SCAFFOLD)
# =============================================================================

@DomainRegistry.register
class HealthDomain(BaseDomain):
    """
    Health Domain - Container for all health-related sub-domains.
    
    This is a CORE DOMAIN that:
    1. Cannot be disabled
    2. Provides namespace for health traits
    3. Aggregates sub-domain data
    4. Coordinates health synthesis
    
    SCAFFOLD STATUS:
    ✅ Domain registration and metadata
    ✅ Schema definitions
    ✅ Sub-domain coordination hooks
    ⬜ Cross-domain synthesis (pending Nutrition implementation)
    ⬜ Health insights generation
    ⬜ External API integration (Apple Health, etc.)
    """
    
    # -------------------------------------------------------------------------
    # Domain Identity
    # -------------------------------------------------------------------------
    
    domain_id = CoreDomainId.HEALTH
    display_name = "Health"
    description = "Container for all health-related tracking and insights"
    icon = "💚"
    version = "1.0.0"
    priority = 80  # High priority, core domain
    
    # Classification
    domain_type = DomainType.CORE
    is_core = True
    
    # Capabilities this container provides
    capabilities = {
        DomainCapability.READ_TRAITS,
        DomainCapability.WRITE_TRAITS,
        DomainCapability.DETECT_PATTERNS,
        DomainCapability.GENERATE_INSIGHTS,
        DomainCapability.SYNTHESIZE,
    }
    
    # Dependencies (Genesis for user profile)
    dependencies = [
        DomainDependency(
            domain_id=CoreDomainId.GENESIS,
            dependency_type="optional",
            reason="User profile for personalization"
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self._config = HealthDomainConfig()
        self._sub_domains: Dict[str, BaseDomain] = {}
        self._event_handlers: Dict[str, List] = {}
        
    # -------------------------------------------------------------------------
    # Schema Definition
    # -------------------------------------------------------------------------
    
    def get_schema(self) -> DomainSchema:
        """
        Return the schema for the Health domain.
        
        The Health domain itself has few direct traits - most traits
        live in sub-domains. These are aggregate/summary traits.
        """
        schema = DomainSchema(domain_id=self.domain_id)
        
        # Health summary traits (aggregated from sub-domains)
        schema.add_trait(TraitSchema(
            name="overall_wellness_score",
            display_name="Overall Wellness Score",
            description="Aggregated wellness score from all health sub-domains",
            value_type="scale",
            scale_min=0.0,
            scale_max=100.0,
            category=TraitCategory.HEALTH,
            is_required=False,
            priority=100,
        ))
        
        schema.add_trait(TraitSchema(
            name="health_focus_areas",
            display_name="Health Focus Areas",
            description="Areas identified for health improvement",
            value_type="list",
            category=TraitCategory.HEALTH,
            priority=90,
        ))
        
        schema.add_trait(TraitSchema(
            name="health_goals",
            display_name="Health Goals",
            description="User's stated health goals",
            value_type="list",
            category=TraitCategory.GOAL,
            priority=85,
        ))
        
        schema.add_trait(TraitSchema(
            name="dietary_restrictions",
            display_name="Dietary Restrictions",
            description="Allergies, intolerances, preferences",
            value_type="list",
            category=TraitCategory.PREFERENCE,
            priority=80,
        ))
        
        schema.add_trait(TraitSchema(
            name="health_conditions",
            display_name="Health Conditions",
            description="Known health conditions (if shared)",
            value_type="list",
            category=TraitCategory.HEALTH,
            priority=75,
        ))
        
        schema.add_trait(TraitSchema(
            name="energy_baseline",
            display_name="Energy Baseline",
            description="Typical energy level throughout day",
            value_type="enum",
            enum_options=["low", "moderate", "high", "variable"],
            category=TraitCategory.ENERGY,
            priority=70,
        ))
        
        return schema
    
    # -------------------------------------------------------------------------
    # Sub-Domain Management
    # -------------------------------------------------------------------------
    
    def register_sub_domain(self, sub_domain: BaseDomain) -> bool:
        """
        Register a sub-domain under Health.
        
        Sub-domains call this during their initialization to register
        with their parent container.
        """
        domain_id = sub_domain.domain_id
        
        # Verify it's a valid health sub-domain
        valid_sub_domains = ["nutrition", "biometrics", "fitness", "sleep", "medical"]
        if domain_id not in valid_sub_domains:
            logger.warning(f"[HealthDomain] Unknown sub-domain: {domain_id}")
            return False
        
        self._sub_domains[domain_id] = sub_domain
        logger.info(f"[HealthDomain] Registered sub-domain: {domain_id}")
        
        # Emit event
        self._emit_event(DomainEventType.DOMAIN_INITIALIZED, {
            "sub_domain_id": domain_id,
            "parent": self.domain_id,
        })
        
        return True
    
    def get_sub_domain(self, domain_id: str) -> Optional[BaseDomain]:
        """Get a registered sub-domain by ID."""
        return self._sub_domains.get(domain_id)
    
    def list_sub_domains(self) -> List[str]:
        """List all registered sub-domain IDs."""
        return list(self._sub_domains.keys())
    
    def is_sub_domain_enabled(self, domain_id: str) -> bool:
        """Check if a sub-domain is enabled in config."""
        config_map = {
            "nutrition": self._config.enable_nutrition,
            "biometrics": self._config.enable_biometrics,
            "fitness": self._config.enable_fitness,
            "medical": self._config.enable_medical,
        }
        return config_map.get(domain_id, False)
    
    # -------------------------------------------------------------------------
    # Cross-Domain Aggregation (SCAFFOLD)
    # -------------------------------------------------------------------------
    
    def aggregate_from_sub_domains(self) -> Dict[str, Any]:
        """
        Aggregate data from all sub-domains.
        
        SCAFFOLD: Returns basic structure. Full implementation
        will pull and synthesize data from each sub-domain.
        """
        aggregation = {
            "sub_domains": {},
            "summary": {},
            "correlations": [],
            "insights": [],
        }
        
        for domain_id, sub_domain in self._sub_domains.items():
            try:
                summary = sub_domain.get_summary()
                aggregation["sub_domains"][domain_id] = summary
            except Exception as e:
                logger.error(f"[HealthDomain] Error aggregating {domain_id}: {e}")
                aggregation["sub_domains"][domain_id] = {"error": str(e)}
        
        return aggregation
    
    def calculate_wellness_score(self) -> float:
        """
        Calculate overall wellness score from sub-domains.
        
        SCAFFOLD: Returns placeholder. Real implementation will
        use weighted algorithm across sub-domain metrics.
        """
        # Placeholder - will be implemented with Nutrition
        return 0.0
    
    # -------------------------------------------------------------------------
    # Health Synthesis (SCAFFOLD)
    # -------------------------------------------------------------------------
    
    async def synthesize_health_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights by analyzing across health sub-domains.
        
        SCAFFOLD: Returns empty list. Will be implemented when
        sub-domains have enough data.
        """
        insights = []
        
        # TODO: Implement cross-domain pattern detection
        # - Sleep + Nutrition correlations
        # - Energy + Activity patterns
        # - Diet + Biometric trends
        
        return insights
    
    # -------------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------------
    
    def _emit_event(self, event_type: DomainEventType, data: Dict[str, Any]):
        """Emit a domain event."""
        event = DomainEvent(
            event_type=event_type,
            domain_id=self.domain_id,
            data=data,
            source="health_domain",
        )
        
        # Call registered handlers
        handlers = self._event_handlers.get(event_type.value, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"[HealthDomain] Event handler error: {e}")
    
    def subscribe_to_event(
        self, 
        event_type: DomainEventType, 
        handler
    ) -> None:
        """Subscribe to domain events."""
        key = event_type.value
        if key not in self._event_handlers:
            self._event_handlers[key] = []
        self._event_handlers[key].append(handler)
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    def get_config(self) -> HealthDomainConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, **kwargs) -> HealthDomainConfig:
        """Update configuration."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self._config
    
    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------
    
    def get_metadata(self) -> DomainMetadata:
        """Get domain metadata."""
        return DomainMetadata(
            domain_id=self.domain_id,
            display_name=self.display_name,
            description=self.description,
            domain_type=DomainType.CORE,
            icon=self.icon,
            version=self.version,
            priority=self.priority,
            capabilities=self.capabilities,
            dependencies=self.dependencies,
            sub_domain_ids=list(self._sub_domains.keys()),
            is_core=True,
        )
    
    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert domain state to dictionary."""
        base = super().to_dict()
        base.update({
            "config": self._config.to_dict(),
            "sub_domains": self.list_sub_domains(),
            "sub_domain_count": len(self._sub_domains),
            "wellness_score": self.calculate_wellness_score(),
        })
        return base


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_health_domain_instance: Optional[HealthDomain] = None


async def get_health_domain() -> HealthDomain:
    """Get the Health domain instance."""
    global _health_domain_instance
    if _health_domain_instance is None:
        registry = DomainRegistry.get(CoreDomainId.HEALTH)
        if registry:
            _health_domain_instance = registry
        else:
            _health_domain_instance = HealthDomain()
            _health_domain_instance.initialize()
    return _health_domain_instance
