"""
Human Design Constants - Production Configuration

Source: dturkuler/humandesign_api (GPL-3.0)
Verified against Jovian Archive and Ra Uru Hu BlackBook.

All configuration constants for Human Design calculations.
NO calculation logic here - pure constants and mappings.
"""

# -----------------------------------------------------------------------------
# EPHEMERIS CONFIGURATION
# -----------------------------------------------------------------------------

# IGING offset - synchronizes zodiac (0° Aries) with gate circle (Gate 41 at 302°)
# This 58° offset is fundamental to HD calculations
IGING_OFFSET = 58

# Swiss Ephemeris planet codes
SWE_PLANETS = {
    "Sun": 0,
    "Earth": 0,  # Calculated as Sun + 180°
    "Moon": 1,
    "North_Node": 11,  # True Node
    "South_Node": 11,  # Calculated as North Node + 180°
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
}

# Design calculation: 88° solar arc (NOT 88 days!)
DESIGN_ARC_DEGREES = 88

# -----------------------------------------------------------------------------
# GATE CIRCLE - I CHING WHEEL ORDER
# -----------------------------------------------------------------------------

# 64 gates in order around the wheel, starting from Gate 41
# Gate 41 begins at 302° (2° Aquarius)
# Each gate spans exactly 5.625° (360/64)
IGING_CIRCLE_LIST = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# -----------------------------------------------------------------------------
# GATE TO CENTER MAPPING
# -----------------------------------------------------------------------------

# All 64 gates mapped to their respective centers
GATE_TO_CENTER = {
    # Head Center (3 gates) - Inspiration & Mental Pressure
    64: "Head", 61: "Head", 63: "Head",
    
    # Ajna Center (6 gates) - Mental Awareness & Conceptualization
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    
    # Throat Center (11 gates) - Communication & Manifestation
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat", 12: "Throat",
    45: "Throat", 33: "Throat", 8: "Throat", 31: "Throat", 20: "Throat", 16: "Throat",
    
    # G Center (8 gates) - Identity & Direction
    7: "G", 1: "G", 13: "G", 10: "G", 15: "G", 46: "G", 25: "G", 2: "G",
    
    # Heart/Ego Center (4 gates) - Willpower & Ego
    26: "Heart", 51: "Heart", 21: "Heart", 40: "Heart",
    
    # Sacral Center (9 gates) - Life Force & Response
    5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral", 9: "Sacral",
    3: "Sacral", 42: "Sacral", 27: "Sacral", 34: "Sacral",
    
    # Solar Plexus Center (7 gates) - Emotions & Awareness
    6: "Solar Plexus", 37: "Solar Plexus", 22: "Solar Plexus",
    36: "Solar Plexus", 30: "Solar Plexus", 55: "Solar Plexus", 49: "Solar Plexus",
    
    # Spleen Center (7 gates) - Intuition & Survival
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen",
    28: "Spleen", 32: "Spleen", 18: "Spleen",
    
    # Root Center (9 gates) - Pressure & Adrenal
    38: "Root", 54: "Root", 53: "Root", 60: "Root", 52: "Root",
    19: "Root", 39: "Root", 41: "Root", 58: "Root",
}

# Center abbreviations used in channel definitions
CENTER_ABBREV = {
    "HD": "Head",
    "AA": "Ajna",
    "TT": "Throat",
    "GC": "G",
    "HT": "Heart",
    "SL": "Sacral",
    "SP": "Solar Plexus",
    "SN": "Spleen",
    "RT": "Root",
}

# Reverse mapping
CENTER_TO_ABBREV = {v: k for k, v in CENTER_ABBREV.items()}

# List of all centers
ALL_CENTERS = ["Head", "Ajna", "Throat", "G", "Heart", "Sacral", "Solar Plexus", "Spleen", "Root"]

# Motor centers (can connect to Throat for Manifestor/MG)
MOTOR_CENTERS = {"Sacral", "Solar Plexus", "Heart", "Root"}

# -----------------------------------------------------------------------------
# CHANNEL DEFINITIONS
# -----------------------------------------------------------------------------

