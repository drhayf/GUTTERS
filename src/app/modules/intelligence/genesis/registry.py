"""
Genesis Uncertainty Registry

Central registry for uncertainty extractors.
Modules register their extractors at startup, and Genesis
calls extract_all() to get uncertainties from all modules.
"""

from typing import Any, TypeVar

from .uncertainty import UncertaintyDeclaration
from .declarations.base import UncertaintyExtractor


T = TypeVar("T")


class UncertaintyRegistry:
    """
    Central registry of all uncertainty extractors.
    
    Modules register their extractors during initialization.
    Genesis calls extract_all() after profile calculations to
    get a unified view of all uncertainties.
    
    Usage:
        # During module init
        UncertaintyRegistry.register(AstrologyUncertaintyExtractor())
        
        # After calculations
        declarations = await UncertaintyRegistry.extract_all(
            results={"astrology": {...}, "human_design": {...}},
            user_id=42,
            session_id="conv-abc"
        )
    """
    
    _extractors: dict[str, UncertaintyExtractor] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, extractor: UncertaintyExtractor) -> None:
        """
        Register a module's uncertainty extractor.
        
        Args:
            extractor: Extractor instance with module_name set
            
        Raises:
            ValueError: If extractor doesn't have module_name
        """
        if not hasattr(extractor, "module_name") or not extractor.module_name:
            raise ValueError("Extractor must have a module_name")
        
        cls._extractors[extractor.module_name] = extractor
    
    @classmethod
    def unregister(cls, module_name: str) -> bool:
        """
        Remove an extractor from the registry.
        
        Returns True if extractor was found and removed.
        """
        if module_name in cls._extractors:
            del cls._extractors[module_name]
            return True
        return False
    
    @classmethod
    def get_extractor(cls, module_name: str) -> UncertaintyExtractor | None:
        """Get a specific extractor by module name."""
        return cls._extractors.get(module_name)
    
    @classmethod
    def list_registered(cls) -> list[str]:
        """List all registered module names."""
        return list(cls._extractors.keys())
    
    @classmethod
    async def extract_all(
        cls,
        results: dict[str, Any],
        user_id: int,
        session_id: str
    ) -> list[UncertaintyDeclaration]:
        """
        Extract uncertainties from all module results.
        
        Iterates through registered extractors, checks if each
        can extract from its corresponding result, and collects
        all declarations.
        
        Args:
            results: Dict mapping module names to calculation results
                     e.g., {"astrology": {...}, "human_design": {...}}
            user_id: User these results belong to
            session_id: Current conversation/session ID
            
        Returns:
            List of UncertaintyDeclaration from all modules
        """
        declarations: list[UncertaintyDeclaration] = []
        
        for module_name, result in results.items():
            extractor = cls._extractors.get(module_name)
            if not extractor:
                continue
            
            try:
                if extractor.can_extract(result):
                    decl = extractor.extract(result, user_id, session_id)
                    if decl and decl.has_uncertainties:
                        declarations.append(decl)
            except Exception as e:
                # Log but don't fail - uncertainties are non-critical
                import logging
                logging.warning(
                    f"Failed to extract uncertainties from {module_name}: {e}"
                )
        
        # Update StateTracker if available
        await cls._update_state_tracker(user_id, declarations)
        
        return declarations
    
    @classmethod
    async def _update_state_tracker(
        cls,
        user_id: int,
        declarations: list[UncertaintyDeclaration]
    ) -> None:
        """
        Update StateTracker with uncertainty information.
        
        This affects profile completion percentages - modules with
        uncertainties are considered less than 100% complete.
        """
        try:
            # Import here to avoid circular imports
            from ...core.state.tracker import get_state_tracker
            
            tracker = await get_state_tracker()
            if tracker:
                await tracker.update_uncertainties(user_id, declarations)
        except ImportError:
            # StateTracker not available - skip
            pass
        except Exception as e:
            import logging
            logging.warning(f"Failed to update StateTracker: {e}")
    
    @classmethod
    def initialize_default_extractors(cls) -> None:
        """
        Register default extractors for all calculation modules.
        
        Call this during application startup.
        """
        if cls._initialized:
            return
        
        from .declarations import (
            AstrologyUncertaintyExtractor,
            HumanDesignUncertaintyExtractor,
            SynthesisUncertaintyExtractor,
        )
        
        cls.register(AstrologyUncertaintyExtractor())
        cls.register(HumanDesignUncertaintyExtractor())
        cls.register(SynthesisUncertaintyExtractor())
        # Numerology has no uncertainties (doesn't use birth time)
        
        cls._initialized = True
    
    @classmethod
    def reset(cls) -> None:
        """Clear all registered extractors (for testing)."""
        cls._extractors = {}
        cls._initialized = False
