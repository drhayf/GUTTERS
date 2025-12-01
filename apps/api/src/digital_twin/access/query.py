"""
Query Builder - Fluent Query Interface for Digital Twin

Provides a clean API for building complex queries across
domains and traits.

@module Query
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class QueryOperator(str, Enum):
    """Operators for query conditions."""
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    STARTS_WITH = "starts"
    ENDS_WITH = "ends"
    MATCHES = "matches"  # Regex
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class SortOrder(str, Enum):
    """Sort order for results."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class QueryCondition:
    """A single query condition."""
    field: str
    operator: QueryOperator
    value: Any = None
    
    def matches(self, obj: Dict[str, Any]) -> bool:
        """Check if an object matches this condition."""
        # Navigate nested fields
        parts = self.field.split(".")
        current = obj
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                if self.operator == QueryOperator.NOT_EXISTS:
                    return True
                return False
            current = current[part]
        
        if self.operator == QueryOperator.EXISTS:
            return True
        if self.operator == QueryOperator.NOT_EXISTS:
            return False
        
        # Compare values
        if self.operator == QueryOperator.EQUALS:
            return current == self.value
        elif self.operator == QueryOperator.NOT_EQUALS:
            return current != self.value
        elif self.operator == QueryOperator.GREATER_THAN:
            return current > self.value
        elif self.operator == QueryOperator.GREATER_EQUAL:
            return current >= self.value
        elif self.operator == QueryOperator.LESS_THAN:
            return current < self.value
        elif self.operator == QueryOperator.LESS_EQUAL:
            return current <= self.value
        elif self.operator == QueryOperator.IN:
            return current in self.value
        elif self.operator == QueryOperator.NOT_IN:
            return current not in self.value
        elif self.operator == QueryOperator.CONTAINS:
            return self.value in current if isinstance(current, (str, list)) else False
        elif self.operator == QueryOperator.STARTS_WITH:
            return current.startswith(self.value) if isinstance(current, str) else False
        elif self.operator == QueryOperator.ENDS_WITH:
            return current.endswith(self.value) if isinstance(current, str) else False
        elif self.operator == QueryOperator.MATCHES:
            import re
            return bool(re.match(self.value, str(current)))
        
        return False


@dataclass
class QueryResult:
    """Result of a Digital Twin query."""
    success: bool = True
    data: Any = None
    count: int = 0
    total: int = 0
    error: Optional[str] = None
    query_time_ms: float = 0.0
    
    @classmethod
    def empty(cls) -> "QueryResult":
        """Create an empty result."""
        return cls(success=True, data=[], count=0, total=0)
    
    @classmethod
    def single(cls, data: Any) -> "QueryResult":
        """Create a result with single item."""
        return cls(success=True, data=data, count=1, total=1)
    
    @classmethod
    def many(cls, data: List[Any], total: Optional[int] = None) -> "QueryResult":
        """Create a result with multiple items."""
        count = len(data)
        return cls(success=True, data=data, count=count, total=total or count)
    
    @classmethod
    def error(cls, message: str) -> "QueryResult":
        """Create an error result."""
        return cls(success=False, error=message)
    
    def first(self) -> Optional[Any]:
        """Get first result or None."""
        if isinstance(self.data, list) and self.data:
            return self.data[0]
        elif not isinstance(self.data, list):
            return self.data
        return None


