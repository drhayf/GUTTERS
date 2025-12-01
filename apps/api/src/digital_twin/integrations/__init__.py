"""
Sovereign Integration - Connecting Sovereign Agent to Digital Twin

This module provides the integration layer between the Sovereign Agent
and the Digital Twin system. The Sovereign Agent is OMNISCIENT (can read
everything) and OMNIPOTENT (can execute anything).

This integration ensures:
1. Sovereign Agent has immediate access to all identity data
2. Any changes are reflected in real-time
3. Sovereign can write directly to any trait
4. Full event subscription for awareness

@module SovereignIntegration
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import logging

from ..core import DigitalTwinCore, get_digital_twin_core
from ..access import (
    TwinAccessor, 
    AccessContext, 
    AccessPermission, 
    PermissionLevel,
    QueryBuilder,
    QueryResult,
)
from ..traits import Trait, TraitCategory, TraitFramework
from ..events import EventType, ProfileEvent, get_event_bus
from ..identity import Identity


logger = logging.getLogger(__name__)


@dataclass
class SovereignDigitalTwinState:
    """
    Cached state of the Digital Twin for Sovereign Agent.
    
    Updated in real-time via event subscriptions.
    """
    identity: Optional[Identity] = None
    last_updated: Optional[str] = None
    trait_count: int = 0
    domains: List[str] = field(default_factory=list)
    
    # Quick access to key traits
    hd_type: Optional[str] = None
    jung_dominant: Optional[str] = None
    energy_pattern: Optional[str] = None
    profiling_phase: str = "awakening"
    completion_percentage: float = 0.0


class SovereignDigitalTwinIntegration:
    """
    Integration class for Sovereign Agent to access Digital Twin.
    
    This gives the Sovereign Agent complete omniscient access to the
    Digital Twin with real-time awareness of all changes.
    
    Usage:
        # In Sovereign Agent initialization
        self.twin_integration = await SovereignDigitalTwinIntegration.create()
        
        # Read any trait
        hd_type = await self.twin_integration.get("genesis.hd_type")
        
        # Write any trait
        await self.twin_integration.set(
            "genesis.energy_pattern",
            "sustainable",
            confidence=0.9
        )
        
        # Query with full access
        result = await self.twin_integration.query(
            QueryBuilder()
                .from_domain("genesis")
                .confidence_above(0.7)
        )
        
        # Get current state snapshot
        state = self.twin_integration.get_state()
    """
    
    _instance: Optional["SovereignDigitalTwinIntegration"] = None
    
    def __init__(self):
        """Initialize (use create() for async initialization)."""
        self._core: Optional[DigitalTwinCore] = None
        self._accessor: Optional[TwinAccessor] = None
        self._context: Optional[AccessContext] = None
        self._state = SovereignDigitalTwinState()
        self._event_subscription_id: Optional[str] = None
        self._change_handlers: List[Callable[[ProfileEvent], Any]] = []
    
    @classmethod
    async def create(cls) -> "SovereignDigitalTwinIntegration":
        """Create and initialize the integration."""
        if cls._instance is not None:
            return cls._instance
        
        instance = cls()
        await instance._initialize()
        cls._instance = instance
        return instance
    
    @classmethod
    async def get_instance(cls) -> "SovereignDigitalTwinIntegration":
        """Get the singleton instance (creates if needed)."""
        if cls._instance is None:
            return await cls.create()
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize connection to Digital Twin."""
        logger.info("Initializing Sovereign-DigitalTwin integration...")
        
        # Get core
        self._core = await get_digital_twin_core()
        
        # Get accessor with sovereign permissions
        self._accessor = await self._core.get_accessor()
        self._context = self._core.sovereign_context()
        
        # Load initial state
        await self._refresh_state()
        
        # Subscribe to all events
        bus = get_event_bus()
        self._event_subscription_id = await bus.subscribe(
            handler=self._on_event,
            event_types=None  # All events
        )
        
        logger.info("Sovereign-DigitalTwin integration ready")
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        if self._event_subscription_id:
            bus = get_event_bus()
            await bus.unsubscribe(self._event_subscription_id)
    
    # ============================================================
    # STATE ACCESS
    # ============================================================
    
    def get_state(self) -> SovereignDigitalTwinState:
        """Get the current cached state."""
        return self._state
    
    async def refresh_state(self) -> SovereignDigitalTwinState:
        """Force refresh state from source."""
        await self._refresh_state()
        return self._state
    
    async def _refresh_state(self) -> None:
        """Internal state refresh."""
        identity = await self._accessor.get_active_identity()
        
        self._state.identity = identity
        self._state.domains = list(identity.traits_by_domain.keys())
        self._state.trait_count = sum(
            len(traits) for traits in identity.traits_by_domain.values()
        )
        
        # Quick access to key traits
        self._state.hd_type = identity.hd_type
        self._state.jung_dominant = identity.jung_dominant
        self._state.energy_pattern = identity.energy_pattern
        
        # Get phase and completion from traits
        phase_trait = await self._accessor.get("genesis.profiling_phase", self._context)
        if phase_trait:
            self._state.profiling_phase = phase_trait.value
        
        completion_trait = await self._accessor.get("genesis.completion_percentage", self._context)
        if completion_trait:
            self._state.completion_percentage = completion_trait.value
    
    # ============================================================
    # READ OPERATIONS
    # ============================================================
    
    async def get(self, path: str, default: Any = None) -> Any:
        """
        Get a trait value by path.
        
        Examples:
            hd_type = await integration.get("genesis.hd_type")
            energy = await integration.get("genesis.energy_pattern", "unknown")
        """
        trait = await self._accessor.get(path, self._context, default)
        return trait.value if trait else default
    
    async def get_trait(self, path: str) -> Optional[Trait]:
        """Get the full Trait object by path."""
        return await self._accessor.get(path, self._context)
    
    async def get_all(self, domain: Optional[str] = None) -> Dict[str, Trait]:
        """Get all traits, optionally filtered by domain."""
        return await self._accessor.get_all(domain, self._context)
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the Digital Twin."""
        return await self._accessor.get_summary(self._context)
    
    async def export(self) -> Dict[str, Any]:
        """Export the full Digital Twin."""
        return await self._accessor.export(self._context)
    
    # ============================================================
    # WRITE OPERATIONS
    # ============================================================
    
    async def set(
        self,
        path: str,
        value: Any,
        confidence: float = 1.0,
        framework: Optional[TraitFramework] = None,
        source: str = "sovereign_agent"
    ) -> Trait:
        """
        Set a trait value.
        
        Examples:
            await integration.set("genesis.hd_type", "Generator", confidence=0.95)
            await integration.set("genesis.energy_pattern", "sustainable")
        """
        return await self._accessor.set(
            path=path,
            value=value,
            confidence=confidence,
            framework=framework,
            source=source,
            context=self._context,
            auto_save=True
        )
    
    async def update_profile(self, updates: Dict[str, Any]) -> List[Trait]:
        """
        Batch update multiple traits.
        
        Example:
            await integration.update_profile({
                "genesis.hd_type": "Generator",
                "genesis.energy_pattern": "sustainable",
                "genesis.profiling_phase": "synthesis"
            })
        """
        results = []
        for path, value in updates.items():
            if isinstance(value, dict) and "value" in value:
                trait = await self.set(
                    path=path,
                    value=value["value"],
                    confidence=value.get("confidence", 1.0),
                    source=value.get("source", "sovereign_agent")
                )
            else:
                trait = await self.set(path=path, value=value)
            results.append(trait)
        return results
    
    async def delete(self, path: str) -> bool:
        """Delete a trait."""
        return await self._accessor.delete(path, self._context)
    
    # ============================================================
    # QUERY OPERATIONS
    # ============================================================
    
    async def query(self, query: QueryBuilder) -> QueryResult:
        """
        Execute a query against the Digital Twin.
        
        Example:
            result = await integration.query(
                QueryBuilder()
                    .from_domain("genesis")
                    .confidence_above(0.8)
                    .limit(10)
            )
        """
        return await self._accessor.query(query, self._context)
    
    async def find_traits(
        self,
        domain: Optional[str] = None,
        category: Optional[TraitCategory] = None,
        framework: Optional[TraitFramework] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find traits matching criteria.
        
        Convenience wrapper around query().
        """
        builder = QueryBuilder()
        
        if domain:
            builder = builder.from_domain(domain)
        
        if min_confidence > 0:
            builder = builder.confidence_above(min_confidence)
        
        if category:
            builder = builder.where_eq("category", category.value)
        
        if framework:
            builder = builder.where_eq("framework", framework.value)
        
        result = await self.query(builder)
        return result.data if result.success else []
    
    # ============================================================
    # EVENT HANDLING
    # ============================================================
    
    async def _on_event(self, event: ProfileEvent) -> None:
        """Handle incoming events."""
        # Refresh state on relevant events
        if event.event_type in [
            EventType.TRAIT_ADDED,
            EventType.TRAIT_UPDATED,
            EventType.IDENTITY_LOADED,
        ]:
            await self._refresh_state()
        
        # Notify registered handlers
        for handler in self._change_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error: {e}")
    
    def on_change(self, handler: Callable[[ProfileEvent], Any]) -> None:
        """
        Register a handler for Digital Twin changes.
        
        This allows the Sovereign Agent to react to any changes
        in the Digital Twin in real-time.
        
        Example:
            def handle_change(event):
                if event.event_type == EventType.TRAIT_UPDATED:
                    print(f"Trait changed: {event.trait_path}")
            
            integration.on_change(handle_change)
        """
        self._change_handlers.append(handler)
    
    def off_change(self, handler: Callable[[ProfileEvent], Any]) -> None:
        """Remove a change handler."""
        if handler in self._change_handlers:
            self._change_handlers.remove(handler)
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    async def start_session(self, session_id: str) -> None:
        """Start a new session."""
        await self._core.start_session(session_id)
    
    async def end_session(self, session_id: str) -> None:
        """End a session."""
        await self._core.end_session(session_id)
    
    # ============================================================
    # CONTEXT FOR OTHER COMPONENTS
    # ============================================================
    
    def create_agent_context(
        self,
        agent_id: str,
        level: PermissionLevel = PermissionLevel.WRITE
    ) -> AccessContext:
        """
        Create an access context for another agent.
        
        The Sovereign Agent can grant access to sub-agents.
        """
        return self._core.create_context(
            accessor_id=agent_id,
            permission=level
        )


import asyncio  # Needed for iscoroutinefunction check


# Convenience function
async def get_sovereign_twin_integration() -> SovereignDigitalTwinIntegration:
    """Get the singleton integration instance."""
    return await SovereignDigitalTwinIntegration.get_instance()
