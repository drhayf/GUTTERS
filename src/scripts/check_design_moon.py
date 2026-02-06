#!/usr/bin/env python3
"""
Check Design calculation - 88 days before birth
"""
import sys
from datetime import date, time, timedelta
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from kerykeion import AstrologicalSubject

# Birth: July 23, 1999, 18:00
birth_date = date(1999, 7, 23)
birth_time = time(18, 0)

# Design: 88 days before birth
design_date = birth_date - timedelta(days=88)

print("=" * 80)
print("DESIGN CALCULATION CHECK")
print("=" * 80)
print(f"Birth: {birth_date} at {birth_time}")
print(f"Design (88 days before): {design_date} at {birth_time}")

# Calculate design chart
design_subject = AstrologicalSubject(
    name="Design",
    year=design_date.year,
    month=design_date.month,
    day=design_date.day,
    hour=birth_time.hour,
    minute=birth_time.minute,
    lat=5.6037,
    lng=-0.1870,
    tz_str="Africa/Accra"
)

print("\nDesign Moon:")
print(f"  Sign: {design_subject.moon.sign}")
print(f"  Position: {design_subject.moon.position:.2f}°")
print(f"  Absolute longitude: {design_subject.moon.abs_pos:.2f}°")

# Convert to HD gate
from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

gate, line = calc._longitude_to_gate(design_subject.moon.abs_pos)
print("\nOur calculation:")
print(f"  Gate {gate}.{line}")

print("\nJovian shows:")
print("  Gate 9.5")

print(f"\nMatch: {'YES' if gate == 9 else 'NO - BUG IN GATE MAPPING!'}")

print("\n" + "=" * 80)
print(f"Moon absolute longitude: {design_subject.moon.abs_pos:.4f}°")
print("We need to verify this maps to Gate 9, not Gate 6")
print("=" * 80)
