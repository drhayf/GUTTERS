#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import date, time
from collections import Counter

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("Hayford Ayirebi, July 23, 1999, Accra")
print("Testing all 24 hours...\n")

types = []
for hour in range(24):
    chart = calc._calculate_full_chart(
        name="Hayford",
        birth_date=date(1999, 7, 23),
        birth_time=time(hour, 0),
        latitude=5.6037,
        longitude=-0.1870,
        timezone="Africa/Accra"
    )
    types.append((hour, chart.type))
    print(f"{hour:02}:00 = {chart.type}")

print("\nSummary:")
counter = Counter([t[1] for t in types])
for type_name, count in counter.most_common():
    print(f"{type_name}: {count}/24 hours ({count/24*100:.1f}%)")

print(f"\nAt 12:00 (Jovian shows Projector): {types[12][1]}")
