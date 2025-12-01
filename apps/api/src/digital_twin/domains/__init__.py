"""
Domain System - Pluggable Data Domains

This module provides the framework for pluggable data domains:
- BaseDomain: Abstract base class all domains implement
- DomainRegistry: Dynamic discovery and registration
- Core Types: DomainType, DomainTier, DomainCapability for classification
- Built-in domains: Genesis, Health, Nutrition, Journaling, Finance

Each domain encapsulates a specific area of understanding about the user.
Domains can be added without modifying existing code - just create a class
that inherits from BaseDomain and it's automatically registered.

DOMAIN HIERARCHY:
=================
CORE DOMAINS (always enabled, essential):
- Genesis: Profiling and Digital Twin creation
- Journaling: Self-reflection and insight capture

STANDARD DOMAINS (optional, can be disabled):
- Health (parent): Physical health coordination
  └── Nutrition (child): Complete implementation - THE reference domain
  └── Fitness (child): Scaffold - awaiting implementation
  └── Sleep (child): Scaffold - awaiting implementation
- Finance (parent): Financial tracking and insights
  └── Budgeting (child): Scaffold - awaiting implementation
  └── Investing (child): Scaffold - awaiting implementation

EXTENSION DOMAINS (third-party, future):
- Coming soon...

@module Domains
"""

from .base import (
    BaseDomain,
    DomainSchema,
    DomainQuery,
    DomainResponse,
    TraitSchema,
)
from .registry import (
    DomainRegistry,
    get_domain_registry,
)

# Core types for domain classification
from .core_types import (
    DomainType,
    DomainTier,
    DomainCapability,
    DomainMetadata,
    CoreDomainConfig,
    CORE_DOMAINS,
    CoreDomainId,
    OptionalDomainId,
)

# Built-in domains
from .genesis import GenesisDomain
from .health import HealthDomain
from .journaling import JournalingDomain
from .finance import FinanceDomain

# Nutrition sub-domain (complete implementation)
from .nutrition import NutritionDomain

__all__ = [
    # Base classes
    "BaseDomain",
    "DomainSchema",
    "DomainQuery",
    "DomainResponse",
    "TraitSchema",
    
    # Registry
    "DomainRegistry",
    "get_domain_registry",
    
    # Core types
    "DomainType",
    "DomainTier",
    "DomainCapability",
    "DomainMetadata",
    "CoreDomainConfig",
    "CORE_DOMAINS",
    "CoreDomainId",
    "OptionalDomainId",
    
    # Domain implementations
    "GenesisDomain",
    "HealthDomain",
    "JournalingDomain",
    "FinanceDomain",
    "NutritionDomain",
]
