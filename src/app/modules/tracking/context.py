# src/app/modules/tracking/context.py

"""
Cosmic Context Provider

Provides a unified cosmic context snapshot for any moment in time.
Used by:
- Journal entries for auto-tagging
- Observer for correlation analysis
- Intelligence module for pattern detection
- Notifications for contextual alerts

This module orchestrates all tracking modules to create a comprehensive
cosmic fingerprint that can be attached to any user activity.
"""

from datetime import datetime, UTC
from typing import Any, Optional

from .solar.tracker import SolarTracker
from .lunar.tracker import LunarTracker
from .transits.tracker import TransitTracker


async def get_cosmic_context(
    user_id: int,
    timestamp: Optional[datetime] = None,
    include_transits: bool = True,
    include_solar: bool = True,
    include_lunar: bool = True,
) -> dict[str, Any]:
    """
    Get comprehensive cosmic context for a moment.
    
    Creates a snapshot of all cosmic conditions that can be
    attached to journal entries, used for correlation analysis,
    or displayed to the user.
    
    Args:
        user_id: User ID for natal-relative calculations
        timestamp: Specific moment (defaults to now)
        include_transits: Whether to include planetary transit data
        include_solar: Whether to include solar/geomagnetic data
        include_lunar: Whether to include lunar data
    
    Returns:
        Dictionary with comprehensive cosmic context
    """
    timestamp = timestamp or datetime.now(UTC)
    
    context = {
        "timestamp": timestamp.isoformat(),
        "user_id": user_id,
    }
    
    # Solar conditions (geomagnetic activity)
    if include_solar:
        try:
            solar_tracker = SolarTracker()
            solar_data = await solar_tracker.fetch_current_data()
            context["solar"] = {
                "kp_index": solar_data.data.get("kp_index", 0),
                "kp_status": solar_data.data.get("kp_status", "Unknown"),
                "geomagnetic_storm": solar_data.data.get("geomagnetic_storm", False),
                "bz": solar_data.data.get("bz", 0),
                "bz_orientation": solar_data.data.get("bz_orientation", "Unknown"),
                "solar_wind_speed": solar_data.data.get("solar_wind_speed", 0),
                "storm_potential": solar_data.data.get("storm_potential", "Low"),
                "shield_integrity": solar_data.data.get("shield_integrity", "HOLDING"),
            }
        except Exception as e:
            context["solar"] = {"error": str(e), "kp_index": 0}
    
    # Lunar conditions
    if include_lunar:
        try:
            lunar_tracker = LunarTracker()
            lunar_data = await lunar_tracker.fetch_current_data()
            context["lunar"] = {
                "phase_name": lunar_data.data.get("phase_name", "Unknown"),
                "phase_angle": lunar_data.data.get("phase_angle", 0),
                "illumination": lunar_data.data.get("illumination", 0),
                "sign": lunar_data.data.get("sign", "Unknown"),
                "is_voc": lunar_data.data.get("is_voc", False),
                "is_full_moon": lunar_data.data.get("is_full_moon", False),
                "is_new_moon": lunar_data.data.get("is_new_moon", False),
            }
        except Exception as e:
            context["lunar"] = {"error": str(e), "phase_name": "Unknown"}
    
    # Planetary transits
    if include_transits:
        try:
            transit_tracker = TransitTracker()
            transit_result = await transit_tracker.update(user_id)
            comparison = transit_result.get("comparison", {})
            positions = transit_result.get("current_data", {}).get("data", {}).get("positions", {})
            
            # Extract active retrogrades
            retrogrades = [
                planet for planet, data in positions.items()
                if data.get("is_retrograde", False)
            ]
            
            # Extract exact aspects
            exact_transits = comparison.get("exact_transits", [])
            
            context["transits"] = {
                "retrogrades": retrogrades,
                "retrograde_count": len(retrogrades),
                "exact_aspects": [
                    {
                        "transit": t.get("transit_planet"),
                        "natal": t.get("natal_planet"),
                        "aspect": t.get("aspect"),
                        "orb": t.get("orb"),
                    }
                    for t in exact_transits[:5]  # Top 5 exact
                ],
                "total_active_transits": comparison.get("total_transits", 0),
            }
        except Exception as e:
            context["transits"] = {"error": str(e), "retrogrades": []}
    
    # Generate summary tags for easy filtering
    context["tags"] = _generate_cosmic_tags(context)
    
    # Generate overall cosmic intensity score (0-10)
    context["intensity_score"] = _calculate_cosmic_intensity(context)
    
    return context


