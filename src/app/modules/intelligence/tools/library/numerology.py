from datetime import date
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.app.modules.calculation.numerology.brain.calculator import NumerologyCalculator


class NumerologyInput(BaseModel):
    """Input parameters for calculating a Numerology chart."""

    name: str = Field(..., description="Full birth name of the person")
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")


async def _calculate_numerology_async(name: str, birth_date: str) -> dict[str, Any]:
    """
    Calculate a Numerology chart including Life Path, Expression, and Soul Urge numbers.
    """
    calculator = NumerologyCalculator()

    b_date = date.fromisoformat(birth_date)

    return await calculator.calculate(name=name, birth_date=b_date)


def get_tool() -> StructuredTool:
    """Return the Numerology calculation tool."""
    return StructuredTool.from_function(
        func=None,
        coroutine=_calculate_numerology_async,
        name="calculate_numerology",
        description=(
            "Calculate a Numerology chart. Returns Life Path, Expression, Soul Urge, "
            "and Personality numbers. Use this when the user asks for numerology "
            "readings or numbers."
        ),
        args_schema=NumerologyInput,
    )
