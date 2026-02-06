"""
GUTTERS Cardology Module (NODE)

Wraps the Chronos-Magi Kernel in a proper BaseModule for GUTTERS integration.
This module is STATELESS - all calculations derive from birth date + target date.

The kernel itself is a sealed engine block. This wrapper:
1. Exposes calculate_profile() for onboarding/profile calculation
2. Provides contribute_to_synthesis() for master synthesis
3. Formats data for UserProfile.data["cardology"] storage
"""

from datetime import date
from typing import Any, Dict, Optional

from src.app.modules.base import BaseModule

# Import the sealed kernel
from . import kernel


class CardologyModule(BaseModule):
    """
    Cardology Module (NODE) - The Magi OS Time Engine.

    Provides deterministic temporal mapping based on the 52-card calendar.
    No external dependencies, pure mathematical calculations.
    """

    # Module metadata (no manifest.json needed - pure logic module)
    name: str = "cardology"
    layer: str = "intelligence"
    version: str = "1.0.0"
    description: str = "Deterministic Time-Mapping Engine (Order of the Magi)"

    def __init__(self):
        """Initialize without manifest (pure logic module)."""
        # Don't call super().__init__() with manifest loading
        # This module has no manifest.json - it's pure computation
        self.initialized = False
        self.manifest: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "layer": self.layer,
            "description": self.description,
            "dependencies": [],
            "subscriptions": [],
        }
        self.config: dict[str, Any] = {}

        # Get event bus reference (but we don't subscribe to anything)
        from src.app.core.events.bus import get_event_bus
        self.event_bus = get_event_bus()

    def calculate_profile(
        self,
        birth_date: date,
        target_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete Cardology profile for a birth date.

        This is the main entry point for profile calculation.

        Args:
            birth_date: User's date of birth
            target_year: Year to calculate planetary periods for (default: current year)

        Returns:
            Dictionary suitable for storage in UserProfile.data["cardology"]
        """
        if target_year is None:
            target_year = date.today().year

        # Generate the complete blueprint using the sealed kernel
        blueprint = kernel.generate_blueprint(birth_date, include_year=target_year)

        # Format for UserProfile storage
        return self._format_profile_data(blueprint)

    def get_current_period(
        self,
        birth_date: date,
        current_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get the current planetary period for dashboard/quest integration.

        Args:
            birth_date: User's date of birth
            current_date: Date to check (default: today)

        Returns:
            Period info dict with card, planet, theme, guidance
        """
        return kernel.get_current_period_info(birth_date, current_date)

    def get_yearly_timeline(
        self,
        birth_date: date,
        year: int
    ) -> list[Dict[str, Any]]:
        """
        Get complete timeline of 52-day periods for a year.

        Args:
            birth_date: User's date of birth
            year: Year to generate timeline for

        Returns:
            List of period dictionaries
        """
        return kernel.generate_yearly_timeline(birth_date, year)

    def analyze_relationship(
        self,
        birth_date_a: date,
        birth_date_b: date
    ) -> Dict[str, Any]:
        """
        Analyze relationship connections between two birth dates.

        Args:
            birth_date_a: First person's birth date
            birth_date_b: Second person's birth date

        Returns:
            Connection analysis with planetary relationships
        """
        card_a = kernel.calculate_birth_card_from_date(birth_date_a)
        card_b = kernel.calculate_birth_card_from_date(birth_date_b)

        connections = kernel.analyze_connections(card_a, card_b)

        return {
            "person_a": {
                "birth_date": birth_date_a.isoformat(),
                "birth_card": str(card_a),
                "birth_card_repr": repr(card_a),
            },
            "person_b": {
                "birth_date": birth_date_b.isoformat(),
                "birth_card": str(card_b),
                "birth_card_repr": repr(card_b),
            },
            "connections": [
                {
                    "type": c.connection_type,
                    "planet": c.planet.value if c.planet else None,
                    "spread": c.spread_type,
                    "is_mutual": c.is_mutual,
                    "description": c.description,
                }
                for c in connections
            ],
            "connection_count": len(connections),
            "mutual_connections": sum(1 for c in connections if c.is_mutual),
        }

    def _format_profile_data(self, blueprint: kernel.CardologyBlueprint) -> Dict[str, Any]:
        """
        Format CardologyBlueprint for UserProfile.data storage.

        Converts dataclasses/enums to JSON-serializable dict.
        """
        return {
            "birth_card": {
                "card": str(blueprint.birth_card),
                "repr": repr(blueprint.birth_card),
                "rank": blueprint.birth_card.rank,
                "suit": blueprint.birth_card.suit.name,
                "suit_symbol": blueprint.birth_card.suit.value,
                "solar_value": blueprint.birth_card.solar_value,
            },
            "planetary_ruling_card": {
                "card": str(blueprint.planetary_ruling_card),
                "repr": repr(blueprint.planetary_ruling_card),
            } if blueprint.planetary_ruling_card else None,
            "zodiac_sign": blueprint.zodiac_sign.value,
            "karma_cards": {
                "first": {
                    "card": str(blueprint.first_karma_card),
                    "repr": repr(blueprint.first_karma_card),
                    "description": "Karmic debt - energy you must master",
                } if blueprint.first_karma_card else None,
                "second": {
                    "card": str(blueprint.second_karma_card),
                    "repr": repr(blueprint.second_karma_card),
                    "description": "Karmic gift - energy that comes naturally",
                } if blueprint.second_karma_card else None,
            },
            "is_fixed_card": blueprint.is_fixed_card,
            "is_semi_fixed": blueprint.is_semi_fixed,
            "semi_fixed_twin": {
                "card": str(blueprint.semi_fixed_twin),
                "repr": repr(blueprint.semi_fixed_twin),
            } if blueprint.semi_fixed_twin else None,
            "life_spread_position": {
                "row": blueprint.life_spread_row,
                "col": blueprint.life_spread_col,
                "row_planet": blueprint.life_row_planet.value if blueprint.life_row_planet else None,
                "col_planet": blueprint.life_col_planet.value if blueprint.life_col_planet else None,
            },
            "spirit_spread_position": {
                "row": blueprint.spirit_spread_row,
                "col": blueprint.spirit_spread_col,
                "row_planet": blueprint.spirit_row_planet.value if blueprint.spirit_row_planet else None,
                "col_planet": blueprint.spirit_col_planet.value if blueprint.spirit_col_planet else None,
            },
            "life_path_spread": {
                position: {
                    "card": str(card),
                    "repr": repr(card),
                } if card else None
                for position, card in blueprint.life_path_spread.items()
            },
            "current_year_periods": [
                {
                    "planet": period.planet.value,
                    "start_date": period.start_date.isoformat(),
                    "end_date": period.end_date.isoformat(),
                    "duration_days": period.duration_days,
                    "direct_card": {
                        "card": str(period.direct_card),
                        "repr": repr(period.direct_card),
                    } if period.direct_card else None,
                }
                for period in blueprint.planetary_periods
            ],
            "calculated_at": date.today().isoformat(),
        }

    async def contribute_to_synthesis(self, user_id: str) -> dict[str, Any]:
        """
        Provide Cardology data for master synthesis.

        NOTE: This requires user's birth_date to be fetched from DB.
        For now, returns placeholder structure.
        """
        # In full integration, we would:
        # 1. Fetch user's birth_date from User model
        # 2. Calculate profile
        # 3. Return formatted data

        return {
            "module": self.name,
            "layer": self.layer,
            "data": {
                "note": "Cardology synthesis requires birth_date context"
            },
            "insights": [],
            "metadata": {
                "version": self.version
            }
        }

    async def handle_event(self, packet: Any) -> None:
        """
        Handle events (not used - Cardology is pull-based, not event-driven).
        """
        pass


# Module instance for registration
module = CardologyModule()
