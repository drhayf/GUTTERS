"""
GUTTERS Module System

Auto-discovery and registration of all GUTTERS modules.
"""
from typing import Dict, Type

from .base import BaseModule

# Module registry will be populated at runtime
_registry: Dict[str, Type[BaseModule]] = {}

def register_module(name: str, module_class: Type[BaseModule]) -> None:
    """Register a module in the global registry."""
    _registry[name] = module_class

def get_module(name: str) -> Type[BaseModule] | None:
    """Get a module class by name."""
    return _registry.get(name)

def get_all_modules() -> Dict[str, Type[BaseModule]]:
    """Get all registered modules."""
    return _registry.copy()
