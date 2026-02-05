"""
Profile API Endpoints

Handles profile creation, calculation, and retrieval for onboarding flow.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import date, time as time_type
import logging

from src.app.api.dependencies import get_current_user
from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.core.db.database import async_get_db
from src.app.modules.calculation.registry import CalculationModuleRegistry
from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class BirthDataRequest(BaseModel):
    """Birth data submission request."""

    birth_date: date
    birth_time: time_type | None = None
    birth_location: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str
    time_unknown: bool = False


class OnboardingStatusResponse(BaseModel):
    """Onboarding completion status."""

    onboarding_completed: bool
    has_birth_data: bool
    has_calculated_profile: bool
    has_synthesis: bool
    modules_calculated: list[str] = []


class CalculationProgressResponse(BaseModel):
    """Real-time calculation progress (for future streaming)."""

    status: str  # "pending", "calculating", "complete", "failed"
    current_module: str | None = None
    completed_modules: list[str] = []
    progress_percentage: int = Field(..., ge=0, le=100)
    message: str


class ModuleRegistryResponse(BaseModel):
    """Available calculation modules from registry."""

    modules: list[dict]
    total_modules: int
    total_weight: int
    has_birth_time: bool


class GeocodeRequest(BaseModel):
    """Geocoding request."""

    location: str


@router.post("/geocode")
async def geocode_location_endpoint(request: GeocodeRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Geocode a location string to coordinates and timezone.
    """
    from src.app.core.utils.geocoding import geocode_location_cached

    result = geocode_location_cached(request.location)

    if not result:
        raise HTTPException(status_code=404, detail="Location not found")

    address, lat, lng, tz = result

    return {"address": address, "latitude": lat, "longitude": lng, "timezone": tz}


class ProfilePreferencesRequest(BaseModel):
    """Request schema for updating user profile preferences."""

    notifications: dict[str, bool]


