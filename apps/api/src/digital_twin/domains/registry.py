"""
Domain Registry - Dynamic Domain Discovery

The DomainRegistry provides:
- Automatic domain registration on import
- Domain lookup by ID
- Domain listing and enumeration
- Schema aggregation across domains

Usage:
    # Register a domain (usually via decorator)
    @DomainRegistry.register
    class MyDomain(BaseDomain):
        domain_id = "my_domain"
        ...
    
    # Or register manually
    DomainRegistry.register(MyDomain)
    
    # Get a domain
    registry = get_domain_registry()
    genesis = registry.get("genesis")
    
    # List all domains
    all_domains = registry.get_all()

@module DomainRegistry
"""

from typing import Any, Dict, List, Optional, Type, Set
from datetime import datetime
import logging

from .base import BaseDomain, DomainSchema

logger = logging.getLogger(__name__)


class DomainRegistry:
    """
    Central registry for all data domains.
    
    Provides dynamic discovery and management of domains.
    Implemented as a class with class methods for decorator usage.
    """
    
    # Class-level storage
    _domains: Dict[str, Type[BaseDomain]] = {}
    _instances: Dict[str, BaseDomain] = {}
    _registration_order: List[str] = []
    
    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------
    
    @classmethod
    def register(cls, domain_class: Type[BaseDomain]) -> Type[BaseDomain]:
        """
        Register a domain class.
        
        Can be used as a decorator:
            @DomainRegistry.register
            class MyDomain(BaseDomain):
                ...
        
        Or called directly:
            DomainRegistry.register(MyDomain)
        """
        domain_id = domain_class.domain_id
        
        if domain_id in cls._domains:
            logger.warning(f"[DomainRegistry] Overwriting domain: {domain_id}")
        
        cls._domains[domain_id] = domain_class
        cls._registration_order.append(domain_id)
        
        logger.info(f"[DomainRegistry] Registered domain: {domain_id}")
        
        return domain_class
    
    @classmethod
    def unregister(cls, domain_id: str) -> bool:
        """
        Unregister a domain.
        
        Returns True if found and removed.
        """
        if domain_id in cls._domains:
            del cls._domains[domain_id]
            if domain_id in cls._instances:
                del cls._instances[domain_id]
            if domain_id in cls._registration_order:
                cls._registration_order.remove(domain_id)
            logger.info(f"[DomainRegistry] Unregistered domain: {domain_id}")
            return True
        return False
    
    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------
    
    @classmethod
    def get(cls, domain_id: str) -> Optional[BaseDomain]:
        """
        Get a domain instance by ID.
        
        Creates and caches the instance on first access.
        """
        if domain_id not in cls._domains:
            return None
        
        if domain_id not in cls._instances:
            # Create instance
            domain_class = cls._domains[domain_id]
            instance = domain_class()
            instance.initialize()
            cls._instances[domain_id] = instance
        
        return cls._instances[domain_id]
    
    @classmethod
    def get_class(cls, domain_id: str) -> Optional[Type[BaseDomain]]:
        """Get a domain class by ID (without instantiating)."""
        return cls._domains.get(domain_id)
    
    @classmethod
    def get_all(cls) -> List[BaseDomain]:
        """
        Get all registered domain instances.
        
        Creates instances for any not yet created.
        """
        domains = []
        for domain_id in cls._registration_order:
            instance = cls.get(domain_id)
            if instance:
                domains.append(instance)
        return domains
    
    @classmethod
    def get_all_ids(cls) -> List[str]:
        """Get all registered domain IDs."""
        return list(cls._registration_order)
    
    @classmethod
    def has(cls, domain_id: str) -> bool:
        """Check if a domain is registered."""
        return domain_id in cls._domains
    
    # -------------------------------------------------------------------------
    # Schema
    # -------------------------------------------------------------------------
    
    @classmethod
    def get_schema(cls, domain_id: str) -> Optional[DomainSchema]:
        """Get the schema for a specific domain."""
        domain = cls.get(domain_id)
        return domain.get_schema() if domain else None
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, DomainSchema]:
        """Get schemas for all registered domains."""
        return {
            domain.domain_id: domain.get_schema()
            for domain in cls.get_all()
        }
    
    @classmethod
    def get_trait_schema(cls, path: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific trait by path.
        
        Path format: "domain.trait_name"
        """
        parts = path.split(".", 1)
        if len(parts) != 2:
            return None
        
        domain_id, trait_name = parts
        schema = cls.get_schema(domain_id)
        if not schema:
            return None
        
        trait_schema = schema.get_trait(trait_name)
        return trait_schema.to_dict() if trait_schema else None
    
    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get registry statistics."""
        domains = cls.get_all()
        
        return {
            "registered_count": len(cls._domains),
            "instantiated_count": len(cls._instances),
            "domains": [
                {
                    "id": d.domain_id,
                    "name": d.display_name,
                    "icon": d.icon,
                    "trait_count": len(d._traits),
                    "priority": d.priority,
                }
                for d in domains
            ],
        }
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert registry to dictionary."""
        return {
            "domains": {
                domain.domain_id: domain.to_dict()
                for domain in cls.get_all()
            },
            "stats": cls.get_stats(),
        }
    
    # -------------------------------------------------------------------------
    # Reset (for testing)
    # -------------------------------------------------------------------------
    
    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing)."""
        cls._domains.clear()
        cls._instances.clear()
        cls._registration_order.clear()
        logger.info("[DomainRegistry] Reset")


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

def get_domain_registry() -> Type[DomainRegistry]:
    """Get the domain registry class."""
    return DomainRegistry
