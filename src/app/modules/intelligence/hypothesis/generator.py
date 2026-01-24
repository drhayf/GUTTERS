"""
Hypothesis generation engine.

Reads Observer patterns and generates testable theories.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional

from .models import Hypothesis, HypothesisType, HypothesisStatus
from langchain_core.messages import SystemMessage, HumanMessage
from src.app.core.events.bus import get_event_bus
from src.app.protocol.events import HYPOTHESIS_GENERATED

class HypothesisGenerator:
    """Generate theories from Observer patterns."""
    
    def __init__(self, llm):
        self.llm = llm
        self.event_bus = get_event_bus()
    
    async def _ensure_event_bus(self):
        """Ensure event bus is initialized."""
        if not self.event_bus.redis_client:
            await self.event_bus.initialize()

    async def generate_from_patterns(
        self,
        user_id: int,
        patterns: List[dict]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses from Observer patterns.
        
        Args:
            user_id: User ID
            patterns: List of Observer findings
        
        Returns:
            List of generated hypotheses
        """
        await self._ensure_event_bus()
        hypotheses = []
        
        for pattern in patterns:
            hypothesis = None
            
            # Solar sensitivity hypothesis
            if pattern.get('pattern_type') == 'solar_symptom':
                hypothesis = self._generate_solar_sensitivity_hypothesis(
                    user_id,
                    pattern
                )
            
            # Lunar pattern hypothesis
            elif pattern.get('pattern_type') == 'lunar_phase':
                hypothesis = self._generate_lunar_pattern_hypothesis(
                    user_id,
                    pattern
                )
            
            # Temporal pattern hypothesis
            elif pattern.get('pattern_type') == 'day_of_week':
                hypothesis = self._generate_temporal_hypothesis(
                    user_id,
                    pattern
                )
            
            # Transit correlation hypothesis
            elif pattern.get('pattern_type') == 'transit_theme':
                hypothesis = self._generate_transit_hypothesis(
                    user_id,
                    pattern
                )
            
            if hypothesis:
                hypotheses.append(hypothesis)
                
                # Publish event
                await self.event_bus.publish(
                    HYPOTHESIS_GENERATED,
                    {
                        "user_id": hypothesis.user_id,
                        "hypothesis_id": hypothesis.id,
                        "hypothesis_type": hypothesis.hypothesis_type.value,
                        "confidence": hypothesis.confidence,
                        "generated_at": hypothesis.generated_at.isoformat()
                    }
                )
        
        return hypotheses
    
    def _generate_solar_sensitivity_hypothesis(
        self,
        user_id: int,
        pattern: dict
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about solar sensitivity."""
        
        # Extract pattern details
        correlation = pattern.get('correlation', 0)
        symptom = pattern.get('symptom', 'symptoms')
        data_points = pattern.get('data_points', 0)
        
        # Initial confidence from correlation strength
        # Strong correlation (0.8+) = high initial confidence
        initial_confidence = min(correlation * 0.85, 0.75)  # Cap at 0.75 initially
        
        # Determine status
        if initial_confidence < 0.60:
            status = HypothesisStatus.FORMING
        elif initial_confidence < 0.85:
            status = HypothesisStatus.TESTING
        else:
            status = HypothesisStatus.CONFIRMED
        
        return Hypothesis(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
            claim=f"User is electromagnetically sensitive, experiencing {symptom} during geomagnetic storms",
            predicted_value=f"Sensitive to solar activity (Kp > 5)",
            confidence=initial_confidence,
            evidence_count=data_points,
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            supporting_evidence=[{
                "type": "observer_pattern",
                "correlation": correlation,
                "p_value": pattern.get('p_value', 0),
                "data_points": data_points,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            status=status,
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            last_evidence_at=datetime.now(timezone.utc)
        )
    
    def _generate_lunar_pattern_hypothesis(
        self,
        user_id: int,
        pattern: dict
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about lunar patterns."""
        
        phase = pattern.get('phase', 'unknown')
        mood_diff = pattern.get('mood_diff', 0)
        energy_diff = pattern.get('energy_diff', 0)
        
        # Confidence from pattern strength
        initial_confidence = min(pattern.get('confidence', 0.5) * 0.9, 0.75)
        
        if mood_diff < -1.5:
            claim = f"User experiences mood drops during {phase} moon phase"
            predicted_value = f"Low mood during {phase}"
        elif mood_diff > 1.5:
            claim = f"User experiences mood elevation during {phase} moon phase"
            predicted_value = f"High mood during {phase}"
        elif energy_diff < -1.5:
            claim = f"User experiences energy depletion during {phase} moon phase"
            predicted_value = f"Low energy during {phase}"
        else:
            claim = f"User experiences energy peaks during {phase} moon phase"
            predicted_value = f"High energy during {phase}"
        
        return Hypothesis(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
            claim=claim,
            predicted_value=predicted_value,
            confidence=initial_confidence,
            evidence_count=pattern.get('data_points', 0),
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            status=HypothesisStatus.TESTING if initial_confidence >= 0.60 else HypothesisStatus.FORMING,
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            last_evidence_at=datetime.now(timezone.utc)
        )
    
    def _generate_temporal_hypothesis(
        self,
        user_id: int,
        pattern: dict
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about time-based patterns."""
        
        day = pattern.get('day', 'unknown')
        mood_diff = pattern.get('mood_diff', 0)
        
        initial_confidence = pattern.get('confidence', 0.5) * 0.9
        
        if mood_diff < 0:
            claim = f"User consistently experiences mood drops on {day}s"
            predicted_value = f"Low mood on {day}"
        else:
            claim = f"User consistently experiences mood elevation on {day}s"
            predicted_value = f"High mood on {day}"
        
        return Hypothesis(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hypothesis_type=HypothesisType.TEMPORAL_PATTERN,
            claim=claim,
            predicted_value=predicted_value,
            confidence=initial_confidence,
            evidence_count=pattern.get('data_points', 0),
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            status=HypothesisStatus.TESTING if initial_confidence >= 0.60 else HypothesisStatus.FORMING,
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            last_evidence_at=datetime.now(timezone.utc)
        )
    
    def _generate_transit_hypothesis(
        self,
        user_id: int,
        pattern: dict
    ) -> Optional[Hypothesis]:
        """Generate hypothesis about transit effects."""
        
        transit = pattern.get('transit', 'unknown')
        theme = pattern.get('theme', 'unknown')
        frequency = pattern.get('frequency', 0)
        
        initial_confidence = min(frequency * 0.85, 0.75)  # Frequency-based confidence
        
        return Hypothesis(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hypothesis_type=HypothesisType.TRANSIT_EFFECT,
            claim=f"User experiences {theme} themes when {transit} is active",
            predicted_value=f"{theme} during {transit}",
            confidence=initial_confidence,
            evidence_count=pattern.get('data_points', 0),
            contradictions=0,
            based_on_patterns=[pattern.get('id', 'unknown')],
            status=HypothesisStatus.TESTING if initial_confidence >= 0.60 else HypothesisStatus.FORMING,
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            last_evidence_at=datetime.now(timezone.utc)
        )
    
    async def generate_birth_time_hypothesis(
        self,
        user_id: int,
        personality_traits: List[str],
        life_events: List[dict]
    ) -> Hypothesis:
        """
        Generate hypothesis about likely birth time / rising sign.
        
        Uses LLM to analyze personality traits and life events to predict rising sign.
        """
        traits_text = "\n".join([f"- {trait}" for trait in personality_traits])
        events_text = "\n".join([f"- {event['description']} (age {event['age']})" for event in life_events])
        
        prompt = f"""Based on these personality traits and life events, predict the most likely rising sign:

**Personality Traits:**
{traits_text}

**Life Events:**
{events_text}

Analyze which rising sign best matches these characteristics. Consider:
1. Outer persona and first impressions
2. Approach to new situations
3. Physical appearance themes
4. Life path milestones

Respond with JSON:
{{
    "rising_sign": "Virgo",
    "confidence": 0.68,
    "reasoning": "Organizational traits, attention to detail, and methodical approach suggest Virgo rising..."
}}
"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert astrologer skilled at rising sign prediction."),
            HumanMessage(content=prompt)
        ])
        
        # Parse response
        import json
        import re
        
        # Attempt to extract JSON if LLM included conversational text
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            # Fallback if parsing fails
            result = {"rising_sign": "Unknown", "confidence": 0.5, "reasoning": "Analysis failed"}
        
        return Hypothesis(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hypothesis_type=HypothesisType.RISING_SIGN,
            claim=f"User's rising sign is likely {result['rising_sign']} based on personality and life patterns",
            predicted_value=result['rising_sign'],
            confidence=result.get('confidence', 0.5),
            evidence_count=len(personality_traits) + len(life_events),
            contradictions=0,
            based_on_patterns=[],
            supporting_evidence=[{
                "type": "personality_analysis",
                "traits": personality_traits,
                "life_events": life_events,
                "reasoning": result.get('reasoning', "Analyzed personality traits"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            status=HypothesisStatus.TESTING,
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            last_evidence_at=datetime.now(timezone.utc)
        )
