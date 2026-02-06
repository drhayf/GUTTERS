"""
Integration Tests for Cardology Kernel (Magi OS)

Validates the Chronos-Magi Cardology Logic Kernel using known celebrity
birth cards and formula-verified test cases.

The kernel is a SEALED ENGINE BLOCK - these tests verify correctness
without modifying the kernel itself.
"""

from datetime import date

import pytest

from src.app.modules.intelligence.cardology import (
    JOKER,
    Card,
    CardologyModule,
    Planet,
    Suit,
    ZodiacSign,
    calculate_birth_card,
    calculate_birth_card_from_date,
    generate_blueprint,
)
from src.app.modules.intelligence.cardology.kernel import (
    calculate_karma_cards,
    is_fixed_card,
    is_semi_fixed_card,
    run_test_suite,
)


class TestBirthCardCalculation:
    """Test Birth Card calculation using the Magi Formula."""

    def test_brad_pitt_december_18(self):
        """
        Brad Pitt (December 18, 1963) - King of Hearts

        Formula: 55 - ((12 * 2) + 18) = 55 - 42 = 13
        Solar Value 13 = King of Hearts (Hearts: 1-13)
        """
        birth_date = date(1963, 12, 18)
        card = calculate_birth_card_from_date(birth_date)

        assert card.rank == 13, f"Expected rank 13 (King), got {card.rank}"
        assert card.suit == Suit.HEARTS, f"Expected HEARTS, got {card.suit}"
        assert str(card) == "King of Hearts"
        assert repr(card) == "K♥"

    def test_january_1_king_of_spades(self):
        """
        January 1 - King of Spades (highest solar value: 52)

        Formula: 55 - ((1 * 2) + 1) = 55 - 3 = 52
        Solar Value 52 = King of Spades
        """
        card = calculate_birth_card(1, 1)

        assert card.rank == 13
        assert card.suit == Suit.SPADES
        assert repr(card) == "K♠"

    def test_december_30_ace_of_hearts(self):
        """
        December 30 - Ace of Hearts (lowest non-Joker solar value: 1)

        Formula: 55 - ((12 * 2) + 30) = 55 - 54 = 1
        Solar Value 1 = Ace of Hearts
        """
        card = calculate_birth_card(12, 30)

        assert card.rank == 1
        assert card.suit == Suit.HEARTS
        assert repr(card) == "A♥"

    def test_december_31_joker(self):
        """
        December 31 - The Joker (solar value 0)

        Formula: 55 - ((12 * 2) + 31) = 55 - 55 = 0
        """
        card = calculate_birth_card(12, 31)

        assert card == JOKER
        assert card.rank == 0

    def test_july_4_jack_of_diamonds(self):
        """
        July 4 (US Independence Day) - Jack of Diamonds

        Formula: 55 - ((7 * 2) + 4) = 55 - 18 = 37
        Solar Value 37 = Jack of Diamonds (Diamonds: 27-39)
        """
        card = calculate_birth_card(7, 4)

        assert card.rank == 11  # Jack
        assert card.suit == Suit.DIAMONDS
        assert repr(card) == "J♦"

    def test_suit_boundaries(self):
        """Test cards at suit boundaries."""
        # Hearts end at 13
        card_13 = Card.from_solar_value(13)
        assert card_13.suit == Suit.HEARTS
        assert card_13.rank == 13

        # Clubs start at 14
        card_14 = Card.from_solar_value(14)
        assert card_14.suit == Suit.CLUBS
        assert card_14.rank == 1

        # Clubs end at 26
        card_26 = Card.from_solar_value(26)
        assert card_26.suit == Suit.CLUBS
        assert card_26.rank == 13

        # Diamonds start at 27
        card_27 = Card.from_solar_value(27)
        assert card_27.suit == Suit.DIAMONDS
        assert card_27.rank == 1

        # Diamonds end at 39
        card_39 = Card.from_solar_value(39)
        assert card_39.suit == Suit.DIAMONDS
        assert card_39.rank == 13

        # Spades start at 40
        card_40 = Card.from_solar_value(40)
        assert card_40.suit == Suit.SPADES
        assert card_40.rank == 1


