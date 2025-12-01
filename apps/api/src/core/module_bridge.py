"""
Module-Domain Bridge - Connecting Frontend Modules to Backend Domains

This is THE BRIDGE that connects:
- Frontend Module System (module-preferences-atoms.ts)
- Backend Domain System (digital_twin/domains/)

Key Responsibilities:
1. Receive module preferences from frontend
2. Map modules to domains (1:1 and 1:many)
3. Enable/disable domain processing based on module state
4. Propagate capability awareness to all agents
5. Store preferences in Digital Twin for persistence

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌────────────────────────────────────────────────────────────────────┐
    │                        FRONTEND (React Native)                      │
    │                                                                     │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │           module-preferences-atoms.ts                        │  │
    │  │  • ModuleDefinition registry                                 │  │
    │  │  • Toggle atoms with AsyncStorage persistence                │  │
    │  │  • Categories: wisdom, health, life, system                  │  │
    │  └────────────────────────────┬────────────────────────────────┘  │
    └───────────────────────────────┼────────────────────────────────────┘
                                    │ API: POST /modules/sync
                                    ▼
    ┌────────────────────────────────────────────────────────────────────┐
    │                           MODULE BRIDGE                             │
    │                                                                     │
    │  ┌─────────────────────────────────────────────────────────────┐  │
    │  │           ModuleBridge (this file)                           │  │
    │  │  • Receives preferences from frontend                        │  │
    │  │  • Maps modules → domains                                    │  │
    │  │  • Updates capability registry                               │  │
    │  │  • Stores in Digital Twin                                    │  │
    │  └────────────────────────────┬────────────────────────────────┘  │
    └───────────────────────────────┼────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │     Domain Registry      │   │     Capability Registry   │
    │  • GenesisDomain         │   │  • Active capabilities    │
    │  • HealthDomain          │   │  • Routing decisions      │
    │  • FinanceDomain         │   │  • Agent filtering        │
    └──────────────────────────┘   └──────────────────────────┘

@module ModuleBridge
"""

from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# MODULE CAPABILITY ENUM (mirrors frontend AgentCapability)
# =============================================================================

class ModuleCapability(str, Enum):
    """
    All available module capabilities.
    MUST match AgentCapability in lib/agents/sovereign-protocol.ts
    """
    # System (always enabled)
    PROFILING = "profiling"
    VISION = "vision"
    SYNTHESIS = "synthesis"
    
    # Wisdom frameworks
    ARCHETYPES = "archetypes"
    HUMAN_DESIGN = "human_design"
    GENE_KEYS = "gene_keys"
    ASTROLOGY = "astrology"
    NUMEROLOGY = "numerology"
    
    # Health
    FOOD_ANALYSIS = "food_analysis"
    HEALTH_METRICS = "health_metrics"
    
    # Life management
    FINANCE = "finance"
    JOURNALING = "journaling"
    
    # Optional system
    HRM_REASONING = "hrm_reasoning"


class ModuleCategory(str, Enum):
    """Module categories matching frontend."""
    WISDOM = "wisdom"
    HEALTH = "health"
    LIFE = "life"
    SYSTEM = "system"


# =============================================================================
# MODULE-DOMAIN MAPPING
# =============================================================================

@dataclass
class ModuleDomainMapping:
    """Mapping between a frontend module and backend domain(s)."""
    module_id: ModuleCapability
    domain_name: str
    category: ModuleCategory
    is_core: bool  # Core modules cannot be disabled
    dependencies: List[ModuleCapability] = field(default_factory=list)
    
    # Domain-specific configuration
    domain_config: Dict[str, Any] = field(default_factory=dict)


