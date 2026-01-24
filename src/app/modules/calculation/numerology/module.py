"""
GUTTERS Numerology Module - NODE

Event-driven module for numerology calculation and interpretation.
Subscribes to USER_BIRTH_DATA_UPDATED events and calculates numerology charts.

NOTE: Numerology doesn't require birth time - only birth date and name.
"""

from datetime import datetime, UTC
from typing import Any

from ....core.events.bus import get_event_bus
from ....protocol import MODULE_PROFILE_CALCULATED, USER_BIRTH_DATA_UPDATED
from ....protocol.packet import Packet
from ...base import BaseModule

from .brain.calculator import NumerologyCalculator
from .brain.interpreter import NumerologyInterpreter
from .schemas import NumerologyChart


class NumerologyModule(BaseModule):
    """Numerology calculation and interpretation module"""

    def __init__(self):
        # Let BaseModule auto-detect manifest.json in this directory
        super().__init__()

        self.calculator = NumerologyCalculator()

        # LLM is optional - will use basic interpretation if not available
        self.llm = None
        try:
            from ....core.ai.llm_factory import get_llm

            self.llm = get_llm(
                self.manifest["llm_config"]["model"], temperature=self.manifest["llm_config"]["temperature"]
            )
        except Exception:
            pass

        self.interpreter = NumerologyInterpreter(self.llm)

    async def contribute_to_synthesis(self, user_id: str) -> dict[str, Any]:
        """
        Provide Numerology data for master synthesis.

        Args:
            user_id: User UUID to get profile for

        Returns:
            Dict with numerology chart data and key insights
        """
        return {
            "module": self.name,
            "layer": self.layer,
            "data": {},  # Numerology chart data
            "insights": [],  # Key numerology insights
            "metadata": {
                "version": self.version,
            },
        }

    async def handle_event(self, packet: Packet) -> None:
        """
        Handle incoming events.

        Args:
            packet: Event packet with birth data
        """
        if packet.event_type == USER_BIRTH_DATA_UPDATED:
            await self._handle_birth_data_updated(packet)

    async def _handle_birth_data_updated(self, packet: Packet) -> dict[str, Any]:
        """Calculate numerology chart when birth data submitted"""

        # Extract birth data from payload
        payload = packet.payload
        user_id = packet.user_id

        if not payload or not user_id:
            return {}

        # Calculate chart (doesn't need birth time)
        chart = self.calculator.calculate_chart(
            name=payload.get("name", "Unknown"),
            birth_date=payload.get("birth_date"),
        )

        # Interpret chart
        insights = await self.interpreter.interpret_chart(chart)

        # Prepare profile data for storage
        profile_data = {
            "chart": chart.model_dump(),
            "insights": insights,
            "calculated_at": datetime.now(UTC).isoformat(),
        }

        print(f"[Numerology] Chart calculated: LP={chart.life_path}, Exp={chart.expression}")

        # Publish result to event bus
        event_bus = get_event_bus()
        await event_bus.publish(
            event_type=MODULE_PROFILE_CALCULATED,
            payload={
                "module_name": self.name,
                "user_id": str(user_id),
                "profile_data": profile_data,
            },
            source=self.name,
            user_id=str(user_id),
        )

        return profile_data


# Module instance for registration
module = NumerologyModule()
