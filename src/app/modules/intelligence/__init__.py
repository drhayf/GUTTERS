"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        GUTTERS INTELLIGENCE MODULE                           ║
║                                                                              ║
║   The Council of Systems - Multi-Paradigm Metaphysical Intelligence          ║
║                                                                              ║
║   Components:                                                                ║
║   - iching: I-Ching / Human Design / Gene Keys calculation kernel           ║
║   - cardology: Order of the Magi / Cardology calculation kernel             ║
║   - synthesis: Harmonic resonance and cross-system integration              ║
║   - observer: Pattern observation and learning                              ║
║   - hypothesis: Hypothesis generation and testing                           ║
║   - journal: Journal analysis and insights                                  ║
║   - nutrition: Personalized nutrition recommendations                       ║
║                                                                              ║
║   Architecture: Harmonic/Parallel (Council of Systems)                       ║
║   - All systems are sovereign equals                                         ║
║   - Synthesis layer determines resonance/dissonance                          ║
║   - Extensible to additional systems (Vedic, Mayan, etc.)                   ║
║                                                                              ║
║   Author: GUTTERS Project / GUTTERS OS                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# Version
__version__ = "1.0.0"

# Council of Systems - Core Intelligence
# I-Ching Kernel
from .iching import GATE_DATABASE, IChingKernel
from .synthesis.harmonic import (
    CouncilOfSystems,
    HarmonicSynthesis,
    cross_system_synthesis,
)

__all__ = [
    # Council of Systems
    "CouncilOfSystems",
    "HarmonicSynthesis",
    "cross_system_synthesis",
    # I-Ching Kernel
    "IChingKernel",
    "GATE_DATABASE",
]
