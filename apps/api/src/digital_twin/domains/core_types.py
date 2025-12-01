"""
Core Domain Types - Foundation Types for Domain Architecture

This module defines the core type system for domains:
- DomainType: Core vs Optional domain classification
- DomainCapability: What a domain can do
- DomainDependency: Inter-domain relationships
- SubDomainConfig: How sub-domains attach to parent domains

Core Domains are always available and form the foundation of the system.
Optional Domains can be enabled/disabled by users.

The fractal pattern means:
- Each domain can have sub-domains
- Sub-domains can have their own sub-domains
- All follow the same interface and patterns

@module CoreDomainTypes
"""

from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


# =============================================================================
# DOMAIN CLASSIFICATION
# =============================================================================

class DomainType(str, Enum):
    """
    Classification of domains by their role in the system.
    
    CORE: Always available, cannot be disabled. Forms the foundation.
          Examples: genesis, health (container), journaling
    
    OPTIONAL: Can be enabled/disabled by user.
          Examples: astrology, numerology, gene_keys
    
    SUB: Lives under a parent domain. Enabled when parent is enabled.
          Examples: nutrition (under health), biometrics (under health)
    
    SYSTEM: Internal system domains, not user-facing.
          Examples: analytics, audit, cache
    """
    CORE = "core"
    OPTIONAL = "optional"
    SUB = "sub"
    SYSTEM = "system"


class DomainCapability(str, Enum):
    """
    Capabilities a domain can have.
    
    Used for:
    - Routing decisions (what domains can handle what)
    - Permission checking (what domains can write where)
    - Feature discovery (what the system can do)
    """
    # Data capabilities
    READ_TRAITS = "read_traits"           # Can read trait values
    WRITE_TRAITS = "write_traits"         # Can write trait values
    DELETE_TRAITS = "delete_traits"       # Can delete traits
    
    # Processing capabilities
    DETECT_PATTERNS = "detect_patterns"   # Can run pattern detection
    GENERATE_INSIGHTS = "generate_insights"  # Can generate insights
    SYNTHESIZE = "synthesize"             # Can synthesize across data
    
    # I/O capabilities
    PROCESS_IMAGES = "process_images"     # Can process images
    PROCESS_TEXT = "process_text"         # Can process text
    PROCESS_VOICE = "process_voice"       # Can process voice
    
    # Integration capabilities
    EXTERNAL_API = "external_api"         # Can call external APIs
    STORE_FILES = "store_files"           # Can store files
    SEND_NOTIFICATIONS = "send_notifications"  # Can send notifications
    
    # Calculation capabilities
    CALCULATE = "calculate"               # Can perform calculations
    PREDICT = "predict"                   # Can make predictions
    RECOMMEND = "recommend"               # Can make recommendations


class DomainState(str, Enum):
    """Runtime state of a domain."""
    INITIALIZING = "initializing"   # Being set up
    ACTIVE = "active"               # Ready and processing
    PAUSED = "paused"               # Temporarily paused
    DISABLED = "disabled"           # User-disabled
    ERROR = "error"                 # In error state
    MAINTENANCE = "maintenance"     # Under maintenance


class DomainTier(str, Enum):
    """
    Hierarchical tier of a domain in the domain tree.
    
    PARENT: Top-level domain that can have sub-domains.
            Examples: health, finance
    
    PEER: Independent domain at the same level.
          Examples: journaling, genesis
    
    CHILD: Sub-domain under a parent.
           Examples: nutrition (under health), budgeting (under finance)
    """
    PARENT = "parent"
    PEER = "peer"
    CHILD = "child"


# =============================================================================
# DOMAIN RELATIONSHIPS
# =============================================================================

@dataclass
class DomainDependency:
    """
    Defines a dependency relationship between domains.
    
    Examples:
    - nutrition depends on health (parent)
    - gene_keys depends on human_design (requires HD data)
    - synthesis depends on genesis (needs profile)
    """
    domain_id: str                          # The domain we depend on
    dependency_type: str = "required"       # required, optional, enhances
    min_version: Optional[str] = None       # Minimum version needed
    reason: str = ""                        # Why this dependency exists
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "dependency_type": self.dependency_type,
            "min_version": self.min_version,
            "reason": self.reason,
        }


