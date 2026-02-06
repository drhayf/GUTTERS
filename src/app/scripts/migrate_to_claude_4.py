"""
Migration script to verify Claude 4.5 integration.

Tests that all LLM-using components work with new models.
"""

import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage, SystemMessage

from src.app.core.llm.config import LLMConfig, LLMTier, get_premium_llm, get_standard_llm


async def test_premium_model():
    """Test Claude Sonnet 4.5."""
    print("Testing Claude Sonnet 4.5 (Premium)...")

    try:
        llm = get_premium_llm()

        response = await llm.ainvoke(
            [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Say 'Premium model working!' in a creative way."),
            ]
        )

        print(f"✓ Response: {response.content[:100]}...")

        # Check model info
        provider, model, config = LLMConfig.get_model_info(LLMTier.PREMIUM)
        print(f"✓ Provider: {provider}, Model: {model}")
        print(f"✓ Cost: ${config.cost_per_1k_input}/${config.cost_per_1k_output} per 1K tokens")
    except Exception as e:
        print(f"✗ Premium model test failed: {e}")


async def test_standard_model():
    """Test Claude Haiku 4.5."""
    print("\nTesting Claude Haiku 4.5 (Standard)...")

    try:
        llm = get_standard_llm()

        response = await llm.ainvoke(
            [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Say 'Standard model working!' briefly."),
            ]
        )

        print(f"✓ Response: {response.content[:100]}...")

        # Check model info
        provider, model, config = LLMConfig.get_model_info(LLMTier.STANDARD)
        print(f"✓ Provider: {provider}, Model: {model}")
        print(f"✓ Cost: ${config.cost_per_1k_input}/${config.cost_per_1k_output} per 1K tokens")
    except Exception as e:
        print(f"✗ Standard model test failed: {e}")


async def test_cost_calculation():
    """Test cost estimation."""
    print("\nTesting cost calculation...")

    # Typical query: 2000 tokens in, 500 tokens out
    premium_cost = LLMConfig.estimate_cost(LLMTier.PREMIUM, 2000, 500)
    standard_cost = LLMConfig.estimate_cost(LLMTier.STANDARD, 2000, 500)

    print(f"✓ Premium cost (2K in, 500 out): {premium_cost:.6f} AUD")
    print(f"✓ Standard cost (2K in, 500 out): {standard_cost:.6f} AUD")
    print(f"✓ Savings: {((premium_cost - standard_cost) / premium_cost * 100):.1f}%")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Claude 4.5 Migration Verification")
    print("=" * 60)

    # Load settings to ensure API keys are available
    from src.app.core.config import settings

    if not settings.OPENROUTER_API_KEY:
        print("✗ Error: OPENROUTER_API_KEY not found in settings.")
        return

    await test_premium_model()
    await test_standard_model()
    await test_cost_calculation()

    print("\n" + "=" * 60)
    print("✓ Migration verification script completed.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