class TestFixedCards:
    """Test Fixed Card identification."""

    def test_king_of_spades_is_fixed(self):
        """King of Spades is one of three fixed cards."""
        card = Card(rank=13, suit=Suit.SPADES)
        assert is_fixed_card(card) is True

    def test_jack_of_hearts_is_fixed(self):
        """Jack of Hearts (July 30) is a fixed card."""
        # July 30: 55 - ((7*2) + 30) = 55 - 44 = 11 (Jack of Hearts)
        card = calculate_birth_card(7, 30)
        assert card.rank == 11
        assert card.suit == Suit.HEARTS
        assert is_fixed_card(card) is True

    def test_eight_of_clubs_is_fixed(self):
        """Eight of Clubs is a fixed card."""
        card = Card(rank=8, suit=Suit.CLUBS)
        assert is_fixed_card(card) is True

    def test_fixed_cards_have_no_karma(self):
        """Fixed cards return (None, None) for karma cards."""
        fixed_card = Card(rank=13, suit=Suit.SPADES)
        first, second = calculate_karma_cards(fixed_card)

        assert first is None
        assert second is None


class TestSemiFixedCards:
    """Test Semi-Fixed Card pairs."""

    def test_ace_of_clubs_semi_fixed(self):
        """Ace of Clubs swaps with Two of Hearts."""
        card = Card(rank=1, suit=Suit.CLUBS)
        is_semi, twin = is_semi_fixed_card(card)

        assert is_semi is True
        assert twin.rank == 2
        assert twin.suit == Suit.HEARTS

    def test_seven_of_diamonds_semi_fixed(self):
        """Seven of Diamonds swaps with Nine of Hearts."""
        card = Card(rank=7, suit=Suit.DIAMONDS)
        is_semi, twin = is_semi_fixed_card(card)

        assert is_semi is True
        assert twin.rank == 9
        assert twin.suit == Suit.HEARTS


class TestCardologyBlueprint:
    """Test complete blueprint generation."""

    def test_brad_pitt_blueprint(self):
        """Generate and validate Brad Pitt's full blueprint."""
        birth_date = date(1963, 12, 18)
        blueprint = generate_blueprint(birth_date, include_year=2026)

        # Birth Card
        assert blueprint.birth_card.rank == 13
        assert blueprint.birth_card.suit == Suit.HEARTS

        # Zodiac
        assert blueprint.zodiac_sign == ZodiacSign.SAGITTARIUS

        # Planetary Periods (should have 7)
        assert len(blueprint.planetary_periods) == 7

        # First period is Mercury
        assert blueprint.planetary_periods[0].planet == Planet.MERCURY

        # Last period is Neptune
        assert blueprint.planetary_periods[6].planet == Planet.NEPTUNE

        # Periods should cover the full year
        first_period = blueprint.planetary_periods[0]
        last_period = blueprint.planetary_periods[6]

        assert first_period.start_date == date(2026, 12, 18)
        assert last_period.end_date == date(2027, 12, 17)

    def test_blueprint_life_path_spread(self):
        """Verify life path spread has all positions."""
        birth_date = date(1990, 6, 15)
        blueprint = generate_blueprint(birth_date)

        expected_positions = [
            "Sun (Birth)", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
        ]

        for position in expected_positions:
            assert position in blueprint.life_path_spread


