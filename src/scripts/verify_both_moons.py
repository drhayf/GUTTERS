#!/usr/bin/env python3
"""
Verify Design calculation - check if 88 days is correct
"""
import sys
from datetime import date, time, timedelta
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Birth: July 23, 1999, 18:00
birth_date = date(1999, 7, 23)
birth_time = time(18, 0)

# Design: 88 days before birth
design_date = birth_date - timedelta(days=88)

print("=" * 80)
print("DESIGN DATE VERIFICATION")
print("=" * 80)
print(f"Birth date: {birth_date} ({birth_date.strftime('%B %d, %Y')})")
print(f"Design date (88 days before): {design_date} ({design_date.strftime('%B %d, %Y')})")
print(f"Days difference: {(birth_date - design_date).days}")

# Calculate both personality and design
from kerykeion import AstrologicalSubject

personality = AstrologicalSubject(
    name="Personality",
    year=birth_date.year,
    month=birth_date.month,
    day=birth_date.day,
    hour=birth_time.hour,
    minute=birth_time.minute,
    lat=5.6037,
    lng=-0.1870,
    tz_str="Africa/Accra"
)

design = AstrologicalSubject(
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

print("\nPersonality Moon (at birth):")
print(f"  Position: {personality.moon.abs_pos:.4f}°")

print("\nDesign Moon (88 days before):")
print(f"  Position: {design.moon.abs_pos:.4f}°")

# Convert to gates
from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

calc = HumanDesignCalculator()

p_gate, p_line = calc._longitude_to_gate(personality.moon.abs_pos)
d_gate, d_line = calc._longitude_to_gate(design.moon.abs_pos)

print("\nOur calculations:")
print(f"  Personality Moon: Gate {p_gate}.{p_line}")
print(f"  Design Moon: Gate {d_gate}.{d_line}")

print("\nJovian shows:")
print("  Personality Moon: Gate 9.2")
print("  Design Moon: Gate 9.5")

print("\nMatches:")
print(f"  Personality: {'YES' if p_gate == 9 else 'NO'}")
print(f"  Design: {'YES' if d_gate == 9 else 'NO'}")
print("=" * 80)
