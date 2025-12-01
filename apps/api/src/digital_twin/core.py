"""
Digital Twin Core - The Central Orchestrator

This is the main entry point for all Digital Twin operations.
It coordinates:
- Identity management
- Domain registration
- Event distribution
- Unified access

The Sovereign Agent and all other components interact with
the Digital Twin through this core.

@module DigitalTwinCore
"""

from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
import asyncio
import logging

from .traits import Trait, TraitCategory, TraitFramework, TraitValidator, ConfidenceThreshold
from .identity import Identity, IdentityStore, IdentitySession, get_identity_store
from .events import ProfileEventBus, EventType, ProfileEvent, get_event_bus
from .domains import BaseDomain, DomainRegistry, get_domain_registry
from .access import TwinAccessor, AccessContext, AccessPermission, PermissionLevel, QueryBuilder, QueryResult


logger = logging.getLogger(__name__)


@dataclass
class DigitalTwinConfig:
    """Configuration for the Digital Twin system."""
    
    # Storage
    storage_path: str = "data/identities"
    auto_save: bool = True
    save_interval_seconds: int = 30
    
    # Confidence thresholds
    confirmed_threshold: float = 0.80
    high_threshold: float = 0.65
    medium_threshold: float = 0.45
    low_threshold: float = 0.25
    
    # Events
    enable_events: bool = True
    event_history_size: int = 100
    
    # Domains
    auto_discover_domains: bool = True
    
    # Debug
    verbose_logging: bool = False


