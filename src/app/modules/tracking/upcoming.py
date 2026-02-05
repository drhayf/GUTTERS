# src/app/modules/tracking/upcoming.py

"""
Upcoming Cosmic Events Calculator

Calculates significant astrological events within a specified time window:
- Void of Course Moon periods
- Lunar phases (New/Full Moon)
- Planetary ingresses (sign changes)
- Retrograde stations (direct/retrograde)
- Exact transits to natal chart

Uses Swiss Ephemeris and Skyfield for high-precision calculations.
"""

import math
from datetime import UTC, datetime, timedelta
from typing import Any

import swisseph as swe
from skyfield.api import load

# Ephemeris data (loaded once)
_ts = None
_eph = None


def _get_skyfield():
    """Lazy-load Skyfield ephemeris."""
    global _ts, _eph
    if _ts is None:
        _ts = load.timescale()
        _eph = load("de421.bsp")
    return _ts, _eph


# Sign boundaries at 0° of each sign
SIGNS = [
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

PLANETS = {
    swe.SUN: ("Sun", "☉"),
    swe.MERCURY: ("Mercury", "☿"),
    swe.VENUS: ("Venus", "♀"),
    swe.MARS: ("Mars", "♂"),
    swe.JUPITER: ("Jupiter", "♃"),
    swe.SATURN: ("Saturn", "♄"),
    swe.URANUS: ("Uranus", "♅"),
    swe.NEPTUNE: ("Neptune", "♆"),
    swe.PLUTO: ("Pluto", "♇"),
}

# Outer planets for retrograde tracking (more significant)
OUTER_PLANETS = {swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO}


def _longitude_to_sign(longitude: float) -> str:
    """Convert ecliptic longitude to zodiac sign."""
    return SIGNS[int(longitude / 30) % 12]


def _get_julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day."""
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def _get_planet_position(planet_id: int, jd: float) -> dict[str, Any]:
    """Get planet position at Julian Day."""
    result = swe.calc_ut(jd, planet_id)
    longitude = result[0][0]
    speed = result[0][3]
    return {
        "longitude": longitude,
        "sign": _longitude_to_sign(longitude),
        "degree": longitude % 30,
        "speed": speed,
        "is_retrograde": speed < 0,
    }


async def calculate_upcoming_voc_periods(days: int = 7) -> list[dict[str, Any]]:
    """
    Calculate upcoming Void of Course Moon periods.

    VoC = Moon has made its last major aspect before leaving a sign.
    We approximate by finding when Moon enters next sign.
    """
    events = []
    ts, eph = _get_skyfield()

    earth = eph["earth"]
    moon = eph["moon"]

    now = datetime.now(UTC)

    # Check each hour for the next N days to find sign changes
    current_t = ts.utc(now.year, now.month, now.day, now.hour)
    current_pos = earth.at(current_t).observe(moon).ecliptic_latlon()
    current_sign = _longitude_to_sign(current_pos[0].degrees)

    for hour_offset in range(days * 24):
        check_time = now + timedelta(hours=hour_offset)
        t = ts.utc(check_time.year, check_time.month, check_time.day, check_time.hour)

        moon_pos = earth.at(t).observe(moon).ecliptic_latlon()
        sign = _longitude_to_sign(moon_pos[0].degrees)

        if sign != current_sign:
            # Moon is changing signs - VoC ends here
            events.append(
                {
                    "type": "voc_end",
                    "event_type": "cosmic.lunar.voc_end",
                    "title": f"Moon enters {sign}",
                    "description": f"Void of Course ends. Moon enters {sign} - good time for new beginnings.",
                    "icon": "✨",
                    "datetime": check_time.isoformat(),
                    "timestamp": check_time.timestamp(),
                    "new_sign": sign,
                    "old_sign": current_sign,
                    "category": "lunar",
                }
            )
            current_sign = sign

    return events


async def calculate_upcoming_lunar_phases(days: int = 30) -> list[dict[str, Any]]:
    """Calculate upcoming New and Full Moons."""
    events = []
    ts, eph = _get_skyfield()

    earth = eph["earth"]
    moon = eph["moon"]
    sun = eph["sun"]

    now = datetime.now(UTC)

    # Check every 6 hours for phase changes
    prev_phase_angle = None

    for hour_offset in range(0, days * 24, 6):
        check_time = now + timedelta(hours=hour_offset)
        t = ts.utc(check_time.year, check_time.month, check_time.day, check_time.hour)

        moon_geo = earth.at(t).observe(moon)
        sun_geo = earth.at(t).observe(sun)
        phase_angle = moon_geo.apparent().separation_from(sun_geo).degrees

        moon_pos = earth.at(t).observe(moon).ecliptic_latlon()
        sign = _longitude_to_sign(moon_pos[0].degrees)
        illumination = (1 + math.cos(math.radians(phase_angle))) / 2

        if prev_phase_angle is not None:
            # Detect New Moon (phase angle near 0, crossing from high to low)
            if prev_phase_angle > 330 and phase_angle < 30:
                events.append(
                    {
                        "type": "new_moon",
                        "event_type": "cosmic.lunar.phase",
                        "title": f"🌑 New Moon in {sign}",
                        "description": f"New Moon at {phase_angle:.1f}°. Time for new intentions and beginnings.",
                        "icon": "🌑",
                        "datetime": check_time.isoformat(),
                        "timestamp": check_time.timestamp(),
                        "sign": sign,
                        "phase_name": "New Moon",
                        "illumination": illumination,
                        "category": "lunar",
                    }
                )

            # Detect Full Moon (phase angle near 180)
            if prev_phase_angle < 180 and phase_angle >= 180:
                events.append(
                    {
                        "type": "full_moon",
                        "event_type": "cosmic.lunar.phase",
                        "title": f"🌕 Full Moon in {sign}",
                        "description": "Full Moon illumination. Time for culmination and release.",
                        "icon": "🌕",
                        "datetime": check_time.isoformat(),
                        "timestamp": check_time.timestamp(),
                        "sign": sign,
                        "phase_name": "Full Moon",
                        "illumination": illumination,
                        "category": "lunar",
                    }
                )

        prev_phase_angle = phase_angle

    return events


async def calculate_upcoming_ingresses(days: int = 30) -> list[dict[str, Any]]:
    """Calculate planetary sign ingresses (sign changes)."""
    events = []
    now = datetime.now(UTC)

    # Track current signs
    current_jd = _get_julian_day(now)
    current_signs = {}
    for planet_id in PLANETS:
        pos = _get_planet_position(planet_id, current_jd)
        current_signs[planet_id] = pos["sign"]

    # Check daily for sign changes (planets move slowly enough)
    for day_offset in range(days):
        check_time = now + timedelta(days=day_offset)
        jd = _get_julian_day(check_time)

        for planet_id, (name, symbol) in PLANETS.items():
            pos = _get_planet_position(planet_id, jd)
            if pos["sign"] != current_signs[planet_id]:
                old_sign = current_signs[planet_id]
                new_sign = pos["sign"]

                events.append(
                    {
                        "type": "ingress",
                        "event_type": "cosmic.ingress",
                        "title": f"{symbol} {name} enters {new_sign}",
                        "description": f"{name} shifts from {old_sign} to {new_sign}. Energy transition begins.",
                        "icon": "🚀",
                        "datetime": check_time.isoformat(),
                        "timestamp": check_time.timestamp(),
                        "planet": name,
                        "planet_symbol": symbol,
                        "old_sign": old_sign,
                        "new_sign": new_sign,
                        "is_outer_planet": planet_id in OUTER_PLANETS,
                        "category": "planetary",
                    }
                )

                current_signs[planet_id] = new_sign

    return events


async def calculate_upcoming_retrogrades(days: int = 90) -> list[dict[str, Any]]:
    """Calculate upcoming retrograde stations (direct and retrograde)."""
    events = []
    now = datetime.now(UTC)

    # Track current retrograde status
    current_jd = _get_julian_day(now)
    current_retrogrades = {}
    for planet_id in OUTER_PLANETS:
        pos = _get_planet_position(planet_id, current_jd)
        current_retrogrades[planet_id] = pos["is_retrograde"]

    # Check daily for retrograde status changes
    for day_offset in range(days):
        check_time = now + timedelta(days=day_offset)
        jd = _get_julian_day(check_time)

        for planet_id in OUTER_PLANETS:
            name, symbol = PLANETS[planet_id]
            pos = _get_planet_position(planet_id, jd)
            is_retro = pos["is_retrograde"]

            if is_retro != current_retrogrades[planet_id]:
                if is_retro:
                    # Going retrograde
                    events.append(
                        {
                            "type": "retrograde_start",
                            "event_type": "cosmic.retrograde.start",
                            "title": f"↩️ {name} stations Retrograde",
                            "description": f"{name} moves backward in {pos['sign']}. Review and reflect.",
                            "icon": "↩️",
                            "datetime": check_time.isoformat(),
                            "timestamp": check_time.timestamp(),
                            "planet": name,
                            "planet_symbol": symbol,
                            "sign": pos["sign"],
                            "station_type": "retrograde",
                            "category": "planetary",
                        }
                    )
                else:
                    # Going direct
                    events.append(
                        {
                            "type": "retrograde_end",
                            "event_type": "cosmic.retrograde.end",
                            "title": f"➡️ {name} stations Direct",
                            "description": f"{name} resumes forward motion in {pos['sign']}. Forward momentum returns.",
                            "icon": "➡️",
                            "datetime": check_time.isoformat(),
                            "timestamp": check_time.timestamp(),
                            "planet": name,
                            "planet_symbol": symbol,
                            "sign": pos["sign"],
                            "station_type": "direct",
                            "category": "planetary",
                        }
                    )

                current_retrogrades[planet_id] = is_retro

    return events


async def calculate_upcoming_natal_transits(user_id: int, days: int = 30) -> list[dict[str, Any]]:
    """Calculate upcoming exact transits to natal chart."""
    events = []
    now = datetime.now(UTC)

    # Get natal chart
    from src.app.core.memory import get_active_memory

    memory = get_active_memory()
    await memory.initialize()

    astrology_data = await memory.get_module_output(user_id, "astrology")
    if not astrology_data:
        return events

    # Extract natal planet positions
    natal_points = []
    if "planets" in astrology_data:
        natal_points = astrology_data["planets"]
    elif isinstance(astrology_data, list):
        natal_points = astrology_data

    natal_positions = {}
    for entry in natal_points:
        if isinstance(entry, dict):
            name = entry.get("name", "")
            lon = entry.get("longitude", entry.get("degree", 0))
            if entry.get("sign"):
                # Calculate absolute longitude from sign + degree
                sign_idx = SIGNS.index(entry["sign"]) if entry["sign"] in SIGNS else 0
                lon = sign_idx * 30 + entry.get("degree", 0)
        else:
            name = getattr(entry, "name", "")
            lon = getattr(entry, "longitude", 0)

        if name:
            natal_positions[name] = lon

    # Major aspects to check
    ASPECTS = {
        "conjunction": (0, "☌", 2),  # angle, symbol, orb
        "opposition": (180, "☍", 2),
        "square": (90, "□", 1.5),
        "trine": (120, "△", 1.5),
    }

    # Check daily for exact transits
    for day_offset in range(days):
        check_time = now + timedelta(days=day_offset)
        jd = _get_julian_day(check_time)

        for planet_id in OUTER_PLANETS:
            transit_name, transit_symbol = PLANETS[planet_id]
            transit_pos = _get_planet_position(planet_id, jd)
            transit_lon = transit_pos["longitude"]

            for natal_name, natal_lon in natal_positions.items():
                for aspect_name, (angle, symbol, orb) in ASPECTS.items():
                    # Calculate aspect angle
                    diff = abs(transit_lon - natal_lon)
                    if diff > 180:
                        diff = 360 - diff

                    aspect_diff = abs(diff - angle)

                    # Check if within tight orb (exact transit)
                    if aspect_diff <= orb:
                        events.append(
                            {
                                "type": "natal_transit",
                                "event_type": "cosmic.transit.exact",
                                "title": f"{transit_symbol} {transit_name} {symbol} natal {natal_name}",
                                "description": f"{transit_name} forms {aspect_name} to natal {natal_name}.",
                                "icon": "🎯",
                                "datetime": check_time.isoformat(),
                                "timestamp": check_time.timestamp(),
                                "transit_planet": transit_name,
                                "natal_planet": natal_name,
                                "aspect": aspect_name,
                                "aspect_symbol": symbol,
                                "orb": round(aspect_diff, 2),
                                "exactness": round(1 - (aspect_diff / orb), 2),
                                "category": "personal",
                            }
                        )

    return events


async def calculate_upcoming_events(user_id: int, days: int = 7) -> list[dict[str, Any]]:
    """
    Master function to calculate all upcoming cosmic events.

    Returns events sorted by datetime.
    """
    all_events = []

    # Collect all event types
    voc_events = await calculate_upcoming_voc_periods(days=min(days, 14))
    lunar_events = await calculate_upcoming_lunar_phases(days=max(days, 30))
    ingress_events = await calculate_upcoming_ingresses(days=max(days, 30))
    retrograde_events = await calculate_upcoming_retrogrades(days=max(days, 90))
    natal_events = await calculate_upcoming_natal_transits(user_id, days=max(days, 30))

    all_events.extend(voc_events)
    all_events.extend(lunar_events)
    all_events.extend(ingress_events)
    all_events.extend(retrograde_events)
    all_events.extend(natal_events)

    # Sort by timestamp
    all_events.sort(key=lambda e: e.get("timestamp", 0))

    # Add countdown and relative time
    now = datetime.now(UTC)
    for event in all_events:
        event_time = datetime.fromisoformat(event["datetime"].replace("Z", "+00:00"))
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=UTC)

        delta = event_time - now
        total_hours = delta.total_seconds() / 3600

        if total_hours < 1:
            event["countdown"] = f"{int(delta.total_seconds() / 60)} minutes"
        elif total_hours < 24:
            event["countdown"] = f"{int(total_hours)} hours"
        else:
            event["countdown"] = f"{int(total_hours / 24)} days"

        event["hours_until"] = round(total_hours, 1)

    # Filter to only events within the requested window
    cutoff_timestamp = (now + timedelta(days=days)).timestamp()
    all_events = [e for e in all_events if e.get("timestamp", 0) <= cutoff_timestamp]

    return all_events
