from datetime import datetime, timedelta, timezone, UTC
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class Observer:
    """
    Pattern detection and correlation analysis engine.

    Watches:
    - Journal entries (mood, sentiment)
    - Cosmic events (solar storms, lunar phases, transits)
    - User behavior patterns

    Detects:
    - Correlations (cosmic events → user state)
    - Temporal patterns (time-based trends)
    - Threshold patterns (certain events trigger responses)
    """

    # Minimum data requirements
    MIN_SOLAR_DAYS = 30
    MIN_SOLAR_JOURNAL_ENTRIES = 10

    MIN_LUNAR_DAYS = 60
    MIN_LUNAR_JOURNAL_ENTRIES = 15

    MIN_TRANSIT_DAYS = 90
    MIN_TRANSIT_JOURNAL_ENTRIES = 20

    MIN_TIME_PATTERN_DAYS = 60
    MIN_TIME_PATTERN_ENTRIES = 30

    def __init__(self):
        self.correlation_threshold = 0.6  # Minimum correlation to report

    # === CORRELATION DETECTION ===

    async def detect_solar_correlations(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detect correlations between solar activity and user state.

        Example: "User reports headaches when Kp index > 5"
        """
        # Check preference
        if not await self._is_observer_enabled(user_id, db):
            return []

        # Get solar tracking history
        solar_events = await self._get_solar_history(user_id, db, days=self.MIN_SOLAR_DAYS)

        # Get journal entries with mood/symptoms
        journal_entries = await self._get_journal_entries(user_id, db, days=self.MIN_SOLAR_DAYS)

        logger.info(
            f"[Observer] Solar detection for user {user_id}: {len(solar_events)} events, {len(journal_entries)} entries"
        )

        if len(solar_events) < self.MIN_SOLAR_DAYS or len(journal_entries) < self.MIN_SOLAR_JOURNAL_ENTRIES:
            logger.warning(f"[Observer] Insufficient data for user {user_id}")
            return []

        correlations = []

        # Test: Kp index vs. reported symptoms
        kp_values = [event["kp_index"] for event in solar_events]

        # For each symptom type, check correlation
        symptoms = ["headache", "anxiety", "fatigue", "insomnia", "irritability"]

        for symptom in symptoms:
            # Get symptom occurrences aligned with Kp data
            symptom_scores = self._align_symptom_scores(journal_entries, solar_events, symptom)

            if len(symptom_scores) < self.MIN_SOLAR_DAYS:
                continue

            try:
                # Calculate Pearson correlation
                correlation, p_value = stats.pearsonr(kp_values, symptom_scores)

                # Robust error handling
                if np.isnan(correlation) or np.isnan(p_value):
                    continue

                if abs(correlation) >= self.correlation_threshold and p_value < 0.05:
                    logger.info(f"[Observer] Found {symptom} correlation: {correlation:.2f} (p={p_value:.4f})")
                    correlations.append(
                        {
                            "pattern_type": "solar_symptom",
                            "correlation": float(correlation),
                            "p_value": float(p_value),
                            "symptom": symptom,
                            "finding": f"User reports {symptom} during high geomagnetic activity (Kp > 5)",
                            "confidence": self._calculate_confidence(correlation, p_value, len(symptom_scores)),
                            "data_points": len(symptom_scores),
                            "detected_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                else:
                    logger.debug(
                        f"[Observer] {symptom} correlation {correlation:.2f} (p={p_value:.4f}) below threshold"
                    )
            except (ValueError, ZeroDivisionError) as e:
                logger.warning(f"[Observer] Correlation error for user {user_id}: {e}")
                continue

        return correlations

    async def detect_lunar_correlations(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detect correlations between lunar phases and user patterns.
        """
        if not await self._is_observer_enabled(user_id):
            return []

        lunar_events = await self._get_lunar_history(user_id, db, days=self.MIN_LUNAR_DAYS)
        journal_entries = await self._get_journal_entries(user_id, db, days=self.MIN_LUNAR_DAYS)

        if len(lunar_events) < self.MIN_LUNAR_DAYS or len(journal_entries) < self.MIN_LUNAR_JOURNAL_ENTRIES:
            return []

        correlations = []

        # Group by lunar phase
        phase_groups = {
            "new": [],  # New moon (0-45 deg)
            "waxing": [],  # Waxing (45-135 deg)
            "full": [],  # Full moon (135-225 deg)
            "waning": [],  # Waning (225-360 deg)
        }

        for entry in journal_entries:
            # Find corresponding lunar phase
            lunar_data = self._find_closest_lunar_data(entry["timestamp"], lunar_events)
            if not lunar_data:
                continue

            phase = lunar_data.get("phase_name", "")

            # Group entries by phase
            if "New" in phase or "Crescent" in phase:
                phase_groups["new"].append(entry)
            elif "Waxing" in phase or "First Quarter" in phase:
                phase_groups["waxing"].append(entry)
            elif "Full" in phase or "Gibbous" in phase:
                phase_groups["full"].append(entry)
            else:
                phase_groups["waning"].append(entry)

        # Analyze mood/energy by phase
        for phase, entries in phase_groups.items():
            if len(entries) < 5:
                continue

            avg_mood = np.mean([e.get("mood_score", 5) for e in entries])
            avg_energy = np.mean([e.get("energy_score", 5) for e in entries])

            # Compare to overall average
            all_mood = np.mean([e.get("mood_score", 5) for e in journal_entries])
            all_energy = np.mean([e.get("energy_score", 5) for e in journal_entries])

            mood_diff = avg_mood - all_mood
            energy_diff = avg_energy - all_energy

            # Significant difference?
            if abs(mood_diff) > 1.5 or abs(energy_diff) > 1.5:
                correlations.append(
                    {
                        "pattern_type": "lunar_phase",
                        "phase": phase,
                        "mood_diff": float(mood_diff),
                        "energy_diff": float(energy_diff),
                        "finding": self._format_lunar_finding(phase, mood_diff, energy_diff),
                        "confidence": min(abs(mood_diff) / 3, abs(energy_diff) / 3, 1.0),
                        "data_points": len(entries),
                        "detected_at": datetime.now(UTC).isoformat(),
                    }
                )

        return correlations

    async def detect_transit_correlations(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detect correlations between specific transits and user events.
        """
        if not await self._is_observer_enabled(user_id):
            return []

        # Get transit history
        transit_events = await self._get_transit_history(user_id, db, days=self.MIN_TRANSIT_DAYS)

        # Get journal entries
        journal_entries = await self._get_journal_entries(user_id, db, days=self.MIN_TRANSIT_DAYS)

        if not transit_events or not journal_entries:
            return []

        correlations = []

        # Group journal entries by themes
        themes = self._extract_themes(journal_entries)

        # For each theme, check if specific transits were active
        for theme, theme_entries in themes.items():
            # Find which transits were active during these entries
            active_transits = []

            for entry in theme_entries:
                transits_at_time = self._get_transits_at_time(entry["timestamp"], transit_events)
                active_transits.extend(transits_at_time)

            # Count transit frequency
            transit_counts = {}
            for transit in active_transits:
                key = f"{transit.get('transit_planet')} {transit.get('aspect')} {transit.get('natal_planet')}"
                transit_counts[key] = transit_counts.get(key, 0) + 1

            # If a transit appears significantly often with this theme
            for transit_key, count in transit_counts.items():
                frequency = count / len(theme_entries)

                if frequency >= 0.5:  # Transit present in 50%+ of theme entries
                    correlations.append(
                        {
                            "pattern_type": "transit_theme",
                            "theme": theme,
                            "transit": transit_key,
                            "frequency": frequency,
                            "finding": f"User experiences {theme} themes when {transit_key} is active",
                            "confidence": frequency,
                            "data_points": len(theme_entries),
                            "detected_at": datetime.now(UTC).isoformat(),
                        }
                    )

        return correlations

    # === TEMPORAL PATTERN DETECTION ===

    async def detect_time_based_patterns(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detect patterns based on time of day, day of week, etc.
        """
        if not await self._is_observer_enabled(user_id):
            return []

        journal_entries = await self._get_journal_entries(user_id, db, days=self.MIN_TIME_PATTERN_DAYS)

        if len(journal_entries) < self.MIN_TIME_PATTERN_ENTRIES:
            return []

        patterns = []

        # Group by day of week
        day_groups = {day: [] for day in range(7)}  # 0=Monday, 6=Sunday

        for entry in journal_entries:
            ts = datetime.fromisoformat(str(entry["timestamp"]))
            day = ts.weekday()
            day_groups[day].append(entry)

        # Analyze mood by day
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        avg_moods = {}

        for day, entries in day_groups.items():
            if len(entries) >= 3:
                avg_mood = np.mean([e.get("mood_score", 5) for e in entries])
                avg_moods[day] = avg_mood

        # Find outliers (days significantly different from average)
        if avg_moods:
            overall_avg = np.mean(list(avg_moods.values()))

            for day, avg_mood in avg_moods.items():
                diff = avg_mood - overall_avg

                if abs(diff) > 1.5:
                    patterns.append(
                        {
                            "pattern_type": "day_of_week",
                            "day": day_names[day],
                            "mood_diff": float(diff),
                            "finding": f"User's mood {'improves' if diff > 0 else 'drops'} on {day_names[day]}s",
                            "confidence": min(abs(diff) / 3, 1.0),
                            "data_points": len(day_groups[day]),
                            "detected_at": datetime.now(UTC).isoformat(),
                        }
                    )

        return patterns

    # === QUESTION GENERATION ===

    def generate_questions(self, findings: List[Dict[str, Any]]) -> List[str]:
        """
        Generate questions to ask user based on findings.
        """
        questions = []

        for finding in findings:
            if finding["pattern_type"] == "solar_symptom":
                symptom = finding["symptom"]
                questions.append(
                    f"I've noticed you might experience {symptom} during geomagnetic storms. "
                    f"Did you feel any {symptom} in the last few days? "
                    f"(There was a G{int(finding.get('kp_index', 5)) // 2} storm recently.)"
                )

            elif finding["pattern_type"] == "lunar_phase":
                phase = finding["phase"]
                mood_diff = finding.get("mood_diff", 0)
                if mood_diff < 0:
                    questions.append(
                        f"How do you typically feel during {phase} moon phases? "
                        f"I'm seeing a pattern of lower mood during this time."
                    )
                else:
                    questions.append(
                        f"Do you feel more energized during {phase} moon phases? "
                        f"Your journal suggests you do well during this time."
                    )

            elif finding["pattern_type"] == "transit_theme":
                transit = finding["transit"]
                theme = finding["theme"]
                questions.append(
                    f"When you experience {theme}, have you noticed any astrological patterns? "
                    f"I see {transit} is often active during these times."
                )

        return questions

    # === HELPER METHODS ===

    async def _is_observer_enabled(self, user_id: int, db: AsyncSession) -> bool:
        """Check if Observer is enabled in user preferences."""
        from src.app.models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile and profile.data:
            return profile.data.get("preferences", {}).get("observer_enabled", True)

        return True

    async def _get_solar_history(self, user_id: int, db: AsyncSession, days: int) -> List[Dict]:
        """Get solar tracking history from UserProfile."""
        from src.app.models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile or not profile.data or "tracking_history" not in profile.data:
            return []

        solar_history = profile.data["tracking_history"].get("solar_tracking", [])

        # Filter by date and parse
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        parsed_history = []

        for entry in solar_history:
            try:
                ts_str = entry["timestamp"]
                if not ts_str.endswith("Z") and "+" not in ts_str:
                    ts_str += "Z"
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    parsed_history.append(
                        {
                            "timestamp": ts,
                            "kp_index": float(entry["data"].get("kp_index", 0)),
                            "geomagnetic_storm": entry["data"].get("geomagnetic_storm", False),
                        }
                    )
            except (ValueError, TypeError):
                continue

        return parsed_history

    async def _get_lunar_history(self, user_id: int, db: AsyncSession, days: int) -> List[Dict]:
        """Get lunar tracking history from UserProfile."""
        from src.app.models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile or not profile.data or "tracking_history" not in profile.data:
            return []

        lunar_history = profile.data["tracking_history"].get("lunar_tracking", [])

        cutoff = datetime.now(UTC) - timedelta(days=days)
        parsed_history = []

        for entry in lunar_history:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    parsed_history.append(
                        {
                            "timestamp": ts,
                            "phase_name": entry["data"].get("phase_name", ""),
                            "sign": entry["data"].get("sign", ""),
                            "longitude": float(entry["data"].get("longitude", 0)),
                        }
                    )
            except (ValueError, TypeError):
                continue

        return parsed_history

    async def _get_transit_history(self, user_id: int, db: AsyncSession, days: int) -> List[Dict]:
        """Get transit tracking history from UserProfile."""
        from src.app.models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile or not profile.data or "tracking_history" not in profile.data:
            return []

        history = profile.data["tracking_history"].get("transit_tracking", [])

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        parsed_history = []

        for entry in history:
            try:
                ts_str = entry["timestamp"]
                if not ts_str.endswith("Z") and "+" not in ts_str:
                    ts_str += "Z"
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    # Assuming 'active_transits' list in data
                    active = entry["data"].get("active_transits", [])
                    parsed_history.append({"timestamp": ts, "active_transits": active})
            except (ValueError, TypeError):
                continue

        return parsed_history

    async def _get_journal_entries(self, user_id: int, db: AsyncSession, days: int) -> List[Dict]:
        """Get journal entries from database."""
        from src.app.models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile or not profile.data:
            return []

        # Get journal entries from profile.data
        entries = profile.data.get("journal_entries", [])

        # Filter by date range
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = []
        for e in entries:
            try:
                ts_str = e["timestamp"]
                if not ts_str.endswith("Z") and "+" not in ts_str:
                    ts_str += "Z"
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    e_copy = e.copy()
                    e_copy["timestamp"] = ts  # Use datetime object
                    filtered.append(e_copy)
            except (ValueError, TypeError):
                continue

        return filtered

    def _align_symptom_scores(self, journal_entries: List[Dict], solar_events: List[Dict], symptom: str) -> List[float]:
        """
        Align symptom mentions with solar event data.
        """
        scores = []

        for event in solar_events:
            event_time = event["timestamp"]

            # Find journal entries within 24 hours of event
            nearby_entries = [e for e in journal_entries if abs((e["timestamp"] - event_time).total_seconds()) < 86400]

            # Check if symptom mentioned
            symptom_present = any(symptom.lower() in e.get("text", "").lower() for e in nearby_entries)

            scores.append(1.0 if symptom_present else 0.0)

        return scores

    def _find_closest_lunar_data(self, target_time: datetime, lunar_history: List[Dict]) -> Optional[Dict]:
        """Find closest lunar data point to a timestamp."""
        if not lunar_history:
            return None

        # Assuming sorted history, but let's just find min distance
        closest = min(lunar_history, key=lambda x: abs((x["timestamp"] - target_time).total_seconds()))

        # Only use if within reasonable window (e.g. 24 hours)
        if abs((closest["timestamp"] - target_time).total_seconds()) < 86400:
            return closest

        return None

    def _get_transits_at_time(self, target_time: datetime, transit_history: List[Dict]) -> List[Dict]:
        """Get active transits at a given time."""
        if not transit_history:
            return []

        closest = min(transit_history, key=lambda x: abs((x["timestamp"] - target_time).total_seconds()))

        if abs((closest["timestamp"] - target_time).total_seconds()) < 86400:
            return closest.get("active_transits", [])

        return []

    def _calculate_confidence(self, correlation: float, p_value: float, data_points: int) -> float:
        """
        Calculate confidence score for a finding.
        """
        # Base confidence from correlation
        base = abs(correlation)

        # Adjust for statistical significance
        significance_factor = 1.0 - min(p_value, 0.05) / 0.05

        # Adjust for sample size (more data = higher confidence)
        sample_factor = min(data_points / 30, 1.0)

        confidence = base * (0.5 + 0.5 * significance_factor) * sample_factor

        return min(confidence, 1.0)

    def _extract_themes(self, journal_entries: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract themes from journal entries using simple keyword matching.
        """
        themes = {"relationship": [], "work": [], "health": [], "creativity": [], "anxiety": []}

        keywords = {
            "relationship": ["relationship", "partner", "love", "romance", "breakup"],
            "work": ["work", "job", "career", "project", "meeting", "boss"],
            "health": ["health", "sick", "pain", "tired", "energy"],
            "creativity": ["creative", "art", "writing", "project", "inspiration"],
            "anxiety": ["anxiety", "stress", "worry", "nervous", "panic"],
        }

        for entry in journal_entries:
            text = entry.get("text", "").lower()

            for theme, words in keywords.items():
                if any(word in text for word in words):
                    themes[theme].append(entry)

        # Remove empty themes
        return {k: v for k, v in themes.items() if v}

    def _format_lunar_finding(self, phase: str, mood_diff: float, energy_diff: float) -> str:
        """Format lunar correlation finding."""
        if mood_diff < -1.5:
            return f"User's mood tends to drop during {phase} moon phase"
        elif mood_diff > 1.5:
            return f"User's mood improves during {phase} moon phase"
        elif energy_diff < -1.5:
            return f"User's energy drops during {phase} moon phase"
        elif energy_diff > 1.5:
            return f"User's energy peaks during {phase} moon phase"
        return f"User shows different patterns during {phase} moon phase"
