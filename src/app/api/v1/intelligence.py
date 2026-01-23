"""
GUTTERS Intelligence API

Endpoints for profile synthesis and query functionality.
Integrates with all calculation modules to provide unified insights.
"""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...models.user_profile import UserProfile
from ...modules.intelligence.query import QueryEngine, QueryRequest, QueryResponse
from ...modules.intelligence.synthesis import (
    ALLOWED_MODELS,
    DEFAULT_MODEL,
    ProfileSynthesizer,
    SynthesisRequest,
    SynthesisResponse,
    UnifiedProfile,
    get_user_preferred_model,
    update_user_preference,
)
from ...modules.registry import ModuleRegistry

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ============================================================================
# Model Preference Endpoints
# ============================================================================

class ModelInfo:
    """Model information for API response."""
    
    MODELS = [
        {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet",
            "description": "Balanced performance and cost",
            "tier": "standard"
        },
        {
            "id": "anthropic/claude-opus-4.5-20251101",
            "name": "Claude Opus 4.5",
            "description": "Maximum reasoning power",
            "tier": "premium"
        },
        {
            "id": "qwen/qwen-2.5-72b-instruct:free",
            "name": "Qwen 2.5 72B",
            "description": "Fast and free for testing",
            "tier": "free"
        }
    ]


@router.get("/preferences/models")
async def get_available_models():
    """
    Get list of available LLM models.
    
    Returns all configured models with metadata for UI display.
    """
    return {
        "models": ModelInfo.MODELS,
        "default": DEFAULT_MODEL
    }


@router.get("/preferences/model")
async def get_current_model(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get user's current preferred LLM model.
    """
    model = await get_user_preferred_model(current_user["id"], db)
    return {"model": model}


@router.post("/preferences/model")
async def set_preferred_model(
    model: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Set user's preferred LLM model.
    
    Validates model is in allowed list before saving.
    """
    if model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Allowed: {ALLOWED_MODELS}"
        )
    
    await update_user_preference(current_user["id"], "llm_model", model, db)
    
    return {"model": model, "status": "updated"}


# ============================================================================
# Synthesis Endpoints
# ============================================================================

@router.get("/profile/synthesis", response_model=UnifiedProfile | None)
async def get_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get existing synthesis for current user.
    
    Returns cached synthesis if available, otherwise None.
    Use POST to trigger new synthesis.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.data:
        return None
    
    synthesis_data = profile.data.get("synthesis")
    if not synthesis_data:
        return None
    
    return UnifiedProfile(**synthesis_data)


@router.post("/profile/synthesis", response_model=SynthesisResponse)
async def trigger_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    background_tasks: BackgroundTasks,
    request: SynthesisRequest | None = None,
):
    """
    Trigger profile synthesis.
    
    Queues synthesis as a background task and returns immediately.
    Uses specified model, user's preferred model, or default.
    
    If force_regenerate is True, regenerates even if synthesis exists.
    """
    user_id = current_user["id"]
    
    # Determine model to use
    request = request or SynthesisRequest()
    if request.model:
        if request.model not in ALLOWED_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Allowed: {ALLOWED_MODELS}"
            )
        model = request.model
    else:
        model = await get_user_preferred_model(user_id, db)
    
    # Check if synthesis already exists
    if not request.force_regenerate:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile and profile.data and profile.data.get("synthesis"):
            return SynthesisResponse(
                status="exists",
                message="Synthesis already exists. Use force_regenerate=true to regenerate.",
                model=model,
                synthesis=UnifiedProfile(**profile.data["synthesis"])
            )
    
    # Check if there are modules to synthesize
    calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
    if not calculated:
        raise HTTPException(
            status_code=400,
            detail="No calculated modules found. Submit birth data first."
        )
    
    # Queue synthesis in background
    background_tasks.add_task(
        _run_synthesis_background,
        user_id,
        model,
    )
    
    return SynthesisResponse(
        status="queued",
        message=f"Synthesis queued for {len(calculated)} modules",
        model=model,
    )


async def _run_synthesis_background(user_id: int, model: str):
    """
    Background task to run synthesis.
    
    Creates its own database session since this runs after
    the request completes.
    """
    from ...core.db.database import async_session
    
    async with async_session() as db:
        try:
            synthesizer = ProfileSynthesizer(model_id=model)
            await synthesizer.synthesize_profile(user_id, db)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Background synthesis failed for user {user_id}: {e}")


# ============================================================================
# Query Endpoints
# ============================================================================

@router.post("/query", response_model=QueryResponse)
async def query_profile(
    request: QueryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Answer a question about the user's cosmic profile.
    
    Searches across all calculated modules and uses LLM
    to generate a personalized answer.
    
    Optionally specify a model override.
    """
    user_id = current_user["id"]
    
    # Determine model to use
    if request.model:
        if request.model not in ALLOWED_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Allowed: {ALLOWED_MODELS}"
            )
        model = request.model
    else:
        model = await get_user_preferred_model(user_id, db)
    
    # Check if there's any profile data
    calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
    if not calculated:
        raise HTTPException(
            status_code=400,
            detail="No calculated modules found. Submit birth data first."
        )
    
    # Create engine with selected model and answer query
    engine = QueryEngine(model_id=model)
    response = await engine.answer_query(user_id, request.question, db)
    
    return response


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/profile/modules")
async def get_calculated_modules(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Get list of modules that have calculated for the current user.
    """
    calculated = await ModuleRegistry.get_calculated_modules_for_user(
        current_user["id"], db
    )
    
    return {
        "user_id": current_user["id"],
        "calculated_modules": calculated,
        "total": len(calculated)
    }


@router.get("/registry/modules")
async def get_registered_modules():
    """
    Get list of all registered modules in the system.
    
    Primarily for debugging and admin purposes.
    """
    modules = ModuleRegistry.get_all_modules()
    
    return {
        "modules": [
            {
                "name": m.name,
                "layer": m.layer,
                "version": m.version,
                "description": m.description,
            }
            for m in modules
        ],
        "total": len(modules)
    }
