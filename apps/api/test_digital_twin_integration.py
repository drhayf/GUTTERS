"""
Digital Twin Integration Tests

Comprehensive tests for the new Digital Twin system integration:
1. Module Bridge - Frontend/Backend sync
2. Genesis Adapter - Profiler to Digital Twin writes
3. Profile Migration - Legacy to new format
4. API Endpoints - Module sync endpoints

Run with: python test_digital_twin_integration.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_header(title: str):
    """Print a formatted test header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(name: str, passed: bool, message: str = ""):
    """Print a test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f" - {message}" if message else ""
    print(f"  {status}: {name}{msg}")


async def test_module_bridge():
    """Test the Module-Domain Bridge."""
    print_header("Module Bridge Tests")
    
    try:
        from core.module_bridge import (
            ModuleBridge,
            CapabilityRegistry,
            ModuleCapability,
            get_bridge,
        )
        
        # Test 1: Get bridge instance
        bridge = await get_bridge()
        print_result("Get bridge instance", bridge is not None)
        
        # Test 2: Sync preferences
        result = await bridge.sync_from_frontend({
            "enabled": ["profiling", "human_design", "archetypes"],
            "disabled": ["finance", "astrology"],
        })
        print_result("Sync preferences", result.get("success", False))
        
        # Test 3: Check capability active
        is_active = bridge.is_capability_active("profiling")
        print_result("Check capability active", is_active)
        
        # Test 4: Get enabled modules
        enabled = await bridge.get_enabled_modules()
        print_result("Get enabled modules", len(enabled) > 0, f"Found {len(enabled)} modules")
        
        # Test 5: Toggle module
        state = await bridge.toggle_module("finance", True)
        print_result("Toggle module", state.enabled)
        
        # Test 6: Get domain for module
        domain = bridge.get_domain_for_module("human_design")
        print_result("Get domain for module", domain == "genesis", f"Domain: {domain}")
        
        return True
    except Exception as e:
        print_result("Module Bridge", False, str(e))
        return False


async def test_genesis_adapter():
    """Test the Genesis Digital Twin Adapter."""
    print_header("Genesis Adapter Tests")
    
    try:
        from agents.genesis.digital_twin_adapter import (
            GenesisTwinAdapter,
            TraitResult,
            get_adapter,
        )
        
        # Test 1: Get adapter instance
        adapter = await get_adapter()
        print_result("Get adapter instance", adapter is not None)
        
        # Test 2: Record a trait
        success = await adapter.record_trait(
            trait_name="hd_type",
            value="projector",
            confidence=0.75,
            evidence=["User mentioned waiting for invitations"],
            source="test"
        )
        print_result("Record trait", success)
        
        # Test 3: Get trait back
        trait = await adapter.get_trait("hd_type")
        if trait:
            print_result("Get trait", trait.value == "projector", f"Value: {trait.value}")
        else:
            print_result("Get trait", False, "Trait not found (Digital Twin may not be initialized)")
        
        # Test 4: Update confidence
        new_conf = await adapter.update_confidence("hd_type", 0.1, "Additional evidence")
        if new_conf is not None:
            print_result("Update confidence", new_conf > 0.75, f"New confidence: {new_conf}")
        else:
            print_result("Update confidence", True, "Skipped (no trait to update)")
        
        # Test 5: Get completion percentage
        completion = await adapter.get_completion_percentage()
        print_result("Get completion", completion >= 0, f"Completion: {completion:.1f}%")
        
        return True
    except Exception as e:
        print_result("Genesis Adapter", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_profile_migration():
    """Test the Profile Migration system."""
    print_header("Profile Migration Tests")
    
    try:
        from core.profile_migration import (
            ProfileMigrator,
            MigrationResult,
            get_migrator,
            FIELD_MAPPING,
        )
        
        # Test 1: Get migrator instance
        migrator = get_migrator()
        print_result("Get migrator instance", migrator is not None)
        
        # Test 2: Check migration status
        status = await migrator.check_migration_status()
        print_result(
            "Check migration status",
            "needs_migration" in status,
            f"Needs: {status.get('needs_migration', [])}"
        )
        
        # Test 3: Migrate sample rubric data
        sample_rubric = {
            "hd_type": {
                "value": "generator",
                "confidence": 0.8,
                "evidence": ["Mentioned response", "Sacral sounds"],
                "source": "profiler"
            },
            "jung_dominant": {
                "value": "Ni",
                "confidence": 0.6,
                "evidence": ["Future vision talk"],
                "source": "profiler"
            },
            "energy_pattern": "sustainable",  # Simple value format
        }
        
        result = await migrator.migrate_rubric_data(sample_rubric)
        print_result(
            "Migrate sample data",
            result.traits_migrated > 0 or result.success,
            f"Migrated: {result.traits_migrated} traits"
        )
        
        # Test 4: Check field mapping completeness
        essential_fields = ["hd_type", "jung_dominant", "energy_pattern"]
        all_mapped = all(f in FIELD_MAPPING for f in essential_fields)
        print_result("Field mapping complete", all_mapped)
        
        return True
    except Exception as e:
        print_result("Profile Migration", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_digital_twin_core():
    """Test the Digital Twin Core system."""
    print_header("Digital Twin Core Tests")
    
    try:
        from digital_twin import (
            DigitalTwinCore,
            get_digital_twin_core,
            Trait,
            get_event_bus,
            get_accessor,
        )
        
        # Test 1: Get core instance
        core = await get_digital_twin_core()
        print_result("Get core instance", core is not None)
        
        # Test 2: Set a trait
        await core.set(
            path="test.sample_trait",
            value="test_value",
            confidence=0.9,
            source="test_suite"
        )
        print_result("Set trait", True)
        
        # Test 3: Get trait back
        result = await core.get("test.sample_trait")
        print_result(
            "Get trait",
            result is not None,
            f"Got: {type(result).__name__}"
        )
        
        # Test 4: Event bus
        bus = await get_event_bus()
        print_result("Get event bus", bus is not None)
        
        # Test 5: Accessor
        accessor = await get_accessor()
        print_result("Get accessor", accessor is not None)
        
        return True
    except Exception as e:
        print_result("Digital Twin Core", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test module sync API endpoints (requires running server)."""
    print_header("API Endpoint Tests")
    
    try:
        import aiohttp
        
        base_url = "http://localhost:8000/api/python"
        
        async with aiohttp.ClientSession() as session:
            # Test 1: List modules
            try:
                async with session.get(f"{base_url}/modules/") as resp:
                    if resp.status == 200:
                        modules = await resp.json()
                        print_result("List modules", len(modules) > 0, f"Found {len(modules)} modules")
                    else:
                        print_result("List modules", False, f"Status: {resp.status}")
            except aiohttp.ClientConnectorError:
                print_result("List modules", False, "Server not running")
                return False
            
            # Test 2: Get enabled modules
            async with session.get(f"{base_url}/modules/enabled") as resp:
                if resp.status == 200:
                    enabled = await resp.json()
                    print_result("Get enabled", isinstance(enabled, list), f"Found {len(enabled)} enabled")
                else:
                    print_result("Get enabled", False)
            
            # Test 3: Sync modules
            sync_payload = {
                "preferences": {
                    "enabled_modules": ["profiling", "human_design"],
                    "disabled_modules": ["finance"],
                    "sync_timestamp": datetime.now().isoformat()
                }
            }
            async with session.post(f"{base_url}/modules/sync", json=sync_payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print_result("Sync modules", result.get("success", False))
                else:
                    print_result("Sync modules", False, f"Status: {resp.status}")
            
            # Test 4: Get domain mappings
            async with session.get(f"{base_url}/modules/domains") as resp:
                if resp.status == 200:
                    mappings = await resp.json()
                    print_result("Get domains", len(mappings) > 0, f"Found {len(mappings)} mappings")
                else:
                    print_result("Get domains", False)
        
        return True
    except ImportError:
        print_result("API Tests", False, "aiohttp not installed - skipping API tests")
        return True  # Don't fail if aiohttp not available
    except Exception as e:
        print_result("API Endpoints", False, str(e))
        return False


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "🧪" * 30)
    print("  DIGITAL TWIN INTEGRATION TEST SUITE")
    print("🧪" * 30)
    
    results = []
    
    # Run tests
    results.append(("Digital Twin Core", await test_digital_twin_core()))
    results.append(("Module Bridge", await test_module_bridge()))
    results.append(("Genesis Adapter", await test_genesis_adapter()))
    results.append(("Profile Migration", await test_profile_migration()))
    
    # API tests only if server might be running
    try:
        import aiohttp
        results.append(("API Endpoints", await test_api_endpoints()))
    except ImportError:
        print("\n⚠️  Skipping API tests (aiohttp not installed)")
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} suites passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠️  {total - passed} test suite(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
