from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import async_get_db
from src.app.api.dependencies import get_current_user as get_current_active_user
from src.app.models.progression import PlayerStats

router = APIRouter(prefix="/progression", tags=["progression"])

# --- Schemas ---


class ProgressionStats(BaseModel):
    level: int
    rank: str
    experience_points: int
    xp_to_next_level: int
    xp_current_level: int
    xp_required_level: int
    level_progress_percent: float
    sync_rate: float
    sync_rate_momentum: float
    streak_count: int


# --- Endpoints ---


@router.get("/stats", response_model=ProgressionStats)
async def get_progression_stats(
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Fetch the current user's Solo Leveling HUD statistics.
    """
    stmt = select(PlayerStats).where(PlayerStats.user_id == current_user["id"])
    result = await db.execute(stmt)
    stats = result.scalar_one_or_none()

    if not stats:
        # Initialize if not found
        stats = PlayerStats(user_id=current_user["id"])
        db.add(stats)
        await db.commit()
        await db.refresh(stats)

    # Momentum Logic: Compare current WMA to yesterday's score in history
    momentum = 0.0
    if stats.sync_history and len(stats.sync_history) > 0:
        last_score = stats.sync_history[-1].get("score", stats.sync_rate)
        momentum = stats.sync_rate - last_score

    # Calculate Level Thresholds
    import math

    def calculate_threshold(lvl):
        if lvl <= 1:
            return 0
        return int((lvl - 1) * 1000 * math.pow(1.5, lvl - 2))

    # Current Level Floor (Total XP required to reach CURRENT level)
    # Using the formula derived from xp_to_next_level:
    # To reach Level L, you needed the ceiling of L-1.
    # Formula used in model: threshold = L * 1000 * 1.5^(L-1). This is the ceiling of L.
    # So floor of L is ceiling of L-1.

    # Let's verify formula from model `xp_to_next_level`:
    # threshold = int(self.level * 1000 * math.pow(1.5, self.level - 1))
    # This 'threshold' is the TOTAL XP needed to complete the current level.
    xp_ceiling = int(stats.level * 1000 * math.pow(1.5, stats.level - 1))

    # xp_floor is the ceiling of the previous level (stats.level - 1)
    if stats.level > 1:
        prev_level = stats.level - 1
        xp_floor = int(prev_level * 1000 * math.pow(1.5, prev_level - 1))
    else:
        xp_floor = 0

    xp_current_level = max(0, stats.experience_points - xp_floor)
    xp_required_level = max(1, xp_ceiling - xp_floor)  # Avoid div by 0

    level_progress_percent = min(100.0, (xp_current_level / xp_required_level) * 100)

    return ProgressionStats(
        level=stats.level,
        rank=stats.rank,
        experience_points=stats.experience_points,
        xp_to_next_level=stats.xp_to_next_level,
        xp_current_level=xp_current_level,
        xp_required_level=xp_required_level,
        level_progress_percent=level_progress_percent,
        sync_rate=stats.sync_rate,
        sync_rate_momentum=momentum,
        streak_count=stats.streak_count,
    )


@router.get("/history")
async def get_progression_history(
    limit: int = 10,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Returns a timeline of recent sync performance.
    """
    stmt = select(PlayerStats).where(PlayerStats.user_id == current_user["id"])
    result = await db.execute(stmt)
    stats = result.scalar_one_or_none()

    if not stats:
        return []

    return stats.sync_history[-limit:]
