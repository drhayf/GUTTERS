"""
Deterministic seed data generator for high-fidelity integration tests.

Generates realistic journal entries, observer findings, and tracking history
that match the exact schema the real system will produce.

This is NOT mocking - it's pre-populating the database with valid data
so we can test intelligence modules (Enhanced Synthesis, Hypothesis, Vector Search)
before Journal Module exists.
"""

import uuid
from datetime import datetime, timedelta
from typing import List


class SeedDataGenerator:
    """Generate deterministic, realistic seed data for testing."""

    @staticmethod
    def generate_journal_entries(
        user_id: int,
        days: int = 60,
        entries_per_week: int = 3
    ) -> List[dict]:
        """
        Generate realistic journal entries with detectable patterns.

        Patterns embedded:
        1. Sunday anxiety (temporal pattern)
        2. Headaches every 10th entry (solar storm correlation)
        3. Low energy during waning moon simulation (days 15-29 of 30-day cycle)
        4. Creative breakthroughs during new moon simulation (days 0-7)

        Args:
            user_id: User ID (for reference)
            days: How many days back to generate
            entries_per_week: Frequency (default 3 = Mon, Wed, Sat)

        Returns:
            List of journal entry dicts matching JournalEntry schema
        """
        entries = []
        start_date = datetime.utcnow() - timedelta(days=days)
        current_date = start_date
        entry_count = 0

        while current_date < datetime.utcnow():
            # Generate entries on Mon (0), Wed (2), Sat (5), Sun (6)
            if current_date.weekday() in [0, 2, 5, 6]:

                # PATTERN 1: Sunday anxiety (day_of_week pattern)
                if current_date.weekday() == 6:  # Sunday
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Feeling anxious about the upcoming week. Sunday blues hitting hard.",
                        "mood_score": 3,
                        "energy_score": 4,
                        "tags": ["anxiety", "stress"],
                        "themes": ["mental_health"]
                    }

                # PATTERN 2: Headaches on "storm days" (solar correlation)
                elif entry_count % 10 == 0:  # Every 10th entry simulates geomagnetic storm day
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Terrible headache today. Felt exhausted and couldn't concentrate.",
                        "mood_score": 4,
                        "energy_score": 3,
                        "tags": ["headache", "fatigue", "brain_fog"],
                        "themes": ["health"]
                    }

                # PATTERN 3: Low energy during "waning moon" (lunar correlation)
                # Simulate 30-day lunar cycle, days 15-29 = waning
                elif (entry_count % 30) in range(15, 29):
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Energy levels are really low today. Just want to rest and recharge.",
                        "mood_score": 5,
                        "energy_score": 4,
                        "tags": ["tired", "low_energy", "rest"],
                        "themes": ["health", "self_care"]
                    }

                # PATTERN 4: Creative breakthroughs during "new moon" (lunar correlation)
                elif (entry_count % 30) in range(0, 7):
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Had an amazing creative breakthrough! New ideas flowing. Feeling inspired and focused.",
                        "mood_score": 8,
                        "energy_score": 8,
                        "tags": ["creative", "inspired", "breakthrough", "focused"],
                        "themes": ["creativity", "work"]
                    }

                # PATTERN 5: Work stress (transit correlation - Saturn square Mars simulation)
                elif entry_count % 15 == 0:
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Work has been incredibly stressful. Conflicts with team. Feeling frustrated.",
                        "mood_score": 4,
                        "energy_score": 5,
                        "tags": ["stress", "work", "conflict", "frustration"],
                        "themes": ["work", "mental_health"]
                    }

                # NORMAL DAYS (no special pattern)
                else:
                    entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": current_date.isoformat(),
                        "text": "Regular day. Work was fine, nothing special. Feeling okay.",
                        "mood_score": 6,
                        "energy_score": 6,
                        "tags": [],
                        "themes": []
                    }

                entries.append(entry)
                entry_count += 1

            current_date += timedelta(days=1)

        return entries

    @staticmethod
    def generate_observer_findings(user_id: int) -> List[dict]:
        """
        Generate realistic Observer findings that would be detected from journal entries.

        These match patterns in generate_journal_entries().
        """
        return [
            {
                "pattern_type": "solar_symptom",
                "correlation": 0.82,
                "p_value": 0.01,
                "symptom": "headache",
                "finding": "User reports headaches during high geomagnetic activity (Kp > 5)",
                "confidence": 0.82,
                "data_points": 15,
                "detected_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_type": "lunar_phase",
                "phase": "waning",
                "mood_diff": -1.8,
                "energy_diff": -2.1,
                "finding": "User's energy drops during waning moon phase",
                "confidence": 0.75,
                "data_points": 12,
                "detected_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_type": "lunar_phase",
                "phase": "new",
                "mood_diff": 2.3,
                "energy_diff": 2.1,
                "finding": "User experiences creative breakthroughs during new moon phase",
                "confidence": 0.78,
                "data_points": 10,
                "detected_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_type": "day_of_week",
                "day": "Sunday",
                "mood_diff": -2.3,
                "finding": "User's mood significantly drops on Sundays",
                "confidence": 0.88,
                "data_points": 8,
                "detected_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_type": "transit_theme",
                "theme": "work",
                "transit": "Saturn square Mars",
                "frequency": 0.65,
                "finding": "User experiences work stress when Saturn squares natal Mars",
                "confidence": 0.65,
                "data_points": 7,
                "detected_at": datetime.utcnow().isoformat()
            }
        ]

    @staticmethod
    def generate_tracking_history(user_id: int, days: int = 60) -> dict:
        """
        Generate tracking history (solar, lunar, transits) that aligns with journal patterns.

        Solar: Storms every 10 days (matches headache pattern)
        Lunar: 30-day cycle simulation
        Transits: Periodic Saturn-Mars square
        """
        history = {
            "solar_tracking": [],
            "lunar_tracking": [],
            "transit_tracking": []
        }

        start_date = datetime.utcnow() - timedelta(days=days)
        current_date = start_date
        day_count = 0

        while current_date < datetime.utcnow():
            # SOLAR: Storm every 10 days (aligns with headache entries)
            if day_count % 10 == 0:
                kp_index = 7.0  # G4 storm
                geomagnetic_storm = True
            else:
                kp_index = 2.0  # Quiet
                geomagnetic_storm = False

            history["solar_tracking"].append({
                "timestamp": current_date.isoformat(),
                "data": {
                    "kp_index": kp_index,
                    "kp_status": "G4 - Severe" if geomagnetic_storm else "Quiet",
                    "geomagnetic_storm": geomagnetic_storm,
                    "solar_flares": []
                }
            })

            # LUNAR: 30-day cycle
            day_in_cycle = day_count % 30

            if day_in_cycle < 7:
                phase_name = "New Moon"
                illumination = day_in_cycle / 14  # 0 to 0.5
            elif day_in_cycle < 15:
                phase_name = "Waxing Gibbous"
                illumination = 0.5 + (day_in_cycle - 7) / 16
            elif day_in_cycle < 22:
                phase_name = "Full Moon"
                illumination = 1.0 - (day_in_cycle - 15) / 14
            else:
                phase_name = "Waning Crescent"
                illumination = (30 - day_in_cycle) / 16

            history["lunar_tracking"].append({
                "timestamp": current_date.isoformat(),
                "data": {
                    "phase_name": phase_name,
                    "illumination": illumination,
                    "sign": "Aries",  # Simplified
                    "is_new_moon": day_in_cycle < 2,
                    "is_full_moon": 14 <= day_in_cycle < 16
                }
            })

            # TRANSITS: Saturn square Mars every 15 days (aligns with work stress)
            if day_count % 15 == 0:
                transit_active = True
            else:
                transit_active = False

            if transit_active:
                history["transit_tracking"].append({
                    "timestamp": current_date.isoformat(),
                    "data": {
                        "applying_transits": [
                            {
                                "transit_planet": "Saturn",
                                "natal_planet": "Mars",
                                "aspect": "square",
                                "orb": 0.5,
                                "exact": True,
                                "interpretation": "Saturn creates tension with natal Mars"
                            }
                        ]
                    }
                })

            current_date += timedelta(days=1)
            day_count += 1

        return history
