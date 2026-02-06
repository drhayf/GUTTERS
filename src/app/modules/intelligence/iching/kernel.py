"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        I-CHING LOGIC KERNEL v1.0                             ║
║                                                                              ║
║   A Stateless Implementation of the Binary Cosmic Code                       ║
║   Integrating: I-Ching Classical + Human Design + Gene Keys                  ║
║                                                                              ║
║   Mathematical Foundation:                                                   ║
║   - 64 Gates mapped to 360° ecliptic (5.625° per gate)                      ║
║   - 6 Lines per gate (0.9375° per line)                                     ║
║   - 6 Colors per line (0.15625° per color)                                  ║
║   - 6 Tones per color (~0.026° per tone)                                    ║
║   - 5 Bases per tone (~0.0052° per base)                                    ║
║                                                                              ║
║   Zodiac System: Fixed Tropical (No Precession Correction)                   ║
║   Offset: 58° (Gate 41 begins at 302° / Aquarius 2°)                        ║
║                                                                              ║
║   Author: GUTTERS Project / Magi OS                                          ║
║   License: For metaphysical research and consciousness development           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: FOUNDATIONAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# The I-Ching offset synchronizes the zodiac wheel (0° Aries) with the Gate wheel
# Gate 41 begins at 302° tropical (2° Aquarius)
ICHING_OFFSET = 58  # Degrees

# Degrees per division (derived from 360° / 64 gates)
DEGREES_PER_GATE = 360 / 64      # 5.625°
DEGREES_PER_LINE = 360 / 384     # 0.9375° (64 * 6 = 384 lines)
DEGREES_PER_COLOR = 360 / 2304   # 0.15625° (384 * 6 = 2304 colors)
DEGREES_PER_TONE = 360 / 13824   # ~0.026° (2304 * 6 = 13824 tones)
DEGREES_PER_BASE = 360 / 69120   # ~0.0052° (13824 * 5 = 69120 bases)

# Human Design 88° Solar Arc for Design calculation
DESIGN_ARC_DEGREES = 88

# The Gate Circle - 64 gates in wheel order starting from Gate 41 at 302°
# This is the Rave Mandala sequence, NOT the King Wen sequence
GATE_CIRCLE = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# Reverse lookup: Gate number -> Index in circle (for position calculations)
GATE_TO_INDEX = {gate: idx for idx, gate in enumerate(GATE_CIRCLE)}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: TRIGRAM DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Trigram(Enum):
    """
    The 8 Trigrams (Bagua) - building blocks of hexagrams.
    Each trigram is a 3-bit binary pattern.

    Binary notation: 1 = Yang (solid line ━━━), 0 = Yin (broken line ━ ━)
    Read from bottom to top.
    """
    HEAVEN = ("111", "☰", "Qian", "Creative", "Heaven", "Father")
    EARTH = ("000", "☷", "Kun", "Receptive", "Earth", "Mother")
    THUNDER = ("001", "☳", "Zhen", "Arousing", "Thunder", "Eldest Son")
    WATER = ("010", "☵", "Kan", "Abysmal", "Water", "Middle Son")
    MOUNTAIN = ("100", "☶", "Gen", "Keeping Still", "Mountain", "Youngest Son")
    WIND = ("110", "☴", "Xun", "Gentle", "Wind/Wood", "Eldest Daughter")
    FIRE = ("101", "☲", "Li", "Clinging", "Fire", "Middle Daughter")
    LAKE = ("011", "☱", "Dui", "Joyous", "Lake", "Youngest Daughter")

    def __init__(self, binary: str, symbol: str, chinese: str,
                 quality: str, element: str, family: str):
        self.binary = binary
        self.symbol = symbol
        self.chinese = chinese
        self.quality = quality
        self.element = element
        self.family = family


# Binary to Trigram lookup
BINARY_TO_TRIGRAM = {t.binary: t for t in Trigram}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: LINE ARCHETYPES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LineArchetype:
    """Archetype definition for each of the 6 lines."""
    number: int
    name: str
    theme: str
    profile_role: str
    description: str