# The master mapping table
MODULE_DOMAIN_MAP: Dict[ModuleCapability, ModuleDomainMapping] = {
    # Core system modules → Genesis domain
    ModuleCapability.PROFILING: ModuleDomainMapping(
        module_id=ModuleCapability.PROFILING,
        domain_name="genesis",
        category=ModuleCategory.SYSTEM,
        is_core=True,
        dependencies=[],
    ),
    ModuleCapability.SYNTHESIS: ModuleDomainMapping(
        module_id=ModuleCapability.SYNTHESIS,
        domain_name="genesis",  # Synthesis is part of Genesis core
        category=ModuleCategory.SYSTEM,
        is_core=True,
        dependencies=[ModuleCapability.PROFILING],
    ),
    ModuleCapability.VISION: ModuleDomainMapping(
        module_id=ModuleCapability.VISION,
        domain_name="vision",
        category=ModuleCategory.SYSTEM,
        is_core=True,
        dependencies=[],
    ),
    
    # Wisdom framework modules → Genesis domain (different trait schemas)
    ModuleCapability.ARCHETYPES: ModuleDomainMapping(
        module_id=ModuleCapability.ARCHETYPES,
        domain_name="genesis",
        category=ModuleCategory.WISDOM,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
        domain_config={"trait_prefix": "jung_", "framework": "jungian_cognitive"},
    ),
    ModuleCapability.HUMAN_DESIGN: ModuleDomainMapping(
        module_id=ModuleCapability.HUMAN_DESIGN,
        domain_name="genesis",
        category=ModuleCategory.WISDOM,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
        domain_config={"trait_prefix": "hd_", "framework": "human_design"},
    ),
    ModuleCapability.GENE_KEYS: ModuleDomainMapping(
        module_id=ModuleCapability.GENE_KEYS,
        domain_name="genesis",
        category=ModuleCategory.WISDOM,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING, ModuleCapability.HUMAN_DESIGN],
        domain_config={"trait_prefix": "gk_", "framework": "gene_keys"},
    ),
    ModuleCapability.ASTROLOGY: ModuleDomainMapping(
        module_id=ModuleCapability.ASTROLOGY,
        domain_name="genesis",
        category=ModuleCategory.WISDOM,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
        domain_config={"trait_prefix": "astro_", "framework": "astrology"},
    ),
    ModuleCapability.NUMEROLOGY: ModuleDomainMapping(
        module_id=ModuleCapability.NUMEROLOGY,
        domain_name="genesis",
        category=ModuleCategory.WISDOM,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
        domain_config={"trait_prefix": "num_", "framework": "numerology"},
    ),
    
    # Health modules → Health domain
    ModuleCapability.FOOD_ANALYSIS: ModuleDomainMapping(
        module_id=ModuleCapability.FOOD_ANALYSIS,
        domain_name="health",
        category=ModuleCategory.HEALTH,
        is_core=False,
        dependencies=[ModuleCapability.VISION],
        domain_config={"sub_domain": "nutrition"},
    ),
    ModuleCapability.HEALTH_METRICS: ModuleDomainMapping(
        module_id=ModuleCapability.HEALTH_METRICS,
        domain_name="health",
        category=ModuleCategory.HEALTH,
        is_core=False,
        dependencies=[],
        domain_config={"sub_domain": "biometrics"},
    ),
    
    # Life management modules → Respective domains
    ModuleCapability.FINANCE: ModuleDomainMapping(
        module_id=ModuleCapability.FINANCE,
        domain_name="finance",
        category=ModuleCategory.LIFE,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
    ),
    ModuleCapability.JOURNALING: ModuleDomainMapping(
        module_id=ModuleCapability.JOURNALING,
        domain_name="journaling",
        category=ModuleCategory.LIFE,
        is_core=False,
        dependencies=[ModuleCapability.PROFILING],
    ),
    
    # Optional system modules
    ModuleCapability.HRM_REASONING: ModuleDomainMapping(
        module_id=ModuleCapability.HRM_REASONING,
        domain_name="system",  # System-wide capability
        category=ModuleCategory.SYSTEM,
        is_core=False,
        dependencies=[],
    ),
}


# =============================================================================
# MODULE PREFERENCES STATE
# =============================================================================

@dataclass
class ModulePreference:
    """State of a single module preference."""
    enabled: bool
    enabled_at: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModulePreferencesState:
    """Complete module preferences state from frontend."""
    preferences: Dict[str, ModulePreference] = field(default_factory=dict)
    last_synced: Optional[str] = None
    identity_id: Optional[str] = None
    
    def is_enabled(self, module_id: str) -> bool:
        """Check if a module is enabled."""
        if module_id in self.preferences:
            return self.preferences[module_id].enabled
        # Check if it's a core module (always enabled)
        try:
            cap = ModuleCapability(module_id)
            mapping = MODULE_DOMAIN_MAP.get(cap)
            if mapping and mapping.is_core:
                return True
        except ValueError:
            pass
        return False
    
    def get_enabled_modules(self) -> Set[str]:
        """Get all enabled module IDs."""
        enabled = set()
        for mod_id, pref in self.preferences.items():
            if pref.enabled:
                enabled.add(mod_id)
        # Add core modules
        for cap, mapping in MODULE_DOMAIN_MAP.items():
            if mapping.is_core:
                enabled.add(cap.value)
        return enabled
    
    def get_enabled_by_category(self, category: ModuleCategory) -> Set[str]:
        """Get enabled modules in a category."""
        enabled = self.get_enabled_modules()
        return {
            mod_id for mod_id in enabled
            if MODULE_DOMAIN_MAP.get(ModuleCapability(mod_id), ModuleDomainMapping(
                module_id=ModuleCapability.PROFILING,
                domain_name="",
                category=ModuleCategory.SYSTEM,
                is_core=False
            )).category == category
        }


