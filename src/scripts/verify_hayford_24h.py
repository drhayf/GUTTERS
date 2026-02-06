#!/usr/bin/env python3
"""
Verify EVERY hour for Hayford Ayirebi, July 23, 1999
Compare against Jovian Archive to ensure accuracy
"""
import sys
from datetime import date, time
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 80)
print("COMPLETE 24-HOUR VERIFICATION")
print("Hayford Ayirebi, July 23, 1999, Accra, Ghana")
print("Jovian Archive shows: PROJECTOR at 12:00")
print("=" * 80)

type_counts = {}

for hour in range(24):
    try:
        chart = calc._calculate_full_chart(
            name="Hayford",
            birth_date=date(1999, 7, 23),
            birth_time=time(hour, 0),
            latitude=5.6037,
            longitude=-0.1870,
            timezone="Africa/Accra"
        )

        hd_type = chart.type
        type_counts[hd_type] = type_counts.get(hd_type, 0) + 1

        # Show details for each hour
        sacral_defined = "Sacral" in chart.defined_centers
        throat_defined = "Throat" in chart.defined_centers

        # Get defined channels
        defined_channels = [ch.name for ch in chart.channels if ch.defined]

        marker = ""
        if hour == 12:
            marker = " ← NOON (Jovian shows Projector)"

        print(f"\n{hour:02}:00 → {hd_type:22} {marker}")
        print(f"       Sacral: {'DEFINED' if sacral_defined else 'undefined'}")
        print(f"       Throat: {'DEFINED' if throat_defined else 'undefined'}")
        print(f"       Channels: {', '.join(defined_channels[:3])}...")

    except Exception as e:
        print(f"\n{hour:02}:00 → ERROR: {e}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
for hd_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    percentage = (count / 24) * 100
    print(f"{hd_type:22} {count:2}/24 hours ({percentage:5.1f}%)")

print("\n" + "=" * 80)
print("CRITICAL VERIFICATION:")
print("=" * 80)
print("At 12:00 (noon), Jovian Archive shows: PROJECTOR")
calc_result = calc._calculate_full_chart(
    name='H',
    birth_date=date(1999, 7, 23),
    birth_time=time(12, 0),
    latitude=5.6037,
    longitude=-0.1870,
    timezone='Africa/Accra',
)
print(f"Our calculation at 12:00 shows: {calc_result.type}")
print("\nIf these don't match, there's still a bug in our gate/channel/type logic.")
print("=" * 80)
