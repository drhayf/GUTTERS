"""
GUTTERS Profile Synthesizer

Core synthesis engine that combines insights from all calculation modules
using LLM to generate unified profile insights.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.ai.llm_factory import get_llm
from ....core.activity.logger import get_activity_logger
from ....models.user_profile import UserProfile
from ...registry import ModuleRegistry
from .schemas import ModuleInsights, SynthesisPattern, UnifiedProfile

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


# Available LLM models
ALLOWED_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-opus-4.5-20251101",
    "qwen/qwen-2.5-72b-instruct:free",
]

DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


async def get_user_preferred_model(user_id: int, db: AsyncSession) -> str:
    """
    Get user's preferred LLM model or default.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Model identifier string
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile and profile.data:
        preferences = profile.data.get("preferences", {})
        model = preferences.get("llm_model")
        if model and model in ALLOWED_MODELS:
            return model
    
    return DEFAULT_MODEL


async def update_user_preference(
    user_id: int,
    key: str,
    value: Any,
    db: AsyncSession
) -> None:
    """
    Update a user preference in their profile.
    
    Args:
        user_id: User ID
        key: Preference key (e.g., "llm_model")
        value: Preference value
        db: Database session
    """
    from sqlalchemy.dialects.postgresql import insert
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile:
        # Update existing profile's preferences
        data = profile.data or {}
        if "preferences" not in data:
            data["preferences"] = {}
        data["preferences"][key] = value
        
        await db.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(data=data, updated_at=datetime.utcnow())
        )
    else:
        # Create new profile with preference
        new_profile = UserProfile(
            user_id=user_id,
            data={"preferences": {key: value}}
        )
        db.add(new_profile)
    
    await db.commit()


