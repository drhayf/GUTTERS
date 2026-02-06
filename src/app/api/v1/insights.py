import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import async_get_db
from src.app.api.dependencies import get_current_user as get_current_active_user
from src.app.models.insight import JournalEntry, PromptStatus, ReflectionPrompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])

# --- Schemas ---


class ReflectionPromptRead(BaseModel):
    id: int
    prompt_text: str
    topic: str
    status: PromptStatus
    created_at: str  # Simplification for display


class JournalEntryCreate(BaseModel):
    content: str
    mood_score: Optional[int] = None
    tags: List[str] = []
    prompt_id: Optional[int] = None
    context_snapshot: Optional[dict] = None


class JournalEntryRead(BaseModel):
    id: int
    content: str
    mood_score: Optional[int] = None
    tags: List[str] = []
    context_snapshot: Optional[dict] = None
    created_at: str
    prompt_id: Optional[int] = None


# --- Endpoints ---


@router.get("/prompts", response_model=List[ReflectionPromptRead])
async def list_pending_prompts(
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Fetch pending reflection prompts for the current user.
    """
    stmt = (
        select(ReflectionPrompt)
        .where(ReflectionPrompt.user_id == current_user["id"], ReflectionPrompt.status == PromptStatus.PENDING)
        .order_by(ReflectionPrompt.created_at.desc())
    )

    result = await db.execute(stmt)
    prompts = result.scalars().all()

    # Simple conversion to string for created_at to avoid pydantic issues with datetime
    return [
        ReflectionPromptRead(
            id=p.id, prompt_text=p.prompt_text, topic=p.topic, status=p.status, created_at=p.created_at.isoformat()
        )
        for p in prompts
    ]


@router.get("/journal", response_model=List[JournalEntryRead])
async def list_journal_entries(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    List past journal entries.
    """
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == current_user["id"])
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    entries = result.scalars().all()

    return [
        JournalEntryRead(
            id=e.id,
            content=e.content,
            mood_score=e.mood_score,
            tags=e.tags or [],
            context_snapshot=e.context_snapshot,
            created_at=e.created_at.isoformat(),
            prompt_id=e.prompt_id,
        )
        for e in entries
    ]


