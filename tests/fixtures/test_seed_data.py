"""
Tests for SeedDataGenerator.
"""
from tests.fixtures.seed_data import SeedDataGenerator


def test_generate_journal_entries():
    entries = SeedDataGenerator.generate_journal_entries(user_id=1, days=60)
    assert len(entries) > 20  # Roughly 3.5 per week for 8.5 weeks

    # Check for Sunday anxiety pattern
    sundays = [e for e in entries if "Sunday blues" in e['text']]
    assert len(sundays) > 0

    # Check for headache pattern
    headaches = [e for e in entries if "headache" in e['text'].lower()]
    assert len(headaches) > 0

def test_generate_observer_findings():
    findings = SeedDataGenerator.generate_observer_findings(user_id=1)
    assert len(findings) == 5
    assert findings[0]['pattern_type'] == "solar_symptom"

def test_generate_tracking_history():
    history = SeedDataGenerator.generate_tracking_history(user_id=1, days=60)
    assert "solar_tracking" in history
    assert "lunar_tracking" in history
    assert "transit_tracking" in history
    assert len(history["solar_tracking"]) == 60
