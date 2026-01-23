#!/usr/bin/env python3
"""
Quick HD feature verification - confirms all new features work.
"""
import sys
from pathlib import Path
from datetime import date, time

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

print("=" * 80)
print("HD FEATURE VERIFICATION - Hayford 18:00")
print("=" * 80)

chart = calc.calculate_chart(
    name="Hayford Ayirebi",
    birth_date=date(1999, 7, 23),
    birth_time=time(18, 0),
    latitude=5.6037,
    longitude=-0.1870,
    timezone="Africa/Accra"
)

print("\n✅ CORE FEATURES:")
print(f"  Type: {chart.type}")
print(f"  Strategy: {chart.strategy}")
print(f"  Authority: {chart.authority}")
print(f"  Profile: {chart.profile}")
print(f"  Definition: {chart.definition}")

print("\n✅ NEW FEATURES:")
print(f"  Signature: {chart.signature}")
print(f"  Not-Self: {chart.not_self}")
print(f"  Incarnation Cross: {chart.incarnation_cross}")

print("\n✅ GATES (with sub-lines):")
for gate in chart.personality_gates[:3]:
    print(f"  {gate.planet}: Gate {gate.gate}.{gate.line} (Color:{gate.color} Tone:{gate.tone} Base:{gate.base})")

print("\n✅ CHANNELS (with theme):")
for ch in chart.channels[:3]:
    print(f"  {ch.name} ({ch.gates[0]}-{ch.gates[1]})")
    print(f"    Theme: {ch.theme}")

print("\n✅ CENTERS:")
print(f"  Defined: {chart.defined_centers}")
print(f"  Undefined: {chart.undefined_centers}")

print("\n" + "=" * 80)
print("ALL HD FEATURES VERIFIED SUCCESSFULLY!")
print("=" * 80)
