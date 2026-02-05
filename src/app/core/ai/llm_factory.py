"""
GUTTERS LLM Factory

Factory for creating LangChain LLM instances using OpenRouter.

OpenRouter provides access to multiple AI models through a unified API.
This factory handles configuration, caching, and error handling.
"""

import os
from functools import lru_cache

from langchain_openai import ChatOpenAI


def get_llm(model_id: str, temperature: float = 0.7) -> ChatOpenAI:
    """
    Get a configured LangChain LLM instance via OpenRouter.

    Uses caching to avoid recreating LLM instances for the same model_id.

    Args:
        model_id: OpenRouter model identifier (e.g., "anthropic/claude-3.5-sonnet")
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If OPENROUTER_API_KEY environment variable is not set

    Example:
        >>> from src.app.core.ai.llm_factory import get_llm
        >>>
        >>> # Get Claude Sonnet 4.5 for synthesis
        >>> llm = get_llm("anthropic/claude-sonnet-4.5", temperature=0.7)
        >>> response = await llm.ainvoke("Synthesize this data...")
        >>>
        >>> # Get GPT-4 for analysis
        >>> llm = get_llm("openai/gpt-4-turbo", temperature=0.3)
    """
    from ..config import settings

    api_key = settings.OPENROUTER_API_KEY.get_secret_value() if settings.OPENROUTER_API_KEY else None

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Please add it to your .env file: OPENROUTER_API_KEY=sk-or-v1-..."
        )

    return _get_cached_llm(model_id, temperature, api_key)


@lru_cache(maxsize=32)
def _get_cached_llm(model_id: str, temperature: float, api_key: str) -> ChatOpenAI:
    """
    Internal cached LLM factory.

    Uses lru_cache to avoid recreating LLM instances for the same parameters.
    Separated from get_llm() to allow cache key to include api_key without exposing it.

    Args:
        model_id: OpenRouter model identifier
        temperature: Sampling temperature
        api_key: OpenRouter API key

    Returns:
        Configured ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model_id,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )
