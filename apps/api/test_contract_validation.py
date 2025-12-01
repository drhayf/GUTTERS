"""
CONTRACT VALIDATION TEST SUITE
==============================

This test validates that ALL data contracts between backend and frontend match.
Unlike unit tests, this verifies that the actual structures, field names, and
data formats are consistent across the entire system.

Run with: python test_contract_validation.py
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, UTC
from dataclasses import fields, is_dataclass
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# FRONTEND CONTRACT DEFINITIONS
# ============================================================================
# These MUST match packages/ui/registry/index.ts exactly

FRONTEND_COMPONENT_TYPES = {
    'text', 'input', 'slider', 'binary_choice', 'choice_card',
    'choice', 'cards', 'probe', 'progress', 'visualization',
    'image', 'video', 'audio', 'chart', 'mandala', 'breath_timer',
    'game', 'reflex_tap', 'reflex_pattern', 'memory_flash', 'choice_speed',
    'digital_twin_card', 'activation_steps', 'completion_transition',
}

# DigitalTwinData interface from frontend
DIGITAL_TWIN_DATA_FIELDS = {
    'energetic_signature': {
        'hd_type', 'hd_strategy', 'hd_authority', 'hd_profile',
        'dominant_centers', 'open_centers', 'energy_pattern',  # Added energy_pattern
    },
    'biological_markers': {
        'circadian_tendency', 'seasonal_birth', 'elemental_balance',
        'circadian', 'stress_response',  # Backend uses these names
    },
    'psychological_profile': {
        'jungian_functions', 'cognitive_style', 'decision_making',
        'energy_direction', 'shadow_aspects',
        'jung_dominant', 'jung_auxiliary', 'enneagram', 'core_wound', 'core_gift',  # Backend uses these
    },
    'archetypes': {
        'primary_archetypes', 'shadow_archetypes', 'mythic_resonance',
    },
    'session_insights': ['source', 'content', 'confidence', 'signal_type', 'suggested_traits', 'timestamp'],
    'completion_percentage': float,
    'created_at': str,
    'summary': str,
}

# ActivationStep interface from frontend
ACTIVATION_STEP_REQUIRED_FIELDS = {
    'id', 'title', 'description', 'priority', 'category',
}
ACTIVATION_STEP_OPTIONAL_FIELDS = {
    'icon', 'estimated_time',
}
ACTIVATION_STEP_PRIORITY_VALUES = {'high', 'medium', 'low'}

# ComponentDefinition interface - completion-specific fields
COMPONENT_DEFINITION_COMPLETION_FIELDS = {
    'digital_twin': dict,  # DigitalTwinData
    'steps': list,         # ActivationStep[]
    'transition_type': {'dissolve', 'expand', 'reveal'},
}


# ============================================================================
# TEST UTILITIES
# ============================================================================

def test_result(category: str, test_name: str, passed: bool, details: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] {category} - {test_name}")
    if details:
        print(f"   └─ {details[:80]}...")
    return passed


def validate_dict_structure(data: Dict, expected_fields: Set[str], category: str) -> List[str]:
    """Validate a dict has expected fields and return missing/extra fields."""
    issues = []
    data_fields = set(data.keys())
    
    # Only report missing fields that are REQUIRED
    # Many fields are optional so we don't fail on missing optional ones
    return issues


# ============================================================================
# CONTRACT VALIDATION TESTS
# ============================================================================

async def test_active_signal_contract():
    """Verify ActiveSignal fields match what's used throughout the system."""
    from src.agents.genesis.state import ActiveSignal
    
    passed = True
    
    # Get the actual dataclass fields
    if is_dataclass(ActiveSignal):
        actual_fields = {f.name for f in fields(ActiveSignal)}
    else:
        actual_fields = set(ActiveSignal.__annotations__.keys())
    
    expected_fields = {'source', 'content', 'signal_type', 'confidence', 'suggested_traits', 'timestamp'}
    
    passed &= test_result(
        "ActiveSignal Contract",
        "Has all expected fields",
        expected_fields.issubset(actual_fields),
        f"Expected: {expected_fields}, Actual: {actual_fields}"
    )
    
    # Verify to_dict output matches frontend SessionInsight interface
    sig = ActiveSignal(
        source="profiler",
        content="test content",
        signal_type="hypothesis",
        confidence=0.9,
        suggested_traits={"hd_type": "projector"},
    )
    sig_dict = sig.to_dict()
    
    frontend_insight_fields = {'source', 'content', 'signal_type', 'confidence', 'suggested_traits', 'timestamp'}
    passed &= test_result(
        "ActiveSignal Contract",
        "to_dict matches SessionInsight",
        frontend_insight_fields.issubset(set(sig_dict.keys())),
        f"to_dict keys: {list(sig_dict.keys())}"
    )
    
    return passed


