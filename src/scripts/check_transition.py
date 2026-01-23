#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

# Check transition hours
h3 = calc._calculate_full_chart('H', date(1999,7,23), time(3,0), 5.6037, -0.1870, 'Africa/Accra')
h4 = calc._calculate_full_chart('H', date(1999,7,23), time(4,0), 5.6037, -0.1870, 'Africa/Accra')

print("TRANSITION: 03:00 (Generator) → 04:00 (Projector)")
print("="*60)

print(f"\n03:00:")
print(f"  Type: {h3.type}")
print(f"  Sacral defined: {'Sacral' in h3.defined_centers}")
print(f"  Defined channels:")
for ch in h3.channels:
    if ch.defined:
        g1, g2 = ch.gates
        c1 = calc.GATE_TO_CENTER.get(g1)
        c2 = calc.GATE_TO_CENTER.get(g2)
        marker = " ← SACRAL" if (c1 == "Sacral" or c2 == "Sacral") else ""
        print(f"    {ch.name} ({g1}-{g2}): {c1}↔{c2}{marker}")

print(f"\n04:00:")
print(f"  Type: {h4.type}")
print(f"  Sacral defined: {'Sacral' in h4.defined_centers}")
print(f"  Defined channels:")
for ch in h4.channels:
    if ch.defined:
        g1, g2 = ch.gates
        c1 = calc.GATE_TO_CENTER.get(g1)
        c2 = calc.GATE_TO_CENTER.get(g2)
        marker = " ← SACRAL" if (c1 == "Sacral" or c2 == "Sacral") else ""
        print(f"    {ch.name} ({g1}-{g2}): {c1}↔{c2}{marker}")

print("\n" + "="*60)
print("ANALYSIS:")
print("="*60)

# Find which channels changed
h3_channels = set((ch.gates[0], ch.gates[1]) for ch in h3.channels if ch.defined)
h4_channels = set((ch.gates[0], ch.gates[1]) for ch in h4.channels if ch.defined)

lost = h3_channels - h4_channels
gained = h4_channels - h3_channels

if lost:
    print(f"Channels LOST at 04:00: {lost}")
if gained:
    print(f"Channels GAINED at 04:00: {gained}")

print("\nThis variation is EXPECTED if Moon crosses gate boundaries.")
print("Moon moves ~0.5° per hour, so it can change gates during the day.")
