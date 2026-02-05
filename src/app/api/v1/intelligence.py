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


# ============================================================================
# Hypothesis Endpoints
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class HypothesisFeedbackRequest(BaseModel):
    """Request model for hypothesis feedback."""
    feedback_type: str = Field(
        description="Type of feedback: 'confirm', 'reject', 'partially', 'unsure'"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional user comment explaining their feedback"
    )


class HypothesisListResponse(BaseModel):
    """Response model for hypothesis list."""
    hypotheses: List[dict]
    total: int
    confirmed_count: int
    testing_count: int
    forming_count: int


class HypothesisDetailResponse(BaseModel):
    """Response model for hypothesis detail."""
    hypothesis: dict
    evidence_summary: dict
    top_contributors: List[dict]


@router.get("/hypotheses", response_model=HypothesisListResponse)
async def list_hypotheses(
    current_user: Annotated[dict, Depends(get_current_user)],
    status: Optional[str] = None,
    min_confidence: float = 0.0,
):
    """
    List all hypotheses for the current user.
    
    Optionally filter by status or minimum confidence.
    """
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.modules.intelligence.hypothesis.models import HypothesisStatus
    
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(current_user["id"])
    
    # Apply filters
    if status:
        hypotheses = [h for h in hypotheses if h.status.value == status]
    
    if min_confidence > 0:
        hypotheses = [h for h in hypotheses if h.confidence >= min_confidence]
    
    # Count by status
    confirmed_count = len([h for h in hypotheses if h.status == HypothesisStatus.CONFIRMED])
    testing_count = len([h for h in hypotheses if h.status == HypothesisStatus.TESTING])
    forming_count = len([h for h in hypotheses if h.status == HypothesisStatus.FORMING])
    
    return HypothesisListResponse(
        hypotheses=[h.model_dump(mode="json") for h in hypotheses],
        total=len(hypotheses),
        confirmed_count=confirmed_count,
        testing_count=testing_count,
        forming_count=forming_count
    )


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisDetailResponse)
async def get_hypothesis(
    hypothesis_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get detailed information about a specific hypothesis.
    
    Includes evidence breakdown and top contributors.
    """
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.modules.intelligence.hypothesis.confidence import WeightedConfidenceCalculator
    
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(current_user["id"])
    
    hypothesis = next((h for h in hypotheses if h.id == hypothesis_id), None)
    
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    # Get evidence breakdown
    calculator = WeightedConfidenceCalculator()
    
    evidence_summary = {}
    if hypothesis.confidence_breakdown:
        evidence_summary = hypothesis.confidence_breakdown
    elif hypothesis.evidence_records:
        from src.app.modules.intelligence.hypothesis.confidence import EvidenceRecord
        records = [EvidenceRecord(**r) for r in hypothesis.evidence_records]
        evidence_summary = calculator.get_confidence_breakdown(records)
    
    # Get top contributors
    top_contributors = hypothesis.get_top_contributors(limit=5)
    
    return HypothesisDetailResponse(
        hypothesis=hypothesis.model_dump(mode="json"),
        evidence_summary=evidence_summary,
        top_contributors=top_contributors
    )


@router.post("/hypotheses/{hypothesis_id}/feedback")
async def submit_hypothesis_feedback(
    hypothesis_id: str,
    feedback: HypothesisFeedbackRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Submit feedback on a hypothesis.
    
    User feedback is the highest-weighted evidence type:
    - 'confirm': Strongly increases confidence (+1.0 weight)
    - 'reject': Strongly decreases confidence (-1.5 weight)
    - 'partially': Moderate increase (+0.95 weight)
    - 'unsure': Neutral, recorded for context
    
    User feedback can push hypotheses past confirmation threshold (0.85)
    or trigger rejection.
    """
    from src.app.modules.intelligence.hypothesis.updater import get_hypothesis_updater
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.core.state.chronos import get_chronos_manager
    
    # Validate feedback type
    valid_types = ["confirm", "reject", "partially", "unsure"]
    if feedback.feedback_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback_type. Must be one of: {valid_types}"
        )
    
    # Fetch magi context for the feedback
    magi_context = None
    try:
        chronos_manager = get_chronos_manager()
        chronos_state = await chronos_manager.get_user_chronos(current_user["id"])
        if chronos_state:
            magi_context = {
                "period_card": chronos_state.get("current_card", {}).get("name"),
                "planetary_ruler": chronos_state.get("current_planet"),
                "theme": chronos_state.get("theme"),
            }
    except Exception as e:
        logger.warning(f"[HypothesisAPI] Failed to fetch magi context: {e}")
    
    # Get updater and process feedback
    updater = get_hypothesis_updater()
    
    updated_hypothesis = await updater.add_user_feedback(
        hypothesis_id=hypothesis_id,
        user_id=current_user["id"],
        feedback_type=feedback.feedback_type,
        comment=feedback.comment,
        db=db,
        magi_context=magi_context
    )
    
    if not updated_hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    logger.info(
        f"[HypothesisAPI] User {current_user['id']} submitted '{feedback.feedback_type}' "
        f"feedback for hypothesis {hypothesis_id}. "
        f"New confidence: {updated_hypothesis.confidence:.2f}, "
        f"status: {updated_hypothesis.status.value}"
    )
    
    return {
        "status": "feedback_recorded",
        "hypothesis_id": hypothesis_id,
        "feedback_type": feedback.feedback_type,
        "new_confidence": updated_hypothesis.confidence,
        "new_status": updated_hypothesis.status.value,
        "evidence_count": updated_hypothesis.evidence_count,
        "contradictions": updated_hypothesis.contradictions
    }


