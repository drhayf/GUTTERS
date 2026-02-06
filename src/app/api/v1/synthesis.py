"""
GUTTERS Synthesis API

Endpoints for hierarchical profile synthesis.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.ai.llm_factory import get_llm
from ...core.db.database import async_get_db
from ...core.memory.active_memory import get_active_memory
from ...modules.intelligence.observer.storage import ObserverFindingStorage
from ...modules.intelligence.synthesis.module_synthesis import ModuleSynthesizer

router = APIRouter(prefix="/synthesis", tags=["synthesis"])

@router.get("/hierarchical/{user_id}")
async def get_hierarchical_synthesis(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get hierarchical synthesis showing module-specific insights.

    Returns:
        {
            "master_synthesis": "...",
            "module_syntheses": {
                "astrology": "...",
                "human_design": "...",
                "numerology": "...",
                "observer": "..."
            },
            "modules_included": [...],
            "confidence": 0.85
        }
    """
    # Verify authorization (current_user is a dict from get_current_user in this project)
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    memory = get_active_memory()
    await memory.initialize()

    # Get cached master synthesis
    master = await memory.get_master_synthesis(user_id)

    # Get module data and generate individual syntheses
    module_synthesizer = ModuleSynthesizer(get_llm())

    astro_data = await memory.get_module_output(user_id, "astrology")
    hd_data = await memory.get_module_output(user_id, "human_design")
    num_data = await memory.get_module_output(user_id, "numerology")

    observer_storage = ObserverFindingStorage()
    findings = await observer_storage.get_findings(user_id, min_confidence=0.7)

    module_syntheses = {}

    if astro_data:
        module_syntheses["astrology"] = await module_synthesizer.synthesize_astrology(astro_data)

    if hd_data:
        module_syntheses["human_design"] = await module_synthesizer.synthesize_human_design(hd_data)

    if num_data:
        module_syntheses["numerology"] = await module_synthesizer.synthesize_numerology(num_data)

    if findings:
        module_syntheses["observer"] = await module_synthesizer.synthesize_observer_patterns(findings)

    return {
        "master_synthesis": master.get("synthesis") if master else None,
        "module_syntheses": module_syntheses,
        "modules_included": master.get("modules_included", []) if master else [],
        "confidence": 0.85,  # TODO: Calculate from Genesis
        "generated_at": master.get("generated_at") if master else None
    }
