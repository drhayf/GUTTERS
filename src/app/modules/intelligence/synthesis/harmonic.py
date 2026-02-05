"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    HARMONIC SYNTHESIS KERNEL v1.0                            ║
║                                                                              ║
║   The "Council of Systems" - Parallel Intelligence Architecture              ║
║                                                                              ║
║   Philosophy:                                                                ║
║   - Cardology = Macro-Coordinate (The Terrain/Season - 52 Days)             ║
║   - I-Ching = Micro-Coordinate (The Atmosphere/Weather - ~6 Days)           ║
║   - Both systems are SOVEREIGN - neither subservient                         ║
║   - Synthesis Layer determines resonance/dissonance between systems          ║
║                                                                              ║
║   Architecture:                                                              ║
║   - Extensible: Designed to accept 3rd/4th systems (Vedic, etc.)            ║
║   - Equal Weighting: All inputs weighted equally in synthesis                ║
║   - Gamification Ready: Gene Keys spectrum maps to XP/Leveling              ║
║                                                                              ║
║   Author: GUTTERS Project / Magi OS                                          ║
║   License: For metaphysical research and consciousness development           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Protocol
from abc import ABC, abstractmethod
import math


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: SYSTEM PROTOCOL (Interface for Council Members)
# ═══════════════════════════════════════════════════════════════════════════════

class MetaphysicalSystem(Protocol):
    """
    Protocol defining what any metaphysical system must provide
    to participate in the Council of Systems.
    
    This enables extensibility - any new system (Vedic, Mayan, etc.)
    can be added by implementing this interface.
    """
    
    @property
    def system_name(self) -> str:
        """Unique identifier for this system."""
        ...
    
    @property
    def cycle_duration_days(self) -> float:
        """Average duration of one cycle in days."""
        ...
    
    def get_current_position(self, dt: datetime) -> Dict[str, Any]:
        """Get the current position/state for a given datetime."""
        ...
    
    def get_element(self, dt: datetime) -> str:
        """Get the elemental correspondence for the current position."""
        ...
    
    def get_archetype(self, dt: datetime) -> str:
        """Get the archetype/theme for the current position."""
        ...
    
    def get_frequency_spectrum(self, dt: datetime) -> Dict[str, str]:
        """Get the frequency range (low/balanced/high states)."""
        ...


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: ELEMENTAL CORRESPONDENCES
# ═══════════════════════════════════════════════════════════════════════════════

class Element(Enum):
    """
    Universal elemental system used for cross-system resonance.
    
    This is the "common language" that allows different systems
    to be compared and synthesized.
    """
    FIRE = "fire"       # Action, Will, Transformation
    WATER = "water"     # Emotion, Intuition, Flow
    AIR = "air"         # Mind, Communication, Ideas
    EARTH = "earth"     # Form, Material, Stability
    ETHER = "ether"     # Spirit, Transcendence (5th element)


# Cardology Suit to Element mapping
CARDOLOGY_SUIT_ELEMENTS = {
    "Hearts": Element.WATER,      # Emotions, Love
    "Clubs": Element.FIRE,        # Knowledge, Ideas (Fire of Mind)
    "Diamonds": Element.EARTH,    # Values, Material
    "Spades": Element.AIR,        # Work, Wisdom, Transformation
}

# Human Design Center to Element mapping
HD_CENTER_ELEMENTS = {
    "Head": Element.AIR,          # Mental Pressure
    "Ajna": Element.AIR,          # Mental Awareness
    "Throat": Element.ETHER,      # Manifestation
    "G": Element.ETHER,           # Identity, Direction
    "Heart": Element.FIRE,        # Willpower
    "Sacral": Element.WATER,      # Life Force
    "Solar Plexus": Element.WATER,# Emotions
    "Spleen": Element.EARTH,      # Survival, Intuition
    "Root": Element.EARTH,        # Pressure, Grounding
}

