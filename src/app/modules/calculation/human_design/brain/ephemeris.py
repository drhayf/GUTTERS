"""
Human Design Ephemeris - Swiss Ephemeris Wrapper

Clean abstraction over Swiss Ephemeris library.
Handles all astronomical calculations for HD.

Key functions:
- Julian date conversion
- Design date calculation (88° solar arc)
- Planetary position calculations
- Gate/line derivation from longitude

Source: Integrates verified logic from dturkuler/humandesign_api (GPL-3.0)
"""
from datetime import datetime
from typing import Optional
import swisseph as swe

from . import constants


class EphemerisCalculator:
    """
    Swiss Ephemeris wrapper for Human Design calculations.
    
    Provides clean interface for astronomical calculations.
    """
    
    def __init__(self):
        """Initialize Swiss Ephemeris."""
        # Set ephemeris path if needed (uses built-in by default)
        pass
    
    def datetime_to_julian(
        self,
        dt: datetime,
        tz_offset: float = 0.0
    ) -> float:
        """
        Convert datetime to Julian date.
        
        Args:
            dt: datetime object with date and time
            tz_offset: Timezone offset in hours (e.g., -5 for EST)
            
        Returns:
            Julian date (float)
        """
        time_zone = swe.utc_time_zone(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second,
            tz_offset
        )
        jdut = swe.utc_to_jd(*time_zone)
        return jdut[1]  # Return UT1
    
    def julian_to_datetime(self, jd: float) -> tuple:
        """
        Convert Julian date back to datetime components.
        
        Args:
            jd: Julian date
            
        Returns:
            Tuple of (year, month, day, hour, minute, second)
        """
        return swe.jdut1_to_utc(jd)[:6]
    
    def calculate_design_date(self, birth_jd: float) -> float:
        """
        Calculate Design date using 88° solar arc method.
        
        CRITICAL: This uses 88 DEGREES of solar arc, NOT 88 days!
        The Design is calculated for when the Sun was 88° before
        its birth position, approximately 88-89 days before birth.
        
        Source: Ra Uru Hu BlackBook, verified implementation from
        dturkuler/humandesign_api
        
        Args:
            birth_jd: Birth Julian date
            
        Returns:
            Design Julian date
        """
        # Get Sun's longitude at birth
        sun_result = swe.calc_ut(birth_jd, swe.SUN)
        sun_long = sun_result[0][0]
        
        # Calculate target longitude (88° before birth position)
        target_long = swe.degnorm(sun_long - constants.DESIGN_ARC_DEGREES)
        
        # Find when Sun crossed this longitude (search backwards)
        # Start search ~100 days before to ensure we find it
        search_start = birth_jd - 100
        design_jd = swe.solcross_ut(target_long, search_start)
        
        return design_jd
    
    def get_planet_longitude(
        self,
        jd: float,
        planet_name: str
    ) -> float:
        """
        Get ecliptic longitude for a planet.
        
        Handles special cases:
        - Earth: Opposite Sun (Sun + 180°)
        - South Node: Opposite North Node (North + 180°)
        
        Args:
            jd: Julian date
            planet_name: Planet name (Sun, Moon, Mercury, etc.)
            
        Returns:
            Ecliptic longitude in degrees (0-360)
        """
        planet_code = constants.SWE_PLANETS.get(planet_name)
        
        if planet_code is None:
            raise ValueError(f"Unknown planet: {planet_name}")
        
        # Handle derived positions
        if planet_name == "Earth":
            # Earth is opposite Sun
            sun_result = swe.calc_ut(jd, swe.SUN)
            return (sun_result[0][0] + 180) % 360
        
        elif planet_name == "South_Node":
            # South Node is opposite North Node
            north_result = swe.calc_ut(jd, swe.TRUE_NODE)
            return (north_result[0][0] + 180) % 360
        
        else:
            # Regular planet calculation
            result = swe.calc_ut(jd, planet_code)
            return result[0][0]
    
    def longitude_to_gate(self, longitude: float) -> tuple[int, int]:
        """
        Convert ecliptic longitude to HD gate and line.
        
        Uses IGING offset (58°) to synchronize zodiac with gate wheel.
        Gate 41 begins at zodiac position 302° (Aquarius 2°).
        
        Args:
            longitude: Ecliptic longitude (0-360°)
            
        Returns:
            (gate_number, line_number) - gate 1-64, line 1-6
        """
        # Apply IGING offset to synchronize with gate wheel
        angle = (longitude + constants.IGING_OFFSET) % 360
        angle_percentage = angle / 360
        
        # Calculate gate (each gate spans 5.625°)
        gate_index = int(angle_percentage * 64)
        gate = constants.IGING_CIRCLE_LIST[gate_index]
        
        # Calculate line (each line spans 0.9375°)
        line = int((angle_percentage * 64 * 6) % 6) + 1
        
        return gate, line
    
    def longitude_to_full_activation(
        self,
        longitude: float
    ) -> dict:
        """
        Convert longitude to full HD activation data.
        
        Returns gate, line, color, tone, and base.
        
        Args:
            longitude: Ecliptic longitude (0-360°)
            
        Returns:
            Dict with gate, line, color, tone, base
        """
        angle = (longitude + constants.IGING_OFFSET) % 360
        angle_percentage = angle / 360
        
        gate_index = int(angle_percentage * 64)
        gate = constants.IGING_CIRCLE_LIST[gate_index]
        line = int((angle_percentage * 64 * 6) % 6) + 1
        color = int((angle_percentage * 64 * 6 * 6) % 6) + 1
        tone = int((angle_percentage * 64 * 6 * 6 * 6) % 6) + 1
        base = int((angle_percentage * 64 * 6 * 6 * 6 * 5) % 5) + 1
        
        return {
            "gate": gate,
            "line": line,
            "color": color,
            "tone": tone,
            "base": base,
            "longitude": longitude,
        }
    
    def get_all_planetary_positions(
        self,
        jd: float,
        label: str = "personality"
    ) -> list[dict]:
        """
        Get all planetary positions with gate/line data.
        
        Args:
            jd: Julian date
            label: "personality" or "design"
            
        Returns:
            List of dicts with planet name and activation data
        """
        positions = []
        
        for planet_name in constants.SWE_PLANETS.keys():
            longitude = self.get_planet_longitude(jd, planet_name)
            activation = self.longitude_to_full_activation(longitude)
            activation["planet"] = planet_name
            activation["label"] = label
            positions.append(activation)
        
        return positions


# Module-level singleton for convenience
_ephemeris = None

def get_ephemeris() -> EphemerisCalculator:
    """Get or create ephemeris calculator singleton."""
    global _ephemeris
    if _ephemeris is None:
        _ephemeris = EphemerisCalculator()
    return _ephemeris
