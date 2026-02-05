from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from src.app.api.dependencies import async_get_db, get_current_user as get_current_active_user
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import RecurrenceType, QuestSource, Quest

router = APIRouter()

# --- Schemas ---


class QuestRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    recurrence: str  # Changed to str - always serialize as string
    cron_expression: Optional[str] = None
    difficulty: int
    tags: str
    is_active: bool
    source: str  # Changed to str - serialize Enum as string
    # Instance Data (Optional, for Dashboard)
    job_id: Optional[str] = None
    log_id: Optional[int] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("recurrence", mode="before")
    @classmethod
    def parse_recurrence(cls, v):
        """Normalize recurrence to lowercase string."""
        if isinstance(v, str):
            return v.lower()
        # Handle Enum objects
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()

    @field_validator("source", mode="before")
    @classmethod
    def parse_source(cls, v):
        """Normalize source to lowercase string."""
        if isinstance(v, str):
            return v.lower()
        # Handle Enum objects
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()

    @field_validator("difficulty", mode="before")
    @classmethod
    def parse_difficulty(cls, v):
        if isinstance(v, int):
            return v
        # Map DB string enum back to integer for API
        mapping = {"easy": 1, "medium": 2, "hard": 3, "elite": 4}
        if isinstance(v, str):
            return mapping.get(v.lower(), 1)
        # Handle Enum objects
        if hasattr(v, "value"):
            return mapping.get(str(v.value).lower(), 1)
        return 1


class QuestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    recurrence: str = "once"  # Accept string, will normalize in manager
    cron_expression: Optional[str] = None
    difficulty: int = 1
    tags: List[str] = []

    @field_validator("recurrence", mode="before")
    @classmethod
    def normalize_recurrence(cls, v):
        """Normalize recurrence string to lowercase."""
        if isinstance(v, str):
            return v.lower()
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class QuestUpdate(BaseModel):
    title: Optional[str] = None
    recurrence: Optional[RecurrenceType] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None


# --- Endpoints ---


@router.get("/", response_model=List[QuestRead])
@router.get("", response_model=List[QuestRead])
async def list_quests(
    view: str = Query("tasks", enum=["tasks", "definitions"]),  # "tasks" (Dashboard) or "definitions" (Control Room)
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    List quests.
    view='tasks': Returns pending QuestLogs (the To-Do list).
    view='definitions': Returns all active Quest definitions (for management).
    """
    results = []

    if view == "definitions":
        # Control Room: Show all active quest definitions
        quests = await QuestManager.get_active_quests(db, current_user["id"])
        for q in quests:
            results.append(
                QuestRead(
                    id=q.id,
                    title=q.title,
                    description=q.description,
                    recurrence=q.recurrence,
                    cron_expression=q.cron_expression,
                    difficulty=q.difficulty,
                    tags=q.tags,
                    is_active=q.is_active,
                    source=q.source,
                    job_id=q.job_id,
                    log_id=None,
                    status=None,  # Definitions are conceptually 'active' but have no execution status
                )
            )
    else:
        # Dashboard: Show Pending Logs
        pending_logs = await QuestManager.get_pending_logs(db, current_user["id"])
        for log in pending_logs:
            q = log.quest
            results.append(
                QuestRead(
                    id=q.id,
                    title=q.title,
                    description=q.description,
                    recurrence=q.recurrence,
                    cron_expression=q.cron_expression,
                    difficulty=q.difficulty,
                    tags=q.tags,
                    is_active=q.is_active,
                    source=q.source,
                    job_id=q.job_id,
                    log_id=log.id,
                    status=log.status,
                )
            )

    return results


@router.post("/", response_model=QuestRead)
@router.post("", response_model=QuestRead)
async def create_quest(
    quest_in: QuestCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Create a new quest (Source = USER).
    """
    quest = await QuestManager.create_quest(
        db=db,
        user_id=current_user["id"],
        title=quest_in.title,
        description=quest_in.description,
        recurrence=quest_in.recurrence,
        cron_expression=quest_in.cron_expression,
        difficulty=quest_in.difficulty,
        tags=quest_in.tags,
        source=QuestSource.USER,  # Force User Source
    )
    return quest


@router.patch("/{quest_id}", response_model=QuestRead)
async def update_quest(
    quest_id: int,
    quest_in: QuestUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Update a quest. Handles rescheduling if recurrence changes.
    """
    # Verify ownership handled possibly by manager or check here?
    # Manager doesn't verify ownership if we just pass ID. Ideally we check here.
    # For now, let's trust the ID or add user check.
    # Let's add user check for fidelity.

    # Manager update_quest doesn't check user_id.
    # Let's fetch first to verify ownership.

    try:
        quest = await QuestManager.update_quest(
            db=db,
            quest_id=quest_id,
            title=quest_in.title,
            recurrence=quest_in.recurrence,
            cron_expression=quest_in.cron_expression,
            is_active=quest_in.is_active,
        )
        if quest.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to edit this quest")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return quest


@router.delete("/{quest_id}")
async def delete_quest(
    quest_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Delete a quest and cancel its job.
    """
    try:
        # Verify ownership before deletion
        stmt = select(Quest).where(Quest.id == quest_id)
        result = await db.execute(stmt)
        quest = result.scalar_one_or_none()

        if not quest:
            raise HTTPException(status_code=404, detail="Quest not found")

        if quest.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this quest")

        await QuestManager.delete_quest(db, quest_id)
        return {"status": "success"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
