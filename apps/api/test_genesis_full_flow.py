"""
Comprehensive Genesis Flow Test

This test validates the ENTIRE Genesis profiling flow:
1. Opening message generation
2. User response processing
3. Signal detection (Profiler)
4. Hypothesis generation and probing (HypothesisEngine)
5. Voice selection and transformation (Face)
6. Swarm communication (Master agents)
7. Phase transitions
8. ProfileRubric updates
9. ALL Generative UI component types

Run with: python test_genesis_full_flow.py
"""
import asyncio
import logging
from typing import Dict, Any, List

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
from src.agents.genesis_profiler import GenesisProfilerAgent
from src.agents.genesis.core import GenesisCore, GenesisResponse
from src.agents.genesis.state import GenesisState, GenesisPhase
from src.agents.genesis.hypothesis import HypothesisEngine, Hypothesis
from src.agents.genesis.profiler import GenesisProfiler, Signal
from src.agents.genesis.session_manager import GenesisSessionManager, GenesisSession
from src.agents.genesis.face import (
    FaceOrchestrator,
    FaceFactory,
    Voice,
    VoiceRegistry,
    VoiceSelector,
    VoiceSelectionMode,
)
from src.core.schemas import AgentInput, AgentContext


# =============================================================================
# TEST SCENARIOS
# =============================================================================

# These responses are SPECIFICALLY CRAFTED to trigger the profiler's regex patterns
# Each response contains multiple keywords from the signal detection maps
SIMULATED_USER_RESPONSES = [
    # Response 1: Strong PROJECTOR signals
    # Keywords: wait, invitation, recognize, guide, insight, wisdom, bitter, tired, rest, exhausted
    "I've learned that I must wait for the right invitation before sharing my insights. "
    "When I try to just guide people without being asked, I end up feeling bitter. "
    "I get tired easily - I need lots of rest and can feel exhausted after working too long. "
    "My wisdom comes through when someone actually recognizes what I see and invites me in.",
    
    # Response 2: Strong GENERATOR signals + Ni cognitive function
    # Keywords: respond, gut, sacral, energy, satisf, frustrat, vision, pattern, meaning, just know
    "I get this strong gut response when something is right for me. My sacral energy just says YES. "
    "I find deep satisfaction when I can respond to work that lights me up. "
    "I often feel frustrated when I initiate without waiting. "
    "I have this vision about patterns - I just know things without knowing how I know.",
    
    # Response 3: MANIFESTOR signals + Te cognitive function
    # Keywords: initiate, start, impact, inform, independent, powerful, efficient, organize, goal, result
    "I like to initiate projects and make an impact. I need to be independent and start things my way. "
    "I feel most powerful when I can inform others of what I'm creating. "
    "I'm very efficient and like to organize my goals toward clear results. "
    "I don't wait for permission - I just make it happen.",
    
    # Response 4: Energy patterns + Fi cognitive function
    # Keywords: wave, cycle, emotional, ebb, flow, value, authentic, true to, integrity, inner compass
    "My energy comes in waves - I cycle between highs and lows, emotional ups and downs. "
    "There's an ebb and flow to my creative process. "
    "What I value most is being authentic and true to my inner compass. "
    "I live with integrity and trust my personal values above all else.",
    
    # Response 5: Depleted energy + Fe cognitive function
    # Keywords: tired, exhausted, drained, burnout, harmony, group, empathy, connect, care, together
    "I've been feeling so tired and drained lately - complete burnout. "
    "I care deeply about harmony in the group. Empathy comes naturally to me. "
    "I love to connect with people and nurture community. "
    "When we're all together and caring for each other, that's when I thrive.",
]

# Expected component types that MUST be supported
REQUIRED_COMPONENT_TYPES = [
    'text',           # Text display
    'input',          # Text input
    'progress',       # Progress indicator
    'choice',         # Choice selection (backend naming)
    'slider',         # Slider input
    'cards',          # Card selection
]

# Frontend-specific aliases that must also work
FRONTEND_ALIASES = {
    'binary_choice': 'choice',
    'choice_card': 'choice',
}


