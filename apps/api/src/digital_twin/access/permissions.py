"""
Access Permissions - Permission Levels for Digital Twin Access

Defines permission levels for controlling who can do what
with the Digital Twin data.

@module Permissions
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PermissionLevel(str, Enum):
    """Permission levels for access control."""
    NONE = "none"           # No access
    READ = "read"           # Read-only access
    WRITE = "write"         # Read + write (not delete)
    ADMIN = "admin"         # Full access including delete
    SOVEREIGN = "sovereign" # Unrestricted access (for Sovereign Agent)


@dataclass
class AccessPermission:
    """
    Permission configuration for an accessor.
    
    Defines what an accessor (agent, tool, etc.) can do.
    """
    level: PermissionLevel = PermissionLevel.READ
    
    # Domain restrictions (empty = all domains)
    allowed_domains: Set[str] = field(default_factory=set)
    denied_domains: Set[str] = field(default_factory=set)
    
    # Trait restrictions
    allowed_trait_prefixes: Set[str] = field(default_factory=set)
    denied_trait_prefixes: Set[str] = field(default_factory=set)
    
    # Identity restrictions
    allowed_identity_ids: Set[str] = field(default_factory=set)
    
    def can_read(self, path: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """Check if read is allowed."""
        if self.level == PermissionLevel.NONE:
            return False
        
        if domain:
            if self.denied_domains and domain in self.denied_domains:
                return False
            if self.allowed_domains and domain not in self.allowed_domains:
                return False
        
        if path:
            if self.denied_trait_prefixes:
                if any(path.startswith(p) for p in self.denied_trait_prefixes):
                    return False
            if self.allowed_trait_prefixes:
                if not any(path.startswith(p) for p in self.allowed_trait_prefixes):
                    return False
        
        return True
    
    def can_write(self, path: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """Check if write is allowed."""
        if self.level not in [PermissionLevel.WRITE, PermissionLevel.ADMIN, PermissionLevel.SOVEREIGN]:
            return False
        
        return self.can_read(path, domain)
    
    def can_delete(self, path: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """Check if delete is allowed."""
        if self.level not in [PermissionLevel.ADMIN, PermissionLevel.SOVEREIGN]:
            return False
        
        return self.can_read(path, domain)
    
    def can_access_identity(self, identity_id: str) -> bool:
        """Check if access to a specific identity is allowed."""
        if not self.allowed_identity_ids:
            return True
        return identity_id in self.allowed_identity_ids
    
    @classmethod
    def read_only(cls) -> "AccessPermission":
        """Create read-only permission."""
        return cls(level=PermissionLevel.READ)
    
    @classmethod
    def read_write(cls) -> "AccessPermission":
        """Create read-write permission."""
        return cls(level=PermissionLevel.WRITE)
    
    @classmethod
    def admin(cls) -> "AccessPermission":
        """Create admin permission."""
        return cls(level=PermissionLevel.ADMIN)
    
    @classmethod
    def sovereign(cls) -> "AccessPermission":
        """Create unrestricted sovereign permission."""
        return cls(level=PermissionLevel.SOVEREIGN)
    
    @classmethod
    def for_domain(cls, domain: str, level: PermissionLevel = PermissionLevel.WRITE) -> "AccessPermission":
        """Create permission restricted to a specific domain."""
        return cls(level=level, allowed_domains={domain})
