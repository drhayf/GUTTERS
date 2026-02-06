#!/usr/bin/env python3
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator

c = HumanDesignCalculator()

# Find Gate 6 and Gate 9 positions
idx6 = c.GATE_ORDER_FROM_41.index(6)
idx9 = c.GATE_ORDER_FROM_41.index(9)

start6 = idx6 * 5.625
end6 = start6 + 5.625

start9 = idx9 * 5.625
end9 = start9 + 5.625

print(f"Gate 6: {start6:.2f}° to {end6:.2f}°")
print(f"Gate 9: {start9:.2f}° to {end9:.2f}°")
print(f"\n172.94° is in Gate 6 range? {start6 <= 172.94 < end6}")
print(f"172.94° is in Gate 9 range? {start9 <= 172.94 < end9}")

# Show gates around 172.94
print("\nGates around 172.94°:")
for i in range(max(0, idx6-2), min(len(c.GATE_ORDER_FROM_41), idx6+3)):
    gate = c.GATE_ORDER_FROM_41[i]
    start = i * 5.625
    end = start + 5.625
    marker = " ← 172.94° HERE" if start <= 172.94 < end else ""
    print(f"  Gate {gate:2}: {start:6.2f}° to {end:6.2f}°{marker}")
