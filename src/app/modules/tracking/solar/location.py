# src/app/modules/tracking/solar/location.py

"""
Location-Based Solar Impact Calculator

Calculates how solar activity affects the user's specific location:
- Geomagnetic latitude calculation
- Aurora visibility probability
- Local impact severity based on Kp and location
- Specific effects and recommendations

Aurora visibility depends on geomagnetic (not geographic) latitude.
Geomagnetic latitude is roughly geographic latitude adjusted for magnetic pole offset.
"""

import math
from datetime import UTC, datetime
from typing import Any

# Approximate Geomagnetic North Pole coordinates (2025 estimate)
# The pole moves ~50km/year towards Siberia
GEOMAG_POLE_LAT = 80.7  # degrees N
GEOMAG_POLE_LON = -72.7  # degrees W (288.3 E)


def calculate_geomagnetic_latitude(lat: float, lon: float) -> float:
    """
    Calculate geomagnetic latitude from geographic coordinates.

    Uses the centered dipole approximation. The geomagnetic latitude
    determines aurora visibility - higher geomagnetic latitudes see
    aurora at lower Kp values.

    Args:
        lat: Geographic latitude (-90 to 90)
        lon: Geographic longitude (-180 to 180)

    Returns:
        Geomagnetic latitude in degrees
    """
    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    pole_lat_rad = math.radians(GEOMAG_POLE_LAT)
    pole_lon_rad = math.radians(GEOMAG_POLE_LON)

    # Spherical geometry: geomagnetic latitude
    # sin(λm) = sin(λ)sin(λp) + cos(λ)cos(λp)cos(φ - φp)
    sin_geomag = (
        math.sin(lat_rad) * math.sin(pole_lat_rad) +
        math.cos(lat_rad) * math.cos(pole_lat_rad) * math.cos(lon_rad - pole_lon_rad)
    )

    # Clamp to valid range for asin
    sin_geomag = max(-1.0, min(1.0, sin_geomag))

    return math.degrees(math.asin(sin_geomag))


def get_aurora_visibility_kp(geomag_lat: float) -> int:
    """
    Get minimum Kp index required for aurora visibility at given geomagnetic latitude.

    Based on empirical aurora oval data:
    - Kp 0: ~67° geomag lat (extreme north)
    - Kp 5: ~55° geomag lat (northern US/Canada)
    - Kp 9: ~45° geomag lat (mid-latitudes possible)

    Args:
        geomag_lat: Geomagnetic latitude (absolute value used)

    Returns:
        Minimum Kp index (0-9) for aurora visibility, or 10 if impossible
    """
    abs_lat = abs(geomag_lat)

    # Aurora visibility thresholds (approximate)
    # These expand equatorward as Kp increases
    thresholds = [
        (67, 0),   # Kp 0: Only extreme north
        (65, 1),
        (62, 2),
        (60, 3),
        (57, 4),
        (55, 5),   # Kp 5: Northern US/southern Canada
        (52, 6),
        (50, 7),
        (47, 8),
        (45, 9),   # Kp 9: Mid-latitudes during extreme storms
    ]

    for lat_threshold, kp in thresholds:
        if abs_lat >= lat_threshold:
            return kp

    return 10  # Aurora essentially impossible at this latitude


def calculate_aurora_probability(kp_index: float, geomag_lat: float) -> float:
    """
    Calculate probability of aurora visibility at location.

    Args:
        kp_index: Current Kp index (0-9)
        geomag_lat: Geomagnetic latitude

    Returns:
        Probability 0.0 - 1.0
    """
    min_kp = get_aurora_visibility_kp(geomag_lat)

    if min_kp > 9:
        return 0.0  # Location too far from poles

    if kp_index < min_kp:
        # Below threshold - small chance if close
        margin = min_kp - kp_index
        if margin <= 1:
            return 0.1  # Slight possibility
        return 0.0

    # Above threshold - probability increases with Kp excess
    excess = kp_index - min_kp
    base_prob = 0.5 + (excess * 0.1)

    return min(0.95, base_prob)


