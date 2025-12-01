"""
Framework Registry for Dynamic Discovery.

This module provides a registry pattern for auto-discovering and registering
all trait frameworks defined in the subfolders.
"""
from typing import Dict, List, Optional
from pathlib import Path
import importlib


class FrameworkRegistry:
    """
    Auto-discovers and registers all trait frameworks.
    
    This registry scans the frameworks folder for subdirectories,
    loads their definitions, and provides access to framework metadata.
    """
    
    _instance: Optional["FrameworkRegistry"] = None
    _frameworks: Dict[str, dict]
    
    def __new__(cls) -> "FrameworkRegistry":
        """Singleton pattern for registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._frameworks = {}
            cls._instance._discover_frameworks()
        return cls._instance
    
    def _discover_frameworks(self) -> None:
        """Auto-discover all framework folders."""
        frameworks_dir = Path(__file__).parent
        for folder in frameworks_dir.iterdir():
            if folder.is_dir() and not folder.name.startswith("_"):
                try:
                    module = importlib.import_module(
                        f".{folder.name}", 
                        package="digital_twin.traits.frameworks"
                    )
                    # Get the uppercase constant (e.g., HUMAN_DESIGN, JUNGIAN)
                    framework_const = folder.name.upper()
                    if hasattr(module, framework_const):
                        self._frameworks[folder.name] = {
                            "value": getattr(module, framework_const),
                            "display_name": getattr(module, "DISPLAY_NAME", folder.name.title()),
                            "description": getattr(module, "DESCRIPTION", ""),
                            "icon": getattr(module, "ICON", "📝"),
                        }
                except ImportError as e:
                    # Skip folders that don't have proper structure
                    pass
    
    def get(self, framework_id: str) -> Optional[dict]:
        """Get framework metadata by ID."""
        return self._frameworks.get(framework_id)
    
    def list_all(self) -> List[str]:
        """List all framework IDs."""
        return list(self._frameworks.keys())
    
    def list_with_metadata(self) -> List[dict]:
        """List all frameworks with full metadata."""
        return [
            {"id": k, **v} for k, v in self._frameworks.items()
        ]
    
    def get_enum_value(self, framework_id: str) -> Optional[str]:
        """Get the string value for enum compatibility."""
        fw = self._frameworks.get(framework_id)
        return fw["value"] if fw else None


def get_framework_registry() -> FrameworkRegistry:
    """Get the singleton framework registry."""
    return FrameworkRegistry()
