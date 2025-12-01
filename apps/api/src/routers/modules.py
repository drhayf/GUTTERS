"""
Module Sync API - Frontend/Backend Module State Synchronization

This router provides endpoints for synchronizing module preferences
between the frontend (Jotai atoms) and the backend (Domain system).

Endpoints:
- GET  /modules/           - List all modules with current state
- GET  /modules/{id}       - Get specific module state
- POST /modules/sync       - Sync frontend preferences to backend
- POST /modules/{id}/toggle - Toggle a specific module
- GET  /modules/domains    - List domain mappings

The Module-Domain Bridge connects frontend UI toggles to backend
capability enablement, ensuring the system is "aware" of which
modules the user has enabled.

@module ModulesRouter
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ModuleState(BaseModel):
    """State of a single module."""
    id: str
    name: str
    enabled: bool
    domain: Optional[str] = None
    category: str = "wisdom"
    config: Dict[str, Any] = {}
    last_synced: Optional[str] = None


class ModulePreferences(BaseModel):
    """Full module preferences from frontend."""
    enabled_modules: List[str]
    disabled_modules: List[str]
    preset: Optional[str] = None
    sync_timestamp: str


class SyncRequest(BaseModel):
    """Request to sync frontend preferences to backend."""
    preferences: ModulePreferences
    identity_id: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from sync operation."""
    success: bool
    modules_synced: int
    domains_updated: List[str]
    message: str


class DomainMapping(BaseModel):
    """Mapping between module and domain."""
    module_id: str
    module_name: str
    domain_name: str
    enabled: bool


# =============================================================================
# MODULE DEFINITIONS (mirror of frontend)
# =============================================================================

MODULE_DEFINITIONS = {
    # Wisdom Modules
    "HUMAN_DESIGN": {
        "name": "Human Design",
        "category": "wisdom",
        "domain": "genesis",
        "description": "HD Type, Authority, Profile",
    },
    "JUNGIAN": {
        "name": "Jungian Psychology",
        "category": "wisdom",
        "domain": "genesis",
        "description": "Cognitive functions, archetypes",
    },
    "ASTROLOGY": {
        "name": "Astrology",
        "category": "wisdom",
        "domain": "astrology",
        "description": "Birth chart interpretation",
    },
    "ENNEAGRAM": {
        "name": "Enneagram",
        "category": "wisdom",
        "domain": "genesis",
        "description": "Type with wings and instincts",
    },
    "GENE_KEYS": {
        "name": "Gene Keys",
        "category": "wisdom",
        "domain": "genesis",
        "description": "Shadow, Gift, Siddhi journey",
    },
    "NUMEROLOGY": {
        "name": "Numerology",
        "category": "wisdom",
        "domain": "numerology",
        "description": "Life path and expression numbers",
    },
    # Health Modules
    "HEALTH_TRACKING": {
        "name": "Health Tracking",
        "category": "health",
        "domain": "health",
        "description": "Metrics integration",
    },
    "SOMATIC": {
        "name": "Somatic Intelligence",
        "category": "health",
        "domain": "health",
        "description": "Body wisdom and energy patterns",
    },
    # Life Modules
    "JOURNALING": {
        "name": "AI Journaling",
        "category": "life",
        "domain": "journaling",
        "description": "Voice and text journaling",
    },
    "FINANCE": {
        "name": "Financial Tracking",
        "category": "life",
        "domain": "finance",
        "description": "Spending patterns aligned to design",
    },
    "RELATIONSHIPS": {
        "name": "Relationship Analysis",
        "category": "life",
        "domain": "relationships",
        "description": "Composite chart compatibility",
    },
    # System Modules
    "PROACTIVE_AGENT": {
        "name": "Proactive Agent",
        "category": "system",
        "domain": None,
        "description": "AI-initiated check-ins",
    },
    "GAMES": {
        "name": "Micro-Games",
        "category": "system",
        "domain": None,
        "description": "Cognitive assessment games",
    },
}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[ModuleState])
async def list_modules():
    """
    List all available modules with their current state.
    
    Returns all modules defined in the system with their
    enabled/disabled status and domain mappings.
    """
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        
        modules = []
        for module_id, definition in MODULE_DEFINITIONS.items():
            state = await bridge.get_module_state(module_id)
            modules.append(ModuleState(
                id=module_id,
                name=definition["name"],
                enabled=state.enabled if state else True,
                domain=definition.get("domain"),
                category=definition["category"],
                config=state.config if state else {},
                last_synced=state.last_synced.isoformat() if state and state.last_synced else None,
            ))
        
        return modules
        
    except Exception as e:
        logger.error(f"Error listing modules: {e}")
        # Return defaults on error
        return [
            ModuleState(
                id=module_id,
                name=definition["name"],
                enabled=True,
                domain=definition.get("domain"),
                category=definition["category"],
            )
            for module_id, definition in MODULE_DEFINITIONS.items()
        ]


