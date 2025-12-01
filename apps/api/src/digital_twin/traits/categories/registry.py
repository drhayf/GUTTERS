"""
Category Registry for Dynamic Discovery

Provides auto-discovery of all trait categories in the categories/ folder.
New categories can be added simply by creating a new folder with definition.py.

@module CategoryRegistry
"""

from typing import Dict, List, Optional
from pathlib import Path
import importlib


class CategoryInfo:
    """Information about a single trait category."""
    
    def __init__(
        self,
        id: str,
        value: str,
        display_name: str,
        description: str,
        icon: str,
        priority: int
    ):
        self.id = id
        self.value = value
        self.display_name = display_name
        self.description = description
        self.icon = icon
        self.priority = priority
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "value": self.value,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "priority": self.priority,
        }


class CategoryRegistry:
    """
    Auto-discovers and registers all trait categories.
    
    Categories are discovered by scanning subdirectories of the categories/
    folder. Each subdirectory should have a definition.py with the category
    constants (VALUE, DISPLAY_NAME, DESCRIPTION, ICON, PRIORITY).
    
    Usage:
        registry = CategoryRegistry()
        # or
        registry = get_category_registry()
        
        # List all categories
        categories = registry.list_all()
        
        # Get specific category info
        info = registry.get("personality")
    """
    
    _instance: Optional["CategoryRegistry"] = None
    _categories: Dict[str, CategoryInfo] = {}
    
    def __new__(cls) -> "CategoryRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._discover_categories()
        return cls._instance
    
    def _discover_categories(self) -> None:
        """Auto-discover all category folders."""
        categories_dir = Path(__file__).parent
        
        for folder in sorted(categories_dir.iterdir()):
            if folder.is_dir() and not folder.name.startswith("_"):
                try:
                    # Import the category module
                    module = importlib.import_module(
                        f".{folder.name}",
                        package="src.digital_twin.traits.categories"
                    )
                    
                    # Get the category value (e.g., PERSONALITY = "personality")
                    upper_name = folder.name.upper()
                    if hasattr(module, upper_name):
                        self._categories[folder.name] = CategoryInfo(
                            id=folder.name,
                            value=getattr(module, upper_name),
                            display_name=getattr(module, "DISPLAY_NAME", folder.name.title()),
                            description=getattr(module, "DESCRIPTION", ""),
                            icon=getattr(module, "ICON", "📝"),
                            priority=getattr(module, "PRIORITY", 50),
                        )
                except ImportError as e:
                    # Skip folders that can't be imported
                    pass
    
    def get(self, category_id: str) -> Optional[CategoryInfo]:
        """Get category info by ID."""
        return self._categories.get(category_id)
    
    def list_all(self) -> List[str]:
        """List all category IDs."""
        return list(self._categories.keys())
    
    def list_sorted_by_priority(self) -> List[str]:
        """List all category IDs sorted by priority (lowest first)."""
        return sorted(
            self._categories.keys(),
            key=lambda x: self._categories[x].priority
        )
    
    def get_enum_value(self, category_id: str) -> Optional[str]:
        """Get the string value for enum compatibility."""
        cat = self._categories.get(category_id)
        return cat.value if cat else None
    
    def get_all_values(self) -> List[str]:
        """Get all category string values."""
        return [c.value for c in self._categories.values()]
    
    def get_all_info(self) -> Dict[str, CategoryInfo]:
        """Get all category information."""
        return dict(self._categories)


# Singleton accessor
_registry_instance: Optional[CategoryRegistry] = None


def get_category_registry() -> CategoryRegistry:
    """Get the singleton category registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = CategoryRegistry()
    return _registry_instance
