# src/app/modules/tracking/transits/tracker.py

import swisseph as swe
from datetime import datetime, UTC
from typing import Optional, List, Dict
import math

from ..base import BaseTrackingModule, TrackingData


class TransitTracker(BaseTrackingModule):
    """
    Tracks planetary transits against natal chart.

    Data source: Swiss Ephemeris (same as natal charts)

    Monitors:
    - Current planet positions
    - Major transits (conjunctions, oppositions, squares)
    - Exactness of transits (within 1-degree orb)
    """

    module_name = "transit_tracking"
    update_frequency = "daily"

    PLANETS = {
        swe.SUN: "Sun",
        swe.MOON: "Moon",
        swe.MERCURY: "Mercury",
        swe.VENUS: "Venus",
        swe.MARS: "Mars",
        swe.JUPITER: "Jupiter",
        swe.SATURN: "Saturn",
        swe.URANUS: "Uranus",
        swe.NEPTUNE: "Neptune",
        swe.PLUTO: "Pluto",
    }

    MAJOR_ASPECTS = {
        "conjunction": (0, 8),  # 0° ± 8° orb
        "opposition": (180, 8),  # 180° ± 8°
        "square": (90, 6),  # 90° ± 6°
        "trine": (120, 6),  # 120° ± 6°
        "sextile": (60, 4),  # 60° ± 4°
    }

    async def fetch_current_data(self) -> TrackingData:
        """Calculate current planetary positions."""
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)

        positions = {}
        for planet_id, planet_name in self.PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            longitude = result[0][0]
            positions[planet_name] = {
                "longitude": longitude,
                "sign": self._longitude_to_sign(longitude),
                "degree": longitude % 30,
            }

        return TrackingData(timestamp=now, source="Swiss Ephemeris", data={"positions": positions})

    async def compare_to_natal(self, user_id: int, current_data: TrackingData) -> dict:
        """Compare current positions to natal chart."""
        # Get natal chart
        from app.core.memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        astrology_data = await memory.get_module_output(user_id, "astrology")
        if not astrology_data:
            return {"note": "Natal chart not available"}

        # Find transits (current planets aspecting natal planets)
        transits = []
        current_positions = current_data.data["positions"]

        natal_points = {}
        if "planets" in astrology_data:
            natal_points = astrology_data["planets"]
        elif "sun" in astrology_data:  # old structure?
            natal_points = astrology_data

        for transit_planet, transit_data in current_positions.items():
            for natal_planet_name, natal_data in natal_points.items():
                # Filter only major planets
                if natal_planet_name.lower() not in [
                    "sun",
                    "moon",
                    "mercury",
                    "venus",
                    "mars",
                    "jupiter",
                    "saturn",
                    "uranus",
                    "neptune",
                    "pluto",
                ]:
                    continue

                if not isinstance(natal_data, dict):
                    continue

                natal_longitude = 0.0
                # Try to find absolute longitude or calculate it
                if "absolute_degree" in natal_data:
                    natal_longitude = natal_data["absolute_degree"]
                elif "sign" in natal_data and "degree" in natal_data:
                    natal_longitude = self._sign_to_longitude(natal_data["sign"]) + natal_data["degree"]
                else:
                    continue  # Can't calculate aspect without position

                transit_longitude = transit_data["longitude"]

                # Check aspects
                aspect = self._calculate_aspect(transit_longitude, natal_longitude)
                if aspect:
                    transits.append(
                        {
                            "transit_planet": transit_planet,
                            "natal_planet": natal_planet_name.title(),
                            "aspect": aspect["name"],
                            "orb": aspect["orb"],
                            "exact": aspect["orb"] < 1,  # Within 1 degree = exact
                            "interpretation": self._interpret_transit(
                                transit_planet, natal_planet_name.title(), aspect["name"]
                            ),
                        }
                    )

        # Sort by exactness (closest orb first)
        transits.sort(key=lambda t: t["orb"])

        return {
            "total_transits": len(transits),
            "exact_transits": [t for t in transits if t["exact"]],
            "applying_transits": transits[:5],  # Top 5 closest
            "current_positions": current_positions,
        }

    def detect_significant_events(self, current_data: TrackingData, previous_data: Optional[TrackingData]) -> List[str]:
        """Detect when transits become exact."""
        # Event detection for transits is tricky because 'exact' depends on natal chart.
        # This global detect logic runs WITHOUT user_id (it compares global state).
        # However, BaseTrackingModule.update() passes user_id to compare_to_natal(),
        # but detect_significant_events() only takes current/previous data.

        # Refactoring approach:
        # Since transits are personal, significant events are personal.
        # But 'detect_significant_events' in base module is designed around data changes (like solar storm).
        # For personal transits, we might need to rely on 'compare_to_natal' result or
        # change the architecture to allow personal event detection.

        # IMPORTANT: The BaseTrackingModule.update() calls detect_significant_events(current, previous).
        # It does NOT pass user_id. This is a limit of the requested architecture for personal events.
        # However, update() DOES call compare_to_natal().
        # We can return events from compare_to_natal? No, base class doesn't support that.

        # Hack/Workaround:
        # Since 'update()' is called PER USER in the background job (see functions.py logic),
        # we can't easily detect "my transit is exact" inside the global data fetch.
        # BUT 'update()' fetches data once? No, 'update(user_id)' logic:
        # 1. Check cache for *data* (shared?)
        # BaseTrackingModule.update() caches data by user_id?
        # `last_update_key = f"tracking:{self.module_name}:last_update_timestamp:{user_id}"`
        # Yes! The caching is per-user!
        # So `current_data` is unique to user?
        # NO. `fetch_current_data()` returns global cosmic data (TrackingData).
        # It does not take user_id.

        # So `previous_data` in `detect_significant_events(current, previous)` is global previous data.
        # This works for Solar (storm is global) and Lunar (phase is global).
        # It DOES NOT work for Transits (exact transit is personal).

        # Unless... we detect "Transit of Saturn to 15 deg Leo" as a global event?
        # No, that's too granular.

        # User requested: "When transit becomes exact -> synthesis triggered automatically"
        # Since the architecture provided separates global data (fetch) from personal (compare),
        # and trigger logic is based on `detect_significant_events` (global)...
        # We have a design flaw in the requested architecture for personal transit triggers.

        # However, I must follow the requested architecture.
        # Use case: "When transit becomes exact -> synthesis triggered"
        # I will leave this empty for now as strictly instructed by the user's implementation plan which said:
        # "For now, return empty (significant events detected in compare_to_natal)"
        # AND "Synthesis triggers work... When transit becomes exact -> synthesis triggered automatically" is a success criteria.

        # If I want to trigger synthesis for personal transits, I should do it in `compare_to_natal`?
        # But `base.py` only triggers if `events` is returned by `detect_significant_events`.

        # I will modify `base.py` locally or hook into it? No, keep base.py generic.
        # Wait, the user's base.py code:
        # events = self.detect_significant_events(current, previous)
        # comparison = await self.compare_to_natal(user_id, current)

        # I'll stick to the user's plan.

        return []

    def _calculate_aspect(self, transit_lon: float, natal_lon: float) -> Optional[dict]:
        """Calculate aspect between two planets."""
        diff = abs(transit_lon - natal_lon)
        if diff > 180:
            diff = 360 - diff

        for aspect_name, (angle, orb_val) in self.MAJOR_ASPECTS.items():
            if abs(diff - angle) <= orb_val:
                return {"name": aspect_name, "angle": angle, "orb": abs(diff - angle)}

        return None

    def _interpret_transit(self, transit_planet: str, natal_planet: str, aspect: str) -> str:
        """Generate interpretation of transit."""
        if aspect == "conjunction":
            return f"{transit_planet} energizes your natal {natal_planet}"
        if aspect == "opposition":
            return f"{transit_planet} challenges your natal {natal_planet}"
        if aspect == "square":
            return f"{transit_planet} creates tension with your natal {natal_planet}"
        if aspect == "trine":
            return f"{transit_planet} harmonizes with your natal {natal_planet}"
        if aspect == "sextile":
            return f"{transit_planet} offers opportunities through your natal {natal_planet}"
        return ""

    def _longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign."""
        signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        return signs[int(longitude / 30) % 12]

    def _sign_to_longitude(self, sign: str) -> float:
        """Convert sign to starting longitude."""
        signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        try:
            return signs.index(sign) * 30.0
        except ValueError:
            return 0.0
