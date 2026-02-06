from typing import Any, Dict

from langchain_core.tools import tool

from src.app.modules.intelligence.evolution.refiner import get_evolution_refiner


@tool
async def semantic_self_audit(
    user_id: int,
    field_name: str,
    candidate_value: str,
    context_title: str,
    context_desc: str,
    journal_text: str,
    is_ascension: bool = False,
) -> Dict[str, Any]:
    """
    Perform a semantic self-audit of a specific hypothesis against recent context.

    Args:
        user_id: The ID of the user.
        field_name: The field to audit (e.g., 'rising_sign').
        candidate_value: The value to test (e.g., 'Leo').
        context_title: Title of the event or quest.
        context_desc: Description of the action taken.
        journal_text: Recent journal entries for context.
        is_ascension: Whether this is a major milestone (uses Premium LLM).

    Returns:
        Structured refinement result with confidence delta and insight.
    """
    refiner = get_evolution_refiner()
    result = await refiner.refine_semantic_alignment(
        user_id=user_id,
        field_name=field_name,
        candidate_value=candidate_value,
        context_title=context_title,
        context_desc=context_desc,
        journal_text=journal_text,
        is_ascension=is_ascension,
    )

    return result.model_dump()
