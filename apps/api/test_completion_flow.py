#!/usr/bin/env python3
"""
Genesis Completion Flow Test Suite

Tests the Digital Twin delivery, Master Scout notification,
and completion UI generation when profiling finishes.
"""

import asyncio
import sys
import logging
from typing import Dict, Any
from datetime import datetime

# Add the project to path
sys.path.insert(0, ".")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_header(title: str):
    """Print a test section header."""
    print(f"\n{'='*70}")
    print(f"    {title}")
    print(f"{'='*70}\n")


def test_result(category: str, test_name: str, passed: bool, detail: str = ""):
    """Log a test result."""
    status = "[PASS]" if passed else "[FAIL]"
    logger.info(f"{status} {category} - {test_name}")
    if detail:
        logger.info(f"   └─ {detail[:60]}...")
    return passed


async def test_profile_rubric_export():
    """Test that ProfileRubric correctly exports to Digital Twin format."""
    from src.agents.genesis.state import ProfileRubric, DetectedTrait
    from datetime import datetime, UTC
    
    rubric = ProfileRubric()
    
    # Add some test data using proper DetectedTrait objects
    rubric.set_trait("hd_type", DetectedTrait(
        name="hd_type",
        value="generator",
        confidence=0.9,
        evidence=["sustained_energy", "sacral_response"],
        detected_at=datetime.now(UTC),
    ))
    rubric.set_trait("hd_strategy", DetectedTrait(
        name="hd_strategy",
        value="to_respond",
        confidence=0.85,
        evidence=["waiting_pattern"],
        detected_at=datetime.now(UTC),
    ))
    rubric.set_trait("hd_authority", DetectedTrait(
        name="hd_authority",
        value="emotional",
        confidence=0.7,
        evidence=["wave_patterns"],
        detected_at=datetime.now(UTC),
    ))
    rubric.set_trait("jung_dominant", DetectedTrait(
        name="jung_dominant",
        value="Ni",
        confidence=0.8,
        evidence=["future_focus", "pattern_recognition"],
        detected_at=datetime.now(UTC),
    ))
    rubric.set_trait("energy_pattern", DetectedTrait(
        name="energy_pattern",
        value="sustainable",
        confidence=0.75,
        evidence=["consistent_energy"],
        detected_at=datetime.now(UTC),
    ))
    
    # Export to Digital Twin format (via to_dict or export method)
    passed = True
    
    # Check rubric has traits
    all_traits = rubric.get_all_traits()
    passed &= test_result(
        "ProfileRubric Export", 
        "Traits stored correctly", 
        len(all_traits) >= 5,
        f"Found {len(all_traits)} traits"
    )
    
    # Check hd_type
    hd_type = rubric.get_trait("hd_type")
    passed &= test_result(
        "ProfileRubric Export", 
        "hd_type retrievable", 
        hd_type is not None and hd_type.value == "generator"
    )
    
    # Check jung_dominant
    jung = rubric.get_trait("jung_dominant")
    passed &= test_result(
        "ProfileRubric Export", 
        "jung_dominant retrievable", 
        jung is not None and jung.value == "Ni"
    )
    
    # Check completion percentage
    completion = rubric.completion_percentage()
    passed &= test_result(
        "ProfileRubric Export", 
        "completion_percentage works", 
        completion > 0,
        f"Completion: {completion:.1%}"
    )
    
    return passed


async def test_genesis_core_digital_twin_export():
    """Test that GenesisCore correctly exports Digital Twin."""
    from src.agents.genesis.core import GenesisCore
    from src.agents.genesis.state import GenesisState, DetectedTrait, ActiveSignal
    from datetime import datetime, UTC
    
    core = GenesisCore()
    state = GenesisState()
    
    # Set up some data using proper DetectedTrait
    state.rubric.set_trait("hd_type", DetectedTrait(
        name="hd_type",
        value="projector",
        confidence=0.9,
        evidence=["guidance_orientation"],
        detected_at=datetime.now(UTC),
    ))
    state.rubric.set_trait("jung_dominant", DetectedTrait(
        name="jung_dominant",
        value="Fe",
        confidence=0.85,
        evidence=["harmony_seeking"],
        detected_at=datetime.now(UTC),
    ))
    state.insights.append("Strong leadership potential")
    state.insights.append("Intuitive pattern recognition")
    
    # Add active signals for session_insights - ActiveSignal uses simple string fields
    state.active_signals.append(ActiveSignal(
        source="profiler",
        content="guidance orientation detected",
        signal_type="hypothesis",
        confidence=0.9,
        suggested_traits={"hd_type": "projector"},
    ))
    
    # Export
    digital_twin = core.export_digital_twin(state)
    
    passed = True
    
    passed &= test_result(
        "GenesisCore Export",
        "export_digital_twin returns dict",
        isinstance(digital_twin, dict)
    )
    
    passed &= test_result(
        "GenesisCore Export",
        "energetic_signature present",
        "energetic_signature" in digital_twin
    )
    
    passed &= test_result(
        "GenesisCore Export",
        "psychological_profile present",
        "psychological_profile" in digital_twin
    )
    
    passed &= test_result(
        "GenesisCore Export",
        "session_insights present",
        "session_insights" in digital_twin
    )
    
    passed &= test_result(
        "GenesisCore Export",
        "session_insights has data",
        len(digital_twin.get("session_insights", [])) > 0,
        str(digital_twin.get("session_insights", []))
    )
    
    return passed