LINE_ARCHETYPES = {
    1: LineArchetype(
        number=1,
        name="Investigator",
        theme="Foundation / Introspection",
        profile_role="The Foundation",
        description="Seeks security through knowledge. Must understand deeply before acting."
    ),
    2: LineArchetype(
        number=2,
        name="Hermit",
        theme="Projection / Natural Talent",
        profile_role="The Naturalist",
        description="Possesses natural gifts. Waits to be called out. Selective engagement."
    ),
    3: LineArchetype(
        number=3,
        name="Martyr",
        theme="Adaptation / Trial and Error",
        profile_role="The Experimenter",
        description="Learns through experience and mistakes. Resilient. Discovers what doesn't work."
    ),
    4: LineArchetype(
        number=4,
        name="Opportunist",
        theme="Externalization / Network",
        profile_role="The Networker",
        description="Influences through relationships. Fixed in foundation, flexible in expression."
    ),
    5: LineArchetype(
        number=5,
        name="Heretic",
        theme="Universalization / Projection Field",
        profile_role="The General",
        description="Others project expectations. Must deliver practical solutions. Seductive."
    ),
    6: LineArchetype(
        number=6,
        name="Role Model",
        theme="Transition / Objectivity",
        profile_role="The Administrator",
        description="Three-part life: experimentation, retreat, emergence as example."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: THE COMPLETE 64-GATE DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LineInterpretation:
    """Individual line interpretation within a gate."""
    number: int                    # 1-6
    name: str                      # Line name/archetype
    keynote: str                   # Primary theme
    description: str               # Full interpretation
    exaltation: str | None = None  # Planetary exaltation
    detriment: str | None = None   # Planetary detriment


@dataclass
class GateData:
    """
    Complete semantic data for a single Gate/Hexagram.

    Integrates three wisdom traditions:
    - I-Ching: Classical Chinese oracle (King Wen sequence)
    - Human Design: Ra Uru Hu's mechanical keywords
    - Gene Keys: Richard Rudd's frequency spectrum
    """
    # Core Identity
    number: int                    # 1-64
    binary: str                    # 6-bit string, e.g., "111111"
    king_wen_sequence: int         # Position in traditional I-Ching order

    # Trigram Composition (bottom to top)
    lower_trigram: str             # Binary of lower trigram
    upper_trigram: str             # Binary of upper trigram

    # I-Ching Layer
    iching_name: str               # Traditional name (e.g., "The Creative")
    iching_chinese: str            # Chinese characters
    iching_pinyin: str             # Romanization
    iching_judgment: str           # Core oracle text
    iching_image: str              # The Image text

    # Human Design Layer
    hd_name: str                   # Ra's gate name
    hd_keynote: str                # Primary keyword
    hd_center: str                 # Which center this gate belongs to
    hd_circuit: str                # Circuit group
    hd_stream: str                 # Stream within circuit

    # Gene Keys Layer (The Frequency Spectrum)
    gk_shadow: str                 # Low frequency expression
    gk_gift: str                   # Balanced frequency expression
    gk_siddhi: str                 # High frequency expression
    gk_programming_partner: int    # The complementary gate
    gk_codon_ring: str             # Genetic grouping
    gk_amino_acid: str             # Associated amino acid

    # Wheel Position
    wheel_index: int               # Position in Rave Mandala (0-63)
    start_degree: float            # Starting longitude on wheel
    zodiac_sign: str               # Sign where gate begins
    zodiac_degree: float           # Degree within sign

    # Line Interpretations (Enhanced in Phase 26.1)
    lines: dict[int, LineInterpretation] | None = None

    # Gate Relationships (Enhanced in Phase 26.1)
    harmonious_gates: list[int] | None = None   # Gates that support this gate
    challenging_gates: list[int] | None = None  # Gates that tension this gate
    keywords: list[str] | None = None           # Quick reference keywords


# The complete 64-gate database
# Each entry contains full I-Ching, Human Design, and Gene Keys data
GATE_DATABASE: Dict[int, GateData] = {

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 1: THE CREATIVE
    # ═══════════════════════════════════════════════════════════════════════════
    1: GateData(
        number=1,
        binary="111111",
        king_wen_sequence=1,
        lower_trigram="111",  # Heaven
        upper_trigram="111",  # Heaven

        # I-Ching
        iching_name="The Creative",
        iching_chinese="乾",
        iching_pinyin="Qián",
        iching_judgment="The Creative works sublime success, furthering through perseverance.",
        iching_image=(
            "The movement of heaven is full of power. Thus the superior man "
            "makes himself strong and untiring."
        ),

        # Human Design
        hd_name="The Gate of Self-Expression",
        hd_keynote="Creative Self-Expression",
        hd_center="G",
        hd_circuit="Individual",
        hd_stream="Knowing",

        # Gene Keys
        gk_shadow="Entropy",
        gk_gift="Freshness",
        gk_siddhi="Beauty",
        gk_programming_partner=2,
        gk_codon_ring="Ring of Fire",
        gk_amino_acid="Glycine",

        # Wheel Position (calculated)
        wheel_index=50,
        start_degree=223.25,
        zodiac_sign="Scorpio",
        zodiac_degree=13.25,

        # Line Interpretations
        lines={
            1: LineInterpretation(
                number=1,
                name="Creativity is Primal",
                keynote="Hidden dragon. Do not act.",
                description=(
                    "Creative potential exists but timing isn't right. Preparation "
                    "phase. The foundation is being built."
                ),
                exaltation="Saturn",
                detriment="Jupiter"
            ),
            2: LineInterpretation(
                number=2,
                name="Love is Light",
                keynote="Dragon appearing in the field. It furthers one to see the great person.",
                description="Emerging creativity. Beginning to share your unique expression. Testing the waters.",
                exaltation="Jupiter",
                detriment="Venus"
            ),
            3: LineInterpretation(
                number=3,
                name="Energy for Individuality & Change",
                keynote="All day long creative, at nightfall still creative. Dangerous. Blameless.",
                description=(
                    "Sustained creative effort. Tireless innovation. Risk of burnout "
                    "but necessary for breakthrough."
                ),
                exaltation="Mars",
                detriment="Saturn"
            ),
            4: LineInterpretation(
                number=4,
                name="Aloneness as Foundation of Leadership",
                keynote="Wavering flight over the depths. No blame.",
                description=(
                    "Testing your wings. Creative uncertainty. Exploring possibilities "
                    "without full commitment."
                ),
                exaltation="Venus",
                detriment="Mars"
            ),
            5: LineInterpretation(
                number=5,
                name="Objectivity - The Acceptance of Your Uniqueness",
                keynote="Flying dragon in the heavens. It furthers one to see the great person.",
                description="Full creative expression. Confidence in uniqueness. Leadership through authentic being.",
                exaltation="Sun",
                detriment="Moon"
            ),
            6: LineInterpretation(
                number=6,
                name="Excess: Objectivity through Interaction",
                keynote="Arrogant dragon will have cause to repent.",
                description="Overextension of creativity. Learn limits. Wisdom comes through recognizing boundaries.",
                exaltation="Moon",
                detriment="Sun"
            ),
        },

        # Gate Relationships
        harmonious_gates=[8, 13, 10, 25, 7],  # Creative flow partners
        challenging_gates=[2, 14, 43],         # Tension with receptive/response gates
        keywords=["creativity", "self-expression", "individuality", "innovation", "originality"]
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 2: THE RECEPTIVE
    # ═══════════════════════════════════════════════════════════════════════════
    2: GateData(
        number=2,
        binary="000000",
        king_wen_sequence=2,
        lower_trigram="000",  # Earth
        upper_trigram="000",  # Earth

        iching_name="The Receptive",
        iching_chinese="坤",
        iching_pinyin="Kūn",
        iching_judgment=(
            "The Receptive brings about sublime success, furthering through the "
            "perseverance of a mare."
        ),
        iching_image=(
            "The earth's condition is receptive devotion. Thus the superior man "
            "who has breadth of character carries the outer world."
        ),

        hd_name="The Gate of the Direction of the Self",
        hd_keynote="The Keeper of Keys",
        hd_center="G",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Dislocation",
        gk_gift="Orientation",
        gk_siddhi="Unity",
        gk_programming_partner=1,
        gk_codon_ring="Ring of Fire",
        gk_amino_acid="Glycine",

        wheel_index=18,
        start_degree=43.25,
        zodiac_sign="Taurus",
        zodiac_degree=13.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 3: DIFFICULTY AT THE BEGINNING
    # ═══════════════════════════════════════════════════════════════════════════
    3: GateData(
        number=3,
        binary="010001",
        king_wen_sequence=3,
        lower_trigram="001",  # Thunder
        upper_trigram="010",  # Water

        iching_name="Difficulty at the Beginning",
        iching_chinese="屯",
        iching_pinyin="Zhūn",
        iching_judgment="Difficulty at the beginning works supreme success. Furthering through perseverance.",
        iching_image="Clouds and thunder: the image of difficulty at the beginning.",

        hd_name="The Gate of Ordering",
        hd_keynote="Innovation through Mutation",
        hd_center="Sacral",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Chaos",
        gk_gift="Innovation",
        gk_siddhi="Innocence",
        gk_programming_partner=50,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=15,
        start_degree=26.375,
        zodiac_sign="Aries",
        zodiac_degree=26.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 4: YOUTHFUL FOLLY
    # ═══════════════════════════════════════════════════════════════════════════
    4: GateData(
        number=4,
        binary="100010",
        king_wen_sequence=4,
        lower_trigram="010",  # Water
        upper_trigram="100",  # Mountain

        iching_name="Youthful Folly",
        iching_chinese="蒙",
        iching_pinyin="Méng",
        iching_judgment="Youthful folly has success. It is not I who seek the young fool; the young fool seeks me.",
        iching_image="A spring wells up at the foot of the mountain: the image of youth.",

        hd_name="The Gate of Formulization",
        hd_keynote="Mental Answers and Solutions",
        hd_center="Ajna",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Intolerance",
        gk_gift="Understanding",
        gk_siddhi="Forgiveness",
        gk_programming_partner=49,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=35,
        start_degree=138.875,
        zodiac_sign="Leo",
        zodiac_degree=18.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 5: WAITING
    # ═══════════════════════════════════════════════════════════════════════════
    5: GateData(
        number=5,
        binary="010111",
        king_wen_sequence=5,
        lower_trigram="111",  # Heaven
        upper_trigram="010",  # Water

        iching_name="Waiting",
        iching_chinese="需",
        iching_pinyin="Xū",
        iching_judgment=(
            "Waiting. If you are sincere, you have light and success. "
            "Perseverance brings good fortune."
        ),
        iching_image=(
            "Clouds rise up to heaven: the image of waiting. Thus the superior "
            "man eats and drinks, is joyous and of good cheer."
        ),

        hd_name="The Gate of Fixed Patterns",
        hd_keynote="Waiting for Universal Timing",
        hd_center="Sacral",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Impatience",
        gk_gift="Patience",
        gk_siddhi="Timelessness",
        gk_programming_partner=35,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=55,
        start_degree=251.375,
        zodiac_sign="Sagittarius",
        zodiac_degree=11.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 6: CONFLICT
    # ═══════════════════════════════════════════════════════════════════════════
    6: GateData(
        number=6,
        binary="111010",
        king_wen_sequence=6,
        lower_trigram="010",  # Water
        upper_trigram="111",  # Heaven

        iching_name="Conflict",
        iching_chinese="訟",
        iching_pinyin="Sòng",
        iching_judgment="Conflict. You are sincere and being obstructed. A cautious halt halfway brings good fortune.",
        iching_image="Heaven and water go their opposite ways: the image of conflict.",

        hd_name="The Gate of Friction",
        hd_keynote="Emotional Intimacy",
        hd_center="Solar Plexus",
        hd_circuit="Tribal",
        hd_stream="Defense",

        gk_shadow="Conflict",
        gk_gift="Diplomacy",
        gk_siddhi="Peace",
        gk_programming_partner=36,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=41,
        start_degree=172.625,
        zodiac_sign="Virgo",
        zodiac_degree=22.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 7: THE ARMY
    # ═══════════════════════════════════════════════════════════════════════════
    7: GateData(
        number=7,
        binary="000010",
        king_wen_sequence=7,
        lower_trigram="010",  # Water
        upper_trigram="000",  # Earth

        iching_name="The Army",
        iching_chinese="師",
        iching_pinyin="Shī",
        iching_judgment="The army needs perseverance and a strong man. Good fortune without blame.",
        iching_image="In the middle of the earth is water: the image of the army.",

        hd_name="The Gate of the Role of the Self",
        hd_keynote="Leadership by Example",
        hd_center="G",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Division",
        gk_gift="Guidance",
        gk_siddhi="Virtue",
        gk_programming_partner=13,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=34,
        start_degree=133.25,
        zodiac_sign="Leo",
        zodiac_degree=13.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 8: HOLDING TOGETHER
    # ═══════════════════════════════════════════════════════════════════════════
    8: GateData(
        number=8,
        binary="010000",
        king_wen_sequence=8,
        lower_trigram="000",  # Earth
        upper_trigram="010",  # Water

        iching_name="Holding Together",
        iching_chinese="比",
        iching_pinyin="Bǐ",
        iching_judgment=(
            "Holding together brings good fortune. Inquire of the oracle once "
            "again whether you possess sublimity, constancy, and perseverance."
        ),
        iching_image="On the earth is water: the image of holding together.",

        hd_name="The Gate of Contribution",
        hd_keynote="The Creative Role Model",
        hd_center="Throat",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Mediocrity",
        gk_gift="Style",
        gk_siddhi="Exquisiteness",
        gk_programming_partner=14,
        gk_codon_ring="Ring of Water",
        gk_amino_acid="Alanine",

        wheel_index=20,
        start_degree=54.5,
        zodiac_sign="Taurus",
        zodiac_degree=24.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 9: THE TAMING POWER OF THE SMALL
    # ═══════════════════════════════════════════════════════════════════════════
    9: GateData(
        number=9,
        binary="110111",
        king_wen_sequence=9,
        lower_trigram="111",  # Heaven
        upper_trigram="110",  # Wind

        iching_name="The Taming Power of the Small",
        iching_chinese="小畜",
        iching_pinyin="Xiǎo Chù",
        iching_judgment="The taming power of the small has success. Dense clouds, no rain from our western region.",
        iching_image="The wind drives across heaven: the image of the taming power of the small.",

        hd_name="The Gate of Focus",
        hd_keynote="The Power of Detail",
        hd_center="Sacral",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Inertia",
        gk_gift="Determination",
        gk_siddhi="Invincibility",
        gk_programming_partner=16,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Histidine",

        wheel_index=54,
        start_degree=245.75,
        zodiac_sign="Sagittarius",
        zodiac_degree=5.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 10: TREADING
    # ═══════════════════════════════════════════════════════════════════════════
    10: GateData(
        number=10,
        binary="111011",
        king_wen_sequence=10,
        lower_trigram="011",  # Lake
        upper_trigram="111",  # Heaven

        iching_name="Treading",
        iching_chinese="履",
        iching_pinyin="Lǚ",
        iching_judgment="Treading upon the tail of the tiger. It does not bite the man. Success.",
        iching_image="Heaven above, the lake below: the image of treading.",

        hd_name="The Gate of Behavior of the Self",
        hd_keynote="Love of Self",
        hd_center="G",
        hd_circuit="Individual",
        hd_stream="Centering",

        gk_shadow="Self-Obsession",
        gk_gift="Naturalness",
        gk_siddhi="Being",
        gk_programming_partner=15,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Proline",

        wheel_index=58,
        start_degree=268.25,
        zodiac_sign="Sagittarius",
        zodiac_degree=28.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 11: PEACE
    # ═══════════════════════════════════════════════════════════════════════════
    11: GateData(
        number=11,
        binary="000111",
        king_wen_sequence=11,
        lower_trigram="111",  # Heaven
        upper_trigram="000",  # Earth

        iching_name="Peace",
        iching_chinese="泰",
        iching_pinyin="Tài",
        iching_judgment="Peace. The small departs, the great approaches. Good fortune. Success.",
        iching_image="Heaven and earth unite: the image of peace.",

        hd_name="The Gate of Ideas",
        hd_keynote="A Seeker of Harmony",
        hd_center="Ajna",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Obscurity",
        gk_gift="Idealism",
        gk_siddhi="Light",
        gk_programming_partner=12,
        gk_codon_ring="Ring of Light",
        gk_amino_acid="Leucine",

        wheel_index=57,
        start_degree=262.625,
        zodiac_sign="Sagittarius",
        zodiac_degree=22.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 12: STANDSTILL
    # ═══════════════════════════════════════════════════════════════════════════
    12: GateData(
        number=12,
        binary="111000",
        king_wen_sequence=12,
        lower_trigram="000",  # Earth
        upper_trigram="111",  # Heaven

        iching_name="Standstill",
        iching_chinese="否",
        iching_pinyin="Pǐ",
        iching_judgment="Standstill. Evil people do not further the perseverance of the superior man.",
        iching_image="Heaven and earth do not unite: the image of standstill.",

        hd_name="The Gate of Caution",
        hd_keynote="Caution in Expression",
        hd_center="Throat",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Vanity",
        gk_gift="Discrimination",
        gk_siddhi="Purity",
        gk_programming_partner=11,
        gk_codon_ring="Ring of Light",
        gk_amino_acid="Leucine",

        wheel_index=25,
        start_degree=82.625,
        zodiac_sign="Gemini",
        zodiac_degree=22.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 13: FELLOWSHIP WITH MEN
    # ═══════════════════════════════════════════════════════════════════════════
    13: GateData(
        number=13,
        binary="111101",
        king_wen_sequence=13,
        lower_trigram="101",  # Fire
        upper_trigram="111",  # Heaven

        iching_name="Fellowship with Men",
        iching_chinese="同人",
        iching_pinyin="Tóng Rén",
        iching_judgment="Fellowship with men in the open. Success. It furthers one to cross the great water.",
        iching_image="Heaven together with fire: the image of fellowship with men.",

        hd_name="The Gate of the Listener",
        hd_keynote="The Fellowship of Humanity",
        hd_center="G",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Discord",
        gk_gift="Discernment",
        gk_siddhi="Empathy",
        gk_programming_partner=7,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=2,
        start_degree=313.25,
        zodiac_sign="Aquarius",
        zodiac_degree=13.25,

        # Line Interpretations
        lines={
            1: LineInterpretation(
                number=1,
                name="Fellowship with Men",
                keynote="Fellowship at the gate. No blame.",
                description=(
                    "Open and honest communication. Building community from the "
                    "foundation. Welcoming all without prejudice."
                ),
                exaltation="Neptune",
                detriment="Mercury"
            ),
            2: LineInterpretation(
                number=2,
                name="Bigotry",
                keynote="Fellowship with men in the clan. Humiliation.",
                description="Selective association. Creating in-groups and out-groups. Learning the cost of exclusion.",
                exaltation="Saturn",
                detriment="Jupiter"
            ),
            3: LineInterpretation(
                number=3,
                name="Pessimism",
                keynote="He hides weapons in the thicket; he climbs the high hill in front of it.",
                description="Suspicious listening. Defensive posture in relationships. Protection through mistrust.",
                exaltation="Pluto",
                detriment="Venus"
            ),
            4: LineInterpretation(
                number=4,
                name="Fatigue",
                keynote="He climbs up on his wall; he cannot attack. Good fortune.",
                description="Exhausted by discord. Recognizing the futility of conflict. Wisdom through weariness.",
                exaltation="Mars",
                detriment="Neptune"
            ),
            5: LineInterpretation(
                number=5,
                name="The Savior",
                keynote="Men bound in fellowship first weep and lament, but afterward laugh.",
                description=(
                    "Mediator energy. Bringing opposing sides together. Joy "
                    "follows the hard work of reconciliation."
                ),
                exaltation="Venus",
                detriment="Saturn"
            ),
            6: LineInterpretation(
                number=6,
                name="The Optimist",
                keynote="Fellowship with men in the meadow. No remorse.",
                description="Universal fellowship. Seeing the humanity in all. Natural empathy without effort.",
                exaltation="Jupiter",
                detriment="Pluto"
            ),
        },

        # Gate Relationships
        harmonious_gates=[7, 1, 43, 25],     # Direction, creativity, insight, innocence
        challenging_gates=[31, 33, 10],      # Influence, retreat, behavior
        keywords=["listening", "fellowship", "discernment", "empathy", "community", "hearing"]
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 14: POSSESSION IN GREAT MEASURE
    # ═══════════════════════════════════════════════════════════════════════════
    14: GateData(
        number=14,
        binary="101111",
        king_wen_sequence=14,
        lower_trigram="111",  # Heaven
        upper_trigram="101",  # Fire

        iching_name="Possession in Great Measure",
        iching_chinese="大有",
        iching_pinyin="Dà Yǒu",
        iching_judgment="Possession in great measure. Supreme success.",
        iching_image="Fire in heaven above: the image of possession in great measure.",

        hd_name="The Gate of Power Skills",
        hd_keynote="Blessed with Wealth",
        hd_center="Sacral",
        hd_circuit="Individual",
        hd_stream="Empowering",

        gk_shadow="Compromise",
        gk_gift="Competence",
        gk_siddhi="Bounteousness",
        gk_programming_partner=8,
        gk_codon_ring="Ring of Water",
        gk_amino_acid="Alanine",

        wheel_index=52,
        start_degree=234.5,
        zodiac_sign="Scorpio",
        zodiac_degree=24.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 15: MODESTY
    # ═══════════════════════════════════════════════════════════════════════════
    15: GateData(
        number=15,
        binary="000100",
        king_wen_sequence=15,
        lower_trigram="100",  # Mountain
        upper_trigram="000",  # Earth

        iching_name="Modesty",
        iching_chinese="謙",
        iching_pinyin="Qiān",
        iching_judgment="Modesty creates success. The superior man carries things through.",
        iching_image="Within the earth, a mountain: the image of modesty.",

        hd_name="The Gate of Extremes",
        hd_keynote="Love of Humanity",
        hd_center="G",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Dullness",
        gk_gift="Magnetism",
        gk_siddhi="Florescence",
        gk_programming_partner=10,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Proline",

        wheel_index=26,
        start_degree=88.25,
        zodiac_sign="Gemini",
        zodiac_degree=28.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 16: ENTHUSIASM
    # ═══════════════════════════════════════════════════════════════════════════
    16: GateData(
        number=16,
        binary="001000",
        king_wen_sequence=16,
        lower_trigram="000",  # Earth
        upper_trigram="001",  # Thunder

        iching_name="Enthusiasm",
        iching_chinese="豫",
        iching_pinyin="Yù",
        iching_judgment="Enthusiasm. It furthers one to install helpers and to set armies marching.",
        iching_image="Thunder comes resounding out of the earth: the image of enthusiasm.",

        hd_name="The Gate of Skills",
        hd_keynote="Mastery through Enthusiasm",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Indifference",
        gk_gift="Versatility",
        gk_siddhi="Mastery",
        gk_programming_partner=9,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Histidine",

        wheel_index=22,
        start_degree=65.75,
        zodiac_sign="Gemini",
        zodiac_degree=5.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 17: FOLLOWING
    # ═══════════════════════════════════════════════════════════════════════════
    17: GateData(
        number=17,
        binary="011001",
        king_wen_sequence=17,
        lower_trigram="001",  # Thunder
        upper_trigram="011",  # Lake

        iching_name="Following",
        iching_chinese="隨",
        iching_pinyin="Suí",
        iching_judgment="Following has supreme success. Perseverance furthers. No blame.",
        iching_image="Thunder in the middle of the lake: the image of following.",

        hd_name="The Gate of Opinions",
        hd_keynote="Organizing with Logic",
        hd_center="Ajna",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Opinion",
        gk_gift="Far-Sightedness",
        gk_siddhi="Omniscience",
        gk_programming_partner=18,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=11,
        start_degree=3.875,
        zodiac_sign="Aries",
        zodiac_degree=3.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 18: WORK ON WHAT HAS BEEN SPOILED
    # ═══════════════════════════════════════════════════════════════════════════
    18: GateData(
        number=18,
        binary="100110",
        king_wen_sequence=18,
        lower_trigram="110",  # Wind
        upper_trigram="100",  # Mountain

        iching_name="Work on What Has Been Spoiled",
        iching_chinese="蠱",
        iching_pinyin="Gǔ",
        iching_judgment="Work on what has been spoiled has supreme success. It furthers one to cross the great water.",
        iching_image="The wind blows low on the mountain: the image of decay.",

        hd_name="The Gate of Correction",
        hd_keynote="The Drive to Correct",
        hd_center="Spleen",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Judgement",
        gk_gift="Integrity",
        gk_siddhi="Perfection",
        gk_programming_partner=17,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=43,
        start_degree=183.875,
        zodiac_sign="Libra",
        zodiac_degree=3.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 19: APPROACH
    # ═══════════════════════════════════════════════════════════════════════════
    19: GateData(
        number=19,
        binary="000011",
        king_wen_sequence=19,
        lower_trigram="011",  # Lake
        upper_trigram="000",  # Earth

        iching_name="Approach",
        iching_chinese="臨",
        iching_pinyin="Lín",
        iching_judgment=(
            "Approach has supreme success. Perseverance furthers. When the "
            "eighth month comes, there will be misfortune."
        ),
        iching_image="The earth above the lake: the image of approach.",

        hd_name="The Gate of Wanting",
        hd_keynote="The Pressure of Need",
        hd_center="Root",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Co-Dependence",
        gk_gift="Sensitivity",
        gk_siddhi="Sacrifice",
        gk_programming_partner=33,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=1,
        start_degree=307.625,
        zodiac_sign="Aquarius",
        zodiac_degree=7.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 20: CONTEMPLATION
    # ═══════════════════════════════════════════════════════════════════════════
    20: GateData(
        number=20,
        binary="110000",
        king_wen_sequence=20,
        lower_trigram="000",  # Earth
        upper_trigram="110",  # Wind

        iching_name="Contemplation",
        iching_chinese="觀",
        iching_pinyin="Guān",
        iching_judgment="Contemplation. The ablution has been made, but not yet the offering.",
        iching_image="The wind blows over the earth: the image of contemplation.",

        hd_name="The Gate of the Now",
        hd_keynote="Present Awareness",
        hd_center="Throat",
        hd_circuit="Individual",
        hd_stream="Integration",

        gk_shadow="Superficiality",
        gk_gift="Self-Assurance",
        gk_siddhi="Presence",
        gk_programming_partner=34,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=21,
        start_degree=60.125,
        zodiac_sign="Gemini",
        zodiac_degree=0.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 21: BITING THROUGH
    # ═══════════════════════════════════════════════════════════════════════════
    21: GateData(
        number=21,
        binary="101001",
        king_wen_sequence=21,
        lower_trigram="001",  # Thunder
        upper_trigram="101",  # Fire

        iching_name="Biting Through",
        iching_chinese="噬嗑",
        iching_pinyin="Shì Kè",
        iching_judgment="Biting through has success. It is favorable to let justice be administered.",
        iching_image="Thunder and lightning: the image of biting through.",

        hd_name="The Gate of the Hunter/Huntress",
        hd_keynote="Control of Resources",
        hd_center="Heart",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Control",
        gk_gift="Authority",
        gk_siddhi="Valour",
        gk_programming_partner=48,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=12,
        start_degree=9.5,
        zodiac_sign="Aries",
        zodiac_degree=9.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 22: GRACE
    # ═══════════════════════════════════════════════════════════════════════════
    22: GateData(
        number=22,
        binary="100101",
        king_wen_sequence=22,
        lower_trigram="101",  # Fire
        upper_trigram="100",  # Mountain

        iching_name="Grace",
        iching_chinese="賁",
        iching_pinyin="Bì",
        iching_judgment="Grace has success. In small matters it is favorable to undertake something.",
        iching_image="Fire at the foot of the mountain: the image of grace.",

        hd_name="The Gate of Openness",
        hd_keynote="Emotional Openness",
        hd_center="Solar Plexus",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Dishonour",
        gk_gift="Graciousness",
        gk_siddhi="Grace",
        gk_programming_partner=47,
        gk_codon_ring="Ring of Matter",
        gk_amino_acid="Isoleucine",

        wheel_index=8,
        start_degree=347.0,
        zodiac_sign="Pisces",
        zodiac_degree=17.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 23: SPLITTING APART
    # ═══════════════════════════════════════════════════════════════════════════
    23: GateData(
        number=23,
        binary="100000",
        king_wen_sequence=23,
        lower_trigram="000",  # Earth
        upper_trigram="100",  # Mountain

        iching_name="Splitting Apart",
        iching_chinese="剝",
        iching_pinyin="Bō",
        iching_judgment="Splitting apart. It does not further one to go anywhere.",
        iching_image="The mountain rests on the earth: the image of splitting apart.",

        hd_name="The Gate of Assimilation",
        hd_keynote="Communication of Knowing",
        hd_center="Throat",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Complexity",
        gk_gift="Simplicity",
        gk_siddhi="Quintessence",
        gk_programming_partner=43,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=19,
        start_degree=48.875,
        zodiac_sign="Taurus",
        zodiac_degree=18.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 24: RETURN
    # ═══════════════════════════════════════════════════════════════════════════
    24: GateData(
        number=24,
        binary="000001",
        king_wen_sequence=24,
        lower_trigram="001",  # Thunder
        upper_trigram="000",  # Earth

        iching_name="Return",
        iching_chinese="復",
        iching_pinyin="Fù",
        iching_judgment="Return. Success. Going out and coming in without error.",
        iching_image="Thunder within the earth: the image of the turning point.",

        hd_name="The Gate of Rationalization",
        hd_keynote="The Return to Knowing",
        hd_center="Ajna",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Addiction",
        gk_gift="Invention",
        gk_siddhi="Silence",
        gk_programming_partner=44,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=17,
        start_degree=37.625,
        zodiac_sign="Taurus",
        zodiac_degree=7.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 25: INNOCENCE
    # ═══════════════════════════════════════════════════════════════════════════
    25: GateData(
        number=25,
        binary="111001",
        king_wen_sequence=25,
        lower_trigram="001",  # Thunder
        upper_trigram="111",  # Heaven

        iching_name="Innocence",
        iching_chinese="無妄",
        iching_pinyin="Wú Wàng",
        iching_judgment="Innocence. Supreme success. Perseverance furthers.",
        iching_image="Under heaven thunder rolls: all things attain the natural state of innocence.",

        hd_name="The Gate of the Spirit of the Self",
        hd_keynote="Love of Spirit",
        hd_center="G",
        hd_circuit="Individual",
        hd_stream="Centering",

        gk_shadow="Constriction",
        gk_gift="Acceptance",
        gk_siddhi="Universal Love",
        gk_programming_partner=46,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Proline",

        wheel_index=10,
        start_degree=358.25,
        zodiac_sign="Pisces",
        zodiac_degree=28.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 26: THE TAMING POWER OF THE GREAT
    # ═══════════════════════════════════════════════════════════════════════════
    26: GateData(
        number=26,
        binary="100111",
        king_wen_sequence=26,
        lower_trigram="111",  # Heaven
        upper_trigram="100",  # Mountain

        iching_name="The Taming Power of the Great",
        iching_chinese="大畜",
        iching_pinyin="Dà Chù",
        iching_judgment="The taming power of the great. Perseverance furthers. Not eating at home brings good fortune.",
        iching_image="Heaven within the mountain: the image of the taming power of the great.",

        hd_name="The Gate of the Egoist",
        hd_keynote="The Accumulator",
        hd_center="Heart",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Pride",
        gk_gift="Artfulness",
        gk_siddhi="Invisibility",
        gk_programming_partner=45,
        gk_codon_ring="Ring of No Return",
        gk_amino_acid="Asparagine",

        wheel_index=56,
        start_degree=257.0,
        zodiac_sign="Sagittarius",
        zodiac_degree=17.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 27: NOURISHMENT
    # ═══════════════════════════════════════════════════════════════════════════
    27: GateData(
        number=27,
        binary="100001",
        king_wen_sequence=27,
        lower_trigram="001",  # Thunder
        upper_trigram="100",  # Mountain

        iching_name="The Corners of the Mouth (Nourishment)",
        iching_chinese="頤",
        iching_pinyin="Yí",
        iching_judgment=(
            "The corners of the mouth. Perseverance brings good fortune. "
            "Pay heed to the providing of nourishment and to what a man seeks to fill his own mouth with."
        ),
        iching_image=(
            "At the foot of the mountain, thunder: the image of providing "
            "nourishment."
        ),

        hd_name="The Gate of Caring",
        hd_keynote="Caring for Others",
        hd_center="Sacral",
        hd_circuit="Tribal",
        hd_stream="Defense",

        gk_shadow="Selfishness",
        gk_gift="Altruism",
        gk_siddhi="Selflessness",
        gk_programming_partner=28,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=16,
        start_degree=32.0,
        zodiac_sign="Taurus",
        zodiac_degree=2.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 28: PREPONDERANCE OF THE GREAT
    # ═══════════════════════════════════════════════════════════════════════════
    28: GateData(
        number=28,
        binary="011110",
        king_wen_sequence=28,
        lower_trigram="110",  # Wind
        upper_trigram="011",  # Lake

        iching_name="Preponderance of the Great",
        iching_chinese="大過",
        iching_pinyin="Dà Guò",
        iching_judgment=(
            "Preponderance of the great. The ridgepole sags to the breaking point. "
            "It furthers one to have somewhere to go."
        ),
        iching_image="The lake rises above the trees: the image of preponderance of the great.",

        hd_name="The Gate of the Game Player",
        hd_keynote="Risking for Purpose",
        hd_center="Spleen",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Purposelessness",
        gk_gift="Totality",
        gk_siddhi="Immortality",
        gk_programming_partner=27,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=48,
        start_degree=212.0,
        zodiac_sign="Scorpio",
        zodiac_degree=2.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 29: THE ABYSMAL
    # ═══════════════════════════════════════════════════════════════════════════
    29: GateData(
        number=29,
        binary="010010",
        king_wen_sequence=29,
        lower_trigram="010",  # Water
        upper_trigram="010",  # Water

        iching_name="The Abysmal (Water)",
        iching_chinese="坎",
        iching_pinyin="Kǎn",
        iching_judgment=(
            "The abysmal repeated. If you are sincere, you have success in your "
            "heart, and whatever you do succeeds."
        ),
        iching_image="Water flows on and reaches the goal: the image of the abysmal repeated.",

        hd_name="The Gate of Saying Yes",
        hd_keynote="Perseverance",
        hd_center="Sacral",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Half-Heartedness",
        gk_gift="Commitment",
        gk_siddhi="Devotion",
        gk_programming_partner=30,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=36,
        start_degree=144.5,
        zodiac_sign="Leo",
        zodiac_degree=24.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 30: THE CLINGING (FIRE)
    # ═══════════════════════════════════════════════════════════════════════════
    30: GateData(
        number=30,
        binary="101101",
        king_wen_sequence=30,
        lower_trigram="101",  # Fire
        upper_trigram="101",  # Fire

        iching_name="The Clinging (Fire)",
        iching_chinese="離",
        iching_pinyin="Lí",
        iching_judgment="The clinging. Perseverance furthers. It brings success. Care of the cow brings good fortune.",
        iching_image="That which is bright rises twice: the image of fire.",

        hd_name="The Gate of Recognition of Feelings",
        hd_keynote="The Clinging Fire",
        hd_center="Solar Plexus",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Desire",
        gk_gift="Lightness",
        gk_siddhi="Rapture",
        gk_programming_partner=29,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=4,
        start_degree=324.5,
        zodiac_sign="Aquarius",
        zodiac_degree=24.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 31: INFLUENCE
    # ═══════════════════════════════════════════════════════════════════════════
    31: GateData(
        number=31,
        binary="011100",
        king_wen_sequence=31,
        lower_trigram="100",  # Mountain
        upper_trigram="011",  # Lake

        iching_name="Influence (Wooing)",
        iching_chinese="咸",
        iching_pinyin="Xián",
        iching_judgment="Influence. Success. Perseverance furthers. To take a maiden to wife brings good fortune.",
        iching_image="A lake on the mountain: the image of influence.",

        hd_name="The Gate of Influence",
        hd_keynote="Leading through Influence",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Arrogance",
        gk_gift="Leadership",
        gk_siddhi="Humility",
        gk_programming_partner=41,
        gk_codon_ring="Ring of No Return",
        gk_amino_acid="Asparagine",

        wheel_index=32,
        start_degree=122.0,
        zodiac_sign="Leo",
        zodiac_degree=2.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 32: DURATION
    # ═══════════════════════════════════════════════════════════════════════════
    32: GateData(
        number=32,
        binary="001110",
        king_wen_sequence=32,
        lower_trigram="110",  # Wind
        upper_trigram="001",  # Thunder

        iching_name="Duration",
        iching_chinese="恆",
        iching_pinyin="Héng",
        iching_judgment="Duration. Success. No blame. Perseverance furthers. It furthers one to have somewhere to go.",
        iching_image="Thunder and wind: the image of duration.",

        hd_name="The Gate of Continuity",
        hd_keynote="Instinctive Continuity",
        hd_center="Spleen",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Failure",
        gk_gift="Preservation",
        gk_siddhi="Veneration",
        gk_programming_partner=42,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=46,
        start_degree=200.75,
        zodiac_sign="Libra",
        zodiac_degree=20.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 33: RETREAT
    # ═══════════════════════════════════════════════════════════════════════════
    33: GateData(
        number=33,
        binary="111100",
        king_wen_sequence=33,
        lower_trigram="100",  # Mountain
        upper_trigram="111",  # Heaven

        iching_name="Retreat",
        iching_chinese="遯",
        iching_pinyin="Dùn",
        iching_judgment="Retreat. Success. In what is small, perseverance furthers.",
        iching_image="Mountain under heaven: the image of retreat.",

        hd_name="The Gate of Privacy",
        hd_keynote="Memory and Retreat",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Forgetting",
        gk_gift="Mindfulness",
        gk_siddhi="Revelation",
        gk_programming_partner=19,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=33,
        start_degree=127.625,
        zodiac_sign="Leo",
        zodiac_degree=7.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 34: THE POWER OF THE GREAT
    # ═══════════════════════════════════════════════════════════════════════════
    34: GateData(
        number=34,
        binary="001111",
        king_wen_sequence=34,
        lower_trigram="111",  # Heaven
        upper_trigram="001",  # Thunder

        iching_name="The Power of the Great",
        iching_chinese="大壯",
        iching_pinyin="Dà Zhuàng",
        iching_judgment="The power of the great. Perseverance furthers.",
        iching_image="Thunder in heaven above: the image of the power of the great.",

        hd_name="The Gate of Power",
        hd_keynote="Pure Power Available",
        hd_center="Sacral",
        hd_circuit="Individual",
        hd_stream="Integration",

        gk_shadow="Force",
        gk_gift="Strength",
        gk_siddhi="Majesty",
        gk_programming_partner=20,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=53,
        start_degree=240.125,
        zodiac_sign="Sagittarius",
        zodiac_degree=0.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 35: PROGRESS
    # ═══════════════════════════════════════════════════════════════════════════
    35: GateData(
        number=35,
        binary="101000",
        king_wen_sequence=35,
        lower_trigram="000",  # Earth
        upper_trigram="101",  # Fire

        iching_name="Progress",
        iching_chinese="晉",
        iching_pinyin="Jìn",
        iching_judgment=(
            "Progress. The powerful prince is honored with horses in large numbers. "
            "In a single day he is granted audience three times."
        ),
        iching_image="The sun rises over the earth: the image of progress.",

        hd_name="The Gate of Change",
        hd_keynote="The Hunger for Experience",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Hunger",
        gk_gift="Adventure",
        gk_siddhi="Boundlessness",
        gk_programming_partner=5,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=23,
        start_degree=71.375,
        zodiac_sign="Gemini",
        zodiac_degree=11.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 36: DARKENING OF THE LIGHT
    # ═══════════════════════════════════════════════════════════════════════════
    36: GateData(
        number=36,
        binary="000101",
        king_wen_sequence=36,
        lower_trigram="101",  # Fire
        upper_trigram="000",  # Earth

        iching_name="Darkening of the Light",
        iching_chinese="明夷",
        iching_pinyin="Míng Yí",
        iching_judgment="Darkening of the light. In adversity it furthers one to be persevering.",
        iching_image="The light has sunk into the earth: the image of darkening of the light.",

        hd_name="The Gate of Crisis",
        hd_keynote="Inexperience as a Path",
        hd_center="Solar Plexus",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Turbulence",
        gk_gift="Humanity",
        gk_siddhi="Compassion",
        gk_programming_partner=6,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=9,
        start_degree=352.625,
        zodiac_sign="Pisces",
        zodiac_degree=22.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 37: THE FAMILY
    # ═══════════════════════════════════════════════════════════════════════════
    37: GateData(
        number=37,
        binary="110101",
        king_wen_sequence=37,
        lower_trigram="101",  # Fire
        upper_trigram="110",  # Wind

        iching_name="The Family",
        iching_chinese="家人",
        iching_pinyin="Jiā Rén",
        iching_judgment="The family. The perseverance of the woman furthers.",
        iching_image="Wind comes forth from fire: the image of the family.",

        hd_name="The Gate of Friendship",
        hd_keynote="Community & Family",
        hd_center="Solar Plexus",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Weakness",
        gk_gift="Equality",
        gk_siddhi="Tenderness",
        gk_programming_partner=40,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=6,
        start_degree=335.75,
        zodiac_sign="Pisces",
        zodiac_degree=5.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 38: OPPOSITION
    # ═══════════════════════════════════════════════════════════════════════════
    38: GateData(
        number=38,
        binary="101011",
        king_wen_sequence=38,
        lower_trigram="011",  # Lake
        upper_trigram="101",  # Fire

        iching_name="Opposition",
        iching_chinese="睽",
        iching_pinyin="Kuí",
        iching_judgment="Opposition. In small matters, good fortune.",
        iching_image="Above, fire; below, the lake: the image of opposition.",

        hd_name="The Gate of the Fighter",
        hd_keynote="The Will to Fight",
        hd_center="Root",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Struggle",
        gk_gift="Perseverance",
        gk_siddhi="Honour",
        gk_programming_partner=39,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=60,
        start_degree=279.5,
        zodiac_sign="Capricorn",
        zodiac_degree=9.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 39: OBSTRUCTION
    # ═══════════════════════════════════════════════════════════════════════════
    39: GateData(
        number=39,
        binary="010100",
        king_wen_sequence=39,
        lower_trigram="100",  # Mountain
        upper_trigram="010",  # Water

        iching_name="Obstruction",
        iching_chinese="蹇",
        iching_pinyin="Jiǎn",
        iching_judgment=(
            "Obstruction. The southwest furthers. The northeast does not further. "
            "It furthers one to see the great man. Perseverance brings good fortune."
        ),
        iching_image="Water on the mountain: the image of obstruction.",

        hd_name="The Gate of Provocation",
        hd_keynote="The Provoker",
        hd_center="Root",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Provocation",
        gk_gift="Dynamism",
        gk_siddhi="Liberation",
        gk_programming_partner=38,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=28,
        start_degree=99.5,
        zodiac_sign="Cancer",
        zodiac_degree=9.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 40: DELIVERANCE
    # ═══════════════════════════════════════════════════════════════════════════
    40: GateData(
        number=40,
        binary="001010",
        king_wen_sequence=40,
        lower_trigram="010",  # Water
        upper_trigram="001",  # Thunder

        iching_name="Deliverance",
        iching_chinese="解",
        iching_pinyin="Xiè",
        iching_judgment=(
            "Deliverance. The southwest furthers. If there is no longer anything "
            "where one has to go, return brings good fortune."
        ),
        iching_image="Thunder and rain set in: the image of deliverance.",

        hd_name="The Gate of Aloneness",
        hd_keynote="The Stomach—Loneliness",
        hd_center="Heart",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Exhaustion",
        gk_gift="Resolve",
        gk_siddhi="Divine Will",
        gk_programming_partner=37,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=38,
        start_degree=155.75,
        zodiac_sign="Virgo",
        zodiac_degree=5.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 41: DECREASE
    # ═══════════════════════════════════════════════════════════════════════════
    41: GateData(
        number=41,
        binary="100011",
        king_wen_sequence=41,
        lower_trigram="011",  # Lake
        upper_trigram="100",  # Mountain

        iching_name="Decrease",
        iching_chinese="損",
        iching_pinyin="Sǔn",
        iching_judgment="Decrease combined with sincerity brings about supreme good fortune without blame.",
        iching_image="At the foot of the mountain, the lake: the image of decrease.",

        hd_name="The Gate of Contraction",
        hd_keynote="The Start Codon",
        hd_center="Root",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Fantasy",
        gk_gift="Anticipation",
        gk_siddhi="Emanation",
        gk_programming_partner=31,
        gk_codon_ring="Ring of No Return",
        gk_amino_acid="Asparagine",

        wheel_index=0,
        start_degree=302.0,
        zodiac_sign="Aquarius",
        zodiac_degree=2.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 42: INCREASE
    # ═══════════════════════════════════════════════════════════════════════════
    42: GateData(
        number=42,
        binary="110001",
        king_wen_sequence=42,
        lower_trigram="001",  # Thunder
        upper_trigram="110",  # Wind

        iching_name="Increase",
        iching_chinese="益",
        iching_pinyin="Yì",
        iching_judgment="Increase. It furthers one to undertake something. It furthers one to cross the great water.",
        iching_image="Wind and thunder: the image of increase.",

        hd_name="The Gate of Growth",
        hd_keynote="Completion of Cycles",
        hd_center="Sacral",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Expectation",
        gk_gift="Detachment",
        gk_siddhi="Celebration",
        gk_programming_partner=32,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=14,
        start_degree=20.75,
        zodiac_sign="Aries",
        zodiac_degree=20.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 43: BREAKTHROUGH
    # ═══════════════════════════════════════════════════════════════════════════
    43: GateData(
        number=43,
        binary="011111",
        king_wen_sequence=43,
        lower_trigram="111",  # Heaven
        upper_trigram="011",  # Lake

        iching_name="Breakthrough (Resoluteness)",
        iching_chinese="夬",
        iching_pinyin="Guài",
        iching_judgment="Breakthrough. One must resolutely make the matter known at the court of the king.",
        iching_image="The lake has risen up to heaven: the image of breakthrough.",

        hd_name="The Gate of Insight",
        hd_keynote="Inner Resolution",
        hd_center="Ajna",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Deafness",
        gk_gift="Insight",
        gk_siddhi="Epiphany",
        gk_programming_partner=23,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=51,
        start_degree=228.875,
        zodiac_sign="Scorpio",
        zodiac_degree=18.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 44: COMING TO MEET
    # ═══════════════════════════════════════════════════════════════════════════
    44: GateData(
        number=44,
        binary="111110",
        king_wen_sequence=44,
        lower_trigram="110",  # Wind
        upper_trigram="111",  # Heaven

        iching_name="Coming to Meet",
        iching_chinese="姤",
        iching_pinyin="Gòu",
        iching_judgment="Coming to meet. The maiden is powerful. One should not marry such a maiden.",
        iching_image="Under heaven, wind: the image of coming to meet.",

        hd_name="The Gate of Alertness",
        hd_keynote="Patterns of the Past",
        hd_center="Spleen",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Interference",
        gk_gift="Teamwork",
        gk_siddhi="Synarchy",
        gk_programming_partner=24,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=49,
        start_degree=217.625,
        zodiac_sign="Scorpio",
        zodiac_degree=7.625
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 45: GATHERING TOGETHER
    # ═══════════════════════════════════════════════════════════════════════════
    45: GateData(
        number=45,
        binary="011000",
        king_wen_sequence=45,
        lower_trigram="000",  # Earth
        upper_trigram="011",  # Lake

        iching_name="Gathering Together",
        iching_chinese="萃",
        iching_pinyin="Cuì",
        iching_judgment=(
            "Gathering together. Success. The king approaches his temple. "
            "It furthers one to see the great man. This brings success. "
            "Perseverance furthers."
        ),
        iching_image="Over the earth, the lake: the image of gathering together.",

        hd_name="The Gate of the Gatherer",
        hd_keynote="The King or Queen",
        hd_center="Throat",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Dominance",
        gk_gift="Synergy",
        gk_siddhi="Communion",
        gk_programming_partner=26,
        gk_codon_ring="Ring of No Return",
        gk_amino_acid="Asparagine",

        wheel_index=24,
        start_degree=77.0,
        zodiac_sign="Gemini",
        zodiac_degree=17.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 46: PUSHING UPWARD
    # ═══════════════════════════════════════════════════════════════════════════
    46: GateData(
        number=46,
        binary="000110",
        king_wen_sequence=46,
        lower_trigram="110",  # Wind
        upper_trigram="000",  # Earth

        iching_name="Pushing Upward",
        iching_chinese="升",
        iching_pinyin="Shēng",
        iching_judgment=(
            "Pushing upward has supreme success. One must see the great man. "
            "Fear not. Departure toward the south brings good fortune."
        ),
        iching_image="Within the earth, wood grows: the image of pushing upward.",

        hd_name="The Gate of the Determination of the Self",
        hd_keynote="Love of Body",
        hd_center="G",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Seriousness",
        gk_gift="Delight",
        gk_siddhi="Ecstasy",
        gk_programming_partner=25,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Proline",

        wheel_index=42,
        start_degree=178.25,
        zodiac_sign="Virgo",
        zodiac_degree=28.25
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 47: OPPRESSION
    # ═══════════════════════════════════════════════════════════════════════════
    47: GateData(
        number=47,
        binary="011010",
        king_wen_sequence=47,
        lower_trigram="010",  # Water
        upper_trigram="011",  # Lake

        iching_name="Oppression (Exhaustion)",
        iching_chinese="困",
        iching_pinyin="Kùn",
        iching_judgment=(
            "Oppression. Success. Perseverance. The great man brings about good "
            "fortune. No blame. When one has something to say, it is not believed."
        ),
        iching_image="There is no water in the lake: the image of exhaustion.",

        hd_name="The Gate of Realization",
        hd_keynote="The Abstract Mind",
        hd_center="Ajna",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Oppression",
        gk_gift="Transmutation",
        gk_siddhi="Transfiguration",
        gk_programming_partner=22,
        gk_codon_ring="Ring of Matter",
        gk_amino_acid="Isoleucine",

        wheel_index=40,
        start_degree=167.0,
        zodiac_sign="Virgo",
        zodiac_degree=17.0
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 48: THE WELL
    # ═══════════════════════════════════════════════════════════════════════════
    48: GateData(
        number=48,
        binary="010110",
        king_wen_sequence=48,
        lower_trigram="110",  # Wind
        upper_trigram="010",  # Water

        iching_name="The Well",
        iching_chinese="井",
        iching_pinyin="Jǐng",
        iching_judgment=(
            "The well. The town may be changed, but the well cannot be changed. "
            "It neither decreases nor increases."
        ),
        iching_image="Water over wood: the image of the well.",

        hd_name="The Gate of Depth",
        hd_keynote="The Well of Wisdom",
        hd_center="Spleen",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Inadequacy",
        gk_gift="Resourcefulness",
        gk_siddhi="Wisdom",
        gk_programming_partner=21,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=44,
        start_degree=189.5,
        zodiac_sign="Libra",
        zodiac_degree=9.5
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 49: REVOLUTION
    # ═══════════════════════════════════════════════════════════════════════════
    49: GateData(
        number=49,
        binary="011101",
        king_wen_sequence=49,
        lower_trigram="101",  # Fire
        upper_trigram="011",  # Lake

        iching_name="Revolution (Molting)",
        iching_chinese="革",
        iching_pinyin="Gé",
        iching_judgment=(
            "Revolution. On your own day you are believed. Supreme success, "
            "furthering through perseverance. Remorse disappears."
        ),
        iching_image="Fire in the lake: the image of revolution.",

        hd_name="The Gate of Principles",
        hd_keynote="Revolution through Sensitivity",
        hd_center="Solar Plexus",
        hd_circuit="Tribal",
        hd_stream="Defense",

        gk_shadow="Reaction",
        gk_gift="Revolution",
        gk_siddhi="Rebirth",
        gk_programming_partner=4,
        gk_codon_ring="Ring of Union",
        gk_amino_acid="Valine",

        wheel_index=3,
        start_degree=318.875,
        zodiac_sign="Aquarius",
        zodiac_degree=18.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 50: THE CALDRON
    # ═══════════════════════════════════════════════════════════════════════════
    50: GateData(
        number=50,
        binary="101110",
        king_wen_sequence=50,
        lower_trigram="110",  # Wind
        upper_trigram="101",  # Fire

        iching_name="The Caldron",
        iching_chinese="鼎",
        iching_pinyin="Dǐng",
        iching_judgment="The caldron. Supreme good fortune. Success.",
        iching_image="Fire over wood: the image of the caldron.",

        hd_name="The Gate of Values",
        hd_keynote="Tribal Values & Laws",
        hd_center="Spleen",
        hd_circuit="Tribal",
        hd_stream="Defense",

        gk_shadow="Corruption",
        gk_gift="Equilibrium",
        gk_siddhi="Harmony",
        gk_programming_partner=3,
        gk_codon_ring="Ring of Life and Death",
        gk_amino_acid="Glutamine",

        wheel_index=47,
        start_degree=206.375,
        zodiac_sign="Libra",
        zodiac_degree=26.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 51: THE AROUSING (SHOCK)
    # ═══════════════════════════════════════════════════════════════════════════
    51: GateData(
        number=51,
        binary="001001",
        king_wen_sequence=51,
        lower_trigram="001",  # Thunder
        upper_trigram="001",  # Thunder

        iching_name="The Arousing (Shock, Thunder)",
        iching_chinese="震",
        iching_pinyin="Zhèn",
        iching_judgment=(
            "Shock brings success. Shock comes—oh, oh! Laughing words—ha, ha! "
            "The shock terrifies for a hundred miles, and he does not let fall "
            "the sacrificial spoon and chalice."
        ),
        iching_image="Thunder repeated: the image of shock.",

        hd_name="The Gate of Shock",
        hd_keynote="Competitive Spirit",
        hd_center="Heart",
        hd_circuit="Individual",
        hd_stream="Centering",

        gk_shadow="Agitation",
        gk_gift="Initiative",
        gk_siddhi="Awakening",
        gk_programming_partner=57,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=13,
        start_degree=15.125,
        zodiac_sign="Aries",
        zodiac_degree=15.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 52: KEEPING STILL (MOUNTAIN)
    # ═══════════════════════════════════════════════════════════════════════════
    52: GateData(
        number=52,
        binary="100100",
        king_wen_sequence=52,
        lower_trigram="100",  # Mountain
        upper_trigram="100",  # Mountain

        iching_name="Keeping Still (Mountain)",
        iching_chinese="艮",
        iching_pinyin="Gèn",
        iching_judgment=(
            "Keeping still. Keeping his back still so that he no longer feels "
            "his body. He goes into his courtyard and does not see his people. "
            "No blame."
        ),
        iching_image="Mountains standing close together: the image of keeping still.",

        hd_name="The Gate of Inaction",
        hd_keynote="Stillness—Non-Action",
        hd_center="Root",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Stress",
        gk_gift="Restraint",
        gk_siddhi="Stillness",
        gk_programming_partner=58,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Histidine",

        wheel_index=27,
        start_degree=93.875,
        zodiac_sign="Cancer",
        zodiac_degree=3.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 53: DEVELOPMENT (GRADUAL PROGRESS)
    # ═══════════════════════════════════════════════════════════════════════════
    53: GateData(
        number=53,
        binary="110100",
        king_wen_sequence=53,
        lower_trigram="100",  # Mountain
        upper_trigram="110",  # Wind

        iching_name="Development (Gradual Progress)",
        iching_chinese="漸",
        iching_pinyin="Jiàn",
        iching_judgment="Development. The maiden is given in marriage. Good fortune. Perseverance furthers.",
        iching_image="On the mountain, a tree: the image of development.",

        hd_name="The Gate of Beginnings",
        hd_keynote="Starting Things",
        hd_center="Root",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Immaturity",
        gk_gift="Expansion",
        gk_siddhi="Superabundance",
        gk_programming_partner=54,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=29,
        start_degree=105.125,
        zodiac_sign="Cancer",
        zodiac_degree=15.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 54: THE MARRYING MAIDEN
    # ═══════════════════════════════════════════════════════════════════════════
    54: GateData(
        number=54,
        binary="001011",
        king_wen_sequence=54,
        lower_trigram="011",  # Lake
        upper_trigram="001",  # Thunder

        iching_name="The Marrying Maiden",
        iching_chinese="歸妹",
        iching_pinyin="Guī Mèi",
        iching_judgment="The marrying maiden. Undertakings bring misfortune. Nothing that would further.",
        iching_image="Thunder over the lake: the image of the marrying maiden.",

        hd_name="The Gate of Ambition",
        hd_keynote="Drive to Rise",
        hd_center="Root",
        hd_circuit="Tribal",
        hd_stream="Ego",

        gk_shadow="Greed",
        gk_gift="Aspiration",
        gk_siddhi="Ascension",
        gk_programming_partner=53,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Tryptophan",

        wheel_index=61,
        start_degree=285.125,
        zodiac_sign="Capricorn",
        zodiac_degree=15.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 55: ABUNDANCE
    # ═══════════════════════════════════════════════════════════════════════════
    55: GateData(
        number=55,
        binary="001101",
        king_wen_sequence=55,
        lower_trigram="101",  # Fire
        upper_trigram="001",  # Thunder

        iching_name="Abundance (Fullness)",
        iching_chinese="豐",
        iching_pinyin="Fēng",
        iching_judgment="Abundance has success. The king attains abundance. Be not sad. Be like the sun at midday.",
        iching_image="Both thunder and lightning come: the image of abundance.",

        hd_name="The Gate of Spirit",
        hd_keynote="Emotional Abundance",
        hd_center="Solar Plexus",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Victimization",
        gk_gift="Freedom",
        gk_siddhi="Freedom",
        gk_programming_partner=59,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=5,
        start_degree=330.125,
        zodiac_sign="Pisces",
        zodiac_degree=0.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 56: THE WANDERER
    # ═══════════════════════════════════════════════════════════════════════════
    56: GateData(
        number=56,
        binary="101100",
        king_wen_sequence=56,
        lower_trigram="100",  # Mountain
        upper_trigram="101",  # Fire

        iching_name="The Wanderer",
        iching_chinese="旅",
        iching_pinyin="Lǚ",
        iching_judgment="The wanderer. Success through smallness. Perseverance brings good fortune to the wanderer.",
        iching_image="Fire on the mountain: the image of the wanderer.",

        hd_name="The Gate of Stimulation",
        hd_keynote="The Storyteller",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Distraction",
        gk_gift="Enrichment",
        gk_siddhi="Intoxication",
        gk_programming_partner=60,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=31,
        start_degree=116.375,
        zodiac_sign="Cancer",
        zodiac_degree=26.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 57: THE GENTLE (WIND)
    # ═══════════════════════════════════════════════════════════════════════════
    57: GateData(
        number=57,
        binary="110110",
        king_wen_sequence=57,
        lower_trigram="110",  # Wind
        upper_trigram="110",  # Wind

        iching_name="The Gentle (Wind, Penetrating)",
        iching_chinese="巽",
        iching_pinyin="Xùn",
        iching_judgment=(
            "The gentle. Success through what is small. It furthers one to have "
            "somewhere to go. It furthers one to see the great man."
        ),
        iching_image="Winds following one upon the other: the image of the gently penetrating.",

        hd_name="The Gate of Intuitive Insight",
        hd_keynote="The Gentle Intuition",
        hd_center="Spleen",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Unease",
        gk_gift="Intuition",
        gk_siddhi="Clarity",
        gk_programming_partner=51,
        gk_codon_ring="Ring of Humanity",
        gk_amino_acid="Arginine",

        wheel_index=45,
        start_degree=195.125,
        zodiac_sign="Libra",
        zodiac_degree=15.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 58: THE JOYOUS (LAKE)
    # ═══════════════════════════════════════════════════════════════════════════
    58: GateData(
        number=58,
        binary="011011",
        king_wen_sequence=58,
        lower_trigram="011",  # Lake
        upper_trigram="011",  # Lake

        iching_name="The Joyous (Lake)",
        iching_chinese="兌",
        iching_pinyin="Duì",
        iching_judgment="The joyous. Success. Perseverance is favorable.",
        iching_image="Lakes resting one on the other: the image of the joyous.",

        hd_name="The Gate of Vitality",
        hd_keynote="Joy of Life",
        hd_center="Root",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Dissatisfaction",
        gk_gift="Vitality",
        gk_siddhi="Bliss",
        gk_programming_partner=52,
        gk_codon_ring="Ring of Seeking",
        gk_amino_acid="Histidine",

        wheel_index=59,
        start_degree=273.875,
        zodiac_sign="Capricorn",
        zodiac_degree=3.875
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 59: DISPERSION
    # ═══════════════════════════════════════════════════════════════════════════
    59: GateData(
        number=59,
        binary="110010",
        king_wen_sequence=59,
        lower_trigram="010",  # Water
        upper_trigram="110",  # Wind

        iching_name="Dispersion (Dissolution)",
        iching_chinese="渙",
        iching_pinyin="Huàn",
        iching_judgment=(
            "Dispersion. Success. The king approaches his temple. It furthers "
            "one to cross the great water. Perseverance furthers."
        ),
        iching_image="The wind drives over the water: the image of dispersion.",

        hd_name="The Gate of Sexuality",
        hd_keynote="Breaking Down Barriers",
        hd_center="Sacral",
        hd_circuit="Tribal",
        hd_stream="Defense",

        gk_shadow="Dishonesty",
        gk_gift="Intimacy",
        gk_siddhi="Transparency",
        gk_programming_partner=55,
        gk_codon_ring="Ring of Alchemy",
        gk_amino_acid="Serine",

        wheel_index=37,
        start_degree=150.125,
        zodiac_sign="Virgo",
        zodiac_degree=0.125
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 60: LIMITATION
    # ═══════════════════════════════════════════════════════════════════════════
    60: GateData(
        number=60,
        binary="010011",
        king_wen_sequence=60,
        lower_trigram="011",  # Lake
        upper_trigram="010",  # Water

        iching_name="Limitation",
        iching_chinese="節",
        iching_pinyin="Jié",
        iching_judgment="Limitation. Success. Galling limitation must not be persevered in.",
        iching_image="Water over lake: the image of limitation.",

        hd_name="The Gate of Acceptance",
        hd_keynote="Accepting Limitation",
        hd_center="Root",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Limitation",
        gk_gift="Realism",
        gk_siddhi="Justice",
        gk_programming_partner=56,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=63,
        start_degree=296.375,
        zodiac_sign="Capricorn",
        zodiac_degree=26.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 61: INNER TRUTH
    # ═══════════════════════════════════════════════════════════════════════════
    61: GateData(
        number=61,
        binary="110011",
        king_wen_sequence=61,
        lower_trigram="011",  # Lake
        upper_trigram="110",  # Wind

        iching_name="Inner Truth",
        iching_chinese="中孚",
        iching_pinyin="Zhōng Fú",
        iching_judgment=(
            "Inner truth. Pigs and fishes. Good fortune. It furthers one to "
            "cross the great water. Perseverance furthers."
        ),
        iching_image="Wind over lake: the image of inner truth.",

        hd_name="The Gate of Mystery",
        hd_keynote="The Pressure to Know",
        hd_center="Head",
        hd_circuit="Individual",
        hd_stream="Knowing",

        gk_shadow="Psychosis",
        gk_gift="Inspiration",
        gk_siddhi="Sanctity",
        gk_programming_partner=62,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=62,
        start_degree=290.75,
        zodiac_sign="Capricorn",
        zodiac_degree=20.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 62: PREPONDERANCE OF THE SMALL
    # ═══════════════════════════════════════════════════════════════════════════
    62: GateData(
        number=62,
        binary="001100",
        king_wen_sequence=62,
        lower_trigram="100",  # Mountain
        upper_trigram="001",  # Thunder

        iching_name="Preponderance of the Small",
        iching_chinese="小過",
        iching_pinyin="Xiǎo Guò",
        iching_judgment=(
            "Preponderance of the small. Success. Perseverance furthers. "
            "Small things may be done; great things should not be done."
        ),
        iching_image="Thunder on the mountain: the image of preponderance of the small.",

        hd_name="The Gate of Details",
        hd_keynote="The Preponderance of the Small",
        hd_center="Throat",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Intellect",
        gk_gift="Precision",
        gk_siddhi="Impeccability",
        gk_programming_partner=61,
        gk_codon_ring="Ring of Gaia",
        gk_amino_acid="Threonine",

        wheel_index=30,
        start_degree=110.75,
        zodiac_sign="Cancer",
        zodiac_degree=20.75
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 63: AFTER COMPLETION
    # ═══════════════════════════════════════════════════════════════════════════
    63: GateData(
        number=63,
        binary="010101",
        king_wen_sequence=63,
        lower_trigram="101",  # Fire
        upper_trigram="010",  # Water

        iching_name="After Completion",
        iching_chinese="既濟",
        iching_pinyin="Jì Jì",
        iching_judgment=(
            "After completion. Success in small matters. Perseverance furthers. "
            "At the beginning good fortune, at the end disorder."
        ),
        iching_image="Water over fire: the image of the condition in after completion.",

        hd_name="The Gate of Doubt",
        hd_keynote="Logical Questioning",
        hd_center="Head",
        hd_circuit="Collective",
        hd_stream="Understanding",

        gk_shadow="Doubt",
        gk_gift="Inquiry",
        gk_siddhi="Truth",
        gk_programming_partner=64,
        gk_codon_ring="Ring of Matter",
        gk_amino_acid="Isoleucine",

        wheel_index=7,
        start_degree=341.375,
        zodiac_sign="Pisces",
        zodiac_degree=11.375
    ),

    # ═══════════════════════════════════════════════════════════════════════════
    # GATE 64: BEFORE COMPLETION
    # ═══════════════════════════════════════════════════════════════════════════
    64: GateData(
        number=64,
        binary="101010",
        king_wen_sequence=64,
        lower_trigram="010",  # Water
        upper_trigram="101",  # Fire

        iching_name="Before Completion",
        iching_chinese="未濟",
        iching_pinyin="Wèi Jì",
        iching_judgment=(
            "Before completion. Success. But if the little fox, after nearly "
            "completing the crossing, gets his tail in the water, there is "
            "nothing that would further."
        ),
        iching_image="Fire over water: the image of the condition before transition.",

        hd_name="The Gate of Confusion",
        hd_keynote="Mental Pressure to Resolve",
        hd_center="Head",
        hd_circuit="Collective",
        hd_stream="Sharing",

        gk_shadow="Confusion",
        gk_gift="Imagination",
        gk_siddhi="Illumination",
        gk_programming_partner=63,
        gk_codon_ring="Ring of Matter",
        gk_amino_acid="Isoleucine",

        wheel_index=39,
        start_degree=161.375,
        zodiac_sign="Virgo",
        zodiac_degree=11.375
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: CENTER DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Center(Enum):
    """The 9 Centers of the Human Design BodyGraph."""
    HEAD = "Head"
    AJNA = "Ajna"
    THROAT = "Throat"
    G = "G"
    HEART = "Heart"
    SACRAL = "Sacral"
    SOLAR_PLEXUS = "Solar Plexus"
    SPLEEN = "Spleen"
    ROOT = "Root"


# Gate to Center mapping (derived from GATE_DATABASE)
GATE_TO_CENTER = {gate: Center(data.hd_center) for gate, data in GATE_DATABASE.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: CHANNEL DEFINITIONS (36 CHANNELS)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ChannelData:
    """Definition of a Human Design Channel."""
    gate_1: int
    gate_2: int
    center_1: Center
    center_2: Center
    name: str
    circuit: str
    keynote: str


CHANNELS: Dict[tuple, ChannelData] = {
    # Head -> Ajna (Inspiration to Conceptualization)
    (64, 47): ChannelData(
        64,
        47,
        Center.HEAD,
        Center.AJNA,
        "Abstraction",
        "Collective",
        "Mental activity, doubt, confusion",
    ),
    (61, 24): ChannelData(61, 24, Center.HEAD, Center.AJNA, "Awareness", "Individual", "A thinker, knowing"),
    (63, 4): ChannelData(63, 4, Center.HEAD, Center.AJNA, "Logic", "Collective", "Mental ease mixed with doubt"),

    # Ajna -> Throat (Conceptualization to Communication)
    (17, 62): ChannelData(17, 62, Center.AJNA, Center.THROAT, "Acceptance", "Collective", "Organizational skills"),
    (43, 23): ChannelData(43, 23, Center.AJNA, Center.THROAT, "Structuring", "Individual", "Genius to freak"),
    (11, 56): ChannelData(11, 56, Center.AJNA, Center.THROAT, "Curiosity", "Collective", "A storyteller, seeker"),

    # Throat -> Spleen
    (16, 48): ChannelData(16, 48, Center.THROAT, Center.SPLEEN, "The Wavelength", "Collective", "Talent expressed"),
    (20, 57): ChannelData(20, 57, Center.THROAT, Center.SPLEEN, "The Brainwave", "Individual", "Penetrating awareness"),

    # Throat -> Sacral
    (20, 34): ChannelData(
        20,
        34,
        Center.THROAT,
        Center.SACRAL,
        "Charisma",
        "Individual",
        "Where thoughts become actions",
    ),

    # Throat -> G Center
    (20, 10): ChannelData(
        20,
        10,
        Center.THROAT,
        Center.G,
        "Awakening",
        "Individual",
        "Commitment to higher principles",
    ),
    (31, 7): ChannelData(31, 7, Center.THROAT, Center.G, "The Alpha", "Collective", "Leadership"),
    (8, 1): ChannelData(8, 1, Center.THROAT, Center.G, "Inspiration", "Individual", "Creative role model"),
    (33, 13): ChannelData(33, 13, Center.THROAT, Center.G, "The Prodigal", "Collective", "A witness"),

    # Throat -> Heart
    (45, 21): ChannelData(45, 21, Center.THROAT, Center.HEART, "Money", "Tribal", "A materialist"),

    # Throat -> Solar Plexus
    (35, 36): ChannelData(
        35,
        36,
        Center.THROAT,
        Center.SOLAR_PLEXUS,
        "Transitoriness",
        "Collective",
        "A jack of all trades",
    ),
    (12, 22): ChannelData(12, 22, Center.THROAT, Center.SOLAR_PLEXUS, "Openness", "Individual", "A social being"),

    # Spleen -> Root
    (32, 54): ChannelData(32, 54, Center.SPLEEN, Center.ROOT, "Transformation", "Tribal", "Being driven"),
    (28, 38): ChannelData(28, 38, Center.SPLEEN, Center.ROOT, "Struggle", "Individual", "Stubbornness"),
    (18, 58): ChannelData(18, 58, Center.SPLEEN, Center.ROOT, "Judgment", "Collective", "Insatiability"),

    # Spleen -> Sacral
    (57, 34): ChannelData(57, 34, Center.SPLEEN, Center.SACRAL, "Power", "Individual", "An archetype"),
    (50, 27): ChannelData(50, 27, Center.SPLEEN, Center.SACRAL, "Preservation", "Tribal", "A custodian"),

    # G -> Sacral
    (10, 34): ChannelData(10, 34, Center.G, Center.SACRAL, "Exploration", "Individual", "Following one's convictions"),
    (15, 5): ChannelData(15, 5, Center.G, Center.SACRAL, "Rhythm", "Collective", "Being in the flow"),
    (2, 14): ChannelData(2, 14, Center.G, Center.SACRAL, "The Beat", "Individual", "A keeper of keys"),
    (46, 29): ChannelData(46, 29, Center.G, Center.SACRAL, "Discovery", "Collective", "Succeeding where others fail"),

    # G -> Spleen
    (10, 57): ChannelData(10, 57, Center.G, Center.SPLEEN, "Perfected Form", "Individual", "Survival"),

    # G -> Heart
    (25, 51): ChannelData(25, 51, Center.G, Center.HEART, "Initiation", "Individual", "Needing to be first"),

    # Sacral -> Solar Plexus
    (59, 6): ChannelData(59, 6, Center.SACRAL, Center.SOLAR_PLEXUS, "Intimacy", "Tribal", "Focused on reproduction"),

    # Sacral -> Root
    (42, 53): ChannelData(42, 53, Center.SACRAL, Center.ROOT, "Maturation", "Collective", "Balanced development"),
    (3, 60): ChannelData(3, 60, Center.SACRAL, Center.ROOT, "Mutation", "Individual", "Energy which initiates"),
    (9, 52): ChannelData(9, 52, Center.SACRAL, Center.ROOT, "Concentration", "Collective", "Determination"),

    # Heart -> Spleen
    (26, 44): ChannelData(26, 44, Center.HEART, Center.SPLEEN, "Surrender", "Tribal", "A transmitter"),

    # Heart -> Solar Plexus
    (40, 37): ChannelData(40, 37, Center.HEART, Center.SOLAR_PLEXUS, "Community", "Tribal", "A part seeking a whole"),

    # Solar Plexus -> Root
    (49, 19): ChannelData(49, 19, Center.SOLAR_PLEXUS, Center.ROOT, "Synthesis", "Tribal", "A sensitive"),
    (55, 39): ChannelData(55, 39, Center.SOLAR_PLEXUS, Center.ROOT, "Emoting", "Individual", "Moodiness"),
    (30, 41): ChannelData(30, 41, Center.SOLAR_PLEXUS, Center.ROOT, "Recognition", "Collective", "Focused energy"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: PROFILE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProfileData:
    """Definition of a Human Design Profile."""
    line_1: int
    line_2: int
    name: str
    angle: str  # Right Angle, Juxtaposition, Left Angle
    cross_type: str  # RAC, JXP, LAC
    theme: str


PROFILES: Dict[tuple, ProfileData] = {
    (1, 3): ProfileData(1, 3, "Investigator/Martyr", "Right Angle", "RAC", "Research through trial and error"),
    (1, 4): ProfileData(1, 4, "Investigator/Opportunist", "Right Angle", "RAC", "Foundation through network"),
    (2, 4): ProfileData(2, 4, "Hermit/Opportunist", "Right Angle", "RAC", "Natural talent called out"),
    (2, 5): ProfileData(2, 5, "Hermit/Heretic", "Right Angle", "RAC", "Natural talent projected upon"),
    (3, 5): ProfileData(3, 5, "Martyr/Heretic", "Right Angle", "RAC", "Trial and error, universal solutions"),
    (3, 6): ProfileData(3, 6, "Martyr/Role Model", "Right Angle", "RAC", "Adaptation to objective wisdom"),
    (4, 6): ProfileData(4, 6, "Opportunist/Role Model", "Right Angle", "RAC", "Network leading to wisdom"),
    (4, 1): ProfileData(4, 1, "Opportunist/Investigator", "Juxtaposition", "JXP", "Fixed fate through foundation"),
    (5, 1): ProfileData(5, 1, "Heretic/Investigator", "Left Angle", "LAC", "Universal solutions through research"),
    (5, 2): ProfileData(5, 2, "Heretic/Hermit", "Left Angle", "LAC", "Projected natural talent"),
    (6, 2): ProfileData(6, 2, "Role Model/Hermit", "Left Angle", "LAC", "Objective witness with natural gifts"),
    (6, 3): ProfileData(6, 3, "Role Model/Martyr", "Left Angle", "LAC", "Wisdom through experience"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: INCARNATION CROSS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

# Key: Personality Sun Gate
# Value: Dict with RAC, JXP, LAC cross names
INCARNATION_CROSSES: Dict[int, Dict[str, str]] = {
    1: {
        "RAC": "Right Angle Cross of the Sphinx 4",
        "JXP": "Juxtaposition Cross of Self-Expression",
        "LAC": "Left Angle Cross of Defiance 2",
    },
    2: {
        "RAC": "Right Angle Cross of the Sphinx 2",
        "JXP": "Juxtaposition Cross of the Driver",
        "LAC": "Left Angle Cross of Defiance 1",
    },
    3: {
        "RAC": "Right Angle Cross of Laws 1",
        "JXP": "Juxtaposition Cross of Mutation",
        "LAC": "Left Angle Cross of Wishes 1",
    },
    4: {
        "RAC": "Right Angle Cross of Explanation 2",
        "JXP": "Juxtaposition Cross of Formulization",
        "LAC": "Left Angle Cross of Revolution 2",
    },
    5: {
        "RAC": "Right Angle Cross of Consciousness 1",
        "JXP": "Juxtaposition Cross of Habits",
        "LAC": "Left Angle Cross of Separation 1",
    },
    6: {
        "RAC": "Right Angle Cross of Eden 1",
        "JXP": "Juxtaposition Cross of Conflict",
        "LAC": "Left Angle Cross of the Plane 1",
    },
    7: {
        "RAC": "Right Angle Cross of the Sphinx 3",
        "JXP": "Juxtaposition Cross of Interaction",
        "LAC": "Left Angle Cross of Masks 2",
    },
    8: {
        "RAC": "Right Angle Cross of Contagion 2",
        "JXP": "Juxtaposition Cross of Contribution",
        "LAC": "Left Angle Cross of Uncertainty 2",
    },
    9: {
        "RAC": "Right Angle Cross of Planning 2",
        "JXP": "Juxtaposition Cross of Focus",
        "LAC": "Left Angle Cross of Dedication 2",
    },
    10: {
        "RAC": "Right Angle Cross of the Vessel of Love 2",
        "JXP": "Juxtaposition Cross of Behavior",
        "LAC": "Left Angle Cross of Prevention 2",
    },
    11: {
        "RAC": "Right Angle Cross of Eden 2",
        "JXP": "Juxtaposition Cross of Ideas",
        "LAC": "Left Angle Cross of Education 2",
    },
    12: {
        "RAC": "Right Angle Cross of Eden 3",
        "JXP": "Juxtaposition Cross of Articulation",
        "LAC": "Left Angle Cross of Education 1",
    },
    13: {
        "RAC": "Right Angle Cross of the Sphinx 1",
        "JXP": "Juxtaposition Cross of Listening",
        "LAC": "Left Angle Cross of Masks 1",
    },
    14: {
        "RAC": "Right Angle Cross of the Vessel of Love 4",
        "JXP": "Juxtaposition Cross of Power Skills",
        "LAC": "Left Angle Cross of Uncertainty 1",
    },
    15: {
        "RAC": "Right Angle Cross of the Vessel of Love 1",
        "JXP": "Juxtaposition Cross of Extremes",
        "LAC": "Left Angle Cross of Prevention 1",
    },
    16: {
        "RAC": "Right Angle Cross of Planning 3",
        "JXP": "Juxtaposition Cross of Experimentation",
        "LAC": "Left Angle Cross of Identification 1",
    },
    17: {
        "RAC": "Right Angle Cross of Service 1",
        "JXP": "Juxtaposition Cross of Opinions",
        "LAC": "Left Angle Cross of Upheaval 1",
    },
    18: {
        "RAC": "Right Angle Cross of Service 2",
        "JXP": "Juxtaposition Cross of Correction",
        "LAC": "Left Angle Cross of Upheaval 2",
    },
    19: {
        "RAC": "Right Angle Cross of the Four Ways 1",
        "JXP": "Juxtaposition Cross of Need",
        "LAC": "Left Angle Cross of Refinement 1",
    },
    20: {
        "RAC": "Right Angle Cross of the Sleeping Phoenix 1",
        "JXP": "Juxtaposition Cross of the Now",
        "LAC": "Left Angle Cross of Duality 1",
    },
    21: {
        "RAC": "Right Angle Cross of Tension 1",
        "JXP": "Juxtaposition Cross of Control",
        "LAC": "Left Angle Cross of Endeavor 1",
    },
    22: {
        "RAC": "Right Angle Cross of Rulership 1",
        "JXP": "Juxtaposition Cross of Grace",
        "LAC": "Left Angle Cross of Informing 1",
    },
    23: {
        "RAC": "Right Angle Cross of Explanation 1",
        "JXP": "Juxtaposition Cross of Assimilation",
        "LAC": "Left Angle Cross of Dedication 1",
    },
    24: {
        "RAC": "Right Angle Cross of the Four Ways 4",
        "JXP": "Juxtaposition Cross of Rationalization",
        "LAC": "Left Angle Cross of Incarnation 2",
    },
    25: {
        "RAC": "Right Angle Cross of the Vessel of Love 3",
        "JXP": "Juxtaposition Cross of Innocence",
        "LAC": "Left Angle Cross of the Spirit 1",
    },
    26: {
        "RAC": "Right Angle Cross of Rulership 2",
        "JXP": "Juxtaposition Cross of the Trickster",
        "LAC": "Left Angle Cross of Confrontation 2",
    },
    27: {
        "RAC": "Right Angle Cross of the Unexpected 1",
        "JXP": "Juxtaposition Cross of Caring",
        "LAC": "Left Angle Cross of Alignment 1",
    },
    28: {
        "RAC": "Right Angle Cross of the Unexpected 2",
        "JXP": "Juxtaposition Cross of Risks",
        "LAC": "Left Angle Cross of Alignment 2",
    },
    29: {
        "RAC": "Right Angle Cross of Contagion 4",
        "JXP": "Juxtaposition Cross of Commitment",
        "LAC": "Left Angle Cross of Industry 2",
    },
    30: {
        "RAC": "Right Angle Cross of Contagion 1",
        "JXP": "Juxtaposition Cross of Fates",
        "LAC": "Left Angle Cross of Industry 1",
    },
    31: {
        "RAC": "Right Angle Cross of the Unexpected 3",
        "JXP": "Juxtaposition Cross of Influence",
        "LAC": "Left Angle Cross of the Alpha 1",
    },
    32: {
        "RAC": "Right Angle Cross of Maya 4",
        "JXP": "Juxtaposition Cross of Continuity",
        "LAC": "Left Angle Cross of Limitation 2",
    },
    33: {
        "RAC": "Right Angle Cross of the Four Ways 2",
        "JXP": "Juxtaposition Cross of Retreat",
        "LAC": "Left Angle Cross of Refinement 2",
    },
    34: {
        "RAC": "Right Angle Cross of the Sleeping Phoenix 2",
        "JXP": "Juxtaposition Cross of Power",
        "LAC": "Left Angle Cross of Duality 2",
    },
    35: {
        "RAC": "Right Angle Cross of Consciousness 2",
        "JXP": "Juxtaposition Cross of Experience",
        "LAC": "Left Angle Cross of Separation 2",
    },
    36: {
        "RAC": "Right Angle Cross of Eden 4",
        "JXP": "Juxtaposition Cross of Crisis",
        "LAC": "Left Angle Cross of the Plane 2",
    },
    37: {
        "RAC": "Right Angle Cross of Planning 1",
        "JXP": "Juxtaposition Cross of Bargains",
        "LAC": "Left Angle Cross of Migration 1",
    },
    38: {
        "RAC": "Right Angle Cross of Tension 2",
        "JXP": "Juxtaposition Cross of Opposition",
        "LAC": "Left Angle Cross of Individualism 2",
    },
    39: {
        "RAC": "Right Angle Cross of Tension 3",
        "JXP": "Juxtaposition Cross of Provocation",
        "LAC": "Left Angle Cross of Individualism 1",
    },
    40: {
        "RAC": "Right Angle Cross of Planning 4",
        "JXP": "Juxtaposition Cross of Denial",
        "LAC": "Left Angle Cross of Migration 2",
    },
    41: {
        "RAC": "Right Angle Cross of the Unexpected 4",
        "JXP": "Juxtaposition Cross of Fantasy",
        "LAC": "Left Angle Cross of the Alpha 2",
    },
    42: {
        "RAC": "Right Angle Cross of Maya 1",
        "JXP": "Juxtaposition Cross of Completion",
        "LAC": "Left Angle Cross of Limitation 1",
    },
    43: {
        "RAC": "Right Angle Cross of Explanation 4",
        "JXP": "Juxtaposition Cross of Insight",
        "LAC": "Left Angle Cross of Dedication 2",
    },
    44: {
        "RAC": "Right Angle Cross of the Four Ways 3",
        "JXP": "Juxtaposition Cross of Alertness",
        "LAC": "Left Angle Cross of Incarnation 1",
    },
    45: {
        "RAC": "Right Angle Cross of Rulership 3",
        "JXP": "Juxtaposition Cross of Possession",
        "LAC": "Left Angle Cross of Confrontation 1",
    },
    46: {
        "RAC": "Right Angle Cross of the Vessel of Love",
        "JXP": "Juxtaposition Cross of Serendipity",
        "LAC": "Left Angle Cross of Healing 2",
    },
    47: {
        "RAC": "Right Angle Cross of Rulership 4",
        "JXP": "Juxtaposition Cross of Oppression",
        "LAC": "Left Angle Cross of Informing 2",
    },
    48: {
        "RAC": "Right Angle Cross of Tension 4",
        "JXP": "Juxtaposition Cross of Depth",
        "LAC": "Left Angle Cross of Endeavor 2",
    },
    49: {
        "RAC": "Right Angle Cross of Explanation 3",
        "JXP": "Juxtaposition Cross of Principles",
        "LAC": "Left Angle Cross of Revolution 1",
    },
    50: {
        "RAC": "Right Angle Cross of Laws 2",
        "JXP": "Juxtaposition Cross of Values",
        "LAC": "Left Angle Cross of Wishes 2",
    },
    51: {
        "RAC": "Right Angle Cross of Penetration 1",
        "JXP": "Juxtaposition Cross of Shock",
        "LAC": "Left Angle Cross of the Clarion 1",
    },
    52: {
        "RAC": "Right Angle Cross of Service 3",
        "JXP": "Juxtaposition Cross of Stillness",
        "LAC": "Left Angle Cross of Demands 1",
    },
    53: {
        "RAC": "Right Angle Cross of Penetration 2",
        "JXP": "Juxtaposition Cross of Beginnings",
        "LAC": "Left Angle Cross of Cycles 2",
    },
    54: {
        "RAC": "Right Angle Cross of Penetration 3",
        "JXP": "Juxtaposition Cross of Ambition",
        "LAC": "Left Angle Cross of Cycles 1",
    },
    55: {
        "RAC": "Right Angle Cross of the Sleeping Phoenix 3",
        "JXP": "Juxtaposition Cross of Moods",
        "LAC": "Left Angle Cross of Spirit 2",
    },
    56: {
        "RAC": "Right Angle Cross of Laws 3",
        "JXP": "Juxtaposition Cross of Stimulation",
        "LAC": "Left Angle Cross of Distraction 1",
    },
    57: {
        "RAC": "Right Angle Cross of Penetration 4",
        "JXP": "Juxtaposition Cross of Intuition",
        "LAC": "Left Angle Cross of the Clarion 2",
    },
    58: {
        "RAC": "Right Angle Cross of Service 4",
        "JXP": "Juxtaposition Cross of Vitality",
        "LAC": "Left Angle Cross of Demands 2",
    },
    59: {
        "RAC": "Right Angle Cross of the Sleeping Phoenix 4",
        "JXP": "Juxtaposition Cross of Strategy",
        "LAC": "Left Angle Cross of the Spirit 1",
    },
    60: {
        "RAC": "Right Angle Cross of Laws 4",
        "JXP": "Juxtaposition Cross of Limitation",
        "LAC": "Left Angle Cross of Distraction 2",
    },
    61: {
        "RAC": "Right Angle Cross of Maya 2",
        "JXP": "Juxtaposition Cross of Thinking",
        "LAC": "Left Angle Cross of Obscuration 2",
    },
    62: {
        "RAC": "Right Angle Cross of Maya 3",
        "JXP": "Juxtaposition Cross of Detail",
        "LAC": "Left Angle Cross of Obscuration 1",
    },
    63: {
        "RAC": "Right Angle Cross of Consciousness 3",
        "JXP": "Juxtaposition Cross of Doubts",
        "LAC": "Left Angle Cross of Dominion 1",
    },
    64: {
        "RAC": "Right Angle Cross of Consciousness 4",
        "JXP": "Juxtaposition Cross of Confusion",
        "LAC": "Left Angle Cross of Dominion 2",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: DATA CLASSES FOR CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Activation:
    """
    A complete activation at a specific longitude.
    Contains gate, line, color, tone, and base.
    """
    longitude: float
    gate: int
    line: int
    color: int
    tone: int
    base: int

    # Derived properties
    gate_data: Optional[GateData] = None
    line_archetype: Optional[LineArchetype] = None

    def __post_init__(self):
        """Populate derived properties."""
        if self.gate in GATE_DATABASE:
            self.gate_data = GATE_DATABASE[self.gate]
        if self.line in LINE_ARCHETYPES:
            self.line_archetype = LINE_ARCHETYPES[self.line]

    @property
    def binary(self) -> str:
        """Return the 6-bit binary of this gate."""
        return self.gate_data.binary if self.gate_data else "000000"

    @property
    def hexagram_name(self) -> str:
        """Return the I-Ching name."""
        return self.gate_data.iching_name if self.gate_data else f"Gate {self.gate}"

    @property
    def hd_name(self) -> str:
        """Return the Human Design gate name."""
        return self.gate_data.hd_name if self.gate_data else f"Gate {self.gate}"

    @property
    def gene_key_spectrum(self) -> Dict[str, str]:
        """Return the Gene Keys Shadow/Gift/Siddhi."""
        if self.gate_data:
            return {
                "shadow": self.gate_data.gk_shadow,
                "gift": self.gate_data.gk_gift,
                "siddhi": self.gate_data.gk_siddhi
            }
        return {"shadow": "Unknown", "gift": "Unknown", "siddhi": "Unknown"}

    @property
    def center(self) -> str:
        """Return which center this gate belongs to."""
        return self.gate_data.hd_center if self.gate_data else "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "longitude": self.longitude,
            "gate": self.gate,
            "line": self.line,
            "color": self.color,
            "tone": self.tone,
            "base": self.base,
            "binary": self.binary,
            "hexagram_name": self.hexagram_name,
            "hd_name": self.hd_name,
            "gene_keys": self.gene_key_spectrum,
            "center": self.center,
            "line_archetype": self.line_archetype.name if self.line_archetype else None,
        }


@dataclass
class DailyCode:
    """
    The cosmic code for a specific day/moment.
    Contains Sun and Earth activations.
    """
    timestamp: datetime
    sun_activation: Activation
    earth_activation: Activation  # Always 180° opposite

    @property
    def theme(self) -> str:
        """Generate the theme string for this day."""
        sun_gate = self.sun_activation.gate_data
        if sun_gate:
            return f"Gate {self.sun_activation.gate}: {sun_gate.hd_name}"
        return f"Gate {self.sun_activation.gate}"

    @property
    def gene_key_focus(self) -> Dict[str, str]:
        """The Gene Key spectrum for today."""
        return self.sun_activation.gene_key_spectrum

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "sun": self.sun_activation.to_dict(),
            "earth": self.earth_activation.to_dict(),
            "theme": self.theme,
            "gene_key_focus": self.gene_key_focus,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: THE I-CHING LOGIC KERNEL
# ═══════════════════════════════════════════════════════════════════════════════

class IChingKernel:
    """
    Stateless I-Ching / Human Design calculation kernel.

    This kernel performs high-fidelity calculations for:
    - Longitude to Gate/Line/Color/Tone/Base conversion
    - Daily cosmic code determination
    - Design date calculation (88° solar arc)
    - Type, Authority, and Profile derivation

    All calculations use Fixed Tropical Zodiac with 58° IGING offset.
    For ephemeris calculations, inject a compatible ephemeris service.
    """

    # Class constants (exposing for external reference)
    OFFSET = ICHING_OFFSET
    GATE_CIRCLE = GATE_CIRCLE
    DEGREES_PER_GATE = DEGREES_PER_GATE

    def __init__(self, ephemeris_service=None):
        """
        Initialize the kernel.

        Args:
            ephemeris_service: Optional ephemeris calculator for real-time positions.
                              Must implement get_sun_longitude(jd) -> float
        """
        self._ephemeris = ephemeris_service

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE CALCULATION: Longitude → Activation
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def longitude_to_activation(longitude: float) -> Activation:
        """
        Convert ecliptic longitude to full HD activation.

        This is the core calculation that maps any degree (0-360°) to:
        - Gate (1-64)
        - Line (1-6)
        - Color (1-6)
        - Tone (1-6)
        - Base (1-5)

        Mathematical precision:
        - 64 Gates × 5.625° = 360°
        - 6 Lines × 0.9375° = 5.625° (per gate)
        - 6 Colors × 0.15625° = 0.9375° (per line)
        - 6 Tones × ~0.026° = 0.15625° (per color)
        - 5 Bases × ~0.0052° = ~0.026° (per tone)

        Args:
            longitude: Ecliptic longitude (0-360°, Tropical)

        Returns:
            Activation object with all subdivision data
        """
        # Apply IGING offset to synchronize zodiac with gate wheel
        # Gate 41 begins at zodiac position 302° (302 + 58 = 360 = 0 on wheel)
        angle = (longitude + ICHING_OFFSET) % 360
        angle_percentage = angle / 360

        # Calculate gate (each gate spans 5.625°)
        gate_index = int(angle_percentage * 64)
        gate = GATE_CIRCLE[gate_index]

        # Calculate line (each line spans 0.9375°)
        # Total divisions: 64 × 6 = 384
        line = int((angle_percentage * 384) % 6) + 1

        # Calculate color (each color spans 0.15625°)
        # Total divisions: 384 × 6 = 2304
        color = int((angle_percentage * 2304) % 6) + 1

        # Calculate tone (each tone spans ~0.026°)
        # Total divisions: 2304 × 6 = 13824
        tone = int((angle_percentage * 13824) % 6) + 1

        # Calculate base (each base spans ~0.0052°)
        # Total divisions: 13824 × 5 = 69120
        base = int((angle_percentage * 69120) % 5) + 1

        return Activation(
            longitude=longitude,
            gate=gate,
            line=line,
            color=color,
            tone=tone,
            base=base
        )

    @staticmethod
    def calculate_solar_gate(longitude: float) -> Dict[str, Any]:
        """
        Calculate the active Gate from a solar longitude.

        Simplified interface for basic gate/line lookup.

        Args:
            longitude: Sun's ecliptic longitude (0-360°)

        Returns:
            Dict with gate number, line, and semantic data
        """
        activation = IChingKernel.longitude_to_activation(longitude)
        gate_data = GATE_DATABASE.get(activation.gate)

        result = {
            "gate": activation.gate,
            "line": activation.line,
            "binary": activation.binary,
            "longitude": longitude,
        }

        if gate_data:
            result.update({
                # I-Ching Layer
                "iching_name": gate_data.iching_name,
                "iching_chinese": gate_data.iching_chinese,
                "iching_judgment": gate_data.iching_judgment,

                # Human Design Layer
                "hd_name": gate_data.hd_name,
                "hd_keynote": gate_data.hd_keynote,
                "hd_center": gate_data.hd_center,
                "hd_circuit": gate_data.hd_circuit,

                # Gene Keys Layer
                "gk_shadow": gate_data.gk_shadow,
                "gk_gift": gate_data.gk_gift,
                "gk_siddhi": gate_data.gk_siddhi,

                # Trigram composition
                "lower_trigram": gate_data.lower_trigram,
                "upper_trigram": gate_data.upper_trigram,
            })

        # Add line archetype
        line_data = LINE_ARCHETYPES.get(activation.line)
        if line_data:
            result["line_archetype"] = {
                "name": line_data.name,
                "theme": line_data.theme,
                "description": line_data.description
            }

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # DAILY CODE: Theme of the Day
    # ═══════════════════════════════════════════════════════════════════════════

    def get_daily_code(self, dt: datetime = None) -> DailyCode:
        """
        Get the cosmic code for a specific date/time.

        Requires ephemeris service for real-time calculations.
        If no ephemeris, uses approximation based on date.

        Args:
            dt: Datetime for calculation (default: now UTC)

        Returns:
            DailyCode with Sun and Earth activations
        """
        if dt is None:
            dt = datetime.now(UTC)

        # Get Sun longitude
        if self._ephemeris:
            # Use injected ephemeris service
            jd = self._datetime_to_julian(dt)
            sun_long = self._ephemeris.get_sun_longitude(jd)
        else:
            # Fallback: approximate solar position
            sun_long = self._approximate_sun_longitude(dt)

        # Earth is always 180° opposite Sun
        earth_long = (sun_long + 180) % 360

        return DailyCode(
            timestamp=dt,
            sun_activation=self.longitude_to_activation(sun_long),
            earth_activation=self.longitude_to_activation(earth_long)
        )

    def _approximate_sun_longitude(self, dt: datetime) -> float:
        """
        Approximate Sun's ecliptic longitude from date.

        This is a simplified calculation for when no ephemeris is available.
        Accuracy: ~1° (sufficient for gate-level, not line-level)

        For high-fidelity calculations, use swisseph ephemeris.
        """
        # Days from J2000.0 epoch (Jan 1, 2000, 12:00 TT)
        j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
        # Ensure dt is timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        days = (dt - j2000).total_seconds() / 86400.0

        # Mean longitude of Sun (simplified)
        # L = 280.46° + 0.9856474° × d
        mean_long = (280.46 + 0.9856474 * days) % 360

        # Mean anomaly
        # g = 357.528° + 0.9856003° × d
        g = math.radians((357.528 + 0.9856003 * days) % 360)

        # Equation of center (first two terms)
        # C ≈ 1.915° sin(g) + 0.020° sin(2g)
        center = 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)

        # True longitude
        true_long = (mean_long + center) % 360

        return true_long

    @staticmethod
    def _datetime_to_julian(dt: datetime) -> float:
        """Convert datetime to Julian Date."""
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)

        year = dt.year
        month = dt.month
        day = dt.day + (dt.hour + dt.minute/60 + dt.second/3600) / 24

        if month <= 2:
            year -= 1
            month += 12

        A = int(year / 100)
        B = 2 - A + int(A / 4)

        jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5

        return jd

    # ═══════════════════════════════════════════════════════════════════════════
    # DESIGN DATE: 88° Solar Arc
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_design_date(self, birth_jd: float, birth_sun_long: float) -> float:
        """
        Calculate the Design date using 88° solar arc method.

        CRITICAL: This uses 88 DEGREES of solar arc, NOT 88 days!
        The Design is calculated for when the Sun was 88° behind
        its birth position, approximately 88-89 days before birth.

        Args:
            birth_jd: Birth Julian date
            birth_sun_long: Sun's longitude at birth

        Returns:
            Design Julian date

        Note: For production use, requires ephemeris service with
              solcross_ut or equivalent function.
        """
        if not self._ephemeris:
            # Approximate: ~88.6 days before (Sun moves ~1°/day)
            return birth_jd - 88.6

        # Calculate target longitude (88° before birth position)
        target_long = (birth_sun_long - DESIGN_ARC_DEGREES) % 360

        # Use ephemeris to find exact crossing
        # search_start should be ~100 days before to ensure we find it
        search_start = birth_jd - 100

        if hasattr(self._ephemeris, 'solcross_ut'):
            return self._ephemeris.solcross_ut(target_long, search_start)
        else:
            # Binary search approximation
            return self._find_sun_crossing(target_long, search_start, birth_jd)

    def _find_sun_crossing(self, target_long: float, start_jd: float, end_jd: float) -> float:
        """Binary search to find when Sun crossed target longitude."""
        tolerance = 0.0001  # ~8 seconds precision

        while (end_jd - start_jd) > tolerance:
            mid_jd = (start_jd + end_jd) / 2
            mid_long = self._ephemeris.get_sun_longitude(mid_jd)

            # Handle wrap-around at 0°/360°
            diff = (mid_long - target_long + 180) % 360 - 180

            if abs(diff) < 0.001:
                return mid_jd
            elif diff > 0:
                end_jd = mid_jd
            else:
                start_jd = mid_jd

        return (start_jd + end_jd) / 2

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITY: Gate Information
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_gate_info(gate_number: int) -> Optional[Dict[str, Any]]:
        """
        Get complete information about a specific gate.

        Args:
            gate_number: Gate number (1-64)

        Returns:
            Complete gate data dictionary or None if invalid
        """
        gate_data = GATE_DATABASE.get(gate_number)
        if not gate_data:
            return None

        return {
            "number": gate_data.number,
            "binary": gate_data.binary,
            "king_wen_sequence": gate_data.king_wen_sequence,

            # Trigram composition
            "lower_trigram": {
                "binary": gate_data.lower_trigram,
                "trigram": BINARY_TO_TRIGRAM.get(gate_data.lower_trigram),
            },
            "upper_trigram": {
                "binary": gate_data.upper_trigram,
                "trigram": BINARY_TO_TRIGRAM.get(gate_data.upper_trigram),
            },

            # I-Ching Layer
            "iching": {
                "name": gate_data.iching_name,
                "chinese": gate_data.iching_chinese,
                "pinyin": gate_data.iching_pinyin,
                "judgment": gate_data.iching_judgment,
                "image": gate_data.iching_image,
            },

            # Human Design Layer
            "human_design": {
                "name": gate_data.hd_name,
                "keynote": gate_data.hd_keynote,
                "center": gate_data.hd_center,
                "circuit": gate_data.hd_circuit,
                "stream": gate_data.hd_stream,
            },

            # Gene Keys Layer (THE CRITICAL XP SPECTRUM)
            "gene_keys": {
                "shadow": gate_data.gk_shadow,
                "gift": gate_data.gk_gift,
                "siddhi": gate_data.gk_siddhi,
                "programming_partner": gate_data.gk_programming_partner,
                "codon_ring": gate_data.gk_codon_ring,
                "amino_acid": gate_data.gk_amino_acid,
            },

            # Wheel Position
            "wheel": {
                "index": gate_data.wheel_index,
                "start_degree": gate_data.start_degree,
                "zodiac_sign": gate_data.zodiac_sign,
                "zodiac_degree": gate_data.zodiac_degree,
            },
        }

    @staticmethod
    def get_hexagram_binary(gate_number: int) -> str:
        """
        Get the 6-bit binary representation of a gate.

        Binary is read from bottom to top:
        - Bits 0-2: Lower trigram
        - Bits 3-5: Upper trigram

        Args:
            gate_number: Gate number (1-64)

        Returns:
            6-character binary string (e.g., "111111" for Gate 1)
        """
        gate_data = GATE_DATABASE.get(gate_number)
        return gate_data.binary if gate_data else "000000"

    @staticmethod
    def binary_to_gate(binary: str) -> Optional[int]:
        """
        Convert a 6-bit binary string to its gate number.

        Args:
            binary: 6-character binary string

        Returns:
            Gate number (1-64) or None if invalid
        """
        for gate, data in GATE_DATABASE.items():
            if data.binary == binary:
                return gate
        return None

    @staticmethod
    def get_gene_key_spectrum(gate_number: int) -> Optional[Dict[str, str]]:
        """
        Get the Gene Key frequency spectrum for a gate.

        This is the core XP mapping for the Solo Leveling gamification:
        - Shadow: Low XP state (unconscious pattern)
        - Gift: Balanced state (conscious expression)
        - Siddhi: High XP state (transcendent expression)

        Args:
            gate_number: Gate number (1-64)

        Returns:
            Dict with shadow/gift/siddhi or None
        """
        gate_data = GATE_DATABASE.get(gate_number)
        if not gate_data:
            return None

        return {
            "shadow": gate_data.gk_shadow,
            "gift": gate_data.gk_gift,
            "siddhi": gate_data.gk_siddhi,
            "programming_partner": gate_data.gk_programming_partner,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CHANNEL & DEFINITION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def find_channels(active_gates: set) -> List[ChannelData]:
        """
        Find all defined channels from a set of active gates.

        A channel is defined when BOTH its gates are active.

        Args:
            active_gates: Set of active gate numbers

        Returns:
            List of ChannelData for all defined channels
        """
        defined_channels = []

        for (gate1, gate2), channel in CHANNELS.items():
            if gate1 in active_gates and gate2 in active_gates:
                defined_channels.append(channel)

        return defined_channels

    @staticmethod
    def find_defined_centers(active_gates: set) -> set:
        """
        Find all defined centers from active gates.

        A center is defined if it has at least one CHANNEL
        (not just an active gate).

        Args:
            active_gates: Set of active gate numbers

        Returns:
            Set of defined Center values
        """
        channels = IChingKernel.find_channels(active_gates)
        defined = set()

        for channel in channels:
            defined.add(channel.center_1)
            defined.add(channel.center_2)

        return defined

    @staticmethod
    def determine_type(defined_centers: set, channels: List[ChannelData]) -> str:
        """
        Determine Human Design Type from centers and channels.

        Type hierarchy:
        1. No centers defined → Reflector
        2. Sacral defined + motor-to-throat → Manifesting Generator
        3. Sacral defined → Generator
        4. Motor-to-throat → Manifestor
        5. Default → Projector

        Args:
            defined_centers: Set of defined Center values
            channels: List of defined channels

        Returns:
            Type string
        """
        # Rule 1: No Definition = Reflector
        if not defined_centers:
            return "Reflector"

        has_sacral = Center.SACRAL in defined_centers
        has_motor_to_throat = IChingKernel._check_motor_to_throat(defined_centers, channels)

        # Rule 2 & 3: Sacral defined
        if has_sacral:
            if has_motor_to_throat:
                return "Manifesting Generator"
            else:
                return "Generator"

        # Rule 4: Motor to Throat (no Sacral)
        if has_motor_to_throat:
            return "Manifestor"

        # Rule 5: Default
        return "Projector"

    @staticmethod
    def _check_motor_to_throat(defined_centers: set, channels: List[ChannelData]) -> bool:
        """
        Check if there's a path from any motor center to throat.

        Motor Centers: Sacral, Solar Plexus, Heart, Root

        Uses BFS to find any path through defined channels.
        """
        motors = {Center.SACRAL, Center.SOLAR_PLEXUS, Center.HEART, Center.ROOT}
        defined_motors = motors & defined_centers

        if not defined_motors or Center.THROAT not in defined_centers:
            return False

        # Build adjacency graph from channels
        graph = {}
        for channel in channels:
            c1, c2 = channel.center_1, channel.center_2
            if c1 not in graph:
                graph[c1] = set()
            if c2 not in graph:
                graph[c2] = set()
            graph[c1].add(c2)
            graph[c2].add(c1)

        # BFS from each motor to throat
        for motor in defined_motors:
            if motor not in graph:
                continue

            visited = {motor}
            queue = [motor]

            while queue:
                current = queue.pop(0)
                if current == Center.THROAT:
                    return True

                for neighbor in graph.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # PROFILE CALCULATION
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_profile(personality_sun_line: int, design_sun_line: int) -> Dict[str, Any]:
        """
        Calculate Profile from Sun lines.

        Profile = Personality Sun Line / Design Sun Line

        Args:
            personality_sun_line: Line of Personality Sun (1-6)
            design_sun_line: Line of Design Sun (1-6)

        Returns:
            Profile data dictionary
        """
        profile_data = PROFILES.get((personality_sun_line, design_sun_line))

        if profile_data:
            return {
                "line_1": personality_sun_line,
                "line_2": design_sun_line,
                "name": profile_data.name,
                "angle": profile_data.angle,
                "cross_type": profile_data.cross_type,
                "theme": profile_data.theme,
            }

        # Fallback for invalid combinations
        return {
            "line_1": personality_sun_line,
            "line_2": design_sun_line,
            "name": f"{personality_sun_line}/{design_sun_line}",
            "angle": "Unknown",
            "cross_type": "Unknown",
            "theme": "Non-standard profile",
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # INCARNATION CROSS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_incarnation_cross(
        personality_sun_gate: int,
        cross_type: str
    ) -> str:
        """
        Get the Incarnation Cross name.

        Args:
            personality_sun_gate: Personality Sun's gate number
            cross_type: "RAC", "JXP", or "LAC"

        Returns:
            Incarnation Cross name
        """
        crosses = INCARNATION_CROSSES.get(personality_sun_gate, {})
        return crosses.get(cross_type, f"Cross of Gate {personality_sun_gate}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: SWISS EPHEMERIS WRAPPER (Optional High-Fidelity)
# ═══════════════════════════════════════════════════════════════════════════════

class SwissEphemerisService:
    """
    Swiss Ephemeris wrapper for high-fidelity planetary calculations.

    This service provides exact solar longitudes for precise gate/line
    calculations, down to tone and base level.

    Requires: pip install pyswisseph
    """

    def __init__(self, ephemeris_path: str = None):
        """
        Initialize the ephemeris service.

        Args:
            ephemeris_path: Path to Swiss Ephemeris data files (optional)
        """
        try:
            import swisseph as swe
            self._swe = swe

            if ephemeris_path:
                swe.set_ephe_path(ephemeris_path)

            self._available = True
        except ImportError:
            self._swe = None
            self._available = False

    @property
    def is_available(self) -> bool:
        """Check if ephemeris is available."""
        return self._available

    def get_sun_longitude(self, jd: float) -> float:
        """
        Get Sun's tropical longitude at Julian Date.

        Args:
            jd: Julian Date

        Returns:
            Sun's ecliptic longitude (0-360°)
        """
        if not self._available:
            raise RuntimeError("Swiss Ephemeris not available")

        # Calculate Sun position (tropical)
        result = self._swe.calc_ut(jd, self._swe.SUN)
        return result[0][0]  # Longitude is first element

    def get_planetary_positions(self, jd: float) -> Dict[str, float]:
        """
        Get positions of all HD-relevant bodies.

        Returns longitudes for:
        - Sun, Earth (180° from Sun)
        - Moon, Nodes (North/South)
        - Mercury, Venus, Mars, Jupiter, Saturn
        - Uranus, Neptune, Pluto

        Args:
            jd: Julian Date

        Returns:
            Dict mapping body name to longitude
        """
        if not self._available:
            raise RuntimeError("Swiss Ephemeris not available")

        bodies = {
            "Sun": self._swe.SUN,
            "Moon": self._swe.MOON,
            "Mercury": self._swe.MERCURY,
            "Venus": self._swe.VENUS,
            "Mars": self._swe.MARS,
            "Jupiter": self._swe.JUPITER,
            "Saturn": self._swe.SATURN,
            "Uranus": self._swe.URANUS,
            "Neptune": self._swe.NEPTUNE,
            "Pluto": self._swe.PLUTO,
            "North Node": self._swe.TRUE_NODE,
        }

        positions = {}
        for name, body_id in bodies.items():
            result = self._swe.calc_ut(jd, body_id)
            positions[name] = result[0][0]

        # Earth is opposite Sun
        positions["Earth"] = (positions["Sun"] + 180) % 360

        # South Node is opposite North Node
        positions["South Node"] = (positions["North Node"] + 180) % 360

        return positions

    def solcross_ut(self, target_long: float, start_jd: float) -> float:
        """
        Find when Sun crossed a specific longitude.

        Args:
            target_long: Target longitude (0-360°)
            start_jd: Start Julian Date for search

        Returns:
            Julian Date of crossing
        """
        if not self._available:
            raise RuntimeError("Swiss Ephemeris not available")

        return self._swe.solcross_ut(target_long, start_jd)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12: VERIFICATION & TESTING
# ═══════════════════════════════════════════════════════════════════════════════

def verify_gate_database():
    """
    Verify the integrity of the gate database.

    Checks:
    1. All 64 gates present
    2. All binaries unique
    3. All wheel indices valid (0-63)
    4. Programming partners are symmetric
    """
    errors = []

    # Check all 64 gates present
    for i in range(1, 65):
        if i not in GATE_DATABASE:
            errors.append(f"Missing gate {i}")

    # Check binary uniqueness
    binaries = {}
    for gate, data in GATE_DATABASE.items():
        if data.binary in binaries:
            errors.append(f"Duplicate binary {data.binary}: gates {binaries[data.binary]} and {gate}")
        binaries[data.binary] = gate

    # Check wheel indices
    indices = set()
    for gate, data in GATE_DATABASE.items():
        if data.wheel_index < 0 or data.wheel_index > 63:
            errors.append(f"Invalid wheel_index {data.wheel_index} for gate {gate}")
        if data.wheel_index in indices:
            errors.append(f"Duplicate wheel_index {data.wheel_index}")
        indices.add(data.wheel_index)

    # Check programming partners are symmetric
    for gate, data in GATE_DATABASE.items():
        partner_gate = data.gk_programming_partner
        if partner_gate in GATE_DATABASE:
            partner_data = GATE_DATABASE[partner_gate]
            if partner_data.gk_programming_partner != gate:
                    errors.append(
                        f"Asymmetric programming partners: {gate} -> {partner_gate} -> "
                        f"{partner_data.gk_programming_partner}"
                    )
    return errors


def run_calculation_tests():
    """
    Run test cases to verify calculation accuracy.
    """
    kernel = IChingKernel()
    tests = []

    # Test 1: Gate 41 starts at 302° (2° Aquarius)
    # With 58° offset: 302 + 58 = 360 = 0 on wheel = index 0 = Gate 41
    activation = kernel.longitude_to_activation(302.0)
    tests.append({
        "name": "Gate 41 at 302°",
        "expected_gate": 41,
        "actual_gate": activation.gate,
        "passed": activation.gate == 41
    })

    # Test 2: Gate 1 at 223.25° (13.25° Scorpio)
    # Gate 1 is at wheel index 50, zodiac longitude = (50 * 5.625 - 58) % 360 = 223.25°
    activation = kernel.longitude_to_activation(223.25)
    tests.append({
        "name": "Gate 1 at 223.25° (Scorpio 13°)",
        "expected_gate": 1,
        "actual_gate": activation.gate,
        "passed": activation.gate == 1
    })

    # Test 3: Gate 2 at 43.25° (13.25° Taurus)
    # Gate 2 is at wheel index 18, zodiac longitude = (18 * 5.625 - 58) % 360 = 43.25°
    activation = kernel.longitude_to_activation(43.25)
    tests.append({
        "name": "Gate 2 at 43.25° (Taurus 13°)",
        "expected_gate": 2,
        "actual_gate": activation.gate,
        "passed": activation.gate == 2
    })

    # Test 4: Line calculation (first line of any gate should be line 1)
    # Gate 41 spans 302° - 307.625°
    # Line 1 should be 302° - 302.9375°
    activation = kernel.longitude_to_activation(302.5)
    tests.append({
        "name": "Line 1 calculation",
        "expected_line": 1,
        "actual_line": activation.line,
        "passed": activation.line == 1
    })

    # Test 5: Line 6 calculation
    # Line 6 should be near end of gate
    activation = kernel.longitude_to_activation(307.0)
    tests.append({
        "name": "Line 6 calculation",
        "expected_line": 6,
        "actual_line": activation.line,
        "passed": activation.line == 6
    })

    # Test 6: Binary verification
    gate_1_binary = kernel.get_hexagram_binary(1)
    tests.append({
        "name": "Gate 1 binary (Creative)",
        "expected": "111111",
        "actual": gate_1_binary,
        "passed": gate_1_binary == "111111"
    })

    gate_2_binary = kernel.get_hexagram_binary(2)
    tests.append({
        "name": "Gate 2 binary (Receptive)",
        "expected": "000000",
        "actual": gate_2_binary,
        "passed": gate_2_binary == "000000"
    })

    # Test 7: Channel detection
    active_gates = {64, 47}  # Channel of Abstraction
    channels = kernel.find_channels(active_gates)
    tests.append({
        "name": "Channel detection (64-47)",
        "expected": 1,
        "actual": len(channels),
        "passed": len(channels) == 1 and channels[0].name == "Abstraction"
    })

    # Test 8: Type determination - Reflector (no definition)
    hd_type = kernel.determine_type(set(), [])
    tests.append({
        "name": "Type: Reflector",
        "expected": "Reflector",
        "actual": hd_type,
        "passed": hd_type == "Reflector"
    })

    # Test 9: Type determination - Generator (Sacral defined)
    active = {59, 6}  # Intimacy channel (Sacral-Solar Plexus)
    channels = kernel.find_channels(active)
    centers = kernel.find_defined_centers(active)
    hd_type = kernel.determine_type(centers, channels)
    tests.append({
        "name": "Type: Generator (Sacral defined)",
        "expected": "Generator",
        "actual": hd_type,
        "passed": hd_type == "Generator"
    })

    # Test 10: Profile calculation
    profile = kernel.calculate_profile(3, 5)
    tests.append({
        "name": "Profile 3/5",
        "expected": "Martyr/Heretic",
        "actual": profile["name"],
        "passed": profile["name"] == "Martyr/Heretic"
    })

    return tests


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("I-CHING LOGIC KERNEL v1.0 - VERIFICATION")
    print("=" * 80)

    # Verify database integrity
    print("\n📊 DATABASE INTEGRITY CHECK")
    print("-" * 40)
    errors = verify_gate_database()
    if errors:
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("  ✅ All 64 gates present")
        print("  ✅ All binaries unique")
        print("  ✅ All wheel indices valid")
        print("  ✅ Programming partners symmetric")

    # Run calculation tests
    print("\n📐 CALCULATION TESTS")
    print("-" * 40)
    tests = run_calculation_tests()
    passed = sum(1 for t in tests if t["passed"])
    total = len(tests)

    for test in tests:
        status = "✅" if test["passed"] else "❌"
        print(f"  {status} {test['name']}")
        if not test["passed"]:
            print(f"      Expected: {test.get('expected', test.get('expected_gate', test.get('expected_line', '?')))}")
            print(f"      Actual:   {test.get('actual', test.get('actual_gate', test.get('actual_line', '?')))}")

    print(f"\n  Results: {passed}/{total} tests passed")

    # Demo: Daily Code
    print("\n🌞 DAILY CODE DEMO")
    print("-" * 40)
    kernel = IChingKernel()
    daily = kernel.get_daily_code()

    print(f"  Timestamp: {daily.timestamp}")
    print(f"  Sun Gate:  {daily.sun_activation.gate} - {daily.sun_activation.hexagram_name}")
    print(
        f"  Sun Line:  {daily.sun_activation.line} ("
        f"{daily.sun_activation.line_archetype.name if daily.sun_activation.line_archetype else 'Unknown'})"
    )
    print(f"  Earth Gate: {daily.earth_activation.gate} - {daily.earth_activation.hexagram_name}")
    print("\n  Gene Key Focus:")
    gk = daily.gene_key_focus
    print(f"    Shadow: {gk['shadow']}")
    print(f"    Gift:   {gk['gift']}")
    print(f"    Siddhi: {gk['siddhi']}")

    # Demo: Gate Info
    print("\n📖 GATE INFO DEMO (Gate 1: The Creative)")
    print("-" * 40)
    info = kernel.get_gate_info(1)
    print(f"  Binary: {info['binary']}")
    print(f"  I-Ching: {info['iching']['name']} ({info['iching']['chinese']})")
    print(f"  Human Design: {info['human_design']['name']}")
    print(f"  Center: {info['human_design']['center']}")
    print("  Gene Keys:")
    print(f"    Shadow: {info['gene_keys']['shadow']}")
    print(f"    Gift: {info['gene_keys']['gift']}")
    print(f"    Siddhi: {info['gene_keys']['siddhi']}")

    print("\n" + "=" * 80)
    print("KERNEL VERIFICATION COMPLETE")
    print("=" * 80 + "\n")
