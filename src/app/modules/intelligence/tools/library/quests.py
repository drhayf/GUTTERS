from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.features.quests.manager import QuestManager
from src.app.modules.features.quests.models import QuestCategory, QuestDifficulty, QuestSource, RecurrenceType


class CreateQuestInput(BaseModel):
    title: str = Field(..., description="The title of the quest.")
    description: Optional[str] = Field(None, description="Detailed description.")
    category: str = Field("daily", description="Category: 'daily', 'mission', 'reflection'.")
    difficulty: str = Field("easy", description="Difficulty: 'easy', 'medium', 'hard', 'elite'.")
    recurrence: str = Field(
        "once", description="Recurrence: 'once', 'daily', 'weekly', 'monthly', 'custom'. Default is 'once'."
    )
    cron_expression: Optional[str] = Field(None, description="Cron expression if recurrence is 'custom'.")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization.")


class CompleteQuestInput(BaseModel):
    quest_log_id: int = Field(description="The ID of the specific quest instance (log) to complete.")
    notes: Optional[str] = Field(default=None, description="Reflection notes or comments on completion.")


def get_create_quest_tool(user_id: int, db: AsyncSession) -> StructuredTool:
    async def _create_quest(
        title: str,
        description: str = None,
        category: str = "daily",
        difficulty: str = "easy",
        recurrence: str = "once",
        cron_expression: str = None,
        tags: List[str] = None,
    ) -> str:
        """
        Creates a quest with difficulty and category.
        """
        try:
            # Enums conversion
            try:
                rec_enum = RecurrenceType(recurrence.lower())
            except ValueError:
                return f"Error: Invalid recurrence '{recurrence}'. Use: once, daily, weekly, monthly, custom."

            try:
                cat_enum = QuestCategory(category.lower())
            except ValueError:
                cat_enum = QuestCategory.DAILY

            try:
                diff_enum = QuestDifficulty(difficulty.lower())
            except ValueError:
                diff_enum = QuestDifficulty.EASY

            quest = await QuestManager.create_quest(
                db=db,
                user_id=user_id,
                title=title,
                description=description,
                category=cat_enum,
                difficulty=diff_enum,
                recurrence=rec_enum,
                cron_expression=cron_expression,
                tags=tags or [],
                source=QuestSource.AGENT,
            )
            # Return structured data for the Agent to "see" and for the Handler to parse
            import json

            result_data = {
                "status": "success",
                "quest_id": quest.id,
                "title": quest.title,
                "xp_reward": quest.xp_reward,
                "message": f"Quest '{quest.title}' created successfully.",
            }
            return json.dumps(result_data)
        except Exception as e:
            return f"Failed to create quest: {str(e)}"

    return StructuredTool.from_function(
        func=None,
        coroutine=_create_quest,
        name="create_quest",
        description=(
            "Create a new Quest or Task for the user. System can assign "
            "difficulty and category based on user state."
        ),
        args_schema=CreateQuestInput,
    )


def get_list_quests_tool(user_id: int, db: AsyncSession) -> StructuredTool:
    async def _list_quests() -> str:
        """
        Lists pending quest logs and active quest definitions.
        """
        try:
            pending = await QuestManager.get_pending_logs(db, user_id)
            active = await QuestManager.get_active_quests(db, user_id)

            output = "Pending Quests (Do these now!):\n"
            if not pending:
                output += "None.\n"
            for log in pending:
                output += (
                    f"- [ID:{log.id}] {log.quest.title} (Difficulty: "
                    f"{log.quest.difficulty.value}, XP: {log.quest.xp_reward})\n"
                )

            output += "\nActive Quest Definitions:\n"
            for q in active:
                output += (
                    f"- {q.title} ({q.recurrence}, {q.category})\n"
                )

            return output
        except Exception as e:
            return f"Failed to list quests: {str(e)}"

    return StructuredTool.from_function(
        func=None,
        coroutine=_list_quests,
        name="list_quests",
        description="List the user's pending quests and active definitions.",
    )


def get_complete_quest_tool(user_id: int, db: AsyncSession) -> StructuredTool:
    async def _complete_quest(quest_log_id: int, notes: str = None) -> str:
        """
        Completes a quest log.
        """
        try:
            log = await QuestManager.complete_quest(db, quest_log_id, notes)
            return f"Quest '{log.quest.title}' marked as COMPLETED! XP gained. Check progression for Level Up status."
        except Exception as e:
            return f"Failed to complete quest: {str(e)}"

    return StructuredTool.from_function(
        func=None,
        coroutine=_complete_quest,
        name="complete_quest",
        description="Mark a specific quest instance as completed and gain XP.",
        args_schema=CompleteQuestInput,
    )
