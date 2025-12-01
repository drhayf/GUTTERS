"""
Digital Twin - The Living Identity System

This module implements the SINGLE SOURCE OF TRUTH for user identity in Project Sovereign.
All systems read from and write to the Digital Twin through a unified interface.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌────────────────────────────────┐
                    │       SOVEREIGN AGENT          │
                    │   (Omniscient / Omnipotent)    │
                    │  • Full read/write access      │
                    │  • Real-time awareness         │
                    │  • Generative UI anywhere      │
                    │  • System-wide control         │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │       DIGITAL TWIN CORE        │
                    │    (Single Source of Truth)    │
                    ├────────────────────────────────┤
                    │  ┌──────────────────────────┐  │
                    │  │     Unified Accessor     │  │
                    │  │  get() / set() / query() │  │
                    │  └────────────┬─────────────┘  │
                    │               │                │
                    │  ┌────────────▼─────────────┐  │
                    │  │      Domain Registry     │  │
                    │  │  genesis, health, etc.   │  │
                    │  └────────────┬─────────────┘  │
                    │               │                │
                    │  ┌────────────▼─────────────┐  │
                    │  │       Event Bus          │  │
                    │  │    Real-time sync        │  │
                    │  └────────────┬─────────────┘  │
                    │               │                │
                    │  ┌────────────▼─────────────┐  │
                    │  │    Identity Store        │  │
                    │  │  Persistent identity     │  │
                    │  └──────────────────────────┘  │
                    └────────────────────────────────┘

Key Principles:
1. SINGLE SOURCE OF TRUTH - One place for all identity data
2. UNIFIED INTERFACE - All access through get()/set()/query()
3. REAL-TIME SYNC - EventBus notifies all subscribers
4. IDENTITY-CENTRIC - Storage is tied to identity, not session
5. FRACTAL EXTENSIBILITY - New domains plug in seamlessly
6. SOVEREIGN ACCESS - Main agent has omniscient read/write

Usage:
    from digital_twin import get_twin, DigitalTwinCore
    
    # Get the singleton instance
    twin = await get_twin(identity_id="user_123")
    
    # Read data (any system can read)
    hd_type = twin.get("genesis.hd_type")
    all_traits = twin.query(domain="genesis", min_confidence=0.8)
    
    # Write data (with provenance tracking)
    twin.set(
        path="genesis.energy_pattern",
        value="sustainable",
        source="genesis.profiler",
        confidence=0.85,
        evidence=["User mentioned steady pace"]
    )
    
    # Subscribe to changes (real-time sync)
    twin.subscribe(handler=my_handler, filter={"domain": "genesis"})

@module DigitalTwin
"""

from .core import (
    DigitalTwinCore,
    DigitalTwinConfig,
    get_digital_twin_core,
)
from .traits import (
    Trait,
    TraitCategory,
    TraitFramework,
    TraitSource,
    TraitChange,
    TraitValidator,
    ConfidenceThreshold,
)
from .domains import (
    BaseDomain,
    DomainRegistry,
    DomainSchema,
    DomainQuery,
    DomainResponse,
    TraitSchema,
    GenesisDomain,
    get_domain_registry,
)
from .events import (
    ProfileEventBus,
    ProfileEvent,
    EventType,
    TraitAddedEvent,
    TraitUpdatedEvent,
    IdentityLoadedEvent,
    SessionStartedEvent,
    get_event_bus,
)
from .access import (
    TwinAccessor,
    QueryBuilder,
    QueryResult,
    AccessPermission,
    AccessContext,
    PermissionLevel,
    get_twin_accessor,
)
from .identity import (
    IdentityStore,
    Identity,
    IdentitySession,
    SessionContext,
    get_identity_store,
)
from .integrations import (
    SovereignDigitalTwinIntegration,
    SovereignDigitalTwinState,
    get_sovereign_twin_integration,
)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Alias functions for easier import
async def get_accessor() -> TwinAccessor:
    """Get the TwinAccessor instance."""
    return await get_twin_accessor()


async def get_twin(identity_id: str = None) -> DigitalTwinCore:
    """Get the Digital Twin core, optionally for a specific identity."""
    core = await get_digital_twin_core()
    if identity_id:
        await core.set_identity(identity_id)
    return core


__all__ = [
    # Core
    "DigitalTwinCore",
    "DigitalTwinConfig",
    "get_digital_twin_core",
    # Traits
    "Trait",
    "TraitCategory",
    "TraitFramework",
    "TraitSource",
    "TraitChange",
    "TraitValidator",
    "ConfidenceThreshold",
    # Domains
    "BaseDomain",
    "DomainRegistry",
    "DomainSchema",
    "DomainQuery",
    "DomainResponse",
    "TraitSchema",
    "GenesisDomain",
    "get_domain_registry",
    # Events
    "ProfileEventBus",
    "ProfileEvent",
    "EventType",
    "TraitAddedEvent",
    "TraitUpdatedEvent",
    "IdentityLoadedEvent",
    "SessionStartedEvent",
    "get_event_bus",
    # Access
    "TwinAccessor",
    "QueryBuilder",
    "QueryResult",
    "AccessPermission",
    "AccessContext",
    "PermissionLevel",
    "get_twin_accessor",
    "get_accessor",  # Convenience alias
    # Identity
    "IdentityStore",
    "Identity",
    "IdentitySession",
    "SessionContext",
    "get_identity_store",
    # Integrations (Sovereign Agent)
    "SovereignDigitalTwinIntegration",
    "SovereignDigitalTwinState",
    "get_sovereign_twin_integration",
    # Convenience
    "get_twin",
]
