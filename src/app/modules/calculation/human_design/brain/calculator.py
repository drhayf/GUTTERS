"""
GUTTERS Human Design Calculator - Production Implementation

Complete Human Design chart calculation with verified logic.
Integrates ephemeris, mechanics, and configuration modules.

Source: Incorporates verified logic from dturkuler/humandesign_api (GPL-3.0)
Original author: dturkuler

Features:
- 88° solar arc Design calculation (verified against Jovian Archive)
- Complete type/authority/definition determination
- Profile and Incarnation Cross calculation
- Probabilistic calculations for unknown birth time
- Full gate/channel/center activation
"""

from datetime import date, time, datetime, timedelta
from typing import Any, Optional
from collections import Counter
import pytz

from ..schemas import HumanDesignChart, HDGate, HDChannel, TypeProbability, ChartSubject
from .ephemeris import get_ephemeris, EphemerisCalculator
from .mechanics import (
    get_channel_builder,
    get_type_determinator,
    get_authority_determinator,
    get_definition_calculator,
    get_profile_calculator,
    get_cross_calculator,
    ChannelBuilder,
    TypeDeterminator,
)
from . import constants
from src.app.modules.calculation.registry import CalculationModuleRegistry


@CalculationModuleRegistry.register(
    name="human_design",
    display_name="Human Design",
    description="Analyzing bodygraph, centers, and gates",
    weight=1,
    requires_birth_time=True,
    order=2,
    version="1.0.0",
)
class HumanDesignCalculator:
    """
    Production-ready Human Design calculator.

    Uses Swiss Ephemeris for astronomical precision.
    Integrates verified calculation logic for maximum accuracy.
    """

    def __init__(self):
        """Initialize calculator with all sub-modules."""
        self.ephemeris = get_ephemeris()
        self.channel_builder = get_channel_builder()
        self.type_determinator = get_type_determinator()
        self.authority_determinator = get_authority_determinator()
        self.definition_calculator = get_definition_calculator()
        self.profile_calculator = get_profile_calculator()
        self.cross_calculator = get_cross_calculator()

    # Expose GATE_TO_CENTER for backward compatibility
    GATE_TO_CENTER = constants.GATE_TO_CENTER

    async def calculate(
        self,
        name: str,
        birth_date: date,
        birth_time: time | None,
        latitude: float,
        longitude: float,
        timezone: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Registry-compatible entry point.
        """
        return self.calculate_natal_chart(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )

    def _get_timezone_offset(self, timezone_str: str, dt: datetime) -> float:
        """
        Get timezone offset in hours for a given datetime.

        Handles DST automatically.

        Args:
            timezone_str: Timezone string (e.g., "America/New_York")
            dt: datetime for which to calculate offset

        Returns:
            Offset in hours (e.g., -5.0 for EST)
        """
        try:
            tz = pytz.timezone(timezone_str)
            localized = tz.localize(dt)
            offset_seconds = localized.utcoffset().total_seconds()
            return offset_seconds / 3600
        except Exception:
            return 0.0

    def _calculate_full_chart(
        self, name: str, birth_date: date, birth_time: time, latitude: float, longitude: float, timezone: str
    ) -> HumanDesignChart:
        """
        Calculate complete HD chart with full birth time.

        Args:
            name: Person's name
            birth_date: Birth date
            birth_time: Birth time (required for full calculation)
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone string

        Returns:
            Complete HumanDesignChart
        """
        # Build datetime
        birth_dt = datetime(
            birth_date.year, birth_date.month, birth_date.day, birth_time.hour, birth_time.minute, birth_time.second
        )

        # Get timezone offset
        tz_offset = self._get_timezone_offset(timezone, birth_dt)

        # Convert to Julian date
        birth_jd = self.ephemeris.datetime_to_julian(birth_dt, tz_offset)

        # Calculate Design date (88° solar arc)
        design_jd = self.ephemeris.calculate_design_date(birth_jd)

        # Get planetary positions
        personality_positions = self.ephemeris.get_all_planetary_positions(birth_jd, "personality")
        design_positions = self.ephemeris.get_all_planetary_positions(design_jd, "design")

        # Convert to HDGate objects
        personality_gates = self._positions_to_gates(personality_positions)
        design_gates = self._positions_to_gates(design_positions)

        # Combine all gates for channel detection
        all_gate_numbers = [g.gate for g in personality_gates] + [g.gate for g in design_gates]

        # Find active channels and defined centers
        active_channels, defined_centers = self.channel_builder.find_active_channels(all_gate_numbers)

        # Build center connection graph
        connections = self.channel_builder.build_center_connections(active_channels)

        # Calculate type
        type_result = self.type_determinator.determine_type(defined_centers, connections)

        # Calculate authority
        authority_result = self.authority_determinator.determine_authority(defined_centers, connections)

        # Calculate definition
        definition_result = self.definition_calculator.calculate_definition(defined_centers, connections)

        # Extract Sun lines for profile
        personality_sun = next((p for p in personality_positions if p["planet"] == "Sun"), None)
        design_sun = next((p for p in design_positions if p["planet"] == "Sun"), None)

        profile_result = self.profile_calculator.calculate_profile(
            personality_sun["line"] if personality_sun else 1, design_sun["line"] if design_sun else 1
        )

        # Calculate Incarnation Cross
        personality_earth = next((p for p in personality_positions if p["planet"] == "Earth"), None)
        design_earth = next((p for p in design_positions if p["planet"] == "Earth"), None)

        cross_result = self.cross_calculator.calculate_cross(
            personality_sun["gate"] if personality_sun else 1,
            personality_earth["gate"] if personality_earth else 2,
            design_sun["gate"] if design_sun else 1,
            design_earth["gate"] if design_earth else 2,
            profile_result["cross_type"],
        )

        # Build channel objects
        channels = self._build_channel_objects(active_channels, all_gate_numbers)

        # Build undefined centers list
        undefined_centers = [c for c in constants.ALL_CENTERS if c not in defined_centers]

        return HumanDesignChart(
            subject=ChartSubject(
                name=name,
                birth_date=birth_date,
                birth_time=birth_time,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
            ),
            type=type_result["type"],
            strategy=type_result["strategy"],
            authority=authority_result["name"],
            profile=profile_result["name"],
            incarnation_cross=cross_result["name"],
            definition=definition_result["name"],
            personality_gates=personality_gates,
            design_gates=design_gates,
            channels=channels,
            defined_centers=list(defined_centers),
            undefined_centers=undefined_centers,
            accuracy="full",
            note=None,
            signature=type_result.get("signature"),
            not_self=type_result.get("not_self"),
        )

    def _positions_to_gates(self, positions: list[dict]) -> list[HDGate]:
        """Convert position dicts to HDGate objects."""
        gates = []
        for pos in positions:
            gates.append(
                HDGate(
                    planet=pos["planet"].replace("_", " "),
                    gate=pos["gate"],
                    line=pos["line"],
                    color=pos.get("color", 1),
                    tone=pos.get("tone", 1),
                    base=pos.get("base", 1),
                    sign="",
                    degree=pos["longitude"],
                )
            )
        return gates

    def _build_channel_objects(self, active_channels: list[tuple], all_gates: list[int]) -> list[HDChannel]:
        """Build HDChannel objects from active channel tuples."""
        channels = []

        for gate1, gate2 in active_channels:
            # Get channel name and theme
            channel_info = constants.CHANNEL_NAMES.get((gate1, gate2))
            if not channel_info:
                channel_info = constants.CHANNEL_NAMES.get((gate2, gate1), ("Unknown", ""))

            name, theme = channel_info

            channels.append(HDChannel(gates=(gate1, gate2), name=name, defined=True, theme=theme))

        return channels

    def _calculate_probabilistic_type(self, birth_date: date, latitude: float, longitude: float, timezone: str) -> dict:
        """
        Calculate type probabilities when birth time is unknown.

        Samples all 24 hours to determine probability distribution.

        Args:
            birth_date: Birth date
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone string

        Returns:
            Dict with most_likely type and probabilities
        """
        type_counts = Counter()
        data_points = []

        for hour in range(24):
            try:
                chart = self._calculate_full_chart(
                    name="Sample",
                    birth_date=birth_date,
                    birth_time=time(hour, 0),
                    latitude=latitude,
                    longitude=longitude,
                    timezone=timezone,
                )
                type_counts[chart.type] += 1
                data_points.append({"hour": hour, "type": chart.type, "defined_centers": chart.defined_centers})
            except Exception:
                continue

        if not type_counts:
            return {"most_likely": "Unknown", "confidence": 0.0, "probabilities": []}

        total = sum(type_counts.values())
        probabilities = []

        for type_name, count in type_counts.most_common():
            prob = count / total
            confidence = "certain" if prob >= 1.0 else "high" if prob >= 0.75 else "medium" if prob >= 0.5 else "low"

            probabilities.append(
                TypeProbability(value=type_name, probability=round(prob, 3), sample_count=count, confidence=confidence)
            )

        most_likely = type_counts.most_common(1)[0]

        return {
            "most_likely": most_likely[0],
            "confidence": most_likely[1] / total,
            "probabilities": probabilities,
            "data_points": data_points,
        }

    def calculate_natal_chart(
        self, name: str, birth_date: date, birth_time: Optional[time], latitude: float, longitude: float, timezone: str
    ) -> dict[str, Any]:
        """
        Calculate Human Design chart.

        This is the main entry point for HD calculations.

        Args:
            name: Person's name
            birth_date: Birth date
            birth_time: Birth time (None for probabilistic)
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone string

        Returns:
            Dict with chart data (astrology-compatible format)
        """
        if birth_time is not None:
            # Full calculation
            chart = self._calculate_full_chart(name, birth_date, birth_time, latitude, longitude, timezone)

            return {
                "subject": {
                    "name": name,
                    "birth_date": birth_date.isoformat(),
                    "birth_time": birth_time.isoformat(),
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone,
                },
                "type": chart.type,
                "strategy": chart.strategy,
                "authority": chart.authority,
                "profile": chart.profile,
                "incarnation_cross": chart.incarnation_cross,
                "definition": chart.definition,
                "personality_gates": [
                    {
                        "planet": g.planet,
                        "gate": g.gate,
                        "line": g.line,
                        "color": g.color,
                        "tone": g.tone,
                        "base": g.base,
                    }
                    for g in chart.personality_gates
                ],
                "design_gates": [
                    {
                        "planet": g.planet,
                        "gate": g.gate,
                        "line": g.line,
                        "color": g.color,
                        "tone": g.tone,
                        "base": g.base,
                    }
                    for g in chart.design_gates
                ],
                "channels": [{"gates": ch.gates, "name": ch.name, "defined": ch.defined} for ch in chart.channels],
                "defined_centers": chart.defined_centers,
                "undefined_centers": chart.undefined_centers,
                "signature": chart.signature,
                "not_self": chart.not_self,
                "accuracy": "full",
                "note": None,
            }
        else:
            # Probabilistic calculation
            prob_result = self._calculate_probabilistic_type(birth_date, latitude, longitude, timezone)

            # Get a sample chart for noon to show other properties
            sample_chart = self._calculate_full_chart(name, birth_date, time(12, 0), latitude, longitude, timezone)

            return {
                "subject": {
                    "name": name,
                    "birth_date": birth_date.isoformat(),
                    "birth_time": None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone,
                },
                "type": prob_result["most_likely"],
                "type_probabilities": [
                    {
                        "value": p.value,
                        "probability": p.probability,
                        "sample_count": p.sample_count,
                        "confidence": p.confidence,
                    }
                    for p in prob_result["probabilities"]
                ],
                "confidence": prob_result["confidence"],
                "strategy": sample_chart.strategy,
                "authority": sample_chart.authority,
                "profile": sample_chart.profile,
                "defined_centers": sample_chart.defined_centers,
                "accuracy": "probabilistic",
                "note": f"Most likely {prob_result['most_likely']} with {prob_result['confidence']:.0%} confidence",
            }

    def calculate_chart(
        self, name: str, birth_date: date, birth_time: Optional[time], latitude: float, longitude: float, timezone: str
    ) -> HumanDesignChart:
        """
        Calculate Human Design chart - Backward compatible API.

        Returns HumanDesignChart Pydantic model for use with existing
        test infrastructure and interpreters.

        Args:
            name: Person's name
            birth_date: Birth date
            birth_time: Birth time (None for probabilistic)
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone string

        Returns:
            HumanDesignChart Pydantic model
        """
        if birth_time is not None:
            # Full calculation with known birth time
            return self._calculate_full_chart(name, birth_date, birth_time, latitude, longitude, timezone)
        else:
            # Probabilistic calculation - unknown birth time
            return self._calculate_probabilistic_chart(name, birth_date, latitude, longitude, timezone)

    def _calculate_probabilistic_chart(
        self, name: str, birth_date: date, latitude: float, longitude: float, timezone: str
    ) -> HumanDesignChart:
        """
        Calculate probabilistic HD chart when birth time is unknown.

        Samples all 24 hours to determine type distribution,
        then uses noon sample for other chart properties.

        Returns HumanDesignChart with probabilistic type data.
        """
        # Get type probabilities
        prob_result = self._calculate_probabilistic_type(birth_date, latitude, longitude, timezone)

        # Get noon sample for baseline chart
        noon_chart = self._calculate_full_chart(name, birth_date, time(12, 0), latitude, longitude, timezone)

        # Build probabilistic chart
        type_probs = prob_result["probabilities"]
        most_likely = prob_result["most_likely"]
        confidence = prob_result["confidence"]

        return HumanDesignChart(
            subject=ChartSubject(
                name=name,
                birth_date=birth_date,
                birth_time=None,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
            ),
            type=most_likely,
            strategy=noon_chart.strategy,
            authority=noon_chart.authority,
            profile=noon_chart.profile,
            incarnation_cross=noon_chart.incarnation_cross,
            definition=noon_chart.definition,
            signature=noon_chart.signature,
            not_self=noon_chart.not_self,
            personality_gates=noon_chart.personality_gates,
            design_gates=noon_chart.design_gates,
            channels=noon_chart.channels,
            defined_centers=noon_chart.defined_centers,
            undefined_centers=noon_chart.undefined_centers,
            accuracy="probabilistic",
            note=f"Most likely {most_likely} with {confidence:.0%} confidence. Type varies across 24 hours.",
            type_confidence=confidence,
            type_probabilities=type_probs,
        )