@router.get("/{module_id}", response_model=ModuleState)
async def get_module(module_id: str):
    """
    Get state of a specific module.
    
    Args:
        module_id: The module identifier (e.g., "HUMAN_DESIGN")
    
    Returns:
        ModuleState with enabled status and configuration
    """
    if module_id not in MODULE_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        
        definition = MODULE_DEFINITIONS[module_id]
        state = await bridge.get_module_state(module_id)
        
        return ModuleState(
            id=module_id,
            name=definition["name"],
            enabled=state.enabled if state else True,
            domain=definition.get("domain"),
            category=definition["category"],
            config=state.config if state else {},
            last_synced=state.last_synced.isoformat() if state and state.last_synced else None,
        )
        
    except Exception as e:
        logger.error(f"Error getting module {module_id}: {e}")
        definition = MODULE_DEFINITIONS[module_id]
        return ModuleState(
            id=module_id,
            name=definition["name"],
            enabled=True,
            domain=definition.get("domain"),
            category=definition["category"],
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_modules(request: SyncRequest):
    """
    Sync frontend module preferences to backend.
    
    This is the PRIMARY method for keeping frontend and backend
    module states in sync. The frontend calls this after any
    module toggle or preset change.
    
    Args:
        request: SyncRequest with enabled/disabled module lists
        
    Returns:
        SyncResponse with sync results
    """
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        
        # Sync preferences
        result = await bridge.sync_from_frontend({
            "enabled": request.preferences.enabled_modules,
            "disabled": request.preferences.disabled_modules,
            "preset": request.preferences.preset,
        })
        
        # Get list of updated domains
        updated_domains = []
        for module_id in request.preferences.enabled_modules:
            definition = MODULE_DEFINITIONS.get(module_id, {})
            domain = definition.get("domain")
            if domain and domain not in updated_domains:
                updated_domains.append(domain)
        
        return SyncResponse(
            success=True,
            modules_synced=len(request.preferences.enabled_modules) + len(request.preferences.disabled_modules),
            domains_updated=updated_domains,
            message=f"Synced {len(request.preferences.enabled_modules)} enabled modules",
        )
        
    except Exception as e:
        logger.error(f"Error syncing modules: {e}")
        return SyncResponse(
            success=False,
            modules_synced=0,
            domains_updated=[],
            message=f"Sync failed: {str(e)}",
        )


@router.post("/{module_id}/toggle", response_model=ModuleState)
async def toggle_module(module_id: str, enabled: bool):
    """
    Toggle a specific module on or off.
    
    Args:
        module_id: The module to toggle
        enabled: New enabled state
        
    Returns:
        Updated ModuleState
    """
    if module_id not in MODULE_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        
        # Toggle the module
        new_state = await bridge.toggle_module(module_id, enabled)
        
        definition = MODULE_DEFINITIONS[module_id]
        return ModuleState(
            id=module_id,
            name=definition["name"],
            enabled=new_state.enabled,
            domain=definition.get("domain"),
            category=definition["category"],
            config=new_state.config,
            last_synced=new_state.last_synced.isoformat() if new_state.last_synced else None,
        )
        
    except Exception as e:
        logger.error(f"Error toggling module {module_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains", response_model=List[DomainMapping])
async def list_domain_mappings():
    """
    List all module-to-domain mappings.
    
    Returns the mapping between frontend modules and backend domains,
    showing which modules affect which domains.
    """
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        
        mappings = []
        for module_id, definition in MODULE_DEFINITIONS.items():
            domain = definition.get("domain")
            if domain:
                state = await bridge.get_module_state(module_id)
                mappings.append(DomainMapping(
                    module_id=module_id,
                    module_name=definition["name"],
                    domain_name=domain,
                    enabled=state.enabled if state else True,
                ))
        
        return mappings
        
    except Exception as e:
        logger.error(f"Error listing domain mappings: {e}")
        return [
            DomainMapping(
                module_id=module_id,
                module_name=definition["name"],
                domain_name=definition["domain"],
                enabled=True,
            )
            for module_id, definition in MODULE_DEFINITIONS.items()
            if definition.get("domain")
        ]


@router.get("/enabled")
async def get_enabled_modules() -> List[str]:
    """
    Get list of currently enabled module IDs.
    
    Quick endpoint for checking which modules are active.
    """
    try:
        from ..core.module_bridge import get_bridge
        bridge = await get_bridge()
        return await bridge.get_enabled_modules()
    except Exception as e:
        logger.error(f"Error getting enabled modules: {e}")
        # Default to all enabled
        return list(MODULE_DEFINITIONS.keys())
