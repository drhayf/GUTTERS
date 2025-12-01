"""
Identity - The Persistent User Profile

Represents the user's complete identity that persists across sessions.
This is the "save file" that contains all accumulated knowledge about the user.

@module Identity
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from enum import Enum

from ..traits import Trait


class IdentityStatus(str, Enum):
    """Status of an identity."""
    ACTIVE = "active"           # Currently in use
    ARCHIVED = "archived"       # Kept for reference
    MIGRATING = "migrating"     # Being transferred


@dataclass
class IdentityMetadata:
    """
    Metadata about an identity (without the full trait data).
    
    Used for listing/selecting identities.
    """
    id: str
    name: str
    created_at: datetime
    last_accessed: datetime
    version: int
    status: IdentityStatus
    
    # Summary stats
    trait_count: int = 0
    domain_count: int = 0
    session_count: int = 0
    completion_percentage: float = 0.0
    
    # Essence
    essence_statement: Optional[str] = None
    primary_archetype: Optional[str] = None
    hd_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "version": self.version,
            "status": self.status.value,
            "trait_count": self.trait_count,
            "domain_count": self.domain_count,
            "session_count": self.session_count,
            "completion_percentage": self.completion_percentage,
            "essence_statement": self.essence_statement,
            "primary_archetype": self.primary_archetype,
            "hd_type": self.hd_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityMetadata":
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            version=data.get("version", 1),
            status=IdentityStatus(data.get("status", "active")),
            trait_count=data.get("trait_count", 0),
            domain_count=data.get("domain_count", 0),
            session_count=data.get("session_count", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            essence_statement=data.get("essence_statement"),
            primary_archetype=data.get("primary_archetype"),
            hd_type=data.get("hd_type"),
        )


@dataclass
class Identity:
    """
    The complete persistent identity of a user.
    
    Contains:
    - All traits organized by domain
    - Session history
    - Evolution timeline
    - Synthesis data (essence statement, archetypes)
    
    This is the data structure that gets saved/loaded from storage.
    """
    # Core identity
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Default Profile"
    status: IdentityStatus = IdentityStatus.ACTIVE
    
    # Versioning
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_modified: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    # Traits by domain
    traits: Dict[str, Dict[str, Trait]] = field(default_factory=dict)
    
    # Session tracking
    session_ids: List[str] = field(default_factory=list)
    session_count: int = 0
    
    # Synthesis
    essence_statement: Optional[str] = None
    archetypes: Dict[str, Any] = field(default_factory=dict)
    
    # High-level attributes (for quick access)
    hd_type: Optional[str] = None
    hd_authority: Optional[str] = None
    hd_profile: Optional[str] = None
    jung_dominant: Optional[str] = None
    
    # Stats
    total_interactions: int = 0
    
    # -------------------------------------------------------------------------
    # Trait Management
    # -------------------------------------------------------------------------
    
    def get_trait(self, path: str) -> Optional[Trait]:
        """
        Get a trait by path.
        
        Path format: "domain.trait_name"
        """
        parts = path.split(".", 1)
        if len(parts) != 2:
            return None
        
        domain_id, trait_name = parts
        domain_traits = self.traits.get(domain_id, {})
        return domain_traits.get(trait_name)
    
    def set_trait(self, trait: Trait) -> None:
        """
        Set a trait (add or update).
        """
        domain_id = trait.domain
        
        if domain_id not in self.traits:
            self.traits[domain_id] = {}
        
        self.traits[domain_id][trait.name] = trait
        self.last_modified = datetime.utcnow()
        self.version += 1
        
        # Update high-level attributes if applicable
        self._update_high_level_attribute(trait)
    
    def remove_trait(self, path: str) -> bool:
        """
        Remove a trait by path.
        
        Returns True if found and removed.
        """
        parts = path.split(".", 1)
        if len(parts) != 2:
            return False
        
        domain_id, trait_name = parts
        domain_traits = self.traits.get(domain_id)
        if domain_traits and trait_name in domain_traits:
            del domain_traits[trait_name]
            self.last_modified = datetime.utcnow()
            self.version += 1
            return True
        return False
    
    def get_domain_traits(self, domain_id: str) -> List[Trait]:
        """Get all traits for a domain."""
        return list(self.traits.get(domain_id, {}).values())
    
    def get_all_traits(self) -> List[Trait]:
        """Get all traits across all domains."""
        all_traits = []
        for domain_traits in self.traits.values():
            all_traits.extend(domain_traits.values())
        return all_traits
    
    def get_trait_count(self) -> int:
        """Get total trait count."""
        return sum(len(dt) for dt in self.traits.values())
    
    def get_domain_count(self) -> int:
        """Get number of domains with traits."""
        return len([d for d in self.traits.values() if d])
    
    def _update_high_level_attribute(self, trait: Trait) -> None:
        """Update high-level attributes from trait if applicable."""
        if trait.domain == "genesis":
            if trait.name == "hd_type":
                self.hd_type = trait.value
            elif trait.name == "hd_authority":
                self.hd_authority = trait.value
            elif trait.name == "hd_profile":
                self.hd_profile = trait.value
            elif trait.name == "jung_dominant":
                self.jung_dominant = trait.value
    
    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    
    def record_session(self, session_id: str) -> None:
        """Record a session associated with this identity."""
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)
        self.session_count = len(self.session_ids)
        self.last_accessed = datetime.utcnow()
    
    # -------------------------------------------------------------------------
    # Completion
    # -------------------------------------------------------------------------
    
    def get_completion_percentage(self) -> float:
        """
        Calculate overall profile completion.
        
        Based on key traits having high confidence.
        """
        key_traits = [
            "genesis.hd_type",
            "genesis.hd_authority",
            "genesis.jung_dominant",
            "genesis.energy_pattern",
            "genesis.core_wound",
            "genesis.core_gift",
            "genesis.decision_style",
        ]
        
        filled = 0
        for path in key_traits:
            trait = self.get_trait(path)
            if trait and trait.confidence >= 0.7:
                filled += 1
        
        return filled / len(key_traits) if key_traits else 0.0
    
    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------
    
    def get_metadata(self) -> IdentityMetadata:
        """Get metadata summary for this identity."""
        return IdentityMetadata(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            last_accessed=self.last_accessed,
            version=self.version,
            status=self.status,
            trait_count=self.get_trait_count(),
            domain_count=self.get_domain_count(),
            session_count=self.session_count,
            completion_percentage=self.get_completion_percentage(),
            essence_statement=self.essence_statement,
            primary_archetype=self.archetypes.get("primary"),
            hd_type=self.hd_type,
        )
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        # Serialize traits
        traits_dict = {}
        for domain_id, domain_traits in self.traits.items():
            traits_dict[domain_id] = {
                name: trait.to_dict()
                for name, trait in domain_traits.items()
            }
        
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "traits": traits_dict,
            "session_ids": self.session_ids,
            "session_count": self.session_count,
            "essence_statement": self.essence_statement,
            "archetypes": self.archetypes,
            "hd_type": self.hd_type,
            "hd_authority": self.hd_authority,
            "hd_profile": self.hd_profile,
            "jung_dominant": self.jung_dominant,
            "total_interactions": self.total_interactions,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Identity":
        """Create from dictionary."""
        identity = cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", "Unnamed Profile"),
            status=IdentityStatus(data.get("status", "active")),
            version=data.get("version", 1),
            essence_statement=data.get("essence_statement"),
            archetypes=data.get("archetypes", {}),
            hd_type=data.get("hd_type"),
            hd_authority=data.get("hd_authority"),
            hd_profile=data.get("hd_profile"),
            jung_dominant=data.get("jung_dominant"),
            total_interactions=data.get("total_interactions", 0),
        )
        
        # Parse timestamps
        if "created_at" in data:
            identity.created_at = datetime.fromisoformat(data["created_at"])
        if "last_modified" in data:
            identity.last_modified = datetime.fromisoformat(data["last_modified"])
        if "last_accessed" in data:
            identity.last_accessed = datetime.fromisoformat(data["last_accessed"])
        
        # Parse traits
        for domain_id, domain_traits_data in data.get("traits", {}).items():
            identity.traits[domain_id] = {}
            for trait_name, trait_data in domain_traits_data.items():
                identity.traits[domain_id][trait_name] = Trait.from_dict(trait_data)
        
        # Parse sessions
        identity.session_ids = data.get("session_ids", [])
        identity.session_count = data.get("session_count", len(identity.session_ids))
        
        return identity
    
    def to_summary(self) -> Dict[str, Any]:
        """Get condensed summary for context injection."""
        high_conf_traits = {}
        for domain_id, domain_traits in self.traits.items():
            for name, trait in domain_traits.items():
                if trait.is_high_confidence:
                    if domain_id not in high_conf_traits:
                        high_conf_traits[domain_id] = []
                    high_conf_traits[domain_id].append({
                        "name": name,
                        "value": trait.value,
                        "confidence": trait.confidence,
                    })
        
        return {
            "id": self.id,
            "name": self.name,
            "essence": self.essence_statement,
            "hd_type": self.hd_type,
            "hd_authority": self.hd_authority,
            "jung_dominant": self.jung_dominant,
            "archetypes": self.archetypes,
            "traits": high_conf_traits,
            "completion": self.get_completion_percentage(),
        }
