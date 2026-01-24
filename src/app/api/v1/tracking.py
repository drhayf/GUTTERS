# src/app/api/v1/tracking.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/tracking", tags=["tracking"])

@router.get("/solar")
async def get_solar_tracking(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get current solar weather data."""
    from ...modules.tracking.solar.tracker import SolarTracker
    
    tracker = SolarTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lunar")
async def get_lunar_tracking(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get current lunar phase and position."""
    from ...modules.tracking.lunar.tracker import LunarTracker
    
    tracker = LunarTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transits")
async def get_transit_tracking(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get current planetary transits vs natal chart."""
    from ...modules.tracking.transits.tracker import TransitTracker
    
    tracker = TransitTracker()
    try:
        result = await tracker.update(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
async def get_all_tracking(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get all tracking data (solar, lunar, transits)."""
    from ...modules.tracking.solar.tracker import SolarTracker
    from ...modules.tracking.lunar.tracker import LunarTracker
    from ...modules.tracking.transits.tracker import TransitTracker
    
    try:
        solar = await SolarTracker().update(current_user["id"])
        lunar = await LunarTracker().update(current_user["id"])
        transits = await TransitTracker().update(current_user["id"])
        
        return {
            "solar": solar,
            "lunar": lunar,
            "transits": transits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