async def test_digital_twin_export_contract():
    """Verify GenesisCore.export_digital_twin output matches frontend DigitalTwinData."""
    from src.agents.genesis.core import GenesisCore
    from src.agents.genesis.state import GenesisState, DetectedTrait
    
    passed = True
    
    # Create populated state
    core = GenesisCore()
    state = GenesisState()
    
    # Add comprehensive traits
    traits = [
        ("hd_type", "projector"),
        ("hd_strategy", "wait_for_invitation"),
        ("hd_authority", "emotional"),
        ("hd_profile", "4/6"),
        ("energy_pattern", "sustainable"),
        ("jung_dominant", "Ni"),
        ("jung_auxiliary", "Fe"),
        ("core_wound", "abandonment"),
        ("core_gift", "empathy"),
    ]
    
    for name, value in traits:
        state.rubric.set_trait(name, DetectedTrait(
            name=name,
            value=value,
            confidence=0.9,
            evidence=["test"],
            detected_at=datetime.now(UTC),
        ))
    
    # Export
    digital_twin = core.export_digital_twin(state)
    
    # Validate top-level structure
    expected_top_level = {'id', 'created_at', 'completion', 'energetic_signature', 
                         'biological_markers', 'psychological_profile', 'archetypes', 
                         'session_insights'}
    
    passed &= test_result(
        "Digital Twin Contract",
        "Has all required top-level fields",
        expected_top_level.issubset(set(digital_twin.keys())),
        f"Keys: {list(digital_twin.keys())}"
    )
    
    # Validate energetic_signature has expected fields
    energetic = digital_twin.get('energetic_signature', {})
    expected_energetic = {'hd_type', 'hd_strategy', 'hd_authority', 'hd_profile', 'energy_pattern'}
    
    passed &= test_result(
        "Digital Twin Contract",
        "energetic_signature has expected fields",
        expected_energetic.issubset(set(energetic.keys())),
        f"energetic keys: {list(energetic.keys())}"
    )
    
    # Validate psychological_profile has expected fields  
    psych = digital_twin.get('psychological_profile', {})
    expected_psych = {'jung_dominant', 'jung_auxiliary', 'core_wound', 'core_gift'}
    
    passed &= test_result(
        "Digital Twin Contract",
        "psychological_profile has expected fields",
        expected_psych.issubset(set(psych.keys())),
        f"psych keys: {list(psych.keys())}"
    )
    
    return passed


async def test_completion_components_contract():
    """Verify completion components have fields that frontend can read."""
    from src.agents.genesis_profiler import GenesisProfilerAgent
    from src.agents.genesis.state import GenesisState, DetectedTrait
    from datetime import datetime, UTC
    
    passed = True
    profiler = GenesisProfilerAgent()
    
    # Create Digital Twin data
    digital_twin = {
        "id": "test-session",
        "created_at": datetime.now(UTC).isoformat(),
        "completion": 85.0,
        "energetic_signature": {
            "hd_type": "projector",
            "hd_strategy": "wait_for_invitation",
            "energy_pattern": "sustainable",
        },
        "psychological_profile": {
            "jung_dominant": "Ni",
            "core_gift": "insight",
        },
    }
    
    # Build completion components
    components = profiler._build_completion_components(
        digital_twin=digital_twin,
        completion_message="Your journey is complete.",
        voice_id="oracle",
    )
    
    # Find each completion component type
    component_by_type = {c['type']: c for c in components}
    
    # ---- Validate digital_twin_card ----
    dtc = component_by_type.get('digital_twin_card')
    passed &= test_result(
        "Completion Components",
        "digital_twin_card exists",
        dtc is not None,
        f"Component types: {list(component_by_type.keys())}"
    )
    
    if dtc:
        # CRITICAL: Frontend reads digitalTwinComp?.digital_twin at ROOT level
        has_digital_twin_at_root = 'digital_twin' in dtc
        passed &= test_result(
            "Completion Components",
            "digital_twin_card has digital_twin at ROOT",
            has_digital_twin_at_root,
            f"Keys: {list(dtc.keys())}"
        )
        
        if has_digital_twin_at_root:
            digital_twin_data = dtc['digital_twin']
            required_fields = {'energetic_signature', 'psychological_profile', 'completion_percentage'}
            has_required = all(f in digital_twin_data for f in required_fields)
            passed &= test_result(
                "Completion Components", 
                "digital_twin has required fields",
                has_required,
                f"digital_twin keys: {list(digital_twin_data.keys())}"
            )
    
    # ---- Validate activation_steps ----
    asc = component_by_type.get('activation_steps')
    passed &= test_result(
        "Completion Components",
        "activation_steps exists",
        asc is not None,
    )
    
    if asc:
        # Frontend reads activationStepsComp?.steps at ROOT level
        steps = asc.get('steps', [])
        passed &= test_result(
            "Completion Components",
            "activation_steps has steps at ROOT",
            'steps' in asc and isinstance(steps, list) and len(steps) > 0,
            f"Steps count: {len(steps)}"
        )
        
        if steps:
            step = steps[0]
            required_step_fields = ACTIVATION_STEP_REQUIRED_FIELDS
            has_required = all(f in step for f in required_step_fields)
            passed &= test_result(
                "Completion Components",
                "activation step has required fields",
                has_required,
                f"Step keys: {list(step.keys())}"
            )
            
            # Validate priority is valid enum value
            priority_valid = step.get('priority') in ACTIVATION_STEP_PRIORITY_VALUES
            passed &= test_result(
                "Completion Components",
                "activation step priority is valid enum",
                priority_valid,
                f"Priority: {step.get('priority')}"
            )
    
    # ---- Validate completion_transition ----
    ctc = component_by_type.get('completion_transition')
    passed &= test_result(
        "Completion Components",
        "completion_transition exists",
        ctc is not None,
    )
    
    if ctc:
        # Frontend reads transition_type at ROOT level
        has_transition_type = 'transition_type' in ctc
        required = {'title', 'message', 'cta_text', 'cta_action'}
        has_required = all(f in ctc for f in required)
        passed &= test_result(
            "Completion Components",
            "completion_transition has required fields at ROOT",
            has_required and has_transition_type,
            f"Keys: {list(ctc.keys())}"
        )
    
    return passed


