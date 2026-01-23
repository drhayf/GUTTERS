#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

chart = calc._calculate_full_chart(
    name="Hayford",
    birth_date=date(1999, 7, 23),
    birth_time=time(18, 0),
    latitude=5.6037,
    longitude=-0.1870,
    timezone="Africa/Accra"
)

print("=" * 80)
print("18:00 ANALYSIS")
print("=" * 80)
print(f"Our Type: {chart.type}")
print(f"Jovian Type: Projector")
print(f"\nDefined Centers: {chart.defined_centers}")
print(f"Sacral defined: {'Sacral' in chart.defined_centers}")

print(f"\nDefined Channels:")
for ch in chart.channels:
    if ch.defined:
        g1, g2 = ch.gates
        c1 = calc.GATE_TO_CENTER.get(g1)
        c2 = calc.GATE_TO_CENTER.get(g2)
        sacral_marker = " ← SACRAL!" if (c1 == "Sacral" or c2 == "Sacral") else ""
        print(f"  {ch.name:20} Gates {g1:2}-{g2:2} ({c1:15} ↔ {c2:15}){sacral_marker}")

print(f"\nPersonality Gates:")
for g in chart.personality_gates[:8]:
    center = calc.GATE_TO_CENTER.get(g.gate)
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line} ({center})")

print(f"\nDesign Gates:")
for g in chart.design_gates[:8]:
    center = calc.GATE_TO_CENTER.get(g.gate)
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line} ({center})")

print("\n" + "=" * 80)
print("If Sacral is defined, we have a bug in our gate/channel logic!")
print("=" * 80)
