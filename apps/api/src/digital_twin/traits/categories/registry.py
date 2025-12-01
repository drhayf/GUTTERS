"""
Category Registry - Auto-Discovery System for Trait Categories

This module provides dynamic discovery and registration of all trait categories.
New categories can be added by simply dropping a new folder with definition.py.

Part of the True Fractal Pattern - infinite extensibility via auto-discovery.

@module TraitCategories.Registry
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import importlib
import logging

logger = logging.getLogger(__name__)


class CategoryInfo:
    """
    Information about a trait category.
    
    This is a lightweight container that holds the metadata
    extracted from each category's definition.py.
    """
    
    def __init__(
        self,
        category_id: str,
        display_name: str,
        description: str,
        icon: str = "",
        priority: int = 50,
    ):
        self.id = category_id
        self.value = category_id  # For enum compatibility
        self.display_name = display_name
        self.description = description
        self.icon = icon
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "value": self.value,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "priority": self.priority,
        }
    
    def __repr__(self) -> str:
        return f"CategoryInfo(id={self.id!r}, display_name={self.display_name!r})"


class CategoryRegistry:
    """
    Auto-discovers and registers all trait categories.
    
    This registry scans the categories/ directory for subfolders,
    imports their definitions, and makes them available via a clean API.
    
    Usage:
        registry = get_category_registry()
        all_categories = registry.list_all()
        personality = registry.get("personality")
    """
    
    _instance: Optional["CategoryRegistry"] = None
    _categories: Dict[str, CategoryInfo] = {}
    _initialized: bool = False
    
    def __new__(cls) -> "CategoryRegistry":
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _discover_categories(self) -> None:
        """
        Auto-discover all category folders and import their definitions.
        
        For each subfolder in categories/:
        1. Try to import the folder as a module
        2. Look for the category constant (e.g., PERSONALITY)
        3. Extract metadata (DISPLAY_NAME, DESCRIPTION, ICON, PRIORITY)
        4. Register in the _categories dictionary
        """
        if self._initialized:
            return
        
        categories_dir = Path(__file__).parent
        
        for folder in categories_dir.iterdir():
            # Skip non-directories, private folders, and extensions
            if not folder.is_dir():
                continue
            if folder.name.startswith("_"):
                continue
            if folder.name == "extensions":
                continue  # Handle extensions separately
            
            try:
                # Import the category module
                module = importlib.import_module(
                    f".{folder.name}",
                    package="src.digital_twin.traits.categories"
                )
                
                # Look for the category constant (uppercase folder name)
                constant_name = folder.name.upper()
                if hasattr(module, constant_name):
                    category_value = getattr(module, constant_name)
                    
                    # Extract metadata with fallbacks
                    display_name = getattr(module, "DISPLAY_NAME", folder.name.title())
                    description = getattr(module, "DESCRIPTION", "")
                    icon = getattr(module, "ICON", "")
                    priority = getattr(module, "PRIORITY", 50)
                    
                    # Register the category
                    self._categories[folder.name] = CategoryInfo(
                        category_id=category_value,
                        display_name=display_name,
                        description=description,
                        icon=icon,
                        priority=priority,
                    )
                    
                    logger.debug(f"Discovered category: {folder.name}")
                    
            except ImportError as e:
                logger.warning(f"Failed to import category {folder.name}: {e}")
            except Exception as e:
                logger.error(f"Error processing category {folder.name}: {e}")
        
        self._initialized = True
        logger.info(f"CategoryRegistry initialized with {len(self._categories)} categories")
    
    def get(self, category_id: str) -> Optional[CategoryInfo]:
        """
        Get category info by ID.
        
        Args:
            category_id: The category identifier (e.g., "personality")
            
        Returns:
            CategoryInfo if found, None otherwise
        """
        self._discover_categories()
        return self._categories.get(category_id)
    
    def list_all(self) -> List[str]:
        """
        List all registered category IDs.
        
        Returns:
            List of category identifiers
        """
        self._discover_categories()
        return list(self._categories.keys())
    
    def list_all_info(self) -> List[CategoryInfo]:
        """
        Get all category info objects.
        
        Returns:
            List of CategoryInfo objects
        """
        self._discover_categories()
        return list(self._categories.values())
    
    def list_by_priority(self) -> List[CategoryInfo]:
        """
        Get categories sorted by priority (lower = higher priority).
        
        Returns:
            List of CategoryInfo objects sorted by priority
        """
        self._discover_categories()
        return sorted(self._categories.values(), key=lambda c: c.priority)
    
    def get_enum_value(self, category_id: str) -> Optional[str]:
        """
        Get the string value for enum compatibility.
        
        Args:
            category_id: The category identifier
            
        Returns:
            The category's string value if found, None otherwise
        """
        info = self.get(category_id)
        return info.value if info else None
    
    def contains(self, category_id: str) -> bool:
        """
        Check if a category exists.
        
        Args:
            category_id: The category identifier
            
        Returns:
            True if the category exists
        """
        self._discover_categories()
        return category_id in self._categories
    
    def __len__(self) -> int:
        """Return the number of registered categories."""
        self._discover_categories()
        return len(self._categories)
    
    def __iter__(self):
        """Iterate over category IDs."""
        self._discover_categories()
        return iter(self._categories.keys())


# Singleton accessor function
def get_category_registry() -> CategoryRegistry:
    """
    Get the singleton CategoryRegistry instance.
    
    Returns:
        The CategoryRegistry singleton
        
    Example:
        >>> registry = get_category_registry()
        >>> print(registry.list_all())
        ['personality', 'archetype', 'cognition', ...]
    """
    return CategoryRegistry()
