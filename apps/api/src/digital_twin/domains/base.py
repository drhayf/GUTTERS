"""
Domain Base Classes - Framework for Data Domains

Defines the abstract base class that all domains must implement.
A domain represents a specific area of understanding about the user.

Examples:
- Genesis Domain: HD type, Jungian functions, archetypes
- Health Domain: Sleep, nutrition, exercise, biometrics
- Finance Domain: Spending patterns, financial goals
- Relationships Domain: Communication style, attachment

Each domain:
1. Defines its trait schema (what traits it manages)
2. Provides methods to contribute to the Digital Twin
3. Handles domain-specific queries
4. Can have sub-agents for pattern detection

@module DomainBase
"""

from typing import Any, Dict, List, Optional, Set, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from ..traits import Trait, TraitCategory, TraitFramework


# =============================================================================
# DOMAIN SCHEMA
# =============================================================================

@dataclass
class TraitSchema:
    """
    Schema definition for a single trait within a domain.
    
    Defines:
    - Type constraints
    - Default values
    - Validation rules
    - Display metadata
    """
    name: str
    display_name: str
    description: str
    
    # Type
    value_type: str = "string"  # string, number, boolean, enum, scale
    enum_options: Optional[List[str]] = None
    scale_min: float = 0.0
    scale_max: float = 1.0
    unit: Optional[str] = None
    
    # Classification
    category: TraitCategory = TraitCategory.DETECTED
    frameworks: List[TraitFramework] = field(default_factory=list)
    
    # Defaults
    default_value: Optional[Any] = None
    is_required: bool = False
    
    # Display
    icon: str = "📝"
    priority: int = 0  # Higher = more important
    is_visible: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "value_type": self.value_type,
            "enum_options": self.enum_options,
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "unit": self.unit,
            "category": self.category.value,
            "frameworks": [f.value for f in self.frameworks],
            "default_value": self.default_value,
            "is_required": self.is_required,
            "icon": self.icon,
            "priority": self.priority,
            "is_visible": self.is_visible,
        }


@dataclass
class DomainSchema:
    """
    Complete schema for a domain.
    
    Defines all traits the domain manages and their constraints.
    """
    domain_id: str
    traits: Dict[str, TraitSchema] = field(default_factory=dict)
    
    def add_trait(self, schema: TraitSchema) -> None:
        """Add a trait schema."""
        self.traits[schema.name] = schema
    
    def get_trait(self, name: str) -> Optional[TraitSchema]:
        """Get a trait schema by name."""
        return self.traits.get(name)
    
    def validate_value(self, trait_name: str, value: Any) -> bool:
        """Validate a value against the trait schema."""
        schema = self.traits.get(trait_name)
        if not schema:
            return True  # Unknown trait, allow
        
        if schema.value_type == "enum" and schema.enum_options:
            return value in schema.enum_options
        
        if schema.value_type == "scale":
            return schema.scale_min <= value <= schema.scale_max
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "traits": {k: v.to_dict() for k, v in self.traits.items()},
        }


# =============================================================================
# DOMAIN QUERY/RESPONSE
# =============================================================================

@dataclass
class DomainQuery:
    """
    A query to a domain for specific data.
    
    Supports:
    - Getting specific traits
    - Filtering by confidence
    - Getting summaries
    """
    # What to query
    trait_names: Optional[List[str]] = None  # None = all
    
    # Filters
    min_confidence: float = 0.0
    only_verified: bool = False
    include_archived: bool = False
    
    # Output format
    format: str = "full"  # full, summary, values_only
    limit: Optional[int] = None
    
    # Time filters
    updated_since: Optional[datetime] = None
    updated_before: Optional[datetime] = None


@dataclass
class DomainResponse:
    """
    Response from a domain query.
    """
    success: bool = True
    domain_id: str = ""
    
    # Data
    traits: List[Trait] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    
    # Stats
    total_traits: int = 0
    high_confidence_count: int = 0
    
    # Errors
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "domain_id": self.domain_id,
            "traits": [t.to_summary() for t in self.traits],
            "summary": self.summary,
            "total_traits": self.total_traits,
            "high_confidence_count": self.high_confidence_count,
            "error": self.error,
        }


# =============================================================================
# BASE DOMAIN
# =============================================================================