@dataclass
class SubDomainConfig:
    """
    Configuration for how a sub-domain attaches to its parent.
    
    Sub-domains are domains that:
    - Live under a parent domain namespace
    - Inherit parent's enable/disable state
    - Can have their own traits, schemas, and logic
    - Follow the fractal extensibility pattern
    """
    parent_domain_id: str
    
    # Namespace isolation
    trait_prefix: str = ""                  # Prefix for trait names
    isolated_namespace: bool = False        # If True, traits are fully isolated
    
    # Parent relationship
    inherits_capabilities: bool = True      # Inherit parent's capabilities
    inherits_permissions: bool = True       # Inherit parent's permissions
    visible_to_parent: bool = True          # Parent can query our traits
    
    # Lifecycle
    auto_initialize: bool = True            # Initialize when parent initializes
    shared_event_bus: bool = True           # Share event bus with parent
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_domain_id": self.parent_domain_id,
            "trait_prefix": self.trait_prefix,
            "isolated_namespace": self.isolated_namespace,
            "inherits_capabilities": self.inherits_capabilities,
            "inherits_permissions": self.inherits_permissions,
            "visible_to_parent": self.visible_to_parent,
            "auto_initialize": self.auto_initialize,
            "shared_event_bus": self.shared_event_bus,
        }


# =============================================================================
# DOMAIN METADATA
# =============================================================================

@dataclass
class DomainMetadata:
    """
    Complete metadata about a domain.
    
    This is the "manifest" that describes everything about a domain
    without instantiating it.
    """
    domain_id: str
    display_name: str
    description: str = ""
    
    # Classification
    domain_type: DomainType = DomainType.OPTIONAL
    icon: str = "📁"
    color: str = "#6366f1"  # Indigo default
    
    # Version
    version: str = "1.0.0"
    api_version: str = "1"
    
    # Author
    author: str = "Project Sovereign"
    maintainer: str = ""
    
    # Categories for UI grouping
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Priority (higher = more prominent)
    priority: int = 0
    
    # Capabilities this domain has
    capabilities: Set[DomainCapability] = field(default_factory=set)
    
    # Dependencies on other domains
    dependencies: List[DomainDependency] = field(default_factory=list)
    
    # Sub-domain configuration (if this is a sub-domain)
    sub_domain_config: Optional[SubDomainConfig] = None
    
    # IDs of registered sub-domains
    sub_domain_ids: List[str] = field(default_factory=list)
    
    # Feature flags
    is_core: bool = False                   # Core domain, cannot disable
    is_beta: bool = False                   # Beta feature
    is_experimental: bool = False           # Experimental feature
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        # Set is_core based on domain_type
        if self.domain_type == DomainType.CORE:
            self.is_core = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "display_name": self.display_name,
            "description": self.description,
            "domain_type": self.domain_type.value,
            "icon": self.icon,
            "color": self.color,
            "version": self.version,
            "api_version": self.api_version,
            "author": self.author,
            "maintainer": self.maintainer,
            "category": self.category,
            "tags": self.tags,
            "priority": self.priority,
            "capabilities": [c.value for c in self.capabilities],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "sub_domain_config": self.sub_domain_config.to_dict() if self.sub_domain_config else None,
            "sub_domain_ids": self.sub_domain_ids,
            "is_core": self.is_core,
            "is_beta": self.is_beta,
            "is_experimental": self.is_experimental,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# DOMAIN EVENT TYPES
# =============================================================================

class DomainEventType(str, Enum):
    """Events that domains can emit and subscribe to."""
    # Lifecycle events
    DOMAIN_INITIALIZED = "domain_initialized"
    DOMAIN_ENABLED = "domain_enabled"
    DOMAIN_DISABLED = "domain_disabled"
    DOMAIN_ERROR = "domain_error"
    
    # Trait events
    TRAIT_ADDED = "trait_added"
    TRAIT_UPDATED = "trait_updated"
    TRAIT_DELETED = "trait_deleted"
    TRAIT_CONFIRMED = "trait_confirmed"
    
    # Processing events
    PATTERN_DETECTED = "pattern_detected"
    INSIGHT_GENERATED = "insight_generated"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    
    # External events
    IMAGE_PROCESSED = "image_processed"
    DATA_IMPORTED = "data_imported"
    DATA_EXPORTED = "data_exported"