class ProfileSynthesizer:
    """
    Synthesizes insights across all calculated modules.
    
    Uses LLM to find cross-system patterns and generate
    unified profile insights.
    """
    
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        temperature: float = 0.7
    ):
        """
        Initialize synthesizer.
        
        Args:
            model_id: LLM model to use
            temperature: Sampling temperature
        """
        self.model_id = model_id
        self.temperature = temperature
        self._llm: BaseChatModel | None = None
        self.activity_logger = get_activity_logger()
    
    @property
    def llm(self) -> "BaseChatModel":
        """Lazy-load LLM instance."""
        if self._llm is None:
            self._llm = get_llm(self.model_id, self.temperature)
        return self._llm
    
    async def synthesize_profile(
        self,
        user_id: int,
        db: AsyncSession,
        trace_id: str | None = None
    ) -> UnifiedProfile:
        """
        Create unified synthesis across all modules.
        
        Steps:
        1. Get all calculated modules for user
        2. Extract key insights from each
        3. Use LLM to find cross-system patterns
        4. Generate unified insights
        5. Return structured synthesis
        
        Args:
            user_id: User to synthesize for
            db: Database session
            trace_id: Optional trace ID for logging
            
        Returns:
            UnifiedProfile with synthesis
        """
        import uuid
        trace_id = trace_id or str(uuid.uuid4())
        
        # 1. Get calculated modules
        calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
        
        if not calculated:
            logger.warning(f"No calculated modules for user {user_id}")
            return UnifiedProfile(
                user_id=user_id,
                modules_included=[],
                synthesis="No cosmic profiles have been calculated yet. Submit your birth data to begin.",
                themes=[],
                patterns=[],
                model_used=self.model_id,
            )
        
        # 2. Extract insights from each module
        module_insights: dict[str, ModuleInsights] = {}
        for module_name in calculated:
            data = await ModuleRegistry.get_user_profile_data(user_id, db, module_name)
            insights = self._extract_key_insights(module_name, data)
            module_insights[module_name] = insights
        
        # 3. Build synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(module_insights)
        
        # 4. Log activity start
        await self.activity_logger.log_activity(
            trace_id=trace_id,
            agent="synthesis.synthesizer",
            activity_type="llm_call_started",
            details={
                "model": self.model_id,
                "purpose": "profile_synthesis",
                "modules": calculated,
            }
        )
        
        # 5. Call LLM for synthesis
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            system_prompt = (
                "You are a master synthesist who finds profound connections across wisdom traditions. "
                "Your insights are warm, practical, and deeply personal. You speak directly to the person, "
                "helping them understand how different systems paint a complete picture of who they are."
            )
            
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=synthesis_prompt)
            ])
            
            synthesis_text = response.content
            
            # Log successful call
            await self.activity_logger.log_llm_call(
                trace_id=trace_id,
                model_id=self.model_id,
                prompt=synthesis_prompt[:500],
                response=synthesis_text[:500] if isinstance(synthesis_text, str) else str(synthesis_text)[:500],
            )
            
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            synthesis_text = self._fallback_synthesis(module_insights)
            
            await self.activity_logger.log_activity(
                trace_id=trace_id,
                agent="synthesis.synthesizer",
                activity_type="llm_call_failed",
                details={"error": str(e)}
            )
        
        # 6. Extract themes and patterns
        themes = self._extract_themes(synthesis_text if isinstance(synthesis_text, str) else str(synthesis_text))
        patterns = self._extract_patterns(module_insights)
        
        # 7. Build and return result
        result = UnifiedProfile(
            user_id=user_id,
            modules_included=calculated,
            synthesis=synthesis_text if isinstance(synthesis_text, str) else str(synthesis_text),
            themes=themes,
            patterns=patterns,
            model_used=self.model_id,
        )
        
        # 8. Store synthesis in profile
        await self._store_synthesis(user_id, result, db)
        
        return result
    
    def _extract_key_insights(self, module_name: str, data: dict) -> ModuleInsights:
        """
        Extract key insights from module data.
        
        Each module has different structure, so we need
        module-specific extraction logic.
        
        Args:
            module_name: Name of the module
            data: Module's profile data
            
        Returns:
            ModuleInsights with key points
        """
        key_points: list[str] = []
        
        if module_name == "astrology":
            # Extract Sun, Moon, Rising
            if "planets" in data:
                planets = data.get("planets", [])
                sun = next((p for p in planets if p.get("name") == "Sun"), None)
                moon = next((p for p in planets if p.get("name") == "Moon"), None)
                
                if sun:
                    key_points.append(f"Sun in {sun.get('sign', 'Unknown')} (House {sun.get('house', '?')})")
                if moon:
                    key_points.append(f"Moon in {moon.get('sign', 'Unknown')} (House {moon.get('house', '?')})")
            
            if "ascendant" in data:
                asc = data["ascendant"]
                key_points.append(f"Rising Sign: {asc.get('sign', 'Unknown')}")
        
        elif module_name == "human_design":
            # Extract Type, Strategy, Authority
            hd_type = data.get("type", "Unknown")
            strategy = data.get("strategy", "Unknown")
            authority = data.get("authority", "Unknown")
            profile = data.get("profile", "Unknown")
            
            key_points.extend([
                f"Type: {hd_type}",
                f"Strategy: {strategy}",
                f"Authority: {authority}",
                f"Profile: {profile}",
            ])
        
        elif module_name == "numerology":
            # Extract Life Path, Expression, Soul Urge
            life_path = data.get("life_path", {})
            expression = data.get("expression", {})
            soul_urge = data.get("soul_urge", {})
            
            if life_path:
                key_points.append(f"Life Path: {life_path.get('number', '?')}")
            if expression:
                key_points.append(f"Expression: {expression.get('number', '?')}")
            if soul_urge:
                key_points.append(f"Soul Urge: {soul_urge.get('number', '?')}")
        
        else:
            # Generic extraction for unknown modules
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    key_points.append(f"{key}: {value}")
                elif isinstance(value, dict) and "value" in value:
                    key_points.append(f"{key}: {value['value']}")
        
        return ModuleInsights(
            module_name=module_name,
            key_points=key_points[:10],  # Limit to 10 points
            raw_data=data
        )
    
    def _build_synthesis_prompt(self, module_insights: dict[str, ModuleInsights]) -> str:
        """
        Build LLM prompt for synthesis.
        
        Args:
            module_insights: Extracted insights from each module
            
        Returns:
            Formatted prompt string
        """
        insights_text = ""
        for name, insights in module_insights.items():
            insights_text += f"\n## {name.replace('_', ' ').title()}\n"
            for point in insights.key_points:
                insights_text += f"- {point}\n"
        
        prompt = f"""Synthesize insights across multiple wisdom traditions for this person.

**AVAILABLE INSIGHTS:**
{insights_text}

**YOUR TASK:**
1. Find the through-line connecting all systems - what's the core essence of this person?
2. Identify where systems confirm each other (e.g., "Your Leo Sun and Projector type both...")
3. Note where they add nuance or create interesting tensions
4. Reconcile any apparent contradictions
5. Provide warm, practical guidance

**OUTPUT:**
Write a warm, personal synthesis (600-900 words) that shows how these systems
paint a complete picture of this person's design. Speak directly to them using "you"
language. Be specific and insightful, not generic.

Begin your synthesis now:"""
        
        return prompt
    
    def _extract_themes(self, synthesis_text: str) -> list[str]:
        """
        Extract key themes from synthesis text.
        
        Args:
            synthesis_text: LLM-generated synthesis
            
        Returns:
            List of theme strings
        """
        # Simple keyword extraction for now
        # Could be enhanced with NLP
        theme_keywords = [
            "leadership", "creativity", "communication", "intuition",
            "structure", "freedom", "service", "transformation",
            "wisdom", "power", "harmony", "independence",
            "nurturing", "vision", "discipline", "adventure"
        ]
        
        text_lower = synthesis_text.lower()
        found_themes = [
            theme for theme in theme_keywords
            if theme in text_lower
        ]
        
        return found_themes[:5]  # Return top 5
    
    def _extract_patterns(
        self,
        module_insights: dict[str, ModuleInsights]
    ) -> list[SynthesisPattern]:
        """
        Identify cross-system patterns.
        
        Args:
            module_insights: Insights from each module
            
        Returns:
            List of identified patterns
        """
        patterns: list[SynthesisPattern] = []
        
        # Check for fire sign + Generator/MG pattern
        has_fire = False
        has_generator = False
        
        if "astrology" in module_insights:
            astro = module_insights["astrology"]
            fire_signs = ["Aries", "Leo", "Sagittarius"]
            for point in astro.key_points:
                if any(sign in point for sign in fire_signs):
                    has_fire = True
                    break
        
        if "human_design" in module_insights:
            hd = module_insights["human_design"]
            for point in hd.key_points:
                if "Generator" in point or "Manifesting Generator" in point:
                    has_generator = True
                    break
        
        if has_fire and has_generator:
            patterns.append(SynthesisPattern(
                pattern_name="Energetic Powerhouse",
                modules_involved=["astrology", "human_design"],
                description="Fire sign energy combined with Generator sacral power creates sustained creative force",
                confidence=0.8
            ))
        
        return patterns
    
    def _fallback_synthesis(
        self,
        module_insights: dict[str, ModuleInsights]
    ) -> str:
        """
        Generate fallback synthesis when LLM fails.
        
        Args:
            module_insights: Insights from each module
            
        Returns:
            Template-based synthesis
        """
        parts = ["Your cosmic profile reveals a unique design across multiple wisdom traditions:\n"]
        
        for name, insights in module_insights.items():
            parts.append(f"\n**{name.replace('_', ' ').title()}:** ")
            parts.append(", ".join(insights.key_points[:3]))
        
        parts.append("\n\nFor a deeper synthesis, please try again when the AI service is available.")
        
        return "".join(parts)
    
    async def _store_synthesis(
        self,
        user_id: int,
        synthesis: UnifiedProfile,
        db: AsyncSession
    ) -> None:
        """
        Store synthesis result in user profile.
        
        Args:
            user_id: User ID
            synthesis: Synthesis result
            db: Database session
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            data = profile.data or {}
            data["synthesis"] = synthesis.model_dump(mode="json")
            
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(data=data, updated_at=datetime.utcnow())
            )
            await db.commit()