async def test_swarm_integration_methods():
    """Test SwarmBus notification methods exist and have correct signatures."""
    from src.agents.genesis.swarm_integration import GenesisSwarmHandler
    from src.agents.genesis.session_manager import GenesisSessionManager
    
    # Create handler with proper dependency
    session_manager = GenesisSessionManager()
    handler = GenesisSwarmHandler(session_manager)
    passed = True
    
    # Check send_digital_twin method
    passed &= test_result(
        "SwarmIntegration",
        "send_digital_twin method exists",
        hasattr(handler, "send_digital_twin")
    )
    
    # Check broadcast_profile_ready method
    passed &= test_result(
        "SwarmIntegration",
        "broadcast_profile_ready method exists",
        hasattr(handler, "broadcast_profile_ready")
    )
    
    # Verify they're async
    import inspect
    
    if hasattr(handler, "send_digital_twin"):
        passed &= test_result(
            "SwarmIntegration",
            "send_digital_twin is async",
            inspect.iscoroutinefunction(handler.send_digital_twin)
        )
    
    if hasattr(handler, "broadcast_profile_ready"):
        passed &= test_result(
            "SwarmIntegration",
            "broadcast_profile_ready is async",
            inspect.iscoroutinefunction(handler.broadcast_profile_ready)
        )
    
    return passed


async def test_completion_response_structure():
    """Test that completion response has correct component structure."""
    from src.agents.genesis_profiler import GenesisProfilerAgent
    from src.agents.genesis.state import GenesisState
    
    agent = GenesisProfilerAgent()
    
    passed = True
    
    # Test _build_completion_components method exists
    passed &= test_result(
        "Completion Response",
        "_build_completion_components method exists",
        hasattr(agent, "_build_completion_components")
    )
    
    # Test _generate_activation_steps method exists
    passed &= test_result(
        "Completion Response",
        "_generate_activation_steps method exists",
        hasattr(agent, "_generate_activation_steps")
    )
    
    # Test _generate_completion_response method exists
    passed &= test_result(
        "Completion Response",
        "_generate_completion_response method exists",
        hasattr(agent, "_generate_completion_response")
    )
    
    return passed


async def test_activation_steps_generation():
    """Test that activation steps are correctly generated based on HD type."""
    from src.agents.genesis_profiler import GenesisProfilerAgent
    
    agent = GenesisProfilerAgent()
    
    passed = True
    
    # Test for Generator - pass full digital twin dict
    dt_generator = {
        "energetic_signature": {"hd_type": "generator"},
        "psychological_profile": {},
    }
    steps_generator = agent._generate_activation_steps(dt_generator)
    passed &= test_result(
        "Activation Steps",
        "Generator steps generated",
        len(steps_generator) >= 1,
        f"Generated {len(steps_generator)} steps"
    )
    
    # Check step structure
    if steps_generator:
        step = steps_generator[0]
        passed &= test_result(
            "Activation Steps",
            "Step has id",
            "id" in step
        )
        passed &= test_result(
            "Activation Steps",
            "Step has title",
            "title" in step
        )
        passed &= test_result(
            "Activation Steps",
            "Step has description",
            "description" in step
        )
        passed &= test_result(
            "Activation Steps",
            "Step has priority",
            "priority" in step
        )
        passed &= test_result(
            "Activation Steps",
            "Step has category",
            "category" in step
        )
    
    # Test for Projector (different steps)
    dt_projector = {
        "energetic_signature": {"hd_type": "projector"},
        "psychological_profile": {},
    }
    steps_projector = agent._generate_activation_steps(dt_projector)
    passed &= test_result(
        "Activation Steps",
        "Projector steps generated",
        len(steps_projector) >= 1,
        f"Projector has {len(steps_projector)} steps"
    )
    
    # Test for Manifestor
    dt_manifestor = {
        "energetic_signature": {"hd_type": "manifestor"},
        "psychological_profile": {},
    }
    steps_manifestor = agent._generate_activation_steps(dt_manifestor)
    passed &= test_result(
        "Activation Steps",
        "Manifestor steps generated",
        len(steps_manifestor) >= 1
    )
    
    # Test for Reflector
    dt_reflector = {
        "energetic_signature": {"hd_type": "reflector"},
        "psychological_profile": {},
    }
    steps_reflector = agent._generate_activation_steps(dt_reflector)
    passed &= test_result(
        "Activation Steps",
        "Reflector steps generated",
        len(steps_reflector) >= 1
    )
    
    return passed


