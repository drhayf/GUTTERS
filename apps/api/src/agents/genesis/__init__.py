"""
Genesis Agent - The Fractal Profiling System

The Genesis module is the "Gateway" to Project Sovereign - the initial
profiling system that builds the user's Digital Twin through deep,
penetrating questions and sophisticated pattern detection.

Architecture (The Fractal Pattern):
    genesis/
    ├── __init__.py         - This file (exports)
    ├── core.py             - The "Face" - Conversational interface
    ├── profiler.py         - The "Scout" - Silent pattern detection
    ├── hypothesis.py       - The "Logic" - Confidence-based probing
    ├── state.py            - The "Memory" - ProfileRubric and state
    ├── graph.py            - The "Wiring" - LangGraph workflow
    ├── session_manager.py  - Session lifecycle management
    ├── swarm_integration.py - SwarmBus communication
    └── face/               - Voice personality system
        ├── __init__.py     - FaceOrchestrator, FaceFactory
        └── voice/          - Oracle, Sage, Companion, Challenger, Mirror

The Genesis Node operates in 5 phases:
    1. AWAKENING   - Initial contact, establishing rapport
    2. EXCAVATION  - Digging deep into shadows and patterns
    3. MAPPING     - Connecting dots, building the constellation
    4. SYNTHESIS   - Weaving insights into a coherent portrait
    5. ACTIVATION  - Empowering action and next steps

Each phase has its own visual theme, question style, and detection focus.
"""

# Core conversation
from .core import GenesisCore, GenesisResponse

# Silent pattern detection
from .profiler import GenesisProfiler, Signal

# Confidence-based probing
from .hypothesis import HypothesisEngine, Hypothesis

# State management
from .state import (
    GenesisState,
    GenesisPhase,
    ProfileRubric,
    DetectedTrait,
    SessionMemory,
    ActiveSignal,
)

# LangGraph workflow
from .graph import (
    create_genesis_graph,
    get_genesis_graph,
    run_genesis_turn,
    run_genesis_turn_sync,
)

# Session management
from .session_manager import GenesisSessionManager, GenesisSession

# Swarm communication
from .swarm_integration import GenesisSwarmHandler

# Digital Twin integration
from .digital_twin_adapter import (
    GenesisTwinAdapter,
    TraitResult,
    TraitCategory,
    get_adapter as get_twin_adapter,
    record_trait,
    get_trait,
)

__all__ = [
    # Core
    "GenesisCore",
    "GenesisResponse",
    # Profiler
    "GenesisProfiler",
    "Signal",
    # Hypothesis
    "HypothesisEngine",
    "Hypothesis",
    # State
    "GenesisState",
    "GenesisPhase",
    "ProfileRubric",
    "DetectedTrait",
    "SessionMemory",
    "ActiveSignal",
    # Graph
    "create_genesis_graph",
    "get_genesis_graph",
    "run_genesis_turn",
    "run_genesis_turn_sync",
    # Session Management
    "GenesisSessionManager",
    "GenesisSession",
    # Swarm Integration
    "GenesisSwarmHandler",
    # Digital Twin Integration
    "GenesisTwinAdapter",
    "TraitResult",
    "TraitCategory",
    "get_twin_adapter",
    "record_trait",
    "get_trait",
]
