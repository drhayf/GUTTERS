"""
GUTTERS Birth Data API

Endpoints for submitting birth data and triggering cosmic profile calculations.
"""
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...core.events.bus import get_event_bus
from ...core.exceptions.http_exceptions import NotFoundException
from ...core.utils.geocoding import geocode_location
from ...crud.crud_users import crud_users
from ...protocol import USER_BIRTH_DATA_UPDATED
from ...schemas.profile import BirthDataComplete, BirthDataInput, UserProfileRead

router = APIRouter(prefix="/birth-data", tags=["birth-data"])


@router.post("/submit")
async def submit_birth_data(
    request: Request,
    birth_data: BirthDataInput,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    """
    Submit birth data and trigger cosmic profile calculations.

    This endpoint:
    1. Geocodes the birth location to get coordinates and timezone
    2. Updates the user's birth data in the database
    3. Publishes USER_BIRTH_DATA_UPDATED event
    4. All subscribed modules (astrology, numerology, etc.) will calculate profiles

    Args:
        birth_data: Birth data input (name, date, time, location)

    Returns:
        {
            "status": "processing",
            "trace_id": "uuid",
            "message": "Birth data submitted, profile calculation in progress"
        }
    """
    user_id = current_user["id"]
    username = current_user["username"]

    # Geocode the birth location
    geocode_result = geocode_location(birth_data.birth_location)

    if geocode_result is None:
        return {
            "status": "error",
            "message": f"Could not geocode location: {birth_data.birth_location}"
        }

    # Create complete birth data with coordinates
    birth_data_complete = BirthDataComplete(
        name=birth_data.name,
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        birth_location=birth_data.birth_location,
        timezone=birth_data.timezone,
        birth_latitude=geocode_result["latitude"],
        birth_longitude=geocode_result["longitude"],
        birth_timezone=geocode_result["timezone"],
        birth_location_formatted=geocode_result["address"],
    )

    # Update user with birth data
    update_data = {
        "birth_date": birth_data_complete.birth_date,
        "birth_time": birth_data_complete.birth_time,
        "birth_location": birth_data_complete.birth_location_formatted,
        "birth_latitude": birth_data_complete.birth_latitude,
        "birth_longitude": birth_data_complete.birth_longitude,
        "birth_timezone": birth_data_complete.birth_timezone,
    }

    await crud_users.update(db=db, object=update_data, username=username)

    # Generate trace ID for tracking
    trace_id = str(uuid4())

    # Publish event to trigger module calculations
    event_bus = get_event_bus()
    await event_bus.publish(
        event_type=USER_BIRTH_DATA_UPDATED,
        payload={
            "user_id": user_id,
            "name": birth_data_complete.name,
            "birth_date": str(birth_data_complete.birth_date),
            "birth_time": str(birth_data_complete.birth_time) if birth_data_complete.birth_time else None,
            "birth_location": birth_data_complete.birth_location_formatted,
            "birth_latitude": birth_data_complete.birth_latitude,
            "birth_longitude": birth_data_complete.birth_longitude,
            "birth_timezone": birth_data_complete.birth_timezone,
        },
        source="api.birth_data",
        user_id=str(user_id),
    )

    # Genesis auto-start: Check for uncertainties if no birth time provided
    genesis_session = None
    if birth_data_complete.birth_time is None:
        try:
            import asyncio
            # Brief wait for modules to calculate
            await asyncio.sleep(1)

            from ...modules.intelligence.genesis.engine import get_genesis_engine
            from ...modules.intelligence.genesis.session import get_session_manager
            from ...modules.intelligence.genesis.uncertainty import UncertaintyDeclaration, UncertaintyField

            # Create uncertainty declaration for missing birth time
            declaration = UncertaintyDeclaration(
                module="astrology",
                user_id=user_id,
                session_id=trace_id,
                source_accuracy="probabilistic",
                fields=[
                    UncertaintyField(
                        field="rising_sign",
                        module="astrology",
                        candidates=dict.fromkeys(
                            [
                                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
                            ],
                            1 / 12
                        ),
                        confidence_threshold=0.80,
                        refinement_strategies=["morning_routine", "first_impression"],
                    )
                ],
            )

            engine = get_genesis_engine()
            hypotheses = await engine.initialize_from_uncertainties([declaration])

            if hypotheses:
                manager = get_session_manager()
                session = await manager.create_session(
                    user_id=user_id,
                    hypothesis_ids=[h.id for h in hypotheses]
                )
                first_probe = await manager.get_next_probe(session, engine)

                genesis_session = {
                    "session_id": session.session_id,
                    "message": "We'd like to ask a few questions to refine your profile.",
                    "hypotheses_count": len(hypotheses),
                    "fields_to_refine": list({h.field for h in hypotheses}),
                    "first_probe": first_probe.model_dump() if first_probe else None,
                }
        except Exception:
            # Genesis failure shouldn't block birth data submission
            pass

    return {
        "status": "processing",
        "trace_id": trace_id,
        "message": "Birth data submitted, profile calculation in progress",
        "geocoded_location": birth_data_complete.birth_location_formatted,
        "genesis_session": genesis_session,
    }


@router.get("/profile", response_model=UserProfileRead)
async def get_profile(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    """
    Get the current user's cosmic profile.

    Returns all calculated module profiles (astrology, numerology, etc.).
    Profile is populated after submitting birth data.

    Returns:
        UserProfileRead with all module data in the 'data' field
    """
    from ...crud.crud_user_profile import crud_user_profiles

    user_id = current_user["id"]

    profile = await crud_user_profiles.get(db=db, user_id=user_id)

    if profile is None:
        raise NotFoundException("Profile not found. Submit birth data first.")

    return profile


@router.get("/me")
async def get_birth_data(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get the current user's birth data.

    Returns:
        User's birth data fields
    """
    return {
        "name": current_user.get("name"),
        "birth_date": current_user.get("birth_date"),
        "birth_time": current_user.get("birth_time"),
        "birth_location": current_user.get("birth_location"),
        "birth_latitude": current_user.get("birth_latitude"),
        "birth_longitude": current_user.get("birth_longitude"),
        "birth_timezone": current_user.get("birth_timezone"),
    }