# Channel definitions: (gate1, gate2) -> (center1_abbrev, center2_abbrev)
GATES_CHAKRA_DICT = {
    (64, 47): ("HD", "AA"),
    (61, 24): ("HD", "AA"),
    (63, 4): ("HD", "AA"),
    (17, 62): ("AA", "TT"),
    (43, 23): ("AA", "TT"),
    (11, 56): ("AA", "TT"),
    (16, 48): ("TT", "SN"),
    (20, 57): ("TT", "SN"),
    (20, 34): ("TT", "SL"),
    (20, 10): ("TT", "GC"),
    (31, 7): ("TT", "GC"),
    (8, 1): ("TT", "GC"),
    (33, 13): ("TT", "GC"),
    (45, 21): ("TT", "HT"),
    (35, 36): ("TT", "SP"),
    (12, 22): ("TT", "SP"),
    (32, 54): ("SN", "RT"),
    (28, 38): ("SN", "RT"),
    (57, 34): ("SN", "SL"),
    (50, 27): ("SN", "SL"),
    (18, 58): ("SN", "RT"),
    (10, 34): ("GC", "SL"),
    (15, 5): ("GC", "SL"),
    (2, 14): ("GC", "SL"),
    (46, 29): ("GC", "SL"),
    (10, 57): ("GC", "SN"),
    (25, 51): ("GC", "HT"),
    (59, 6): ("SL", "SP"),
    (42, 53): ("SL", "RT"),
    (3, 60): ("SL", "RT"),
    (9, 52): ("SL", "RT"),
    (26, 44): ("HT", "SN"),
    (40, 37): ("HT", "SP"),
    (49, 19): ("SP", "RT"),
    (55, 39): ("SP", "RT"),
    (30, 41): ("SP", "RT"),
}

# Channel names and meanings
CHANNEL_NAMES = {
    (64, 47): ("Abstraction", "Design of mental activity and clarity"),
    (61, 24): ("Awareness", "Design of a thinker"),
    (63, 4): ("Logic", "Design of mental ease mixed with doubt"),
    (17, 62): ("Acceptance", "Design of an organizational being"),
    (43, 23): ("Structuring", "Design of individuality"),
    (11, 56): ("Curiosity", "Design of a searcher"),
    (16, 48): ("Wavelength", "Design of talent"),
    (20, 57): ("Brainwave", "Design of penetrating awareness"),
    (20, 34): ("Charisma", "Design where thoughts must become deeds"),
    (32, 54): ("Transformation", "Design of being driven"),
    (28, 38): ("Struggle", "Design of stubbornness"),
    (18, 58): ("Judgment", "Design of insatiability"),
    (20, 10): ("Awakening", "Design of commitment to higher principles"),
    (31, 7): ("Alpha", "Design of leadership for good or bad"),
    (8, 1): ("Inspiration", "Creative role model"),
    (33, 13): ("Prodigal", "Design of witness"),
    (10, 34): ("Exploration", "Design of following one's convictions"),
    (15, 5): ("Rhythm", "Design of being in the flow"),
    (2, 14): ("Beat", "Design of being the keeper of keys"),
    (46, 29): ("Discovery", "Design of succeeding where others fail"),
    (10, 57): ("Perfected Form", "Design of survival"),
    (57, 34): ("Power", "Design of an archetype"),
    (50, 27): ("Preservation", "Design of custodianship"),
    (45, 21): ("Money", "Design of a materialist"),
    (59, 6): ("Mating", "Design focused on reproduction"),
    (42, 53): ("Maturation", "Design of balanced development"),
    (3, 60): ("Mutation", "Energy which fluctuates and initiates"),
    (9, 52): ("Concentration", "Design of determination"),
    (26, 44): ("Surrender", "Design of a transmitter"),
    (25, 51): ("Initiation", "Design of needing to be first"),
    (40, 37): ("Community", "Design of being part seeking a whole"),
    (35, 36): ("Transitoriness", "Design of a jack of all trades"),
    (12, 22): ("Openness", "Design of a social being"),
    (49, 19): ("Synthesis", "Design of being sensitive"),
    (55, 39): ("Emoting", "Design of moodiness"),
    (30, 41): ("Recognition", "Design of focused energy"),
}

