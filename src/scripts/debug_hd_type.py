#!/usr/bin/env python3
"""
Test probabilistic type calculation with fixed gate mapping
Shows what types appear across all 24 hours of the day
"""
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 80)
print("PROBABILISTIC TYPE CALCULATION")
print("Hayford Ayirebi, July 23, 1999 (NO BIRTH TIME)")
print("Using FIXED gate-to-degree mapping")
print("=" * 80)

# Calculate chart without birth time (uses probabilistic calculation)
chart = calc.calculate_chart(
    name="Hayford Ayirebi",
    birth_date=date(1999, 7, 23),
    birth_time=None,  # No birth time!
    latitude=5.6037,
    longitude=-0.1870,
    timezone="Africa/Accra"
)

print(f"\n📊 RESULT:")
print(f"   Most Likely Type: {chart.type}")
print(f"   Confidence: {chart.type_confidence:.1%}" if chart.type_confidence else "   Confidence: N/A")
print(f"   Strategy: {chart.strategy}")
print(f"   Authority: {chart.authority}")

if chart.type_probabilities:
    print(f"\n🎯 TYPE PROBABILITIES ACROSS 24 HOURS:")
    for tp in chart.type_probabilities:
        bar = "█" * int(tp.probability * 30)
        print(f"   {tp.type:22} {tp.probability:5.1%} ({tp.hours_count:2}/24h) [{tp.confidence:8}] {bar}")

print(f"\n📝 Note: {chart.note}")

print("\n" + "=" * 80)
print("HOURLY BREAKDOWN (what type at each hour):")
print("=" * 80)

for hour in range(24):
    test_time = time(hour, 0)
    try:
        hourly_chart = calc._calculate_full_chart(
            name="Hayford",
            birth_date=date(1999, 7, 23),
            birth_time=test_time,
            latitude=5.6037,
            longitude=-0.1870,
            timezone="Africa/Accra"
        )
        # Show if this is different from Projector
        marker = "" if hourly_chart.type == "Projector" else "⚠️"
        print(f"   {hour:02}:00 → {hourly_chart.type:<22} {marker}")
    except Exception as e:
        print(f"   {hour:02}:00 → Error: {e}")

print("\n" + "=" * 80)
