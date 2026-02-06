"""
GUTTERS Memory API

Endpoints for Active Working Memory operations:
- Get current context
- Trigger synthesis
- Invalidate cache
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...api.dependencies import get_current_user
from ...core.memory import SynthesisTrigger, get_active_memory, get_orchestrator

router = APIRouter(prefix="/memory", tags=["memory"])


# ============================================================================
# Response Models
# ============================================================================

class ContextResponse(BaseModel):
    """Response for get_context endpoint."""
    synthesis: dict | None
    modules: dict
    history: list
    preferences: dict
    assembled_at: str


class SynthesizeRequest(BaseModel):
    """Request for synthesize endpoint."""
    background: bool = True


class SynthesizeResponse(BaseModel):
    """Response for synthesize endpoint."""
    status: str
    message: str
    synthesis: dict | None = None


class InvalidateResponse(BaseModel):
    """Response for invalidate endpoint."""
    status: str
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/context", response_model=ContextResponse)
async def get_active_context(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Get current active working memory context.

    Returns the full context assembled from hot and warm memory layers:
    - synthesis: Current master synthesis (if available)
    - modules: Cached module outputs (astrology, human_design, numerology)
    - history: Recent conversation history (last 5)
    - preferences: User preferences

    This is a fast read (<5ms from Redis).
    """
    memory = get_active_memory()

    if not memory.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    context = await memory.get_full_context(current_user["id"])

    return ContextResponse(
        synthesis=context.get("synthesis"),
        modules=context.get("modules", {}),
        history=context.get("history", []),
        preferences=context.get("preferences", {}),
        assembled_at=context.get("assembled_at", "")
    )


@router.post("/synthesize", response_model=SynthesizeResponse)
async def trigger_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: SynthesizeRequest | None = None
):
    """
    Manually trigger synthesis.

    By default runs in background (non-blocking, returns immediately).
    Set background=false to wait for synthesis to complete.

    Background mode returns:
        - status: "queued"

    Foreground mode returns:
        - status: "complete"
        - synthesis: Full synthesis result
    """
    request = request or SynthesizeRequest()

    try:
        orchestrator = await get_orchestrator()

        result = await orchestrator.trigger_synthesis(
            user_id=current_user["id"],
            trigger_type=SynthesisTrigger.USER_REQUESTED,
            background=request.background
        )

        if request.background:
            return SynthesizeResponse(
                status="queued",
                message="Synthesis queued for background processing"
            )
        else:
            return SynthesizeResponse(
                status="complete",
                message="Synthesis completed successfully",
                synthesis=result
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.delete("/invalidate", response_model=InvalidateResponse)
async def invalidate_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    module: str | None = None
):
    """
    Invalidate cached synthesis or module output.

    Without module parameter: Clears master synthesis cache.
    With module parameter: Clears specific module output cache.

    Forces re-generation/re-read on next access.

    Args:
        module: Optional module name to invalidate (astrology, human_design, numerology)
    """
    memory = get_active_memory()

    if not memory.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    user_id = current_user["id"]

    if module:
        # Validate module name
        valid_modules = ["astrology", "human_design", "numerology"]
        if module not in valid_modules:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid module. Valid options: {valid_modules}"
            )

        await memory.invalidate_module(user_id, module)
        return InvalidateResponse(
            status="invalidated",
            message=f"Module '{module}' cache cleared for user {user_id}"
        )
    else:
        await memory.invalidate_synthesis(user_id)
        return InvalidateResponse(
            status="invalidated",
            message=f"Synthesis cache cleared for user {user_id}"
        )


@router.get("/history")
async def get_conversation_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 10
):
    """
    Get recent conversation history.

    Returns the last N conversations from hot memory (Redis).
    Maximum limit is 10 (stored in hot memory).

    Args:
        limit: Number of conversations to return (default: 10, max: 10)
    """
    memory = get_active_memory()

    if not memory.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    # Enforce limit
    limit = min(limit, 10)

    history = await memory.get_conversation_history(current_user["id"], limit)

    return {
        "history": history,
        "count": len(history)
    }


@router.get("/preferences")
async def get_preferences(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Get user preferences from memory.

    Returns cached preferences (or defaults if not set).
    """
    memory = get_active_memory()

    if not memory.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    prefs = await memory.get_user_preferences(current_user["id"])

    return {"preferences": prefs}


@router.post("/preferences/{key}")
async def set_preference(
    key: str,
    value: str,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Set a user preference.

    Updates in both Redis (cache) and PostgreSQL (permanent).

    Args:
        key: Preference key (e.g., "synthesis_schedule")
        value: Preference value
    """
    memory = get_active_memory()

    if not memory.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    # Validate known keys
    valid_keys = ["llm_model", "synthesis_schedule", "synthesis_time"]
    if key not in valid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preference key. Valid options: {valid_keys}"
        )

    await memory.set_user_preference(current_user["id"], key, value)

    return {
        "status": "updated",
        "key": key,
        "value": value
    }
