"""
Genesis Graph - The Neural Wiring

This module wires together the Genesis fractal using LangGraph:
- GenesisCore (the Face)
- GenesisProfiler (the Scout)  
- HypothesisEngine (the Logic)
- ProfileRubric (the Memory)

The graph implements a stateful workflow that:
1. Receives user input
2. Runs silent analysis (Profiler)
3. Updates hypotheses
4. Decides: Probe or Continue?
5. Generates response
6. Checks phase transitions
7. Loops until profile complete

Graph Structure:
    [input] → [analyze] → [hypothesize] → [decide] → [respond] → [check_phase] → [output]
                  ↑                            ↓
                  └────────── [probe] ←────────┘
"""

from typing import TypedDict, Annotated, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging
import operator

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .state import GenesisState, GenesisPhase
from .core import GenesisCore, GenesisResponse
from .profiler import GenesisProfiler, Signal
from .hypothesis import HypothesisEngine, Hypothesis
from ...shared.protocol import SovereignPacket, InsightType, TargetLayer
from ...core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# GRAPH STATE
# =============================================================================

class GenesisGraphState(TypedDict):
    """
    The state that flows through the Genesis graph.
    
    Using TypedDict for LangGraph compatibility.
    """
    # Session identity
    session_id: str
    
    # User input for this turn
    user_input: str
    
    # Accumulated messages (LangGraph-style)
    messages: Annotated[list, add_messages]
    
    # Current phase
    phase: str
    
    # Genesis internal state (serialized)
    genesis_state_dict: dict
    
    # Detected signals from this turn
    signals: list[dict]
    
    # Current hypotheses
    hypotheses: list[dict]
    
    # The response to send
    response: Optional[dict]
    
    # Whether we're probing
    is_probing: bool
    
    # Profile completion percentage
    completion: float
    
    # Should we continue or end?
    should_continue: bool


# =============================================================================
# GRAPH NODES
# =============================================================================

