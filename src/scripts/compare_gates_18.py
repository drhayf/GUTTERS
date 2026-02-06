#!/usr/bin/env python3
"""
Compare our planetary gate calculations with Jovian for 18:00
"""
import sys
from datetime import date, time
from pathlib import Path

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
print("GATE COMPARISON - 18:00")
print("=" * 80)
print("\nOUR PERSONALITY GATES:")
for g in chart.personality_gates:
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line}")

print("\nOUR DESIGN GATES:")
for g in chart.design_gates:
    print(f"  {g.planet:12} Gate {g.gate:2}.{g.line}")

print("\n" + "=" * 80)
print("KEY GATES TO VERIFY:")
print("=" * 80)
print("\nChannel 59-6 (Mating):")
personality_gate_59 = [g for g in chart.personality_gates if g.planet == 'Venus'][0].gate
design_gate_6 = [g for g in chart.design_gates if g.planet == 'Moon'][0].gate
print(f"  Gate 59 (Sacral): Personality Venus = Gate {personality_gate_59}")
print(f"  Gate 6 (Solar Plexus): Design Moon = Gate {design_gate_6}")

print("\nIf Jovian shows Projector, then either:")
print("  1. Venus is NOT in Gate 59, OR")
print("  2. Design Moon is NOT in Gate 6")
print("\nPlease check Jovian's gate list on the right side of the bodygraph!")
print("=" * 80)
