"""
GUTTERS Numerology Calculator - BRAIN

Complete Pythagorean numerology calculation system.
Calculates Life Path, Expression, Soul Urge, Personality, Birthday,
Master Numbers, and Karmic Debt.

NO event system knowledge - pure inputs and outputs.
"""

from datetime import date
from typing import Any

from src.app.modules.calculation.registry import CalculationModuleRegistry

from ..schemas import NumerologyChart


@CalculationModuleRegistry.register(
    name="numerology",
    display_name="Numerology",
    description="Computing life path and core numbers",
    weight=1,
    requires_birth_time=False,
    order=3,
    version="1.0.0",
)
class NumerologyCalculator:
    """
    Complete Pythagorean numerology calculator.

    Calculates:
    - Life Path (birth date) - Core life purpose
    - Expression (full name) - Natural talents
    - Soul Urge (vowels in name) - Inner desires
    - Personality (consonants in name) - Outer persona
    - Birthday number - Natural gifts
    - Master numbers (11, 22, 33)
    - Karmic debt (13, 14, 16, 19)
    """

    # Pythagorean letter values (1-9 cycle)
    LETTER_VALUES = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }

    VOWELS = set("AEIOUY")
    MASTER_NUMBERS = {11, 22, 33}
    KARMIC_DEBT_NUMBERS = {13, 14, 16, 19}

    async def calculate(self, name: str, birth_date: date, **kwargs: Any) -> dict[str, Any]:
        """
        Registry-compatible entry point.
        """
        chart = self.calculate_chart(name=name, birth_date=birth_date)
        return chart.model_dump()

    def calculate_chart(
        self,
        name: str,
        birth_date: date | str,
    ) -> NumerologyChart:
        """
        Calculate complete numerology chart.

        Args:
            name: Full birth name for Expression/Soul Urge/Personality
            birth_date: Birth date for Life Path and Birthday

        Returns:
            NumerologyChart with all core numbers calculated
        """
        # Parse date if string
        if isinstance(birth_date, str):
            from datetime import datetime as dt

            birth_date = dt.strptime(birth_date, "%Y-%m-%d").date()

        # Life Path from birth date
        life_path, is_master_lp = self.calculate_life_path(birth_date)

        # Expression, Soul Urge, Personality from name
        expression, is_master_exp = self.calculate_expression(name)
        soul_urge, is_master_su = self.calculate_soul_urge(name)
        personality, is_master_pers = self.calculate_personality(name)

        # Birthday number (just the day, reduced if needed)
        birthday = self._reduce_preserve_master(birth_date.day)

        # Detect karmic debt and master numbers
        karmic_debt = self._detect_karmic_debt(birth_date, name)
        master_nums = []
        if is_master_lp:
            master_nums.append(life_path)
        if is_master_exp:
            master_nums.append(expression)
        if is_master_su:
            master_nums.append(soul_urge)

        return NumerologyChart(
            life_path=life_path,
            expression=expression,
            soul_urge=soul_urge,
            personality=personality,
            birthday=birthday,
            is_master_life_path=is_master_lp,
            is_master_expression=is_master_exp,
            is_master_soul_urge=is_master_su,
            karmic_debt_numbers=karmic_debt,
            master_numbers=list(set(master_nums)),
            accuracy="full",
        )

    def calculate_life_path(self, birth_date: date) -> tuple[int, bool]:
        """
        Calculate Life Path number from birth date.

        Method: Reduce each component (year, month, day) to single digit,
        then add and reduce again. Preserve master numbers (11, 22, 33).

        Example: 1990-05-15
        1. Reduce year: 1+9+9+0 = 19 → 1+9 = 10 → 1+0 = 1
        2. Month: 5 (already single)
        3. Day: 1+5 = 6
        4. Total: 1+5+6 = 12 → 1+2 = 3

        Returns:
            (number, is_master) tuple
        """
        # Reduce each component separately
        year_sum = self._reduce_preserve_master(sum(int(d) for d in str(birth_date.year)))
        month_sum = self._reduce_preserve_master(birth_date.month)
        day_sum = self._reduce_preserve_master(birth_date.day)

        # Add all components
        total = year_sum + month_sum + day_sum

        # Final reduction
        result = self._reduce_preserve_master(total)
        is_master = result in self.MASTER_NUMBERS

        return result, is_master

    def calculate_expression(self, full_name: str) -> tuple[int, bool]:
        """
        Calculate Expression (Destiny) number from full birth name.

        Sums all letters (vowels + consonants) in the name.
        Represents natural talents, abilities, and how you express yourself.

        Returns:
            (number, is_master) tuple
        """
        total = self._sum_letters(full_name)
        result = self._reduce_preserve_master(total)
        is_master = result in self.MASTER_NUMBERS
        return result, is_master

    def calculate_soul_urge(self, full_name: str) -> tuple[int, bool]:
        """
        Calculate Soul Urge (Heart's Desire) from vowels in name.

        Represents inner motivations, desires, and what truly fulfills you.

        Note: Y is counted as a vowel when it sounds like a vowel
        (simplified: we always include Y as vowel)

        Returns:
            (number, is_master) tuple
        """
        vowels_only = "".join(c for c in full_name.upper() if c in self.VOWELS)
        total = self._sum_letters(vowels_only)
        result = self._reduce_preserve_master(total)
        is_master = result in self.MASTER_NUMBERS
        return result, is_master

    def calculate_personality(self, full_name: str) -> tuple[int, bool]:
        """
        Calculate Personality number from consonants in name.

        Represents your outer persona, how others perceive you,
        and first impressions you make.

        Returns:
            (number, is_master) tuple
        """
        consonants_only = "".join(c for c in full_name.upper() if c.isalpha() and c not in self.VOWELS)
        total = self._sum_letters(consonants_only)
        result = self._reduce_preserve_master(total)
        is_master = result in self.MASTER_NUMBERS
        return result, is_master

    def _sum_letters(self, text: str) -> int:
        """Sum Pythagorean letter values for given text"""
        return sum(self.LETTER_VALUES.get(c, 0) for c in text.upper() if c.isalpha())

    def _reduce_preserve_master(self, num: int) -> int:
        """
        Reduce number to single digit, preserving master numbers.

        Master numbers (11, 22, 33) are NOT reduced further.
        All other multi-digit numbers are reduced to single digit.

        Examples:
            19 → 1+9 = 10 → 1+0 = 1
            11 → 11 (master, preserved)
            22 → 22 (master, preserved)
            33 → 33 (master, preserved)
        """
        if num in self.MASTER_NUMBERS:
            return num

        while num > 9:
            num = sum(int(d) for d in str(num))
            if num in self.MASTER_NUMBERS:
                return num

        return num

    def _detect_karmic_debt(self, birth_date: date, full_name: str) -> list[int]:
        """
        Detect karmic debt numbers (13, 14, 16, 19).

        Karmic debt appears when these numbers show up during
        intermediate calculations before final reduction.

        13 - Laziness/shortcuts in past life
        14 - Abuse of freedom
        16 - Ego/pride issues
        19 - Abuse of power

        Returns:
            List of karmic debt numbers found
        """
        karmic = []

        # Check year digits sum
        year_sum = sum(int(d) for d in str(birth_date.year))
        if year_sum in self.KARMIC_DEBT_NUMBERS:
            karmic.append(year_sum)

        # Check birth day
        if birth_date.day in self.KARMIC_DEBT_NUMBERS:
            karmic.append(birth_date.day)

        # Check name total before reduction
        name_total = self._sum_letters(full_name)
        name_intermediates = self._get_reduction_intermediates(name_total)
        karmic.extend([n for n in name_intermediates if n in self.KARMIC_DEBT_NUMBERS])

        return sorted(set(karmic))  # Dedupe and sort

    def _get_reduction_intermediates(self, num: int) -> list[int]:
        """
        Get all intermediate sums during reduction process.

        Used to detect karmic debt numbers that appear
        during calculation but get reduced away.
        """
        intermediates = [num]

        while num > 9:
            if num in self.MASTER_NUMBERS:
                break
            num = sum(int(d) for d in str(num))
            intermediates.append(num)

        return intermediates
