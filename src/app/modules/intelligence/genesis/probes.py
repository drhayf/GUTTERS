"""
Genesis Probe System

Defines probe types, packets, and the LLM-powered probe generator.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .hypothesis import Hypothesis


class ProbeType(str, Enum):
    """Types of probes for gathering evidence."""
    
    BINARY_CHOICE = "binary_choice"
    """Two options: 'Which resonates more? [A] or [B]'"""
    
    SLIDER = "slider"
    """Scale response: 'On a scale of 1-10...'"""
    
    REFLECTION = "reflection"
    """Open-ended: 'Tell me more about...'"""
    
    CONFIRMATION = "confirmation"
    """Verify assumption: 'It sounds like you... Is that accurate?'"""


class ProbePacket(BaseModel):
    """
    A generated probe question ready to present to user.
    
    Contains the question, response options (if applicable),
    and mapping of responses to confidence adjustments.
    
    Example:
        ProbePacket(
            hypothesis_id="a1b2c3d4",
            probe_type=ProbeType.BINARY_CHOICE,
            question="In the morning, do you prefer to...",
            options=["Jump right into tasks", "Ease into the day slowly"],
            strategy_used="morning_routine",
            confidence_mappings={
                "0": {"Virgo": 0.15, "Capricorn": 0.10},
                "1": {"Leo": 0.12, "Pisces": 0.08}
            }
        )
    """
    
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    hypothesis_id: str = Field(description="Which hypothesis this probes")
    field: str = Field(description="Field being probed (e.g., 'rising_sign')")
    module: str = Field(description="Module that owns this field")
    probe_type: ProbeType = Field(description="Type of probe")
    question: str = Field(description="The question to ask")
    options: list[str] | None = Field(
        default=None,
        description="Options for BINARY_CHOICE type"
    )
    strategy_used: str = Field(description="Which refinement strategy generated this")
    
    # Response handling
    confidence_mappings: dict[str, dict[str, float]] | None = Field(
        default=None,
        description="Map of response index/value to candidate confidence deltas"
    )
    analysis_hints: dict[str, Any] | None = Field(
        default=None,
        description="Hints for analyzing REFLECTION responses"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime | None = Field(
        default=None,
        description="When this probe expires (optional)"
    )
    
    def get_confidence_delta(
        self, 
        response_key: str, 
        candidate: str
    ) -> float:
        """
        Get confidence delta for a candidate based on response.
        
        Args:
            response_key: Response index ("0", "1") or value
            candidate: Candidate value to get delta for
            
        Returns:
            Confidence delta (positive = boost, negative = reduce)
        """
        if not self.confidence_mappings:
            return 0.0
        
        response_mapping = self.confidence_mappings.get(response_key, {})
        return response_mapping.get(candidate, 0.0)


class ProbeResponse(BaseModel):
    """User's response to a probe."""
    
    probe_id: str = Field(description="ID of the probe being responded to")
    response_type: ProbeType = Field(description="Type of response")
    
    # Response data (one of these will be set based on type)
    selected_option: int | None = Field(
        default=None,
        description="Index of selected option for BINARY_CHOICE"
    )
    slider_value: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Value for SLIDER (0-10)"
    )
    reflection_text: str | None = Field(
        default=None,
        description="Text response for REFLECTION"
    )
    confirmed: bool | None = Field(
        default=None,
        description="True/False for CONFIRMATION"
    )
    
    responded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ProbeGenerator:
    """
    Generates conversational probes using LLM.
    
    Uses strategy templates to create natural questions that
    don't feel like interrogations.
    """
    
    # Default model for probe generation
    DEFAULT_MODEL = "anthropic/claude-3-haiku"
    
    def __init__(self, llm=None):
        """
        Initialize probe generator.
        
        Args:
            llm: LangChain LLM instance (optional, will create if not provided)
        """
        self._llm = llm
    
    @property
    def llm(self):
        """Lazy-load LLM."""
        if self._llm is None:
            from ....core.ai.llm_factory import get_llm
            self._llm = get_llm(self.DEFAULT_MODEL, temperature=0.7)
        return self._llm
    
    async def generate_probe(
        self,
        hypothesis: Hypothesis,
        strategy_name: str,
        probe_type: ProbeType,
        strategy_prompt: str | None = None
    ) -> ProbePacket:
        """
        Generate a conversational probe for this hypothesis.
        
        Args:
            hypothesis: The hypothesis to probe
            strategy_name: Which strategy to use
            probe_type: Type of probe to generate
            strategy_prompt: Custom prompt template (optional)
            
        Returns:
            ProbePacket ready to present to user
        """
        # Build prompt
        prompt = strategy_prompt or self._build_default_prompt(
            hypothesis, strategy_name, probe_type
        )
        
        # Log activity: probe generation started
        trace_id = f"genesis_{hypothesis.user_id}_{hypothesis.id}"
        try:
            from ....core.activity.logger import get_activity_logger
            logger = get_activity_logger()
            await logger.log_activity(
                trace_id=trace_id,
                agent="genesis.probe_generator",
                activity_type="probe_generation_started",
                details={
                    "user_id": hypothesis.user_id,
                    "hypothesis_id": hypothesis.id,
                    "field": hypothesis.field,
                    "suspected_value": hypothesis.suspected_value,
                    "strategy": strategy_name,
                }
            )
        except Exception:
            pass
        
        try:
            # Generate with LLM
            response = await self.llm.ainvoke(prompt)
            result = self._parse_llm_response(response.content, probe_type)
            
            probe = ProbePacket(
                hypothesis_id=hypothesis.id,
                field=hypothesis.field,
                module=hypothesis.module,
                probe_type=probe_type,
                question=result.get("question", "Tell me more about yourself..."),
                options=result.get("options"),
                strategy_used=strategy_name,
                confidence_mappings=result.get("mappings"),
                analysis_hints=result.get("analysis_hints"),
            )
            
            # Log activity: probe generated
            try:
                from ....core.activity.logger import get_activity_logger
                logger = get_activity_logger()
                await logger.log_activity(
                    trace_id=trace_id,
                    agent="genesis.probe_generator",
                    activity_type="probe_generated",
                    details={
                        "user_id": hypothesis.user_id,
                        "hypothesis_id": hypothesis.id,
                        "question": probe.question[:100],
                        "probe_type": probe_type.value,
                    }
                )
            except Exception:
                pass
            
            return probe
            
        except Exception as e:
            # Fallback to simple template if LLM fails
            return self._fallback_probe(hypothesis, strategy_name, probe_type)
    
    def _build_default_prompt(
        self,
        hypothesis: Hypothesis,
        strategy_name: str,
        probe_type: ProbeType
    ) -> str:
        """Build default prompt for probe generation."""
        type_instructions = {
            ProbeType.BINARY_CHOICE: """Generate a binary choice question with exactly 2 options.
Return JSON: {"question": "...", "options": ["A", "B"], "mappings": {"0": {...}, "1": {...}}}""",
            ProbeType.SLIDER: """Generate a scale question (1-10).
Return JSON: {"question": "...", "mappings": {"low": {...}, "mid": {...}, "high": {...}}}""",
            ProbeType.REFLECTION: """Generate an open-ended reflection question.
Return JSON: {"question": "...", "analysis_hints": {...}}""",
            ProbeType.CONFIRMATION: """Generate a confirmation question.
Return JSON: {"question": "...", "mappings": {"yes": {...}, "no": {...}}}""",
        }
        
        return f"""You are helping determine someone's {hypothesis.field} in {hypothesis.module}.

We're testing if their {hypothesis.field} might be {hypothesis.suspected_value}.

Strategy: {strategy_name}
Question type: {probe_type.value}

Requirements:
- Tone: Warm, curious, conversational (not interrogative)
- Focus on observable behaviors and preferences
- Don't mention astrology/HD directly
- Make it feel like getting to know them

{type_instructions.get(probe_type, "")}

The mappings should show confidence adjustments for each candidate:
- Positive values (0.05-0.20) = this response supports this candidate
- Negative values or 0 = doesn't support

Generate the probe now:"""
    
    def _parse_llm_response(
        self, 
        content: str, 
        probe_type: ProbeType
    ) -> dict:
        """Parse LLM response into probe components."""
        import json
        
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "{" in content:
                # Find first { and last }
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
            else:
                raise ValueError("No JSON found")
            
            return json.loads(json_str)
            
        except Exception:
            # Return minimal structure
            return {
                "question": content.strip()[:500],
                "options": None,
                "mappings": None,
            }
    
    def _fallback_probe(
        self,
        hypothesis: Hypothesis,
        strategy_name: str,
        probe_type: ProbeType
    ) -> ProbePacket:
        """Generate fallback probe if LLM fails."""
        fallback_questions = {
            "morning_routine": "Do you tend to be an early riser who jumps into action, or do you prefer easing into your day?",
            "energy_pattern": "Do you experience consistent energy throughout the day, or do you have natural peaks and valleys?",
            "decision_style": "When making important decisions, do you tend to act quickly or do you need time to process?",
            "first_impression": "How do people typically describe their first impression of you?",
        }
        
        return ProbePacket(
            hypothesis_id=hypothesis.id,
            field=hypothesis.field,
            module=hypothesis.module,
            probe_type=probe_type,
            question=fallback_questions.get(
                strategy_name, 
                f"Tell me about your typical {strategy_name.replace('_', ' ')}..."
            ),
            options=["Option A", "Option B"] if probe_type == ProbeType.BINARY_CHOICE else None,
            strategy_used=strategy_name,
            confidence_mappings=None,
        )
