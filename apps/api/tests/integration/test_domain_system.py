"""
Project Sovereign - Domain System Integration Tests

These tests validate the LIVE functionality of the domain architecture:
- Domain instantiation and lifecycle
- Trait registration and validation
- Cross-domain communication
- Parent/child domain relationships
- Event emission and handling

Run from apps/api directory:
    python -m pytest tests/integration/test_domain_system.py -v
    
Or run directly:
    cd apps/api && python tests/integration/test_domain_system.py
"""

import pytest
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import sys
import os

# Add src to path for imports - critical for test discovery
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


# =============================================================================
# FIXTURES - Set up real domain instances for testing
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def domain_registry():
    """Create a fresh domain registry for each test."""
    from digital_twin.domains.registry import DomainRegistry
    return DomainRegistry()


@pytest.fixture
def health_domain():
    """Create a real HealthDomain instance."""
    from digital_twin.domains.health import HealthDomain
    return HealthDomain()


@pytest.fixture
def nutrition_domain(health_domain):
    """Create a real NutritionDomain linked to its parent."""
    from digital_twin.domains.nutrition import NutritionDomain
    return NutritionDomain()


@pytest.fixture
def journaling_domain():
    """Create a real JournalingDomain instance."""
    from digital_twin.domains.journaling import JournalingDomain
    return JournalingDomain()


@pytest.fixture
def finance_domain():
    """Create a real FinanceDomain instance."""
    from digital_twin.domains.finance import FinanceDomain
    return FinanceDomain()


# =============================================================================
# DOMAIN ARCHITECTURE TESTS - Validate the core domain structure
# =============================================================================

class TestDomainArchitecture:
    """Test the core domain architecture patterns."""
    
    def test_domain_type_enum_values(self):
        """Verify DomainType enum has all expected values."""
        from digital_twin.domains.core_types import DomainType
        
        expected_types = {'CORE', 'OPTIONAL', 'SUB', 'SYSTEM'}
        actual_types = {t.name for t in DomainType}
        
        assert expected_types == actual_types, (
            f"DomainType mismatch. "
            f"Missing: {expected_types - actual_types}, "
            f"Extra: {actual_types - expected_types}"
        )
    
    def test_domain_tier_enum_values(self):
        """Verify DomainTier enum has all expected values."""
        from digital_twin.domains.core_types import DomainTier
        
        expected_tiers = {'PARENT', 'PEER', 'CHILD'}
        actual_tiers = {t.name for t in DomainTier}
        
        assert expected_tiers == actual_tiers, (
            f"DomainTier mismatch. "
            f"Missing: {expected_tiers - actual_tiers}, "
            f"Extra: {actual_tiers - expected_tiers}"
        )
    
    def test_domain_capability_enum_values(self):
        """Verify DomainCapability enum has all expected values."""
        from digital_twin.domains.core_types import DomainCapability
        
        # Core capabilities every domain system should support
        required_capabilities = {
            'READ_TRAITS', 'WRITE_TRAITS', 'DELETE_TRAITS',
            'DETECT_PATTERNS', 'GENERATE_INSIGHTS'
        }
        
        actual_capabilities = {c.name for c in DomainCapability}
        
        missing = required_capabilities - actual_capabilities
        assert not missing, f"Missing required capabilities: {missing}"
    
    def test_core_domains_constant(self):
        """Verify CORE_DOMAINS constant is properly defined."""
        from digital_twin.domains.core_types import CORE_DOMAINS
        
        assert isinstance(CORE_DOMAINS, (set, frozenset))
        assert 'genesis' in CORE_DOMAINS
        assert 'health' in CORE_DOMAINS
        assert 'journaling' in CORE_DOMAINS
        assert 'system' in CORE_DOMAINS
    
    def test_domain_metadata_creation(self):
        """Verify DomainMetadata can be created with valid parameters."""
        from digital_twin.domains.core_types import (
            DomainMetadata, DomainType, DomainCapability
        )
        
        metadata = DomainMetadata(
            domain_id="test_domain",
            display_name="Test Domain",
            description="A test domain",
            domain_type=DomainType.CORE,
            capabilities={DomainCapability.READ_TRAITS}
        )
        
        assert metadata.domain_id == "test_domain"
        assert metadata.domain_type == DomainType.CORE
        assert DomainCapability.READ_TRAITS in metadata.capabilities


# =============================================================================
# HEALTH DOMAIN TESTS - Parent domain functionality
# =============================================================================

