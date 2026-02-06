import logging
from typing import List  # keeping for compatibility if needed, but fixing usage below

# actually let's just use list as per modern python
from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from .library import astrology, human_design, journal, numerology, quests

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all Intelligence Tools.

    Handles:
    1. Loading stateless calculation tools.
    2. Injecting context (user_id, db) into stateful tools (Journal).
    """

    @staticmethod
    def get_tools_for_request(user_id: int, db: AsyncSession) -> List[StructuredTool]:
        """
        Returns a list of tools available for the current request context.
        Injects necessary dependencies (user_id, db session) into stateful tools.
        """
        tools = []

        try:
            tools.append(astrology.get_tool())
        except Exception as e:
            logger.error(f"Failed to load Astrology tool: {e}")

        try:
            tools.append(human_design.get_tool())
        except Exception as e:
            logger.error(f"Failed to load Human Design tool: {e}")

        try:
            tools.append(numerology.get_tool())
        except Exception as e:
            logger.error(f"Failed to load Numerology tool: {e}")

        # Stateful Tools (Journaling, Quests)
        try:
            tools.append(journal.get_tool(user_id=user_id, db=db))
        except Exception as e:
            logger.error(f"Failed to load Journal tool: {e}")

        try:
            tools.append(quests.get_create_quest_tool(user_id=user_id, db=db))
            tools.append(quests.get_list_quests_tool(user_id=user_id, db=db))
            tools.append(quests.get_complete_quest_tool(user_id=user_id, db=db))
        except Exception as e:
            logger.error(f"Failed to load Quest tools: {e}")

        return tools

    @staticmethod
    def get_tools_map(user_id: int, db: AsyncSession) -> dict[str, StructuredTool]:
        """Get tools as a map for easy lookup by name."""
        tools = ToolRegistry.get_tools_for_request(user_id, db)
        return {tool.name: tool for tool in tools}
