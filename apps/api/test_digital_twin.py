"""
Digital Twin Architecture Tests

Comprehensive test suite for the new Digital Twin system.
Tests all modules: traits, events, domains, identity, access, core.

Run with: python test_digital_twin.py
"""

import asyncio
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test tracking
tests_passed = 0
tests_failed = 0
test_results = []


def test(name: str):
    """Decorator for test functions."""
    def decorator(func):
        async def wrapper():
            global tests_passed, tests_failed
            try:
                await func() if asyncio.iscoroutinefunction(func) else func()
                tests_passed += 1
                test_results.append(("✅", name))
                print(f"  ✅ {name}")
            except AssertionError as e:
                tests_failed += 1
                test_results.append(("❌", name, str(e)))
                print(f"  ❌ {name}: {e}")
            except Exception as e:
                tests_failed += 1
                test_results.append(("💥", name, str(e)))
                print(f"  💥 {name}: {type(e).__name__}: {e}")
        return wrapper
    return decorator


# =============================================================================
# TRAIT TESTS
# =============================================================================

print("\n🧬 Testing Trait System...")

@test("Trait creation")
def test_trait_creation():
    from digital_twin.traits import Trait, TraitCategory, TraitFramework
    
    trait = Trait.create(
        name="hd_type",
        category=TraitCategory.HUMAN_DESIGN,
        framework=TraitFramework.HUMAN_DESIGN,
        value="Generator",
        confidence=0.95,
        source_type="profiler",
        source_agent="genesis.profiler"
    )
    
    assert trait.name == "hd_type"
    assert trait.value == "Generator"
    assert trait.confidence == 0.95
    assert trait.category == TraitCategory.HUMAN_DESIGN


@test("Trait with_update creates history")
def test_trait_update():
    from digital_twin.traits import Trait, TraitCategory
    
    original = Trait.create(
        name="energy_pattern",
        category=TraitCategory.SOMATIC,
        value="sustainable",
        confidence=0.7,
        source_type="initial"
    )
    
    updated = original.with_update(
        value="explosive",
        confidence=0.9,
        source_type="profiler"
    )
    
    assert updated.value == "explosive"
    assert updated.confidence == 0.9
    assert len(updated.history) == 1
    assert updated.history[0].old_value == "sustainable"


@test("TraitCategory enum values")
def test_trait_categories():
    from digital_twin.traits import TraitCategory
    
    assert TraitCategory.HUMAN_DESIGN.value == "human_design"
    assert TraitCategory.JUNGIAN.value == "jungian"
    assert TraitCategory.SOMATIC.value == "somatic"
    assert len(TraitCategory) >= 15  # We have many categories


@test("TraitFramework enum values")
def test_trait_frameworks():
    from digital_twin.traits import TraitFramework
    
    assert TraitFramework.HUMAN_DESIGN.value == "human_design"
    assert TraitFramework.JUNGIAN_COGNITIVE.value == "jungian_cognitive"
    assert TraitFramework.CORE_PATTERNS.value == "core_patterns"


@test("TraitValidator validates correctly")
def test_trait_validation():
    from digital_twin.traits import Trait, TraitCategory, TraitValidator
    
    validator = TraitValidator()
    
    # Valid trait
    valid = Trait.create(
        name="test_trait",
        category=TraitCategory.MISC,
        value="test_value",
        confidence=0.5,
        source_type="test"
    )
    errors = validator.validate(valid)
    assert len(errors) == 0
    
    # Invalid confidence
    invalid = Trait.create(
        name="test_trait",
        category=TraitCategory.MISC,
        value="test",
        confidence=1.5,  # Invalid: > 1.0
        source_type="test"
    )
    errors = validator.validate(invalid)
    assert len(errors) > 0


# =============================================================================
# EVENT TESTS
# =============================================================================

print("\n📡 Testing Event System...")

@test("EventType enum values")
def test_event_types():
    from digital_twin.events import EventType
    
    assert EventType.TRAIT_ADDED.value == "trait_added"
    assert EventType.TRAIT_UPDATED.value == "trait_updated"
    assert EventType.IDENTITY_LOADED.value == "identity_loaded"


@test("ProfileEventBus singleton")
async def test_event_bus_singleton():
    from digital_twin.events import get_event_bus, ProfileEventBus
    
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    
    assert bus1 is bus2