def create_genesis_graph():
    """
    Create the Genesis LangGraph workflow.
    
    Returns a compiled graph that can be invoked with:
        result = graph.invoke({"user_input": "...", "session_id": "..."})
    """
    
    # Initialize the components (these will be shared across invocations)
    # In production, you'd want to make these stateless or use a factory
    core = GenesisCore()
    
    # --- NODE: Initialize ---
    def initialize(state: GenesisGraphState) -> GenesisGraphState:
        """Initialize or restore session state."""
        session_id = state.get("session_id") or str(uuid4())
        
        # Restore or create genesis state
        state_dict = state.get("genesis_state_dict", {})
        if state_dict:
            genesis_state = GenesisState.from_dict(state_dict)
        else:
            genesis_state = GenesisState(session_id=session_id)
        
        logger.info(f"[Genesis Graph] Initialize - session={session_id}, phase={genesis_state.phase.value}")
        
        return {
            **state,
            "session_id": session_id,
            "phase": genesis_state.phase.value,
            "genesis_state_dict": genesis_state.to_dict(),
            "signals": [],
            "hypotheses": [],
            "response": None,
            "is_probing": False,
            "completion": genesis_state.rubric.get_completion_percentage(),
            "should_continue": True,
        }
    
    # --- NODE: Analyze ---
    def analyze(state: GenesisGraphState) -> GenesisGraphState:
        """Run the Profiler to detect signals in user input."""
        genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
        user_input = state.get("user_input", "")
        
        if not user_input:
            return state
        
        # Run profiler analysis
        profiler = core.profiler
        signals = profiler.analyze_message(user_input, genesis_state)
        
        # Serialize signals
        signal_dicts = [s.to_dict() for s in signals]
        
        logger.info(f"[Genesis Graph] Analyze - detected {len(signals)} signals")
        
        return {
            **state,
            "signals": signal_dicts,
            "genesis_state_dict": genesis_state.to_dict(),
        }
    
    # --- NODE: Hypothesize ---
    def hypothesize(state: GenesisGraphState) -> GenesisGraphState:
        """Convert signals into hypotheses."""
        signals = state.get("signals", [])
        
        for signal in signals:
            suggested_traits = signal.get("suggested_traits", {})
            confidence = signal.get("confidence", 0.5)
            content = signal.get("content", "")
            
            for trait, value in suggested_traits.items():
                core.hypothesis_engine.add_hypothesis(
                    trait_name=trait,
                    suspected_value=value,
                    confidence=confidence * 0.7,
                    evidence=[content],
                )
        
        # Get current hypotheses summary
        hypotheses = core.hypothesis_engine.get_summary()["hypotheses"]
        
        logger.info(f"[Genesis Graph] Hypothesize - {len(hypotheses)} active hypotheses")
        
        return {
            **state,
            "hypotheses": hypotheses,
        }
    
    # --- NODE: Decide ---
    def decide(state: GenesisGraphState) -> GenesisGraphState:
        """Decide whether to probe or continue conversation."""
        genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
        
        # Check if we should probe
        top_hypotheses = core.hypothesis_engine.get_top_hypotheses(limit=1)
        should_probe = False
        
        if top_hypotheses:
            # Probe more aggressively in MAPPING phase
            if genesis_state.phase == GenesisPhase.MAPPING:
                should_probe = True
            # Probe occasionally in other phases
            elif len(genesis_state.memory.messages) % 3 == 0:
                should_probe = True
        
        logger.info(f"[Genesis Graph] Decide - should_probe={should_probe}")
        
        return {
            **state,
            "is_probing": should_probe,
        }
    
    # --- NODE: Generate Probe ---
    def generate_probe(state: GenesisGraphState) -> GenesisGraphState:
        """Generate a probe question."""
        genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
        
        probe_packet = core.hypothesis_engine.generate_probe(genesis_state)
        
        if probe_packet:
            probe_data = probe_packet.payload.get("probe", {})
            response = {
                "message": probe_data.get("prompt", "Tell me more..."),
                "components": [{
                    "type": "probe",
                    "probe_type": probe_data.get("probe_type", "confirmation"),
                    "prompt": probe_data.get("prompt", ""),
                    "options": probe_data.get("options", []),
                }],
                "phase": genesis_state.phase.value,
                "is_probe": True,
            }
        else:
            # Fallback to normal response
            response = None
        
        logger.info(f"[Genesis Graph] Generate Probe - created probe")
        
        return {
            **state,
            "response": response,
            "genesis_state_dict": genesis_state.to_dict(),
        }
    
    # --- NODE: Generate Response ---
    def generate_response(state: GenesisGraphState) -> GenesisGraphState:
        """Generate a conversational response."""
        genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
        user_input = state.get("user_input", "")
        
        # Skip if we already have a probe response
        if state.get("response") and state["response"].get("is_probe"):
            return state
        
        # Process the message through the core
        genesis_response = core.process_message(user_input, genesis_state)
        
        response = {
            "message": genesis_response.message,
            "components": genesis_response.components,
            "phase": genesis_response.phase.value,
            "is_probe": False,
        }
        
        logger.info(f"[Genesis Graph] Generate Response - phase={genesis_response.phase.value}")
        
        return {
            **state,
            "response": response,
            "phase": genesis_state.phase.value,
            "genesis_state_dict": genesis_state.to_dict(),
        }
    
    # --- NODE: Check Phase ---
    def check_phase(state: GenesisGraphState) -> GenesisGraphState:
        """Check for phase transitions and completion."""
        genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
        
        completion = genesis_state.rubric.get_completion_percentage()
        should_continue = completion < 100 and genesis_state.phase != GenesisPhase.ACTIVATION
        
        logger.info(f"[Genesis Graph] Check Phase - completion={completion}%, continue={should_continue}")
        
        return {
            **state,
            "completion": completion,
            "phase": genesis_state.phase.value,
            "should_continue": should_continue,
            "genesis_state_dict": genesis_state.to_dict(),
        }
    
    # --- NODE: Finalize ---
    def finalize(state: GenesisGraphState) -> GenesisGraphState:
        """Export the final Digital Twin if complete."""
        if not state.get("should_continue"):
            genesis_state = GenesisState.from_dict(state["genesis_state_dict"])
            digital_twin = core.export_digital_twin(genesis_state)
            
            state["response"]["digital_twin"] = digital_twin
            logger.info(f"[Genesis Graph] Finalize - exported Digital Twin")
        
        return state
    
    # --- ROUTING LOGIC ---
    def route_after_decide(state: GenesisGraphState) -> str:
        """Route based on whether we're probing."""
        if state.get("is_probing"):
            return "generate_probe"
        return "generate_response"
    
    def route_after_check(state: GenesisGraphState) -> str:
        """Route based on whether we should continue."""
        if state.get("should_continue"):
            return END  # Single turn complete, wait for next input
        return "finalize"
    
    # ==========================================================================
    # BUILD THE GRAPH
    # ==========================================================================
    
    graph = StateGraph(GenesisGraphState)
    
    # Add nodes
    graph.add_node("initialize", initialize)
    graph.add_node("analyze", analyze)
    graph.add_node("hypothesize", hypothesize)
    graph.add_node("decide", decide)
    graph.add_node("generate_probe", generate_probe)
    graph.add_node("generate_response", generate_response)
    graph.add_node("check_phase", check_phase)
    graph.add_node("finalize", finalize)
    
    # Set entry point
    graph.set_entry_point("initialize")
    
    # Add edges
    graph.add_edge("initialize", "analyze")
    graph.add_edge("analyze", "hypothesize")
    graph.add_edge("hypothesize", "decide")
    
    # Conditional: probe or respond?
    graph.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "generate_probe": "generate_probe",
            "generate_response": "generate_response",
        }
    )
    
    # Both paths lead to check_phase
    graph.add_edge("generate_probe", "check_phase")
    graph.add_edge("generate_response", "check_phase")
    
    # Conditional: continue or finalize?
    graph.add_conditional_edges(
        "check_phase",
        route_after_check,
        {
            END: END,
            "finalize": "finalize",
        }
    )
    
    graph.add_edge("finalize", END)
    
    # Compile
    compiled = graph.compile()
    
    return compiled


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global graph instance (compiled once)
_genesis_graph = None


