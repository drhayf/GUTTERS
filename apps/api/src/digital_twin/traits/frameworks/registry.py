"""
Framework Registry for Dynamic Discovery

Provides auto-discovery of all trait frameworks in the frameworks/ folder.
New frameworks can be added simply by creating a new folder with definition.py.

@module FrameworkRegistry
"""

from typing import Dict, List, Optional
from pathlib import Path
import importlib


class FrameworkInfo:
    """Information about a single trait framework."""
    
    def __init__(
        self,
        id: str,
        value: str,
        display_name: str,
        description: str,
        icon: str
    ):
        self.id = id
        self.value = value
        self.display_name = display_name
        self.description = description
        self.icon = icon
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "value": self.value,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
        }


class FrameworkRegistry:
    """
    Auto-discovers and registers all trait frameworks.
    
    Frameworks are discovered by scanning subdirectories of the frameworks/
    folder. Each subdirectory should have a definition.py with the framework
    constants (VALUE, DISPLAY_NAME, DESCRIPTION, ICON).
    
    Usage:
        registry = FrameworkRegistry()
        # or
        registry = get_framework_registry()
        
        # List all frameworks
        frameworks = registry.list_all()
        
        # Get specific framework info
        info = registry.get("human_design")
    """
    
    _instance: Optional["FrameworkRegistry"] = None
    _frameworks: Dict[str, FrameworkInfo] = {}
    
    def __new__(cls) -> "FrameworkRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._discover_frameworks()
        return cls._instance
    
    def _discover_frameworks(self) -> None:
        """Auto-discover all framework folders."""
        frameworks_dir = Path(__file__).parent
        
        for folder in sorted(frameworks_dir.iterdir()):
            if folder.is_dir() and not folder.name.startswith("_"):
                try:
                    # Import the framework module
                    module = importlib.import_module(
                        f".{folder.name}",
                        package="src.digital_twin.traits.frameworks"
                    )
                    
                    # Get the framework value (e.g., HUMAN_DESIGN = "human_design")
                    upper_name = folder.name.upper()
                    if hasattr(module, upper_name):
                        self._frameworks[folder.name] = FrameworkInfo(
                            id=folder.name,
                            value=getattr(module, upper_name),
                            display_name=getattr(module, "DISPLAY_NAME", folder.name.replace("_", " ").title()),
                            description=getattr(module, "DESCRIPTION", ""),
                            icon=getattr(module, "ICON", "📝"),
                        )
                except ImportError as e:
                    # Skip folders that can't be imported
                    pass
    
    def get(self, framework_id: str) -> Optional[FrameworkInfo]:
        """Get framework info by ID."""
        return self._frameworks.get(framework_id)
    
    def list_all(self) -> List[str]:
        """List all framework IDs."""
        return list(self._frameworks.keys())
    
    def get_enum_value(self, framework_id: str) -> Optional[str]:
        """Get the string value for enum compatibility."""
        fw = self._frameworks.get(framework_id)
        return fw.value if fw else None
    
    def get_all_values(self) -> List[str]:
        """Get all framework string values."""
        return [f.value for f in self._frameworks.values()]
    
    def get_all_info(self) -> Dict[str, FrameworkInfo]:
        """Get all framework information."""
        return dict(self._frameworks)


# Singleton accessor
_registry_instance: Optional[FrameworkRegistry] = None


def get_framework_registry() -> FrameworkRegistry:
    """Get the singleton framework registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = FrameworkRegistry()
    return _registry_instance