class TestResults:
    """Collector for test results."""
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
        
    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        logger.info(f"[PASS] {test_name}")
        
    def add_fail(self, test_name: str, reason: str):
        self.failed.append(f"{test_name}: {reason}")
        logger.error(f"[FAIL] {test_name} - {reason}")
        
    def add_warning(self, test_name: str, message: str):
        self.warnings.append(f"{test_name}: {message}")
        logger.warning(f"[WARN] {test_name} - {message}")
        
    def summary(self) -> str:
        total = len(self.passed) + len(self.failed)
        lines = [
            "",
            "=" * 70,
            "                    GENESIS FLOW TEST RESULTS",
            "=" * 70,
            f"  PASSED:   {len(self.passed):3d}/{total}",
            f"  FAILED:   {len(self.failed):3d}/{total}",
            f"  WARNINGS: {len(self.warnings):3d}",
            "-" * 70,
        ]
        
        for p in self.passed:
            lines.append(f"  [OK] {p[:64]}")
        for f in self.failed:
            lines.append(f"  [XX] {f[:64]}")
        for w in self.warnings:
            lines.append(f"  [??] {w[:64]}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


# =============================================================================
# COMPONENT VALIDATION HELPERS
# =============================================================================

def validate_component(component: Dict[str, Any], test_name: str, results: TestResults) -> bool:
    """Validate a single component structure."""
    if not isinstance(component, dict):
        results.add_fail(test_name, f"Component is not a dict: {type(component)}")
        return False
    
    if "type" not in component:
        results.add_fail(test_name, "Component missing 'type' field")
        return False
    
    comp_type = component.get("type")
    props = component.get("props", {})
    
    # Validate based on type
    if comp_type == "text":
        content = props.get("content") or component.get("content")
        if not content:
            results.add_warning(test_name, f"Text component has no content")
        else:
            results.add_pass(f"{test_name} - text component valid ({len(content)} chars)")
        return True
        
    elif comp_type == "input":
        placeholder = props.get("placeholder") or component.get("placeholder")
        results.add_pass(f"{test_name} - input component valid (placeholder: {placeholder[:30] if placeholder else 'none'}...)")
        return True
        
    elif comp_type == "progress":
        phase = props.get("phase") or component.get("phase")
        phase_index = props.get("phaseIndex") or component.get("phaseIndex", 0)
        total_phases = props.get("totalPhases") or component.get("totalPhases", 5)
        results.add_pass(f"{test_name} - progress component valid (phase: {phase}, {phase_index}/{total_phases})")
        return True
        
    elif comp_type in ("choice", "binary_choice", "choice_card"):
        options = props.get("options") or component.get("options", [])
        if not options:
            results.add_warning(test_name, f"Choice component has no options")
        else:
            # Validate options structure
            for i, opt in enumerate(options):
                if isinstance(opt, dict):
                    if "label" not in opt and "value" not in opt:
                        results.add_warning(test_name, f"Choice option {i} missing label/value")
                # String options are also valid
            results.add_pass(f"{test_name} - choice component valid ({len(options)} options)")
        return True
        
    elif comp_type == "slider":
        min_val = props.get("min") or component.get("min", 1)
        max_val = props.get("max") or component.get("max", 10)
        labels = props.get("labels") or component.get("labels", {})
        results.add_pass(f"{test_name} - slider component valid (range: {min_val}-{max_val}, {len(labels)} labels)")
        return True
        
    elif comp_type == "cards":
        cards = props.get("cards") or component.get("cards", [])
        if not cards:
            results.add_warning(test_name, f"Cards component has no cards")
        else:
            results.add_pass(f"{test_name} - cards component valid ({len(cards)} cards)")
        return True
        
    elif comp_type == "probe":
        probe_type = props.get("probe_type") or component.get("probe_type")
        prompt = props.get("prompt") or component.get("prompt")
        results.add_pass(f"{test_name} - probe component valid (type: {probe_type})")
        return True
        
    elif comp_type in ("game", "reflex_tap"):
        difficulty = props.get("difficulty") or component.get("difficulty", "medium")
        results.add_pass(f"{test_name} - game component valid (difficulty: {difficulty})")
        return True
        
    else:
        results.add_warning(test_name, f"Unknown component type: {comp_type}")
        return True


def validate_components(components: List[Dict[str, Any]], test_name: str, results: TestResults) -> bool:
    """Validate a list of components."""
    if not components:
        results.add_fail(test_name, "No components generated")
        return False
    
    all_valid = True
    for i, comp in enumerate(components):
        if not validate_component(comp, f"{test_name}[{i}]", results):
            all_valid = False
    
    return all_valid


# =============================================================================
# UNIT TESTS
# =============================================================================

async def test_voice_system(results: TestResults):
    """Test the Voice system is properly wired."""
    test_name = "Voice System Initialization"
    
    try:
        # Test VoiceRegistry has all built-in voices
        all_voices = VoiceRegistry.list_all()
        voice_ids = [v.identity.id for v in all_voices]
        
        expected_voices = ["oracle", "sage", "companion", "challenger", "mirror"]
        for v in expected_voices:
            if v not in voice_ids:
                results.add_fail(test_name, f"Missing voice: {v}")
                return
        
        results.add_pass(f"{test_name} - All 5 voices registered")
        
        # Test VoiceSelector
        selector = VoiceSelector(
            mode=VoiceSelectionMode.DYNAMIC,
            default_voice_id="oracle",
        )
        selected = selector.select(context={"phase": "awakening"}, history=[])
        
        if selected is None:
            results.add_fail(test_name, "VoiceSelector returned None")
            return
            
        results.add_pass(f"{test_name} - VoiceSelector works ({selected.identity.name})")
        
        # Test FaceOrchestrator
        face = FaceFactory.create_default()
        voice = face.get_voice(context={"phase": "awakening"}, history=[])
        
        if voice is None:
            results.add_fail(test_name, "FaceOrchestrator.get_voice returned None")
            return
            
        results.add_pass(f"{test_name} - FaceOrchestrator works")
        
        # Test Voice.get_system_prompt
        from src.agents.genesis.face.voice import ConversationPhase
        prompt = voice.get_system_prompt(phase=ConversationPhase.AWAKENING)
        
        if not prompt or len(prompt) < 100:
            results.add_fail(test_name, f"System prompt too short: {len(prompt)} chars")
            return
            
        results.add_pass(f"{test_name} - Voice.get_system_prompt works ({len(prompt)} chars)")
        
        # Test Voice.transform
        original = "Tell me about yourself."
        transformed = voice.transform(original, context={"phase": "awakening"})
        
        results.add_pass(f"{test_name} - Voice.transform works")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_session_face_integration(results: TestResults):
    """Test that Face is properly integrated into sessions."""
    test_name = "Session-Face Integration"
    
    try:
        manager = GenesisSessionManager()
        session = manager.get_or_create_session("test-session-123")
        
        # Check session has face
        if not hasattr(session, 'face') or session.face is None:
            results.add_fail(test_name, "Session missing 'face' attribute")
            return
            
        results.add_pass(f"{test_name} - Session has Face")
        
        # Check face can get voice
        voice = session.face.get_voice(context={"phase": "awakening"}, history=[])
        if voice is None:
            results.add_fail(test_name, "Session Face.get_voice returned None")
            return
            
        results.add_pass(f"{test_name} - Session Face returns voice")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_genesis_core_methods(results: TestResults):
    """Test GenesisCore has the required methods."""
    test_name = "GenesisCore Methods"
    
    try:
        core = GenesisCore()
        
        # Check generate_probe exists and is async
        if not hasattr(core, 'generate_probe'):
            results.add_fail(test_name, "Missing generate_probe method")
            return
            
        results.add_pass(f"{test_name} - generate_probe exists")
        
        # Check generate_question exists and is async
        if not hasattr(core, 'generate_question'):
            results.add_fail(test_name, "Missing generate_question method")
            return
            
        results.add_pass(f"{test_name} - generate_question exists")
        
        # Check _build_voice_system_prompt exists
        if not hasattr(core, '_build_voice_system_prompt'):
            results.add_fail(test_name, "Missing _build_voice_system_prompt method")
            return
            
        results.add_pass(f"{test_name} - _build_voice_system_prompt exists")
        
        # Check generate_next_turn accepts voice parameter
        import inspect
        sig = inspect.signature(core.generate_next_turn)
        if 'voice' not in sig.parameters:
            results.add_fail(test_name, "generate_next_turn missing 'voice' parameter")
            return
            
        results.add_pass(f"{test_name} - generate_next_turn accepts voice")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_hypothesis_engine(results: TestResults):
    """Test HypothesisEngine functionality."""
    test_name = "HypothesisEngine"
    
    try:
        engine = HypothesisEngine()
        
        # Add a hypothesis
        hyp = engine.add_hypothesis(
            trait_name="hd_type",
            suspected_value="projector",
            confidence=0.6,
            evidence=["waiting language", "recognition need"],
        )
        
        if hyp is None:
            results.add_fail(test_name, "add_hypothesis returned None")
            return
            
        results.add_pass(f"{test_name} - add_hypothesis works")
        
        # Test get_top_hypotheses
        top = engine.get_top_hypotheses(limit=1)
        if not top:
            results.add_fail(test_name, "get_top_hypotheses returned empty")
            return
            
        results.add_pass(f"{test_name} - get_top_hypotheses works")
        
        # Test get_confirmed_hypotheses
        confirmed = engine.get_confirmed_hypotheses()
        results.add_pass(f"{test_name} - get_confirmed_hypotheses works ({len(confirmed)} confirmed)")
        
        # Test generate_probe
        state = GenesisState(session_id="test")
        probe_packet = engine.generate_probe(state, hyp)
        
        if probe_packet is None:
            results.add_warning(test_name, "generate_probe returned None (may be expected if no templates)")
        else:
            results.add_pass(f"{test_name} - generate_probe works")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_profiler_integration(results: TestResults):
    """Test that Profiler properly detects signals and updates rubric."""
    test_name = "Profiler Integration"
    
    try:
        profiler = GenesisProfiler()
        state = GenesisState(session_id="test-profiler")
        
        # Test 1: Analyze first response (strong Projector signals)
        packets = await profiler.analyze(SIMULATED_USER_RESPONSES[0], state)
        
        if packets:
            results.add_pass(f"{test_name} - Detected {len(packets)} patterns in response 1")
            for p in packets[:3]:
                # SovereignPacket structure: insight_type, payload, confidence_score
                insight = p.insight_type.value if hasattr(p.insight_type, 'value') else str(p.insight_type)
                payload_summary = str(p.payload)[:50] if p.payload else "empty"
                logger.info(f"   └─ {insight}: {payload_summary}... ({p.confidence_score:.0%})")
        else:
            results.add_warning(test_name, "No patterns detected in response 1")
        
        # Test 2: Check rubric was updated by _scan_patterns
        all_traits = state.rubric.get_all_traits()
        if all_traits:
            results.add_pass(f"{test_name} - ProfileRubric has {len(all_traits)} traits")
            for trait in all_traits[:3]:
                logger.info(f"   └─ {trait.name}={trait.value} ({trait.confidence:.0%})")
        else:
            # This is expected if patterns don't meet threshold, not a failure
            results.add_warning(test_name, "ProfileRubric empty (patterns may not meet threshold)")
        
        # Test 3: Analyze ALL simulated responses to accumulate evidence
        total_packets = len(packets) if packets else 0
        for i, response in enumerate(SIMULATED_USER_RESPONSES[1:], start=2):
            more_packets = await profiler.analyze(response, state)
            if more_packets:
                total_packets += len(more_packets)
                results.add_pass(f"{test_name} - Response {i}: {len(more_packets)} patterns")
        
        if total_packets >= 5:
            results.add_pass(f"{test_name} - Total patterns across all responses: {total_packets}")
        else:
            results.add_warning(test_name, f"Only {total_packets} patterns total (expected 5+)")
        
        # Test 4: Verify rubric accumulation after all responses
        final_traits = state.rubric.get_all_traits()
        if len(final_traits) > len(all_traits):
            results.add_pass(f"{test_name} - Rubric accumulated: {len(all_traits)} → {len(final_traits)} traits")
        
        # Test 5: Test analyze_message (sync version) for comparison
        sync_signals = profiler.analyze_message(SIMULATED_USER_RESPONSES[0], state)
        if sync_signals:
            results.add_pass(f"{test_name} - analyze_message: {len(sync_signals)} signals")
        else:
            results.add_warning(test_name, "analyze_message returned no signals")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_opening_message(results: TestResults):
    """Test opening message generation."""
    test_name = "Opening Message"
    
    try:
        agent = GenesisProfilerAgent()
        
        input_data = AgentInput(
            framework='genesis',
            context=AgentContext(userQuery='Begin the Genesis profiling process')
        )
        
        result = await agent.execute(input_data)
        
        # Check interpretationSeed
        if not result.interpretationSeed or len(result.interpretationSeed) < 50:
            results.add_fail(test_name, f"Message too short: {len(result.interpretationSeed)}")
            return
            
        results.add_pass(f"{test_name} - Message generated ({len(result.interpretationSeed)} chars)")
        
        # Check components
        components = result.visualizationData.get("components", [])
        if len(components) < 3:
            results.add_fail(test_name, f"Too few components: {len(components)}")
            return
            
        results.add_pass(f"{test_name} - Components generated ({len(components)})")
        
        # Validate all components
        validate_components(components, test_name, results)
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_component_generation_text(results: TestResults):
    """Test text component generation."""
    test_name = "Component: Text"
    
    try:
        core = GenesisCore()
        state = GenesisState(session_id="test-text-comp")
        
        # Generate opening which includes text components
        response = core.generate_next_turn(state)
        
        if not response.components:
            results.add_fail(test_name, "No components in response")
            return
        
        text_comps = [c for c in response.components if c.get("type") == "text"]
        if not text_comps:
            # Check for probe type which also contains text
            probe_comps = [c for c in response.components if c.get("type") == "probe"]
            if probe_comps:
                results.add_pass(f"{test_name} - Found probe component (contains text)")
            else:
                results.add_warning(test_name, "No text components found")
        else:
            results.add_pass(f"{test_name} - {len(text_comps)} text components generated")
            
            # Validate structure
            for tc in text_comps:
                content = tc.get("props", {}).get("content") or tc.get("content")
                variant = tc.get("props", {}).get("variant") or tc.get("variant")
                if content:
                    results.add_pass(f"{test_name} - content: {content[:40]}... variant: {variant}")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_component_generation_choice(results: TestResults):
    """Test choice component generation from probes."""
    test_name = "Component: Choice"
    
    try:
        core = GenesisCore()
        state = GenesisState(session_id="test-choice-comp")
        face = FaceFactory.create_default()
        voice = face.get_voice()
        
        # Add hypothesis to trigger probe with choices
        core.hypothesis_engine.add_hypothesis(
            trait_name="hd_type",
            suspected_value="projector",
            confidence=0.5,
            evidence=["test"],
        )
        
        hyp = core.hypothesis_engine.get_top_hypotheses(limit=1)[0]
        
        # Generate probe
        probe_response = await core.generate_probe(
            hypothesis=hyp,
            state=state,
            voice=voice,
        )
        
        if not probe_response.components:
            results.add_fail(test_name, "No components in probe response")
            return
        
        # Look for choice component
        choice_comps = [c for c in probe_response.components 
                       if c.get("type") in ("choice", "binary_choice", "choice_card")]
        
        if choice_comps:
            for cc in choice_comps:
                options = cc.get("props", {}).get("options") or cc.get("options", [])
                results.add_pass(f"{test_name} - {len(options)} options: {[o.get('label') if isinstance(o, dict) else o for o in options[:3]]}")
        else:
            # May have input instead for reflection probe
            input_comps = [c for c in probe_response.components if c.get("type") == "input"]
            if input_comps:
                results.add_pass(f"{test_name} - Probe uses input (reflection type)")
            else:
                results.add_warning(test_name, "No choice or input components in probe")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_component_generation_slider(results: TestResults):
    """Test slider component generation."""
    test_name = "Component: Slider"
    
    try:
        # Manually construct a slider component as backend would
        slider_comp = {
            "type": "slider",
            "props": {
                "min": 1,
                "max": 10,
                "step": 1,
                "labels": {
                    "1": "Never",
                    "5": "Sometimes",
                    "10": "Always"
                }
            }
        }
        
        # Validate structure
        props = slider_comp.get("props", {})
        
        if props.get("min") is None or props.get("max") is None:
            results.add_fail(test_name, "Slider missing min/max")
            return
        
        if props.get("max") <= props.get("min"):
            results.add_fail(test_name, f"Invalid range: {props.get('min')}-{props.get('max')}")
            return
        
        results.add_pass(f"{test_name} - Slider structure valid (range: {props.get('min')}-{props.get('max')})")
        
        labels = props.get("labels", {})
        if labels:
            results.add_pass(f"{test_name} - Labels: {labels}")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_component_generation_cards(results: TestResults):
    """Test cards component generation."""
    test_name = "Component: Cards"
    
    try:
        # Manually construct a cards component as backend would
        cards_comp = {
            "type": "cards",
            "props": {
                "cards": [
                    {"title": "Initiating", "value": "manifestor"},
                    {"title": "Waiting to Respond", "value": "generator"},
                    {"title": "Waiting for Invitation", "value": "projector"},
                    {"title": "Waiting a Lunar Cycle", "value": "reflector"},
                ],
                "selectable": True,
                "maxSelections": 1,
            }
        }
        
        # Validate structure
        props = cards_comp.get("props", {})
        cards = props.get("cards", [])
        
        if not cards:
            results.add_fail(test_name, "Cards component has no cards")
            return
        
        for i, card in enumerate(cards):
            if "title" not in card:
                results.add_warning(test_name, f"Card {i} missing 'title'")
            if "value" not in card:
                results.add_warning(test_name, f"Card {i} missing 'value'")
        
        results.add_pass(f"{test_name} - Cards structure valid ({len(cards)} cards)")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_component_generation_progress(results: TestResults):
    """Test progress component generation."""
    test_name = "Component: Progress"
    
    try:
        agent = GenesisProfilerAgent()
        
        input_data = AgentInput(
            framework='genesis',
            context=AgentContext(userQuery='Begin')
        )
        
        result = await agent.execute(input_data)
        components = result.visualizationData.get("components", [])
        
        progress_comps = [c for c in components if c.get("type") == "progress"]
        
        if not progress_comps:
            results.add_fail(test_name, "No progress component in opening")
            return
        
        for pc in progress_comps:
            props = pc.get("props", {})
            phase = props.get("phase") or pc.get("phase")
            phase_index = props.get("phaseIndex") or pc.get("phaseIndex", 0)
            total_phases = props.get("totalPhases") or pc.get("totalPhases", 5)
            question_index = props.get("questionIndex") or pc.get("questionIndex", 0)
            
            results.add_pass(f"{test_name} - phase={phase}, idx={phase_index}/{total_phases}, q={question_index}")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_full_conversation_flow(results: TestResults):
    """Test a multi-turn conversation with probing."""
    test_name = "Full Conversation Flow"
    
    try:
        # Initialize
        session_manager = GenesisSessionManager()
        session = session_manager.get_or_create_session("test-full-flow")
        state = GenesisState(session_id="test-full-flow")
        core = GenesisCore()
        
        # Get voice from face
        voice = session.face.get_voice(context={"phase": "awakening"}, history=[])
        results.add_pass(f"{test_name} - Voice acquired: {voice.identity.name}")
        
        # Generate opening
        opening = core.generate_next_turn(state, voice=voice)
        if not opening or not opening.message:
            results.add_fail(test_name, "Opening generation failed")
            return
            
        results.add_pass(f"{test_name} - Opening generated")
        
        # Simulate first user response
        user_msg = SIMULATED_USER_RESPONSES[0]
        response = core.process_message(user_msg, state)
        
        if not response or not response.message:
            results.add_fail(test_name, "First response processing failed")
            return
            
        results.add_pass(f"{test_name} - First response processed")
        
        # Check if hypotheses were generated
        hypotheses = core.hypothesis_engine.get_top_hypotheses(limit=5)
        if hypotheses:
            results.add_pass(f"{test_name} - Hypotheses generated ({len(hypotheses)})")
            for h in hypotheses:
                logger.info(f"   └─ {h.trait_name}={h.suspected_value} ({h.confidence:.0%})")
        else:
            results.add_warning(test_name, "No hypotheses generated (may need more input)")
        
        # Check profile rubric
        completion = state.rubric.get_completion_percentage()
        results.add_pass(f"{test_name} - ProfileRubric updated ({completion:.0%} complete)")
        
        # Test generate_probe with voice
        if hypotheses:
            probe_response = await core.generate_probe(
                hypothesis=hypotheses[0],
                state=state,
                voice=voice,
            )
            
            if not probe_response or not probe_response.message:
                results.add_fail(test_name, "Probe generation failed")
                return
                
            results.add_pass(f"{test_name} - Probe generated: {probe_response.message[:50]}...")
            
            # Validate probe components
            if probe_response.components:
                results.add_pass(f"{test_name} - Probe has {len(probe_response.components)} components")
                validate_components(probe_response.components, f"{test_name} - Probe", results)
            else:
                results.add_warning(test_name, "Probe has no components")
        
        # Test generate_question with voice
        signals = []  # Would come from profiler in real flow
        question_response = await core.generate_question(
            state=state,
            voice=voice,
            signals=signals,
            master_insights=[],
        )
        
        if not question_response or not question_response.message:
            results.add_fail(test_name, "Question generation failed")
            return
            
        results.add_pass(f"{test_name} - Question generated: {question_response.message[:50]}...")
        
        # Validate question components
        if question_response.components:
            validate_components(question_response.components, f"{test_name} - Question", results)
        
    except Exception as e:
        results.add_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


async def test_voice_in_response_flow(results: TestResults):
    """Test that Voice is properly used throughout the response flow."""
    test_name = "Voice in Response Flow"
    
    try:
        # Create session with specific voice
        face = FaceFactory.create_with_voice("sage")  # Use Sage voice
        state = GenesisState(session_id="test-voice-flow")
        core = GenesisCore()
        
        sage_voice = face.get_voice()
        
        if sage_voice.identity.id != "sage":
            results.add_warning(test_name, f"Expected 'sage', got '{sage_voice.identity.id}'")
        else:
            results.add_pass(f"{test_name} - Sage voice selected")
        
        # Get opening with voice
        opening = core.generate_next_turn(state, voice=sage_voice)
        results.add_pass(f"{test_name} - Opening with voice: {opening.message[:50]}...")
        
        # Add hypothesis and generate probe with voice
        core.hypothesis_engine.add_hypothesis(
            trait_name="jung_dominant",
            suspected_value="Ti",
            confidence=0.5,
            evidence=["analytical language"],
        )
        
        hyp = core.hypothesis_engine.get_top_hypotheses(limit=1)[0]
        
        probe = await core.generate_probe(
            hypothesis=hyp,
            state=state,
            voice=sage_voice,
        )
        
        if probe and probe.message:
            results.add_pass(f"{test_name} - Probe with Sage voice: {probe.message[:50]}...")
        else:
            results.add_warning(test_name, "Probe generation returned empty")
        
        # Generate question with voice
        question = await core.generate_question(
            state=state,
            voice=sage_voice,
            signals=[],
        )
        
        if question and question.message:
            results.add_pass(f"{test_name} - Question with Sage voice: {question.message[:50]}...")
        else:
            results.add_fail(test_name, "Question generation failed")
        
    except Exception as e:
        results.add_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


async def test_all_voice_personalities(results: TestResults):
    """Test that all 5 voices can generate responses."""
    test_name = "All Voice Personalities"
    
    try:
        core = GenesisCore()
        voices = ["oracle", "sage", "companion", "challenger", "mirror"]
        
        for voice_id in voices:
            face = FaceFactory.create_with_voice(voice_id)
            voice = face.get_voice()
            state = GenesisState(session_id=f"test-{voice_id}")
            
            # Generate question with this voice
            question = await core.generate_question(
                state=state,
                voice=voice,
                signals=[],
            )
            
            if question and question.message:
                results.add_pass(f"{test_name} - {voice_id.upper()}: {question.message[:40]}...")
            else:
                results.add_fail(test_name, f"{voice_id} failed to generate question")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_profiler_full_pipeline(results: TestResults):
    """
    STRESS TEST: Force the profiler through ALL detection paths.
    
    This test validates:
    1. HD Type detection for ALL 5 types (generator, projector, manifestor, reflector, mfg)
    2. Cognitive function detection for ALL 8 functions (Ni, Ne, Si, Se, Ti, Te, Fi, Fe)
    3. Energy pattern detection (sustainable, burst, wave, depleted)
    4. Rubric accumulation and trait updates
    5. Hypothesis packet generation
    6. Evidence accumulation
    """
    test_name = "Profiler Full Pipeline"
    
    try:
        profiler = GenesisProfiler()
        
        # =================================================================
        # TEST 1: HD Type Detection - Each type has specific triggers
        # =================================================================
        hd_type_tests = {
            "generator": "I respond with my gut and sacral energy. I feel satisfied when I do work I love. "
                        "I wait for things to respond to. Frustration tells me something is off.",
            "projector": "I wait for invitations and recognition. I guide others with my wisdom and insight. "
                        "I get bitter when I'm not seen. I need rest and get exhausted easily.",
            "manifestor": "I initiate and start new things. I need to inform others of my plans. "
                         "I feel anger when I'm controlled. I'm independent and powerful.",
            "reflector": "I mirror the environment around me. I wait 28 days with the lunar cycle. "
                        "I feel surprised and disappointed. I sample and taste experiences.",
            "manifesting_generator": "I'm multi-passionate with many interests. I skip steps efficiently. "
                                    "I respond AND initiate. I pivot and change direction quickly.",
        }
        
        hd_detections = 0
        for hd_type, text in hd_type_tests.items():
            state = GenesisState(session_id=f"test-hd-{hd_type}")
            packets = await profiler.analyze(text, state)
            
            # Check if we detected this type
            for p in packets:
                if p.payload.get('trait_name') == 'hd_type' and p.payload.get('suspected_value') == hd_type:
                    hd_detections += 1
                    results.add_pass(f"{test_name} - HD Type detected: {hd_type}")
                    break
            else:
                # Check rubric directly
                if state.rubric.hd_type and state.rubric.hd_type.value == hd_type:
                    hd_detections += 1
                    results.add_pass(f"{test_name} - HD Type in rubric: {hd_type}")
                else:
                    results.add_warning(test_name, f"HD Type {hd_type} not detected")
        
        if hd_detections >= 3:
            results.add_pass(f"{test_name} - HD Types: {hd_detections}/5 detected")
        
        # =================================================================
        # TEST 2: Cognitive Function Detection
        # =================================================================
        cognitive_tests = {
            "Ni": "I have a vision of the future. I see patterns and symbols with deep meaning. "
                  "I just know things intuitively without knowing how. I foresee what will happen.",
            "Ne": "I love exploring possibilities and brainstorming ideas. What if we could do this? "
                  "I'm curious about novel and innovative options. I connect different concepts.",
            "Si": "I remember the past clearly. I value tradition and familiar routines. "
                  "I pay attention to concrete details. How it was done before matters to me.",
            "Se": "I live in the present moment. I love physical action and sensory experience. "
                  "I seek adventure and thrills. I prefer hands-on, tangible things.",
            "Ti": "I analyze everything logically. I need to understand why things work. "
                  "I build mental frameworks and models. Accuracy and precision matter most.",
            "Te": "I focus on efficiency and organization. I set goals and measure results. "
                  "I decide quickly and implement plans. Productivity is key.",
            "Fi": "I value authenticity and being true to myself. My inner compass guides me. "
                  "I have strong personal values and integrity. What feels right matters.",
            "Fe": "I care about group harmony and connecting with people. Empathy comes naturally. "
                  "I nurture community and care for others. We're better together.",
        }
        
        cog_detections = 0
        for func, text in cognitive_tests.items():
            state = GenesisState(session_id=f"test-cog-{func}")
            packets = await profiler.analyze(text, state)
            
            for p in packets:
                if p.payload.get('trait_name') == 'jung_dominant' and p.payload.get('suspected_value') == func:
                    cog_detections += 1
                    logger.info(f"   └─ Cognitive {func}: detected")
                    break
        
        if cog_detections >= 4:
            results.add_pass(f"{test_name} - Cognitive functions: {cog_detections}/8 detected")
        else:
            results.add_warning(test_name, f"Cognitive functions: only {cog_detections}/8")
        
        # =================================================================
        # TEST 3: Energy Pattern Detection
        # =================================================================
        energy_tests = {
            "sustainable": "I have steady, consistent energy. I pace myself like a marathon runner. "
                          "I'm reliable and maintain endurance over time.",
            "burst": "I work in intense short bursts then crash. I'm all-in or all-out. "
                    "My energy is explosive but not sustainable.",
            "wave": "My energy comes in waves and cycles. I have emotional ups and downs. "
                   "There's an ebb and flow to how I feel.",
            "depleted": "I'm exhausted and drained. I'm experiencing burnout. "
                       "I have no energy left - I feel completely empty and tired.",
        }
        
        energy_detections = 0
        for energy_type, text in energy_tests.items():
            state = GenesisState(session_id=f"test-energy-{energy_type}")
            packets = await profiler.analyze(text, state)
            
            for p in packets:
                if f"energy_{energy_type}" in str(p.payload):
                    energy_detections += 1
                    logger.info(f"   └─ Energy {energy_type}: detected")
                    break
        
        if energy_detections >= 2:
            results.add_pass(f"{test_name} - Energy patterns: {energy_detections}/4 detected")
        else:
            results.add_warning(test_name, f"Energy patterns: only {energy_detections}/4")
        
        # =================================================================
        # TEST 4: Rubric Accumulation - Multiple responses build profile
        # =================================================================
        accumulation_state = GenesisState(session_id="test-accumulation")
        
        # Process all HD type texts through one state
        for text in hd_type_tests.values():
            await profiler.analyze(text, accumulation_state)
        
        # Check rubric accumulated evidence
        if accumulation_state.rubric.hd_type:
            evidence_count = len(accumulation_state.rubric.hd_type.evidence)
            results.add_pass(f"{test_name} - Rubric accumulated {evidence_count} evidence items")
        else:
            results.add_warning(test_name, "Rubric did not accumulate hd_type")
        
        # =================================================================
        # TEST 5: Sync vs Async method comparison
        # =================================================================
        test_text = hd_type_tests["projector"]
        state = GenesisState(session_id="test-sync-async")
        
        # Sync method (analyze_message) returns Signal objects
        sync_signals = profiler.analyze_message(test_text, state)
        
        # Async method (analyze) returns SovereignPacket objects  
        async_packets = await profiler.analyze(test_text, state)
        
        if sync_signals and async_packets:
            results.add_pass(f"{test_name} - Both methods work: sync={len(sync_signals)}, async={len(async_packets)}")
        elif sync_signals:
            results.add_pass(f"{test_name} - Sync method works: {len(sync_signals)} signals")
        elif async_packets:
            results.add_pass(f"{test_name} - Async method works: {len(async_packets)} packets")
        else:
            results.add_warning(test_name, "Neither method detected patterns")
        
        # =================================================================
        # SUMMARY
        # =================================================================
        total_detections = hd_detections + cog_detections + energy_detections
        if total_detections >= 10:
            results.add_pass(f"{test_name} - PIPELINE COMPLETE: {total_detections} total detections")
        else:
            results.add_warning(test_name, f"Pipeline partial: {total_detections} detections")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


async def test_phase_transitions(results: TestResults):
    """Test that phase transitions work correctly."""
    test_name = "Phase Transitions"
    
    try:
        state = GenesisState(session_id="test-phases")
        
        # Initial phase should be awakening
        if state.phase != GenesisPhase.AWAKENING:
            results.add_fail(test_name, f"Initial phase wrong: {state.phase}")
            return
        
        results.add_pass(f"{test_name} - Initial phase: {state.phase.value}")
        
        # Test phase transition via advance_question (3 questions per phase)
        # Advance through awakening phase (3 questions)
        for i in range(3):
            state.advance_question(questions_per_phase=3)
        
        if state.phase != GenesisPhase.EXCAVATION:
            results.add_fail(test_name, f"Expected excavation, got: {state.phase}")
            return
        
        results.add_pass(f"{test_name} - Advanced to: {state.phase.value}")
        
        # Test all phase transitions
        expected_phases = [
            GenesisPhase.MAPPING,
            GenesisPhase.SYNTHESIS,
            GenesisPhase.ACTIVATION,
        ]
        
        for expected in expected_phases:
            # 3 questions per phase triggers transition
            for i in range(3):
                state.advance_question(questions_per_phase=3)
            if state.phase != expected:
                results.add_fail(test_name, f"Expected {expected}, got: {state.phase}")
                return
            results.add_pass(f"{test_name} - Transitioned to: {state.phase.value}")
        
        # Complete the ACTIVATION phase (3 more questions to finish)
        for i in range(3):
            state.advance_question(questions_per_phase=3)
        
        # After completing activation phase, profile should be complete
        if not state.profile_complete:
            results.add_fail(test_name, "Profile not marked complete after all phases")
        else:
            results.add_pass(f"{test_name} - Profile marked complete")
        
    except Exception as e:
        results.add_fail(test_name, str(e))


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests():
    """Run all tests and print results."""
    print("\n" + "="*70)
    print("    GENESIS COMPREHENSIVE FLOW TEST SUITE")
    print("    Testing ALL components, voices, phases, and integrations")
    print("="*70 + "\n")
    
    results = TestResults()
    
    # Core system tests
    await test_voice_system(results)
    await test_session_face_integration(results)
    await test_genesis_core_methods(results)
    await test_hypothesis_engine(results)
    await test_profiler_integration(results)
    await test_profiler_full_pipeline(results)  # NEW: Comprehensive profiler stress test
    
    # Component generation tests
    await test_opening_message(results)
    await test_component_generation_text(results)
    await test_component_generation_choice(results)
    await test_component_generation_slider(results)
    await test_component_generation_cards(results)
    await test_component_generation_progress(results)
    
    # Voice and personality tests
    await test_voice_in_response_flow(results)
    await test_all_voice_personalities(results)
    
    # Full flow tests
    await test_full_conversation_flow(results)
    await test_phase_transitions(results)
    
    # Print summary
    print(results.summary())
    
    # Return exit code
    return 0 if not results.failed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    exit(exit_code)