class DigitalTwinCore:
    """
    The central coordinator for the Digital Twin system.
    
    This is THE entry point for all Digital Twin operations.
    Use this class to:
    - Get the unified accessor
    - Register custom domains
    - Subscribe to events
    - Manage identities and sessions
    
    The Sovereign Agent gets its omniscient access through this core.
    
    Usage:
        core = await DigitalTwinCore.get_instance()
        
        # Get accessor for read/write operations
        accessor = await core.get_accessor()
        
        # Register a custom domain
        core.register_domain(MyDomain())
        
        # Subscribe to trait changes
        await core.on_trait_change(my_handler)
    """
    
    _instance: Optional["DigitalTwinCore"] = None
    _initialized: bool = False
    
    def __init__(self, config: Optional[DigitalTwinConfig] = None):
        """Initialize core (use get_instance() for singleton)."""
        self.config = config or DigitalTwinConfig()
        self._accessor: Optional[TwinAccessor] = None
        self._store: Optional[IdentityStore] = None
        self._bus: Optional[ProfileEventBus] = None
        self._registry: Optional[DomainRegistry] = None
        self._auto_save_task: Optional[asyncio.Task] = None
        
    @classmethod
    async def get_instance(
        cls, 
        config: Optional[DigitalTwinConfig] = None
    ) -> "DigitalTwinCore":
        """Get or create the singleton core instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        
        if not cls._instance._initialized:
            await cls._instance._initialize()
        
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize all subsystems."""
        logger.info("Initializing Digital Twin Core...")
        
        # Initialize subsystems
        self._store = get_identity_store()
        self._bus = get_event_bus()
        self._registry = get_domain_registry()
        
        # Initialize accessor
        self._accessor = await TwinAccessor.get_instance()
        
        # Start auto-save if enabled
        if self.config.auto_save:
            self._start_auto_save()
        
        # Auto-discover domains if enabled
        if self.config.auto_discover_domains:
            await self._discover_domains()
        
        self._initialized = True
        logger.info("Digital Twin Core initialized successfully")
    
    async def shutdown(self) -> None:
        """Gracefully shut down the core."""
        logger.info("Shutting down Digital Twin Core...")
        
        # Stop auto-save
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
        
        # Final save
        if self._accessor:
            await self._accessor.save_identity()
        
        logger.info("Digital Twin Core shut down complete")
    
    # ============================================================
    # ACCESSOR ACCESS
    # ============================================================
    
    async def get_accessor(
        self, 
        context: Optional[AccessContext] = None
    ) -> TwinAccessor:
        """
        Get the unified accessor.
        
        This is the main way to interact with the Digital Twin.
        
        Args:
            context: Optional access context (for permission checking)
            
        Returns:
            The TwinAccessor instance
        """
        if self._accessor is None:
            self._accessor = await TwinAccessor.get_instance()
        return self._accessor
    
    def create_context(
        self,
        accessor_id: str,
        permission: PermissionLevel = PermissionLevel.READ,
        session_id: Optional[str] = None
    ) -> AccessContext:
        """
        Create an access context for an accessor.
        
        Args:
            accessor_id: ID of the accessor (agent, tool, etc.)
            permission: Permission level
            session_id: Optional session ID
            
        Returns:
            AccessContext for use with accessor methods
        """
        return AccessContext(
            accessor_id=accessor_id,
            permission=AccessPermission(level=permission),
            session_id=session_id
        )
    
    def sovereign_context(self, session_id: Optional[str] = None) -> AccessContext:
        """
        Create a context with full sovereign access.
        
        For the Sovereign Agent and other privileged components.
        """
        return AccessContext(
            accessor_id="sovereign",
            permission=AccessPermission.sovereign(),
            session_id=session_id
        )
    
    # ============================================================
    # DOMAIN MANAGEMENT
    # ============================================================
    
    def register_domain(self, domain: BaseDomain) -> None:
        """
        Register a custom domain.
        
        Domains define schemas for traits and provide
        domain-specific query methods.
        """
        self._registry.register_instance(domain)
        logger.info(f"Registered domain: {domain.name}")
    
    def get_domain(self, name: str) -> Optional[BaseDomain]:
        """Get a registered domain by name."""
        return self._registry.get(name)
    
    def list_domains(self) -> List[str]:
        """List all registered domain names."""
        return list(self._registry.get_all().keys())
    
    async def _discover_domains(self) -> None:
        """Auto-discover and register domains."""
        # Import built-in domains
        try:
            from .domains.genesis import GenesisDomain
            self.register_domain(GenesisDomain())
        except ImportError:
            logger.debug("Genesis domain not yet implemented")
        
        # Future: Scan for plugin domains
        pass
    
    # ============================================================
    # EVENT SUBSCRIPTION
    # ============================================================
    
    async def on_event(
        self,
        handler: Callable[[ProfileEvent], Any],
        event_types: Optional[List[EventType]] = None
    ) -> str:
        """
        Subscribe to profile events.
        
        Args:
            handler: Async function to call when event occurs
            event_types: Optional filter for specific event types
            
        Returns:
            Subscription ID (for unsubscribing)
        """
        return await self._bus.subscribe(handler, event_types)
    
    async def on_trait_change(
        self,
        handler: Callable[[ProfileEvent], Any]
    ) -> str:
        """Subscribe specifically to trait changes."""
        return await self.on_event(
            handler,
            event_types=[EventType.TRAIT_ADDED, EventType.TRAIT_UPDATED]
        )
    
    async def off_event(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        await self._bus.unsubscribe(subscription_id)
    
    async def emit_event(self, event: ProfileEvent) -> None:
        """Emit a custom event."""
        await self._bus.emit(event)
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    async def start_session(
        self,
        session_id: str,
        identity_id: Optional[str] = None
    ) -> IdentitySession:
        """Start a new session."""
        context = self.sovereign_context(session_id)
        return await self._accessor.start_session(session_id, identity_id, context)
    
    async def end_session(self, session_id: str) -> None:
        """End a session."""
        await self._accessor.end_session(session_id)
    
    async def get_session(self, session_id: str) -> Optional[IdentitySession]:
        """Get an existing session."""
        return await self._accessor.get_session(session_id)
    
    # ============================================================
    # CONVENIENCE METHODS
    # ============================================================
    
    async def get(self, path: str, default: Any = None) -> Any:
        """Quick read - get trait value by path."""
        accessor = await self.get_accessor()
        return await accessor.get_value(path, default=default)
    
    async def set(
        self,
        path: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "system"
    ) -> Trait:
        """Quick write - set trait value."""
        accessor = await self.get_accessor()
        context = self.sovereign_context()
        return await accessor.set(path, value, confidence=confidence, source=source, context=context)
    
    async def query(self, query: QueryBuilder) -> QueryResult:
        """Execute a query."""
        accessor = await self.get_accessor()
        return await accessor.query(query)
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get Digital Twin summary."""
        accessor = await self.get_accessor()
        return await accessor.get_summary()
    
    async def export(self) -> Dict[str, Any]:
        """Export full Digital Twin."""
        accessor = await self.get_accessor()
        return await accessor.export()
    
    # ============================================================
    # AUTO-SAVE
    # ============================================================
    
    def _start_auto_save(self) -> None:
        """Start the auto-save background task."""
        async def auto_save_loop():
            while True:
                await asyncio.sleep(self.config.save_interval_seconds)
                try:
                    if self._accessor:
                        await self._accessor.save_identity()
                        if self.config.verbose_logging:
                            logger.debug("Auto-saved identity")
                except Exception as e:
                    logger.error(f"Auto-save failed: {e}")
        
        self._auto_save_task = asyncio.create_task(auto_save_loop())
    
    # ============================================================
    # MIGRATION
    # ============================================================
    
    async def migrate_from_legacy(
        self,
        legacy_profile: Dict[str, Any],
        source: str = "legacy_migration"
    ) -> Identity:
        """
        Migrate data from legacy ProfileRubric format.
        
        Args:
            legacy_profile: Old ProfileRubric data
            source: Source identifier for provenance
            
        Returns:
            The new Identity with migrated data
        """
        identity = await self._store.migrate_from_legacy_profile(legacy_profile)
        
        logger.info(f"Migrated legacy profile to Identity {identity.id}")
        return identity


# Convenience function
async def get_digital_twin_core() -> DigitalTwinCore:
    """Get the singleton DigitalTwinCore instance."""
    return await DigitalTwinCore.get_instance()
