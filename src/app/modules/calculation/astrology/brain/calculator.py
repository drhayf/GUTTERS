"""
GUTTERS Astrology Calculator - BRAIN

Pure calculation functions for natal chart computation.
Uses Kerykeion for Swiss Ephemeris calculations.

NO event system knowledge - pure inputs and outputs.
This makes the brain:
- Testable in isolation
- Swappable for different calculation engines
- Reusable outside the module system
"""

from datetime import date, time
from typing import Any


def calculate_natal_chart(
    name: str,
    birth_date: date | str,
    birth_time: time | str | None,
    latitude: float,
    longitude: float,
    timezone: str = "UTC",
) -> dict[str, Any]:
    """
    Calculate a complete natal chart.

    Uses Kerykeion (Swiss Ephemeris wrapper) for accurate astronomical calculations.

    Args:
        name: Subject's name
        birth_date: Birth date (YYYY-MM-DD or date object)
        birth_time: Birth time (HH:MM:SS or time object), None for noon chart
        latitude: Birth location latitude
        longitude: Birth location longitude
        timezone: IANA timezone string (e.g., "America/New_York")

    Returns:
        Complete natal chart data:
        {
            "subject": {"name": str, "birth_data": {...}},
            "planets": [{"name": str, "sign": str, "degree": float, "house": int}, ...],
            "houses": [{"number": int, "sign": str, "degree": float}, ...],
            "aspects": [{"planet1": str, "planet2": str, "type": str, "orb": float}, ...],
            "elements": {"fire": int, "earth": int, "air": int, "water": int},
            "modalities": {"cardinal": int, "fixed": int, "mutable": int}
        }

    Example:
        >>> chart = calculate_natal_chart(
        ...     name="John Doe",
        ...     birth_date=date(1990, 5, 15),
        ...     birth_time=time(14, 30),
        ...     latitude=37.7749,
        ...     longitude=-122.4194,
        ...     timezone="America/Los_Angeles"
        ... )
        >>> print(chart["planets"][0])  # Sun position
    """
    from kerykeion import AstrologicalSubjectFactory

    # Parse date if string
    if isinstance(birth_date, str):
        from datetime import datetime as dt

        birth_date = dt.strptime(birth_date, "%Y-%m-%d").date()

    # Track if this is a solar chart (noon default when birth time unknown)
    is_solar_chart = birth_time is None

    # Parse time if string, default to noon if not provided (solar chart)
    hour, minute = 12, 0
    if birth_time is not None:
        if isinstance(birth_time, str):
            parts = birth_time.split(":")
            hour, minute = int(parts[0]), int(parts[1])
        else:
            hour, minute = birth_time.hour, birth_time.minute

    # Create Kerykeion subject
    subject = AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=hour,
        minute=minute,
        lat=latitude,
        lng=longitude,
        tz_str=timezone,
    )

    # Extract planetary positions
    planets = _extract_planets(subject)

    # Extract house cusps
    houses = _extract_houses(subject)

    # Calculate aspects
    aspects = _extract_aspects(subject)

    # Calculate element/modality distribution
    elements = _calculate_elements(planets)
    modalities = _calculate_modalities(planets)

    # Build chart data with accuracy metadata
    chart_data = {
        "subject": {
            "name": name,
            "birth_data": {
                "date": str(birth_date),
                "time": f"{hour:02d}:{minute:02d}",
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
            },
        },
        "planets": planets,
        "aspects": aspects,
        "elements": elements,
        "modalities": modalities,
    }

    # Handle birth time known vs unknown
    if is_solar_chart:
        # Calculate probabilistic rising sign by sampling 24 hours
        rising_data = _calculate_probabilistic_rising(birth_date, latitude, longitude, timezone)

        chart_data.update(
            {
                "houses": [],
                "ascendant": rising_data["most_likely_ascendant"],
                "midheaven": None,
                "accuracy": "probabilistic",
                "rising_confidence": rising_data["confidence"],
                "rising_probabilities": rising_data["probabilities"],
                "planet_stability": rising_data["planet_stability"],
                "aspect_stability": rising_data["aspect_stability"],
                "note": f"Rising sign is {rising_data['most_likely_sign']} with {rising_data['confidence']:.0%} confidence. Exact birth time needed for houses and precise rising degree.",
                "available_data": ["planets", "aspects", "rising_probability", "planet_stability", "aspect_stability"],
            }
        )

    else:
        # Full chart with known birth time
        chart_data.update(
            {
                "houses": houses,
                "ascendant": {
                    "sign": subject.first_house.sign,
                    "degree": round(subject.first_house.position, 2),
                },
                "midheaven": {
                    "sign": subject.tenth_house.sign,
                    "degree": round(subject.tenth_house.position, 2),
                },
                "accuracy": "full",
                "rising_confidence": 1.0,
                "rising_probabilities": None,
                "note": None,
                "available_data": ["planets", "houses", "rising", "aspects"],
            }
        )

    return chart_data