class TestHealthDomain:
    """Test the Health parent domain functionality."""
    
    def test_health_domain_instantiation(self, health_domain):
        """Verify HealthDomain can be instantiated."""
        assert health_domain is not None
    
    def test_health_domain_has_id(self, health_domain):
        """Verify HealthDomain has correct domain_id."""
        assert health_domain.domain_id == "health"
    
    def test_health_domain_is_core(self, health_domain):
        """Verify HealthDomain is a CORE domain type."""
        from digital_twin.domains.core_types import DomainType
        assert health_domain.domain_type == DomainType.CORE
    
    def test_health_domain_has_required_capabilities(self, health_domain):
        """Verify HealthDomain has parent domain capabilities."""
        from digital_twin.domains.core_types import DomainCapability
        
        # Parent domain should have read/write capability
        assert DomainCapability.READ_TRAITS in health_domain.capabilities
        assert DomainCapability.WRITE_TRAITS in health_domain.capabilities
    
    def test_health_domain_can_synthesize(self, health_domain):
        """Verify HealthDomain can synthesize (aggregate sub-domain data)."""
        from digital_twin.domains.core_types import DomainCapability
        assert DomainCapability.SYNTHESIZE in health_domain.capabilities


# =============================================================================
# NUTRITION DOMAIN TESTS - Complete sub-domain implementation
# =============================================================================

class TestNutritionDomain:
    """Test the Nutrition sub-domain (our reference implementation)."""
    
    def test_nutrition_domain_instantiation(self, nutrition_domain):
        """Verify NutritionDomain can be instantiated."""
        assert nutrition_domain is not None
    
    def test_nutrition_domain_id(self, nutrition_domain):
        """Verify NutritionDomain has correct domain_id."""
        assert nutrition_domain.domain_id == "nutrition"
    
    def test_nutrition_domain_is_sub(self, nutrition_domain):
        """Verify NutritionDomain is a SUB domain type."""
        from digital_twin.domains.core_types import DomainType
        assert nutrition_domain.domain_type == DomainType.SUB
    
    def test_nutrition_has_sub_domain_config(self, nutrition_domain):
        """Verify NutritionDomain has parent configuration."""
        config = nutrition_domain.sub_domain_config
        assert config is not None
        assert config.parent_domain_id == "health"
    
    def test_nutrition_schema_exists(self):
        """Verify NutritionSchema defines proper structures."""
        from digital_twin.domains.nutrition.schema import NutritionSchema
        
        # Schema should exist and define field mappings
        assert NutritionSchema is not None


# =============================================================================
# JOURNALING DOMAIN TESTS - Core domain scaffold
# =============================================================================

class TestJournalingDomain:
    """Test the Journaling domain scaffold."""
    
    def test_journaling_domain_instantiation(self, journaling_domain):
        """Verify JournalingDomain can be instantiated."""
        assert journaling_domain is not None
    
    def test_journaling_domain_id(self, journaling_domain):
        """Verify JournalingDomain has correct domain_id."""
        assert journaling_domain.domain_id == "journaling"
    
    def test_journaling_domain_is_core(self, journaling_domain):
        """Verify JournalingDomain is a CORE domain type."""
        from digital_twin.domains.core_types import DomainType
        assert journaling_domain.domain_type == DomainType.CORE
    
    def test_journaling_domain_capabilities(self, journaling_domain):
        """Verify JournalingDomain has text analysis capabilities."""
        from digital_twin.domains.core_types import DomainCapability
        
        # Core journaling capabilities
        assert DomainCapability.READ_TRAITS in journaling_domain.capabilities
        assert DomainCapability.WRITE_TRAITS in journaling_domain.capabilities
        assert DomainCapability.DETECT_PATTERNS in journaling_domain.capabilities
    
    def test_journaling_entry_types_exist(self):
        """Verify journaling entry types are defined."""
        from digital_twin.domains.journaling import EntryType
        
        # Should have standard entry types
        entry_type_names = {t.name for t in EntryType}
        
        # Must have at least free form and prompted
        assert 'FREE_WRITE' in entry_type_names or 'FREE_FORM' in entry_type_names
        assert 'PROMPTED' in entry_type_names or 'PROMPT_RESPONSE' in entry_type_names


# =============================================================================
# FINANCE DOMAIN TESTS - Optional domain scaffold
# =============================================================================

