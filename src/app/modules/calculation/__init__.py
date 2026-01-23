"""
GUTTERS - Calculation Modules

Layer 1: Birth data calculations and foundational cosmic analysis.

Modules in this layer compute static or birth-based information:
- Astrology charts and placements
- Numerology calculations
- Human Design charts
- Name analysis
- And other calculation-based systems
"""
from .human_design.module import HumanDesignModule
from .numerology.module import NumerologyModule

__all__ = ['HumanDesignModule', 'NumerologyModule']
