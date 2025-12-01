"""
Access Layer - Unified Read/Write Interface

This module provides the unified interface for accessing the Digital Twin:
- TwinAccessor: The main access class
- QueryBuilder: Fluent API for building queries
- AccessPermission: Permission levels for access control

All reads and writes go through this layer, ensuring:
- Consistent access patterns
- Validation on writes
- Event emission on changes
- Permission checking

@module Access
"""

from .accessor import (
    TwinAccessor,
    AccessContext,
    get_twin_accessor,
)
from .query import (
    QueryBuilder,
    QueryResult,
    QueryCondition,
    QueryOperator,
    SortOrder,
)
from .permissions import (
    AccessPermission,
    PermissionLevel,
)

__all__ = [
    "TwinAccessor",
    "AccessContext",
    "get_twin_accessor",
    "QueryBuilder",
    "QueryResult",
    "QueryCondition",
    "QueryOperator",
    "SortOrder",
    "AccessPermission",
    "PermissionLevel",
]
