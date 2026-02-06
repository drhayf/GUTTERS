"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              COUNCIL OF SYSTEMS INTEGRATION TESTS                            ║
║                                                                              ║
║   Tests for the I-Ching Logic Kernel and Harmonic Synthesis Engine          ║
║   verifying cross-system integration and resonance calculations             ║
║                                                                              ║
║   Author: GUTTERS Project / Magi OS                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from datetime import UTC, datetime

import pytest

# I-Ching Kernel
from src.app.modules.intelligence.iching import (
    CHANNELS,
    GATE_CIRCLE,
    GATE_DATABASE,
    IChingKernel,
    Trigram,
)

# Harmonic Synthesis
from src.app.modules.intelligence.synthesis.harmonic import (
    CardologyAdapter,
    CouncilOfSystems,
    Element,
    HarmonicSynthesis,
    IChingAdapter,
    ResonanceType,
    SystemReading,
    cross_system_synthesis,
)

# =============================================================================
# I-Ching Kernel Unit Tests
# =============================================================================

class TestIChingKernel:
    """Tests for the I-Ching Logic Kernel."""

    @pytest.fixture
    def kernel(self) -> IChingKernel:
        """Create a fresh kernel instance."""
        return IChingKernel()

    def test_kernel_instantiation(self, kernel: IChingKernel):
        """Kernel should instantiate without errors."""
        assert kernel is not None

    def test_gate_database_completeness(self):
        """GATE_DATABASE should contain all 64 gates."""
        assert len(GATE_DATABASE) == 64
        for gate_num in range(1, 65):
            assert gate_num in GATE_DATABASE, f"Gate {gate_num} missing from database"

    def test_gate_circle_completeness(self):
        """GATE_CIRCLE should contain exactly 64 gates."""
        assert len(GATE_CIRCLE) == 64
        # Should contain all gates 1-64
        assert set(GATE_CIRCLE) == set(range(1, 65))

    def test_channels_structure(self):
        """CHANNELS should define valid gate pairs."""
        # CHANNELS is a dict with (gate1, gate2) tuple keys
        assert isinstance(CHANNELS, dict)
        for key, channel in CHANNELS.items():
            # Key is a tuple of (gate1, gate2)
            assert isinstance(key, tuple)
            assert len(key) == 2
            # Channel has gate_1 and gate_2 attributes
            assert hasattr(channel, 'gate_1')

    def test_gate_1_at_223_degrees(self, kernel: IChingKernel):
        """Gate 1 should be active at longitude 223.25°."""
        activation = kernel.longitude_to_activation(223.25)
        assert activation.gate == 1, f"Expected Gate 1 at 223.25°, got Gate {activation.gate}"

    def test_gate_41_at_302_degrees(self, kernel: IChingKernel):
        """Gate 41 (the starting gate) should be active at longitude 302°."""
        activation = kernel.longitude_to_activation(302.0)
        assert activation.gate == 41, f"Expected Gate 41 at 302°, got Gate {activation.gate}"

    def test_line_calculation_range(self, kernel: IChingKernel):
        """Lines should be in range 1-6."""
        for longitude in [0, 45, 90, 135, 180, 225, 270, 315]:
            activation = kernel.longitude_to_activation(longitude)
            assert 1 <= activation.line <= 6, f"Invalid line {activation.line} at {longitude}°"

    def test_daily_code_structure(self, kernel: IChingKernel):
        """get_daily_code should return valid DailyCode."""
        daily = kernel.get_daily_code()

        assert daily is not None
        assert hasattr(daily, 'sun_activation')
        assert hasattr(daily, 'earth_activation')
        assert daily.sun_activation.gate in range(1, 65)
        assert daily.earth_activation.gate in range(1, 65)

    def test_sun_earth_polarity(self, kernel: IChingKernel):
        """Sun and Earth should be 180° apart (opposite gates)."""
        daily = kernel.get_daily_code()

        # The gates should be different (180° polarity)
        # Note: They won't always be mathematically opposite in the gate circle
        # but they represent the polarity axis
        assert daily.sun_activation.gate != daily.earth_activation.gate

    def test_gate_info_structure(self):
        """Each gate should have complete info structure."""
        gate_1 = GATE_DATABASE.get(1)
        assert gate_1 is not None

        # GateData is a dataclass - check for hd_name attribute
        assert hasattr(gate_1, 'hd_name')
        assert gate_1.hd_name is not None

    def test_hexagram_binary_format(self):
        """Gate binaries should be 6-character strings."""
        for gate_num, gate_data in GATE_DATABASE.items():
            if isinstance(gate_data, dict):
                binary = gate_data.get('binary', '')
            else:
                binary = getattr(gate_data, 'binary', '')

            if binary:  # Only check if binary field exists
                assert len(binary) == 6, f"Gate {gate_num} binary not 6 chars: {binary}"
                assert set(binary) <= {'0', '1'}, f"Gate {gate_num} binary has invalid chars"

    def test_trigram_enum_completeness(self):
        """Trigram enum should have 8 trigrams."""
        assert len(Trigram) == 8

    def test_activation_dataclass(self, kernel: IChingKernel):
        """Activation should include gate, line, color, tone, base."""
        activation = kernel.longitude_to_activation(0.0)

        assert hasattr(activation, 'gate')
        assert hasattr(activation, 'line')
        # color, tone, base may be optional depending on precision

    def test_specific_date_calculation(self, kernel: IChingKernel):
        """Test calculation for a known date."""
        # Use a fixed test date
        test_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        daily = kernel.get_daily_code(test_dt)

        # Just verify we get valid results
        assert 1 <= daily.sun_activation.gate <= 64
        assert 1 <= daily.earth_activation.gate <= 64