async def test_completion_component_types():
    """Test that the correct component types are used for completion."""
    from src.agents.genesis_profiler import GenesisProfilerAgent
    from src.agents.genesis.state import GenesisState
    from src.agents.genesis.face.voice.voices import OracleVoice
    
    agent = GenesisProfilerAgent()
    
    # Create digital twin data
    digital_twin = {
        "energetic_signature": {
            "hd_type": "generator",
            "hd_strategy": "to_respond",
            "hd_authority": "emotional",
        },
        "psychological_profile": {
            "jung_dominant": "Ni",
        },
        "completion": 0.85,
    }
    
    voice = OracleVoice()
    
    # Build components using correct signature
    components = agent._build_completion_components(
        digital_twin=digital_twin,
        completion_message="You are a powerful Generator with deep intuitive gifts.",
        voice_id=voice.identity.id,
    )
    
    passed = True
    
    # Check we have components
    passed &= test_result(
        "Completion Components",
        "Components generated",
        len(components) > 0,
        f"{len(components)} components"
    )
    
    # Check for required component types
    component_types = [c.get("type") for c in components]
    
    passed &= test_result(
        "Completion Components",
        "Has text component",
        "text" in component_types
    )
    
    passed &= test_result(
        "Completion Components",
        "Has digital_twin_card component",
        "digital_twin_card" in component_types
    )
    
    passed &= test_result(
        "Completion Components",
        "Has activation_steps component",
        "activation_steps" in component_types
    )
    
    passed &= test_result(
        "Completion Components",
        "Has completion_transition component",
        "completion_transition" in component_types
    )
    
    # Check digital_twin_card has digital_twin at ROOT (not in props!)
    # Frontend reads: digitalTwinComp?.digital_twin
    twin_card = next((c for c in components if c.get("type") == "digital_twin_card"), None)
    if twin_card:
        passed &= test_result(
            "Completion Components",
            "digital_twin_card has digital_twin at root",
            "digital_twin" in twin_card,
            str(twin_card.get("digital_twin", {}))[:60]
        )
    else:
        passed = False
        test_result("Completion Components", "digital_twin_card found", False)
    
    # Check activation_steps has steps at ROOT (not in props!)
    # Frontend reads: activationStepsComp?.steps
    steps_comp = next((c for c in components if c.get("type") == "activation_steps"), None)
    if steps_comp:
        steps = steps_comp.get("steps", [])
        passed &= test_result(
            "Completion Components",
            "activation_steps has steps at root",
            "steps" in steps_comp and len(steps) > 0,
            f"{len(steps)} steps"
        )
    else:
        passed = False
        test_result("Completion Components", "activation_steps found", False)
    
    return passed


async def run_all_tests():
    """Run all completion flow tests."""
    test_header("GENESIS COMPLETION FLOW TEST SUITE")
    
    tests = [
        ("ProfileRubric Digital Twin Export", test_profile_rubric_export),
        ("GenesisCore Digital Twin Export", test_genesis_core_digital_twin_export),
        ("SwarmBus Integration Methods", test_swarm_integration_methods),
        ("Completion Response Structure", test_completion_response_structure),
        ("Activation Steps Generation", test_activation_steps_generation),
        ("Completion Component Types", test_completion_component_types),
    ]
    
    results = {}
    total_passed = 0
    total_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n--- Testing: {test_name} ---")
        try:
            passed = await test_func()
            results[test_name] = passed
            if passed:
                total_passed += 1
            total_tests += 1
        except Exception as e:
            logger.error(f"[FAIL] {test_name} - Exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
            total_tests += 1
    
    # Summary
    test_header("COMPLETION FLOW TEST RESULTS")
    
    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  PASSED: {total_passed}/{total_tests}")
    print(f"  FAILED: {total_tests - total_passed}/{total_tests}")
    print(f"{'='*70}")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
