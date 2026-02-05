from datetime import date, time
from typing import Optional, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.app.modules.calculation.astrology.brain.calculator import AstrologyCalculator


class AstrologyInput(BaseModel):
    """Input parameters for calculating an astrology chart."""

    name: str = Field(..., description="Name of the person")
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: Optional[str] = Field(
        None, description="Birth time in HH:MM format (24h). Optional (noon is used if unknown)."
    )
    latitude: float = Field(..., description="Birth location latitude")
    longitude: float = Field(..., description="Birth location longitude")
    timezone: str = Field(..., description="IANA timezone string (e.g., 'America/New_York')")


def _calculate_astrology(
    name: str, birth_date: str, latitude: float, longitude: float, timezone: str, birth_time: Optional[str] = None
) -> dict[str, Any]:
    """
    Calculate a natal astrology chart including planetary positions, houses, and aspects.
    """
    raise NotImplementedError("This tool must be called asynchronously.")


async def _calculate_astrology_async(
    name: str, birth_date: str, latitude: float, longitude: float, timezone: str, birth_time: Optional[str] = None
) -> dict[str, Any]:
    """
    Calculate a natal astrology chart including planetary positions, houses, and aspects.
    """
    calculator = AstrologyCalculator()

    b_date = date.fromisoformat(birth_date)
    b_time = None
    if birth_time:
        parts = birth_time.split(":")
        b_time = time(int(parts[0]), int(parts[1]))

    return await calculator.calculate(
        name=name, birth_date=b_date, birth_time=b_time, latitude=latitude, longitude=longitude, timezone=timezone
    )


def get_tool() -> StructuredTool:
    """Return the Astrology calculation tool."""
    return StructuredTool.from_function(
        func=None,  # We don't provide a sync implementation
        coroutine=_calculate_astrology_async,
        name="calculate_astrology_chart",
        description="Calculate a natal astrology chart. Returns planets, houses, and aspects. Use this when the user asks for their chart, positions, or specific astrological details.",
        args_schema=AstrologyInput,
    )
