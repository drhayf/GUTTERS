"""
Category Registry for Dynamic Discovery.

This module provides a registry pattern for auto-discovering and registering
all trait categories defined in the subfolders.
"""
from typing import Dict, List, Optional
from pathlib import Path
import importlib


class CategoryRegistry:
    """
    Auto-discovers and registers all trait categories.
    
    This registry scans the categories folder for subdirectories,
    loads their definitions, and provides access to category metadata.
    """
    
    _instance: Optional["CategoryRegistry"] = None
    _categories: Dict[str, dict]
    
    def __new__(cls) -> "CategoryRegistry":
        """Singleton pattern for registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._categories = {}
            cls._instance._discover_categories()
        return cls._instance
    
    def _discover_categories(self) -> None:
        """Auto-discover all category folders."""
        categories_dir = Path(__file__).parent
        for folder in categories_dir.iterdir():
            if folder.is_dir() and not folder.name.startswith("_"):
                try:
                    module = importlib.import_module(
                        f".{folder.name}", 
                        package="digital_twin.traits.categories"
                    )
                    # Get the uppercase constant (e.g., PERSONALITY, ARCHETYPE)
                    category_const = folder.name.upper()
                    if hasattr(module, category_const):
                        self._categories[folder.name] = {
                            "value": getattr(module, category_const),
                            "display_name": getattr(module, "DISPLAY_NAME", folder.name.title()),
                            "description": getattr(module, "DESCRIPTION", ""),
                            "icon": getattr(module, "ICON", ""),
                        }
                except ImportError as e:
                    # Skip folders that don't have proper structure
                    pass
    
    def get(self, category_id: str) -> Optional[dict]:
        """Get category metadata by ID."""
        return self._categories.get(category_id)
    
    def list_all(self) -> List[str]:
        """List all category IDs."""
        return list(self._categories.keys())
    
    def list_with_metadata(self) -> List[dict]:
        """List all categories with full metadata."""
        return [
            {"id": k, **v} for k, v in self._categories.items()
        ]
    
    def get_enum_value(self, category_id: str) -> Optional[str]:
        """Get the string value for enum compatibility."""
        cat = self._categories.get(category_id)
        return cat["value"] if cat else None


def get_category_registry() -> CategoryRegistry:
    """Get the singleton category registry."""
    return CategoryRegistry()
