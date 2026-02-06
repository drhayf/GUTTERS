# src/app/modules/tracking/solar/tracker.py

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from ..base import BaseTrackingModule, TrackingData
from .location import (
    assess_local_solar_impact,
    calculate_aurora_probability,
    calculate_geomagnetic_latitude,
    get_hemisphere,
    get_optimal_aurora_viewing_direction,
)


class SolarTracker(BaseTrackingModule):
    """
    Tracks space weather and solar activity.

    Data sources:
    - NOAA Space Weather Prediction Center
    - NASA DONKI (backup)

    Monitors:
    - Solar flares (X/M/C class)
    - Coronal mass ejections (CMEs)
    - Geomagnetic storms (Kp index)
    - Solar wind speed
    """

    module_name = "solar_tracking"
    update_frequency = "hourly"

    NOAA_KP_INDEX_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
    NOAA_XRAY_FLARES_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
    NOAA_MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
    NOAA_PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"

    async def get_current_conditions(self) -> dict:
        """Alias for fetch_current_data to satisfy E2E test expectations."""
        tracking_data = await self.fetch_current_data()
        return tracking_data.data

    async def fetch_current_data(self) -> TrackingData:
        """Fetch current space weather from NOAA."""
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Fetch Kp index (Geomagnetic Storms)
                async with session.get(self.NOAA_KP_INDEX_URL, timeout=10) as response:
                    response.raise_for_status()
                    kp_data = await response.json()

                # 2. Fetch Solar Flares (X-Rays)
                async with session.get(self.NOAA_XRAY_FLARES_URL, timeout=10) as response:
                    response.raise_for_status()
                    flare_data = await response.json()

                # 3. Fetch Magnetic Field (Bz)
                async with session.get(self.NOAA_MAG_URL, timeout=10) as response:
                    response.raise_for_status()
                    mag_data_raw = await response.json()

                # 4. Fetch Solar Wind (Plasma)
                async with session.get(self.NOAA_PLASMA_URL, timeout=10) as response:
                    response.raise_for_status()
                    plasma_data_raw = await response.json()

        except (TimeoutError, aiohttp.ClientError) as e:
            print(f"[SolarTracker] API error: {e}")
            # Return safe default
            return TrackingData(
                timestamp=datetime.now(UTC),
                source="NOAA SWPC (Error Fallback)",
                data={
                    "kp_index": 0,
                    "kp_status": "Unknown",
                    "solar_flares": [],
                    "geomagnetic_storm": False,
                    "bz": 0.0,
                    "solar_wind_speed": 400.0,
                    "solar_wind_density": 5.0,
                    "storm_potential": "Low",
                },
            )

        # --- Parse Data ---

        # Kp Index
        latest_kp = kp_data[-1] if kp_data else {}
        kp_index = float(latest_kp.get("kp_index", 0))

        # Solar Flares
        recent_flares = self._parse_recent_flares(flare_data)

        # BZ and Solar Wind (Handle list-of-lists format from SWPC Products)
        bz = self._parse_swpc_product_data(mag_data_raw, "bz_gsm")
        wind_speed = self._parse_swpc_product_data(plasma_data_raw, "speed")
        density = self._parse_swpc_product_data(plasma_data_raw, "density")

        # Calculate composite metrics
        storm_potential = self._calculate_storm_potential(bz, wind_speed, density)
        bz_orientation = "South" if bz < 0 else "North"

        return TrackingData(
            timestamp=datetime.now(UTC),
            source="NOAA SWPC",
            data={
                "kp_index": kp_index,
                "kp_status": self._get_kp_status(kp_index),
                "solar_flares": recent_flares,
                "geomagnetic_storm": kp_index >= 5,
                "bz": bz,
                "bz_orientation": bz_orientation,
                "solar_wind_speed": wind_speed,
                "solar_wind_density": density,
                "storm_potential": storm_potential,
                "shield_integrity": self._calculate_shield_integrity(bz, wind_speed),
            },
        )

    async def fetch_location_aware(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Fetch solar data with location-specific impact analysis.

        Combines real-time NOAA data with geomagnetic calculations
        to provide personalized impact assessment including:
        - Aurora visibility at user's location
        - Local impact severity
        - Specific effects and recommendations

        Args:
            latitude: User's geographic latitude
            longitude: User's geographic longitude

        Returns:
            Dictionary with both global space weather and local impact
        """
        # Get current space weather
        current_data = await self.fetch_current_data()

        # Extract key values for location analysis
        kp_index = current_data.data.get("kp_index", 0)
        bz = current_data.data.get("bz", 0)
        solar_wind_speed = current_data.data.get("solar_wind_speed", 400)

        # Calculate location-specific impact
        local_impact = assess_local_solar_impact(
            kp_index=kp_index,
            bz=bz,
            solar_wind_speed=solar_wind_speed,
            latitude=latitude,
            longitude=longitude,
        )

        # Get aurora viewing direction for user's hemisphere
        hemisphere = get_hemisphere(latitude)
        viewing_direction = get_optimal_aurora_viewing_direction(latitude)

        return {
            "global_conditions": current_data.data,
            "local_impact": local_impact,
            "aurora_guidance": {
                "hemisphere": hemisphere,
                "viewing_direction": viewing_direction,
                "best_time": "Local midnight to 2 AM",
                "tips": self._get_aurora_viewing_tips(local_impact["aurora"]["probability"]),
            },
            "timestamp": current_data.timestamp.isoformat(),
            "source": current_data.source,
        }

    def _get_aurora_viewing_tips(self, probability: float) -> List[str]:
        """Get aurora viewing tips based on probability."""
        tips = []

        if probability >= 0.5:
            tips.extend([
                "Find a location away from city lights",
                "Allow 20-30 minutes for eyes to adjust to darkness",
                "Check for clear skies - clouds will block the view",
                "Use a camera with long exposure for best photos",
                "Peak activity often occurs around local midnight",
            ])
        elif probability > 0:
            tips.extend([
                "Monitor real-time aurora alerts for activity spikes",
                "Have a viewing plan ready in case conditions improve",
                "Even faint aurora can be captured with long-exposure photography",
            ])
        else:
            tips.append("Aurora not expected at your latitude with current conditions")

        return tips

    async def compare_to_natal(self, user_id: int, current_data: TrackingData) -> dict:
        """
        Compare current space weather to user's sensitivity.

        This requires historical data about user's responses to solar events.
        For now, return general insights.
        """
        kp = current_data.data.get("kp_index", 0)

        return {
            "kp_index": kp,
            "sensitivity_level": "high" if kp >= 5 else "moderate" if kp >= 3 else "low",
            "recommendation": self._get_recommendation(kp),
        }

    def detect_significant_events(
        self,
        current_data: TrackingData,
        previous_data: Optional[TrackingData],
        comparison: Optional[dict] = None,
    ) -> List[str]:
        """Detect events that should trigger synthesis and XP."""
        events = []
        current_kp = current_data.data.get("kp_index", 0)

        # Solar Storm Classification (User-facing)
        if current_kp >= 9:
            events.append("Cosmic Witness: G5 Extreme Solar Storm")
        elif current_kp >= 7:
            events.append("Cosmic Witness: G4 Severe Solar Storm")
        elif current_kp >= 5:
            events.append("Cosmic Witness: G2-G3 Moderate Solar Storm")

        # Bz Flips (Southward Turn)
        previous_bz = previous_data.data.get("bz", 0.0) if previous_data else 0.0
        current_bz = current_data.data.get("bz", 0.0)

        # Trigger if Bz goes significantly South (< -5nT) when it wasn't before
        if current_bz <= -5.0 and previous_bz > -5.0:
            events.append("Cosmic Witness: Magnetic Field Cracks South")

        # High Speed Stream
        current_speed = current_data.data.get("solar_wind_speed", 0.0)
        previous_speed = previous_data.data.get("solar_wind_speed", 0.0) if previous_data else 0.0

        # Trigger on large jump or threshold crossing
        if current_speed > 600 and previous_speed <= 600:
            events.append("Cosmic Witness: High-Velocity Solar Wind Stream")

        # Solar Flares
        flares = current_data.data.get("solar_flares", [])
        for flare in flares:
            flare_class = flare.get("class", "")
            if flare_class.startswith("X"):
                events.append(f"Cosmic Witness: {flare_class}-Class Solar Flare")
            elif flare_class.startswith("M"):
                events.append(f"Cosmic Witness: {flare_class}-Class Solar Flare")

        return list(set(events))  # De-duplicate

    def detect_location_aware_events(
        self,
        current_data: TrackingData,
        previous_data: Optional[TrackingData],
        latitude: float,
        longitude: float,
        previous_aurora_prob: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect events that affect the user's specific location.

        Includes aurora alerts when visibility becomes possible at user's latitude.

        Args:
            current_data: Current tracking data
            previous_data: Previous tracking data (for change detection)
            latitude: User's geographic latitude
            longitude: User's geographic longitude
            previous_aurora_prob: Previous aurora probability at location

        Returns:
            List of location-specific events with metadata
        """
        events = []
        kp_index = current_data.data.get("kp_index", 0)
        bz = current_data.data.get("bz", 0)

        # Calculate geomagnetic position
        geomag_lat = calculate_geomagnetic_latitude(latitude, longitude)
        aurora_prob = calculate_aurora_probability(kp_index, geomag_lat)

        # Aurora visibility alert - when it becomes visible at user's location
        if aurora_prob >= 0.5 and previous_aurora_prob < 0.5:
            hemisphere = get_hemisphere(latitude)
            aurora_name = "Aurora Borealis" if hemisphere == "NORTHERN" else "Aurora Australis"
            events.append({
                "type": "aurora_visible",
                "title": f"{aurora_name} Alert",
                "description": f"Aurora may be visible from your location! Current Kp: {kp_index:.1f}",
                "severity": "high",
                "aurora_probability": aurora_prob,
                "viewing_direction": get_optimal_aurora_viewing_direction(latitude),
                "actionable": True,
                "action_hint": "Find a dark location with clear northern horizon view",
            })
        elif aurora_prob >= 0.3 and previous_aurora_prob < 0.3:
            events.append({
                "type": "aurora_possible",
                "title": "Aurora Conditions Improving",
                "description": "Aurora may become visible if activity increases. Monitor alerts.",
                "severity": "medium",
                "aurora_probability": aurora_prob,
                "actionable": False,
            })

        # Location-specific impact alerts
        if abs(geomag_lat) > 55:  # High geomagnetic latitudes
            if kp_index >= 5:
                events.append({
                    "type": "high_latitude_storm",
                    "title": "Geomagnetic Storm at Your Latitude",
                    "description": (
                        f"Your high-latitude location (geomag: {geomag_lat:.1f}°) "
                        f"experiences stronger effects during Kp {kp_index:.1f} storms."
                    ),
                    "severity": "high" if kp_index >= 7 else "medium",
                    "effects": [
                        "GPS accuracy may be reduced",
                        "Radio communications may be affected",
                        "Increased fatigue and sensitivity possible",
                    ],
                    "actionable": True,
                    "action_hint": "Allow extra time for navigation, practice grounding",
                })

        # Shield integrity alert for location
        if bz <= -10:  # Severe Bz southward
            events.append({
                "type": "shield_breach",
                "title": "Earth's Magnetic Shield Severely Strained",
                "description": (
                    f"Bz at {bz:.1f} nT indicates significant magnetic coupling. "
                    f"Geomagnetic effects heightened."
                ),
                "severity": "high",
                "actionable": True,
                "action_hint": "Sensitive individuals should practice self-care",
            })

        return events

    def _get_kp_status(self, kp: float) -> str:
        """Get human-readable Kp status."""
        if kp >= 9:
            return "G5 - Extreme"
        if kp >= 7:
            return "G4 - Severe"
        if kp >= 6:
            return "G3 - Strong"
        if kp >= 5:
            return "G2 - Moderate"
        if kp >= 4:
            return "G1 - Minor"
        return "Quiet"

    def _get_recommendation(self, kp: float) -> str:
        """Get recommendation based on Kp index."""
        if kp >= 7:
            return (
                "High geomagnetic activity. Sensitive individuals may experience "
                "fatigue, anxiety, or headaches. Ground yourself, avoid stress, "
                "get extra rest."
            )
        if kp >= 5:
            return "Moderate geomagnetic activity. You may feel more sensitive than usual. Practice self-care."
        return "Geomagnetic activity is quiet. Normal sensitivity expected."

    def _parse_recent_flares(self, flare_data: list) -> List[dict]:
        """Parse flares from last hour using 0.1-0.8nm flux."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        recent = []

        # NOAA GOES X-ray flux data provides two energy bands:
        # 0.05-0.4nm and 0.1-0.8nm (the standard for flare classification)
        for entry in flare_data:
            if entry.get("energy") != "0.1-0.8nm":
                continue

            try:
                time_tag = datetime.fromisoformat(entry["time_tag"].replace("Z", "+00:00"))
                if time_tag < one_hour_ago:
                    continue

                flux = entry.get("flux", 0)
                if flux >= 1e-4:
                    flare_class = "X"
                elif flux >= 1e-5:
                    flare_class = "M"
                elif flux >= 1e-6:
                    flare_class = "C"
                else:
                    continue  # B-class or lower ignored for events

                recent.append(
                    {
                        "time": entry["time_tag"],
                        "class": flare_class,
                        "flux": flux,
                        "label": f"{flare_class}-class Flare",
                    }
                )
            except (ValueError, KeyError):
                continue

        # Sort by flux descending and keep only unique classes for the hour summary
        # or just return the list sorted by time
        recent.sort(key=lambda x: x["time"], reverse=True)
        return recent

    def _parse_swpc_product_data(self, data_list: list, column_name: str) -> float:
        """Parse list-of-lists JSON from SWPC Products."""
        # Format:
        # [["time_tag", "bz_gsm", ...], ["2023-...", -5.4, ...]]
        if not data_list or len(data_list) < 2:
            return 0.0

        header = data_list[0]
        try:
            col_idx = header.index(column_name)
        except ValueError:
            return 0.0

        # Get latest valid data point (iterate backwards)
        # Sometimes latest is null?
        for row in reversed(data_list[1:]):
            val = row[col_idx]
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return 0.0

    def _calculate_storm_potential(self, bz: float, speed: float, density: float) -> str:
        """
        Estimate Storm Potential.
        Rule of Thumb: South Bz (-ve) + High Speed = High Potential.
        """
        # "E" value proxy (Electric Field = V * Bz)
        # Use abs(V * Bz) and check polarity

        if bz > 0:
            return "Low (North Bz)"

        # If Bz is South, check intensity
        ey = abs(speed * bz) * 1e-3  # mV/m approx

        if ey > 5 or (speed > 700 and bz < -5):
            return "Critical"
        if ey > 2 or (speed > 500 and bz < -3):
            return "High"
        if bz < -3:
            return "Moderate"

        return "Low"

    def _calculate_shield_integrity(self, bz: float, speed: float) -> str:
        """User-facing 'Shield Status'."""
        if bz < -10:
            return "CRITICAL FAILURE"
        if bz < -5 and speed > 500:
            return "CRACKED"
        if bz < -5:
            return "STRAINED"
        if speed > 600:
            return "BUFFETED"
        return "HOLDING"
