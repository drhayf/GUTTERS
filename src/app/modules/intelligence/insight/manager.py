import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.llm.config import get_premium_llm
from src.app.models.insight import PromptPhase, PromptStatus, ReflectionPrompt
from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import QuestCategory, QuestDifficulty, QuestSource
from src.app.modules.infrastructure.push.service import NotificationService
from src.app.modules.intelligence.observer.storage import ObserverFindingStorage

from .schemas import TriggerContext

logger = logging.getLogger(__name__)


class InsightManager:
    """
    The Nervous System: Proactive Insight & Reflection Engine.

    Bridges passive observation (Observer) with active user interaction (Journal/Quest).
    """

    def __init__(self):
        self.llm = get_premium_llm()
        self.notification_service = NotificationService()
        self.observer_storage = ObserverFindingStorage()

    async def evaluate_cosmic_triggers(
        self, user_id: int, cosmic_data: Dict[str, Any], db: AsyncSession
    ) -> List[ReflectionPrompt]:
        """
        Evaluate if current cosmic/system state triggers any personalized prompts.

        Args:
            user_id: User ID
            cosmic_data: Current state (e.g. {'kp_index': 7, 'moon_phase': 'Full', 'transits': [...]})
            db: Database session

        Returns:
            List of created ReflectionPrompt objects
        """
        logger.info(f"Evaluating triggers for user {user_id} with data {cosmic_data}")

        # 1. Fetch User Patterns (Observer Findings)
        findings = await self.observer_storage.get_findings(user_id, min_confidence=0.6)

        prompts = []

        # 2. Check Triggers logic

        # --- Solar Check ---
        kp_index = float(cosmic_data.get("kp_index", 0))
        if kp_index >= 5:  # Storm condition
            # Phase Determination
            # For volatile events like Solar, we assume PEAK if storm is active.
            # Ideally we track history to see if it just started or is ending for INTEGRATION.
            # Simplified: Active Storm = PEAK.

            phase = PromptPhase.PEAK
            trigger_ctx = TriggerContext(
                source_type="cosmic_event", metric="kp_index", value=kp_index, timestamp=datetime.now(UTC)
            )

            # Match against findings
            relevant_findings = [f for f in findings if f.get("pattern_type") == "solar_symptom"]

            if relevant_findings:
                for finding in relevant_findings:
                    # Anti-Spam Check (Topic: solar_sensitivity)
                    if not await self._should_trigger(user_id, "solar_sensitivity", phase, db):
                        logger.info("Skipping Solar trigger due to cooldown")
                        continue

                    prompt = await self._create_prompt(user_id, finding, trigger_ctx, phase, "solar_sensitivity", db)
                    if prompt:
                        prompts.append(prompt)

        # --- Lunar Check ---
        moon_phase = cosmic_data.get("moon_phase", "")  # e.g. 'Full', 'New'
        # Assume cosmic_data includes 'approaching_phase' if we have predictive logic upstream
        # Or we calculate it.
        # For this implementation, I'll rely on explicit 'event_phase' in cosmic_data if available,
        # or defaults.

        # Example: Input might contain {'moon_phase': 'Full', 'phase_type': 'peak'}
        # or {'approaching_moon': 'New', 'hours_until': 24, 'phase_type': 'anticipation'}

        lunar_event_type = cosmic_data.get("moon_event_type", "none")  # anticipation, peak, integration

        if lunar_event_type != "none":
            phase = PromptPhase(lunar_event_type)  # Map string to Enum

            trigger_val = cosmic_data.get("moon_phase_name", moon_phase)

            trigger_ctx = TriggerContext(
                source_type="cosmic_event", metric="moon_phase", value=trigger_val, timestamp=datetime.now(UTC)
            )

            relevant_findings = [f for f in findings if f.get("pattern_type") == "lunar_phase"]
            # Filter related to specific phase if possible, but pattern just says "during {phase}"
            # We assume if user has pattern for 'Full Moon', we trigger on Anticipation/Peak/Integration of Full Moon.

            target_moon = trigger_val

            match = next((f for f in relevant_findings if f.get("phase", "").lower() in target_moon.lower()), None)

            if match:
                if await self._should_trigger(user_id, "lunar_pattern", phase, db):
                    prompt = await self._create_prompt(user_id, match, trigger_ctx, phase, "lunar_pattern", db)
                    if prompt:
                        prompts.append(prompt)

        return prompts

    async def _should_trigger(self, user_id: int, topic: str, phase: PromptPhase, db: AsyncSession) -> bool:
        """
        Anti-Spam & Cooldown Check.

        Rules:
        1. No prompts with same topic in last 18 hours.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=18)

        stmt = select(ReflectionPrompt).where(
            ReflectionPrompt.user_id == user_id, ReflectionPrompt.topic == topic, ReflectionPrompt.created_at >= cutoff
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        return existing is None

    async def _create_prompt(
        self, user_id: int, finding: Dict, trigger: TriggerContext, phase: PromptPhase, topic: str, db: AsyncSession
    ) -> Optional[ReflectionPrompt]:
        """Generate prompt via LLM, save to DB, and notify."""

        # 1. Generate Text
        prompt_text = await self.generate_prompt_text(finding, trigger, phase)

        # 2. Save
        expires = datetime.now(UTC) + timedelta(hours=24)  # Default expiry

        db_prompt = ReflectionPrompt(
            user_id=user_id,
            prompt_text=prompt_text,
            topic=topic,
            trigger_context=trigger.model_dump(mode="json"),
            event_phase=phase,
            status=PromptStatus.PENDING,
            expires_at=expires,
        )
        db.add(db_prompt)
        await db.commit()
        await db.refresh(db_prompt)

        # 3. Notify
        await self.notification_service.send_notification(
            user_id,
            title=f"Cosmic Reflection ({phase.value.title()})",
            body=prompt_text,
            data={"url": f"/journal/new?prompt_id={db_prompt.id}"},  # Deep link
            db=db,
        )

        # 3.5 Emit Event
        await self._emit_prompt_event(user_id, db_prompt.id, topic)

        # 4. PROACTIVE QUEST: If confidence is high, trigger a companion quest
        if finding.get("confidence", 0) >= 0.8:
            try:
                await self.generate_quest_from_insight(user_id, finding, trigger, db_prompt.id, db)
            except Exception as e:
                logger.error(f"Failed to trigger proactive quest: {e}")

        return db_prompt

    async def _emit_prompt_event(self, user_id: int, prompt_id: int, topic: str):
        """Emit REFLECTION_PROMPT_GENERATED event."""
        from src.app.core.events.bus import get_event_bus
        from src.app.protocol import events

        try:
            bus = get_event_bus()
            await bus.publish(
                events.REFLECTION_PROMPT_GENERATED,
                {"prompt_id": prompt_id, "user_id": user_id, "topic": topic},
                user_id=str(user_id),
            )
        except Exception as e:
            logger.error(f"Failed to emit prompt event: {e}")

    async def generate_quest_from_insight(
        self, user_id: int, finding: Dict, trigger: TriggerContext, prompt_id: int, db: AsyncSession
    ):
        """Use LLM to generate a specific, actionable Quest based on an insight."""
        logger.info(f"Triggering proactive quest for user {user_id} based on insight {prompt_id}")

        system_prompt = (
            "You are the System from 'Solo Leveling'. You provide 'Daily Quests' to help users evolve. "
            "Generate a specific, actionable quest based on a cosmic insight."
        )

        user_msg = f"""
        Insight Data:
        - Pattern: {finding.get("finding")}
        - Cosmic Event: {trigger.metric} = {trigger.value}

        Requirements:
        1. Title: Short, gamified (e.g. "Preparation for the Geomagnetic Storm").
        2. Description: 1-2 sentences of instruction.
        3. Difficulty: easy, medium, hard, or elite.

        Return JSON format: {{"title": "...", "description": "...", "difficulty": "..."}}
        """

        try:
            # Note: Using premium LLM for better JSON adherence
            response = await self.llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
            data = json.loads(response.content.strip())

            # Map string difficulty to Enum
            diff_map = {
                "easy": QuestDifficulty.EASY,
                "medium": QuestDifficulty.MEDIUM,
                "hard": QuestDifficulty.HARD,
                "elite": QuestDifficulty.ELITE,
            }
            difficulty = diff_map.get(data.get("difficulty", "easy").lower(), QuestDifficulty.EASY)

            await QuestManager.create_quest(
                db=db,
                user_id=user_id,
                title=data.get("title", "New Quest"),
                description=data.get("description", "A quest from the stars."),
                category=QuestCategory.REFLECTION,
                difficulty=difficulty,
                source=QuestSource.AGENT,
                insight_id=prompt_id,
            )
            logger.info(f"Proactive quest created for user {user_id}")

        except Exception as e:
            logger.error(f"LLM Quest Gen failed: {e}")

    async def generate_prompt_text(self, finding: Dict, trigger: TriggerContext, phase: PromptPhase) -> str:
        """Use LLM to generate context-aware, evidence-based prompt."""

        system_prompt = (
            "You are an empathetic, insightful cosmic guide. "
            "Generate a short (1-2 sentences) reflection question for the user based on "
            "their historical patterns and current cosmic events."
        )

        user_msg = f"""
        Context:
        - Event Phase: {phase.value.upper()}
        - Trigger: {trigger.metric} = {trigger.value}
        - User Pattern Evidence: {finding.get("finding")} (Confidence: {finding.get("confidence", 0):.2f})

        Instructions:
        1. Reference the pattern evidence implicitly or explicitly (e.g. "You often report...", "History shows...").
        2. Tailor to the phase:
           - Anticipation: Preparation, looking ahead.
           - Peak: Checking in, grounding.
           - Integration: Recovery, reflection.
        3. Be gentle but direct.
        """

        try:
            response = await self.llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM Prompt Gen failed: {e}")
            return f"We noticed {trigger.metric} is active. How are you feeling?"

    async def cleanup_expired_prompts(self, db: AsyncSession):
        """Dismiss expired prompts."""
        # Assuming we can execute update logic
        # SQLA bulk update ...
        pass  # Placeholder for now, typically run via cron

    async def generate_period_transition_prompt(
        self, user_id: int, payload: Dict, db: AsyncSession
    ) -> None:
        """
        Generate a reflection prompt when user transitions to a new 52-day planetary period.

        Uses LLM to create personalized transition guidance based on:
        - The planet/card they're leaving
        - The planet/card they're entering
        - Their historical patterns during similar periods

        Args:
            user_id: User transitioning periods
            payload: Event data with old_planet, new_planet, old_card, new_card
            db: Database session
        """
        old_planet = payload.get("old_planet", "Unknown")
        new_planet = payload.get("new_planet", "Unknown")
        old_card = payload.get("old_card", "Unknown")
        new_card = payload.get("new_card", "Unknown")

        logger.info(
            f"[InsightManager] Generating period transition prompt for user {user_id}: "
            f"{old_planet} → {new_planet}"
        )

        # Planetary energy descriptions for LLM context
        planetary_themes = {
            "Mercury": "communication, learning, quick thinking, adaptability",
            "Venus": "relationships, beauty, harmony, values, pleasure",
            "Mars": "action, energy, courage, competition, drive",
            "Jupiter": "expansion, abundance, luck, wisdom, growth",
            "Saturn": "discipline, structure, responsibility, lessons, mastery",
            "Uranus": "innovation, change, rebellion, awakening, freedom",
            "Neptune": "intuition, dreams, spirituality, illusion, transcendence",
            "Long Range": "long-term karmic themes, destiny patterns, life lessons",
            "Pluto": "transformation, power, rebirth, shadow work, regeneration",
            "Result": "culmination, outcomes, harvest of efforts, completion"
        }

        old_theme = planetary_themes.get(old_planet, "transition energy")
        new_theme = planetary_themes.get(new_planet, "new energy")

        system_prompt = (
            "You are a wise cosmic guide helping someone transition between planetary periods. "
            "Generate a warm, insightful reflection prompt (2-3 sentences) that:\n"
            "1. Acknowledges what they're completing/leaving behind\n"
            "2. Introduces the energy of the new period\n"
            "3. Offers a gentle question or intention for the transition\n"
            "Be poetic but grounded. Do not use astrology jargon excessively."
        )

        user_msg = f"""
        The user is transitioning planetary periods in their personal year cycle.

        LEAVING:
        - Planet: {old_planet}
        - Card: {old_card}
        - Theme: {old_theme}

        ENTERING:
        - Planet: {new_planet}
        - Card: {new_card}
        - Theme: {new_theme}

        Generate a reflection prompt that honors this transition.
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            prompt_text = response.content.strip()
        except Exception as e:
            logger.error(f"LLM period transition prompt failed: {e}")
            prompt_text = (
                f"You're entering a {new_planet} period. "
                f"As you leave the energy of {old_planet} behind, "
                f"what wisdom do you carry forward?"
            )

        # Create the prompt record
        try:
            prompt = await self._create_prompt(
                user_id=user_id,
                db=db,
                prompt_text=prompt_text,
                trigger_type=f"magi_period_shift:{old_planet}_to_{new_planet}",
                evidence={
                    "event": "MAGI_PERIOD_SHIFT",
                    "old_planet": old_planet,
                    "new_planet": new_planet,
                    "old_card": old_card,
                    "new_card": new_card,
                },
                priority=8,  # High priority for period transitions
            )

            if prompt:
                logger.info(
                    f"[InsightManager] Created period transition prompt {prompt.id} "
                    f"for user {user_id}: {new_planet} period"
                )
        except Exception as e:
            logger.error(f"Failed to create period transition prompt: {e}")

    # =========================================================================
    # CYCLICAL PATTERN METHODS
    # =========================================================================

    async def generate_cyclical_pattern_prompt(
        self, user_id: int, pattern_data: Dict, prompt_type: str, db: AsyncSession
    ) -> None:
        """
        Generate a reflection prompt when cyclical patterns are detected.

        Creates personalized prompts based on:
        - The type of pattern (symptom, variance, theme, evolution)
        - The planetary period context
        - Historical observations

        Args:
            user_id: User who owns the pattern
            pattern_data: Event payload with pattern details
            prompt_type: "detected" or "confirmed"
            db: Database session
        """
        pattern_type = pattern_data.get("pattern_type", "unknown")
        period_card = pattern_data.get("period_card", "Unknown")
        planetary_ruler = pattern_data.get("planetary_ruler", "Unknown")
        confidence = pattern_data.get("confidence", 0)
        description = pattern_data.get("description", "")
        observation_count = pattern_data.get("observation_count", 0)

        logger.info(
            f"[InsightManager] Generating {prompt_type} cyclical prompt for user {user_id}: "
            f"{pattern_type} in {period_card}"
        )

        # Pattern type descriptions for LLM context
        pattern_descriptions = {
            "period_symptom": "recurring physical or emotional experiences during specific planetary periods",
            "variance": "significant mood or energy differences between planetary periods",
            "theme_alignment": "alignment between journal themes and planetary guidance",
            "evolution": "long-term changes in experience across multiple years",
        }

        pattern_context = pattern_descriptions.get(pattern_type, "cyclical life patterns")

        # Different prompts for detected vs confirmed
        if prompt_type == "confirmed":
            system_prompt = (
                "You are a wise pattern analyst helping someone understand confirmed patterns in their life. "
                "Generate a profound yet accessible reflection prompt (2-3 sentences) that:\n"
                "1. Validates the pattern they've discovered\n"
                "2. Invites deeper exploration of its meaning\n"
                "3. Suggests how to work with this knowledge\n"
                "Be warm but insightful. This is a significant discovery."
            )
        else:
            system_prompt = (
                "You are an observant guide noticing emerging patterns in someone's life. "
                "Generate a curious, open-ended reflection prompt (1-2 sentences) that:\n"
                "1. Gently draws attention to a possible pattern\n"
                "2. Invites awareness without premature conclusions\n"
                "Be subtle and non-prescriptive."
            )

        user_msg = f"""
        Pattern Analysis:
        - Type: {pattern_type} ({pattern_context})
        - Period: {period_card} ({planetary_ruler})
        - Confidence: {confidence:.0%}
        - Based on: {observation_count} observations
        - Description: {description}

        Generate an appropriate reflection prompt.
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            prompt_text = response.content.strip()
        except Exception as e:
            logger.error(f"LLM cyclical pattern prompt failed: {e}")
            prompt_text = (
                f"We've noticed a pattern in your {planetary_ruler} periods. "
                f"How does this resonate with your experience?"
            )

        # Create prompt with appropriate priority
        priority = 9 if prompt_type == "confirmed" else 6

        try:
            await self._create_prompt(
                user_id=user_id,
                db=db,
                prompt_text=prompt_text,
                trigger_type=f"cyclical_pattern_{prompt_type}:{pattern_type}",
                evidence=pattern_data,
                priority=priority,
            )
        except Exception as e:
            logger.error(f"Failed to create cyclical pattern prompt: {e}")

    async def generate_cyclical_synthesis_entry(
        self, user_id: int, pattern_data: Dict, db: AsyncSession
    ) -> None:
        """
        Generate a high-fidelity synthesis journal entry for a confirmed pattern.

        This creates a system-generated journal entry that synthesizes:
        - The pattern discovery
        - Historical evidence
        - Implications and guidance

        Args:
            user_id: User who owns the pattern
            pattern_data: Event payload with pattern details
            db: Database session
        """
        from src.app.modules.features.journal.system_journal import SystemJournalService

        pattern_type = pattern_data.get("pattern_type", "unknown")
        period_card = pattern_data.get("period_card", "Unknown")
        planetary_ruler = pattern_data.get("planetary_ruler", "Unknown")
        confidence = pattern_data.get("confidence", 0)
        description = pattern_data.get("description", "")
        evidence_summary = pattern_data.get("evidence_summary", [])

        logger.info(
            f"[InsightManager] Generating synthesis entry for confirmed pattern: "
            f"{pattern_type} in {period_card}"
        )

        system_prompt = (
            "You are the GUTTERS Intelligence System synthesizing a confirmed life pattern. "
            "Generate a structured journal entry (markdown format) that:\n"
            "1. **Discovery**: Summarize what pattern was confirmed\n"
            "2. **Evidence**: List key observations that support this\n"
            "3. **Meaning**: Interpret what this pattern suggests\n"
            "4. **Integration**: Offer practical guidance for working with this pattern\n\n"
            "Write in second person ('you'), be warm but precise. "
            "This is a significant insight being delivered to the user."
        )

        evidence_text = (
            "\n".join([f"- {e}" for e in evidence_summary[:5]])
            if evidence_summary
            else "Multiple observations over time"
        )

        user_msg = f"""
        CONFIRMED PATTERN:
        Type: {pattern_type}
        Period: {period_card} ({planetary_ruler} energy)
        Confidence: {confidence:.0%}
        Description: {description}

        Evidence Summary:
        {evidence_text}

        Generate a synthesis journal entry.
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            synthesis_content = response.content.strip()
        except Exception as e:
            logger.error(f"LLM synthesis generation failed: {e}")
            synthesis_content = (
                f"## Pattern Confirmed: {pattern_type.replace('_', ' ').title()}\n\n"
                f"During your **{planetary_ruler}** periods ({period_card}), "
                f"we've observed consistent patterns:\n\n{description}\n\n"
                f"This insight has been confirmed with {confidence:.0%} confidence."
            )

        # Create system journal entry
        journal_service = SystemJournalService()

        try:
            await journal_service.create_synthesis_entry(
                user_id=user_id,
                title=f"Pattern Insight: {planetary_ruler} Period",
                content=synthesis_content,
                entry_type="cyclical_synthesis",
                source="observer.cyclical",
                metadata={
                    "pattern_type": pattern_type,
                    "period_card": period_card,
                    "planetary_ruler": planetary_ruler,
                    "confidence": confidence,
                    "pattern_data": pattern_data,
                },
                tags=[
                    "system-insight",
                    "cyclical-pattern",
                    pattern_type,
                    planetary_ruler.lower(),
                ],
                db=db,
            )

            logger.info(f"[InsightManager] Created synthesis entry for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to create synthesis journal entry: {e}")

    async def generate_cyclical_evolution_insight(
        self, user_id: int, evolution_data: Dict, db: AsyncSession
    ) -> None:
        """
        Generate a profound insight about long-term pattern evolution.

        Creates both a notification and a journal entry about how the user's
        experience of a particular period has evolved over multiple years.

        Args:
            user_id: User ID
            evolution_data: Event payload with evolution analysis
            db: Database session
        """
        from src.app.modules.features.journal.system_journal import SystemJournalService

        period_card = evolution_data.get("period_card", "Unknown")
        planetary_ruler = evolution_data.get("planetary_ruler", "Unknown")
        years_analyzed = evolution_data.get("years_analyzed", [])
        mood_trajectory = evolution_data.get("mood_trajectory", "stable")
        theme_evolution = evolution_data.get("theme_evolution", {})
        confidence = evolution_data.get("confidence", 0)

        logger.info(
            f"[InsightManager] Generating evolution insight for user {user_id}: "
            f"{period_card} over {len(years_analyzed)} years"
        )

        trajectory_meanings = {
            "improving": "Your experience during this period has been getting progressively better over time.",
            "declining": "This period has become more challenging for you over the years.",
            "stable": "Your experience during this period has remained consistent across years.",
            "volatile": "Your experience varies significantly each time this period comes around.",
        }

        trajectory_guidance = {
            "improving": "This suggests growth and integration. What have you learned that's made this easier?",
            "declining": "This may be calling for attention. What's changed, and what support might help?",
            "stable": "This consistency is worth noting. Is this stability serving you?",
            "volatile": "The variability suggests external factors may play a role. What differs each year?",
        }

        system_prompt = (
            "You are a wise longitudinal analyst helping someone understand their evolution over years. "
            "Generate a profound journal entry that:\n"
            "1. Acknowledges the span of time analyzed (years)\n"
            "2. Describes the trajectory observed\n"
            "3. Offers perspective on what this might mean\n"
            "4. Suggests reflection questions for deeper understanding\n\n"
            "Be profound but accessible. This is about their life journey."
        )

        years_str = ", ".join(str(y) for y in sorted(years_analyzed))

        user_msg = f"""
        EVOLUTION ANALYSIS:
        Period: {period_card} ({planetary_ruler})
        Years Analyzed: {years_str}
        Mood Trajectory: {mood_trajectory}
        Meaning: {trajectory_meanings.get(mood_trajectory, '')}

        Generate an evolution insight entry.
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            evolution_content = response.content.strip()
        except Exception as e:
            logger.error(f"LLM evolution insight failed: {e}")
            evolution_content = (
                f"## Long-Term Evolution: {planetary_ruler} Periods\n\n"
                f"Analyzing your experience across {len(years_analyzed)} years, "
                f"we observe a **{mood_trajectory}** trajectory.\n\n"
                f"{trajectory_meanings.get(mood_trajectory, '')}\n\n"
                f"{trajectory_guidance.get(mood_trajectory, '')}"
            )

        # Create journal entry
        journal_service = SystemJournalService()

        try:
            await journal_service.create_synthesis_entry(
                user_id=user_id,
                title=f"Evolution Insight: {planetary_ruler} Over {len(years_analyzed)} Years",
                content=evolution_content,
                entry_type="evolution_insight",
                source="observer.cyclical",
                metadata={
                    "period_card": period_card,
                    "planetary_ruler": planetary_ruler,
                    "years_analyzed": years_analyzed,
                    "mood_trajectory": mood_trajectory,
                    "theme_evolution": theme_evolution,
                    "confidence": confidence,
                },
                tags=[
                    "system-insight",
                    "evolution",
                    "longitudinal",
                    planetary_ruler.lower(),
                ],
                db=db,
            )

            # Also send notification for this significant insight
            await self.notification_service.send_notification(
                user_id=user_id,
                title=f"Evolution Insight: {planetary_ruler}",
                body=(
                    f"We've analyzed your {planetary_ruler} periods across "
                    f"{len(years_analyzed)} years and found something meaningful."
                ),
                data={"url": "/journal"},
                db=db,
            )

        except Exception as e:
            logger.error(f"Failed to create evolution insight: {e}")

    async def generate_theme_alignment_acknowledgment(
        self, user_id: int, alignment_data: Dict, db: AsyncSession
    ) -> None:
        """
        Acknowledge when user's journal themes align with planetary guidance.

        This is a positive reinforcement mechanism that celebrates when
        the user is "in flow" with cosmic rhythms.

        Args:
            user_id: User ID
            alignment_data: Event payload with alignment details
            db: Database session
        """
        period_card = alignment_data.get("period_card", "Unknown")
        planetary_ruler = alignment_data.get("planetary_ruler", "Unknown")
        period_theme = alignment_data.get("period_theme", "")
        journal_themes = alignment_data.get("journal_themes", [])
        alignment_score = alignment_data.get("alignment_score", 0)

        logger.info(
            f"[InsightManager] Generating alignment acknowledgment for user {user_id}: "
            f"{planetary_ruler} alignment {alignment_score:.0%}"
        )

        themes_str = ", ".join(journal_themes[:5]) if journal_themes else "your recent reflections"

        system_prompt = (
            "You are an appreciative cosmic guide acknowledging someone's alignment with universal rhythms. "
            "Generate a brief, warm acknowledgment (1-2 sentences) that:\n"
            "1. Celebrates their attunement\n"
            "2. Names what they're aligned with\n"
            "3. Encourages continued awareness\n\n"
            "Be genuine, not sycophantic. This is meaningful."
        )

        user_msg = f"""
        ALIGNMENT DETECTED:
        Period: {period_card} ({planetary_ruler})
        Period Theme: {period_theme}
        Journal Themes: {themes_str}
        Alignment Score: {alignment_score:.0%}

        Generate an acknowledgment.
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            acknowledgment = response.content.strip()
        except Exception as e:
            logger.error(f"LLM alignment acknowledgment failed: {e}")
            acknowledgment = (
                f"You're deeply attuned to your {planetary_ruler} period right now. "
                f"Your reflections on {themes_str} align beautifully with this energy."
            )

        # Send as notification (not a prompt, just acknowledgment)
        try:
            await self.notification_service.send_notification(
                user_id=user_id,
                title=f"✨ Cosmic Alignment: {planetary_ruler}",
                body=acknowledgment,
                data={"url": "/dashboard"},
                db=db,
            )

            logger.info(f"[InsightManager] Sent alignment acknowledgment to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send alignment acknowledgment: {e}")
