#!/usr/bin/env python3
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

print(f"18:00 Type: {chart.type}")
print("Jovian shows: Projector")
print(f"\nMatch: {'YES' if chart.type == 'Projector' else 'NO - BUG!'}")
