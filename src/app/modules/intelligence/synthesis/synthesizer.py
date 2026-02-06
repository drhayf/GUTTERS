"""
GUTTERS Profile Synthesizer

Core synthesis engine that combines insights from all calculation modules
using LLM to generate unified profile insights.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_openai import ChatOpenAI

from src.app.core.llm.config import LLMConfig, LLMTier, get_premium_llm

logger = logging.getLogger(__name__)


# Available LLM models
ALLOWED_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-opus-4.5-20251101",
    "qwen/qwen-2.5-72b-instruct:free",
]

DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"


def get_llm() -> ChatOpenAI:
    """
    Get LLM for synthesis operations.

    Uses Claude Sonnet 4.5 (premium tier) for complex reasoning.
    """
    return get_premium_llm()


def get_llm_with_tier(tier: LLMTier = LLMTier.PREMIUM) -> ChatOpenAI:
    """
    Get LLM with specified tier.

    Allows switching to standard tier for module-specific synthesis
    if complexity is lower.
    """
    return LLMConfig.get_llm(tier)


async def get_user_preferred_model(user_id: int, db: AsyncSession) -> str:
    """
    Get user's preferred LLM model or default.
    """
    from ....models.user_profile import UserProfile

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if profile and profile.data:
        preferences = profile.data.get("preferences", {})
        model = preferences.get("llm_model")
        if model and model in ALLOWED_MODELS:
            return model

    return DEFAULT_MODEL


async def update_user_preference(user_id: int, key: str, value: Any, db: AsyncSession) -> None:
    """
    Update a user preference in their profile.
    """
    from ....models.user_profile import UserProfile

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if profile:
        data = profile.data or {}
        if "preferences" not in data:
            data["preferences"] = {}
        data["preferences"][key] = value

        await db.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(data=data, updated_at=dt.datetime.now(dt.UTC))
        )
    else:
        new_profile = UserProfile(user_id=user_id, data={"preferences": {key: value}})
        db.add(new_profile)

    await db.commit()


class ProfileSynthesizer:
    """
    Synthesizes insights across all calculated modules.

    Uses LLM to find cross-system patterns and generate
    unified profile insights.
    """

    def __init__(self, model_id: str = DEFAULT_MODEL, temperature: float = 0.7):
        """
        Initialize synthesizer.
        """
        from ....core.activity.logger import get_activity_logger

        self.model_id = model_id
        self.temperature = temperature
        self._llm: BaseChatModel | None = None
        self.activity_logger = get_activity_logger()

    @property
    def llm(self) -> BaseChatModel:
        """Lazy-load LLM instance."""
        if self._llm is None:
            # If the model matches our premium tier default, use the new config
            if self.model_id == LLMConfig.MODELS[LLMTier.PREMIUM].model_id:
                self._llm = get_premium_llm()
            else:
                from ....core.ai.llm_factory import get_llm

                self._llm = get_llm(self.model_id, self.temperature)
        return self._llm

    async def synthesize_profile(self, user_id: int, db: AsyncSession, trace_id: str | None = None) -> Any:
        """
        Generate synthesis from all available module data.

        Automatically detects which modules have been calculated
        and includes them in synthesis.
        """
        import uuid

        from ....core.events.bus import get_event_bus
        from ....core.memory.active_memory import get_active_memory
        from ....protocol.events import SYNTHESIS_GENERATED
        from ...calculation.registry import CalculationModuleRegistry
        from .schemas import UnifiedProfile

        trace_id = trace_id or str(uuid.uuid4())

        # Initialize
        memory = get_active_memory()
        await memory.initialize()

        # Get user profile
        from ....models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise ValueError(f"Profile not found for user_id {user_id}")

        # Discover which modules have been calculated
        calculated_modules = {}
        registry_modules = CalculationModuleRegistry.get_all_modules()

        for module_name, metadata in registry_modules.items():
            # Check if this module exists in profile data and has no errors
            if (
                module_name in profile.data
                and isinstance(profile.data[module_name], dict)
                and "error" not in profile.data[module_name]
            ):
                calculated_modules[module_name] = {
                    "data": profile.data[module_name],
                    "display_name": metadata.display_name,
                    "description": metadata.description,
                    "version": metadata.version,
                }

        logger.info(f"Synthesizing {len(calculated_modules)} modules for user {user_id}")

        # Build synthesis prompt
        modules_text = self._format_modules_for_llm(calculated_modules)

        # Include Observer Findings if available (keep separate for now as it's not in registry yet)
        # Or better, treat observer as a special case or register it later.
        # For now, sticking to the plan's registry loop, but maybe Observer patterns should be appended.

        prompt = f"""
        You are a cosmic intelligence system integrating multiple metaphysical frameworks.

        Generate a personalized synthesis for this user based on the following modules:

        {modules_text}

        Requirements:
        - Create a cohesive narrative that integrates insights from ALL available modules
        - Focus on practical guidance and self-understanding
        - Highlight unique patterns across systems
        - Be specific and personalized (not generic)
        - Write in second person ("You are...")
        - Aim for 3-4 paragraphs, 400-600 words

        Begin the synthesis now:
        """

        await self.activity_logger.log_activity(
            trace_id=trace_id,
            agent="synthesis.master_synthesizer",
            activity_type="llm_call_started",
            details={"modules": list(calculated_modules.keys())},
        )

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="You are a cosmic intelligence guide combining multiple wisdom traditions."),
                    HumanMessage(content=prompt),
                ]
            )

            master_synthesis = response.content.strip()

            await self.activity_logger.log_llm_call(
                trace_id=trace_id, model_id=self.model_id, prompt=prompt[:500], response=master_synthesis[:500]
            )
        except Exception as e:
            logger.error(f"Master synthesis failed: {e}")
            master_synthesis = "Unable to generate complete synthesis at this time."

        # Cache in Active Memory
        themes = self._extract_themes(master_synthesis)
        modules_included = list(calculated_modules.keys())

        await memory.set_master_synthesis(
            user_id,
            master_synthesis,
            themes=themes,
            modules_included=modules_included,
            count_confirmed_theories=0,  # Simplified for now
        )

        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish(
            SYNTHESIS_GENERATED,
            {
                "user_id": user_id,
                "modules": modules_included,
                "patterns_detected": 0,
                "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            },
        )

        result = UnifiedProfile(
            user_id=user_id,
            synthesis=master_synthesis,
            themes=themes,
            modules_included=modules_included,
            patterns=[],
            model_used=self.model_id,
            generated_at=dt.datetime.now(dt.UTC),
            confidence=self._calculate_confidence(calculated_modules),
        )

        await self._store_synthesis(user_id, result, db)

        return result

    def _format_modules_for_llm(self, modules: dict) -> str:
        """
        Format module data for LLM prompt.
        Creates structured sections for each module.
        """
        import json

        sections = []

        for name, info in modules.items():
            # Format module data (truncate if too large)
            data_str = json.dumps(info["data"], indent=2)
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "\n... (truncated)"

            sections.append(
                f"## {info['display_name']} (v{info['version']})\n{info['description']}\n\nData:\n{data_str}"
            )

        return "\n\n".join(sections)

    def _calculate_confidence(self, modules: dict) -> float:
        """
        Calculate synthesis confidence based on modules available.
        More modules = higher confidence. Cap at 0.95.
        """
        from ...calculation.registry import CalculationModuleRegistry

        total_possible = len(CalculationModuleRegistry.get_all_modules())
        calculated = len(modules)

        if total_possible == 0:
            return 0.5

        base = (calculated / total_possible) * 0.95
        return min(base, 0.95)

    def _build_master_synthesis_prompt(self, astro: str, hd: str, num: str, observer: str, hypotheses: str = "") -> str:
        sections = []
        if astro:
            sections.append(f"**Astrological Insights:**\n{astro}")
        if hd:
            sections.append(f"**Human Design Insights:**\n{hd}")
        if num:
            sections.append(f"**Numerological Insights:**\n{num}")
        if observer:
            sections.append(f"**Detected Patterns:**\n{observer}")
        if hypotheses:
            sections.append(f"**Confirmed Self-Patterns & Theories:**\n{hypotheses}")

        combined = "\n\n".join(sections)
        return (
            "Synthesize these insights into a cohesive cosmic profile (8-10 sentences):\n\n"
            f"{combined}\n\n"
            "Requirements: Integrate, highlight themes, write in second person, provide guidance."
        )

    def _extract_key_insights(self, module_name: str, data: dict):
        from .schemas import ModuleInsights

        key_points = []
        if module_name == "astrology":
            for p in data.get("planets", [])[:3]:
                key_points.append(f"{p.get('name')}: {p.get('sign')}")
        elif module_name == "human_design":
            key_points.append(f"Type: {data.get('type')}")
            key_points.append(f"Strategy: {data.get('strategy')}")
        return ModuleInsights(module_name=module_name, key_points=key_points, raw_data=data)

    def _extract_themes(self, text: str) -> list[str]:
        keywords = ["leadership", "creativity", "communication", "intuition", "structure"]
        return [k for k in keywords if k in text.lower()][:5]

    def _extract_patterns(self, insights: dict) -> list:
        from .schemas import SynthesisPattern

        patterns = []
        # Simplified pattern logic for performance
        if "astrology" in insights and "human_design" in insights:
            patterns.append(
                SynthesisPattern(
                    pattern_name="Synergy Detected",
                    modules_involved=["astrology", "human_design"],
                    description="Your placements align between systems.",
                    confidence=0.8,
                )
            )
        return patterns

    async def _store_synthesis(self, user_id: int, synthesis: Any, db: AsyncSession) -> None:
        from ....models.user_profile import UserProfile

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile:
            data = profile.data or {}
            data["synthesis"] = synthesis.model_dump(mode="json")
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(data=data, updated_at=dt.datetime.now(dt.UTC))
            )
            await db.commit()
