"""
Astrology Uncertainty Extractor

Extracts uncertainties from astrology calculation results,
specifically rising_sign when birth time is unknown.
"""

from typing import Any

from .base import UncertaintyExtractor
from ..uncertainty import UncertaintyDeclaration, UncertaintyField


class AstrologyUncertaintyExtractor(UncertaintyExtractor[dict]):
    """
    Extracts uncertainties from astrology NatalChartResult.
    
    When birth time is unknown, astrology calculates probabilistically
    and produces rising_probabilities. This extractor reads those
    probabilities and creates uncertainty declarations.
    
    Extracted fields:
    - rising_sign: From rising_probabilities list
    - house_placements: From planet_stability (if variable)
    """
    
    module_name = "astrology"
    result_type = dict
    
    # Refinement strategies for each uncertain field
    REFINEMENT_STRATEGIES = {
        "rising_sign": [
            "morning_routine",      # "When do you naturally wake up?"
            "life_event_timing",    # "What time of day were significant events?"
            "first_impression",     # "How do others describe meeting you?"
            "physical_appearance",  # "Do you identify with these traits?"
            "energy_pattern",       # "When is your energy highest?"
        ],
        "house_placements": [
            "life_area_focus",      # "Which life areas dominate your attention?"
            "career_public_image",  # "How do you present professionally?"
        ]
    }
    
    def can_extract(self, result: dict) -> bool:
        """
        Check if this astrology result has extractable uncertainties.
        
        Looks for:
        - accuracy == "probabilistic" or "solar"
        - rising_probabilities list present
        """
        accuracy = result.get("accuracy", "full")
        has_probabilities = result.get("rising_probabilities") is not None
        
        return accuracy in ("probabilistic", "solar") and has_probabilities
    
    def extract(
        self, 
        result: dict, 
        user_id: int, 
        session_id: str
    ) -> UncertaintyDeclaration | None:
        """
        Extract uncertainties from astrology result.
        
        Reads rising_probabilities and converts to UncertaintyField.
        """
        if not self.can_extract(result):
            return None
        
        fields: list[UncertaintyField] = []
        
        # Extract rising sign uncertainty
        rising_probs = result.get("rising_probabilities", [])
        if rising_probs:
            # Convert list of RisingSignProbability to candidates dict
            # Schema: {"sign": "Leo", "probability": 0.125, ...}
            candidates = {}
            for prob in rising_probs:
                if isinstance(prob, dict):
                    sign = prob.get("sign")
                    probability = prob.get("probability", 0.0)
                else:
                    # Pydantic model - access attributes
                    sign = prob.sign
                    probability = prob.probability
                
                if sign:
                    candidates[sign] = probability
            
            if candidates:
                fields.append(self._create_field(
                    field_name="rising_sign",
                    candidates=candidates,
                    confidence_threshold=0.80
                ))
        
        # Extract planet house uncertainty (from planet_stability)
        planet_stability = result.get("planet_stability", [])
        if planet_stability:
            # Count planets with unstable houses
            unstable_planets = []
            for planet in planet_stability:
                if isinstance(planet, dict):
                    is_stable = planet.get("house_stable", True)
                    planet_name = planet.get("planet")
                else:
                    is_stable = planet.house_stable
                    planet_name = planet.planet
                
                if not is_stable:
                    unstable_planets.append(planet_name)
            
            # If multiple planets have variable houses, add uncertainty
            if len(unstable_planets) >= 3:
                # Create a summary uncertainty for house system
                fields.append(self._create_field(
                    field_name="house_placements",
                    candidates={"variable": 1.0},  # Placeholder
                    confidence_threshold=0.80
                ))
        
        if not fields:
            return None
        
        return self._create_declaration(
            user_id=user_id,
            session_id=session_id,
            fields=fields,
            source_accuracy=result.get("accuracy", "probabilistic")
        )