def assess_local_solar_impact(
    kp_index: float,
    bz: float,
    solar_wind_speed: float,
    latitude: float,
    longitude: float
) -> dict[str, Any]:
    """
    Comprehensive assessment of solar activity impact on specific location.

    Args:
        kp_index: Current Kp index
        bz: IMF Bz component (nT)
        solar_wind_speed: Solar wind velocity (km/s)
        latitude: User's geographic latitude
        longitude: User's geographic longitude

    Returns:
        Dictionary with location-specific impact analysis
    """
    # Calculate geomagnetic position
    geomag_lat = calculate_geomagnetic_latitude(latitude, longitude)
    min_kp_for_aurora = get_aurora_visibility_kp(geomag_lat)
    aurora_prob = calculate_aurora_probability(kp_index, geomag_lat)

    # Determine aurora status
    if aurora_prob >= 0.7:
        aurora_status = "VISIBLE"
        aurora_alert = True
    elif aurora_prob >= 0.3:
        aurora_status = "POSSIBLE"
        aurora_alert = True
    elif aurora_prob > 0:
        aurora_status = "UNLIKELY"
        aurora_alert = False
    else:
        aurora_status = "NOT VISIBLE"
        aurora_alert = False

    # Calculate local intensity factor
    # Higher geomagnetic latitudes experience more intense effects
    intensity_factor = min(1.0, abs(geomag_lat) / 60.0)  # Normalized 0-1

    # Overall impact severity
    base_severity = 0
    if kp_index >= 7:
        base_severity = 3  # Severe
    elif kp_index >= 5:
        base_severity = 2  # Moderate
    elif kp_index >= 3:
        base_severity = 1  # Minor

    # Adjust for location (higher latitudes feel it more)
    local_severity = base_severity + (1 if intensity_factor > 0.8 and kp_index >= 4 else 0)
    local_severity = min(3, local_severity)

    severity_labels = {0: "MINIMAL", 1: "MINOR", 2: "MODERATE", 3: "SIGNIFICANT"}

    # Generate specific effects and recommendations
    effects = []
    recommendations = []

    if local_severity >= 2:
        effects.extend([
            "Potential fluctuations in focus and cognitive clarity",
            "Possible increased sensitivity to electronics",
            "Heightened emotional reactivity",
        ])
        recommendations.extend([
            "Schedule important decisions for calmer conditions",
            "Practice grounding exercises",
            "Limit screen time if experiencing headaches",
        ])

    if local_severity >= 3 or (kp_index >= 6 and intensity_factor > 0.7):
        effects.extend([
            "GPS and navigation systems may be less accurate",
            "Radio communication disruptions possible",
            "Higher probability of fatigue and restlessness",
        ])
        recommendations.extend([
            "Consider delaying high-precision tasks",
            "Ensure adequate hydration",
            "Extra rest may be beneficial",
        ])

    if aurora_alert:
        if aurora_prob >= 0.5:
            recommendations.append("Aurora visible tonight - find a dark location with northern horizon view")
        else:
            recommendations.append("Monitor aurora forecasts - conditions may improve for visibility")

    # Electromagnetic sensitivity context
    sensitivity_note = None
    if local_severity >= 2:
        sensitivity_note = (
            "Electromagnetically sensitive individuals may notice symptoms. "
            "Your journal patterns will help the Observer identify your personal response signature."
        )

    return {
        "geographic_location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "geomagnetic_latitude": round(geomag_lat, 1),
        "intensity_factor": round(intensity_factor, 2),
        "aurora": {
            "status": aurora_status,
            "probability": round(aurora_prob, 2),
            "min_kp_required": min_kp_for_aurora,
            "alert": aurora_alert,
        },
        "local_impact": {
            "severity": local_severity,
            "severity_label": severity_labels[local_severity],
            "effects": effects,
            "recommendations": recommendations,
        },
        "sensitivity_note": sensitivity_note,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def get_hemisphere(latitude: float) -> str:
    """Get hemisphere for aurora direction guidance."""
    return "NORTHERN" if latitude >= 0 else "SOUTHERN"


def get_optimal_aurora_viewing_direction(latitude: float) -> str:
    """Get the direction to look for aurora based on hemisphere."""
    if latitude >= 0:
        return "Look toward the northern horizon"
    else:
        return "Look toward the southern horizon (Aurora Australis)"