@router.patch("/preferences")
async def update_profile_preferences(
    request: ProfilePreferencesRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Update granular user preferences (e.g., notifications).
    Merges with existing preferences in JSONB.
    """
    user_id = current_user["id"]

    # Fetch Profile
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        # Should create if missing, or error? For safety, create empty.
        profile = UserProfile(user_id=user_id, data={})
        db.add(profile)

    # Update Data
    # 1. Get existing preferences or init
    current_data = dict(profile.data) if profile.data else {}
    prefs = current_data.get("preferences", {})

    # 2. Merge notifications
    current_notifs = prefs.get("notifications", {})
    current_notifs.update(request.notifications)

    # 3. Save back
    prefs["notifications"] = current_notifs
    current_data["preferences"] = prefs

    profile.data = current_data
    flag_modified(profile, "data")

    await db.commit()

    return {"message": "Preferences updated", "preferences": prefs}


@router.get("/preferences")
async def get_profile_preferences(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Get user profile preferences.
    """
    user_id = current_user["id"]
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile or not profile.data:
        # Return defaults (all true)
        return {
            "notifications": {"cosmic": True, "quests": True, "evolution": True, "intelligence": True, "journal": True}
        }

    prefs = profile.data.get("preferences", {}).get("notifications", {})
    return {"notifications": prefs}


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/modules", response_model=ModuleRegistryResponse)
async def get_available_modules(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get list of available calculation modules from registry.

    Frontend uses this to:
    - Build dynamic progress UI
    - Show module names during calculation
    - Calculate accurate progress percentages

    Response adapts based on whether user has birth time.
    """
    # Check if user has birth time
    # User dict from dependency has birth_time if it was loaded, but get_current_user returns basic info?
    # Actually get_current_user in dependencies.py returns the DB user dict (from row mapping or similar).
    # Logic: It accesses user['id'], user['username'].
    # If the dict includes all columns, we are good.
    # To be safe, we check 'birth_time' in dict, defaulting to None.
    has_birth_time = current_user.get("birth_time") is not None

    # Get registry metadata (automatically adapts to birth data)
    metadata = CalculationModuleRegistry.get_registry_metadata(has_birth_time)

    return metadata


@router.get("/onboarding-status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Check if user has completed onboarding.

    Frontend uses this on app load to decide:
    - Redirect to /onboarding if incomplete
    - Show dashboard if complete

    A user has completed onboarding if they have:
    1. Birth data submitted
    2. Profile calculated (at least one module)
    3. Synthesis generated
    """
    user_id = current_user["id"]

    # Get user's profile
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        return OnboardingStatusResponse(
            onboarding_completed=False,
            has_birth_data=False,
            has_calculated_profile=False,
            has_synthesis=False,
            modules_calculated=[],
        )

    # Check birth data
    # We should probably fetch the user from DB to be sure about birth data if the token is old.
    # But for now, we'll try to use the dictionary if available or fetch fresh.
    # Let's fetch fresh User to be strictly accurate about current state.
    result = await db.execute(select(User).where(User.id == user_id))
    user_model = result.scalar_one()

    has_birth_data = all([user_model.birth_date is not None, (user_model.birth_location is not None)])

    # Check calculated modules (discover from registry)
    registry_modules = CalculationModuleRegistry.get_all_modules()
    calculated_modules = []

    for module_name in registry_modules.keys():
        if (
            module_name in profile.data
            and isinstance(profile.data[module_name], dict)
            and "error" not in profile.data[module_name]
        ):
            calculated_modules.append(module_name)

    has_calculated = len(calculated_modules) > 0

    # Check synthesis
    has_synthesis = "onboarding_synthesis" in profile.data or "synthesis" in profile.data

    # Onboarding complete if all three conditions met
    onboarding_complete = has_birth_data and has_calculated and has_synthesis

    return OnboardingStatusResponse(
        onboarding_completed=onboarding_complete,
        has_birth_data=has_birth_data,
        has_calculated_profile=has_calculated,
        has_synthesis=has_synthesis,
        modules_calculated=calculated_modules,
    )


@router.post("/birth-data")
async def submit_birth_data(
    request: BirthDataRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Submit birth data for profile calculation.

    Updates User model with birth details.
    Does NOT trigger calculation (that happens via /calculate endpoint).

    This is intentionally separate from the event-driven flow to
    allow synchronous calculation during onboarding.
    """
    logger.info(f"Saving birth data for user {current_user['id']}")

    # Update user with birth data
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user_model = result.scalar_one()

    user_model.birth_date = request.birth_date
    user_model.birth_time = request.birth_time
    user_model.birth_location = request.birth_location
    user_model.birth_latitude = request.latitude
    user_model.birth_longitude = request.longitude
    user_model.birth_timezone = request.timezone

    await db.commit()

    logger.info(f"Birth data saved (time_unknown={request.time_unknown})")

    return {
        "success": True,
        "message": "Birth data saved successfully",
        "time_unknown": request.time_unknown,
        "modules_available": len(
            CalculationModuleRegistry.get_modules_for_birth_data(has_birth_time=not request.time_unknown)
        ),
    }


@router.post("/calculate")
async def calculate_profile(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Calculate profile using all registered modules.

    This is a SYNCHRONOUS operation (not background job) to provide
    real-time feedback during onboarding. Takes 15-30 seconds.

    Automatically discovers and runs all registered modules.
    Automatically includes all calculated modules in synthesis.

    Process:
    1. Verify birth data exists
    2. Run all enabled calculators via registry
    3. Store results in UserProfile.data
    4. Generate synthesis
    5. Cache synthesis in Active Memory
    """
    user_id = current_user["id"]
    logger.info(f"Starting profile calculation for user {user_id}")

    # Get profile
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    result = await db.execute(select(User).where(User.id == user_id))
    user_model = result.scalar_one()

    # Verify birth data exists
    if not user_model.birth_date:
        raise HTTPException(status_code=400, detail="Birth data required. Please submit birth data first.")

    if not profile:
        profile = UserProfile(user_id=user_id, data={})
        db.add(profile)

    # Determine if birth time is known
    has_birth_time = user_model.birth_time is not None

    # Run ALL registered calculators
    logger.info(f"Running calculators (has_birth_time={has_birth_time})")

    calculations = await CalculationModuleRegistry.calculate_all(
        user=user_model, db_session=db, has_birth_time=has_birth_time
    )

    # Store all results in profile
    modules_calculated = []
    modules_with_errors = []

    if profile.data is None:
        profile.data = {}

    # Use a dictionary copy to flag modification properly
    new_data = dict(profile.data)

    for module_name, result in calculations.items():
        if "error" not in result:
            new_data[module_name] = result
            modules_calculated.append(module_name)
            logger.info(f"Module {module_name} calculated successfully")
        else:
            new_data[module_name] = result
            modules_with_errors.append(module_name)
            logger.error(f"Module {module_name} failed: {result['error']}")

    profile.data = new_data
    flag_modified(profile, "data")
    await db.commit()

    logger.info(f"Calculated {len(modules_calculated)} modules, {len(modules_with_errors)} errors")

    # Generate synthesis (automatically includes all calculated modules)
    logger.info("Generating synthesis")

    synthesizer = ProfileSynthesizer()
    synthesis = await synthesizer.synthesize_profile(user_id, db)

    # Store synthesis in profile
    # synthesis is UnifiedProfile object
    profile.data["onboarding_synthesis"] = synthesis.model_dump(mode="json")
    flag_modified(profile, "data")
    await db.commit()

    logger.info("Synthesis generated and stored")

    return {
        "success": True,
        "message": "Profile calculated successfully",
        "modules_calculated": modules_calculated,
        "modules_with_errors": modules_with_errors,
        "synthesis_preview": synthesis.synthesis[:200] + "...",
        "confidence": synthesis.confidence,
    }


@router.get("/synthesis")
async def get_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get user's synthesis for manifesto display.

    Returns the complete synthesis text with metadata.
    """
    user_id = current_user["id"]
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one()

    # Try onboarding synthesis first, fall back to regular synthesis
    synthesis = profile.data.get("onboarding_synthesis") or profile.data.get("synthesis")

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found. Please calculate profile first.")

    return {
        "synthesis": synthesis.get("synthesis_text") or synthesis.get("synthesis", ""),
        "modules_included": synthesis.get("modules_included", []),
        "modules_count": synthesis.get("modules_count", 0),
        "confidence": synthesis.get("confidence", 0.0),
        "generated_at": synthesis.get("timestamp"),
    }


# ============================================================================
# CHRONOS/MAGI STATE ENDPOINTS (Phase 25-D)
# ============================================================================


class ChronosStateResponse(BaseModel):
    """Response schema for Chronos state endpoint."""
    
    birth_card: dict | None = None
    current_planet: str | None = None
    current_card: dict | None = None
    period_start: str | None = None
    period_end: str | None = None
    days_remaining: int | None = None
    days_elapsed: int | None = None
    period_total: int = 52
    progress_percent: float | None = None
    theme: str | None = None
    guidance: str | None = None
    planetary_ruling_card: dict | None = None
    year: int | None = None
    age: int | None = None
    karma_cards: dict | None = None
    cached_at: str | None = None


@router.get("/chronos", response_model=ChronosStateResponse)
async def get_chronos_state(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get user's current Chronos/MAGI state.
    
    Returns the current 52-day planetary period information including:
    - Birth card (core identity)
    - Current planet and period card
    - Period progress (days elapsed, remaining, percentage)
    - Theme and guidance text
    - Karma cards (debts and gifts)
    
    This data powers the TimelineScrubber and BirthCardWidget on the dashboard.
    """
    from src.app.core.state.chronos import get_chronos_manager
    from datetime import datetime, UTC
    
    user_id = current_user["id"]
    
    # Get user's birth date from profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.birth_date:
        raise HTTPException(
            status_code=400, 
            detail="Birth data required. Please complete onboarding first."
        )
    
    # Get chronos state from manager
    chronos = get_chronos_state_manager()
    state = await chronos.get_user_chronos(user_id, birth_date=profile.birth_date)
    
    if not state:
        # Calculate fresh if no cached state
        state = await chronos.refresh_user_chronos(user_id, profile.birth_date)
    
    # Calculate days elapsed and progress percentage
    days_remaining = state.get("days_remaining", 0)
    period_total = 52
    days_elapsed = period_total - days_remaining
    progress_percent = round((days_elapsed / period_total) * 100, 1)
    
    # Get karma cards from full profile data if available
    karma_cards = None
    if profile.data and profile.data.get("cardology"):
        cardology_data = profile.data["cardology"]
        if "karma_cards" in cardology_data:
            karma_cards = cardology_data["karma_cards"]
        elif "profile" in cardology_data:
            karma_cards = cardology_data["profile"].get("karma_cards")
    
    return ChronosStateResponse(
        birth_card=state.get("birth_card"),
        current_planet=state.get("current_planet"),
        current_card=state.get("current_card"),
        period_start=state.get("period_start"),
        period_end=state.get("period_end"),
        days_remaining=days_remaining,
        days_elapsed=days_elapsed,
        period_total=period_total,
        progress_percent=progress_percent,
        theme=state.get("theme"),
        guidance=state.get("guidance"),
        planetary_ruling_card=state.get("planetary_ruling_card"),
        year=state.get("year"),
        age=state.get("age"),
        karma_cards=karma_cards,
        cached_at=state.get("cached_at"),
    )