"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        MAGI OS INTELLIGENCE MODULE                           ║
║                                                                              ║
║   The Council of Systems - Multi-Paradigm Metaphysical Intelligence          ║
║                                                                              ║
║   Components:                                                                ║
║   - iching: I-Ching / Human Design / Gene Keys calculation kernel           ║
║   - cardology: Order of the Magi / Cardology calculation kernel             ║
║   - synthesis: Harmonic resonance and cross-system integration              ║
║                                                                              ║
║   Architecture: Harmonic/Parallel                                            ║
║   - All systems are sovereign equals                                         ║
║   - Synthesis layer determines resonance/dissonance                          ║
║   - Extensible to additional systems (Vedic, Mayan, etc.)                   ║
║                                                                              ║
║   Author: GUTTERS Project / Magi OS                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# Version
__version__ = "1.0.0"

# Convenience imports
from .synthesis.harmonic import (
    CouncilOfSystems,
    HarmonicSynthesis,
    cross_system_synthesis,
)

__all__ = [
    "CouncilOfSystems",
    "HarmonicSynthesis",
    "cross_system_synthesis",
]
