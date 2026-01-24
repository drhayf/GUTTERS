"""
GUTTERS Profile Synthesizer

Core synthesis engine that combines insights from all calculation modules
using LLM to generate unified profile insights.
"""

from __future__ import annotations

import logging
import datetime as dt
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from langchain_core.language_models import BaseChatModel

from src.app.core.llm.config import get_premium_llm, LLMTier, LLMConfig

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
            .values(data=data, updated_at=dt.datetime.now(dt.timezone.utc))
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
    def llm(self) -> "BaseChatModel":
        """Lazy-load LLM instance."""
        if self._llm is None:
            # If the model matches our premium tier default, use the new config
            if self.model_id == LLMConfig.MODELS[LLMTier.PREMIUM].model_id:
                self._llm = get_premium_llm()
            else:
                from ....core.ai.llm_factory import get_llm

                self._llm = get_llm(self.model_id, self.temperature)
        return self._llm

    async def synthesize_profile(self, user_id: int, db: AsyncSession, trace_id: str | None = None):
        """
        Generate hierarchical synthesis from all available data.
        """
        import uuid

        # Defer imports to avoid circular dependencies during collection
        from .module_synthesis import ModuleSynthesizer
        from .schemas import UnifiedProfile
        from ....core.memory.active_memory import get_active_memory
        from ...intelligence.observer.storage import ObserverFindingStorage
        from ....core.events.bus import get_event_bus
        from ....protocol.events import SYNTHESIS_GENERATED

        trace_id = trace_id or str(uuid.uuid4())

        # Initialize
        module_synthesizer = ModuleSynthesizer(self.llm)
        memory = get_active_memory()
        await memory.initialize()

        # STEP 1: Fetch module data
        astro_data = await memory.get_module_output(user_id, "astrology")
        hd_data = await memory.get_module_output(user_id, "human_design")
        num_data = await memory.get_module_output(user_id, "numerology")

        # STEP 2: Generate module-specific syntheses
        astro_synthesis = await module_synthesizer.synthesize_astrology(astro_data) if astro_data else ""
        hd_synthesis = await module_synthesizer.synthesize_human_design(hd_data) if hd_data else ""
        num_synthesis = await module_synthesizer.synthesize_numerology(num_data) if num_data else ""

        # STEP 3: Fetch Observer findings
        observer_storage = ObserverFindingStorage()
        findings = await observer_storage.get_findings(user_id, min_confidence=0.7)

        # STEP 4: Generate Observer pattern narrative
        observer_synthesis = await module_synthesizer.synthesize_observer_patterns(findings) if findings else ""

        # STEP 4.5: Fetch Confirmed Theory Hypotheses
        from ..hypothesis.storage import HypothesisStorage

        hypothesis_storage = HypothesisStorage()
        confirmed_hypotheses = await hypothesis_storage.get_confirmed_hypotheses(user_id)

        hypotheses_text = ""
        if confirmed_hypotheses:
            hypotheses_text = "\n".join(
                [f"- {h.claim} (confidence: {h.confidence:.0%})" for h in confirmed_hypotheses[:5]]
            )

        # STEP 5: Combine into master synthesis
        master_prompt = self._build_master_synthesis_prompt(
            astro_synthesis, hd_synthesis, num_synthesis, observer_synthesis, hypotheses_text
        )

        await self.activity_logger.log_activity(
            trace_id=trace_id,
            agent="synthesis.master_synthesizer",
            activity_type="llm_call_started",
            details={"modules": ["astrology", "human_design", "numerology", "observer"]},
        )

        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="You are a cosmic intelligence guide combining multiple wisdom traditions."),
                    HumanMessage(content=master_prompt),
                ]
            )

            master_synthesis = response.content.strip()

            await self.activity_logger.log_llm_call(
                trace_id=trace_id, model_id=self.model_id, prompt=master_prompt[:500], response=master_synthesis[:500]
            )
        except Exception as e:
            logger.error(f"Master synthesis failed: {e}")
            master_synthesis = "Unable to generate complete synthesis at this time."

        # STEP 6: Cache in Active Memory
        modules_included = []
        if astro_data:
            modules_included.append("astrology")
        if hd_data:
            modules_included.append("human_design")
        if num_data:
            modules_included.append("numerology")
        if findings:
            modules_included.append("observer")

        themes = self._extract_themes(master_synthesis)

        await memory.set_master_synthesis(
            user_id,
            master_synthesis,
            themes=themes,
            modules_included=modules_included,
            count_confirmed_theories=len(confirmed_hypotheses),
        )

        # STEP 7: Publish event
        event_bus = get_event_bus()
        await event_bus.publish(
            SYNTHESIS_GENERATED,
            {
                "user_id": user_id,
                "modules": modules_included,
                "patterns_detected": len(findings),
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
        )

        # Build patterns and return
        module_insights = {}
        if astro_data:
            module_insights["astrology"] = self._extract_key_insights("astrology", astro_data)
        if hd_data:
            module_insights["human_design"] = self._extract_key_insights("human_design", hd_data)

        patterns = self._extract_patterns(module_insights)

        result = UnifiedProfile(
            user_id=user_id,
            synthesis=master_synthesis,
            themes=themes,
            modules_included=modules_included,
            patterns=patterns,
            model_used=self.model_id,
            generated_at=dt.datetime.now(dt.timezone.utc),
        )

        await self._store_synthesis(user_id, result, db)

        return result

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
        return f"Synthesize these insights into a cohesive cosmic profile (8-10 sentences):\n\n{combined}\n\nRequirements: Integrate, highlight themes, write in second person, provide guidance."

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
                .values(data=data, updated_at=dt.datetime.now(dt.timezone.utc))
            )
            await db.commit()
