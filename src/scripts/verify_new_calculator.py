#!/usr/bin/env python3
"""
Full verification test for new HD calculator against Jovian Archive.

Tests Hayford Ayirebi at 03:00, 12:00, and 18:00.
"""
import sys
from datetime import date, time
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 80)
print("VERIFICATION: New HD Calculator vs Jovian Archive")
print("=" * 80)
print("\nTest Subject: Hayford Ayirebi, July 23, 1999, Accra Ghana")
print("Expected results from Jovian Archive:\n")
print("  03:00 = Manifesting Generator, Solar Plexus Authority")
print("  12:00 = Projector")
print("  18:00 = Projector (Design Moon should be Gate 9, NOT Gate 6)")
print("=" * 80)

test_cases = [
    (3, 0, "Manifesting Generator"),
    (12, 0, "Projector"),
    (18, 0, "Projector"),
]

all_passed = True

for hour, minute, expected_type in test_cases:
    print(f"\nTesting {hour:02}:{minute:02}...")

    try:
        chart = calc._calculate_full_chart(
            name="Hayford Ayirebi",
            birth_date=date(1999, 7, 23),
            birth_time=time(hour, minute),
            latitude=5.6037,
            longitude=-0.1870,
            timezone="Africa/Accra"
        )

        match = "✓" if chart.type == expected_type else "✗ MISMATCH!"
        all_passed = all_passed and (chart.type == expected_type)

        print(f"  Type: {chart.type} (expected: {expected_type}) {match}")
        print(f"  Authority: {chart.authority}")
        print(f"  Profile: {chart.profile}")
        print(f"  Defined Centers: {chart.defined_centers}")
        print(f"  Channels: {[ch.name for ch in chart.channels]}")

        # Check Design Moon specifically for 18:00
        if hour == 18:
            design_moon = next((g for g in chart.design_gates if g.planet == "Moon"), None)
            if design_moon:
                moon_match = "✓" if design_moon.gate == 9 else f"✗ (got Gate {design_moon.gate})"
                print(f"  Design Moon: Gate {design_moon.gate}.{design_moon.line} (expected Gate 9) {moon_match}")
                if design_moon.gate != 9:
                    all_passed = False

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✓ ALL TESTS PASSED! Calculator matches Jovian Archive.")
else:
    print("✗ SOME TESTS FAILED. Check implementation.")
print("=" * 80)
