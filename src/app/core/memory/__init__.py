"""
GUTTERS - Active Working Memory

Redis-backed memory cache for current synthesized state.

Provides three-layer memory architecture:
- HOT: Master synthesis, conversation history (24h TTL)
- WARM: Module outputs, preferences (7d TTL)
- COLD: PostgreSQL fallback (permanent)
"""
from .active_memory import ActiveMemory, get_active_memory
from .synthesis_orchestrator import (
    CRITICAL_TRIGGERS,
    SynthesisOrchestrator,
    SynthesisTrigger,
    get_orchestrator,
)

__all__ = [
    "ActiveMemory",
    "get_active_memory",
    "SynthesisOrchestrator",
    "SynthesisTrigger",
    "get_orchestrator",
    "CRITICAL_TRIGGERS",
]
