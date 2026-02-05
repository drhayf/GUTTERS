"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        COUNCIL OF SYSTEMS MODULE                             ║
║                                                                              ║
║   Unified Intelligence Layer for Multi-Paradigm Metaphysical Synthesis       ║
║                                                                              ║
║   Components:                                                                ║
║   - service.py: Core Council service with synthesis, notifications, events  ║
║   - integration.py: Bridges CouncilService with ChronosStateManager         ║
║   - journal_generator.py: Auto-generate journal entries for cosmic events   ║
║                                                                              ║
║   Recommended Usage:                                                         ║
║       # For unified state (combines Cardology + I-Ching + Synthesis):        ║
║       from src.app.modules.intelligence.council import get_council_integration║
║       integration = get_council_integration()                                ║
║       state = await integration.get_unified_state(user_id)                   ║
║       llm_context = await integration.get_llm_context(user_id)               ║
║                                                                              ║
║       # For direct I-Ching/Synthesis access (no user context needed):        ║
║       from src.app.modules.intelligence.council import get_council_service   ║
║       council = get_council_service()                                        ║
║       hexagram = council.get_current_hexagram()                              ║
║                                                                              ║
║   Integration Points:                                                        ║
║   - Hypothesis: Gate/period correlation tracking                            ║
║   - Observer: Cyclical pattern detection for gates                          ║
║   - Push Notifications: Gate transitions and synthesis alerts               ║
║   - Chat: MAGI context injection for LLM awareness                          ║
║   - ChronosStateManager: User-specific state caching and persistence        ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .service import CouncilService, get_council_service
from .integration import CouncilIntegration, get_council_integration, UnifiedCosmicState

__all__ = [
    "CouncilService",
    "get_council_service",
    "CouncilIntegration",
    "get_council_integration",
    "UnifiedCosmicState",
]
