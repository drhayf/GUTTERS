import logging
from typing import Any, Dict, Optional

from src.app.core.llm.config import get_standard_llm

logger = logging.getLogger(__name__)


class JournalistEngine:
    """
    Intelligent engine for generating system-level journal entries.
    Uses LLM (Haiku) to narrate system events with context (Rank, Solar Phase, etc).
    """

    def __init__(self):
        self.llm = get_standard_llm()  # Haiku for speed/cost

    async def generate_log_entry(
        self, event_type: str, title: str, context: Dict[str, Any], details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a sci-fi/system style log entry using LLM.

        Args:
            event_type: Type of event (e.g. "QUEST_COMPLETE", "LEVEL_UP")
            title: Name of the activity/quest
            context: Contextual snapshot (Rank, Kp Index, Sync Rate)
            details: Extra event details (XP gained, etc)

        Returns:
            str: The flavor text for the log.
        """
        try:
            # 1. Build Prompt
            prompt = self._build_prompt(event_type, title, context, details)

            # 2. Call LLM
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # 3. Clean up quotes causing issues sometimes
            content = content.replace('"', "").replace("'", "")

            return content

        except Exception as e:
            logger.error(f"JournalistEngine LLM Failure: {e}")
            return self._get_fallback_entry(event_type, title)

    def _build_prompt(self, event_type: str, title: str, context: Dict[str, Any], details: Dict[str, Any]) -> str:
        # Unpack context
        rank = context.get("rank", "Unknown")
        kp = context.get("kp_index", 0)
        sync = context.get("sync_rate", 0)
        xp = details.get("xp", 0)

        base_prompt = f"""
You are the System Historian for the GUTTERS interface.
Your job is to log system events with a cool, sci-fi, "System Log" aesthetic.

CONTEXT:
- User Rank: {rank}
- Sync Rate: {sync}%
- Planetary Kp Index: {kp} (Higher means more solar interference)

EVENT:
- Type: {event_type}
- Activity: "{title}"
- Reward: {xp} XP

INSTRUCTIONS:
1. Write a SINGLE concise sentence (max 15 words).
2. Use clinical, system-like terminology (e.g., "Vitality confirmed.", "Sync established.", "Endurance verified.").
3. If Kp is high (>4), mention overcoming interference.
4. If Rank is high (B/A/S), acknowledge superior performance.
5. NO hashtags, NO emojis in the text itself (Text only).

Example Output:
"Physical exertion successfully counteracted solar instability."
"Combat drills verified. Neural link stable."
"""
        return base_prompt

    def _get_fallback_entry(self, event_type: str, title: str) -> str:
        """Fallback if LLM fails."""
        if event_type == "QUEST_COMPLETE":
            return f"Activity '{title}' completed successfully."
        elif event_type == "LEVEL_UP":
            return "System Evolution triggered. Level Up processed."
        return f"Event '{title}' logged."