# I-Ching Trigram to Element mapping
TRIGRAM_ELEMENTS = {
    "111": Element.FIRE,    # Heaven/Qian - Creative Force
    "000": Element.EARTH,   # Earth/Kun - Receptive
    "001": Element.FIRE,    # Thunder/Zhen - Arousing
    "010": Element.WATER,   # Water/Kan - Abysmal
    "100": Element.EARTH,   # Mountain/Gen - Stillness
    "110": Element.AIR,     # Wind/Xun - Gentle
    "101": Element.FIRE,    # Fire/Li - Clinging
    "011": Element.WATER,   # Lake/Dui - Joyous
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: RESONANCE SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ResonanceType(Enum):
    """Types of resonance between systems."""
    HARMONIC = "harmonic"           # Strong positive alignment
    SUPPORTIVE = "supportive"       # Moderate positive alignment
    NEUTRAL = "neutral"             # No significant interaction
    CHALLENGING = "challenging"     # Growth-oriented tension
    DISSONANT = "dissonant"         # Strong opposition


@dataclass
class ElementalResonance:
    """
    Resonance calculation between two elements.
    
    Based on traditional elemental relationships:
    - Same element = Harmonic (1.0)
    - Complementary = Supportive (0.7)
    - Neutral = (0.5)
    - Challenging = (0.3)
    - Opposing = Dissonant (0.1)
    """
    element_1: Element
    element_2: Element
    score: float
    resonance_type: ResonanceType
    description: str


# Elemental compatibility matrix
# Score: 1.0 = Perfect harmony, 0.0 = Complete opposition
ELEMENTAL_MATRIX = {
    # Fire relationships
    (Element.FIRE, Element.FIRE): (1.0, ResonanceType.HARMONIC, "Amplified creative force"),
    (Element.FIRE, Element.AIR): (0.8, ResonanceType.SUPPORTIVE, "Air feeds fire - ideas fuel action"),
    (Element.FIRE, Element.WATER): (0.2, ResonanceType.CHALLENGING, "Fire and water create steam - transformation through tension"),
    (Element.FIRE, Element.EARTH): (0.4, ResonanceType.NEUTRAL, "Fire shapes earth - willpower meets form"),
    (Element.FIRE, Element.ETHER): (0.7, ResonanceType.SUPPORTIVE, "Fire rises to spirit"),
    
    # Water relationships
    (Element.WATER, Element.WATER): (1.0, ResonanceType.HARMONIC, "Deep emotional resonance"),
    (Element.WATER, Element.EARTH): (0.8, ResonanceType.SUPPORTIVE, "Earth contains water - emotion finds form"),
    (Element.WATER, Element.AIR): (0.4, ResonanceType.NEUTRAL, "Surface ripples - mental awareness of feeling"),
    (Element.WATER, Element.ETHER): (0.7, ResonanceType.SUPPORTIVE, "Water reflects spirit"),
    
    # Earth relationships
    (Element.EARTH, Element.EARTH): (1.0, ResonanceType.HARMONIC, "Stable foundation"),
    (Element.EARTH, Element.AIR): (0.3, ResonanceType.CHALLENGING, "Earth grounds air - ideas need anchoring"),
    (Element.EARTH, Element.ETHER): (0.5, ResonanceType.NEUTRAL, "Spirit incarnates in form"),
    
    # Air relationships
    (Element.AIR, Element.AIR): (1.0, ResonanceType.HARMONIC, "Mental clarity and exchange"),
    (Element.AIR, Element.ETHER): (0.8, ResonanceType.SUPPORTIVE, "Thought approaches transcendence"),
    
    # Ether relationships
    (Element.ETHER, Element.ETHER): (1.0, ResonanceType.HARMONIC, "Pure spiritual alignment"),
}


def get_elemental_resonance(elem1: Element, elem2: Element) -> ElementalResonance:
    """Calculate resonance between two elements."""
    # Normalize order for lookup (matrix is symmetric)
    key = (elem1, elem2)
    reverse_key = (elem2, elem1)
    
    if key in ELEMENTAL_MATRIX:
        score, res_type, desc = ELEMENTAL_MATRIX[key]
    elif reverse_key in ELEMENTAL_MATRIX:
        score, res_type, desc = ELEMENTAL_MATRIX[reverse_key]
    else:
        # Default for undefined pairs
        score, res_type, desc = 0.5, ResonanceType.NEUTRAL, "Undefined relationship"
    
    return ElementalResonance(elem1, elem2, score, res_type, desc)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: FREQUENCY SPECTRUM (XP/LEVELING SYSTEM)
# ═══════════════════════════════════════════════════════════════════════════════

class FrequencyBand(Enum):
    """
    The three frequency bands for the XP/Leveling system.
    
    Maps directly to Gene Keys Shadow/Gift/Siddhi:
    - SHADOW: Low XP state (unconscious, reactive)
    - GIFT: Balanced state (conscious, responsive)  
    - SIDDHI: High XP state (transcendent, unified)
    """
    SHADOW = "shadow"     # 0-33% XP range
    GIFT = "gift"         # 34-66% XP range
    SIDDHI = "siddhi"     # 67-100% XP range


@dataclass
class FrequencyState:
    """
    Current frequency state with XP context.
    
    This enables the "Solo Leveling" gamification:
    - Low awareness/XP = Shadow expression
    - Growing awareness/XP = Gift expression
    - High awareness/XP = Siddhi expression
    """
    band: FrequencyBand
    shadow_expression: str
    gift_expression: str
    siddhi_expression: str
    current_expression: str  # Based on band
    
    # For gamification
    xp_threshold_low: int = 0
    xp_threshold_mid: int = 333
    xp_threshold_high: int = 666
    xp_max: int = 1000
    
    def get_expression_for_xp(self, xp: int) -> Tuple[FrequencyBand, str]:
        """Determine expression based on XP level."""
        if xp < self.xp_threshold_mid:
            return FrequencyBand.SHADOW, self.shadow_expression
        elif xp < self.xp_threshold_high:
            return FrequencyBand.GIFT, self.gift_expression
        else:
            return FrequencyBand.SIDDHI, self.siddhi_expression


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: SYNTHESIS DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SystemReading:
    """
    A reading from a single metaphysical system.
    
    This is the standardized output format that all systems
    must provide for the synthesis layer.
    """
    system_name: str
    timestamp: datetime
    
    # Primary identification
    primary_symbol: str           # e.g., "K♥" or "Gate 13"
    primary_name: str             # e.g., "King of Hearts" or "Fellowship with Men"
    
    # Elemental correspondence
    element: Element
    
    # Archetype/Theme
    archetype: str
    keynote: str
    
    # Frequency spectrum (for XP mapping)
    shadow: str
    gift: str
    siddhi: str
    
    # Cycle context
    cycle_day: int               # Day within current cycle
    cycle_total: int             # Total days in cycle
    cycle_percentage: float      # Progress through cycle (0-1)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HarmonicSynthesis:
    """
    The synthesized reading from multiple systems.
    
    This is the final output of the Council of Systems -
    a unified field that honors each system's sovereignty
    while revealing their combined wisdom.
    """
    timestamp: datetime
    
    # Individual system readings
    systems: List[SystemReading]
    
    # Cross-system resonance
    resonance_score: float           # 0-1 overall harmony
    resonance_type: ResonanceType
    resonance_description: str
    
    # Unified frequency guidance
    unified_shadow: str              # Combined shadow themes
    unified_gift: str                # Combined gift potential
    unified_siddhi: str              # Combined transcendent state
    
    # Elemental balance
    dominant_element: Element
    elemental_balance: Dict[Element, float]
    
    # Practical guidance
    macro_theme: str                 # From Cardology (52-day)
    micro_theme: str                 # From I-Ching (6-day)
    synthesis_guidance: str          # Combined wisdom
    
    # XP/Quest suggestions
    quest_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "systems": [
                {
                    "name": s.system_name,
                    "symbol": s.primary_symbol,
                    "element": s.element.value,
                    "archetype": s.archetype,
                }
                for s in self.systems
            ],
            "resonance": {
                "score": self.resonance_score,
                "type": self.resonance_type.value,
                "description": self.resonance_description,
            },
            "frequency": {
                "shadow": self.unified_shadow,
                "gift": self.unified_gift,
                "siddhi": self.unified_siddhi,
            },
            "elements": {
                "dominant": self.dominant_element.value,
                "balance": {e.value: v for e, v in self.elemental_balance.items()},
            },
            "themes": {
                "macro": self.macro_theme,
                "micro": self.micro_theme,
                "synthesis": self.synthesis_guidance,
            },
            "quests": self.quest_suggestions,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: THE COUNCIL OF SYSTEMS (Main Synthesis Engine)
# ═══════════════════════════════════════════════════════════════════════════════

class CouncilOfSystems:
    """
    The Harmonic Synthesis Engine.
    
    This class orchestrates multiple metaphysical systems,
    calculates their resonance, and produces unified guidance.
    
    Architecture:
    - Systems are registered as equal members
    - Each system provides its reading via standardized interface
    - The Council calculates cross-system resonance
    - Output is a HarmonicSynthesis with unified guidance
    """
    
    def __init__(self):
        """Initialize the Council with no members."""
        self._systems: Dict[str, Any] = {}  # name -> system adapter
        self._weights: Dict[str, float] = {}  # name -> weight (default 1.0)
    
    def register_system(self, name: str, adapter: Any, weight: float = 1.0):
        """
        Register a metaphysical system with the Council.
        
        Args:
            name: Unique name for this system
            adapter: System adapter implementing the reading interface
            weight: Relative weight in synthesis (default 1.0 = equal)
        """
        self._systems[name] = adapter
        self._weights[name] = weight
    
    def get_reading(self, system_name: str, dt: datetime = None) -> Optional[SystemReading]:
        """
        Get a reading from a specific system.
        
        Args:
            system_name: Name of registered system
            dt: Datetime for reading (default: now UTC)
            
        Returns:
            SystemReading or None if system not found
        """
        if system_name not in self._systems:
            return None
        
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        adapter = self._systems[system_name]
        return adapter.get_reading(dt)
    
    def synthesize(self, dt: datetime = None) -> HarmonicSynthesis:
        """
        Generate the full harmonic synthesis from all registered systems.
        
        Args:
            dt: Datetime for synthesis (default: now UTC)
            
        Returns:
            HarmonicSynthesis with unified guidance
        """
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        # Collect readings from all systems
        readings = []
        for name, adapter in self._systems.items():
            reading = adapter.get_reading(dt)
            if reading:
                readings.append(reading)
        
        if not readings:
            # Return empty synthesis
            return self._empty_synthesis(dt)
        
        # Calculate elemental balance
        elemental_balance = self._calculate_elemental_balance(readings)
        dominant_element = max(elemental_balance, key=elemental_balance.get)
        
        # Calculate cross-system resonance
        resonance_score, resonance_type = self._calculate_resonance(readings)
        resonance_description = self._describe_resonance(readings, resonance_type)
        
        # Unify frequency spectrums
        unified_shadow = self._unify_shadows(readings)
        unified_gift = self._unify_gifts(readings)
        unified_siddhi = self._unify_siddhis(readings)
        
        # Extract macro/micro themes
        macro_theme = self._extract_macro_theme(readings)
        micro_theme = self._extract_micro_theme(readings)
        
        # Generate synthesis guidance
        synthesis_guidance = self._generate_synthesis_guidance(
            readings, resonance_type, dominant_element
        )
        
        # Generate quest suggestions
        quests = self._generate_quest_suggestions(
            readings, resonance_type, elemental_balance
        )
        
        return HarmonicSynthesis(
            timestamp=dt,
            systems=readings,
            resonance_score=resonance_score,
            resonance_type=resonance_type,
            resonance_description=resonance_description,
            unified_shadow=unified_shadow,
            unified_gift=unified_gift,
            unified_siddhi=unified_siddhi,
            dominant_element=dominant_element,
            elemental_balance=elemental_balance,
            macro_theme=macro_theme,
            micro_theme=micro_theme,
            synthesis_guidance=synthesis_guidance,
            quest_suggestions=quests,
        )
    
    def _calculate_elemental_balance(
        self, readings: List[SystemReading]
    ) -> Dict[Element, float]:
        """Calculate the elemental balance across all systems."""
        balance = {e: 0.0 for e in Element}
        total_weight = 0.0
        
        for reading in readings:
            weight = self._weights.get(reading.system_name, 1.0)
            balance[reading.element] += weight
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            for elem in balance:
                balance[elem] /= total_weight
        
        return balance
    
    def _calculate_resonance(
        self, readings: List[SystemReading]
    ) -> Tuple[float, ResonanceType]:
        """Calculate overall resonance score between all system pairs."""
        if len(readings) < 2:
            return 1.0, ResonanceType.HARMONIC
        
        total_score = 0.0
        pair_count = 0
        
        # Calculate resonance between all pairs
        for i, r1 in enumerate(readings):
            for r2 in readings[i+1:]:
                resonance = get_elemental_resonance(r1.element, r2.element)
                weight1 = self._weights.get(r1.system_name, 1.0)
                weight2 = self._weights.get(r2.system_name, 1.0)
                
                total_score += resonance.score * (weight1 + weight2) / 2
                pair_count += 1
        
        avg_score = total_score / pair_count if pair_count > 0 else 1.0
        
        # Determine resonance type from score
        if avg_score >= 0.8:
            res_type = ResonanceType.HARMONIC
        elif avg_score >= 0.6:
            res_type = ResonanceType.SUPPORTIVE
        elif avg_score >= 0.4:
            res_type = ResonanceType.NEUTRAL
        elif avg_score >= 0.2:
            res_type = ResonanceType.CHALLENGING
        else:
            res_type = ResonanceType.DISSONANT
        
        return avg_score, res_type
    
    def _describe_resonance(
        self, readings: List[SystemReading], res_type: ResonanceType
    ) -> str:
        """Generate human-readable resonance description."""
        elements = [r.element.value for r in readings]
        
        descriptions = {
            ResonanceType.HARMONIC: f"Strong alignment between {' and '.join(elements)} - unified flow",
            ResonanceType.SUPPORTIVE: f"Supportive interplay between {' and '.join(elements)} - collaborative energy",
            ResonanceType.NEUTRAL: f"Balanced presence of {' and '.join(elements)} - open potential",
            ResonanceType.CHALLENGING: f"Creative tension between {' and '.join(elements)} - growth opportunity",
            ResonanceType.DISSONANT: f"Dynamic opposition between {' and '.join(elements)} - transformation required",
        }
        
        return descriptions.get(res_type, "Unknown resonance pattern")
    
    def _unify_shadows(self, readings: List[SystemReading]) -> str:
        """Combine shadow expressions from all systems."""
        shadows = [r.shadow for r in readings if r.shadow]
        if not shadows:
            return "Unconscious patterns"
        return " / ".join(shadows)
    
    def _unify_gifts(self, readings: List[SystemReading]) -> str:
        """Combine gift expressions from all systems."""
        gifts = [r.gift for r in readings if r.gift]
        if not gifts:
            return "Conscious potential"
        return " / ".join(gifts)
    
    def _unify_siddhis(self, readings: List[SystemReading]) -> str:
        """Combine siddhi expressions from all systems."""
        siddhis = [r.siddhi for r in readings if r.siddhi]
        if not siddhis:
            return "Transcendent state"
        return " / ".join(siddhis)
    
    def _extract_macro_theme(self, readings: List[SystemReading]) -> str:
        """Extract the macro (longer cycle) theme."""
        # Prioritize Cardology as macro system
        for reading in readings:
            if reading.system_name == "Cardology":
                return f"{reading.keynote} ({reading.primary_symbol})"
        
        # Fallback to longest cycle
        if readings:
            longest = max(readings, key=lambda r: r.cycle_total)
            return f"{longest.keynote} ({longest.primary_symbol})"
        
        return "No macro theme available"
    
    def _extract_micro_theme(self, readings: List[SystemReading]) -> str:
        """Extract the micro (shorter cycle) theme."""
        # Prioritize I-Ching as micro system
        for reading in readings:
            if reading.system_name == "I-Ching":
                return f"{reading.keynote} ({reading.primary_symbol})"
        
        # Fallback to shortest cycle
        if readings:
            shortest = min(readings, key=lambda r: r.cycle_total)
            return f"{shortest.keynote} ({shortest.primary_symbol})"
        
        return "No micro theme available"
    
    def _generate_synthesis_guidance(
        self,
        readings: List[SystemReading],
        res_type: ResonanceType,
        dominant_element: Element
    ) -> str:
        """Generate unified guidance based on synthesis."""
        element_guidance = {
            Element.FIRE: "Channel energy into action and creative expression",
            Element.WATER: "Honor your emotions and trust your intuitive flow",
            Element.EARTH: "Ground your intentions in practical steps",
            Element.AIR: "Clarify your thoughts and communicate with precision",
            Element.ETHER: "Connect to your higher purpose and spiritual alignment",
        }
        
        resonance_guidance = {
            ResonanceType.HARMONIC: "Systems aligned - ride the wave of synchronicity",
            ResonanceType.SUPPORTIVE: "Favorable conditions - lean into opportunities",
            ResonanceType.NEUTRAL: "Open field - conscious choice determines direction",
            ResonanceType.CHALLENGING: "Growth edge active - embrace the friction as fuel",
            ResonanceType.DISSONANT: "Transformation portal - release what no longer serves",
        }
        
        base_guidance = element_guidance.get(dominant_element, "Stay present and aware")
        resonance_note = resonance_guidance.get(res_type, "Navigate with awareness")
        
        return f"{base_guidance}. {resonance_note}."
    
    def _generate_quest_suggestions(
        self,
        readings: List[SystemReading],
        res_type: ResonanceType,
        elemental_balance: Dict[Element, float]
    ) -> List[str]:
        """Generate quest suggestions based on current synthesis."""
        quests = []
        
        # Element-based quests
        dominant = max(elemental_balance, key=elemental_balance.get)
        element_quests = {
            Element.FIRE: [
                "Complete one task that requires courage today",
                "Express your creative vision in some form",
                "Take initiative on something you've been postponing",
            ],
            Element.WATER: [
                "Journal about your current emotional state",
                "Practice 10 minutes of intuitive movement or meditation",
                "Reach out to someone you care about",
            ],
            Element.EARTH: [
                "Organize one area of your physical space",
                "Take a walk in nature and ground yourself",
                "Complete one practical task from your list",
            ],
            Element.AIR: [
                "Learn something new for 20 minutes",
                "Have a meaningful conversation with clear communication",
                "Write down your thoughts to gain clarity",
            ],
            Element.ETHER: [
                "Spend 15 minutes in silent contemplation",
                "Reflect on your life purpose and direction",
                "Practice gratitude for what is",
            ],
        }
        quests.extend(element_quests.get(dominant, [])[:2])
        
        # Resonance-based quest modifiers
        if res_type == ResonanceType.CHALLENGING:
            quests.append("Face one small discomfort consciously today")
        elif res_type == ResonanceType.DISSONANT:
            quests.append("Identify one thing to release and let go of it symbolically")
        elif res_type == ResonanceType.HARMONIC:
            quests.append("Amplify a positive pattern you notice today")
        
        # Add frequency-based quest
        if readings:
            shadow = readings[0].shadow
            gift = readings[0].gift
            quests.append(f"Notice when '{shadow}' arises, pivot to '{gift}'")
        
        return quests[:5]  # Max 5 quests
    
    def _empty_synthesis(self, dt: datetime) -> HarmonicSynthesis:
        """Return empty synthesis when no systems are registered."""
        return HarmonicSynthesis(
            timestamp=dt,
            systems=[],
            resonance_score=0.5,
            resonance_type=ResonanceType.NEUTRAL,
            resonance_description="No systems registered",
            unified_shadow="Unknown",
            unified_gift="Unknown",
            unified_siddhi="Unknown",
            dominant_element=Element.ETHER,
            elemental_balance={e: 0.2 for e in Element},
            macro_theme="No macro theme",
            micro_theme="No micro theme",
            synthesis_guidance="Register systems to receive guidance",
            quest_suggestions=["Register a metaphysical system"],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: SYSTEM ADAPTERS
# ═══════════════════════════════════════════════════════════════════════════════

class IChingAdapter:
    """
    Adapter to connect the I-Ching kernel to the Council of Systems.
    """
    
    def __init__(self, kernel):
        """
        Initialize with an IChingKernel instance.
        
        Args:
            kernel: IChingKernel instance
        """
        self._kernel = kernel
    
    def get_reading(self, dt: datetime) -> SystemReading:
        """Generate a SystemReading from the I-Ching kernel."""
        daily = self._kernel.get_daily_code(dt)
        sun = daily.sun_activation
        gate_data = sun.gate_data
        
        # Determine element from center
        center = gate_data.hd_center if gate_data else "G"
        element = HD_CENTER_ELEMENTS.get(center, Element.ETHER)
        
        # Alternatively, use trigram for element
        if gate_data:
            upper_elem = TRIGRAM_ELEMENTS.get(gate_data.upper_trigram, Element.ETHER)
            # Use upper trigram as primary element influence
            element = upper_elem
        
        # Calculate cycle position
        # I-Ching gates: ~5.7 days per gate (360° / 64 gates, ~1°/day)
        gate_duration = 5.625  # days
        
        return SystemReading(
            system_name="I-Ching",
            timestamp=dt,
            primary_symbol=f"Gate {sun.gate}",
            primary_name=gate_data.iching_name if gate_data else f"Gate {sun.gate}",
            element=element,
            archetype=gate_data.hd_name if gate_data else "Unknown Gate",
            keynote=gate_data.hd_keynote if gate_data else "Unknown",
            shadow=gate_data.gk_shadow if gate_data else "Unknown",
            gift=gate_data.gk_gift if gate_data else "Unknown",
            siddhi=gate_data.gk_siddhi if gate_data else "Unknown",
            cycle_day=sun.line,  # Line represents day within gate
            cycle_total=6,  # 6 lines per gate
            cycle_percentage=sun.line / 6.0,
            metadata={
                "line": sun.line,
                "color": sun.color,
                "tone": sun.tone,
                "base": sun.base,
                "binary": sun.binary,
                "earth_gate": daily.earth_activation.gate,
            }
        )


class CardologyAdapter:
    """
    Adapter to connect the Cardology kernel to the Council of Systems.
    
    Uses the real CardologyModule to get actual planetary period data
    for cross-system synthesis with I-Ching.
    """
    
    def __init__(self, birth_date: date = None):
        """
        Initialize with optional birth date for personalized readings.
        
        Args:
            birth_date: User's birth date for period calculation
                        If None, uses global transit data (current date)
        """
        self._birth_date = birth_date
    
    def get_reading(self, dt: datetime) -> SystemReading:
        """Generate a SystemReading from the real Cardology kernel."""
        try:
            from ..cardology import CardologyModule
            module = CardologyModule()
            
            # If we have a birth date, get personalized period
            if self._birth_date:
                period_info = module.get_current_period(
                    birth_date=self._birth_date,
                    current_date=dt.date() if hasattr(dt, 'date') else dt
                )
                return self._reading_from_period(dt, period_info)
            else:
                # Global transit mode - calculate birth card for today
                # This shows the "universal" card energy for the day
                return self._global_transit_reading(dt)
        except Exception as e:
            # Fallback to demo mode if kernel fails
            import logging
            logging.getLogger(__name__).warning(f"CardologyAdapter kernel error: {e}")
            return self._demo_reading(dt)
    
    def _reading_from_period(self, dt: datetime, period_info: dict) -> SystemReading:
        """Create SystemReading from real period info."""
        period = period_info.get("period", "")  # Planet name
        card = period_info.get("card", "")  # Card symbol
        card_name = period_info.get("card_name", card)
        
        # Parse suit from card for element mapping
        suit = self._extract_suit(card)
        element = CARDOLOGY_SUIT_ELEMENTS.get(suit, Element.ETHER)
        
        # Theme and guidance from kernel
        theme = period_info.get("theme", f"{period} period energy")
        guidance = period_info.get("guidance", "")
        days_remaining = period_info.get("days_remaining", 0)
        
        return SystemReading(
            system_name="Cardology",
            timestamp=dt,
            primary_symbol=card,
            primary_name=card_name,
            element=element,
            archetype=f"{period} Period",
            keynote=theme,
            shadow=f"Unconscious {period} patterns",
            gift=f"Mastery of {period} energy",
            siddhi=f"Transcendence through {period}",
            cycle_day=52 - days_remaining if days_remaining else 1,
            cycle_total=52,
            cycle_percentage=((52 - days_remaining) / 52.0) if days_remaining else 0.5,
            metadata={
                "suit": suit,
                "planetary_period": period,
                "days_remaining": days_remaining,
                "guidance": guidance,
            }
        )
    
    def _global_transit_reading(self, dt: datetime) -> SystemReading:
        """Get universal card energy for the day (no birth date needed)."""
        try:
            from ..cardology import CardologyModule
            from ..cardology.kernel import calculate_card_number_for_date
            
            # Calculate the universal card for this date
            card_num = calculate_card_number_for_date(dt.date() if hasattr(dt, 'date') else dt)
            
            suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
            ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
            
            suit_idx = card_num // 13
            rank_idx = card_num % 13
            
            suit = suits[suit_idx] if suit_idx < 4 else "Spades"
            rank = ranks[rank_idx] if rank_idx < 13 else "K"
            
            symbol = f"{rank}{'♥♣♦♠'[suits.index(suit)]}"
            element = CARDOLOGY_SUIT_ELEMENTS.get(suit, Element.ETHER)
            
            # Calculate current planetary period (52-day universal cycle)
            day_of_year = dt.timetuple().tm_yday
            period_day = day_of_year % 52
            period_index = period_day // 7
            planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
            current_planet = planets[min(period_index, 6)]
            
            return SystemReading(
                system_name="Cardology",
                timestamp=dt,
                primary_symbol=symbol,
                primary_name=f"{rank} of {suit}",
                element=element,
                archetype=f"{current_planet} Period Card",
                keynote=f"{suit} energy in {current_planet} period",
                shadow=f"Unconscious {suit} patterns",
                gift=f"Mastery of {suit} gifts",
                siddhi=f"Transcendence through {suit}",
                cycle_day=period_day % 7 + 1,
                cycle_total=52,
                cycle_percentage=period_day / 52.0,
                metadata={
                    "suit": suit,
                    "rank": rank,
                    "planetary_period": current_planet,
                    "period_day": period_day,
                    "mode": "global_transit",
                }
            )
        except Exception:
            return self._demo_reading(dt)
    
    def _extract_suit(self, card: str) -> str:
        """Extract suit name from card symbol."""
        if "♥" in card or "Hearts" in card:
            return "Hearts"
        elif "♣" in card or "Clubs" in card:
            return "Clubs"
        elif "♦" in card or "Diamonds" in card:
            return "Diamonds"
        elif "♠" in card or "Spades" in card:
            return "Spades"
        return "Hearts"  # Default
    
    def _demo_reading(self, dt: datetime) -> SystemReading:
        """Generate demo reading when no kernel is connected."""
        # Calculate a pseudo-card based on date
        # This is a placeholder - actual implementation would use your CardologyKernel
        
        day_of_year = dt.timetuple().tm_yday
        card_index = day_of_year % 52
        
        suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        
        suit = suits[card_index // 13]
        rank = ranks[card_index % 13]
        
        symbol = f"{rank}{'♥♣♦♠'[suits.index(suit)]}"
        
        # Get element from suit
        element = CARDOLOGY_SUIT_ELEMENTS.get(suit, Element.ETHER)
        
        # Calculate planetary period (52-day cycle divided into 7 periods)
        period_day = day_of_year % 52
        period_index = period_day // 7
        planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
        current_planet = planets[min(period_index, 6)]
        
        # Generate frequency spectrum based on rank
        rank_value = ranks.index(rank) + 1
        shadow = f"Pattern of {rank_value}" if rank_value < 5 else "Ego attachment"
        gift = f"Power of {rank_value}" if rank_value < 5 else "Mastery"
        siddhi = f"Transcendence of {rank_value}" if rank_value < 5 else "Service"
        
        return SystemReading(
            system_name="Cardology",
            timestamp=dt,
            primary_symbol=symbol,
            primary_name=f"{rank} of {suit}",
            element=element,
            archetype=f"{current_planet} Period Card",
            keynote=f"{suit} energy in {current_planet} period",
            shadow=shadow,
            gift=gift,
            siddhi=siddhi,
            cycle_day=period_day % 7 + 1,
            cycle_total=52,
            cycle_percentage=period_day / 52.0,
            metadata={
                "suit": suit,
                "rank": rank,
                "planetary_period": current_planet,
                "period_day": period_day,
            }
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: CROSS-SYSTEM SYNTHESIS FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def cross_system_synthesis(
    card_reading: SystemReading,
    hexagram_reading: SystemReading
) -> Dict[str, Any]:
    """
    Calculate the resonance score between a Cardology card and I-Ching hexagram.
    
    This is the core function for the "Harmonic" synthesis model,
    treating both systems as equal inputs.
    
    Args:
        card_reading: SystemReading from Cardology
        hexagram_reading: SystemReading from I-Ching
        
    Returns:
        Dict with resonance_score and synthesis guidance
    """
    # Calculate elemental resonance
    elem_resonance = get_elemental_resonance(
        card_reading.element,
        hexagram_reading.element
    )
    
    # Calculate thematic resonance (simplified keyword matching)
    # In production, this would use NLP/embeddings for semantic similarity
    thematic_score = 0.5  # Default neutral
    
    # Combine scores (equal weight)
    combined_score = (elem_resonance.score + thematic_score) / 2
    
    # Determine overall resonance type
    if combined_score >= 0.7:
        overall_type = ResonanceType.HARMONIC
    elif combined_score >= 0.5:
        overall_type = ResonanceType.SUPPORTIVE
    elif combined_score >= 0.3:
        overall_type = ResonanceType.CHALLENGING
    else:
        overall_type = ResonanceType.DISSONANT
    
    # Generate synthesis
    return {
        "resonance_score": combined_score,
        "resonance_type": overall_type.value,
        "elemental_resonance": {
            "score": elem_resonance.score,
            "type": elem_resonance.resonance_type.value,
            "description": elem_resonance.description,
        },
        "card": {
            "symbol": card_reading.primary_symbol,
            "element": card_reading.element.value,
            "archetype": card_reading.archetype,
        },
        "hexagram": {
            "symbol": hexagram_reading.primary_symbol,
            "element": hexagram_reading.element.value,
            "archetype": hexagram_reading.archetype,
        },
        "unified_frequency": {
            "shadow": f"{card_reading.shadow} ↔ {hexagram_reading.shadow}",
            "gift": f"{card_reading.gift} ↔ {hexagram_reading.gift}",
            "siddhi": f"{card_reading.siddhi} ↔ {hexagram_reading.siddhi}",
        },
        "synthesis_guidance": _generate_cross_synthesis_guidance(
            card_reading, hexagram_reading, overall_type
        ),
    }


def _generate_cross_synthesis_guidance(
    card: SystemReading,
    hexagram: SystemReading,
    resonance: ResonanceType
) -> str:
    """Generate guidance for the cross-system synthesis."""
    if resonance == ResonanceType.HARMONIC:
        return (
            f"The {card.primary_name} and {hexagram.primary_name} are in strong alignment. "
            f"Your {card.element.value} nature resonates with {hexagram.element.value} energy. "
            f"Lean into {card.gift} and {hexagram.gift} for optimal expression."
        )
    elif resonance == ResonanceType.SUPPORTIVE:
        return (
            f"The {card.primary_name} supports the energy of {hexagram.primary_name}. "
            f"Use your {card.gift} to enhance {hexagram.gift}."
        )
    elif resonance == ResonanceType.CHALLENGING:
        return (
            f"Creative tension exists between {card.primary_name} and {hexagram.primary_name}. "
            f"The {card.element.value}/{hexagram.element.value} dynamic invites growth. "
            f"Transform {card.shadow}/{hexagram.shadow} into {card.gift}/{hexagram.gift}."
        )
    else:
        return (
            f"Significant opposition between {card.primary_name} and {hexagram.primary_name}. "
            f"This is a transformation portal. Release attachment to {card.shadow} and {hexagram.shadow}."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: DEMONSTRATION & TESTING
# ═══════════════════════════════════════════════════════════════════════════════

def run_synthesis_demo():
    """Demonstrate the Harmonic Synthesis system."""
    print("\n" + "=" * 80)
    print("HARMONIC SYNTHESIS - COUNCIL OF SYSTEMS DEMO")
    print("=" * 80)
    
    # Try to import the I-Ching kernel
    try:
        from iching_kernel import IChingKernel
        kernel = IChingKernel()
        print("\n✅ I-Ching Kernel loaded successfully")
    except ImportError:
        print("\n⚠️ I-Ching Kernel not found, using mock data")
        kernel = None
    
    # Create the Council
    council = CouncilOfSystems()
    
    # Register adapters
    if kernel:
        council.register_system("I-Ching", IChingAdapter(kernel), weight=1.0)
    
    council.register_system("Cardology", CardologyAdapter(), weight=1.0)
    
    # Get current synthesis
    now = datetime.now(timezone.utc)
    synthesis = council.synthesize(now)
    
    # Display results
    print("\n" + "-" * 60)
    print(f"SYNTHESIS FOR: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("-" * 60)
    
    print("\n📊 SYSTEM READINGS:")
    for reading in synthesis.systems:
        print(f"\n  {reading.system_name}:")
        print(f"    Symbol: {reading.primary_symbol}")
        print(f"    Name: {reading.primary_name}")
        print(f"    Element: {reading.element.value}")
        print(f"    Archetype: {reading.archetype}")
        print(f"    Cycle: Day {reading.cycle_day}/{reading.cycle_total}")
    
    print("\n🔮 RESONANCE:")
    print(f"  Score: {synthesis.resonance_score:.2f}")
    print(f"  Type: {synthesis.resonance_type.value}")
    print(f"  Description: {synthesis.resonance_description}")
    
    print("\n⚡ FREQUENCY SPECTRUM:")
    print(f"  Shadow: {synthesis.unified_shadow}")
    print(f"  Gift: {synthesis.unified_gift}")
    print(f"  Siddhi: {synthesis.unified_siddhi}")
    
    print("\n🌍 ELEMENTAL BALANCE:")
    print(f"  Dominant: {synthesis.dominant_element.value}")
    for elem, value in synthesis.elemental_balance.items():
        bar = "█" * int(value * 20)
        print(f"    {elem.value:8s}: {bar} ({value:.1%})")
    
    print("\n📜 THEMES:")
    print(f"  Macro (52-day): {synthesis.macro_theme}")
    print(f"  Micro (6-day): {synthesis.micro_theme}")
    print(f"\n  Synthesis: {synthesis.synthesis_guidance}")
    
    print("\n🎯 QUEST SUGGESTIONS:")
    for i, quest in enumerate(synthesis.quest_suggestions, 1):
        print(f"  {i}. {quest}")
    
    # Cross-system synthesis demo
    if len(synthesis.systems) >= 2:
        print("\n" + "-" * 60)
        print("CROSS-SYSTEM SYNTHESIS")
        print("-" * 60)
        
        card = synthesis.systems[1] if synthesis.systems[1].system_name == "Cardology" else synthesis.systems[0]
        hexagram = synthesis.systems[0] if synthesis.systems[0].system_name == "I-Ching" else synthesis.systems[1]
        
        cross = cross_system_synthesis(card, hexagram)
        print(f"\n  {card.primary_symbol} ↔ {hexagram.primary_symbol}")
        print(f"  Resonance Score: {cross['resonance_score']:.2f}")
        print(f"  Type: {cross['resonance_type']}")
        print(f"\n  Guidance: {cross['synthesis_guidance']}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_synthesis_demo()
