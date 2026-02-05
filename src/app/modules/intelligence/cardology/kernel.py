"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CHRONOS-MAGI CARDOLOGY LOGIC KERNEL                       ║
║                                                                              ║
║   A Stateless Implementation of the Order of the Magi System                 ║
║   Based on Olney H. Richmond's "The Mystic Test Book" (1893)                 ║
║                                                                              ║
║   This kernel provides deterministic calculations for:                       ║
║   - Birth Card computation from any date                                     ║
║   - Planetary Ruling Card based on zodiac sign                               ║
║   - Karma Cards (First/Second) via spread position analysis                  ║
║   - 52-Day Planetary Period timeline generation                              ║
║   - Grand Solar Spread quadration (90 yearly spreads)                        ║
║   - Relationship connection analysis                                         ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
║   License: For metaphysical research and personal development tools          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import copy


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: FOUNDATIONAL DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class Suit(Enum):
    """The four suits representing elements and life domains."""
    HEARTS = "♥"      # Water - Emotions, Love, Relationships (Spring)
    CLUBS = "♣"       # Fire - Knowledge, Communication, Ideas (Summer)
    DIAMONDS = "♦"    # Earth - Values, Money, Material (Fall)
    SPADES = "♠"      # Air - Work, Health, Wisdom, Spirituality (Winter)


class Planet(Enum):
    """The seven classical planets plus outer planets used in Cardology."""
    MERCURY = "Mercury"    # Communication, Speed, Short-term
    VENUS = "Venus"        # Love, Home, Beauty, Relationships
    MARS = "Mars"          # Action, Energy, Passion, Conflict
    JUPITER = "Jupiter"    # Expansion, Blessings, Fortune
    SATURN = "Saturn"      # Karma, Lessons, Challenges, Career
    URANUS = "Uranus"      # Freedom, Spirituality, Independence
    NEPTUNE = "Neptune"    # Dreams, Illusions, Hopes, Fears
    # Extended planets for 13-card spreads
    PLUTO = "Pluto"        # Transformation, Deep Change
    SUN = "Sun"            # Core Identity (Birth Card position)
    MOON = "Moon"          # Support, Nurturing, Emotional Foundation


@dataclass(frozen=True)
class Card:
    """
    Represents a playing card with its numeric and suit values.
    
    Solar Value: 1-52 position in the solar calendar system
    Spirit Value: Position in the Natural (Spirit) Spread
    """
    rank: int  # 1-13 (Ace=1, Jack=11, Queen=12, King=13)
    suit: Suit
    
    @property
    def rank_name(self) -> str:
        """Human-readable rank name."""
        names = {1: "Ace", 11: "Jack", 12: "Queen", 13: "King"}
        return names.get(self.rank, str(self.rank))
    
    @property
    def solar_value(self) -> int:
        """
        Solar Value: Position in the solar calendar (1-52).
        Hearts=1-13, Clubs=14-26, Diamonds=27-39, Spades=40-52
        """
        suit_offset = {
            Suit.HEARTS: 0,
            Suit.CLUBS: 13,
            Suit.DIAMONDS: 26,
            Suit.SPADES: 39
        }
        return self.rank + suit_offset[self.suit]
    
    @property
    def spot_value(self) -> int:
        """The numeric face value (1-13)."""
        return self.rank
    
    def __str__(self) -> str:
        return f"{self.rank_name} of {self.suit.name.title()}"
    
    def __repr__(self) -> str:
        return f"{self.rank_name[0] if self.rank > 10 or self.rank == 1 else self.rank}{self.suit.value}"
    
    @classmethod
    def from_solar_value(cls, solar_value: int) -> 'Card':
        """Create a card from its solar value (1-52)."""
        if solar_value == 0:
            # Special case: Joker (December 31)
            return JOKER
        if not 1 <= solar_value <= 52:
            raise ValueError(f"Solar value must be 1-52, got {solar_value}")
        
        suit_index = (solar_value - 1) // 13
        rank = ((solar_value - 1) % 13) + 1
        suits = [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]
        return cls(rank=rank, suit=suits[suit_index])


# Special card: The Joker (December 31)
JOKER = Card(rank=0, suit=Suit.HEARTS)  # Placeholder representation


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: THE NATURAL (SPIRIT) SPREAD - Ground Truth
# ═══════════════════════════════════════════════════════════════════════════════

"""
The Natural Spread (also called the Spirit Spread or Sun Spread) is the 
foundational arrangement of all 52 cards in their "divine" order.

Layout: 8 columns × 7 rows (with 3 Crown positions + 52 grid positions)
- Crown Line (Top Row): 3 positions for the "fixed" court cards
- Grid: 7 rows × 7 columns for planetary positions

Reading Direction: Right to Left, then Down (like Hebrew)

Column Planets: Mercury | Venus | Mars | Jupiter | Saturn | Uranus | Neptune
Row Planets:    Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune

The Natural Spread has cards in sequential order: A♥ → K♠
"""

def build_natural_spread() -> List[List[Card]]:
    """
    Constructs the Natural (Spirit) Spread - the primordial arrangement.
    
    Returns a 8×8 grid where:
    - Row 0: Crown Line (Sun row) - J♠, Q♠, K♠
    - Rows 1-7: Planetary rows (Mercury through Neptune)
    - Columns 0-6: Planetary columns (Neptune through Mercury, R→L)
    
    Cards fill in order A♥ through K♠ starting at position Mercury/Mercury.
    """
    # Initialize empty grid (8 rows, 7 cols for main + Crown)
    grid = [[None for _ in range(8)] for _ in range(8)]
    
    # Build the deck in natural order
    deck = []
    for suit in [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]:
        for rank in range(1, 14):
            deck.append(Card(rank=rank, suit=suit))
    
    # Fill the grid in the Natural Order pattern
    # Row 0 is Crown (Sun), Rows 1-7 are Mercury through Neptune
    # Reading right to left within each row
    
    # The Natural Spread fills like this:
    # Start at Mercury row (row 1), Mercury column (col 7, rightmost)
    # Go left, then down to next row, repeat
    
    card_index = 0
    for row in range(1, 8):  # Planetary rows
        for col in range(7, 0, -1):  # Right to left (Mercury to Neptune)
            if card_index < 49:  # 49 cards in main grid
                grid[row][col] = deck[card_index]
                card_index += 1
    
    # Crown line (row 0) gets J♠, Q♠, K♠ (cards 50, 51, 52)
    # These are the "fixed" positions
    grid[0][7] = deck[49]  # J♠ - rightmost Crown
    grid[0][6] = deck[50]  # Q♠ 
    grid[0][5] = deck[51]  # K♠ - the ultimate fixed card
    
    return grid


