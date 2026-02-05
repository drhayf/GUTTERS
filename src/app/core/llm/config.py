"""
Multi-tier LLM configuration for GUTTERS.

Uses different Claude 4.5 models based on task complexity.
"""

from enum import Enum
from typing import Optional
from langchain_openai import ChatOpenAI
from src.app.core.config import settings


class LLMTier(str, Enum):
    """
    LLM tiers for different task complexities.

    PREMIUM: Claude Sonnet 4.5 - Complex reasoning, user-facing
    STANDARD: Claude Haiku 4.5 - Simple tasks, background processing
    """

    PREMIUM = "premium"
    STANDARD = "standard"


class ModelConfig:
    """Configuration for a specific model."""

    def __init__(
        self, model_id: str, temperature: float, max_tokens: int, cost_per_1k_input: float, cost_per_1k_output: float
    ):
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
        }


class LLMConfig:
    """
    Multi-model LLM configuration manager.

    Provides access to different Claude 4.5 models based on task tier.
    """

    # Model configurations
    MODELS = {
        LLMTier.PREMIUM: ModelConfig(
            model_id="anthropic/claude-sonnet-4.5",
            temperature=0.7,
            max_tokens=4000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        LLMTier.STANDARD: ModelConfig(
            model_id="anthropic/claude-haiku-4.5",
            temperature=0.7,
            max_tokens=4000,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
        ),
    }

    # Exchange rate: 1 USD to AUD
    AUD_EXCHANGE_RATE = 1.54

    @classmethod
    async def initialize_from_db(cls):
        """Load model configurations from system_configuration table."""
        from sqlalchemy import select
        from src.app.core.db.database import local_session
        from src.app.models.system_configuration import SystemConfiguration

        async with local_session() as db:
            result = await db.execute(
                select(SystemConfiguration).where(SystemConfiguration.module_name == "llm_config")
            )
            sys_config = result.scalar_one_or_none()

            if sys_config and sys_config.config:
                stored_models = sys_config.config.get("models", {})
                for tier_name, conf in stored_models.items():
                    try:
                        tier = LLMTier(tier_name)
                        cls.MODELS[tier] = ModelConfig(**conf)
                    except (ValueError, TypeError):
                        continue

                cls.AUD_EXCHANGE_RATE = sys_config.config.get("exchange_rate", cls.AUD_EXCHANGE_RATE)

    @staticmethod
    def get_llm(tier: LLMTier = LLMTier.PREMIUM) -> ChatOpenAI:
        """
        Get LLM instance for specified tier.

        Args:
            tier: LLM tier (PREMIUM or STANDARD)

        Returns:
            Configured LangChain ChatOpenAI instance

        Examples:
            # Get premium model for synthesis
            llm = LLMConfig.get_llm(LLMTier.PREMIUM)

            # Get standard model for journal analysis
            llm = LLMConfig.get_llm(LLMTier.STANDARD)
        """
        config = LLMConfig.MODELS[tier]

        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            model=config.model_id,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": "https://gutters.app",
                    "X-Title": "GUTTERS - Cosmic Intelligence Platform",
                }
            },
        )

    @staticmethod
    def get_model_info(tier: LLMTier) -> tuple[str, str, ModelConfig]:
        """
        Get model information for a tier.

        Returns:
            (provider, model_name, config)

        Examples:
            provider, model, config = LLMConfig.get_model_info(LLMTier.PREMIUM)
            # → ("anthropic", "claude-sonnet-4.5", ModelConfig(...))
        """
        config = LLMConfig.MODELS[tier]

        # Parse provider and model from model_id
        # "anthropic/claude-sonnet-4.5:beta" → ("anthropic", "claude-sonnet-4.5")
        parts = config.model_id.split("/")
        provider = parts[0]
        model = parts[1].split(":")[0] if ":" in parts[1] else parts[1]

        return provider, model, config

    @staticmethod
    def estimate_cost(tier: LLMTier, tokens_in: int, tokens_out: int, currency: str = "AUD") -> float:
        """
        Estimate cost for a request.

        Args:
            tier: Model tier used
            tokens_in: Input tokens
            tokens_out: Output tokens
            currency: Currency code ("USD" or "AUD")

        Returns:
            Estimated cost in specified currency
        """
        config = LLMConfig.MODELS[tier]

        cost_in_usd = (tokens_in / 1000) * config.cost_per_1k_input
        cost_out_usd = (tokens_out / 1000) * config.cost_per_1k_output
        total_usd = cost_in_usd + cost_out_usd

        if currency == "AUD":
            return total_usd * LLMConfig.AUD_EXCHANGE_RATE

        return total_usd


# Convenience functions for common usage
def get_premium_llm() -> ChatOpenAI:
    """
    Get Claude Sonnet 4.5 for complex tasks.

    Use for:
    - User-facing responses (Query Engine)
    - Complex reasoning (Synthesis, Hypothesis)
    - Conversational depth (Genesis, Master Chat)
    """
    return LLMConfig.get_llm(LLMTier.PREMIUM)


def get_standard_llm() -> ChatOpenAI:
    """
    Get Claude Haiku 4.5 for simple tasks.

    Use for:
    - Classification (Journal mood/tags)
    - Statistical analysis (Observer correlations)
    - Background processing (Module synthesis)
    - Simple queries (factual lookups)
    """
    return LLMConfig.get_llm(LLMTier.STANDARD)