def get_genesis_graph():
    """Get or create the global Genesis graph instance."""
    global _genesis_graph
    if _genesis_graph is None:
        _genesis_graph = create_genesis_graph()
    return _genesis_graph


async def run_genesis_turn(
    user_input: str,
    session_id: Optional[str] = None,
    previous_state: Optional[dict] = None,
) -> dict:
    """
    Run a single turn of the Genesis profiling conversation.
    
    Args:
        user_input: The user's message
        session_id: Session identifier (created if not provided)
        previous_state: Previous graph state (for continuity)
    
    Returns:
        dict with response, phase, completion, and state for next turn
    """
    graph = get_genesis_graph()
    
    # Build input state
    input_state = {
        "user_input": user_input,
        "session_id": session_id or str(uuid4()),
        "messages": [],
        "genesis_state_dict": previous_state.get("genesis_state_dict", {}) if previous_state else {},
    }
    
    # Run the graph
    result = await graph.ainvoke(input_state)
    
    return {
        "response": result.get("response", {}),
        "phase": result.get("phase", "awakening"),
        "completion": result.get("completion", 0),
        "hypotheses": result.get("hypotheses", []),
        "session_id": result.get("session_id"),
        "genesis_state_dict": result.get("genesis_state_dict", {}),
    }


def run_genesis_turn_sync(
    user_input: str,
    session_id: Optional[str] = None,
    previous_state: Optional[dict] = None,
) -> dict:
    """Synchronous version of run_genesis_turn."""
    graph = get_genesis_graph()
    
    input_state = {
        "user_input": user_input,
        "session_id": session_id or str(uuid4()),
        "messages": [],
        "genesis_state_dict": previous_state.get("genesis_state_dict", {}) if previous_state else {},
    }
    
    result = graph.invoke(input_state)
    
    return {
        "response": result.get("response", {}),
        "phase": result.get("phase", "awakening"),
        "completion": result.get("completion", 0),
        "hypotheses": result.get("hypotheses", []),
        "session_id": result.get("session_id"),
        "genesis_state_dict": result.get("genesis_state_dict", {}),
    }