@test("Event subscription and emission")
async def test_event_subscription():
    from digital_twin.events import ProfileEventBus, TraitAddedEvent
    
    bus = ProfileEventBus()  # Create fresh for testing
    
    received = []
    
    async def handler(event):
        received.append(event)
    
    sub_id = await bus.subscribe(handler)
    
    event = TraitAddedEvent(
        trait_path="genesis.hd_type",
        trait_name="hd_type",
        domain="genesis",
        value="Generator",
        confidence=0.9
    )
    
    await bus.emit(event)
    await asyncio.sleep(0.1)  # Give time for async processing
    
    assert len(received) >= 1
    await bus.unsubscribe(sub_id)


# =============================================================================
# DOMAIN TESTS
# =============================================================================

print("\n🌐 Testing Domain System...")

@test("DomainRegistry singleton")
def test_domain_registry_singleton():
    from digital_twin.domains import get_domain_registry
    
    reg1 = get_domain_registry()
    reg2 = get_domain_registry()
    
    assert reg1 is reg2


@test("GenesisDomain schema")
def test_genesis_domain_schema():
    from digital_twin.domains import GenesisDomain
    
    domain = GenesisDomain()
    schema = domain.get_schema()
    
    assert schema.domain_name == "genesis"
    assert len(schema.traits) > 20  # Genesis has many traits
    
    # Check for key traits
    trait_names = [t.name for t in schema.traits]
    assert "hd_type" in trait_names
    assert "jung_dominant" in trait_names
    assert "energy_pattern" in trait_names


@test("GenesisDomain summary")
def test_genesis_domain_summary():
    from digital_twin.domains import GenesisDomain
    
    domain = GenesisDomain()
    summary = domain.get_summary()
    
    assert summary["name"] == "genesis"
    assert "trait_count" in summary
    assert summary["trait_count"] > 0


# =============================================================================
# IDENTITY TESTS
# =============================================================================

print("\n🪪 Testing Identity System...")

@test("Identity creation")
def test_identity_creation():
    from digital_twin.identity import Identity
    
    identity = Identity()
    
    assert identity.id is not None
    assert len(identity.traits_by_domain) == 0
    assert identity.hd_type is None


@test("Identity set_trait and get_trait")
def test_identity_traits():
    from digital_twin.identity import Identity
    from digital_twin.traits import Trait, TraitCategory
    
    identity = Identity()
    
    trait = Trait.create(
        name="hd_type",
        category=TraitCategory.HUMAN_DESIGN,
        value="Generator",
        confidence=0.95,
        source_type="test"
    )
    
    identity.set_trait("genesis.hd_type", trait)
    
    retrieved = identity.get_trait("genesis.hd_type")
    assert retrieved is not None
    assert retrieved.value == "Generator"


@test("Identity to_summary")
def test_identity_summary():
    from digital_twin.identity import Identity
    from digital_twin.traits import Trait, TraitCategory
    
    identity = Identity()
    identity.hd_type = "Generator"
    identity.jung_dominant = "Ni"
    
    trait = Trait.create(
        name="hd_type",
        category=TraitCategory.HUMAN_DESIGN,
        value="Generator",
        confidence=0.95,
        source_type="test"
    )
    identity.set_trait("genesis.hd_type", trait)
    
    summary = identity.to_summary()
    
    assert summary["hd_type"] == "Generator"
    assert summary["jung_dominant"] == "Ni"
    assert summary["domains"] == ["genesis"]


@test("IdentityStore save and load")
async def test_identity_store():
    from digital_twin.identity import IdentityStore, Identity
    from digital_twin.traits import Trait, TraitCategory
    
    # Use temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        store = IdentityStore(storage_path=tmpdir)
        
        # Create identity with trait
        identity = Identity()
        trait = Trait.create(
            name="hd_type",
            category=TraitCategory.HUMAN_DESIGN,
            value="Projector",
            confidence=0.85,
            source_type="test"
        )
        identity.set_trait("genesis.hd_type", trait)
        
        # Save
        await store.save(identity)
        
        # Load
        loaded = await store.load(identity.id)
        
        assert loaded is not None
        assert loaded.id == identity.id
        
        loaded_trait = loaded.get_trait("genesis.hd_type")
        assert loaded_trait is not None
        assert loaded_trait.value == "Projector"


# =============================================================================
# ACCESS TESTS
# =============================================================================

print("\n🔑 Testing Access System...")

@test("AccessPermission levels")
def test_permission_levels():
    from digital_twin.access import PermissionLevel, AccessPermission
    
    # Read-only
    perm = AccessPermission.read_only()
    assert perm.can_read()
    assert not perm.can_write()
    assert not perm.can_delete()
    
    # Sovereign
    perm = AccessPermission.sovereign()
    assert perm.can_read()
    assert perm.can_write()
    assert perm.can_delete()