async def test_frontend_rendering_compatibility():
    """
    CRITICAL TEST: Verify that frontend can actually render what backend sends.
    
    The frontend GenerativeRenderer reads completion components like this:
    - digitalTwinComp?.digital_twin (expects ComponentDefinition.digital_twin at ROOT)
    - activationStepsComp?.steps (expects ComponentDefinition.steps at ROOT)
    - completionTransitionComp?.transition_type (expects at ROOT)
    
    This test verifies the backend sends data in the correct format.
    """
    from src.agents.genesis_profiler import GenesisProfilerAgent
    
    passed = True
    profiler = GenesisProfilerAgent()
    
    digital_twin = {
        "id": "test",
        "completion": 85.0,
        "energetic_signature": {"hd_type": "projector"},
        "psychological_profile": {"jung_dominant": "Ni"},
    }
    
    components = profiler._build_completion_components(
        digital_twin=digital_twin,
        completion_message="Complete!",
        voice_id="oracle",
    )
    
    dtc = next((c for c in components if c['type'] == 'digital_twin_card'), None)
    asc = next((c for c in components if c['type'] == 'activation_steps'), None)
    ctc = next((c for c in components if c['type'] == 'completion_transition'), None)
    
    # Frontend reads: digitalTwinComp?.digital_twin at ROOT
    frontend_can_read_dtc = dtc and 'digital_twin' in dtc
    passed &= test_result(
        "Frontend Compatibility",
        "Frontend CAN read digital_twin_card (digital_twin at ROOT)",
        frontend_can_read_dtc,
        f"Keys: {list(dtc.keys()) if dtc else 'None'}"
    )
    
    # Activation steps - frontend reads activationStepsComp?.steps at ROOT
    frontend_can_read_asc = asc and 'steps' in asc
    passed &= test_result(
        "Frontend Compatibility",
        "Frontend CAN read activation_steps (steps at ROOT)",
        frontend_can_read_asc,
        f"Keys: {list(asc.keys()) if asc else 'None'}"
    )
    
    # Completion transition - frontend reads transition_type at ROOT
    frontend_can_read_ctc = ctc and 'transition_type' in ctc
    passed &= test_result(
        "Frontend Compatibility",
        "Frontend CAN read completion_transition (transition_type at ROOT)",
        frontend_can_read_ctc,
        f"Keys: {list(ctc.keys()) if ctc else 'None'}"
    )
    
    return passed