# -----------------------------------------------------------------------------
# TYPE CONFIGURATION
# -----------------------------------------------------------------------------

TYPE_DETAILS = {
    "Manifestor": {
        "strategy": "To Inform",
        "signature": "Peace",
        "not_self": "Anger",
        "aura": "Closed & Repelling",
        "percentage": 9,
    },
    "Generator": {
        "strategy": "Wait to Respond",
        "signature": "Satisfaction",
        "not_self": "Frustration",
        "aura": "Open & Enveloping",
        "percentage": 37,
    },
    "Manifesting Generator": {
        "strategy": "Wait to Respond, then Inform",
        "signature": "Satisfaction",
        "not_self": "Frustration & Anger",
        "aura": "Open & Enveloping",
        "percentage": 33,
    },
    "Projector": {
        "strategy": "Wait for the Invitation",
        "signature": "Success",
        "not_self": "Bitterness",
        "aura": "Focused & Absorbing",
        "percentage": 20,
    },
    "Reflector": {
        "strategy": "Wait a Lunar Cycle",
        "signature": "Surprise",
        "not_self": "Disappointment",
        "aura": "Sampling & Resistant",
        "percentage": 1,
    },
}

# -----------------------------------------------------------------------------
# AUTHORITY CONFIGURATION
# -----------------------------------------------------------------------------

AUTHORITY_NAMES = {
    "SP": "Emotional Authority",
    "SL": "Sacral Authority",
    "SN": "Splenic Authority",
    "HT": "Ego-Manifested Authority",
    "HT_GC": "Ego-Projected Authority",
    "GC": "Self-Projected Authority",
    "lunar": "Lunar Authority",
    "outer": "No Inner Authority",
}

# Authority hierarchy (order of precedence)
AUTHORITY_HIERARCHY = ["SP", "SL", "SN", "HT", "GC"]

# -----------------------------------------------------------------------------
# DEFINITION CONFIGURATION
# -----------------------------------------------------------------------------

DEFINITION_NAMES = {
    0: "No Definition",
    1: "Single Definition",
    2: "Split Definition",
    3: "Triple Split Definition",
    4: "Quadruple Split Definition",
}

# -----------------------------------------------------------------------------
# PROFILE CONFIGURATION
# -----------------------------------------------------------------------------

PROFILE_NAMES = {
    (1, 3): "1/3 Investigator Martyr",
    (1, 4): "1/4 Investigator Opportunist",
    (2, 4): "2/4 Hermit Opportunist",
    (2, 5): "2/5 Hermit Heretic",
    (3, 5): "3/5 Martyr Heretic",
    (3, 6): "3/6 Martyr Role Model",
    (4, 6): "4/6 Opportunist Role Model",
    (4, 1): "4/1 Opportunist Investigator",
    (5, 1): "5/1 Heretic Investigator",
    (5, 2): "5/2 Heretic Hermit",
    (6, 2): "6/2 Role Model Hermit",
    (6, 3): "6/3 Role Model Martyr",
}

# Incarnation cross type based on profile lines
IC_CROSS_TYPE = {
    (1, 3): "RAC",  # Right Angle Cross
    (1, 4): "RAC",
    (2, 4): "RAC",
    (2, 5): "RAC",
    (3, 5): "RAC",
    (3, 6): "RAC",
    (4, 6): "RAC",
    (4, 1): "JXP",  # Juxtaposition
    (5, 1): "LAC",  # Left Angle Cross
    (5, 2): "LAC",
    (6, 2): "LAC",
    (6, 3): "LAC",
}

# -----------------------------------------------------------------------------
# INCARNATION CROSS DATABASE
# -----------------------------------------------------------------------------