@router.post("/journal", response_model=JournalEntryRead)
async def create_journal_entry(
    entry_in: JournalEntryCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Create a journal entry, optionally as a response to a prompt.

    Automatically attaches cosmic context snapshot if not provided,
    including solar, lunar, and transit conditions at the time of entry.
    """
    # 1. Verify prompt ownership if provided
    if entry_in.prompt_id:
        stmt = select(ReflectionPrompt).where(
            ReflectionPrompt.id == entry_in.prompt_id, ReflectionPrompt.user_id == current_user["id"]
        )
        result = await db.execute(stmt)
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise HTTPException(status_code=404, detail="Reflection prompt not found")

        # Mark prompt as answered
        prompt.status = PromptStatus.ANSWERED

    # 2. Auto-attach cosmic context if not provided
    context_snapshot = entry_in.context_snapshot
    if context_snapshot is None:
        try:
            from src.app.core.state.chronos import get_chronos_manager
            from src.app.modules.tracking.context import get_cosmic_context

            # Fetch cosmic context (solar, lunar, transits)
            cosmic_context = await get_cosmic_context(current_user["id"])
            context_snapshot = {
                "solar": cosmic_context.get("solar", {}),
                "lunar": cosmic_context.get("lunar", {}),
                "transits": cosmic_context.get("transits", {}),
                "tags": cosmic_context.get("tags", []),
                "intensity_score": cosmic_context.get("intensity_score", 0),
                "timestamp": cosmic_context.get("timestamp"),
            }

            # Inject Magi chronos state for period-aware analysis
            chronos_manager = get_chronos_manager()
            chronos_state = await chronos_manager.get_user_chronos(current_user["id"])
            if chronos_state:
                context_snapshot["magi"] = {
                    "period_card": chronos_state.get("current_card", {}).get("name"),
                    "period_day": 52 - (chronos_state.get("days_remaining", 0) or 0),
                    "period_total": 52,
                    "planetary_ruler": chronos_state.get("current_planet"),
                    "theme": chronos_state.get("theme"),
                    "guidance": chronos_state.get("guidance"),
                    "period_start": chronos_state.get("period_start"),
                    "period_end": chronos_state.get("period_end"),
                    "progress_percent": round(
                        ((52 - (chronos_state.get("days_remaining", 0) or 0)) / 52) * 100, 2
                    ),
                }
        except Exception as e:
            # Don't fail entry creation if context fetch fails
            logger.warning(f"[JournalAPI] Failed to fetch context for user {current_user['id']}: {e}")
            context_snapshot = {"error": str(e), "timestamp": None}

    # 3. Create entry
    entry = JournalEntry(
        user_id=current_user["id"],
        content=entry_in.content,
        mood_score=entry_in.mood_score,
        tags=entry_in.tags,
        prompt_id=entry_in.prompt_id,
        context_snapshot=context_snapshot,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    # 4. Update relevant hypotheses with journal evidence
    try:
        await _update_hypotheses_from_journal(
            user_id=current_user["id"],
            journal_entry={
                "id": entry.id,
                "content": entry.content,
                "mood_score": entry.mood_score,
                "tags": entry.tags or [],
                "context_snapshot": entry.context_snapshot,
                "created_at": entry.created_at.isoformat(),
            },
            db=db,
            magi_context=context_snapshot.get("magi") if context_snapshot else None
        )
    except Exception as e:
        # Don't fail entry creation if hypothesis update fails
        logger.warning(f"[JournalAPI] Failed to update hypotheses for user {current_user['id']}: {e}")

    return JournalEntryRead(
        id=entry.id,
        content=entry.content,
        mood_score=entry.mood_score,
        tags=entry.tags or [],
        context_snapshot=entry.context_snapshot,
        created_at=entry.created_at.isoformat(),
        prompt_id=entry.prompt_id,
    )


async def _update_hypotheses_from_journal(
    user_id: int,
    journal_entry: dict,
    db: AsyncSession,
    magi_context: Optional[dict] = None
) -> int:
    """
    Update hypotheses that are relevant to the journal entry.

    Args:
        user_id: User ID
        journal_entry: Journal entry data
        db: Database session
        magi_context: Optional magi chronos context

    Returns:
        Number of hypotheses updated
    """
    from src.app.modules.intelligence.hypothesis.updater import get_hypothesis_updater

    updater = get_hypothesis_updater()

    # Find relevant hypotheses
    relevant = await updater.get_relevant_hypotheses_for_journal(
        user_id=user_id,
        journal_content=journal_entry.get("content", ""),
        mood_score=journal_entry.get("mood_score"),
        tags=journal_entry.get("tags", [])
    )

    updated_count = 0

    for match in relevant:
        hypothesis = match["hypothesis"]
        relevance = match["relevance"]
        matching_keywords = match.get("matching_keywords", [])

        # Only add as evidence if relevance is meaningful
        if relevance >= 0.2:
            try:
                await updater.add_journal_evidence(
                    hypothesis=hypothesis,
                    journal_entry=journal_entry,
                    relevance_score=relevance,
                    matching_keywords=matching_keywords,
                    db=db,
                    magi_context=magi_context
                )
                updated_count += 1
                logger.debug(
                    f"[JournalAPI] Updated hypothesis {hypothesis.id} "
                    f"with journal evidence (relevance: {relevance:.0%})"
                )
            except Exception as e:
                logger.warning(
                    f"[JournalAPI] Failed to add journal evidence to hypothesis "
                    f"{hypothesis.id}: {e}"
                )

    if updated_count > 0:
        logger.info(
            f"[JournalAPI] Updated {updated_count} hypotheses from journal entry "
            f"for user {user_id}"
        )

    return updated_count


@router.patch("/prompts/{prompt_id}/dismiss")
async def dismiss_prompt(
    prompt_id: int, db: AsyncSession = Depends(async_get_db), current_user: dict = Depends(get_current_active_user)
):
    """Dismiss a reflection prompt without answering."""
    stmt = select(ReflectionPrompt).where(
        ReflectionPrompt.id == prompt_id, ReflectionPrompt.user_id == current_user["id"]
    )
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt.status = PromptStatus.DISMISSED
    await db.commit()
    return {"status": "success"}


@router.get("/cosmic-context")
async def get_current_cosmic_context(
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get comprehensive cosmic context for the current moment.

    Returns a snapshot of all cosmic conditions including:
    - Solar: Kp index, Bz, solar wind, shield integrity
    - Lunar: Phase, sign, VoC status
    - Transits: Active retrogrades, exact aspects to natal chart
    - Tags: Searchable tags derived from conditions
    - Intensity Score: Overall cosmic activity level (0-10)

    Useful for understanding the cosmic backdrop of the present moment
    before journaling or making decisions.
    """
    from src.app.modules.tracking.context import get_cosmic_context

    try:
        context = await get_cosmic_context(current_user["id"])
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
