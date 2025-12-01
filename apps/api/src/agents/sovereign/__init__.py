"""
The Sovereign Agent - The Omniscient Conversational Core

This module implements the "Main Brain" of Project Sovereign - an omniscient,
omnipresent AI agent that:

1. KNOWS EVERYTHING - Full awareness of all modules, data, and system state
2. CONNECTS TO EVERYTHING - Can route to any agent, tool, or capability
3. SYNTHESIZES ACROSS DOMAINS - Cross-module reasoning and insights
4. GENERATES DYNAMIC UI - Produces generative UI components
5. SPEAKS NATURALLY - Conversational, personality-driven responses
6. USES TOOLS - Function calling for actions (add to nutrition, set reminders, etc.)

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         ┌─────────────────────────────────┐
                         │       SOVEREIGN AGENT           │
                         │   (The Omniscient Core)         │
                         ├─────────────────────────────────┤
                         │                                 │
                         │  ┌─────────────────────────┐   │
                         │  │     CORTEX (Brain)       │   │
                         │  │  • Intent Understanding  │   │
                         │  │  • Context Fusion        │   │
                         │  │  • Response Generation   │   │
                         │  └───────────┬─────────────┘   │
                         │              │                  │
                         │  ┌───────────▼─────────────┐   │
                         │  │    MEMORY (Context)      │   │
                         │  │  • Digital Twin Access   │   │
                         │  │  • Conversation History  │   │
                         │  │  • Module State Cache    │   │
                         │  └───────────┬─────────────┘   │
                         │              │                  │
                         │  ┌───────────▼─────────────┐   │
                         │  │     TOOLS (Actions)      │   │
                         │  │  • Add Nutrition Entry   │   │
                         │  │  • Update Profile        │   │
                         │  │  • Set Reminder          │   │
                         │  │  • Query Data            │   │
                         │  └───────────┬─────────────┘   │
                         │              │                  │
                         │  ┌───────────▼─────────────┐   │
                         │  │    ROUTER (Delegation)   │   │
                         │  │  • SwarmBus Integration  │   │
                         │  │  • Agent Discovery       │   │
                         │  │  • Parallel Execution    │   │
                         │  └─────────────────────────┘   │
                         │                                 │
                         └─────────────────────────────────┘

The Sovereign Agent enhances the Orchestrator pattern by adding:
- Tool use via function calling
- Rich generative UI output
- Cross-module data synthesis
- Personality-driven responses
- Proactive insights and suggestions

@module SovereignAgent
"""

from .agent import SovereignAgent, SovereignContext, SovereignResponse, get_sovereign_agent
from .cortex import SovereignCortex
from .memory import SovereignMemory
from .tools import SovereignToolkit, BaseSovereignTool
from .router import SovereignRouter
from .integrations import (
    SovereignIntegrations,
    HRMIntegration,
    LLMFactoryIntegration,
    SwarmBusIntegration,
    GenesisIntegration,
    MasterAgentsIntegration,
    OrchestratorIntegration,
    get_integrations,
)

__all__ = [
    # Core Agent
    "SovereignAgent",
    "SovereignContext",
    "SovereignResponse",
    "get_sovereign_agent",
    # Components
    "SovereignCortex",
    "SovereignMemory",
    "SovereignToolkit",
    "BaseSovereignTool",
    "SovereignRouter",
    # Integrations
    "SovereignIntegrations",
    "HRMIntegration",
    "LLMFactoryIntegration",
    "SwarmBusIntegration",
    "GenesisIntegration",
    "MasterAgentsIntegration",
    "OrchestratorIntegration",
    "get_integrations",
]