# Key: Personality Sun Gate
# Value: Dict with RAC, JC, LAC cross names
INCARNATION_CROSS_DB = {
    # Quarter of Initiation (Purpose via Mind)
    13: {"RAC": "Right Angle Cross of the Sphinx (1)", "JC": "Juxtaposition Cross of Listening", "LAC": "Left Angle Cross of Masks (1)"},
    49: {"RAC": "Right Angle Cross of Explanation (1)", "JC": "Juxtaposition Cross of Principles", "LAC": "Left Angle Cross of Revolution (1)"},
    30: {"RAC": "Right Angle Cross of Contagion (1)", "JC": "Juxtaposition Cross of Fates", "LAC": "Left Angle Cross of Industry (1)"},
    55: {"RAC": "Right Angle Cross of the Sleeping Phoenix (1)", "JC": "Juxtaposition Cross of Moods", "LAC": "Left Angle Cross of Spirit (1)"},
    37: {"RAC": "Right Angle Cross of Planning (1)", "JC": "Juxtaposition Cross of Bargains", "LAC": "Left Angle Cross of Migration (1)"},
    63: {"RAC": "Right Angle Cross of Consciousness (1)", "JC": "Juxtaposition Cross of Doubts", "LAC": "Left Angle Cross of Dominion (1)"},
    22: {"RAC": "Right Angle Cross of Rulership (1)", "JC": "Juxtaposition Cross of Grace", "LAC": "Left Angle Cross of Informing (1)"},
    36: {"RAC": "Right Angle Cross of Eden (1)", "JC": "Juxtaposition Cross of Crisis", "LAC": "Left Angle Cross of the Plane (1)"},
    25: {"RAC": "Right Angle Cross of the Vessel of Love (1)", "JC": "Juxtaposition Cross of Innocence", "LAC": "Left Angle Cross of Healing (1)"},
    17: {"RAC": "Right Angle Cross of Service (1)", "JC": "Juxtaposition Cross of Opinions", "LAC": "Left Angle Cross of Upheaval (1)"},
    21: {"RAC": "Right Angle Cross of Tension (1)", "JC": "Juxtaposition Cross of Control", "LAC": "Left Angle Cross of Endeavor (1)"},
    51: {"RAC": "Right Angle Cross of Penetration (1)", "JC": "Juxtaposition Cross of Shock", "LAC": "Left Angle Cross of the Clarion (1)"},
    42: {"RAC": "Right Angle Cross of the Maya (1)", "JC": "Juxtaposition Cross of Completion", "LAC": "Left Angle Cross of Limitation (1)"},
    3: {"RAC": "Right Angle Cross of Laws (1)", "JC": "Juxtaposition Cross of Mutation", "LAC": "Left Angle Cross of Wishes (1)"},
    27: {"RAC": "Right Angle Cross of the Unexpected (1)", "JC": "Juxtaposition Cross of Caring", "LAC": "Left Angle Cross of Alignment (1)"},
    24: {"RAC": "Right Angle Cross of the Four Ways (1)", "JC": "Juxtaposition Cross of Rationalization", "LAC": "Left Angle Cross of Incarnation (1)"},
    
    # Quarter of Civilization (Purpose via Form)
    2: {"RAC": "Right Angle Cross of the Sphinx (2)", "JC": "Juxtaposition Cross of the Driver", "LAC": "Left Angle Cross of Defiance (1)"},
    23: {"RAC": "Right Angle Cross of Explanation (2)", "JC": "Juxtaposition Cross of Assimilation", "LAC": "Left Angle Cross of Dedication (1)"},
    8: {"RAC": "Right Angle Cross of Contagion (2)", "JC": "Juxtaposition Cross of Contribution", "LAC": "Left Angle Cross of Uncertainty (1)"},
    20: {"RAC": "Right Angle Cross of the Sleeping Phoenix (2)", "JC": "Juxtaposition Cross of the Now", "LAC": "Left Angle Cross of Duality (1)"},
    16: {"RAC": "Right Angle Cross of Planning (2)", "JC": "Juxtaposition Cross of Experimentation", "LAC": "Left Angle Cross of Identification (1)"},
    35: {"RAC": "Right Angle Cross of Consciousness (2)", "JC": "Juxtaposition Cross of Experience", "LAC": "Left Angle Cross of Separation (1)"},
    45: {"RAC": "Right Angle Cross of Rulership (2)", "JC": "Juxtaposition Cross of Possession", "LAC": "Left Angle Cross of Confrontation (1)"},
    12: {"RAC": "Right Angle Cross of Eden (2)", "JC": "Juxtaposition Cross of Articulation", "LAC": "Left Angle Cross of Education (1)"},
    15: {"RAC": "Right Angle Cross of the Vessel of Love (2)", "JC": "Juxtaposition Cross of Extremes", "LAC": "Left Angle Cross of Prevention (1)"},
    52: {"RAC": "Right Angle Cross of Service (2)", "JC": "Juxtaposition Cross of Stillness", "LAC": "Left Angle Cross of Demands (1)"},
    39: {"RAC": "Right Angle Cross of Tension (2)", "JC": "Juxtaposition Cross of Provocation", "LAC": "Left Angle Cross of Individualism (1)"},
    53: {"RAC": "Right Angle Cross of Penetration (2)", "JC": "Juxtaposition Cross of Beginnings", "LAC": "Left Angle Cross of Cycles (1)"},
    62: {"RAC": "Right Angle Cross of the Maya (2)", "JC": "Juxtaposition Cross of Detail", "LAC": "Left Angle Cross of Obscuration (1)"},
    56: {"RAC": "Right Angle Cross of Laws (2)", "JC": "Juxtaposition Cross of Stimulation", "LAC": "Left Angle Cross of Distraction (1)"},
    31: {"RAC": "Right Angle Cross of the Unexpected (2)", "JC": "Juxtaposition Cross of Influence", "LAC": "Left Angle Cross of the Alpha (1)"},
    33: {"RAC": "Right Angle Cross of the Four Ways (2)", "JC": "Juxtaposition Cross of Retreat", "LAC": "Left Angle Cross of Refinement (1)"},
    
    # Quarter of Duality (Purpose via Bonding)
    7: {"RAC": "Right Angle Cross of the Sphinx (3)", "JC": "Juxtaposition Cross of Interaction", "LAC": "Left Angle Cross of Masks (2)"},
    4: {"RAC": "Right Angle Cross of Explanation (3)", "JC": "Juxtaposition Cross of Formulation", "LAC": "Left Angle Cross of Revolution (2)"},
    29: {"RAC": "Right Angle Cross of Contagion (3)", "JC": "Juxtaposition Cross of Commitment", "LAC": "Left Angle Cross of Industry (2)"},
    59: {"RAC": "Right Angle Cross of the Sleeping Phoenix (3)", "JC": "Juxtaposition Cross of Strategy", "LAC": "Left Angle Cross of Spirit (2)"},
    40: {"RAC": "Right Angle Cross of Planning (3)", "JC": "Juxtaposition Cross of Denial", "LAC": "Left Angle Cross of Migration (2)"},
    64: {"RAC": "Right Angle Cross of Consciousness (3)", "JC": "Juxtaposition Cross of Confusion", "LAC": "Left Angle Cross of Dominion (2)"},
    47: {"RAC": "Right Angle Cross of Rulership (3)", "JC": "Juxtaposition Cross of Oppression", "LAC": "Left Angle Cross of Informing (2)"},
    6: {"RAC": "Right Angle Cross of Eden (3)", "JC": "Juxtaposition Cross of Conflict", "LAC": "Left Angle Cross of the Plane (2)"},
    46: {"RAC": "Right Angle Cross of the Vessel of Love (3)", "JC": "Juxtaposition Cross of Serendipity", "LAC": "Left Angle Cross of Healing (2)"},
    18: {"RAC": "Right Angle Cross of Service (3)", "JC": "Juxtaposition Cross of Correction", "LAC": "Left Angle Cross of Upheaval (2)"},
    48: {"RAC": "Right Angle Cross of Tension (3)", "JC": "Juxtaposition Cross of Depth", "LAC": "Left Angle Cross of Endeavor (2)"},
    57: {"RAC": "Right Angle Cross of Penetration (3)", "JC": "Juxtaposition Cross of Intuition", "LAC": "Left Angle Cross of the Clarion (2)"},
    32: {"RAC": "Right Angle Cross of the Maya (3)", "JC": "Juxtaposition Cross of Conservation", "LAC": "Left Angle Cross of Limitation (2)"},
    50: {"RAC": "Right Angle Cross of Laws (3)", "JC": "Juxtaposition Cross of Values", "LAC": "Left Angle Cross of Wishes (2)"},
    28: {"RAC": "Right Angle Cross of the Unexpected (3)", "JC": "Juxtaposition Cross of Risks", "LAC": "Left Angle Cross of Alignment (2)"},
    44: {"RAC": "Right Angle Cross of the Four Ways (3)", "JC": "Juxtaposition Cross of Alertness", "LAC": "Left Angle Cross of Incarnation (2)"},
    
    # Quarter of Mutation (Purpose via Transformation)
    1: {"RAC": "Right Angle Cross of the Sphinx (4)", "JC": "Juxtaposition Cross of Self-Expression", "LAC": "Left Angle Cross of Defiance (2)"},
    43: {"RAC": "Right Angle Cross of Explanation (4)", "JC": "Juxtaposition Cross of Insight", "LAC": "Left Angle Cross of Dedication (2)"},
    14: {"RAC": "Right Angle Cross of Contagion (4)", "JC": "Juxtaposition Cross of Empowering", "LAC": "Left Angle Cross of Uncertainty (2)"},
    34: {"RAC": "Right Angle Cross of the Sleeping Phoenix (4)", "JC": "Juxtaposition Cross of Power", "LAC": "Left Angle Cross of Duality (2)"},
    9: {"RAC": "Right Angle Cross of Planning (4)", "JC": "Juxtaposition Cross of Focus", "LAC": "Left Angle Cross of Identification (2)"},
    5: {"RAC": "Right Angle Cross of Consciousness (4)", "JC": "Juxtaposition Cross of Habits", "LAC": "Left Angle Cross of Separation (2)"},
    26: {"RAC": "Right Angle Cross of Rulership (4)", "JC": "Juxtaposition Cross of the Trickster", "LAC": "Left Angle Cross of Control (2)"},
    11: {"RAC": "Right Angle Cross of Eden (4)", "JC": "Juxtaposition Cross of Ideas", "LAC": "Left Angle Cross of Education (2)"},
    10: {"RAC": "Right Angle Cross of the Vessel of Love (4)", "JC": "Juxtaposition Cross of Behavior", "LAC": "Left Angle Cross of Prevention (2)"},
    58: {"RAC": "Right Angle Cross of Service (4)", "JC": "Juxtaposition Cross of Vitality", "LAC": "Left Angle Cross of Demands (2)"},
    38: {"RAC": "Right Angle Cross of Tension (4)", "JC": "Juxtaposition Cross of Opposition", "LAC": "Left Angle Cross of Individualism (2)"},
    54: {"RAC": "Right Angle Cross of Penetration (4)", "JC": "Juxtaposition Cross of Ambition", "LAC": "Left Angle Cross of Cycles (2)"},
    61: {"RAC": "Right Angle Cross of the Maya (4)", "JC": "Juxtaposition Cross of Thinking", "LAC": "Left Angle Cross of Obscuration (2)"},
    60: {"RAC": "Right Angle Cross of Laws (4)", "JC": "Juxtaposition Cross of Limitation", "LAC": "Left Angle Cross of Distraction (2)"},
    41: {"RAC": "Right Angle Cross of the Unexpected (4)", "JC": "Juxtaposition Cross of Fantasy", "LAC": "Left Angle Cross of the Alpha (2)"},
    19: {"RAC": "Right Angle Cross of the Four Ways (4)", "JC": "Juxtaposition Cross of Need", "LAC": "Left Angle Cross of Refinement (2)"},
}
