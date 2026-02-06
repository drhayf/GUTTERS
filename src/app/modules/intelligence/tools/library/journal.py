from datetime import UTC, datetime
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.insight import JournalEntry, PromptStatus, ReflectionPrompt


class JournalEntryInput(BaseModel):
    """Input for creating a journal entry."""

    content: str = Field(
        ...,
        description=(
            "The content of the journal entry. Should be the user's thoughts, "
            "feelings, or experiences."
        ),
    )
    mood_score: int = Field(
        ...,
        description=(
            "A score from 1-10 representing the user's mood "
            "(1=Worst, 10=Best). Infer if not explicitly stated."
        ),
        ge=1,
        le=10,
    )
    tags: list[str] = Field(default_factory=list, description="Optional list of tags for the entry.")
    prompt_id: Optional[int] = Field(
        default=None, description="The ID of the Reflection Prompt this entry is answering, if applicable."
    )


def get_tool(user_id: int, db: AsyncSession) -> StructuredTool:
    """
    Return a context-aware Journal tool bound to the specific user and database session.
    """

    async def _log_journal_entry_async(
        content: str, mood_score: int, tags: list[str] = [], prompt_id: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Log a new journal entry for the user.
        """
        try:
            # Create Entry
            entry = JournalEntry(
                user_id=user_id,
                content=content,
                mood_score=mood_score,
                tags=tags,
                prompt_id=prompt_id,
                created_at=datetime.now(UTC),
            )
            db.add(entry)

            # Handle Prompt Linking
            if prompt_id:
                result = await db.execute(select(ReflectionPrompt).where(ReflectionPrompt.id == prompt_id))
                prompt = result.scalar_one_or_none()
                if prompt:
                    prompt.status = PromptStatus.ANSWERED
                    # Copy prompt context if available
                    if prompt.trigger_context:
                        entry.context_snapshot = prompt.trigger_context

            # Inject Magi chronos context before commit
            if not entry.context_snapshot:
                entry.context_snapshot = {}

            try:
                from src.app.core.state.chronos import get_chronos_manager
                chronos_manager = get_chronos_manager()
                chronos_state = await chronos_manager.get_user_chronos(user_id)

                if chronos_state:
                    entry.context_snapshot["magi"] = {
                        "period_card": chronos_state.get("current_card", {}).get("name"),
                        "period_day": 52 - (chronos_state.get("days_remaining", 0) or 0),
                        "period_total": 52,
                        "planetary_ruler": chronos_state.get("current_planet"),
                        "theme": chronos_state.get("theme"),
                        "guidance": chronos_state.get("guidance"),
                        "period_start": chronos_state.get("period_start"),
                        "period_end": chronos_state.get("period_end"),
                        "progress_percent": round(
                            ((52 - (chronos_state.get("days_remaining", 0) or 0)) / 52) * 100, 2
                        ),
                    }

                # Add Council of Systems hexagram context
                from src.app.modules.intelligence.council import get_council_service
                council = get_council_service()
                hexagram = council.get_current_hexagram()

                if hexagram:
                    entry.context_snapshot["council"] = {
                        "sun_gate": hexagram.sun_gate,
                        "sun_line": hexagram.sun_line,
                        "sun_gate_name": hexagram.sun_gate_name,
                        "sun_gene_key_gift": hexagram.sun_gene_key_gift,
                        "sun_gene_key_shadow": hexagram.sun_gene_key_shadow,
                        "earth_gate": hexagram.earth_gate,
                        "earth_gate_name": hexagram.earth_gate_name,
                        "polarity_theme": hexagram.polarity_theme,
                    }

            except Exception as e:
                # Don't fail journal creation if context injection fails
                print(f"[JournalTool] Failed to inject magi context: {e}")

            await db.commit()
            await db.refresh(entry)

            return {
                "status": "success",
                "message": "Journal entry logged successfully.",
                "entry_id": entry.id,
            }

        except Exception as e:
            await db.rollback()
            return {"status": "error", "message": f"Failed to log entry: {str(e)}"}

    return StructuredTool.from_function(
        func=None,
        coroutine=_log_journal_entry_async,
        name="log_journal_entry",
        description=(
            "Log a user's thoughts, feelings, or experiences into their personal "
            "journal. Use this when the user explicitly asks to 'note this down', "
            "'journal this', or 'log this'. Can be linked to a specific prompt IDs."
        ),
        args_schema=JournalEntryInput,
    )