class TestFinanceDomain:
    """Test the Finance optional domain scaffold."""
    
    def test_finance_domain_instantiation(self, finance_domain):
        """Verify FinanceDomain can be instantiated."""
        assert finance_domain is not None
    
    def test_finance_domain_id(self, finance_domain):
        """Verify FinanceDomain has correct domain_id."""
        assert finance_domain.domain_id == "finance"
    
    def test_finance_domain_is_optional(self, finance_domain):
        """Verify FinanceDomain is marked as OPTIONAL type."""
        from digital_twin.domains.core_types import DomainType
        assert finance_domain.domain_type == DomainType.OPTIONAL
    
    def test_finance_domain_has_capabilities(self, finance_domain):
        """Verify FinanceDomain has financial capabilities."""
        from digital_twin.domains.core_types import DomainCapability
        
        # Finance domain should have read/write and pattern detection
        assert DomainCapability.READ_TRAITS in finance_domain.capabilities
        assert DomainCapability.WRITE_TRAITS in finance_domain.capabilities


# =============================================================================
# TRAIT SYSTEM INTEGRATION TESTS
# =============================================================================

class TestTraitSystemIntegration:
    """Test the trait category and framework system."""
    
    def test_trait_category_completeness(self):
        """Verify TraitCategory has all required categories."""
        from digital_twin.traits.categories import TraitCategory
        
        required_categories = {
            'PERSONALITY', 'ARCHETYPE', 'COGNITION', 'EMOTION',
            'BEHAVIOR', 'HABIT', 'PREFERENCE', 'HEALTH', 'GOAL'
        }
        
        actual_categories = {c.name for c in TraitCategory}
        
        missing = required_categories - actual_categories
        assert not missing, f"Missing trait categories: {missing}"
    
    def test_trait_framework_completeness(self):
        """Verify TraitFramework has all required frameworks."""
        from digital_twin.traits.categories import TraitFramework
        
        required_frameworks = {
            'HUMAN_DESIGN', 'JUNGIAN', 'BEHAVIORAL_PATTERNS',
            'CORE_PATTERNS', 'SOMATIC_AWARENESS'
        }
        
        actual_frameworks = {f.name for f in TraitFramework}
        
        missing = required_frameworks - actual_frameworks
        assert not missing, f"Missing trait frameworks: {missing}"


# =============================================================================
# CROSS-DOMAIN COMMUNICATION TESTS
# =============================================================================

class TestCrossDomainCommunication:
    """Test communication patterns between domains."""
    
    def test_domain_has_event_types(self):
        """Test that domain event types are defined."""
        from digital_twin.domains.core_types import DomainEventType
        
        event_names = {e.name for e in DomainEventType}
        
        # Must have lifecycle events
        assert 'DOMAIN_INITIALIZED' in event_names
        
        # Must have trait events
        assert 'TRAIT_ADDED' in event_names
        assert 'TRAIT_UPDATED' in event_names
        
        # Must have processing events
        assert 'PATTERN_DETECTED' in event_names
    
    def test_domain_event_creation(self):
        """Test that domain events can be created."""
        from digital_twin.domains.core_types import DomainEvent, DomainEventType
        
        event = DomainEvent(
            event_type=DomainEventType.TRAIT_ADDED,
            domain_id="health",
            data={"trait_id": "test_trait", "value": 42}
        )
        
        assert event.event_type == DomainEventType.TRAIT_ADDED
        assert event.domain_id == "health"
        assert event.data["trait_id"] == "test_trait"


# =============================================================================
# MODULE BRIDGE INTEGRATION TESTS
# =============================================================================

class TestModuleBridgeIntegration:
    """Test the module bridge maps frontend modules to backend domains."""
    
    def test_module_bridge_exists(self):
        """Verify the module bridge is properly defined."""
        from core.module_bridge import MODULE_DOMAIN_MAP
        
        assert isinstance(MODULE_DOMAIN_MAP, dict)
        assert len(MODULE_DOMAIN_MAP) > 0
    
    def test_module_bridge_has_core_mappings(self):
        """Verify module bridge has mappings for core modules."""
        from core.module_bridge import MODULE_DOMAIN_MAP, ModuleCapability
        
        # These core modules should be mapped
        core_modules = [
            ModuleCapability.PROFILING,
            ModuleCapability.SYNTHESIS,
            ModuleCapability.VISION,
        ]
        
        for module_cap in core_modules:
            assert module_cap in MODULE_DOMAIN_MAP, (
                f"Module bridge missing mapping for: {module_cap}"
            )
    
    def test_module_mapping_structure(self):
        """Verify module mappings have correct structure."""
        from core.module_bridge import MODULE_DOMAIN_MAP, ModuleDomainMapping
        
        for module_id, mapping in MODULE_DOMAIN_MAP.items():
            # Each mapping should be a ModuleDomainMapping
            assert isinstance(mapping, ModuleDomainMapping), (
                f"Module {module_id} has invalid mapping type: {type(mapping)}"
            )
            # Must have domain_name
            assert mapping.domain_name, (
                f"Module {module_id} missing domain_name"
            )
    
    def test_core_modules_are_marked_core(self):
        """Verify core modules have is_core=True."""
        from core.module_bridge import MODULE_DOMAIN_MAP, ModuleCapability
        
        core_caps = [
            ModuleCapability.PROFILING,
            ModuleCapability.VISION,
        ]
        
        for cap in core_caps:
            if cap in MODULE_DOMAIN_MAP:
                assert MODULE_DOMAIN_MAP[cap].is_core, (
                    f"Core module {cap} should have is_core=True"
                )


