"""
Genesis Strategy System

Refinement strategies convert hypotheses into natural probe questions.
Each strategy knows which fields it applies to and how to prompt the LLM.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ..hypothesis import Hypothesis
from ..probes import ProbeType


@runtime_checkable
class StrategyTemplate(Protocol):
    """Protocol for refinement strategy templates."""

    strategy_name: str
    applicable_fields: list[str]
    probe_type: ProbeType

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        """Generate LLM prompt for this strategy."""
        ...


class StrategyRegistry:
    """
    Central registry of refinement strategies.

    Modules register their strategies at startup, and ProbeGenerator
    retrieves them when generating probes.

    Usage:
        # Registration (at startup)
        StrategyRegistry.register(MorningRoutineStrategy())

        # Retrieval
        strategy = StrategyRegistry.get_strategy("morning_routine")
        prompt = strategy.generate_prompt(hypothesis)
    """

    _strategies: dict[str, StrategyTemplate] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, strategy: StrategyTemplate) -> None:
        """Register a strategy template."""
        cls._strategies[strategy.strategy_name] = strategy

    @classmethod
    def unregister(cls, strategy_name: str) -> bool:
        """Remove a strategy from registry."""
        if strategy_name in cls._strategies:
            del cls._strategies[strategy_name]
            return True
        return False

    @classmethod
    def get_strategy(cls, strategy_name: str) -> StrategyTemplate | None:
        """Get strategy by name."""
        return cls._strategies.get(strategy_name)

    @classmethod
    def get_strategies_for_field(cls, field: str) -> list[StrategyTemplate]:
        """Get all strategies applicable to a field."""
        return [
            s for s in cls._strategies.values()
            if field in s.applicable_fields
        ]

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered strategy names."""
        return list(cls._strategies.keys())

    @classmethod
    def initialize_defaults(cls) -> None:
        """Register all default strategies."""
        if cls._initialized:
            return

        from .hd_type import (
            DecisionStyleStrategy,
            EnergyPatternStrategy,
            WaitingResponseStrategy,
            WorkRhythmStrategy,
        )
        from .rising_sign import (
            FirstImpressionStrategy,
            LifeEventTimingStrategy,
            MorningRoutineStrategy,
            PhysicalAppearanceStrategy,
        )

        # Rising sign strategies
        cls.register(MorningRoutineStrategy())
        cls.register(FirstImpressionStrategy())
        cls.register(LifeEventTimingStrategy())
        cls.register(PhysicalAppearanceStrategy())

        # HD type strategies
        cls.register(EnergyPatternStrategy())
        cls.register(DecisionStyleStrategy())
        cls.register(WaitingResponseStrategy())
        cls.register(WorkRhythmStrategy())

        cls._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Clear all registered strategies (for testing)."""
        cls._strategies = {}
        cls._initialized = False
