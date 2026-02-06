"""
Genesis integration for synthesis confidence.

Synthesis can have varying confidence based on:
- Missing birth time (probabilistic astrology)
- Limited Observer data (few patterns detected)
- Incomplete modules
"""

from src.app.modules.intelligence.genesis.core.models import UncertaintyDeclaration, UncertaintyField


class SynthesisUncertaintyExtractor:
    """Extract uncertainty from synthesis generation."""

    module_name = "synthesis"

    async def extract(
        self,
        synthesis_result: dict,
        user_id: int
    ) -> UncertaintyDeclaration | None:
        """
        Determine synthesis confidence.

        Factors:
        - Missing birth time reduces astrology confidence
        - < 20 Observer data points reduces pattern confidence
        - Missing modules reduce overall confidence
        """
        fields = []

        # Check if astrology is probabilistic
        if synthesis_result.get("astrology_probabilistic"):
            fields.append(UncertaintyField(
                field="astrology_synthesis",
                candidates=[
                    {
                        "value": "Full confidence (exact birth time)",
                        "confidence": 0.4,
                        "reasoning": "Birth time unknown, using probabilistic calculation"
                    },
                    {
                        "value": "Moderate confidence (±2 hour window)",
                        "confidence": 0.6,
                        "reasoning": "Birth time estimated from personality traits"
                    }
                ],
                refinement_strategies=["personality_based_rising_sign", "life_event_timing"]
            ))

        # Check Observer data sufficiency
        observer_count = synthesis_result.get("observer_data_points", 0)
        if observer_count < 20:
            fields.append(UncertaintyField(
                field="pattern_synthesis",
                candidates=[
                    {
                        "value": "High confidence patterns",
                        "confidence": 0.3,
                        "reasoning": f"Only {observer_count} data points, need 20+ for strong patterns"
                    },
                    {
                        "value": "Emerging patterns",
                        "confidence": 0.7,
                        "reasoning": "Early pattern detection, will improve with more data"
                    }
                ],
                refinement_strategies=["journal_more", "wait_for_data"]
            ))

        if fields:
            return UncertaintyDeclaration(
                module=self.module_name,
                fields=fields
            )

        return None
