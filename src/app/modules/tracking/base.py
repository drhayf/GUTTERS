# src/app/modules/tracking/base.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from typing import Optional, Any, List, Dict
from pydantic import BaseModel


class TrackingData(BaseModel):
    """Base model for tracking data."""

    timestamp: datetime
    source: str
    data: dict
    significant_events: List[str] = []


class TrackingResult(BaseModel):
    """Standardized result wrapper for caching."""

    module: str
    current_data: Dict[str, Any]
    comparison: Dict[str, Any]
    significant_events: List[str]
    updated_at: str


class BaseTrackingModule(ABC):
    """
    Base class for all tracking modules.

    Tracking modules:
    - Fetch real-time cosmic data
    - Compare to user's natal chart
    - Detect significant events
    - Trigger synthesis when needed
    """

    # Subclasses must define
    module_name: str
    update_frequency: str  # "hourly", "daily", "weekly"

    @abstractmethod
    async def fetch_current_data(self) -> TrackingData:
        """Fetch current cosmic data from external source."""
        pass

    @abstractmethod
    async def compare_to_natal(self, user_id: int, current_data: TrackingData) -> dict:
        """Compare current state to user's natal chart."""
        pass

    @abstractmethod
    def detect_significant_events(
        self,
        current_data: TrackingData,
        previous_data: Optional[TrackingData],
        comparison: Optional[dict] = None,
    ) -> List[str]:
        """Detect events that should trigger synthesis."""
        pass

    async def _store_in_history(self, user_id: int, data: TrackingData) -> None:
        """Store tracking data point in UserProfile for Observer analysis."""
        from src.app.core.db.database import async_get_db
        from src.app.models.user_profile import UserProfile
        from sqlalchemy import select

        async for db in async_get_db():
            result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            profile = result.scalar_one_or_none()

            if not profile:
                return

            # Initialize tracking_history structure
            if "tracking_history" not in profile.data:
                profile.data["tracking_history"] = {}

            if self.module_name not in profile.data["tracking_history"]:
                profile.data["tracking_history"][self.module_name] = []

            # Append current data point
            profile.data["tracking_history"][self.module_name].append(
                {"timestamp": data.timestamp.isoformat(), "data": data.data}
            )

            # Trim to last 90 days (keep history manageable)
            cutoff = datetime.now(UTC) - timedelta(days=90)

            def get_aware_dt(ts_str):
                dt = datetime.fromisoformat(ts_str)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=UTC)
                return dt

            profile.data["tracking_history"][self.module_name] = [
                entry
                for entry in profile.data["tracking_history"][self.module_name]
                if get_aware_dt(entry["timestamp"]) > cutoff
            ]

            # Mark as modified to ensure persistence
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(profile, "data")

            # --- High-Fidelity Telemetry ---
            # Also persist to CosmicConditions table for time-series analysis
            from src.app.models.cosmic_conditions import CosmicConditions

            # Map module_name to condition_type
            condition_type_map = {
                "solar_tracking": "solar",
                "lunar_tracking": "lunar",
                "transit_tracking": "planetary",
            }
            c_type = condition_type_map.get(self.module_name, "other")

            # Create telemetry record
            telemetry = CosmicConditions(
                condition_type=c_type,
                timestamp=data.timestamp,
                source=data.source,
                data=data.data,
            )
            db.add(telemetry)

            await db.commit()

    def _get_update_interval(self) -> timedelta:
        """Get update interval as timedelta."""
        if self.update_frequency == "hourly":
            return timedelta(hours=1)
        if self.update_frequency == "daily":
            return timedelta(days=1)
        if self.update_frequency == "weekly":
            return timedelta(weeks=1)
        return timedelta(days=1)

    async def update(self, user_id: int) -> dict:
        """
        Standard update cycle:
        1. Check cache for recent update
        2. Fetch current data (if needed)
        3. Compare to natal
        4. Detect significant events
        5. Store in cache
        6. Trigger synthesis if needed
        """
        from src.app.core.memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        # Check for cached fresh data to avoid API rate limits
        last_update_key = f"tracking:{self.module_name}:last_update_timestamp:{user_id}"
        # Use get() for simple strings/JSON
        last_update_str = await memory.get(last_update_key)

        if last_update_str:
            try:
                last_time = datetime.fromisoformat(last_update_str)
                if (datetime.now(UTC) - last_time) < self._get_update_interval():
                    # Data is fresh enough, return cached result if available
                    cached_key = f"tracking:{self.module_name}:last_result:{user_id}"
                    cached = await memory.get(cached_key)
                    if cached:
                        return cached
            except (ValueError, TypeError):
                # Invalid timestamp in cache, ignore
                pass

        # Fetch current data
        current = await self.fetch_current_data()

        # Store in history for Observer
        await self._store_in_history(user_id, current)

        # Get previous data from cache for event detection
        previous_key = f"tracking:{self.module_name}:previous_data:{user_id}"
        # Use get() as it auto-parses JSON to dict
        previous_dict = await memory.get(previous_key)
        previous = TrackingData(**previous_dict) if previous_dict else None

        # Compare to natal
        comparison = await self.compare_to_natal(user_id, current)

        # Detect events
        events = self.detect_significant_events(current, previous, comparison)

        # Persist current data as previous for next cycle
        await memory.set(previous_key, current.model_dump(mode="json"), ttl=86400 * 7)

        # Update timestamp of successful fetch
        await memory.set(last_update_key, datetime.now(UTC).isoformat(), ttl=86400)

        # Trigger synthesis if significant events detected
        if events:
            from src.app.core.memory import get_orchestrator, SynthesisTrigger
            from src.app.protocol.packet import ProgressionPacket, Packet
            from src.app.protocol import events as event_types
            from src.app.core.events.bus import get_event_bus

            orchestrator = await get_orchestrator()
            event_bus = get_event_bus()

            # Check User Preferences
            # We need to fetch the profile's preference section
            # Stored in "preferences" key of UserProfile.data
            prefs_data = await memory.get_module_output(user_id, "preferences")

            # Helper to check (logic mirrors UserProfile.get_notification_preference)
            def check_pref(cat: str) -> bool:
                if not prefs_data:
                    return True
                return prefs_data.get("notifications", {}).get(cat, True)

            base_category = "general"
            if self.module_name == "solar_tracking":
                base_category = "solar"
            elif self.module_name == "lunar_tracking":
                base_category = "lunar"
            elif self.module_name == "transit_tracking":
                base_category = "transits"

            # Map events to synthesis triggers
            trigger_map = {
                "solar_storm": SynthesisTrigger.SOLAR_STORM_DETECTED,
                "lunar_phase": SynthesisTrigger.LUNAR_PHASE_CHANGE,
                "transit_exact": SynthesisTrigger.TRANSIT_EXACT,
            }

            # Map events to granular notification event types
            notification_event_map = {
                # Solar events
                "solar_storm": event_types.COSMIC_SOLAR_ALERT,
                "geomagnetic_storm": event_types.COSMIC_SOLAR_ALERT,
                "shield_critical": event_types.COSMIC_SOLAR_ALERT,
                # Lunar events
                "voc_start": event_types.COSMIC_LUNAR_VOC_START,
                "voc_end": event_types.COSMIC_LUNAR_VOC_END,
                "lunar_phase": event_types.COSMIC_LUNAR_PHASE,
                "full_moon": event_types.COSMIC_LUNAR_PHASE,
                "new_moon": event_types.COSMIC_LUNAR_PHASE,
                # Transit events
                "retrograde_start": event_types.COSMIC_RETROGRADE_START,
                "retrograde_end": event_types.COSMIC_RETROGRADE_END,
                "planet_station": event_types.COSMIC_PLANET_STATION,
                "transit_exact": event_types.COSMIC_TRANSIT_EXACT,
                "ingress": event_types.COSMIC_INGRESS,
            }

            for event in events:
                # Granular checks could happen here if we had event-specific categories
                # For now, module-level check
                if not check_pref(base_category):
                    # Skip LLM/Synthesis for this event if user opted out
                    continue

                # Trigger synthesis if applicable
                trigger = trigger_map.get(event)
                if trigger:
                    await orchestrator.trigger_synthesis(user_id, trigger_type=trigger, background=True)

                # ===================================================================
                # PUBLISH NOTIFICATION EVENT
                # This enables the push notification system to alert the user
                # ===================================================================
                notification_event_type = notification_event_map.get(event)
                if notification_event_type:
                    # Build rich payload from current data and comparison
                    notification_payload = {
                        "event_name": event,
                        "module": self.module_name,
                        **current.data,  # Include all tracking data (kp_index, moon_phase, etc.)
                    }

                    # Add comparison data if present
                    if comparison:
                        notification_payload.update(comparison)

                    notification_packet = Packet(
                        source=self.module_name,
                        event_type=notification_event_type,
                        payload=notification_payload,
                        user_id=str(user_id),
                    )
                    await event_bus.publish_packet(notification_packet)

            # Passive Environmental XP
            category = (
                "VITALITY"
                if self.module_name == "solar_tracking"
                else "INTELLECT"
                if self.module_name == "transit_tracking"
                else "SYNC"
            )
            reason = events[0] if len(events) == 1 else f"Cosmic Integration: {len(events)} events"

            packet = ProgressionPacket(
                source=self.module_name,
                event_type=event_types.PROGRESSION_EXPERIENCE_GAIN,
                payload={"tracking_events": events},
                user_id=str(user_id),
                amount=5,  # Standard passive XP
                reason=reason,
                category=category,
            )
            from src.app.core.events.bus import get_event_bus

            await get_event_bus().publish_packet(packet)

        # Create result object
        result_model = TrackingResult(
            module=self.module_name,
            current_data=current.model_dump(mode="json"),
            comparison=comparison,
            significant_events=events,
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Serialize to dict with JSON-compatible types (handling datetimes)
        result_dict = result_model.model_dump(mode="json")

        # Cache the full result
        await memory.set(f"tracking:{self.module_name}:last_result:{user_id}", result_dict, ttl=86400)

        return result_dict
