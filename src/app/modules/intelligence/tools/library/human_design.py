from datetime import date, time
from typing import Optional, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator


class HumanDesignInput(BaseModel):
    """Input parameters for calculating a Human Design chart."""

    name: str = Field(..., description="Name of the person")
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: Optional[str] = Field(
        None, description="Birth time in HH:MM format (24h). Optional (noon is used if unknown)."
    )
    latitude: float = Field(..., description="Birth location latitude")
    longitude: float = Field(..., description="Birth location longitude")
    timezone: str = Field(..., description="IANA timezone string (e.g., 'America/New_York')")


async def _calculate_hd_async(
    name: str, birth_date: str, latitude: float, longitude: float, timezone: str, birth_time: Optional[str] = None
) -> dict[str, Any]:
    """
    Calculate a Human Design chart including Type, Profile, Authority, and Channels.
    """
    calculator = HumanDesignCalculator()

    b_date = date.fromisoformat(birth_date)
    b_time = None
    if birth_time:
        parts = birth_time.split(":")
        b_time = time(int(parts[0]), int(parts[1]))

    return await calculator.calculate(
        name=name, birth_date=b_date, birth_time=b_time, latitude=latitude, longitude=longitude, timezone=timezone
    )


def get_tool() -> StructuredTool:
    """Return the Human Design calculation tool."""
    return StructuredTool.from_function(
        func=None,
        coroutine=_calculate_hd_async,
        name="calculate_human_design",
        description="Calculate a Human Design chart. Returns Type, Strategy, Authority, Profile, and defined centers. Use this when the user asks for their Human Design, BodyGraph, or type.",
        args_schema=HumanDesignInput,
    )
