#!/usr/bin/env python3
"""
Get EXACT values for Hayford at a time that should be Generator
"""
import sys
from datetime import date, time
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

# 03:00 should be Generator (has Sacral defined via channel 2-14)
chart = calc._calculate_full_chart(
    name="Hayford Ayirebi",
    birth_date=date(1999, 7, 23),
    birth_time=time(3, 0),  # 03:00 AM
    latitude=5.6037,
    longitude=-0.1870,
    timezone="Africa/Accra"
)

print("=" * 80)
print("EXACT VALUES FOR JOVIAN ARCHIVE VERIFICATION")
print("=" * 80)
print("\nEnter these values into Jovian Archive:")
print("-" * 80)
print("Name:      Hayford Ayirebi")
print("Date:      July 23, 1999")
print("Time:      03:00 AM (3:00 AM)")
print("Location:  Accra, Ghana")
print("           Latitude: 5.6037° N")
print("           Longitude: 0.1870° W")
print("Timezone:  Africa/Accra (GMT+0)")
print("-" * 80)

print("\nOUR CALCULATION RESULT:")
print(f"Type: {chart.type}")
print(f"Strategy: {chart.strategy}")
print(f"Authority: {chart.authority}")
print(f"Profile: {chart.profile}")

print(f"\nDefined Centers: {', '.join(chart.defined_centers)}")
print(f"Undefined Centers: {', '.join(chart.undefined_centers)}")

print(f"\nKey Detail - Sacral Center: {'DEFINED' if 'Sacral' in chart.defined_centers else 'UNDEFINED'}")

print("\nDefined Channels:")
for ch in chart.channels:
    if ch.defined:
        g1, g2 = ch.gates
        c1 = calc.GATE_TO_CENTER.get(g1)
        c2 = calc.GATE_TO_CENTER.get(g2)
        sacral_marker = " ← DEFINES SACRAL!" if (c1 == "Sacral" or c2 == "Sacral") else ""
        print(f"  {ch.name:20} Gates {g1}-{g2} ({c1} ↔ {c2}){sacral_marker}")

print("\nTop Personality Gates:")
for g in chart.personality_gates[:6]:
    center = calc.GATE_TO_CENTER.get(g.gate)
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line} ({center})")

print("\nTop Design Gates:")
for g in chart.design_gates[:6]:
    center = calc.GATE_TO_CENTER.get(g.gate)
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line} ({center})")

print("\n" + "=" * 80)
print("EXPECTED JOVIAN RESULT:")
print("=" * 80)
print("If our calculation is correct, Jovian should show:")
print(f"  Type: {chart.type}")
print("  Sacral: DEFINED")
print("  Channel 2-14 (Evolution): DEFINED")
print("\nIf Jovian shows PROJECTOR instead, we have a bug!")
print("=" * 80)
