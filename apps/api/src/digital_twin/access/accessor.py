"""
Twin Accessor - Unified Read/Write Interface for Digital Twin

This is THE interface through which all reads and writes to the
Digital Twin flow. Provides a single, consistent API for:
- Reading traits by path
- Writing traits with validation
- Executing complex queries
- Managing subscriptions to changes

@module TwinAccessor
"""

from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
import asyncio
import time
import logging

from ..traits import Trait, TraitCategory, TraitFramework, TraitValidator
from ..identity import Identity, IdentityStore, IdentitySession
from ..events import ProfileEventBus, EventType, TraitAddedEvent, TraitUpdatedEvent
from ..domains import DomainRegistry
from .permissions import AccessPermission, PermissionLevel
from .query import QueryBuilder, QueryResult, QueryCondition


logger = logging.getLogger(__name__)


@dataclass
class AccessContext:
    """
    Context for an access operation.
    
    Tracks who's accessing, what permissions they have,
    and any session context.
    """
    accessor_id: str = "anonymous"
    permission: AccessPermission = field(default_factory=AccessPermission.read_only)
    session_id: Optional[str] = None
    identity_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TwinAccessor:
    """
    Unified accessor for Digital Twin operations.
    
    This is the single point of access for all reads and writes.
    All agents, tools, and components should go through this accessor.
    
    Usage:
        accessor = await TwinAccessor.get_instance()
        
        # Read
        trait = await accessor.get("genesis.hd_type")
        
        # Write
        await accessor.set("genesis.hd_type", "Generator", confidence=0.95)
        
        # Query
        result = await accessor.query(
            QueryBuilder()
                .from_domain("genesis")
                .confidence_above(0.8)
                .build()
        )
    """
    
    _instance: Optional["TwinAccessor"] = None
    _initialized: bool = False
    
    def __init__(self):
        """Initialize accessor (use get_instance() for singleton)."""
        self._store: Optional[IdentityStore] = None
        self._bus: Optional[ProfileEventBus] = None
        self._registry: Optional[DomainRegistry] = None
        self._validator = TraitValidator()
        self._active_identity: Optional[Identity] = None
        self._sessions: Dict[str, IdentitySession] = {}
        
    @classmethod
    async def get_instance(cls) -> "TwinAccessor":
        """Get or create the singleton accessor instance."""
        if cls._instance is None:
            cls._instance = cls()
        
        if not cls._instance._initialized:
            await cls._instance._initialize()
        
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize dependencies."""
        from ..identity.store import get_identity_store
        from ..events.bus import get_event_bus
        from ..domains.registry import get_domain_registry
        
        self._store = get_identity_store()
        self._bus = get_event_bus()
        self._registry = get_domain_registry()
        self._initialized = True
        
        logger.info("TwinAccessor initialized")
    
    # ============================================================
    # IDENTITY MANAGEMENT
    # ============================================================
    
    async def load_identity(
        self, 
        identity_id: str, 
        context: Optional[AccessContext] = None
    ) -> Identity:
        """Load an identity, making it the active one."""
        self._check_permission(context, require_read=True)
        
        if context and not (context.permission.can_access_identity(identity_id)):
            raise PermissionError(f"No access to identity {identity_id}")
        
        self._active_identity = await self._store.load(identity_id)
        
        if self._active_identity is None:
            self._active_identity = await self._store.get_or_create_default()
        
        await self._bus.emit(ProfileEventBus.create_event(
            EventType.IDENTITY_LOADED,
            {"identity_id": self._active_identity.id}
        ))
        
        return self._active_identity
    
    async def get_active_identity(self) -> Identity:
        """Get the currently active identity."""
        if self._active_identity is None:
            self._active_identity = await self._store.get_or_create_default()
        return self._active_identity
    
    async def save_identity(self, context: Optional[AccessContext] = None) -> None:
        """Persist the active identity to storage."""
        self._check_permission(context, require_write=True)
        
        if self._active_identity:
            await self._store.save(self._active_identity)
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    async def start_session(
        self,
        session_id: str,
        identity_id: Optional[str] = None,
        context: Optional[AccessContext] = None
    ) -> IdentitySession:
        """Start a new session linked to an identity."""
        identity = await self.get_active_identity()
        
        if identity_id and identity.id != identity_id:
            identity = await self.load_identity(identity_id, context)
        
        session = IdentitySession(
            session_id=session_id,
            identity_id=identity.id
        )
        await session.start()
        
        self._sessions[session_id] = session
        identity.session_ids.append(session_id)
        
        await self._bus.emit(ProfileEventBus.create_event(
            EventType.SESSION_STARTED,
            {"session_id": session_id, "identity_id": identity.id}
        ))
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IdentitySession]:
        """Get an existing session."""
        return self._sessions.get(session_id)
    
    async def end_session(self, session_id: str) -> None:
        """End a session, persisting any changes."""
        session = self._sessions.get(session_id)
        if session:
            await session.end()
            del self._sessions[session_id]
        
        await self.save_identity()
    
    # ============================================================
    # TRAIT ACCESS - READ
    # ============================================================
    
    async def get(
        self,
        path: str,
        context: Optional[AccessContext] = None,
        default: Any = None
    ) -> Optional[Trait]:
        """
        Get a trait by path.
        
        Path format: "domain.trait_name" or just "trait_name"
        Examples:
            - "genesis.hd_type"
            - "genesis.jung_dominant"
            - "health.sleep_quality"
        
        Args:
            path: Trait path (domain.name or just name)
            context: Access context with permissions
            default: Default value if trait doesn't exist
            
        Returns:
            The Trait object or None
        """
        self._check_permission(context, require_read=True, path=path)
        
        identity = await self.get_active_identity()
        trait = identity.get_trait(path)
        
        if trait is None and default is not None:
            # Create a synthetic trait with default value
            return Trait.create(
                name=path.split(".")[-1],
                category=TraitCategory.MISC,
                value=default,
                confidence=0.0,
                source_type="default"
            )
        
        return trait
    
    async def get_value(
        self,
        path: str,
        context: Optional[AccessContext] = None,
        default: Any = None
    ) -> Any:
        """Get just the value of a trait (convenience method)."""
        trait = await self.get(path, context)
        return trait.value if trait else default
    
    async def get_all(
        self,
        domain: Optional[str] = None,
        context: Optional[AccessContext] = None
    ) -> Dict[str, Trait]:
        """Get all traits, optionally filtered by domain."""
        self._check_permission(context, require_read=True, domain=domain)
        
        identity = await self.get_active_identity()
        
        if domain:
            return identity.traits_by_domain.get(domain, {})
        
        # Flatten all domains
        result = {}
        for domain_name, traits in identity.traits_by_domain.items():
            for trait_name, trait in traits.items():
                result[f"{domain_name}.{trait_name}"] = trait
        return result
    
    async def get_domains(self, context: Optional[AccessContext] = None) -> List[str]:
        """Get list of domains with data."""
        self._check_permission(context, require_read=True)
        
        identity = await self.get_active_identity()
        return list(identity.traits_by_domain.keys())
    
    # ============================================================
    # TRAIT ACCESS - WRITE
    # ============================================================
    
    async def set(
        self,
        path: str,
        value: Any,
        confidence: float = 1.0,
        framework: Optional[TraitFramework] = None,
        source: str = "system",
        context: Optional[AccessContext] = None,
        auto_save: bool = True
    ) -> Trait:
        """
        Set a trait value.
        
        Args:
            path: Trait path (domain.name format required)
            value: The value to set
            confidence: Confidence level (0-1)
            framework: Optional framework the trait belongs to
            source: Source of this value (agent, user, etc.)
            context: Access context with permissions
            auto_save: Whether to auto-save the identity
            
        Returns:
            The created/updated Trait
        """
        self._check_permission(context, require_write=True, path=path)
        
        # Parse path
        parts = path.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid path format: {path}. Expected 'domain.trait_name'")
        
        domain, name = parts
        
        # Check domain permission
        if context:
            if not context.permission.can_write(path=path, domain=domain):
                raise PermissionError(f"No write access to {path}")
        
        identity = await self.get_active_identity()
        existing = identity.get_trait(path)
        
        # Create or update trait
        if existing:
            # Update existing - add to history
            trait = existing.with_update(
                value=value,
                confidence=confidence,
                source_type=source,
                source_agent=context.accessor_id if context else "unknown"
            )
            event_type = EventType.TRAIT_UPDATED
        else:
            # Create new trait
            trait = Trait.create(
                name=name,
                category=self._infer_category(name, domain),
                framework=framework,
                value=value,
                confidence=confidence,
                source_type=source,
                source_agent=context.accessor_id if context else "unknown"
            )
            event_type = EventType.TRAIT_ADDED
        
        # Validate
        errors = self._validator.validate(trait)
        if errors:
            raise ValueError(f"Trait validation failed: {errors}")
        
        # Store
        identity.set_trait(path, trait)
        
        # Update high-level attributes if applicable
        self._update_high_level_attrs(identity, path, value)
        
        # Emit event
        if event_type == EventType.TRAIT_ADDED:
            event = TraitAddedEvent(
                trait_path=path,
                trait_name=name,
                domain=domain,
                value=value,
                confidence=confidence
            )
        else:
            event = TraitUpdatedEvent(
                trait_path=path,
                trait_name=name,
                domain=domain,
                old_value=existing.value if existing else None,
                new_value=value,
                old_confidence=existing.confidence if existing else 0,
                new_confidence=confidence
            )
        
        await self._bus.emit(event)
        
        # Auto-save
        if auto_save:
            await self.save_identity(context)
        
        return trait
    
    async def delete(
        self,
        path: str,
        context: Optional[AccessContext] = None
    ) -> bool:
        """Delete a trait."""
        self._check_permission(context, require_delete=True, path=path)
        
        identity = await self.get_active_identity()
        
        parts = path.split(".", 1)
        if len(parts) != 2:
            return False
        
        domain, name = parts
        
        if domain in identity.traits_by_domain:
            if name in identity.traits_by_domain[domain]:
                del identity.traits_by_domain[domain][name]
                await self.save_identity(context)
                return True
        
        return False
    
    # ============================================================
    # QUERY INTERFACE
    # ============================================================
    
    async def query(
        self,
        query: Union[Dict[str, Any], QueryBuilder],
        context: Optional[AccessContext] = None
    ) -> QueryResult:
        """
        Execute a query against the Digital Twin.
        
        Args:
            query: Query specification (dict or QueryBuilder)
            context: Access context with permissions
            
        Returns:
            QueryResult with matching traits
        """
        self._check_permission(context, require_read=True)
        
        start_time = time.time()
        
        # Convert QueryBuilder to dict if needed
        if isinstance(query, QueryBuilder):
            query = query.build()
        
        identity = await self.get_active_identity()
        
        # Get domains to search
        domains = query.get("domains", [])
        if query.get("domain"):
            domains = [query["domain"]]
        if not domains:
            domains = list(identity.traits_by_domain.keys())
        
        # Check domain permissions
        if context:
            domains = [d for d in domains if context.permission.can_read(domain=d)]
        
        # Collect matching traits
        results = []
        conditions = [
            QueryCondition(
                field=c["field"],
                operator=c["operator"],
                value=c["value"]
            )
            for c in query.get("conditions", [])
        ]
        min_confidence = query.get("min_confidence")
        
        for domain in domains:
            traits = identity.traits_by_domain.get(domain, {})
            for name, trait in traits.items():
                # Check confidence threshold
                if min_confidence and trait.confidence < min_confidence:
                    continue
                
                # Check conditions
                trait_dict = {
                    "name": trait.name,
                    "value": trait.value,
                    "confidence": trait.confidence,
                    "category": trait.category.value if hasattr(trait.category, 'value') else trait.category,
                    "framework": trait.framework.value if trait.framework and hasattr(trait.framework, 'value') else trait.framework,
                    "domain": domain,
                    "path": f"{domain}.{name}"
                }
                
                matches = all(c.matches(trait_dict) for c in conditions)
                if matches:
                    results.append({
                        "path": f"{domain}.{name}",
                        "trait": trait,
                        **trait_dict
                    })
        
        total = len(results)
        
        # Sort
        if query.get("sort_field"):
            reverse = query.get("sort_order") == "desc"
            results.sort(
                key=lambda x: x.get(query["sort_field"], 0),
                reverse=reverse
            )
        
        # Pagination
        offset = query.get("offset", 0)
        limit = query.get("limit")
        
        if offset:
            results = results[offset:]
        if limit:
            results = results[:limit]
        
        elapsed = (time.time() - start_time) * 1000
        
        return QueryResult(
            success=True,
            data=results,
            count=len(results),
            total=total,
            query_time_ms=elapsed
        )
    
    # ============================================================
    # SUMMARY & EXPORT
    # ============================================================
    
    async def get_summary(
        self,
        context: Optional[AccessContext] = None
    ) -> Dict[str, Any]:
        """Get a summary of the Digital Twin."""
        self._check_permission(context, require_read=True)
        
        identity = await self.get_active_identity()
        return identity.to_summary()
    
    async def export(
        self,
        context: Optional[AccessContext] = None
    ) -> Dict[str, Any]:
        """Export the full Digital Twin."""
        self._check_permission(context, require_read=True)
        
        identity = await self.get_active_identity()
        return identity.to_dict()
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _check_permission(
        self,
        context: Optional[AccessContext],
        require_read: bool = False,
        require_write: bool = False,
        require_delete: bool = False,
        path: Optional[str] = None,
        domain: Optional[str] = None
    ) -> None:
        """Check if the access context has required permissions."""
        if context is None:
            # No context = anonymous read-only access
            if require_write or require_delete:
                raise PermissionError("Write/delete requires access context")
            return
        
        if require_read and not context.permission.can_read(path=path, domain=domain):
            raise PermissionError(f"Read access denied for {path or domain or 'resource'}")
        
        if require_write and not context.permission.can_write(path=path, domain=domain):
            raise PermissionError(f"Write access denied for {path or domain or 'resource'}")
        
        if require_delete and not context.permission.can_delete(path=path, domain=domain):
            raise PermissionError(f"Delete access denied for {path or domain or 'resource'}")
    
    def _infer_category(self, name: str, domain: str) -> TraitCategory:
        """Infer trait category from name and domain."""
        name_lower = name.lower()
        
        # Domain-based inference
        if domain == "genesis":
            if "hd_" in name_lower or "human_design" in name_lower:
                return TraitCategory.HUMAN_DESIGN
            if "jung" in name_lower:
                return TraitCategory.JUNGIAN
            if "soma" in name_lower or "body" in name_lower:
                return TraitCategory.SOMATIC
        
        # Name-based inference
        if any(x in name_lower for x in ["emotion", "feeling", "mood"]):
            return TraitCategory.EMOTIONAL
        if any(x in name_lower for x in ["think", "reason", "logic"]):
            return TraitCategory.COGNITIVE
        if any(x in name_lower for x in ["value", "belief", "meaning"]):
            return TraitCategory.VALUES
        
        return TraitCategory.MISC
    
    def _update_high_level_attrs(self, identity: Identity, path: str, value: Any) -> None:
        """Update high-level identity attributes when relevant traits change."""
        if path == "genesis.hd_type":
            identity.hd_type = value
        elif path == "genesis.jung_dominant":
            identity.jung_dominant = value
        elif path == "genesis.energy_pattern":
            identity.energy_pattern = value


# Convenience function
async def get_twin_accessor() -> TwinAccessor:
    """Get the singleton TwinAccessor instance."""
    return await TwinAccessor.get_instance()