def _extract_planets(subject) -> list[dict[str, Any]]:
    """Extract planetary positions from Kerykeion subject."""
    planet_attrs = [
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
        "chiron",
        "north_node",
        "south_node",
    ]

    planets = []
    for attr in planet_attrs:
        if hasattr(subject, attr):
            planet = getattr(subject, attr)
            planets.append(
                {
                    "name": planet.name,
                    "sign": planet.sign,
                    "degree": round(planet.position, 2),
                    "house": planet.house,
                    "retrograde": getattr(planet, "retrograde", False),
                }
            )

    return planets


def _extract_houses(subject) -> list[dict[str, Any]]:
    """Extract house cusps from Kerykeion subject."""
    house_attrs = [
        "first_house",
        "second_house",
        "third_house",
        "fourth_house",
        "fifth_house",
        "sixth_house",
        "seventh_house",
        "eighth_house",
        "ninth_house",
        "tenth_house",
        "eleventh_house",
        "twelfth_house",
    ]

    houses = []
    for i, attr in enumerate(house_attrs, 1):
        if hasattr(subject, attr):
            house = getattr(subject, attr)
            houses.append(
                {
                    "number": i,
                    "sign": house.sign,
                    "degree": round(house.position, 2),
                }
            )

    return houses


def _extract_aspects(subject) -> list[dict[str, Any]]:
    """Extract aspects from Kerykeion subject."""
    aspects = []

    # Get aspects from Kerykeion's aspect calculation
    if hasattr(subject, "aspects_list"):
        for aspect in subject.aspects_list:
            aspects.append(
                {
                    "planet1": aspect.get("p1_name", ""),
                    "planet2": aspect.get("p2_name", ""),
                    "type": aspect.get("aspect", ""),
                    "orb": round(aspect.get("orb", 0), 2),
                }
            )

    return aspects


def _calculate_elements(planets: list[dict]) -> dict[str, int]:
    """Calculate element distribution from planet positions."""
    element_map = {
        "Ari": "fire",
        "Leo": "fire",
        "Sag": "fire",
        "Tau": "earth",
        "Vir": "earth",
        "Cap": "earth",
        "Gem": "air",
        "Lib": "air",
        "Aqu": "air",
        "Can": "water",
        "Sco": "water",
        "Pis": "water",
    }

    elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}

    for planet in planets:
        sign = planet.get("sign", "")[:3]
        if sign in element_map:
            elements[element_map[sign]] += 1

    return elements


def _calculate_modalities(planets: list[dict]) -> dict[str, int]:
    """Calculate modality distribution from planet positions."""
    modality_map = {
        "Ari": "cardinal",
        "Can": "cardinal",
        "Lib": "cardinal",
        "Cap": "cardinal",
        "Tau": "fixed",
        "Leo": "fixed",
        "Sco": "fixed",
        "Aqu": "fixed",
        "Gem": "mutable",
        "Vir": "mutable",
        "Sag": "mutable",
        "Pis": "mutable",
    }

    modalities = {"cardinal": 0, "fixed": 0, "mutable": 0}

    for planet in planets:
        sign = planet.get("sign", "")[:3]
        if sign in modality_map:
            modalities[modality_map[sign]] += 1

    return modalities