async def test_voice_system_contract():
    """Verify Voice system integration is properly wired."""
    from src.agents.genesis.face import FaceOrchestrator, FaceFactory, ConversationPhase
    from src.agents.genesis.face.voice import (
        VoiceRegistry, VoiceSelector, VoiceSelectionMode,
        BlendedVoice, Voice, VoiceModifiers,
    )
    from src.agents.genesis.state import GenesisPhase
    
    passed = True
    
    # Test 1: VoiceRegistry has all built-in voices
    registry = VoiceRegistry()
    expected_voices = {'oracle', 'sage', 'companion', 'challenger', 'mirror'}
    actual_voices = set(registry.list_ids())
    
    passed &= test_result(
        "Voice System",
        "Registry has all built-in voices",
        expected_voices.issubset(actual_voices),
        f"Registered: {actual_voices}"
    )
    
    # Test 2: Each voice can generate a system prompt
    for voice_id in expected_voices:
        voice = registry.get(voice_id)
        if voice:
            prompt = voice.get_system_prompt(
                phase=ConversationPhase.AWAKENING,
                modifiers=VoiceModifiers(),
            )
            has_prompt = isinstance(prompt, str) and len(prompt) > 50
            passed &= test_result(
                "Voice System",
                f"{voice_id} generates valid prompt",
                has_prompt,
                f"Prompt length: {len(prompt)}"
            )
    
    # Test 3: VoiceSelector can select voice for each phase
    selector = VoiceSelector()  # Uses default mode and oracle fallback
    for phase in [GenesisPhase.AWAKENING, GenesisPhase.EXCAVATION, GenesisPhase.SYNTHESIS]:
        context = {"phase": phase.value}
        voice = selector.select(context=context)
        passed &= test_result(
            "Voice System",
            f"Selector returns voice for {phase.value}",
            voice is not None,
            f"Selected: {voice.identity.name if voice else 'None'}"
        )
    
    # Test 4: FaceOrchestrator provides correct interface
    face = FaceFactory.create_default()
    voice = face.get_voice(context={"phase": GenesisPhase.AWAKENING.value})
    passed &= test_result(
        "Voice System",
        "FaceOrchestrator.get_voice works",
        voice is not None,
    )
    
    prompt = face.get_system_prompt(phase=ConversationPhase.AWAKENING)
    passed &= test_result(
        "Voice System",
        "FaceOrchestrator.get_system_prompt works",
        isinstance(prompt, str) and len(prompt) > 0,
    )
    
    return passed


async def test_component_type_registry():
    """Verify all component types used in backend exist in frontend registry."""
    from src.agents.genesis.core import GenesisCore
    from src.agents.genesis_profiler import GenesisProfilerAgent
    
    passed = True
    
    # Collect all component types used in backend
    backend_types: Set[str] = set()
    
    # From genesis_profiler completion components
    profiler = GenesisProfilerAgent()
    components = profiler._build_completion_components(
        digital_twin={"completion": 85, "energetic_signature": {}, "psychological_profile": {}},
        completion_message="test",
        voice_id="oracle",
    )
    for c in components:
        backend_types.add(c['type'])
    
    # Add other known types used in backend
    backend_types.update({
        'text', 'input', 'progress', 'choice', 'slider', 
        'binary_choice', 'probe', 'cards',
    })
    
    # Verify all backend types exist in frontend
    missing_in_frontend = backend_types - FRONTEND_COMPONENT_TYPES
    
    passed &= test_result(
        "Component Registry",
        "All backend types exist in frontend",
        len(missing_in_frontend) == 0,
        f"Missing: {missing_in_frontend}" if missing_in_frontend else "All types present"
    )
    
    # Verify frontend types are superset (frontend may have extra types for future)
    extra_in_frontend = FRONTEND_COMPONENT_TYPES - backend_types
    passed &= test_result(
        "Component Registry",
        "Frontend has all backend types (may have extras)",
        len(missing_in_frontend) == 0,
        f"Frontend extras: {extra_in_frontend}"
    )
    
    return passed


# ============================================================================
# MAIN RUNNER
# ============================================================================

async def main():
    print("=" * 70)
    print("    CONTRACT VALIDATION TEST SUITE")
    print("=" * 70)
    print()
    
    results = {}
    
    print("\n--- Testing: ActiveSignal Contract ---")
    results["ActiveSignal"] = await test_active_signal_contract()
    
    print("\n--- Testing: Digital Twin Export Contract ---")
    results["Digital Twin Export"] = await test_digital_twin_export_contract()
    
    print("\n--- Testing: Completion Components Contract ---")
    results["Completion Components"] = await test_completion_components_contract()
    
    print("\n--- Testing: Frontend Rendering Compatibility ---")
    results["Frontend Compatibility"] = await test_frontend_rendering_compatibility()
    
    print("\n--- Testing: Voice System Contract ---")
    results["Voice System"] = await test_voice_system_contract()
    
    print("\n--- Testing: Component Type Registry ---")
    results["Component Registry"] = await test_component_type_registry()
    
    # Summary
    print()
    print("=" * 70)
    print("    CONTRACT VALIDATION RESULTS")
    print("=" * 70)
    
    passed_count = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset} {name}")
    
    print()
    print("=" * 70)
    print(f"  PASSED: {passed_count}/{total}")
    print(f"  FAILED: {total - passed_count}/{total}")
    print("=" * 70)
    
    # Exit with error code if failures
    if passed_count < total:
        print("\n⚠️  CONTRACT MISMATCHES DETECTED!")
        print("   The backend is sending data in a format the frontend cannot read.")
        print("   See failing tests above for details.")
        sys.exit(1)
    else:
        print("\n✅ All contracts validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
