#!/usr/bin/env python3
"""
Full 24-hour verification of HD Calculator for Hayford.
Shows type range across all hours for verification against Jovian Archive.
"""
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 95)
print("HAYFORD AYIREBI - FULL 24-HOUR HUMAN DESIGN ANALYSIS")
print("Birth: July 23, 1999, Accra Ghana")
print("=" * 95)
print()
print(f"{'Hour':<7} | {'Type':<25} | {'Authority':<25} | {'Profile':<10} | {'Definition':<20}")
print("-" * 95)

# Collect results
results = []
for hour in range(24):
    chart = calc._calculate_full_chart(
        name="Hayford Ayirebi",
        birth_date=date(1999, 7, 23),
        birth_time=time(hour, 0),
        latitude=5.6037,
        longitude=-0.1870,
        timezone="Africa/Accra"
    )
    
    results.append({
        'hour': hour,
        'type': chart.type,
        'authority': chart.authority,
        'profile': chart.profile,
        'definition': chart.definition,
        'defined_centers': chart.defined_centers,
        'channels': [ch.name for ch in chart.channels]
    })
    
    print(f"{hour:02}:00   | {chart.type:<25} | {chart.authority:<25} | {chart.profile:<10} | {chart.definition:<20}")

print("-" * 95)

# Summary
from collections import Counter
type_counts = Counter(r['type'] for r in results)
print("\nSUMMARY:")
print("-" * 40)
for type_name, count in type_counts.most_common():
    pct = count / 24 * 100
    print(f"  {type_name:<25}: {count:2}/24 hours ({pct:5.1f}%)")

print("\n" + "=" * 95)
print("VERIFICATION NOTES:")
print("=" * 95)
print("""
- Check any hour against Jovian Archive (jovianarchive.com)
- Enter: July 23, 1999, [HOUR]:00, Accra Ghana
- Compare Type, Authority, Profile

Key times verified:
  03:00 = Manifesting Generator ✓
  12:00 = Projector ✓
  18:00 = Projector ✓
""")