def _calculate_probabilistic_rising(birth_date: date, latitude: float, longitude: float, timezone: str) -> dict:
    """
    Calculate probabilistic chart data by sampling all 24 hours of the day.

    Returns:
    - Rising sign probabilities
    - Planet stability (sign/house consistency)
    - Aspect stability (which aspects are certain)
    """
    from kerykeion import AstrologicalSubjectFactory
    from collections import Counter, defaultdict
    from datetime import time

    rising_counts = Counter()
    planet_signs = defaultdict(Counter)  # planet -> {sign: count}
    planet_houses = defaultdict(Counter)  # planet -> {house: count}
    aspect_counts = Counter()  # (planet1, planet2, type) -> count

    hourly_charts = []

    # Sample every hour of the day
    for hour in range(24):
        try:
            subject = AstrologicalSubjectFactory.from_birth_data(
                name="Sample",
                year=birth_date.year,
                month=birth_date.month,
                day=birth_date.day,
                hour=hour,
                minute=0,
                lat=latitude,
                lng=longitude,
                tz_str=timezone,
            )

            # Track rising sign
            rising_sign = subject.first_house.sign
            rising_counts[rising_sign] += 1

            # Track planet signs and houses
            planet_attrs = [
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
            ]
            for attr in planet_attrs:
                if hasattr(subject, attr):
                    planet = getattr(subject, attr)
                    planet_signs[planet.name][planet.sign] += 1
                    planet_houses[planet.name][planet.house] += 1

            # Track aspects
            aspects = _extract_aspects(subject)
            for asp in aspects:
                key = (asp["planet1"], asp["planet2"], asp["type"])
                aspect_counts[key] += 1

            hourly_charts.append(subject)

        except Exception:
            continue

    total_samples = len(hourly_charts)

    if total_samples == 0:
        return {
            "most_likely_sign": "Unknown",
            "most_likely_ascendant": None,
            "confidence": 0.0,
            "probabilities": [],
            "planet_stability": [],
            "aspect_stability": [],
        }

    # Build rising sign probabilities
    probabilities = []
    for sign, count in rising_counts.most_common():
        probability = count / total_samples
        confidence = (
            "certain"
            if probability >= 1.0
            else "high"
            if probability >= 0.75
            else "medium"
            if probability >= 0.5
            else "low"
        )
        probabilities.append(
            {"sign": sign, "probability": round(probability, 3), "hours_count": count, "confidence": confidence}
        )

    # Build planet stability analysis
    planet_stability = []
    for planet_name in planet_signs:
        signs = planet_signs[planet_name]
        houses = planet_houses[planet_name]

        most_common_sign = signs.most_common(1)[0][0]
        sign_stable = len(signs) == 1  # Same sign all 24 hours

        house_values = list(houses.keys())
        house_min, house_max = min(house_values), max(house_values)
        house_stable = len(houses) == 1  # Same house all 24 hours

        note = None
        if sign_stable and house_stable:
            note = "Certain (same all day)"
        elif sign_stable and not house_stable:
            note = f"Sign certain, house varies ({house_min}-{house_max})"
        else:
            note = f"Varies: {', '.join(signs.keys())}"

        planet_stability.append(
            {
                "planet": planet_name,
                "sign": most_common_sign,
                "sign_stable": sign_stable,
                "house_range": (house_min, house_max),
                "house_stable": house_stable,
                "note": note,
            }
        )

    # Build aspect stability analysis
    aspect_stability = []
    for (p1, p2, asp_type), count in aspect_counts.most_common():
        probability = count / total_samples
        confidence = (
            "certain"
            if probability >= 1.0
            else "high"
            if probability >= 0.75
            else "medium"
            if probability >= 0.5
            else "low"
        )

        # Only include aspects that appear in at least 50% of hours
        if probability >= 0.5:
            aspect_stability.append(
                {
                    "planet1": p1,
                    "planet2": p2,
                    "aspect_type": asp_type,
                    "stable": count == total_samples,
                    "hours_present": count,
                    "confidence": confidence,
                }
            )

    # Get most likely rising sign
    most_likely_sign, most_likely_count = rising_counts.most_common(1)[0]
    confidence = most_likely_count / total_samples

    return {
        "most_likely_sign": most_likely_sign,
        "most_likely_ascendant": {"sign": most_likely_sign, "degree": 15.0},
        "confidence": round(confidence, 3),
        "probabilities": probabilities,
        "planet_stability": planet_stability,
        "aspect_stability": aspect_stability,
    }