@dataclass
class DomainEvent:
    """
    An event emitted by or for a domain.
    
    Events flow through the Digital Twin's event bus and
    can be subscribed to by any interested party.
    """
    event_type: DomainEventType
    domain_id: str
    
    # Payload
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    source: str = ""                       # What emitted this event
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None   # For tracing related events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "domain_id": self.domain_id,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }


# =============================================================================
# DOMAIN COMMUNICATION INTERFACE
# =============================================================================

@dataclass
class DomainMessage:
    """
    A message between domains.
    
    Used for inter-domain communication via the SwarmBus.
    """
    from_domain: str
    to_domain: str
    message_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    expects_response: bool = False
    timeout_ms: int = 5000
    priority: int = 5  # 1-10, higher = more urgent
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_domain": self.from_domain,
            "to_domain": self.to_domain,
            "message_type": self.message_type,
            "payload": self.payload,
            "expects_response": self.expects_response,
            "timeout_ms": self.timeout_ms,
            "priority": self.priority,
        }


# Type alias for domain message handlers
DomainMessageHandler = Callable[[DomainMessage], Awaitable[Optional[Dict[str, Any]]]]


# =============================================================================
# CORE DOMAIN CONFIGURATION
# =============================================================================

@dataclass
class CoreDomainConfig:
    """
    Configuration for a core domain.
    
    Core domains are always enabled and cannot be disabled.
    This configuration defines their properties.
    """
    domain_id: str
    display_name: str
    description: str
    icon: str = "📁"
    priority: int = 0
    sub_domain_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "priority": self.priority,
            "sub_domain_ids": self.sub_domain_ids,
        }


# =============================================================================
# CORE DOMAIN IDS - The Foundation
# =============================================================================

class CoreDomainId:
    """
    Pre-defined IDs for core system domains.
    
    These are the foundational domains that cannot be disabled
    and form the backbone of the system.
    """
    # Profile and identity
    GENESIS = "genesis"
    
    # Container domains (these aggregate sub-domains)
    HEALTH = "health"
    
    # Core user interaction
    JOURNALING = "journaling"
    
    # System
    SYSTEM = "system"


# Set of all core domain IDs for easy lookup
CORE_DOMAINS: Set[str] = {
    CoreDomainId.GENESIS,
    CoreDomainId.HEALTH,
    CoreDomainId.JOURNALING,
    CoreDomainId.SYSTEM,
}


class OptionalDomainId:
    """
    Pre-defined IDs for optional domains.
    
    These can be enabled/disabled by users.
    """
    # Wisdom frameworks (under Genesis umbrella)
    HUMAN_DESIGN = "human_design"
    GENE_KEYS = "gene_keys"
    ASTROLOGY = "astrology"
    NUMEROLOGY = "numerology"
    ENNEAGRAM = "enneagram"
    
    # Life management
    FINANCE = "finance"
    
    # Health sub-domains
    NUTRITION = "nutrition"
    BIOMETRICS = "biometrics"
    SLEEP = "sleep"
    FITNESS = "fitness"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_core_domain(domain_id: str) -> bool:
    """Check if a domain ID is a core domain."""
    core_ids = [
        CoreDomainId.GENESIS,
        CoreDomainId.HEALTH,
        CoreDomainId.JOURNALING,
        CoreDomainId.SYSTEM,
    ]
    return domain_id in core_ids


def get_domain_hierarchy(domain_id: str) -> List[str]:
    """
    Get the hierarchy path for a domain.
    
    Examples:
    - "nutrition" -> ["health", "nutrition"]
    - "genesis" -> ["genesis"]
    - "sleep" -> ["health", "sleep"]
    """
    # Define parent mappings
    parent_map = {
        OptionalDomainId.NUTRITION: CoreDomainId.HEALTH,
        OptionalDomainId.BIOMETRICS: CoreDomainId.HEALTH,
        OptionalDomainId.SLEEP: CoreDomainId.HEALTH,
        OptionalDomainId.FITNESS: CoreDomainId.HEALTH,
    }
    
    if domain_id in parent_map:
        parent = parent_map[domain_id]
        return [parent, domain_id]
    
    return [domain_id]
