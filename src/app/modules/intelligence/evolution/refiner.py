import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.app.core.llm.config import get_premium_llm, get_standard_llm

logger = logging.getLogger(__name__)


class RefinementResult(BaseModel):
    confidence_delta: float
    evolution_insight: str
    alignment_score: float
    model_used: str
    reasoning: str
    tokens_in: int = 0
    tokens_out: int = 0


class EvolutionRefiner:
    """
    GUTTERS System Auditor.

    Evaluates the semantic alignment between user actions and cosmic hypotheses.
    Uses multi-tier intelligence (Haiku vs Sonnet) based on event significance.
    """

    SYSTEM_AUDITOR_PROMPT = """
    You are the GUTTERS System Auditor. You evaluate the semantic alignment 
    between a User's actions and their Cosmic/Behavioral Hypotheses.

    Your task is to analyze if the provided data confirms or refutes the hypothesis.
    Maintain a "Cosmic Brutalist" and "Solo Leveling" tone.

    INPUT DATA:
    - Quest/Event: {context_title}
    - Description: {context_desc}
    - Journal Context: {journal_text}
    - Hypothesis Field: {field_name}
    - Candidate Being Tested: {candidate_value}

    OUTPUT REQUIREMENTS:
    1. confidence_delta: Float (-0.1 to +0.1). How much does this action change certainty?
    2. evolution_insight: One-sentence high-fidelity summary (Solo Leveling style).
    3. alignment_score: 0.0 to 1.0 (How relevant was this action to this specific hypothesis?).
    4. reasoning: Brief thinking steps of your analysis.

    Respond ONLY in JSON format:
    {{
        "confidence_delta": 0.05,
        "evolution_insight": "Displayed resilience during...",
        "alignment_score": 0.9,
        "reasoning": "User proactively engaged with..."
    }}
    """

    async def refine_semantic_alignment(
        self,
        user_id: int,
        field_name: str,
        candidate_value: str,
        context_title: str,
        context_desc: str,
        journal_text: str,
        is_ascension: bool = False,
    ) -> RefinementResult:
        """
        Invoke semantic refinement with multi-tier LLM logic.
        """
        # 1. Tier Selection
        llm = get_premium_llm() if is_ascension else get_standard_llm()

        model_name = "sonnet-4.5" if is_ascension else "haiku-4.5"

        prompt = self.SYSTEM_AUDITOR_PROMPT.format(
            context_title=context_title,
            context_desc=context_desc,
            journal_text=journal_text,
            field_name=field_name,
            candidate_value=candidate_value,
        )

        try:
            # 2. Invoke LLM
            response = await llm.ainvoke(
                [
                    SystemMessage(content="You are the GUTTERS System Auditor. Respond ONLY in JSON."),
                    HumanMessage(content=prompt),
                ]
            )

            # Extract content and metadata (if available)
            content = response.content if isinstance(response.content, str) else str(response.content)

            # Simple token extraction (mocked for now if metadata isn't easy to get from LangChain response in this env)
            # In a real integration, we'd pull these from response_metadata
            tokens_in = getattr(response, "response_metadata", {}).get("token_usage", {}).get("prompt_tokens", 0)
            tokens_out = getattr(response, "response_metadata", {}).get("token_usage", {}).get("completion_tokens", 0)

            # 3. Parse Output
            start = content.find("{")
            end = content.rfind("}") + 1
            data = json.loads(content[start:end])

            return RefinementResult(
                confidence_delta=data.get("confidence_delta", 0.0),
                evolution_insight=data.get("evolution_insight", "System observed neutral alignment."),
                alignment_score=data.get("alignment_score", 0.5),
                model_used=model_name,
                reasoning=data.get("reasoning", "Semantic audit performed."),
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )

        except Exception as e:
            logger.error(f"EvolutionRefiner Error: {e}. Falling back to neutral calculation.")
            # 4. Neutral Fallback
            return RefinementResult(
                confidence_delta=0.0,
                evolution_insight="System: Profile remains stable. No significant semantic delta detected.",
                alignment_score=0.0,
                model_used="fallback-neutral",
                reasoning=f"LLM failure or timeout. {str(e)}",
            )


# Singleton
_refiner: EvolutionRefiner | None = None


def get_evolution_refiner() -> EvolutionRefiner:
    global _refiner
    if _refiner is None:
        _refiner = EvolutionRefiner()
    return _refiner
