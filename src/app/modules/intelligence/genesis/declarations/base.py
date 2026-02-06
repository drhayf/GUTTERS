"""
Genesis Uncertainty Extractor Base Class

Abstract base for module-specific uncertainty extractors.
Each calculation module implements its own extractor that knows
how to read its result schema and declare uncertainties.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Generic, TypeVar

from ..uncertainty import UncertaintyDeclaration, UncertaintyField

# Type variable for result types (dict, Pydantic model, etc.)
T = TypeVar("T")


class UncertaintyExtractor(ABC, Generic[T]):
    """
    Abstract base class for extracting uncertainties from calculation results.

    Each calculation module (astrology, human_design, etc.) implements
    its own extractor that understands its result schema.

    Type parameter T specifies what the extractor expects:
    - dict for raw dictionary results
    - Specific Pydantic model for typed results

    Example:
        class AstrologyUncertaintyExtractor(UncertaintyExtractor[dict]):
            module_name = "astrology"
            result_type = dict

            def can_extract(self, result: dict) -> bool:
                return result.get("accuracy") == "probabilistic"
    """

    # Subclasses must define these
    module_name: str
    result_type: type[T]

    # Refinement strategies this module supports
    # Maps field name to list of strategy names
    REFINEMENT_STRATEGIES: dict[str, list[str]] = {}

    @abstractmethod
    def can_extract(self, result: T) -> bool:
        """
        Check if the result has extractable uncertainties.

        A result is extractable if:
        - It was calculated probabilistically
        - It contains probability distributions

        Args:
            result: Calculation result (type depends on module)

        Returns:
            True if uncertainties can be extracted
        """
        ...

    @abstractmethod
    def extract(self, result: T, user_id: int, session_id: str) -> UncertaintyDeclaration | None:
        """
        Extract uncertainties from a calculation result.

        Args:
            result: The calculation result to extract from
            user_id: User this result belongs to
            session_id: Current conversation/session ID

        Returns:
            UncertaintyDeclaration if uncertainties found, None otherwise
        """
        ...

    def _create_declaration(
        self, user_id: int, session_id: str, fields: list[UncertaintyField], source_accuracy: str
    ) -> UncertaintyDeclaration:
        """
        Helper to create a properly structured declaration.

        Use this in extract() implementations to ensure consistency.
        """
        return UncertaintyDeclaration(
            module=self.module_name,
            user_id=user_id,
            session_id=session_id,
            fields=fields,
            source_accuracy=source_accuracy,
            declared_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
        )

    def _create_field(
        self, field_name: str, candidates: dict[str, float], confidence_threshold: float = 0.80
    ) -> UncertaintyField:
        """
        Helper to create an uncertainty field with strategies.

        Automatically attaches refinement strategies from REFINEMENT_STRATEGIES.
        """
        return UncertaintyField(
            field=field_name,
            module=self.module_name,
            candidates=candidates,
            confidence_threshold=confidence_threshold,
            refinement_strategies=self.REFINEMENT_STRATEGIES.get(field_name, []),
        )