# =============================================================================
# CAPABILITY REGISTRY
# =============================================================================

class CapabilityRegistry:
    """
    Registry of currently active capabilities.
    
    Used by:
    - Orchestrator for routing decisions
    - SwarmBus for agent filtering
    - Sovereign Agent for tool availability
    - Domain system for trait filtering
    """
    
    _instance: Optional["CapabilityRegistry"] = None
    
    def __init__(self):
        self._active: Set[ModuleCapability] = set()
        self._listeners: List[Callable[[Set[ModuleCapability]], Any]] = []
        self._state: Optional[ModulePreferencesState] = None
        
        # Initialize with core modules
        for cap, mapping in MODULE_DOMAIN_MAP.items():
            if mapping.is_core:
                self._active.add(cap)
    
    @classmethod
    def get_instance(cls) -> "CapabilityRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def is_active(self, capability: ModuleCapability) -> bool:
        """Check if a capability is currently active."""
        return capability in self._active
    
    def is_active_str(self, capability_str: str) -> bool:
        """Check if a capability is active by string ID."""
        try:
            cap = ModuleCapability(capability_str)
            return self.is_active(cap)
        except ValueError:
            return False
    
    def get_active(self) -> Set[ModuleCapability]:
        """Get all active capabilities."""
        return self._active.copy()
    
    def get_active_strings(self) -> Set[str]:
        """Get active capability IDs as strings."""
        return {cap.value for cap in self._active}
    
    def get_active_for_domain(self, domain_name: str) -> Set[ModuleCapability]:
        """Get active capabilities that map to a specific domain."""
        return {
            cap for cap in self._active
            if MODULE_DOMAIN_MAP[cap].domain_name == domain_name
        }
    
    def update_from_preferences(self, state: ModulePreferencesState) -> None:
        """Update active capabilities from preferences state."""
        self._state = state
        new_active = set()
        
        for cap, mapping in MODULE_DOMAIN_MAP.items():
            if mapping.is_core:
                # Core modules always active
                new_active.add(cap)
            elif state.is_enabled(cap.value):
                # User-enabled module
                new_active.add(cap)
        
        old_active = self._active
        self._active = new_active
        
        # Log changes
        added = new_active - old_active
        removed = old_active - new_active
        if added:
            logger.info(f"[CapabilityRegistry] Enabled: {[c.value for c in added]}")
        if removed:
            logger.info(f"[CapabilityRegistry] Disabled: {[c.value for c in removed]}")
        
        # Notify listeners
        self._notify_listeners()
    
    def add_listener(self, listener: Callable[[Set[ModuleCapability]], Any]) -> None:
        """Add a listener for capability changes."""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[Set[ModuleCapability]], Any]) -> None:
        """Remove a listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_listeners(self) -> None:
        """Notify all listeners of capability changes."""
        for listener in self._listeners:
            try:
                result = listener(self._active)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.error(f"[CapabilityRegistry] Listener error: {e}")


# =============================================================================
# MODULE BRIDGE
# =============================================================================

class ModuleBridge:
    """
    The main bridge between frontend modules and backend domains.
    
    Usage:
        bridge = await ModuleBridge.get_instance()
        
        # Sync preferences from frontend
        await bridge.sync_preferences(preferences_from_api)
        
        # Check if a capability is active
        if bridge.is_capability_active("human_design"):
            # Include HD traits in response
            
        # Get domain for a module
        domain = bridge.get_domain_for_module("archetypes")
    """
    
    _instance: Optional["ModuleBridge"] = None
    
    def __init__(self):
        self._registry = CapabilityRegistry.get_instance()
        self._state: Optional[ModulePreferencesState] = None
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> "ModuleBridge":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize the bridge."""
        if self._initialized:
            return
        
        # Try to load preferences from Digital Twin
        try:
            from ..digital_twin import get_digital_twin_core
            core = await get_digital_twin_core()
            
            # Get module preferences from identity
            prefs_data = await core.get("system.module_preferences")
            if prefs_data:
                self._state = self._parse_preferences(prefs_data)
                self._registry.update_from_preferences(self._state)
                logger.info("[ModuleBridge] Loaded preferences from Digital Twin")
        except Exception as e:
            logger.warning(f"[ModuleBridge] Could not load from Digital Twin: {e}")
            # Use defaults
            self._state = ModulePreferencesState()
        
        self._initialized = True
        logger.info("[ModuleBridge] Initialized")
    
    def _parse_preferences(self, data: Any) -> ModulePreferencesState:
        """Parse preferences data into state object."""
        if isinstance(data, dict):
            prefs = {}
            for mod_id, pref_data in data.get("preferences", data).items():
                if isinstance(pref_data, dict):
                    prefs[mod_id] = ModulePreference(
                        enabled=pref_data.get("enabled", False),
                        enabled_at=pref_data.get("enabledAt") or pref_data.get("enabled_at"),
                        settings=pref_data.get("settings", {}),
                    )
                elif isinstance(pref_data, bool):
                    prefs[mod_id] = ModulePreference(enabled=pref_data)
            
            return ModulePreferencesState(
                preferences=prefs,
                last_synced=data.get("last_synced") or datetime.now().isoformat(),
            )
        return ModulePreferencesState()
    
    async def sync_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync module preferences from frontend.
        
        Called by API endpoint when frontend sends preferences.
        
        Args:
            preferences: Raw preferences dict from frontend
            
        Returns:
            Sync result with status and active capabilities
        """
        logger.info("[ModuleBridge] Syncing preferences from frontend")
        
        # Parse and store
        self._state = self._parse_preferences(preferences)
        self._state.last_synced = datetime.now().isoformat()
        
        # Update capability registry
        self._registry.update_from_preferences(self._state)
        
        # Persist to Digital Twin
        try:
            from ..digital_twin import get_digital_twin_core
            core = await get_digital_twin_core()
            
            await core.set(
                path="system.module_preferences",
                value={
                    "preferences": {
                        mod_id: {
                            "enabled": pref.enabled,
                            "enabled_at": pref.enabled_at,
                            "settings": pref.settings,
                        }
                        for mod_id, pref in self._state.preferences.items()
                    },
                    "last_synced": self._state.last_synced,
                },
                source="module_bridge"
            )
            logger.info("[ModuleBridge] Saved preferences to Digital Twin")
        except Exception as e:
            logger.error(f"[ModuleBridge] Could not save to Digital Twin: {e}")
        
        return {
            "success": True,
            "synced_at": self._state.last_synced,
            "active_capabilities": list(self._registry.get_active_strings()),
            "enabled_count": len(self._state.get_enabled_modules()),
        }
    
    def is_capability_active(self, capability: str) -> bool:
        """Check if a capability/module is currently active."""
        return self._registry.is_active_str(capability)
    
    def get_active_capabilities(self) -> Set[str]:
        """Get all active capability IDs."""
        return self._registry.get_active_strings()
    
    def get_domain_for_module(self, module_id: str) -> Optional[str]:
        """Get the domain name for a module."""
        try:
            cap = ModuleCapability(module_id)
            mapping = MODULE_DOMAIN_MAP.get(cap)
            if mapping:
                return mapping.domain_name
        except ValueError:
            pass
        return None
    
    def get_module_config(self, module_id: str) -> Dict[str, Any]:
        """Get domain-specific config for a module."""
        try:
            cap = ModuleCapability(module_id)
            mapping = MODULE_DOMAIN_MAP.get(cap)
            if mapping:
                return mapping.domain_config
        except ValueError:
            pass
        return {}
    
    def should_include_traits(self, trait_framework: str) -> bool:
        """
        Check if traits from a framework should be included.
        
        This is used by the Digital Twin to filter trait output based
        on which modules are enabled.
        """
        # Map framework to capability
        framework_to_cap = {
            "human_design": ModuleCapability.HUMAN_DESIGN,
            "jungian_cognitive": ModuleCapability.ARCHETYPES,
            "jungian_shadow": ModuleCapability.ARCHETYPES,
            "mbti": ModuleCapability.ARCHETYPES,
            "gene_keys": ModuleCapability.GENE_KEYS,
            "astrology": ModuleCapability.ASTROLOGY,
            "numerology": ModuleCapability.NUMEROLOGY,
            "somatic": ModuleCapability.PROFILING,  # Core
            "behavioral": ModuleCapability.PROFILING,  # Core
            "core_patterns": ModuleCapability.PROFILING,  # Core
        }
        
        cap = framework_to_cap.get(trait_framework)
        if cap is None:
            # Unknown framework, include by default
            return True
        
        return self._registry.is_active(cap)
    
    def get_preferences_summary(self) -> Dict[str, Any]:
        """Get a summary of current preferences."""
        if not self._state:
            return {"initialized": False}
        
        by_category = {}
        for cat in ModuleCategory:
            enabled = self._state.get_enabled_by_category(cat)
            by_category[cat.value] = {
                "enabled_count": len(enabled),
                "enabled_modules": list(enabled),
            }
        
        return {
            "initialized": True,
            "last_synced": self._state.last_synced,
            "total_enabled": len(self._state.get_enabled_modules()),
            "by_category": by_category,
            "active_capabilities": list(self._registry.get_active_strings()),
        }
    
    async def sync_from_frontend(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync preferences from frontend API call.
        
        This is the method called by the /modules/sync endpoint.
        
        Args:
            preferences: Dict with 'enabled' and 'disabled' module lists
            
        Returns:
            Sync result
        """
        # Convert from API format to internal format
        prefs_dict = {}
        for mod_id in preferences.get("enabled", []):
            prefs_dict[mod_id] = {"enabled": True, "enabled_at": datetime.now().isoformat()}
        for mod_id in preferences.get("disabled", []):
            prefs_dict[mod_id] = {"enabled": False}
        
        return await self.sync_preferences(prefs_dict)
    
    async def get_module_state(self, module_id: str) -> Optional[ModulePreference]:
        """
        Get the state of a specific module.
        
        Args:
            module_id: The module ID to check
            
        Returns:
            ModulePreference if found, None otherwise
        """
        if not self._state:
            return None
        return self._state.preferences.get(module_id)
    
    async def toggle_module(self, module_id: str, enabled: bool) -> ModulePreference:
        """
        Toggle a specific module on or off.
        
        Args:
            module_id: The module to toggle
            enabled: New enabled state
            
        Returns:
            Updated ModulePreference
        """
        if not self._state:
            self._state = ModulePreferencesState()
        
        pref = ModulePreference(
            enabled=enabled,
            enabled_at=datetime.now().isoformat() if enabled else None,
        )
        self._state.preferences[module_id] = pref
        self._state.last_synced = datetime.now().isoformat()
        
        # Update registry
        self._registry.update_from_preferences(self._state)
        
        # Persist to Digital Twin
        try:
            from ..digital_twin import get_digital_twin_core
            core = await get_digital_twin_core()
            await core.set(
                path="system.module_preferences",
                value={
                    "preferences": {
                        mod_id: {
                            "enabled": p.enabled,
                            "enabled_at": p.enabled_at,
                            "settings": p.settings,
                        }
                        for mod_id, p in self._state.preferences.items()
                    },
                    "last_synced": self._state.last_synced,
                },
                source="module_bridge.toggle"
            )
        except Exception as e:
            logger.warning(f"[ModuleBridge] Could not persist toggle: {e}")
        
        return pref
    
    async def get_enabled_modules(self) -> List[str]:
        """
        Get list of all enabled module IDs.
        
        Returns:
            List of enabled module ID strings
        """
        if not self._state:
            # Return core modules as default
            return [
                cap.value for cap, mapping in MODULE_DOMAIN_MAP.items()
                if mapping.is_core
            ]
        return list(self._state.get_enabled_modules())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_bridge: Optional[ModuleBridge] = None


async def get_module_bridge() -> ModuleBridge:
    """Get the singleton ModuleBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = await ModuleBridge.get_instance()
    return _bridge


async def get_bridge() -> ModuleBridge:
    """Alias for get_module_bridge - used by API routers."""
    return await get_module_bridge()


def get_capability_registry() -> CapabilityRegistry:
    """Get the CapabilityRegistry instance."""
    return CapabilityRegistry.get_instance()


def is_capability_active(capability: str) -> bool:
    """Quick check if a capability is active."""
    return get_capability_registry().is_active_str(capability)