class TestCardologyModule:
    """Test the CardologyModule wrapper."""

    def test_module_initialization(self):
        """Module initializes with correct metadata."""
        module = CardologyModule()

        assert module.name == "cardology"
        assert module.layer == "intelligence"
        assert module.version == "1.0.0"

    def test_calculate_profile(self):
        """Module can calculate profile from birth date."""
        module = CardologyModule()
        birth_date = date(1963, 12, 18)

        profile = module.calculate_profile(birth_date, target_year=2026)

        # Check structure
        assert "birth_card" in profile
        assert "planetary_ruling_card" in profile
        assert "zodiac_sign" in profile
        assert "karma_cards" in profile
        assert "current_year_periods" in profile

        # Check birth card data
        assert profile["birth_card"]["rank"] == 13
        assert profile["birth_card"]["suit"] == "HEARTS"
        assert profile["birth_card"]["repr"] == "K♥"

        # Check zodiac
        assert profile["zodiac_sign"] == "Sagittarius"

    def test_get_current_period(self):
        """Module can return current period info."""
        module = CardologyModule()
        birth_date = date(1963, 12, 18)

        period_info = module.get_current_period(
            birth_date,
            current_date=date(2026, 2, 4)
        )

        assert "period" in period_info
        assert "card" in period_info
        assert "theme" in period_info
        assert "guidance" in period_info
        assert "days_remaining" in period_info

    def test_get_yearly_timeline(self):
        """Module can generate yearly timeline."""
        module = CardologyModule()
        birth_date = date(1990, 1, 15)

        timeline = module.get_yearly_timeline(birth_date, 2026)

        assert len(timeline) == 7
        assert timeline[0]["period_name"] == "Mercury"
        assert timeline[6]["period_name"] == "Neptune"


class TestKernelTestSuite:
    """Run the kernel's built-in test suite."""

    def test_all_kernel_tests_pass(self):
        """All built-in kernel test cases should pass."""
        results = run_test_suite()

        failed = [r for r in results if not r["passed"]]

        if failed:
            for f in failed:
                print(f"FAILED: {f['date']} - Expected {f['expected_card']}, "
                      f"got {f['actual_card']} | {f['notes']}")

        assert len(failed) == 0, f"{len(failed)} kernel tests failed"


class TestZodiacDetermination:
    """Test zodiac sign calculation."""

    def test_zodiac_boundaries(self):
        """Test zodiac sign at boundary dates."""
        from src.app.modules.intelligence.cardology.kernel import get_zodiac_sign

        # Sagittarius: Nov 22 - Dec 21
        assert get_zodiac_sign(11, 22) == ZodiacSign.SAGITTARIUS
        assert get_zodiac_sign(12, 21) == ZodiacSign.SAGITTARIUS

        # Capricorn: Dec 22 - Jan 19
        assert get_zodiac_sign(12, 22) == ZodiacSign.CAPRICORN
        assert get_zodiac_sign(1, 1) == ZodiacSign.CAPRICORN
        assert get_zodiac_sign(1, 19) == ZodiacSign.CAPRICORN

        # Aquarius: Jan 20 - Feb 18
        assert get_zodiac_sign(1, 20) == ZodiacSign.AQUARIUS


class TestPlanetaryPeriods:
    """Test planetary period calculations."""

    def test_period_durations(self):
        """First 6 periods are 52 days, Neptune takes remainder."""
        birth_date = date(1990, 6, 15)
        blueprint = generate_blueprint(birth_date, include_year=2026)

        for i, period in enumerate(blueprint.planetary_periods[:6]):
            assert period.duration_days == 52, \
                f"Period {i} ({period.planet.value}) has {period.duration_days} days, expected 52"

        # Neptune period should be 53 days (365 - 312 = 53, or 366 - 312 = 54 in leap year)
        neptune = blueprint.planetary_periods[6]
        assert neptune.planet == Planet.NEPTUNE
        assert neptune.duration_days >= 52  # Could be 53 or 54

    def test_periods_are_contiguous(self):
        """Periods should be contiguous with no gaps."""
        birth_date = date(1985, 3, 20)
        blueprint = generate_blueprint(birth_date, include_year=2026)

        for i in range(len(blueprint.planetary_periods) - 1):
            current = blueprint.planetary_periods[i]
            next_period = blueprint.planetary_periods[i + 1]

            from datetime import timedelta
            expected_next_start = current.end_date + timedelta(days=1)

            assert next_period.start_date == expected_next_start, \
                f"Gap between {current.planet.value} and {next_period.planet.value}"


# Standalone test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
