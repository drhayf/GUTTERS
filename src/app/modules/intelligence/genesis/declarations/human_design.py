"""
Human Design Uncertainty Extractor

Extracts uncertainties from Human Design calculation results,
specifically type when birth time is unknown.
"""

from typing import Any, Union

from ..uncertainty import UncertaintyDeclaration, UncertaintyField
from .base import UncertaintyExtractor

# Import the HD schema for type hints (optional for duck typing)
try:
    from ....calculation.human_design.schemas import HumanDesignChart
except ImportError:
    HumanDesignChart = dict  # Fallback for testing


class HumanDesignUncertaintyExtractor(UncertaintyExtractor[Union[dict, "HumanDesignChart"]]):
    """
    Extracts uncertainties from Human Design chart results.

    When birth time is unknown, HD calculates probabilistically
    and produces type_probabilities. This extractor reads those
    probabilities and creates uncertainty declarations.

    Extracted fields:
    - type: From type_probabilities list (Generator, Projector, etc.)
    - profile: If profile varies across sampled hours
    """

    module_name = "human_design"
    result_type = dict  # Accept both dict and HumanDesignChart

    # Refinement strategies for each uncertain field
    REFINEMENT_STRATEGIES = {
        "type": [
            "energy_pattern",       # "Do you have consistent energy all day?"
            "work_rhythm",          # "How do you approach sustainable work?"
            "decision_style",       # "Do you initiate or wait to respond?"
            "social_interaction",   # "Are you an initiator in social situations?"
            "rest_recovery",        # "How does rest affect your productivity?"
            "waiting_response",     # "Do you wait for invitations/responses?"
        ],
        "profile": [
            "life_theme",           # "Is your path one of investigation or experimentation?"
            "learning_style",       # "Do you learn by trial/error or study?"
            "social_role",          # "Are you naturally hermit-like or social?"
        ],
        "authority": [
            "decision_making",      # "How do you make important decisions?"
            "gut_feelings",         # "Do you trust spontaneous responses?"
            "emotional_clarity",    # "Do you need time for emotional clarity?"
        ]
    }

    def can_extract(self, result: Union[dict, Any]) -> bool:
        """
        Check if this HD result has extractable uncertainties.

        Looks for:
        - accuracy == "probabilistic" or "partial"
        - type_probabilities list present
        """
        # Handle both dict and Pydantic model
        if isinstance(result, dict):
            accuracy = result.get("accuracy", "full")
            has_probabilities = result.get("type_probabilities") is not None
        else:
            accuracy = getattr(result, "accuracy", "full")
            has_probabilities = getattr(result, "type_probabilities", None) is not None

        return accuracy in ("probabilistic", "partial") and has_probabilities

    def extract(
        self,
        result: Union[dict, Any],
        user_id: int,
        session_id: str
    ) -> UncertaintyDeclaration | None:
        """
        Extract uncertainties from Human Design result.

        Reads type_probabilities and converts to UncertaintyField.
        """
        if not self.can_extract(result):
            return None

        fields: list[UncertaintyField] = []

        # Get type_probabilities (handle both dict and Pydantic)
        if isinstance(result, dict):
            type_probs = result.get("type_probabilities", [])
            accuracy = result.get("accuracy", "probabilistic")
        else:
            type_probs = result.type_probabilities or []
            accuracy = result.accuracy

        # Extract type uncertainty
        if type_probs:
            candidates = {}
            for prob in type_probs:
                if isinstance(prob, dict):
                    type_value = prob.get("value")
                    probability = prob.get("probability", 0.0)
                else:
                    # TypeProbability Pydantic model
                    type_value = prob.value
                    probability = prob.probability

                if type_value:
                    candidates[type_value] = probability

            if candidates:
                fields.append(self._create_field(
                    field_name="type",
                    candidates=candidates,
                    confidence_threshold=0.80
                ))

        # Extract planet stability (for profile uncertainty)
        if isinstance(result, dict):
            planet_stability = result.get("planet_stability", [])
        else:
            planet_stability = getattr(result, "planet_stability", []) or []

        # Check if Sun or Earth gates are unstable (affects profile)
        if planet_stability:
            profile_affecting_planets = {"Sun", "Earth"}
            unstable_profile_planets = []

            for planet in planet_stability:
                if isinstance(planet, dict):
                    planet_name = planet.get("planet", "")
                    is_stable = planet.get("stable", True)
                else:
                    planet_name = planet.planet
                    is_stable = planet.stable

                if planet_name in profile_affecting_planets and not is_stable:
                    unstable_profile_planets.append(planet_name)

            # If Sun or Earth is unstable, profile may vary
            if unstable_profile_planets:
                # We'd need to calculate profile variations, but for now
                # just note that profile is uncertain
                fields.append(self._create_field(
                    field_name="profile",
                    candidates={"variable": 1.0},  # Needs refinement from HD results
                    confidence_threshold=0.80
                ))

        if not fields:
            return None

        return self._create_declaration(
            user_id=user_id,
            session_id=session_id,
            fields=fields,
            source_accuracy=accuracy
        )
