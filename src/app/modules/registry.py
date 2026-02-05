"""
GUTTERS Module Registry

Central registry for all GUTTERS modules. Provides discovery and lookup
functionality for the intelligence layer to find and query all modules.

Usage:
    # Auto-registration happens in BaseModule.__init__
    from src.app.modules.calculation.astrology.module import AstrologyModule
    astro = AstrologyModule()  # Automatically registered
    
    # Query registered modules
    from src.app.modules.registry import ModuleRegistry
    all_calc = ModuleRegistry.get_all_calculation_modules()
    
    # Get specific module
    astro = ModuleRegistry.get_module("astrology")
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from .base import BaseModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Central registry for all GUTTERS modules.
    
    Any module can register itself. Intelligence modules
    query the registry to know what's available.
    
    This is a class with all classmethods to avoid singleton pattern issues
    while still maintaining global state.
    """
    
    _modules: dict[str, "BaseModule"] = {}
    
    @classmethod
    def register(cls, module: "BaseModule") -> None:
        """
        Register a module by name.
        
        Called automatically by BaseModule.__init__ when a module is instantiated.
        
        Args:
            module: The module instance to register
        """
        if not module.name:
            logger.warning(f"Module {module.__class__.__name__} has no name, skipping registration")
            return
            
        if module.name in cls._modules:
            logger.debug(f"Module '{module.name}' already registered, updating")
        
        cls._modules[module.name] = module
        logger.info(f"Registered module: {module.name} (layer: {module.layer})")
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a module by name.
        
        Args:
            name: Module name to unregister
        """
        if name in cls._modules:
            del cls._modules[name]
            logger.info(f"Unregistered module: {name}")
    
    @classmethod
    def get_module(cls, name: str) -> "BaseModule | None":
        """
        Get a module by name.
        
        Args:
            name: Module name to retrieve
            
        Returns:
            Module instance or None if not found
        """
        return cls._modules.get(name)
    
    @classmethod
    def get_all_modules(cls) -> list["BaseModule"]:
        """
        Get all registered modules.
        
        Returns:
            List of all module instances
        """
        return list(cls._modules.values())
    
    @classmethod
    def get_all_calculation_modules(cls) -> list["BaseModule"]:
        """
        Get all modules in the calculation layer.
        
        Returns:
            List of calculation module instances
        """
        return [
            m for m in cls._modules.values()
            if m.layer == "calculation"
        ]
    
    @classmethod
    def get_all_intelligence_modules(cls) -> list["BaseModule"]:
        """
        Get all modules in the intelligence layer.
        
        Returns:
            List of intelligence module instances
        """
        return [
            m for m in cls._modules.values()
            if m.layer == "intelligence"
        ]
    
    @classmethod
    def get_module_names(cls) -> list[str]:
        """
        Get list of all registered module names.
        
        Returns:
            List of module names
        """
        return list(cls._modules.keys())
    
    @classmethod
    async def get_calculated_modules_for_user(
        cls, 
        user_id: int, 
        db: AsyncSession
    ) -> list[str]:
        """
        Get list of modules that have calculated profiles for this user.
        
        Checks UserProfile.data for module results.
        
        Args:
            user_id: User ID to check
            db: Database session
            
        Returns:
            List of module names that have data for this user
        """
        from ..models.user_profile import UserProfile
        
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.data:
            return []
        
        # Get calculation module names that exist in profile data
        calculation_module_names = {m.name for m in cls.get_all_calculation_modules()}
        calculated = [
            key for key in profile.data.keys()
            if key in calculation_module_names
        ]
        
        return calculated
    
    @classmethod
    async def get_user_profile_data(
        cls,
        user_id: int,
        db: AsyncSession,
        module_name: str | None = None
    ) -> dict[str, Any]:
        """
        Get profile data for a user, optionally filtered by module.
        
        Args:
            user_id: User ID
            db: Database session
            module_name: Optional module name to filter by
            
        Returns:
            Profile data dict (full or module-specific)
        """
        from ..models.user_profile import UserProfile
        
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.data:
            return {}
        
        if module_name:
            return profile.data.get(module_name, {})
        
        return profile.data
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered modules.
        
        Primarily used for testing.
        """
        cls._modules.clear()
        logger.info("Cleared all registered modules")
