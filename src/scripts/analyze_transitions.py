#!/usr/bin/env python3
"""
Deep dive: WHY does type change from Generator to Projector?
Check what channels are forming/breaking at the transition points
"""
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 80)
print("TRANSITION ANALYSIS: Why does type change?")
print("=" * 80)

# Check hours around the transitions
check_hours = [3, 4, 17, 18]  # Transitions: 3→4 (Gen→Proj), 17→18 (Proj→Gen)

for hour in check_hours:
    chart = calc._calculate_full_chart(
        name="Hayford",
        birth_date=date(1999, 7, 23),
        birth_time=time(hour, 0),
        latitude=5.6037,
        longitude=-0.1870,
        timezone="Africa/Accra"
    )
    
    print(f"\n{'='*80}")
    print(f"HOUR {hour:02}:00 → {chart.type}")
    print(f"{'='*80}")
    print(f"Defined Centers: {chart.defined_centers}")
    print(f"\nSacral defined? {'Sacral' in chart.defined_centers}")
    print(f"Throat defined? {'Throat' in chart.defined_centers}")
    
    print(f"\nDefined Channels:")
    for ch in chart.channels:
        if ch.defined:
            g1, g2 = ch.gates
            c1 = calc.GATE_TO_CENTER.get(g1)
            c2 = calc.GATE_TO_CENTER.get(g2)
            sacral_marker = " ← SACRAL!" if (c1 == "Sacral" or c2 == "Sacral") else ""
            print(f"  {ch.name:20} ({g1}-{g2}): {c1} ↔ {c2}{sacral_marker}")
    
    # Show which gates are present
    print(f"\nPersonality Gates:")
    for g in chart.personality_gates[:5]:
        print(f"  {g.planet:12} Gate {g.gate}.{g.line}")
    
    print(f"\nDesign Gates:")
    for g in chart.design_gates[:5]:
        print(f"  {g.planet:12} Gate {g.gate}.{g.line}")

print("\n" + "=" * 80)
print("KEY QUESTION:")
print("=" * 80)
print("Does the MOON change houses/gates enough to form/break Sacral channels?")
print("Moon moves ~13° per day = ~0.5° per hour")
print("If Moon is near a gate boundary, it could change gates across hours.")
print("=" * 80)