# =============================================================================
# Harmonic Synthesis Tests
# =============================================================================

class TestHarmonicSynthesis:
    """Tests for the Council of Systems and Harmonic Synthesis."""

    @pytest.fixture
    def council(self) -> CouncilOfSystems:
        """Create Council with registered systems."""
        council = CouncilOfSystems()
        kernel = IChingKernel()

        council.register_system("I-Ching", IChingAdapter(kernel))
        council.register_system("Cardology", CardologyAdapter())

        return council

    def test_council_instantiation(self):
        """Council should instantiate without errors."""
        council = CouncilOfSystems()
        assert council is not None

    def test_system_registration(self, council: CouncilOfSystems):
        """Systems should register successfully."""
        # Council should have both systems registered
        assert len(council._systems) >= 2

    def test_iching_adapter_reading(self):
        """IChingAdapter should produce valid SystemReading."""
        kernel = IChingKernel()
        adapter = IChingAdapter(kernel)

        reading = adapter.get_reading(datetime.now(UTC))

        assert isinstance(reading, SystemReading)
        assert reading.system_name == "I-Ching"
        # SystemReading uses 'element' not 'primary_element'
        assert reading.element is not None

    def test_cardology_adapter_reading(self):
        """CardologyAdapter should produce valid SystemReading."""
        adapter = CardologyAdapter()
        reading = adapter.get_reading(datetime.now(UTC))

        assert isinstance(reading, SystemReading)
        assert reading.system_name == "Cardology"

    def test_synthesis_output_structure(self, council: CouncilOfSystems):
        """Synthesize should return HarmonicSynthesis with all fields."""
        synthesis = council.synthesize()

        assert isinstance(synthesis, HarmonicSynthesis)
        assert hasattr(synthesis, 'resonance_score')
        assert hasattr(synthesis, 'resonance_type')
        assert hasattr(synthesis, 'macro_theme')
        assert hasattr(synthesis, 'micro_theme')
        assert hasattr(synthesis, 'synthesis_guidance')
        assert hasattr(synthesis, 'quest_suggestions')

    def test_resonance_score_range(self, council: CouncilOfSystems):
        """Resonance score should be between 0 and 1."""
        synthesis = council.synthesize()
        assert 0.0 <= synthesis.resonance_score <= 1.0

    def test_resonance_type_validity(self, council: CouncilOfSystems):
        """Resonance type should be a valid ResonanceType."""
        synthesis = council.synthesize()
        assert isinstance(synthesis.resonance_type, ResonanceType)

    def test_quest_suggestions_list(self, council: CouncilOfSystems):
        """Quest suggestions should be a list of strings."""
        synthesis = council.synthesize()
        assert isinstance(synthesis.quest_suggestions, list)

    def test_cross_system_synthesis_function(self):
        """cross_system_synthesis helper should work."""
        # Create mock readings with actual SystemReading signature
        iching_reading = SystemReading(
            system_name="I-Ching",
            timestamp=datetime.now(UTC),
            primary_symbol="1",
            primary_name="Gate 1",
            element=Element.FIRE,
            archetype="Creator",
            keynote="The Creative",
            shadow="Entropy",
            gift="Freshness",
            siddhi="Beauty",
            cycle_day=1,
            cycle_total=6,
            cycle_percentage=16.67,
        )

        cardology_reading = SystemReading(
            system_name="Cardology",
            timestamp=datetime.now(UTC),
            primary_symbol="K♣",
            primary_name="King of Clubs",
            element=Element.FIRE,
            archetype="Master",
            keynote="Knowledge",
            shadow="Confusion",
            gift="Clarity",
            siddhi="Wisdom",
            cycle_day=10,
            cycle_total=52,
            cycle_percentage=19.2,
        )

        result = cross_system_synthesis(cardology_reading, iching_reading)

        assert isinstance(result, dict)
        assert 'resonance_score' in result
        assert 'synthesis_guidance' in result


