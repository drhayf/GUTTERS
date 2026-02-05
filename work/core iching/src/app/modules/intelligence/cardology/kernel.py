"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CARDOLOGY KERNEL INTERFACE                                ║
║                                                                              ║
║   Interface stub for integration with the Chronos-Magi Cardology Kernel      ║
║                                                                              ║
║   This module defines the expected interface that the Cardology kernel       ║
║   must implement to participate in the Council of Systems.                   ║
║                                                                              ║
║   Integration: Copy your chronos_magi_kernel.py here and ensure it          ║
║   exports these classes/functions, or adapt the CardologyAdapter in         ║
║   synthesis/harmonic.py to match your actual implementation.                 ║
║                                                                              ║
║   Author: GUTTERS Project / Magi OS                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class Suit(Enum):
    """The four suits representing elements and life domains."""
    HEARTS = "♥"      # Water - Emotions, Love, Relationships
    CLUBS = "♣"       # Fire - Knowledge, Communication, Ideas
    DIAMONDS = "♦"    # Earth - Values, Money, Material
    SPADES = "♠"      # Air - Work, Health, Wisdom, Spirituality


class Planet(Enum):
    """The seven classical planets used in Cardology planetary periods."""
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"


@dataclass
class Card:
    """A playing card with suit and rank."""
    rank: str        # A, 2-10, J, Q, K
    suit: Suit
    
    def __repr__(self) -> str:
        return f"{self.rank}{self.suit.value}"
    
    @property
    def symbol(self) -> str:
        return f"{self.rank}{self.suit.value}"


@dataclass
class PlanetaryPeriod:
    """A 52-day planetary period."""
    planet: Planet
    start_date: date
    end_date: date
    direct_card: Card
    vertical_card: Optional[Card] = None


@dataclass 
class CardologyBlueprint:
    """
    Complete Cardology blueprint for a person.
    
    This is the expected output structure from your Chronos-Magi kernel.
    """
    birth_date: date
    birth_card: Card
    planetary_ruling_card: Card
    first_karma_card: Optional[Card]
    second_karma_card: Optional[Card]
    is_fixed_card: bool
    planetary_periods: List[PlanetaryPeriod]
    
    # Additional fields from your implementation
    zodiac_sign: Optional[str] = None
    life_spread_row: Optional[int] = None
    life_spread_col: Optional[int] = None
    life_path_spread: Optional[Dict[str, Card]] = None


class CardologyKernel:
    """
    Cardology calculation kernel interface.
    
    This class should be replaced with or wrap your actual
    Chronos-Magi implementation.
    
    Required methods for Council of Systems integration:
    - generate_blueprint(dob: date) -> CardologyBlueprint
    - get_current_period_info(dob: date, current: date) -> Dict
    - calculate_birth_card(dob: date) -> Card
    """
    
    def calculate_birth_card(self, dob: date) -> Card:
        """
        Calculate the birth card for a given date.
        
        This should use the Magi formula from your implementation.
        """
        raise NotImplementedError(
            "Implement this method using your Chronos-Magi kernel"
        )
    
    def generate_blueprint(
        self, 
        dob: date, 
        include_year: Optional[int] = None
    ) -> CardologyBlueprint:
        """
        Generate complete Cardology blueprint for a person.
        
        Args:
            dob: Date of birth
            include_year: Optional year to calculate periods for
            
        Returns:
            CardologyBlueprint with all Cardology data
        """
        raise NotImplementedError(
            "Implement this method using your Chronos-Magi kernel"
        )
    
    def get_current_period_info(
        self, 
        dob: date, 
        current_date: date
    ) -> Dict[str, Any]:
        """
        Get information about the current planetary period.
        
        Args:
            dob: Date of birth
            current_date: Date to calculate for
            
        Returns:
            Dict with period, card, days_remaining, theme, guidance
        """
        raise NotImplementedError(
            "Implement this method using your Chronos-Magi kernel"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
"""
To integrate your existing Chronos-Magi kernel:

1. OPTION A - Direct replacement:
   Copy your chronos_magi_kernel.py contents here, ensuring the 
   CardologyKernel class implements the required methods above.

2. OPTION B - Adapter pattern:
   Keep your kernel separate and modify the CardologyAdapter in
   synthesis/harmonic.py to import and use your implementation:
   
   from your_package import ChronosMagiKernel
   
   class CardologyAdapter:
       def __init__(self, kernel=None):
           self._kernel = kernel or ChronosMagiKernel()
       
       def get_reading(self, dt: datetime) -> SystemReading:
           # Use self._kernel to get actual data
           blueprint = self._kernel.generate_blueprint(dt.date())
           # Convert to SystemReading format
           ...

3. OPTION C - Submodule:
   Place your chronos_magi_kernel.py in this directory and import it:
   
   from .chronos_magi_kernel import CardologyKernel, generate_blueprint
"""