@router.post("/hypotheses/{hypothesis_id}/recalculate")
async def recalculate_hypothesis_confidence(
    hypothesis_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Force recalculation of hypothesis confidence.
    
    Useful after time has passed and recency decay should be applied
    to evidence.
    """
    from src.app.modules.intelligence.hypothesis.updater import get_hypothesis_updater
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(current_user["id"])
    
    hypothesis = next((h for h in hypotheses if h.id == hypothesis_id), None)
    
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    updater = get_hypothesis_updater()
    
    # Recalculate using updater's internal method
    updated = await updater._recalculate_confidence(hypothesis, db)
    
    return {
        "status": "recalculated",
        "hypothesis_id": hypothesis_id,
        "confidence": updated.confidence,
        "status": updated.status.value,
        "last_recalculation": updated.last_recalculation.isoformat() if updated.last_recalculation else None
    }


@router.get("/hypotheses/confidence-trends/{hypothesis_id}")
async def get_hypothesis_confidence_trends(
    hypothesis_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get confidence history for visualization.
    
    Returns snapshots showing how confidence evolved over time.
    """
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(current_user["id"])
    
    hypothesis = next((h for h in hypotheses if h.id == hypothesis_id), None)
    
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    return {
        "hypothesis_id": hypothesis_id,
        "current_confidence": hypothesis.confidence,
        "current_status": hypothesis.status.value,
        "confidence_history": hypothesis.confidence_history,
        "total_snapshots": len(hypothesis.confidence_history),
        "trend": hypothesis.get_confidence_trend() if hasattr(hypothesis, 'get_confidence_trend') else None
    }


# ============================================================================
# Council of Systems Endpoints (I-Ching + Cardology Synthesis)
# ============================================================================

@router.get("/council/hexagram")
async def get_current_hexagram(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get current I-Ching hexagram (Sun/Earth gates).
    
    Returns the daily cosmic code with gate names, lines, and Gene Key gifts.
    This is the micro-coordinate (~6-day cycle) in the Council of Systems.
    """
    from src.app.modules.intelligence.council import get_council_service
    
    service = get_council_service()
    hexagram = service.get_current_hexagram()
    
    return {
        "status": "success",
        "hexagram": {
            "sun_gate": hexagram.sun_gate,
            "sun_line": hexagram.sun_line,
            "sun_gate_name": hexagram.sun_gate_name,
            "sun_gate_keynote": hexagram.sun_gate_keynote,
            "sun_gene_key_gift": hexagram.sun_gene_key_gift,
            "sun_gene_key_shadow": hexagram.sun_gene_key_shadow,
            "sun_gene_key_siddhi": hexagram.sun_gene_key_siddhi,
            "earth_gate": hexagram.earth_gate,
            "earth_line": hexagram.earth_line,
            "earth_gate_name": hexagram.earth_gate_name,
            "earth_gate_keynote": hexagram.earth_gate_keynote,
            "earth_gene_key_gift": hexagram.earth_gene_key_gift,
            "polarity_theme": hexagram.polarity_theme,
        },
        "description": "Current Sun/Earth gate positions from the I-Ching Logic Kernel"
    }


@router.get("/council/synthesis")
async def get_council_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Get unified synthesis from the Council of Systems.
    
    Combines:
    - Cardology (macro: 52-day planetary periods)
    - I-Ching (micro: ~6-day gate transits)
    
    Returns cross-system resonance and synthesized guidance.
    """
    from src.app.modules.intelligence.council import get_council_service
    
    service = get_council_service()
    
    # Get hexagram
    hexagram = service.get_current_hexagram()
    
    # Get full council synthesis
    synthesis = service.get_council_synthesis()
    
    return {
        "status": "success",
        "council": {
            "resonance_score": synthesis.resonance_score,
            "resonance_type": synthesis.resonance_type,
            "resonance_description": synthesis.resonance_description,
            "macro_symbol": synthesis.macro_symbol,
            "macro_archetype": synthesis.macro_archetype,
            "macro_keynote": synthesis.macro_keynote,
            "micro_symbol": synthesis.micro_symbol,
            "micro_archetype": synthesis.micro_archetype,
            "micro_keynote": synthesis.micro_keynote,
            "unified_gift": synthesis.unified_gift,
            "unified_shadow": synthesis.unified_shadow,
            "unified_siddhi": synthesis.unified_siddhi,
            "element_profile": synthesis.element_profile,
            "quest_suggestions": synthesis.quest_suggestions,
        },
        "description": "Unified wisdom from the Council of Systems"
    }


@router.get("/council/resonance")
async def get_cross_system_resonance(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get the current cross-system resonance level.
    
    Calculates elemental harmony between Cardology and I-Ching systems.
    
    Returns:
    - HARMONIC (0.7+): Strong alignment
    - SUPPORTIVE (0.5-0.7): Complementary energies
    - NEUTRAL (0.3-0.5): Independent operation
    - CHALLENGING (0.1-0.3): Growth opportunity
    - DISSONANT (<0.1): Tension requiring integration
    """
    from src.app.modules.intelligence.council import get_council_service
    
    service = get_council_service()
    resonance_score, resonance_type = service.get_resonance_level()
    synthesis = service.get_council_synthesis()
    
    return {
        "status": "success",
        "resonance_score": resonance_score,
        "resonance_type": resonance_type,
        "elemental_profile": synthesis.element_profile,
        "guidance": synthesis.resonance_description,
        "quest_suggestions": synthesis.quest_suggestions,
    }


@router.get("/council/gate/{gate_number}")
async def get_gate_info(
    gate_number: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    line_number: int | None = None
):
    """
    Get detailed information about a specific I-Ching gate and optionally a specific line.
    
    Args:
        gate_number: Gate 1-64
        line_number: Optional line 1-6
        
    Returns gate data including HD name, keynote, Gene Key frequencies, and line interpretation if requested.
    """
    from src.app.modules.intelligence.council import get_council_service
    
    if not 1 <= gate_number <= 64:
        raise HTTPException(
            status_code=400,
            detail="Gate number must be between 1 and 64"
        )
    
    if line_number is not None and not 1 <= line_number <= 6:
        raise HTTPException(
            status_code=400,
            detail="Line number must be between 1 and 6"
        )
    
    service = get_council_service()
    gate_info = service.get_gate_info(gate_number, line_number)
    
    if not gate_info:
        raise HTTPException(
            status_code=404,
            detail=f"Gate {gate_number} not found in database"
        )
    
    return {
        "status": "success",
        "gate": gate_info,
    }


@router.get("/council/gate/{gate_number}/history")
async def get_gate_history(
    gate_number: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get user's historical experience during a specific gate.
    
    Analyzes journal entries, mood scores, and patterns from all times
    this gate has been active for the user.
    
    Args:
        gate_number: Gate 1-64
        
    Returns:
        Historical analysis including mood averages, themes, occurrences
    """
    from src.app.modules.intelligence.council import get_council_service
    
    if not 1 <= gate_number <= 64:
        raise HTTPException(
            status_code=400,
            detail="Gate number must be between 1 and 64"
        )
    
    user_id = current_user["id"]
    service = get_council_service()
    
    history = await service.analyze_gate_history(user_id, gate_number, db)
    
    if "error" in history:
        raise HTTPException(
            status_code=400,
            detail=history["error"]
        )
    
    return {
        "status": "success",
        "history": history,
    }


@router.get("/council/synthesis/contextual")
async def get_contextual_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get Council synthesis with personalized context-aware guidance.
    
    This endpoint provides enhanced guidance that considers:
    - Your recent journal sentiment
    - Your active quests
    - Your historical experience with the current gate
    - Current resonance type
    
    Returns:
        Synthesis with context-aware guidance
    """
    from src.app.modules.intelligence.council import get_council_service
    
    user_id = current_user["id"]
    service = get_council_service()
    
    # Get base synthesis
    synthesis = service.get_council_synthesis()
    
    # Generate context-aware guidance
    contextual_guidance = await service.generate_context_aware_guidance(
        user_id, synthesis, db
    )
    
    return {
        "status": "success",
        "synthesis": {
            "timestamp": synthesis.timestamp,
            "resonance_score": synthesis.resonance_score,
            "resonance_type": synthesis.resonance_type,
            "macro_symbol": synthesis.macro_symbol,
            "micro_symbol": synthesis.micro_symbol,
            "unified_gift": synthesis.unified_gift,
            "contextual_guidance": contextual_guidance,  # Enhanced guidance
            "quest_suggestions": synthesis.quest_suggestions,
        },
        "description": "Context-aware Council synthesis tailored to your current state"
    }


# ============================================================================
# Oracle Endpoints (Phase 28)
# ============================================================================

@router.post("/oracle/draw")
async def perform_oracle_draw(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Perform a cryptographically secure Oracle draw.
    
    Randomly selects a Card (1-52) and Hexagram (1-64) using crypto.getRandomValues,
    then generates a synthesis via the Council of Systems and creates a diagnostic
    question using LLM.
    
    Returns:
        OracleReading with full synthesis and diagnostic question
    """
    from src.app.modules.intelligence.oracle import OracleService
    from datetime import datetime, UTC
    
    user_id = current_user["id"]
    
    # Get user's birth date for personalized context
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    birth_date = profile.birth_date if profile else None
    
    # Perform draw
    service = OracleService()
    reading = await service.perform_daily_draw(user_id, db, birth_date)
    
    return {
        "status": "success",
        "reading": {
            "id": reading.id,
            "card": {
                "rank": reading.card_rank,
                "suit": reading.card_suit,
                "name": f"{_get_rank_name(reading.card_rank)} of {reading.card_suit}"
            },
            "hexagram": {
                "number": reading.hexagram_number,
                "line": reading.hexagram_line
            },
            "synthesis": reading.synthesis_text,
            "diagnostic_question": reading.diagnostic_question,
            "accepted": reading.accepted,
            "reflected": reading.reflected,
            "created_at": reading.created_at.isoformat()
        }
    }


@router.post("/oracle/{reading_id}/accept")
async def accept_oracle_reading(
    reading_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Accept an Oracle reading - creates a Quest.
    
    Quest Spec:
    - Category: MISSION
    - Source: ORACLE
    - Title: "Embodying the [Card Name]"
    - XP: 350 (250 base + 100 Oracle bonus)
    
    Args:
        reading_id: ID of the Oracle reading to accept
        
    Returns:
        Created Quest
    """
    from src.app.modules.intelligence.oracle import OracleService
    
    user_id = current_user["id"]
    
    service = OracleService()
    quest = await service.accept_reading(reading_id, user_id, db)
    
    return {
        "status": "success",
        "message": "Quest created from Oracle reading",
        "quest": {
            "id": quest.id,
            "title": quest.title,
            "description": quest.description,
            "category": quest.category.value,
            "xp_reward": quest.xp_reward,
            "created_at": quest.created_at.isoformat()
        }
    }


@router.post("/oracle/{reading_id}/reflect")
async def reflect_on_oracle_reading(
    reading_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Open journal reflection on Oracle reading.
    
    Creates a ReflectionPrompt with the diagnostic question.
    
    Args:
        reading_id: ID of the Oracle reading to reflect on
        
    Returns:
        Created ReflectionPrompt
    """
    from src.app.modules.intelligence.oracle import OracleService
    
    user_id = current_user["id"]
    
    service = OracleService()
    prompt = await service.reflect_on_reading(reading_id, user_id, db)
    
    return {
        "status": "success",
        "message": "Reflection prompt created",
        "prompt": {
            "id": prompt.id,
            "prompt_text": prompt.prompt_text,
            "topic": prompt.topic,
            "created_at": prompt.created_at.isoformat()
        }
    }


@router.get("/oracle/{reading_id}")
async def get_oracle_reading(
    reading_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get a specific Oracle reading by ID.
    
    Args:
        reading_id: ID of the reading
        
    Returns:
        Oracle reading details
    """
    from src.app.modules.intelligence.oracle import OracleService
    
    user_id = current_user["id"]
    
    service = OracleService()
    reading = await service.get_reading(reading_id, user_id, db)
    
    if not reading:
        raise HTTPException(
            status_code=404,
            detail="Oracle reading not found"
        )
    
    return {
        "status": "success",
        "reading": {
            "id": reading.id,
            "card": {
                "rank": reading.card_rank,
                "suit": reading.card_suit,
                "name": f"{_get_rank_name(reading.card_rank)} of {reading.card_suit}"
            },
            "hexagram": {
                "number": reading.hexagram_number,
                "line": reading.hexagram_line
            },
            "synthesis": reading.synthesis_text,
            "diagnostic_question": reading.diagnostic_question,
            "accepted": reading.accepted,
            "reflected": reading.reflected,
            "quest_id": reading.quest_id,
            "prompt_id": reading.prompt_id,
            "created_at": reading.created_at.isoformat()
        }
    }


@router.get("/oracle/readings")
async def get_user_oracle_readings(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    limit: int = 10
):
    """
    Get user's recent Oracle readings.
    
    Args:
        limit: Number of recent readings to return (default 10)
        
    Returns:
        List of Oracle readings
    """
    from src.app.modules.intelligence.oracle import OracleService
    
    user_id = current_user["id"]
    
    service = OracleService()
    readings = await service.get_user_readings(user_id, db, limit)
    
    return {
        "status": "success",
        "count": len(readings),
        "readings": [
            {
                "id": r.id,
                "card": {
                    "rank": r.card_rank,
                    "suit": r.card_suit,
                    "name": f"{_get_rank_name(r.card_rank)} of {r.card_suit}"
                },
                "hexagram": {
                    "number": r.hexagram_number,
                    "line": r.hexagram_line
                },
                "synthesis": r.synthesis_text[:200] + "..." if len(r.synthesis_text) > 200 else r.synthesis_text,
                "accepted": r.accepted,
                "reflected": r.reflected,
                "created_at": r.created_at.isoformat()
            }
            for r in readings
        ]
    }


def _get_rank_name(rank: int) -> str:
    """Helper to convert rank number to name."""
    names = {1: "Ace", 11: "Jack", 12: "Queen", 13: "King"}
    return names.get(rank, str(rank))