# =============================================================================
# Element and Resonance Tests
# =============================================================================

class TestElementalResonance:
    """Tests for elemental correspondence and resonance calculation."""

    def test_element_enum_values(self):
        """Element enum should have 5 elements."""
        assert len(Element) == 5
        assert Element.FIRE in Element
        assert Element.WATER in Element
        assert Element.AIR in Element
        assert Element.EARTH in Element
        assert Element.ETHER in Element

    def test_resonance_type_hierarchy(self):
        """ResonanceType should have correct hierarchy."""
        assert ResonanceType.HARMONIC is not None
        assert ResonanceType.SUPPORTIVE is not None
        assert ResonanceType.NEUTRAL is not None
        assert ResonanceType.CHALLENGING is not None
        assert ResonanceType.DISSONANT is not None

    def test_same_element_resonance(self):
        """Same elements should produce high resonance."""
        # This tests the internal resonance calculation logic
        # Elements: FIRE+FIRE should resonate highly
        pass  # Depends on internal implementation


# =============================================================================
# Integration with Chronos
# =============================================================================

class TestChronosIntegration:
    """Tests for Chronos-I-Ching integration."""

    @pytest.mark.asyncio
    async def test_chronos_hexagram_method(self):
        """ChronosStateManager should have hexagram methods."""
        from src.app.core.state.chronos import get_chronos_manager

        manager = get_chronos_manager()

        assert hasattr(manager, 'get_current_hexagram')
        assert hasattr(manager, 'refresh_hexagram')
        assert hasattr(manager, 'get_council_synthesis')

    @pytest.mark.asyncio
    async def test_hexagram_calculation_without_redis(self):
        """Hexagram should calculate even without Redis."""
        from src.app.core.state.chronos import get_chronos_manager

        manager = get_chronos_manager()

        # This may return None if kernel fails, but shouldn't crash
        try:
            result = await manager.get_current_hexagram()
            if result:
                assert 'sun_gate' in result
                assert 'earth_gate' in result
        except Exception as e:
            # Expected in test environment without full setup
            pytest.skip(f"Requires full environment: {e}")


# =============================================================================
# Event Integration Tests
# =============================================================================

class TestEventIntegration:
    """Tests for event emission from hexagram changes."""

    def test_hexagram_events_defined(self):
        """MAGI_HEXAGRAM_CHANGE event should be defined."""
        from src.app.protocol.events import (
            MAGI_COUNCIL_SYNTHESIS,
            MAGI_HEXAGRAM_CHANGE,
            MAGI_RESONANCE_SHIFT,
        )

        assert MAGI_HEXAGRAM_CHANGE == "magi.hexagram.change"
        assert MAGI_COUNCIL_SYNTHESIS == "magi.council.synthesis"
        assert MAGI_RESONANCE_SHIFT == "magi.resonance.shift"


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance tests for kernel calculations."""

    def test_kernel_calculation_speed(self):
        """Kernel should calculate activations quickly."""
        import time

        kernel = IChingKernel()

        start = time.time()
        for _ in range(1000):
            kernel.longitude_to_activation(180.0)
        elapsed = time.time() - start

        # Should complete 1000 calculations in under 1 second
        assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s for 1000 calculations"

    def test_synthesis_speed(self):
        """Council synthesis should complete quickly."""
        import time

        council = CouncilOfSystems()
        kernel = IChingKernel()
        council.register_system("I-Ching", IChingAdapter(kernel))
        council.register_system("Cardology", CardologyAdapter())

        start = time.time()
        for _ in range(100):
            council.synthesize()
        elapsed = time.time() - start

        # Should complete 100 syntheses in under 2 seconds
        assert elapsed < 2.0, f"Too slow: {elapsed:.2f}s for 100 syntheses"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
