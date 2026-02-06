# src/app/api/v1/tracking.py

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("/solar")
async def get_solar_tracking(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get current solar weather data."""
    from ...modules.tracking.solar.tracker import SolarTracker

    tracker = SolarTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solar/location")
async def get_solar_location_aware(
    current_user: Annotated[dict, Depends(get_current_user)],
    latitude: float | None = None,
    longitude: float | None = None,
):
    """
    Get location-aware solar weather impact.

    Provides personalized solar weather information including:
    - Aurora visibility probability at user's location
    - Local impact severity based on geomagnetic latitude
    - Specific effects and recommendations for user's position

    If latitude/longitude not provided, falls back to user's birth location.
    """
    from sqlalchemy import select

    from ...core.db.database import async_get_db
    from ...modules.tracking.solar.tracker import SolarTracker

    # Get user's birth location as fallback
    if latitude is None or longitude is None:
        async for db in async_get_db():
            result = await db.execute(
                select(User).where(User.id == current_user["id"])
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Use birth coordinates or default to mid-latitudes
            latitude = latitude or user.birth_latitude or 40.0
            longitude = longitude or user.birth_longitude or -74.0

    tracker = SolarTracker()
    try:
        result = await tracker.fetch_location_aware(latitude, longitude)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lunar")
async def get_lunar_tracking(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get current lunar phase and position."""
    from ...modules.tracking.lunar.tracker import LunarTracker

    tracker = LunarTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transits")
async def get_transit_tracking(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get current planetary transits vs natal chart."""
    from ...modules.tracking.transits.tracker import TransitTracker

    tracker = TransitTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_tracking(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get all tracking data (solar, lunar, transits)."""
    from ...modules.tracking.lunar.tracker import LunarTracker
    from ...modules.tracking.solar.tracker import SolarTracker
    from ...modules.tracking.transits.tracker import TransitTracker

    try:
        solar = await SolarTracker().update(current_user["id"])
        lunar = await LunarTracker().update(current_user["id"])
        transits = await TransitTracker().update(current_user["id"])

        return {"solar": solar, "lunar": lunar, "transits": transits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{condition_type}")
async def get_telemetry_history(
    condition_type: str, hours: int = 24, current_user: Annotated[dict, Depends(get_current_user)] = None
):
    """Get historical telemetry data for graphs."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from ...core.db.database import async_get_db
    from ...models.cosmic_conditions import CosmicConditions

    if condition_type not in ["solar", "lunar", "planetary"]:
        raise HTTPException(status_code=400, detail="Invalid condition type")

    cutoff = datetime.now(UTC) - timedelta(hours=hours)

    async for db in async_get_db():
        result = await db.execute(
            select(CosmicConditions)
            .where(CosmicConditions.condition_type == condition_type)
            .where(CosmicConditions.timestamp >= cutoff)
            .order_by(CosmicConditions.timestamp.asc())
        )
        records = result.scalars().all()

        return [{"timestamp": r.timestamp.isoformat(), "data": r.data} for r in records]


@router.get("/upcoming")
async def get_upcoming_events(
    days: int = 7,
    current_user: Annotated[dict, Depends(get_current_user)] = None
):
    """
    Get upcoming cosmic events for the specified time window.

    Calculates upcoming:
    - Void of Course Moon periods
    - Lunar phases (New/Full Moon)
    - Planetary ingresses (sign changes)
    - Retrograde stations
    - Exact transits to natal chart

    Returns events sorted by date with countdown timers.
    """
    from datetime import UTC, datetime

    from ...modules.tracking.upcoming import calculate_upcoming_events

    try:
        user_id = current_user["id"]
        events = await calculate_upcoming_events(user_id, days=days)
        return {
            "events": events,
            "generated_at": datetime.now(UTC).isoformat(),
            "window_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