def _generate_cosmic_tags(context: dict[str, Any]) -> list[str]:
    """Generate searchable tags from cosmic context."""
    tags = []
    
    # Solar tags
    solar = context.get("solar", {})
    if solar.get("geomagnetic_storm"):
        tags.append("geomagnetic_storm")
    if solar.get("kp_index", 0) >= 5:
        tags.append("high_kp")
    if solar.get("bz", 0) <= -5:
        tags.append("bz_south")
    if solar.get("shield_integrity") in ["CRACKED", "CRITICAL FAILURE"]:
        tags.append("shield_compromised")
    
    # Lunar tags
    lunar = context.get("lunar", {})
    if lunar.get("is_voc"):
        tags.append("void_of_course")
    if lunar.get("is_full_moon"):
        tags.append("full_moon")
    if lunar.get("is_new_moon"):
        tags.append("new_moon")
    if sign := lunar.get("sign"):
        tags.append(f"moon_in_{sign.lower()}")
    
    # Transit tags
    transits = context.get("transits", {})
    if transits.get("retrograde_count", 0) >= 3:
        tags.append("multiple_retrogrades")
    if transits.get("exact_aspects"):
        tags.append("exact_transit_active")
    for planet in transits.get("retrogrades", []):
        tags.append(f"{planet.lower()}_retrograde")
    
    return tags


def _calculate_cosmic_intensity(context: dict[str, Any]) -> float:
    """
    Calculate overall cosmic intensity score (0-10).
    
    Higher scores indicate more active/intense cosmic conditions
    that may affect sensitive individuals.
    """
    score = 0.0
    
    # Solar contribution (0-4)
    solar = context.get("solar", {})
    kp = solar.get("kp_index", 0)
    score += min(4.0, kp / 2.25)  # Kp 9 = 4 points
    
    # Lunar contribution (0-3)
    lunar = context.get("lunar", {})
    if lunar.get("is_full_moon") or lunar.get("is_new_moon"):
        score += 1.5
    if lunar.get("is_voc"):
        score += 0.5
    illumination = lunar.get("illumination", 0.5)
    # Higher illumination = slightly higher intensity
    score += illumination * 1.0
    
    # Transit contribution (0-3)
    transits = context.get("transits", {})
    retrograde_count = transits.get("retrograde_count", 0)
    score += min(1.5, retrograde_count * 0.5)
    
    exact_count = len(transits.get("exact_aspects", []))
    score += min(1.5, exact_count * 0.3)
    
    return round(min(10.0, score), 1)


async def get_location_aware_context(
    user_id: int,
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None,
) -> dict[str, Any]:
    """
    Get cosmic context with location-specific solar impact.
    
    Extends the standard cosmic context with aurora visibility
    and geomagnetic impact calculations for the user's location.
    """
    # Get base context
    context = await get_cosmic_context(user_id, timestamp)
    
    # Add location-aware solar data
    try:
        solar_tracker = SolarTracker()
        location_data = await solar_tracker.fetch_location_aware(latitude, longitude)
        
        context["location_solar"] = location_data["local_impact"]
        context["aurora"] = location_data["aurora_guidance"]
        
        # Add location-specific tags
        if location_data["local_impact"]["aurora"]["status"] in ["VISIBLE", "POSSIBLE"]:
            context["tags"].append("aurora_possible")
        if location_data["local_impact"]["local_impact"]["severity"] >= 2:
            context["tags"].append("high_local_impact")
            
    except Exception as e:
        context["location_solar"] = {"error": str(e)}
    
    return context