@test("QueryBuilder fluent API")
def test_query_builder():
    from digital_twin.access import QueryBuilder
    
    query = (
        QueryBuilder()
        .from_domain("genesis")
        .confidence_above(0.7)
        .where_eq("category", "human_design")
        .limit(10)
        .build()
    )
    
    assert query["domain"] == "genesis"
    assert query["min_confidence"] == 0.7
    assert query["limit"] == 10
    assert len(query["conditions"]) == 1


@test("QueryResult creation")
def test_query_result():
    from digital_twin.access import QueryResult
    
    # Empty result
    empty = QueryResult.empty()
    assert empty.success
    assert empty.count == 0
    
    # Single result
    single = QueryResult.single({"value": "test"})
    assert single.count == 1
    assert single.first()["value"] == "test"
    
    # Error result
    error = QueryResult.error("Something went wrong")
    assert not error.success
    assert error.error == "Something went wrong"


# =============================================================================
# CORE TESTS
# =============================================================================

print("\n🎯 Testing Core System...")

@test("DigitalTwinConfig defaults")
def test_config_defaults():
    from digital_twin.core import DigitalTwinConfig
    
    config = DigitalTwinConfig()
    
    assert config.storage_path == "data/identities"
    assert config.auto_save == True
    assert config.confirmed_threshold == 0.80


@test("DigitalTwinCore singleton")
async def test_core_singleton():
    from digital_twin.core import DigitalTwinCore, get_digital_twin_core
    
    # Reset singleton for test
    DigitalTwinCore._instance = None
    DigitalTwinCore._initialized = False
    
    core1 = await get_digital_twin_core()
    core2 = await get_digital_twin_core()
    
    assert core1 is core2


@test("DigitalTwinCore sovereign_context")
async def test_sovereign_context():
    from digital_twin.core import DigitalTwinCore
    from digital_twin.access import PermissionLevel
    
    # Reset singleton
    DigitalTwinCore._instance = None
    DigitalTwinCore._initialized = False
    
    core = await DigitalTwinCore.get_instance()
    
    context = core.sovereign_context()
    
    assert context.accessor_id == "sovereign"
    assert context.permission.level == PermissionLevel.SOVEREIGN


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

print("\n🔗 Testing Sovereign Integration...")

@test("SovereignDigitalTwinIntegration creation")
async def test_sovereign_integration():
    from digital_twin.integrations import (
        SovereignDigitalTwinIntegration,
        get_sovereign_twin_integration
    )
    
    # Reset singleton
    SovereignDigitalTwinIntegration._instance = None
    
    integration = await get_sovereign_twin_integration()
    
    assert integration is not None


@test("SovereignDigitalTwinIntegration get_state")
async def test_integration_get_state():
    from digital_twin.integrations import get_sovereign_twin_integration
    
    integration = await get_sovereign_twin_integration()
    state = integration.get_state()
    
    assert "profiling_phase" in state
    assert "trait_count" in state
    assert "domains" in state


@test("SovereignDigitalTwinIntegration set and get")
async def test_integration_set_get():
    from digital_twin.integrations import get_sovereign_twin_integration
    
    integration = await get_sovereign_twin_integration()
    
    # Set a trait
    await integration.set("genesis.test_trait", "test_value", confidence=0.8)
    
    # Get it back
    value = await integration.get("genesis.test_trait")
    
    assert value == "test_value"


# =============================================================================
# RUN ALL TESTS
# =============================================================================

async def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("🧪 DIGITAL TWIN ARCHITECTURE TESTS")
    print("=" * 60)
    
    # Run sync tests
    test_trait_creation()
    test_trait_update()
    test_trait_categories()
    test_trait_frameworks()
    test_trait_validation()
    
    test_event_types()
    await test_event_bus_singleton()
    await test_event_subscription()
    
    test_domain_registry_singleton()
    test_genesis_domain_schema()
    test_genesis_domain_summary()
    
    test_identity_creation()
    test_identity_traits()
    test_identity_summary()
    await test_identity_store()
    
    test_permission_levels()
    test_query_builder()
    test_query_result()
    
    test_config_defaults()
    await test_core_singleton()
    await test_sovereign_context()
    
    await test_sovereign_integration()
    await test_integration_get_state()
    await test_integration_set_get()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    if tests_failed > 0:
        print("\n❌ Failed tests:")
        for result in test_results:
            if result[0] != "✅":
                print(f"   {result[0]} {result[1]}: {result[2] if len(result) > 2 else ''}")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