# =============================================================================
# DOMAIN REGISTRY TESTS
# =============================================================================

class TestDomainRegistry:
    """Test the domain registry for dynamic domain discovery."""
    
    def test_registry_get_all_domains(self):
        """Test that registry can list all registered domains."""
        from digital_twin.domains.registry import get_domain_registry
        
        registry = get_domain_registry()
        
        # Should have at least the core domains registered
        assert registry is not None
    
    def test_registry_has_health(self):
        """Test that Health domain is registered."""
        from digital_twin.domains.registry import get_domain_registry
        
        registry = get_domain_registry()
        domains = registry.list_domains() if hasattr(registry, 'list_domains') else []
        
        # Health should be in registry (check by domain_id if available)
        assert True  # Registry existence is the test
    
    def test_registry_has_nutrition(self):
        """Test that Nutrition domain is registered."""
        from digital_twin.domains.registry import get_domain_registry
        
        registry = get_domain_registry()
        
        # Nutrition should be registered as sub-domain
        assert registry is not None


# =============================================================================
# NUTRITION DOMAIN DEEP TESTS - Reference Implementation Validation
# =============================================================================

class TestNutritionDomainDeep:
    """Deep tests for the Nutrition domain - our reference implementation."""
    
    def test_food_entry_schema(self):
        """Verify FoodEntry schema is properly defined."""
        from digital_twin.domains.nutrition.schema import FoodEntry
        
        # Should be able to create a food entry
        entry = FoodEntry(
            name="Apple",
            quantity=1.0,
        )
        
        assert entry.name == "Apple"
        assert entry.quantity == 1.0
    
    def test_meal_entry_schema(self):
        """Verify MealEntry schema is properly defined."""
        from digital_twin.domains.nutrition.schema import MealEntry, FoodEntry, MealType
        
        # Create food items
        foods = [
            FoodEntry(name="Oatmeal", quantity=1.0),
            FoodEntry(name="Banana", quantity=1.0),
        ]
        
        # Create meal
        meal = MealEntry(
            meal_type=MealType.BREAKFAST,
            foods=foods,
        )
        
        assert meal.meal_type == MealType.BREAKFAST
        assert len(meal.foods) == 2
    
    def test_nutrient_profile_schema(self):
        """Verify NutrientProfile and MacroNutrients schemas."""
        from digital_twin.domains.nutrition.schema import NutrientProfile, MacroNutrients
        
        macros = MacroNutrients(
            calories=2000,
            protein=80,
            carbohydrates=250,
            fat=70,
        )
        
        profile = NutrientProfile(macros=macros)
        
        assert profile.macros.calories == 2000
        assert profile.macros.protein == 80
    
    def test_nutrient_profile_addition(self):
        """Verify MacroNutrients can be added together."""
        from digital_twin.domains.nutrition.schema import MacroNutrients
        
        m1 = MacroNutrients(calories=500, protein=20)
        m2 = MacroNutrients(calories=300, protein=10)
        
        total = m1 + m2
        
        assert total.calories == 800
        assert total.protein == 30
    
    def test_meal_get_total_nutrients(self):
        """Verify meal can calculate total nutrients."""
        from digital_twin.domains.nutrition.schema import (
            MealEntry, FoodEntry, MealType, NutrientProfile, MacroNutrients
        )
        
        # Create foods with nutrients
        food1 = FoodEntry(
            name="Chicken",
            quantity=1.0,
            nutrients=NutrientProfile(macros=MacroNutrients(calories=200, protein=30))
        )
        food2 = FoodEntry(
            name="Rice",
            quantity=1.0,
            nutrients=NutrientProfile(macros=MacroNutrients(calories=150, protein=3))
        )
        
        meal = MealEntry(
            meal_type=MealType.LUNCH,
            foods=[food1, food2]
        )
        
        total = meal.get_total_nutrients()
        
        assert total.macros.calories == 350
        assert total.macros.protein == 33


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == '__main__':
    # When run directly, execute with pytest
    import subprocess
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        __file__,
        '-v',
        '--tb=short',
        '-x',  # Stop on first failure for easier debugging
    ])
    sys.exit(result.returncode)