@dataclass 
class QueryBuilder:
    """
    Fluent query builder for Digital Twin data.
    
    Usage:
        query = QueryBuilder() \
            .from_domain("genesis") \
            .where("category", "personality") \
            .confidence_above(0.7) \
            .limit(10) \
            .build()
    """
    _domain: Optional[str] = None
    _domains: List[str] = field(default_factory=list)
    _conditions: List[QueryCondition] = field(default_factory=list)
    _include_fields: List[str] = field(default_factory=list)
    _exclude_fields: List[str] = field(default_factory=list)
    _sort_field: Optional[str] = None
    _sort_order: SortOrder = SortOrder.DESC
    _limit: Optional[int] = None
    _offset: int = 0
    _min_confidence: Optional[float] = None
    _include_history: bool = False
    
    def from_domain(self, domain: str) -> "QueryBuilder":
        """Query from a specific domain."""
        self._domain = domain
        return self
    
    def from_domains(self, *domains: str) -> "QueryBuilder":
        """Query from multiple domains."""
        self._domains = list(domains)
        return self
    
    def where(self, field: str, value: Any, operator: QueryOperator = QueryOperator.EQUALS) -> "QueryBuilder":
        """Add a condition."""
        self._conditions.append(QueryCondition(field=field, operator=operator, value=value))
        return self
    
    def where_eq(self, field: str, value: Any) -> "QueryBuilder":
        """Shortcut for equals condition."""
        return self.where(field, value, QueryOperator.EQUALS)
    
    def where_gt(self, field: str, value: Any) -> "QueryBuilder":
        """Shortcut for greater than."""
        return self.where(field, value, QueryOperator.GREATER_THAN)
    
    def where_gte(self, field: str, value: Any) -> "QueryBuilder":
        """Shortcut for greater than or equal."""
        return self.where(field, value, QueryOperator.GREATER_EQUAL)
    
    def where_lt(self, field: str, value: Any) -> "QueryBuilder":
        """Shortcut for less than."""
        return self.where(field, value, QueryOperator.LESS_THAN)
    
    def where_lte(self, field: str, value: Any) -> "QueryBuilder":
        """Shortcut for less than or equal."""
        return self.where(field, value, QueryOperator.LESS_EQUAL)
    
    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """Shortcut for in list."""
        return self.where(field, values, QueryOperator.IN)
    
    def where_contains(self, field: str, value: str) -> "QueryBuilder":
        """Shortcut for contains."""
        return self.where(field, value, QueryOperator.CONTAINS)
    
    def where_exists(self, field: str) -> "QueryBuilder":
        """Field must exist."""
        return self.where(field, None, QueryOperator.EXISTS)
    
    def confidence_above(self, threshold: float) -> "QueryBuilder":
        """Only traits with confidence above threshold."""
        self._min_confidence = threshold
        return self
    
    def include(self, *fields: str) -> "QueryBuilder":
        """Include only these fields in result."""
        self._include_fields.extend(fields)
        return self
    
    def exclude(self, *fields: str) -> "QueryBuilder":
        """Exclude these fields from result."""
        self._exclude_fields.extend(fields)
        return self
    
    def with_history(self) -> "QueryBuilder":
        """Include trait history in results."""
        self._include_history = True
        return self
    
    def sort_by(self, field: str, order: SortOrder = SortOrder.DESC) -> "QueryBuilder":
        """Sort results by field."""
        self._sort_field = field
        self._sort_order = order
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Limit number of results."""
        self._limit = n
        return self
    
    def offset(self, n: int) -> "QueryBuilder":
        """Offset for pagination."""
        self._offset = n
        return self
    
    def page(self, page_num: int, page_size: int = 20) -> "QueryBuilder":
        """Convenience for pagination."""
        self._offset = (page_num - 1) * page_size
        self._limit = page_size
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the query specification."""
        return {
            "domain": self._domain,
            "domains": self._domains,
            "conditions": [
                {"field": c.field, "operator": c.operator.value, "value": c.value}
                for c in self._conditions
            ],
            "include_fields": self._include_fields,
            "exclude_fields": self._exclude_fields,
            "sort_field": self._sort_field,
            "sort_order": self._sort_order.value if self._sort_field else None,
            "limit": self._limit,
            "offset": self._offset,
            "min_confidence": self._min_confidence,
            "include_history": self._include_history,
        }
    
    def copy(self) -> "QueryBuilder":
        """Create a copy of this query builder."""
        import copy
        return copy.deepcopy(self)