class BaseDomain(ABC):
    """
    Abstract base class for all data domains.
    
    Subclass this to create a new domain:
    
        class NutritionDomain(BaseDomain):
            domain_id = "nutrition"
            display_name = "Nutrition"
            icon = "🥗"
            
            def get_schema(self) -> DomainSchema:
                schema = DomainSchema(domain_id=self.domain_id)
                schema.add_trait(TraitSchema(
                    name="dietary_preference",
                    display_name="Dietary Preference",
                    description="Primary dietary preference",
                    value_type="enum",
                    enum_options=["omnivore", "vegetarian", "vegan", "keto"],
                ))
                return schema
    
    The domain will be automatically registered when imported.
    """
    
    # Override these in subclass
    domain_id: str = "base"
    display_name: str = "Base Domain"
    description: str = ""
    icon: str = "📁"
    version: str = "1.0.0"
    
    # Priority for display ordering (higher = more important)
    priority: int = 0
    
    # Frameworks this domain relates to
    frameworks: List[TraitFramework] = []
    
    def __init__(self):
        self._traits: Dict[str, Trait] = {}
        self._schema: Optional[DomainSchema] = None
        self._initialized = False
    
    # -------------------------------------------------------------------------
    # Abstract Methods - Must Override
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_schema(self) -> DomainSchema:
        """
        Return the schema of traits this domain manages.
        
        Called once during initialization to register trait schemas.
        """
        pass
    
    # -------------------------------------------------------------------------
    # Optional Override Methods
    # -------------------------------------------------------------------------
    
    def initialize(self) -> None:
        """
        Called when domain is registered.
        
        Override for custom initialization.
        """
        self._schema = self.get_schema()
        self._initialized = True
    
    def on_trait_added(self, trait: Trait) -> None:
        """Called when a trait is added to this domain."""
        self._traits[trait.name] = trait
    
    def on_trait_updated(self, trait: Trait) -> None:
        """Called when a trait in this domain is updated."""
        self._traits[trait.name] = trait
    
    def on_trait_removed(self, trait_name: str) -> None:
        """Called when a trait is removed from this domain."""
        if trait_name in self._traits:
            del self._traits[trait_name]
    
    def query(self, query: DomainQuery) -> DomainResponse:
        """
        Handle a query for domain data.
        
        Override for custom query handling.
        """
        traits = list(self._traits.values())
        
        # Apply filters
        if query.trait_names:
            traits = [t for t in traits if t.name in query.trait_names]
        
        if query.min_confidence > 0:
            traits = [t for t in traits if t.confidence >= query.min_confidence]
        
        if query.only_verified:
            traits = [t for t in traits if t.is_verified]
        
        if not query.include_archived:
            traits = [t for t in traits if not t.is_archived]
        
        if query.updated_since:
            traits = [t for t in traits if t.last_updated >= query.updated_since]
        
        if query.updated_before:
            traits = [t for t in traits if t.last_updated <= query.updated_before]
        
        if query.limit:
            traits = traits[:query.limit]
        
        return DomainResponse(
            success=True,
            domain_id=self.domain_id,
            traits=traits,
            total_traits=len(self._traits),
            high_confidence_count=len([t for t in self._traits.values() if t.is_high_confidence]),
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a condensed summary of this domain.
        
        Used for context injection into LLM prompts.
        """
        high_conf_traits = [t for t in self._traits.values() if t.is_high_confidence]
        
        return {
            "domain": self.domain_id,
            "display_name": self.display_name,
            "icon": self.icon,
            "trait_count": len(self._traits),
            "high_confidence_traits": [
                {"name": t.name, "value": t.value, "confidence": t.confidence}
                for t in high_conf_traits
            ],
        }
    
    def get_completion_percentage(self) -> float:
        """
        Calculate how complete this domain's profile is.
        
        Based on required traits and confidence levels.
        """
        if not self._schema:
            return 0.0
        
        required = [s for s in self._schema.traits.values() if s.is_required]
        if not required:
            return 1.0 if self._traits else 0.0
        
        filled = 0
        for schema in required:
            trait = self._traits.get(schema.name)
            if trait and trait.confidence >= 0.7:
                filled += 1
        
        return filled / len(required)
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_trait(self, name: str) -> Optional[Trait]:
        """Get a trait by name."""
        return self._traits.get(name)
    
    def get_traits(self) -> List[Trait]:
        """Get all traits in this domain."""
        return list(self._traits.values())
    
    def get_trait_value(self, name: str, default: Any = None) -> Any:
        """Get just the value of a trait."""
        trait = self._traits.get(name)
        return trait.value if trait else default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert domain to dictionary."""
        return {
            "domain_id": self.domain_id,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "version": self.version,
            "priority": self.priority,
            "trait_count": len(self._traits),
            "completion": self.get_completion_percentage(),
            "summary": self.get_summary(),
        }
