# src/app/modules/tracking/transits/tracker.py

from datetime import UTC, datetime
from typing import List, Optional

import swisseph as swe

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
        now = datetime.now(UTC)
        jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)

        positions = {}
        for planet_id, planet_name in self.PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            longitude = result[0][0]
            speed = result[0][3]  # Longitudinal velocity

            positions[planet_name] = {
                "longitude": longitude,
                "sign": self._longitude_to_sign(longitude),
                "degree": longitude % 30,
                "speed": speed,
                "is_retrograde": speed < 0,
            }

        return TrackingData(timestamp=now, source="Swiss Ephemeris", data={"positions": positions})

    async def compare_to_natal(self, user_id: int, current_data: TrackingData) -> dict:
        """Compare current positions to natal chart."""
        # Get natal chart
        from src.app.core.memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        astrology_data = await memory.get_module_output(user_id, "astrology")
        if not astrology_data:
            return {"note": "Natal chart not available"}

        # Find transits (current planets aspecting natal planets)
        transits = []
        current_positions = current_data.data["positions"]

        natal_points = []
        if "planets" in astrology_data:
            natal_points = astrology_data["planets"]
        elif isinstance(astrology_data, list):
            natal_points = astrology_data

        natal_houses = astrology_data.get("houses", []) if isinstance(astrology_data, dict) else []

        for transit_planet, transit_data in current_positions.items():
            for natal_planet_entry in natal_points:
                # Handle both dict and object (if already parsed)
                if isinstance(natal_planet_entry, dict):
                    natal_planet_name = natal_planet_entry.get("name", "")
                    natal_data = natal_planet_entry
                else:
                    natal_planet_name = getattr(natal_planet_entry, "name", "")
                    natal_data = natal_planet_entry

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

                natal_longitude = 0.0
                # Try to find absolute longitude or calculate it
                if isinstance(natal_data, dict):
                    if "absolute_degree" in natal_data:
                        natal_longitude = natal_data["absolute_degree"]
                    elif "sign" in natal_data and "degree" in natal_data:
                        natal_longitude = self._sign_to_longitude(natal_data["sign"]) + natal_data["degree"]
                    else:
                        continue
                else:
                    abs_deg = getattr(natal_data, "absolute_degree", None)
                    if abs_deg is not None:
                        natal_longitude = abs_deg
                    else:
                        sgn = getattr(natal_data, "sign", None)
                        deg = getattr(natal_data, "degree", None)
                        if sgn and deg is not None:
                            natal_longitude = self._sign_to_longitude(sgn) + deg
                        else:
                            continue

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
                            "applying": self._is_applying(
                                transit_data["longitude"], natal_longitude, transit_data["speed"], aspect["angle"]
                            ),
                        }
                    )

            # Check House Placement
            if natal_houses:
                house_num = self._calculate_house_placement(transit_longitude, natal_houses)
                if house_num:
                    transit_data["current_house"] = house_num

        # Sort by exactness (closest orb first)
        transits.sort(key=lambda t: t["orb"])

        return {
            "total_transits": len(transits),
            "exact_transits": [t for t in transits if t["exact"]],
            "applying_transits": transits[:5],  # Top 5 closest
            "current_positions": current_positions,
        }

    def detect_significant_events(
        self,
        current_data: TrackingData,
        previous_data: Optional[TrackingData],
        comparison: Optional[dict] = None,
    ) -> List[str]:
        """Detect when transits become exact (within 1 degree)."""
        events = []

        if comparison and comparison.get("exact_transits"):
            for transit in comparison["exact_transits"]:
                transit_planet = transit["transit_planet"]
                natal_planet = transit["natal_planet"]
                aspect = transit["aspect"]

                # Professional, user-facing string for Evolution HUD
                label = f"Cosmic Witness: Transit {transit_planet} {aspect} Natal {natal_planet}"
                events.append(label)

        # Retrograde Stations
        current_pos = current_data.data.get("positions", {})
        previous_pos = previous_data.data.get("positions", {}) if previous_data else {}

        for planet, data in current_pos.items():
            if planet in ["Sun", "Moon"]:
                continue

            is_rx = data.get("is_retrograde", False)
            was_rx = previous_pos.get(planet, {}).get("is_retrograde", False)

            if is_rx and not was_rx:
                events.append(f"Cosmic Witness: {planet} Stations Retrograde")
            elif not is_rx and was_rx:
                events.append(f"Cosmic Witness: {planet} Stations Direct")

        return events

    def _is_applying(self, t_lon: float, n_lon: float, t_speed: float, aspect_angle: float) -> bool:
        """
        Check if aspect is applying (getting closer).
        """
        # Calculate current diff
        diff_now = abs(t_lon - n_lon)
        if diff_now > 180:
            diff_now = 360 - diff_now
        orb_now = abs(diff_now - aspect_angle)

        # Calculate future diff (1 hour from now)
        # speed is degrees/day. 1 hour = speed/24
        t_lon_future = (t_lon + t_speed / 24.0) % 360
        diff_future = abs(t_lon_future - n_lon)
        if diff_future > 180:
            diff_future = 360 - diff_future
        orb_future = abs(diff_future - aspect_angle)

        return orb_future < orb_now

    def _calculate_house_placement(self, lon: float, houses: list) -> Optional[int]:
        """
        Determine which house a longitude falls into.
        Expects houses list of dicts: [{'house': 1, 'degree': ...}, ...] or objects.
        """
        # Simplified for common format (list of 1-12)
        # This requires robust House handling which depends on 'astrology' module output format.
        # Assuming simple list first.
        # If houses missing, returns None.
        return None  # Placeholder until House System strict definition confirmed
        # (Safer to disable than error out on robust formatting)

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
