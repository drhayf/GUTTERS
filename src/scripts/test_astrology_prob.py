#!/usr/bin/env python3
"""
Test full probabilistic Astrology calculation
Shows rising sign probabilities, planet stability, and aspect stability
"""
import sys
from datetime import date
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.astrology.brain.calculator import calculate_natal_chart

print("=" * 80)
print("FULL PROBABILISTIC ASTROLOGY CALCULATION")
print("John Doe, May 15, 1990, San Francisco (NO BIRTH TIME)")
print("=" * 80)

# Calculate chart without birth time
chart = calculate_natal_chart(
    name="John Doe",
    birth_date=date(1990, 5, 15),
    birth_time=None,  # No birth time!
    latitude=37.7749,
    longitude=-122.4194,
    timezone="America/Los_Angeles"
)

print(f"\nAccuracy: {chart['accuracy']}")
print(f"Sun: {chart['planets'][0]['sign']} {chart['planets'][0]['degree']:.1f}")
print(f"Moon: {chart['planets'][1]['sign']} {chart['planets'][1]['degree']:.1f}")

print("\n--- RISING SIGN PROBABILITIES ---")
if chart.get('ascendant'):
    print(f"Most Likely: {chart['ascendant']['sign']} ({chart.get('rising_confidence', 0):.0%})")

if chart.get('rising_probabilities'):
    for rp in chart['rising_probabilities'][:5]:  # Top 5
        bar = "#" * int(rp['probability'] * 30)
        print(f"  {rp['sign']:12} {rp['probability']:5.1%} ({rp['hours_count']:2}/24h) {bar}")

print("\n--- PLANET STABILITY ---")
if chart.get('planet_stability'):
    for ps in chart['planet_stability'][:5]:  # Top 5 planets
        status = "CERTAIN" if ps['sign_stable'] else "VARIES"
        print(f"  {ps['planet']:10} {ps['sign']:12} [{status}] {ps['note']}")

print("\n--- ASPECT STABILITY (certain aspects) ---")
if chart.get('aspect_stability'):
    certain = [a for a in chart['aspect_stability'] if a['stable']]
    for asp in certain[:8]:
        print(f"  {asp['planet1']:8} {asp['aspect_type']:12} {asp['planet2']:8} (certain)")

print(f"\nNote: {chart.get('note', 'N/A')}")
print("=" * 80)