# Pre-computed Natural Spread for reference
NATURAL_SPREAD = build_natural_spread()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: THE LIFE SPREAD (First Quadration)
# ═══════════════════════════════════════════════════════════════════════════════

"""
The Life Spread (also called the Earth Spread or Mundane Spread) is created
by applying the Quadration algorithm to the Natural Spread exactly ONE time.

This spread represents our earthly existence - where each person's Birth Card
sits determines their life path and the energies they will work with.

The Quadration Algorithm (from Richmond's "Mystic Test Book"):
1. Arrange deck face up, ordered by suit (Hearts, Clubs, Diamonds, Spades)
2. Within each suit, order Ace to King
3. Stack suits: Hearts bottom, then Clubs, Diamonds, Spades on top
4. Turn deck over (now Hearts are on top)
5. Deal into 4 piles, 3 cards at a time (last 4 cards go 1 per pile)
6. Stack piles: 4th on 3rd on 2nd on 1st
7. Deal face down, 1 card per pile into 4 piles
8. Stack same way: 4th on 3rd on 2nd on 1st
"""

def quadrate_deck(deck: List[Card]) -> List[Card]:
    """
    Apply the Quadration algorithm to transform a deck.
    
    This is the core mathematical operation that generates
    all 90 solar spreads from the Natural order.
    """
    # Step 1-4: Ensure deck is in proper starting order
    # (Assuming deck is already arranged - we receive it that way)
    
    # Step 5: Deal into 4 piles, 3 cards at a time
    piles = [[], [], [], []]
    
    # Deal 3 cards at a time to each pile in rotation
    for i in range(0, 48, 3):  # 48 cards in groups of 3
        for j in range(3):
            pile_index = (i // 3) % 4
            piles[pile_index].append(deck[i + j])
    
    # Last 4 cards go 1 per pile
    for i, pile in enumerate(piles):
        pile.append(deck[48 + i])
    
    # Step 6: Stack piles (4th on 3rd on 2nd on 1st)
    intermediate = piles[0] + piles[1] + piles[2] + piles[3]
    
    # Step 7: Deal 1 card per pile into 4 new piles
    new_piles = [[], [], [], []]
    for i, card in enumerate(intermediate):
        new_piles[i % 4].append(card)
    
    # Step 8: Stack same way
    result = new_piles[0] + new_piles[1] + new_piles[2] + new_piles[3]
    
    return result


def build_life_spread() -> List[List[Card]]:
    """
    Constructs the Life Spread by quadrating the Natural Spread once.
    
    This spread shows where each card "lives" during our earthly existence.
    """
    # Get the deck in natural order
    natural_deck = []
    for suit in [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]:
        for rank in range(1, 14):
            natural_deck.append(Card(rank=rank, suit=suit))
    
    # Apply quadration
    life_deck = quadrate_deck(natural_deck)
    
    # Build grid same pattern as Natural Spread
    grid = [[None for _ in range(8)] for _ in range(8)]
    
    card_index = 0
    for row in range(1, 8):
        for col in range(7, 0, -1):
            if card_index < 49:
                grid[row][col] = life_deck[card_index]
                card_index += 1
    
    # Crown line
    grid[0][7] = life_deck[49]
    grid[0][6] = life_deck[50]
    grid[0][5] = life_deck[51]
    
    return grid


# Pre-computed Life Spread
LIFE_SPREAD = build_life_spread()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: THE GRAND SOLAR SPREADS (90 Yearly Spreads)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_solar_spread(age: int) -> List[List[Card]]:
    """
    Generate the Grand Solar Spread for a specific age (0-89).
    
    Age 0 = Life Spread (already quadrated once)
    Age 1 = Quadrate Life Spread once more
    ...
    Age 89 = Quadrate 89 times from Life Spread
    
    Ages 90+ cycle back: age % 90
    """
    effective_age = age % 90
    
    # Start with natural deck
    deck = []
    for suit in [Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES]:
        for rank in range(1, 14):
            deck.append(Card(rank=rank, suit=suit))
    
    # Quadrate (effective_age + 1) times (Life spread is already 1 quadration)
    for _ in range(effective_age + 1):
        deck = quadrate_deck(deck)
    
    # Build grid
    grid = [[None for _ in range(8)] for _ in range(8)]
    card_index = 0
    for row in range(1, 8):
        for col in range(7, 0, -1):
            if card_index < 49:
                grid[row][col] = deck[card_index]
                card_index += 1
    
    grid[0][7] = deck[49]
    grid[0][6] = deck[50]
    grid[0][5] = deck[51]
    
    return grid


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: BIRTH CARD CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

"""
The Magi Formula for Birth Card Calculation:
    Solar Value = 55 - ((Month × 2) + Day)

If result = 0: Joker (December 31)
If result < 0 or > 52: Formula error / invalid date

Solar Value maps directly to cards:
1-13: Ace♥ through King♥
14-26: Ace♣ through King♣
27-39: Ace♦ through King♦
40-52: Ace♠ through King♠
"""

def calculate_birth_card(month: int, day: int) -> Card:
    """
    Calculate the Birth Card for a given month and day.
    
    Args:
        month: 1-12
        day: 1-31
    
    Returns:
        The Birth Card for this date
    
    Raises:
        ValueError for invalid dates
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1-12, got {month}")
    if not 1 <= day <= 31:
        raise ValueError(f"Day must be 1-31, got {day}")
    
    # The Magi Formula
    solar_value = 55 - ((month * 2) + day)
    
    # Handle special cases
    if solar_value == 0:
        return JOKER  # December 31
    
    if solar_value < 0:
        # This shouldn't happen with valid dates
        raise ValueError(f"Invalid date produces negative solar value: {month}/{day}")
    
    return Card.from_solar_value(solar_value)


def calculate_birth_card_from_date(birth_date: date) -> Card:
    """Calculate Birth Card from a Python date object."""
    return calculate_birth_card(birth_date.month, birth_date.day)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: PLANETARY RULING CARD
# ═══════════════════════════════════════════════════════════════════════════════

"""
The Planetary Ruling Card is determined by:
1. Finding your Zodiac sun sign
2. Finding which classical planet rules that sign
3. Looking up that planet's position card in your Birth Card's Life Spread

Zodiac Rulerships (Classical):
- Aries: Mars
- Taurus: Venus
- Gemini: Mercury
- Cancer: Moon
- Leo: Sun (Birth Card itself)
- Virgo: Mercury
- Libra: Venus
- Scorpio: Mars (classical) / Pluto (modern)
- Sagittarius: Jupiter
- Capricorn: Saturn
- Aquarius: Saturn (classical) / Uranus (modern)
- Pisces: Jupiter (classical) / Neptune (modern)
"""

class ZodiacSign(Enum):
    ARIES = "Aries"          # Mar 21 - Apr 19
    TAURUS = "Taurus"        # Apr 20 - May 20
    GEMINI = "Gemini"        # May 21 - Jun 20
    CANCER = "Cancer"        # Jun 21 - Jul 22
    LEO = "Leo"              # Jul 23 - Aug 22
    VIRGO = "Virgo"          # Aug 23 - Sep 22
    LIBRA = "Libra"          # Sep 23 - Oct 22
    SCORPIO = "Scorpio"      # Oct 23 - Nov 21
    SAGITTARIUS = "Sagittarius"  # Nov 22 - Dec 21
    CAPRICORN = "Capricorn"  # Dec 22 - Jan 19
    AQUARIUS = "Aquarius"    # Jan 20 - Feb 18
    PISCES = "Pisces"        # Feb 19 - Mar 20


# Classical planetary rulerships (what Richmond would have used)
ZODIAC_RULERS_CLASSICAL = {
    ZodiacSign.ARIES: Planet.MARS,
    ZodiacSign.TAURUS: Planet.VENUS,
    ZodiacSign.GEMINI: Planet.MERCURY,
    ZodiacSign.CANCER: Planet.MOON,
    ZodiacSign.LEO: Planet.SUN,
    ZodiacSign.VIRGO: Planet.MERCURY,
    ZodiacSign.LIBRA: Planet.VENUS,
    ZodiacSign.SCORPIO: Planet.MARS,
    ZodiacSign.SAGITTARIUS: Planet.JUPITER,
    ZodiacSign.CAPRICORN: Planet.SATURN,
    ZodiacSign.AQUARIUS: Planet.SATURN,
    ZodiacSign.PISCES: Planet.JUPITER,
}


def get_zodiac_sign(month: int, day: int) -> ZodiacSign:
    """Determine zodiac sign from month and day."""
    zodiac_dates = [
        ((1, 20), (2, 18), ZodiacSign.AQUARIUS),
        ((2, 19), (3, 20), ZodiacSign.PISCES),
        ((3, 21), (4, 19), ZodiacSign.ARIES),
        ((4, 20), (5, 20), ZodiacSign.TAURUS),
        ((5, 21), (6, 20), ZodiacSign.GEMINI),
        ((6, 21), (7, 22), ZodiacSign.CANCER),
        ((7, 23), (8, 22), ZodiacSign.LEO),
        ((8, 23), (9, 22), ZodiacSign.VIRGO),
        ((9, 23), (10, 22), ZodiacSign.LIBRA),
        ((10, 23), (11, 21), ZodiacSign.SCORPIO),
        ((11, 22), (12, 21), ZodiacSign.SAGITTARIUS),
        ((12, 22), (12, 31), ZodiacSign.CAPRICORN),
        ((1, 1), (1, 19), ZodiacSign.CAPRICORN),
    ]
    
    for (start_m, start_d), (end_m, end_d), sign in zodiac_dates:
        if start_m == end_m:
            if month == start_m and start_d <= day <= end_d:
                return sign
        else:
            if (month == start_m and day >= start_d) or (month == end_m and day <= end_d):
                return sign
    
    raise ValueError(f"Could not determine zodiac for {month}/{day}")


def find_card_position_in_spread(card: Card, spread: List[List[Card]]) -> Tuple[int, int]:
    """Find the row and column position of a card in a spread."""
    for row_idx, row in enumerate(spread):
        for col_idx, c in enumerate(row):
            if c and c.rank == card.rank and c.suit == card.suit:
                return (row_idx, col_idx)
    raise ValueError(f"Card {card} not found in spread")


def get_planetary_card(birth_card: Card, planet: Planet, spread: List[List[Card]] = None) -> Optional[Card]:
    """
    Get the card at a specific planetary position relative to the birth card.
    
    The spread is read right-to-left, starting from the birth card position.
    Planet order: Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
    
    Moon is the card to the RIGHT (behind) the birth card.
    """
    if spread is None:
        spread = LIFE_SPREAD
    
    if planet == Planet.SUN:
        return birth_card
    
    try:
        row, col = find_card_position_in_spread(birth_card, spread)
    except ValueError:
        return None
    
    # Planet position offsets (how many cards to the LEFT of birth card)
    # Reading right-to-left, down, wrap to top-right
    planet_offsets = {
        Planet.MOON: -1,      # Behind (to the right)
        Planet.MERCURY: 1,
        Planet.VENUS: 2,
        Planet.MARS: 3,
        Planet.JUPITER: 4,
        Planet.SATURN: 5,
        Planet.URANUS: 6,
        Planet.NEPTUNE: 7,
        Planet.PLUTO: 8,
    }
    
    offset = planet_offsets.get(planet, 0)
    if offset == 0:
        return birth_card
    
    # Navigate the spread (right to left, wrapping)
    current_row, current_col = row, col
    
    if offset < 0:
        # Move right (Moon)
        for _ in range(abs(offset)):
            current_col += 1
            if current_col > 7:
                current_col = 1
                current_row -= 1
                if current_row < 1:
                    current_row = 7
    else:
        # Move left (other planets)
        for _ in range(offset):
            current_col -= 1
            if current_col < 1:
                current_col = 7
                current_row += 1
                if current_row > 7:
                    current_row = 0  # Crown line
                    current_col = 7
    
    return spread[current_row][current_col]


def calculate_ruling_card(birth_card: Card, zodiac: ZodiacSign) -> Card:
    """
    Calculate the Planetary Ruling Card based on zodiac sign.
    
    If Leo (Sun-ruled), the ruling card IS the birth card.
    Otherwise, find the planet's card in the birth card's Life Spread.
    """
    ruling_planet = ZODIAC_RULERS_CLASSICAL[zodiac]
    
    if ruling_planet == Planet.SUN:
        return birth_card
    
    return get_planetary_card(birth_card, ruling_planet, LIFE_SPREAD)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: KARMA CARDS
# ═══════════════════════════════════════════════════════════════════════════════

"""
Karma Cards represent karmic debts and gifts from past lives.

First Karma Card (Challenging): 
- The card whose position in the Natural Spread your card occupies in the Life Spread
- You "owe" this energy - must work to master it

Second Karma Card (Supporting):
- The card that occupies your Natural Spread position in the Life Spread
- This energy "owes" you - comes naturally

Fixed Cards (no movement, no karma cards):
- King of Spades (K♠)
- Jack of Hearts (J♥)  
- Eight of Clubs (8♣)

Semi-Fixed Cards (swap with each other):
- Ace of Clubs (A♣) ↔ Two of Hearts (2♥)
- Seven of Diamonds (7♦) ↔ Nine of Hearts (9♥)
"""

FIXED_CARDS = [
    Card(rank=13, suit=Suit.SPADES),  # K♠
    Card(rank=11, suit=Suit.HEARTS),  # J♥
    Card(rank=8, suit=Suit.CLUBS),    # 8♣
]

SEMI_FIXED_PAIRS = [
    (Card(rank=1, suit=Suit.CLUBS), Card(rank=2, suit=Suit.HEARTS)),    # A♣ ↔ 2♥
    (Card(rank=7, suit=Suit.DIAMONDS), Card(rank=9, suit=Suit.HEARTS)), # 7♦ ↔ 9♥
]


def is_fixed_card(card: Card) -> bool:
    """Check if a card is one of the three fixed cards."""
    return any(card.rank == fc.rank and card.suit == fc.suit for fc in FIXED_CARDS)


def is_semi_fixed_card(card: Card) -> Tuple[bool, Optional[Card]]:
    """Check if card is semi-fixed and return its twin if so."""
    for pair in SEMI_FIXED_PAIRS:
        if card.rank == pair[0].rank and card.suit == pair[0].suit:
            return (True, pair[1])
        if card.rank == pair[1].rank and card.suit == pair[1].suit:
            return (True, pair[0])
    return (False, None)


def calculate_karma_cards(birth_card: Card) -> Tuple[Optional[Card], Optional[Card]]:
    """
    Calculate the First and Second Karma Cards.
    
    Returns:
        (first_karma_card, second_karma_card)
        
    Fixed cards return (None, None)
    """
    if is_fixed_card(birth_card):
        return (None, None)
    
    # Find birth card's position in Life Spread
    life_row, life_col = find_card_position_in_spread(birth_card, LIFE_SPREAD)
    
    # Find birth card's position in Natural Spread
    natural_row, natural_col = find_card_position_in_spread(birth_card, NATURAL_SPREAD)
    
    # First Karma Card: What's at YOUR Life Spread position in the Natural Spread?
    # (The card whose "home" you're sitting in)
    first_karma = NATURAL_SPREAD[life_row][life_col]
    
    # Second Karma Card: What's at YOUR Natural Spread position in the Life Spread?
    # (The card sitting in your "home")
    second_karma = LIFE_SPREAD[natural_row][natural_col]
    
    return (first_karma, second_karma)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: PLANETARY PERIODS (52-Day Cycles)
# ═══════════════════════════════════════════════════════════════════════════════

"""
Each year is divided into 7 planetary periods of ~52 days each:
1. Mercury Period: Birthday + 52 days
2. Venus Period: +52 days
3. Mars Period: +52 days
4. Jupiter Period: +52 days
5. Saturn Period: +52 days
6. Uranus Period: +52 days
7. Neptune Period: Remaining days until next birthday

52 × 7 = 364 days (one day short of a year, handled by Neptune period)
"""

@dataclass
class PlanetaryPeriod:
    """Represents a 52-day planetary period within a yearly cycle."""
    planet: Planet
    start_date: date
    end_date: date
    direct_card: Card        # Card governing this period
    vertical_card: Optional[Card]  # Vertical influence card
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


def calculate_planetary_periods(
    birth_date: date,
    year: int,
    birth_card: Card,
    spread: List[List[Card]] = None
) -> List[PlanetaryPeriod]:
    """
    Calculate the 7 planetary periods for a given year.
    
    Args:
        birth_date: Person's date of birth
        year: The year to calculate periods for
        birth_card: The person's birth card
        spread: The yearly spread to use (defaults to Life Spread)
    
    Returns:
        List of 7 PlanetaryPeriod objects
    """
    if spread is None:
        spread = LIFE_SPREAD
    
    # Calculate birthday in the target year
    try:
        birthday = date(year, birth_date.month, birth_date.day)
    except ValueError:
        # Handle Feb 29 for non-leap years
        birthday = date(year, birth_date.month, birth_date.day - 1)
    
    # Next birthday
    next_year = year + 1
    try:
        next_birthday = date(next_year, birth_date.month, birth_date.day)
    except ValueError:
        next_birthday = date(next_year, birth_date.month, birth_date.day - 1)
    
    # Calculate total days in this birthday year
    total_days = (next_birthday - birthday).days
    
    # Standard period length (52 days for first 6, remainder for Neptune)
    period_length = 52
    
    periods = []
    planet_order = [
        Planet.MERCURY, Planet.VENUS, Planet.MARS,
        Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE
    ]
    
    current_date = birthday
    
    for i, planet in enumerate(planet_order):
        if i < 6:  # First 6 planets: 52 days each
            end_date = current_date + timedelta(days=period_length - 1)
        else:  # Neptune: remaining days
            end_date = next_birthday - timedelta(days=1)
        
        # Get the direct card for this planet from the spread
        direct_card = get_planetary_card(birth_card, planet, spread)
        
        # Vertical card would come from a different row (advanced feature)
        vertical_card = None  # Simplified for now
        
        periods.append(PlanetaryPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            direct_card=direct_card,
            vertical_card=vertical_card
        ))
        
        current_date = end_date + timedelta(days=1)
    
    return periods


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: RELATIONSHIP CONNECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

"""
Relationship connections are determined by the positions of two people's cards
relative to each other in the Life and Spiritual spreads.

Connection Types:
- Moon: Supporting, nurturing (card to the right)
- Venus: Love, attraction
- Mars: Passion, conflict
- Jupiter: Blessing, expansion
- Saturn: Lessons, karma, challenges
- Uranus: Unexpected, freedom
- Neptune: Illusion, dreams
- Vertical: Different row same column (deep/challenging)
- Diagonal: Different row and column relationships
"""

@dataclass
class RelationshipConnection:
    """Represents a connection between two people's cards."""
    connection_type: str
    planet: Optional[Planet]
    from_card: Card
    to_card: Card
    spread_type: str  # "Life" or "Spiritual"
    is_mutual: bool
    description: str


def analyze_connections(card_a: Card, card_b: Card) -> List[RelationshipConnection]:
    """
    Analyze the relationship connections between two birth cards.
    
    Checks both Life and Spiritual spreads for planetary connections.
    """
    connections = []
    
    # Check Life Spread connections
    connections.extend(_check_planetary_connections(card_a, card_b, LIFE_SPREAD, "Life"))
    
    # Check Spiritual Spread connections
    connections.extend(_check_planetary_connections(card_a, card_b, NATURAL_SPREAD, "Spiritual"))
    
    return connections


def _check_planetary_connections(
    card_a: Card, 
    card_b: Card, 
    spread: List[List[Card]],
    spread_name: str
) -> List[RelationshipConnection]:
    """Check if card_b appears in card_a's planetary positions."""
    connections = []
    
    planets = [
        Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
        Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE
    ]
    
    for planet in planets:
        planetary_card = get_planetary_card(card_a, planet, spread)
        if planetary_card and planetary_card.rank == card_b.rank and planetary_card.suit == card_b.suit:
            # Check if mutual
            reverse_card = get_planetary_card(card_b, planet, spread)
            is_mutual = (reverse_card and 
                        reverse_card.rank == card_a.rank and 
                        reverse_card.suit == card_a.suit)
            
            connections.append(RelationshipConnection(
                connection_type=f"{planet.value} Connection",
                planet=planet,
                from_card=card_a,
                to_card=card_b,
                spread_type=spread_name,
                is_mutual=is_mutual,
                description=f"{card_b} is {card_a}'s {planet.value} card in the {spread_name} Spread"
            ))
    
    return connections


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: MAIN OUTPUT SCHEMA - CardologyBlueprint
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CardologyBlueprint:
    """
    Complete Cardology blueprint for a person.
    
    This is the main output schema containing all calculated data.
    """
    # Core Identity
    birth_date: date
    birth_card: Card
    planetary_ruling_card: Card
    zodiac_sign: ZodiacSign
    
    # Karma
    first_karma_card: Optional[Card]
    second_karma_card: Optional[Card]
    is_fixed_card: bool
    is_semi_fixed: bool
    semi_fixed_twin: Optional[Card]
    
    # Life Spread Position
    life_spread_row: int  # 0=Crown, 1-7=Planetary rows
    life_spread_col: int  # 1-7 planetary columns
    life_row_planet: Optional[Planet]
    life_col_planet: Optional[Planet]
    
    # Spiritual Spread Position
    spirit_spread_row: int
    spirit_spread_col: int
    spirit_row_planet: Optional[Planet]
    spirit_col_planet: Optional[Planet]
    
    # Full 13-Card Life Path Spread
    life_path_spread: Dict[str, Card]
    
    # Yearly Timeline (populated when requested)
    planetary_periods: List[PlanetaryPeriod] = field(default_factory=list)
    
    def get_planetary_period_for_date(self, target_date: date) -> Optional[PlanetaryPeriod]:
        """Find which planetary period a specific date falls within."""
        for period in self.planetary_periods:
            if period.start_date <= target_date <= period.end_date:
                return period
        return None


def generate_blueprint(
    birth_date: date,
    include_year: Optional[int] = None
) -> CardologyBlueprint:
    """
    Generate a complete CardologyBlueprint for a person.
    
    Args:
        birth_date: Date of birth
        include_year: If provided, calculates planetary periods for that year
    
    Returns:
        Complete CardologyBlueprint with all calculated fields
    """
    # Core calculations
    birth_card = calculate_birth_card_from_date(birth_date)
    zodiac = get_zodiac_sign(birth_date.month, birth_date.day)
    ruling_card = calculate_ruling_card(birth_card, zodiac)
    
    # Karma cards
    first_karma, second_karma = calculate_karma_cards(birth_card)
    fixed = is_fixed_card(birth_card)
    semi_fixed, twin = is_semi_fixed_card(birth_card)
    
    # Spread positions
    life_row, life_col = find_card_position_in_spread(birth_card, LIFE_SPREAD)
    spirit_row, spirit_col = find_card_position_in_spread(birth_card, NATURAL_SPREAD)
    
    # Map row/col to planets
    row_planets = [None, Planet.MERCURY, Planet.VENUS, Planet.MARS, 
                   Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE]
    col_planets = [None, Planet.NEPTUNE, Planet.URANUS, Planet.SATURN,
                   Planet.JUPITER, Planet.MARS, Planet.VENUS, Planet.MERCURY]
    
    life_row_planet = row_planets[life_row] if life_row < len(row_planets) else None
    life_col_planet = col_planets[life_col] if life_col < len(col_planets) else None
    spirit_row_planet = row_planets[spirit_row] if spirit_row < len(row_planets) else None
    spirit_col_planet = col_planets[spirit_col] if spirit_col < len(col_planets) else None
    
    # Build life path spread (13 cards)
    life_path = {
        "Sun (Birth)": birth_card,
        "Moon": get_planetary_card(birth_card, Planet.MOON),
        "Mercury": get_planetary_card(birth_card, Planet.MERCURY),
        "Venus": get_planetary_card(birth_card, Planet.VENUS),
        "Mars": get_planetary_card(birth_card, Planet.MARS),
        "Jupiter": get_planetary_card(birth_card, Planet.JUPITER),
        "Saturn": get_planetary_card(birth_card, Planet.SATURN),
        "Uranus": get_planetary_card(birth_card, Planet.URANUS),
        "Neptune": get_planetary_card(birth_card, Planet.NEPTUNE),
        "Pluto": get_planetary_card(birth_card, Planet.PLUTO),
    }
    
    # Calculate planetary periods if year provided
    periods = []
    if include_year:
        periods = calculate_planetary_periods(birth_date, include_year, birth_card)
    
    return CardologyBlueprint(
        birth_date=birth_date,
        birth_card=birth_card,
        planetary_ruling_card=ruling_card,
        zodiac_sign=zodiac,
        first_karma_card=first_karma,
        second_karma_card=second_karma,
        is_fixed_card=fixed,
        is_semi_fixed=semi_fixed,
        semi_fixed_twin=twin,
        life_spread_row=life_row,
        life_spread_col=life_col,
        life_row_planet=life_row_planet,
        life_col_planet=life_col_planet,
        spirit_spread_row=spirit_row,
        spirit_spread_col=spirit_col,
        spirit_row_planet=spirit_row_planet,
        spirit_col_planet=spirit_col_planet,
        life_path_spread=life_path,
        planetary_periods=periods
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: COMPLETE BIRTHDAY-TO-CARD LOOKUP TABLE
# ═══════════════════════════════════════════════════════════════════════════════

"""
Pre-computed lookup table for verification and quick reference.
Generated using the Magi Formula: 55 - ((month * 2) + day) = solar_value
"""

def generate_birthday_table() -> Dict[Tuple[int, int], Card]:
    """
    Generate a complete lookup table of (month, day) -> Card.
    
    Returns:
        Dictionary mapping (month, day) tuples to their Birth Cards
    """
    table = {}
    
    # Days in each month (non-leap year - Feb 29 uses Feb 28's card)
    days_in_month = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    for month in range(1, 13):
        for day in range(1, days_in_month[month] + 1):
            table[(month, day)] = calculate_birth_card(month, day)
    
    # Feb 29 (leap year) - typically uses the same card as Feb 28
    table[(2, 29)] = table[(2, 28)]
    
    return table


BIRTHDAY_TABLE = generate_birthday_table()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12: TEST SUITE - Ground Truth Verification
# ═══════════════════════════════════════════════════════════════════════════════

"""
Test cases derived from verified sources to ensure implementation accuracy.
These can be used for validation and regression testing.
"""

TEST_CASES = [
    # Format: (month, day, expected_card_repr, expected_zodiac, notes)
    
    # ══════════════════════════════════════════════════════════════════════════
    # CELEBRITY VERIFICATIONS (From metasymbology.com and cardology sources)
    # ══════════════════════════════════════════════════════════════════════════
    (12, 18, "K♥", ZodiacSign.SAGITTARIUS, "Brad Pitt - King of Hearts (Verified)"),
    (9, 11, "K♣", ZodiacSign.VIRGO, "September 11 - King of Clubs (Master of Knowledge)"),
    (7, 4, "J♦", ZodiacSign.CANCER, "July 4th Independence Day - Jack of Diamonds"),
    (11, 7, "K♣", ZodiacSign.SCORPIO, "November 7 - King of Clubs"),
    (7, 18, "10♣", ZodiacSign.CANCER, "July 18 - Ten of Clubs"),
    (12, 31, "Joker", ZodiacSign.CAPRICORN, "December 31 - The Joker (Solar Value 0)"),
    
    # ══════════════════════════════════════════════════════════════════════════
    # SOLAR VALUE EDGE CASES (Verified by formula: 55 - ((month*2) + day))
    # ══════════════════════════════════════════════════════════════════════════
    (1, 1, "K♠", ZodiacSign.CAPRICORN, "January 1 - King of Spades (SV=52, highest)"),
    (12, 30, "A♥", ZodiacSign.CAPRICORN, "December 30 - Ace of Hearts (SV=1, lowest non-Joker)"),
    (1, 13, "A♠", ZodiacSign.CAPRICORN, "January 13 - Ace of Spades (SV=40)"),
    (7, 1, "A♠", ZodiacSign.CANCER, "July 1 - Ace of Spades (SV=40)"),
    
    # ══════════════════════════════════════════════════════════════════════════
    # FIXED CARDS (These cards never move in quadration)
    # ══════════════════════════════════════════════════════════════════════════
    (1, 7, "7♠", ZodiacSign.CAPRICORN, "January 7 - Seven of Spades"),
    (7, 30, "J♥", ZodiacSign.LEO, "July 30 - Jack of Hearts (Fixed Card)"),
    (8, 8, "5♦", ZodiacSign.LEO, "August 8 - Five of Diamonds (SV=31)"),
    
    # ══════════════════════════════════════════════════════════════════════════
    # SUIT BOUNDARY VERIFICATIONS
    # ══════════════════════════════════════════════════════════════════════════
    (6, 24, "6♣", ZodiacSign.CANCER, "June 24 - Six of Clubs (SV=19)"),
    (9, 30, "7♥", ZodiacSign.LIBRA, "September 30 - Seven of Hearts"),
    (10, 28, "7♥", ZodiacSign.SCORPIO, "October 28 - Seven of Hearts"),
    (3, 30, "6♣", ZodiacSign.ARIES, "March 30 - Six of Clubs (SV=19)"),
    (10, 22, "K♥", ZodiacSign.LIBRA, "October 22 - King of Hearts (SV=13, Hearts max)"),
    (5, 19, "K♣", ZodiacSign.TAURUS, "May 19 - King of Clubs (SV=26, Clubs max)"),
    (1, 14, "K♦", ZodiacSign.CAPRICORN, "January 14 - King of Diamonds (SV=39, Diamonds max)"),
    (4, 20, "A♦", ZodiacSign.TAURUS, "April 20 - Ace of Diamonds (SV=27, Diamonds start)"),
    (6, 17, "K♣", ZodiacSign.GEMINI, "June 17 - King of Clubs (SV=26)"),
    
    # ══════════════════════════════════════════════════════════════════════════
    # SEMI-FIXED CARD DATES
    # ══════════════════════════════════════════════════════════════════════════
    (3, 28, "8♣", ZodiacSign.ARIES, "March 28 - Eight of Clubs (Fixed)"),
    (4, 26, "8♣", ZodiacSign.TAURUS, "April 26 - Eight of Clubs (Fixed)"),
]


def run_test_suite() -> List[Dict]:
    """
    Run all test cases and return results.
    
    Returns:
        List of test results with pass/fail status
    """
    results = []
    
    for month, day, expected, expected_zodiac, notes in TEST_CASES:
        try:
            card = calculate_birth_card(month, day)
            zodiac = get_zodiac_sign(month, day)
            
            actual = repr(card) if card != JOKER else "Joker"
            passed = actual == expected and zodiac == expected_zodiac
            
            results.append({
                "date": f"{month}/{day}",
                "expected_card": expected,
                "actual_card": actual,
                "expected_zodiac": expected_zodiac.value,
                "actual_zodiac": zodiac.value,
                "passed": passed,
                "notes": notes
            })
        except Exception as e:
            results.append({
                "date": f"{month}/{day}",
                "expected_card": expected,
                "actual_card": f"ERROR: {e}",
                "expected_zodiac": expected_zodiac.value,
                "actual_zodiac": "ERROR",
                "passed": False,
                "notes": notes
            })
    
    return results


def print_test_results():
    """Pretty print test results."""
    results = run_test_suite()
    
    print("=" * 80)
    print("CHRONOS-MAGI TEST SUITE RESULTS")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for r in results:
        status = "✓ PASS" if r["passed"] else "✗ FAIL"
        print(f"{status} | {r['date']:>5} | Card: {r['actual_card']:>6} (expected {r['expected_card']:>6}) | "
              f"Zodiac: {r['actual_zodiac']:>12} | {r['notes']}")
    
    print("=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13: UTILITY FUNCTIONS FOR GUTTERS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_period_info(birth_date: date, current_date: date = None) -> Dict:
    """
    Get information about the current planetary period for Quest Dashboard integration.
    
    Returns a dict suitable for GUTTERS system integration:
    {
        "period": "Mars",
        "card": "7♠",
        "start": "2026-01-15",
        "end": "2026-03-07",
        "days_remaining": 42,
        "theme": "Physical energy, action, potential conflict",
        "guidance": "Channel excess Mars force through physical activity"
    }
    """
    if current_date is None:
        current_date = date.today()
    
    # Determine which birthday year we're in
    year = current_date.year
    try:
        birthday_this_year = date(year, birth_date.month, birth_date.day)
    except ValueError:
        birthday_this_year = date(year, birth_date.month, birth_date.day - 1)
    
    if current_date < birthday_this_year:
        year -= 1
    
    birth_card = calculate_birth_card_from_date(birth_date)
    periods = calculate_planetary_periods(birth_date, year, birth_card)
    
    # Find current period
    for period in periods:
        if period.start_date <= current_date <= period.end_date:
            days_remaining = (period.end_date - current_date).days
            
            # Period themes for GUTTERS integration
            themes = {
                Planet.MERCURY: "Communication, quick changes, mental activity",
                Planet.VENUS: "Love, home, beauty, relationships, creativity",
                Planet.MARS: "Physical energy, action, passion, potential conflict",
                Planet.JUPITER: "Expansion, blessings, fortune, opportunities",
                Planet.SATURN: "Karma, lessons, challenges, career focus",
                Planet.URANUS: "Freedom, spirituality, unexpected changes",
                Planet.NEPTUNE: "Dreams, intuition, hopes, creative inspiration",
            }
            
            guidances = {
                Planet.MERCURY: "Focus on learning, communication projects, short trips",
                Planet.VENUS: "Nurture relationships, beautify environment, creative work",
                Planet.MARS: "Channel excess energy through physical activity, be mindful of conflicts",
                Planet.JUPITER: "Expand horizons, take calculated risks, share abundance",
                Planet.SATURN: "Face responsibilities, work diligently, address karmic lessons",
                Planet.URANUS: "Embrace change, express individuality, spiritual development",
                Planet.NEPTUNE: "Trust intuition, creative visualization, careful with illusions",
            }
            
            return {
                "period": period.planet.value,
                "card": repr(period.direct_card) if period.direct_card else "Unknown",
                "card_name": str(period.direct_card) if period.direct_card else "Unknown",
                "start": period.start_date.isoformat(),
                "end": period.end_date.isoformat(),
                "days_remaining": days_remaining,
                "duration_days": period.duration_days,
                "theme": themes.get(period.planet, ""),
                "guidance": guidances.get(period.planet, ""),
            }
    
    return {"error": "No current period found"}


def generate_yearly_timeline(birth_date: date, year: int) -> List[Dict]:
    """
    Generate a complete yearly timeline for export/integration.
    
    Returns a list of period dictionaries suitable for JSON export.
    """
    birth_card = calculate_birth_card_from_date(birth_date)
    periods = calculate_planetary_periods(birth_date, year, birth_card)
    
    timeline = []
    for period in periods:
        timeline.append({
            "period_name": period.planet.value,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "duration_days": period.duration_days,
            "direct_card": repr(period.direct_card) if period.direct_card else None,
            "direct_card_name": str(period.direct_card) if period.direct_card else None,
        })
    
    return timeline


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14: ARCHITECTURAL THESIS - CARDOLOGY AS "THE SCRIPT"
# ═══════════════════════════════════════════════════════════════════════════════

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SYSTEMS SYNTHESIS THESIS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

CARDOLOGY (TIME) - "The Script"
═══════════════════════════════
Cardology provides a deterministic temporal framework that maps consciousness
to the 52-card calendar system. Key architectural principles:

1. DETERMINISTIC CYCLES
   - Birth Card is immutable - your soul's signature
   - 90 yearly quadrations cycle predictably
   - 52-day planetary periods divide each year
   - Every moment has a precise card/planet position

2. FRACTAL TIME
   - 52 cards = 52 weeks
   - 7 planets = 7 periods per year
   - 90 spreads = 90-year life cycle
   - Patterns repeat at multiple scales

3. KARMIC ARCHITECTURE
   - First Karma Card: What you must master (debt)
   - Second Karma Card: What comes naturally (gift)
   - Fixed cards: Already transcended karma
   - Semi-fixed: Dual nature, oscillating lessons

HOW THIS ENABLES "THE SCRIPT AWARENESS"
═══════════════════════════════════════
When integrated into GUTTERS:

1. PREDICTIVE POSITIONING
   - Know which planetary energy governs each 52-day period
   - Anticipate challenging Saturn periods for karmic work
   - Leverage Jupiter periods for expansion opportunities

2. QUEST CONTEXTUALIZATION
   Old Quest: "Go to Gym"
   System-Aware Quest: "Mars Period Active (Days 156-208)
                       Physical Conflict Probable
                       Daily Quest: Heavy Lifting to channel Mars Force
                       Warning: Avoid confrontational situations"

3. RELATIONSHIP TIMING
   - Moon connections indicate nurturing support
   - Saturn connections require patience and work
   - Venus connections favor romantic undertakings

4. LONG-RANGE PLANNING
   - 7-year cycles reveal life chapter themes
   - Age-based spreads show yearly focus cards
   - Displacement cards indicate giving/receiving

INTEGRATION PATTERN
═══════════════════
┌─────────────────────────────────────────────────────────────────────┐
│                         GUTTERS PLATFORM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   User Profile                    Cardology Kernel                  │
│   ┌──────────────┐               ┌──────────────────┐              │
│   │ birth_date   │───────────────│ generate_blueprint│              │
│   │ preferences  │               │                   │              │
│   └──────────────┘               │ CardologyBlueprint│              │
│                                  │ - birth_card      │              │
│                                  │ - ruling_card     │              │
│                                  │ - karma_cards     │              │
│                                  │ - periods[]       │              │
│                                  └────────┬─────────┘              │
│                                           │                         │
│                                           ▼                         │
│                              ┌────────────────────────┐            │
│                              │   Quest Engine          │            │
│                              │   - Contextualizes tasks│            │
│                              │   - Adds timing wisdom  │            │
│                              │   - Warns of conflicts  │            │
│                              │   - Suggests alignments │            │
│                              └────────────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

The kernel is STATELESS - all computations derive purely from the birth date
and target date. No external data sources required. Pure mathematics.

This is the ancient wisdom encoded: "As above, so below" - the 52-card deck
mirrors the 52 weeks, the 7 planets mirror the 7 periods, and every moment
of your life has its corresponding card waiting to reveal its lesson.

"The System knows the script before you read the lines."
"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CHRONOS-MAGI CARDOLOGY KERNEL - DEMONSTRATION")
    print("="*80 + "\n")
    
    # Run test suite first
    print_test_results()
    
    # Demo: Generate blueprint for Brad Pitt (Dec 18, 1963)
    print("\n" + "="*80)
    print("DEMO: Brad Pitt (December 18, 1963)")
    print("="*80 + "\n")
    
    brad_dob = date(1963, 12, 18)
    blueprint = generate_blueprint(brad_dob, include_year=2026)
    
    print(f"Birth Card: {blueprint.birth_card}")
    print(f"Zodiac Sign: {blueprint.zodiac_sign.value}")
    print(f"Planetary Ruling Card: {blueprint.planetary_ruling_card}")
    print(f"First Karma Card: {blueprint.first_karma_card}")
    print(f"Second Karma Card: {blueprint.second_karma_card}")
    print(f"Is Fixed Card: {blueprint.is_fixed_card}")
    
    print(f"\nLife Spread Position: Row {blueprint.life_spread_row}, Col {blueprint.life_spread_col}")
    if blueprint.life_row_planet:
        print(f"  Row Planet: {blueprint.life_row_planet.value}")
    if blueprint.life_col_planet:
        print(f"  Column Planet: {blueprint.life_col_planet.value}")
    
    print("\nLife Path Spread (13 Cards):")
    for position, card in blueprint.life_path_spread.items():
        print(f"  {position:20s}: {card}")
    
    print("\n2026 Planetary Periods:")
    for period in blueprint.planetary_periods:
        print(f"  {period.planet.value:10s}: {period.start_date} - {period.end_date} | "
              f"Card: {period.direct_card}")
    
    # Current period info
    print("\n" + "="*80)
    print("GUTTERS INTEGRATION: Current Period Info")
    print("="*80 + "\n")
    
    current_info = get_current_period_info(brad_dob, date(2026, 2, 4))
    for key, value in current_info.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("KERNEL INITIALIZATION COMPLETE")
    print("="*80 + "\n")
