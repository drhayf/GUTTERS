"""
Component generator for Generative UI.

AI-powered component generation based on conversation context.
"""

from typing import Optional, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
import json
import uuid
import logging
from datetime import datetime, timezone as dt_timezone

from src.app.core.llm.config import get_premium_llm
from .models import (
    ComponentSpec,
    ComponentType,
    HypothesisProbeSpec,
    MoodSliderSpec,
    MultiSliderSpec,
    VoteComponentSpec,
    PatternConfirmationSpec,
    ChecklistItem,
    VoteOption,
    SliderConfig,
)

logger = logging.getLogger(__name__)


class ComponentGenerator:
    """
    Generates interactive UI components based on conversation context.

    Uses LLM to decide when to show a component and what it should contain.
    USES PREMIUM LLM TIER (Sonnet 4.5) for high-fidelity decisions.
    """

    def __init__(self):
        # CRITICAL: Use premium LLM for component decisions
        self.llm = get_premium_llm()

    async def should_generate_component(
        self, message: str, conversation_history: List[dict], context: dict
    ) -> tuple[bool, Optional[ComponentType]]:
        """
        Decide if a UI component should be generated.

        Returns:
            (should_generate, component_type)

        Examples:
            "I felt anxious today" → (True, MOOD_SLIDER)
            "What's my sun sign?" → (False, None)
        """
        prompt = f"""Analyze this conversation and determine if an interactive UI component would be helpful.

User message: "{message}"

Context:
- User has ongoing hypotheses that need testing
- Observer is tracking patterns
- Journal entries benefit from structured mood data

Should we show an interactive component? If yes, which type?

Component types:
- hypothesis_probe: Gather data to test a hypothesis
- mood_slider: Rate a single emotional state (1-10)
- multi_slider: Rate multiple related states (e.g. Mood, Energy, Anxiety) -> PREFER THIS for complex feelings
- vote_component: Binary choice (yes/no, agree/disagree)
- pattern_confirmation: Confirm an observed pattern
- symptom_checklist: List of symptoms to check

Respond with JSON:
{{
    "should_generate": true/false,
    "component_type": "multi_slider" or null,
    "reasoning": "Why this component would be helpful"
}}

Only suggest components when they would genuinely improve data collection or engagement.
Don't suggest components for simple factual questions.
"""

        try:
            response = await self.llm.ainvoke(
                [SystemMessage(content="You are an expert at UX and data collection."), HumanMessage(content=prompt)]
            )

            # Helper to clean response content if it contains markdown code blocks
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            should_gen = data.get("should_generate", False)
            comp_type_str = data.get("component_type")

            if should_gen and comp_type_str:
                # Validate against enum
                try:
                    comp_type = ComponentType(comp_type_str)
                    return True, comp_type
                except ValueError:
                    logger.warning(f"LLM suggested invalid component type: {comp_type_str}")
                    return False, None

            return False, None

        except Exception as e:
            # Logic error or LLM failure -> graceful degradation to text only
            logger.error(f"[ComponentGenerator] Decision failed: {e}")
            return False, None

    async def generate_mood_slider(self, message: str, context: dict) -> ComponentSpec:
        """Generate a single mood slider component."""

        component_id = str(uuid.uuid4())

        return ComponentSpec(
            component_id=component_id,
            component_type=ComponentType.MOOD_SLIDER,
            mood_slider=MoodSliderSpec(
                question="How would you rate your mood right now?",
                slider_config=SliderConfig(
                    id="mood",
                    min_value=1,
                    max_value=10,
                    labels={"1": "Terrible", "5": "Okay", "10": "Amazing"},
                    emoji_scale={1: "😢", 3: "😟", 5: "😐", 7: "🙂", 10: "😄"},
                ),
                context=f'You mentioned: "{message}"',
            ),
            context_message="I'd like to understand your emotional state better.",
        )

    async def generate_multi_slider(self, message: str, context: dict) -> ComponentSpec:
        """Generate a multi-slider component (Mood, Energy, Anxiety)."""

        component_id = str(uuid.uuid4())

        sliders = [
            SliderConfig(
                id="mood",
                label="Mood",
                min_value=1,
                max_value=10,
                min_label="Terrible",
                max_label="Amazing",
                emoji_scale={1: "😢", 5: "😐", 10: "😄"},
            ),
            SliderConfig(
                id="energy",
                label="Energy",
                min_value=1,
                max_value=10,
                min_label="Exhausted",
                max_label="Energized",
                emoji_scale={1: "💤", 5: "😐", 10: "🔥"},
            ),
            SliderConfig(
                id="anxiety",
                label="Anxiety",
                min_value=1,
                max_value=10,
                min_label="Calm",
                max_label="Panic",
                emoji_scale={1: "😌", 5: "😐", 10: "😱"},
            ),
        ]

        return ComponentSpec(
            component_id=component_id,
            component_type=ComponentType.MULTI_SLIDER,
            multi_slider=MultiSliderSpec(
                question="How are you feeling right now?", sliders=sliders, context=f'You mentioned: "{message}"'
            ),
            context_message="I'd like to get a clearer picture of your current state.",
        )

    async def generate_hypothesis_probe(
        self, hypothesis_id: str, hypothesis_text: str, symptoms: List[str]
    ) -> ComponentSpec:
        """Generate a hypothesis probe component."""

        component_id = str(uuid.uuid4())

        items = [
            ChecklistItem(id=f"symptom_{i}", label=symptom, category="physical" if i < 3 else "emotional")
            for i, symptom in enumerate(symptoms)
        ]

        return ComponentSpec(
            component_id=component_id,
            component_type=ComponentType.HYPOTHESIS_PROBE,
            hypothesis_probe=HypothesisProbeSpec(
                hypothesis_id=hypothesis_id,
                hypothesis_text=hypothesis_text,
                question="Have you experienced any of these in the last 3 days?",
                items=items,
                allow_other=True,
                other_placeholder="Any other symptoms...",
            ),
            context_message=f"I'm testing a hypothesis: {hypothesis_text}",
        )

    async def generate_pattern_confirmation(
        self, pattern_id: str, pattern_description: str, confidence: float, evidence: List[str]
    ) -> ComponentSpec:
        """Generate a pattern confirmation component."""

        component_id = str(uuid.uuid4())

        return ComponentSpec(
            component_id=component_id,
            component_type=ComponentType.PATTERN_CONFIRMATION,
            pattern_confirmation=PatternConfirmationSpec(
                pattern_id=pattern_id, pattern_description=pattern_description, confidence=confidence, evidence=evidence
            ),
            context_message="I've noticed a recurring pattern.",
        )

    async def generate_vote(self, question: str, options: List[dict]) -> ComponentSpec:
        """Generate a vote component."""

        component_id = str(uuid.uuid4())

        vote_options = [
            VoteOption(id=opt["id"], label=opt["label"], description=opt.get("description"), emoji=opt.get("emoji"))
            for opt in options
        ]

        return ComponentSpec(
            component_id=component_id,
            component_type=ComponentType.VOTE_COMPONENT,
            vote=VoteComponentSpec(question=question, options=vote_options, allow_multiple=False),
        )
