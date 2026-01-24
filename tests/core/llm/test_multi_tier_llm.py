"""
Tests for multi-tier LLM system.

Verifies Claude 4.5 integration and model selection.
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, SystemMessage

from src.app.core.llm.config import LLMConfig, LLMTier, get_premium_llm, get_standard_llm


@pytest.mark.asyncio
async def test_premium_model_instantiation():
    """Test that premium model (Sonnet 4.5) can be instantiated."""
    llm = get_premium_llm()

    assert llm is not None
    assert "claude-sonnet-4.5" in llm.model_name


@pytest.mark.asyncio
async def test_standard_model_instantiation():
    """Test that standard model (Haiku 4.5) can be instantiated."""
    llm = get_standard_llm()

    assert llm is not None
    assert "claude-haiku-4.5" in llm.model_name


@pytest.mark.asyncio
async def test_model_info_extraction():
    """Test model info extraction."""
    provider, model, config = LLMConfig.get_model_info(LLMTier.PREMIUM)

    assert provider == "anthropic"
    assert "claude-sonnet-4.5" in model
    assert config.cost_per_1k_input == 0.003
    assert config.cost_per_1k_output == 0.015


@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation."""
    # 2000 tokens in, 500 tokens out
    premium_cost = LLMConfig.estimate_cost(LLMTier.PREMIUM, 2000, 500)
    standard_cost = LLMConfig.estimate_cost(LLMTier.STANDARD, 2000, 500)

    # Premium should be more expensive
    assert premium_cost > standard_cost

    # Check ballpark in AUD (USD 0.0135 * 1.54 = 0.02079)
    assert 0.020 < premium_cost < 0.022

    # Standard much cheaper (USD 0.001125 * 1.54 = 0.0017325)
    assert 0.001 < standard_cost < 0.003


@pytest.mark.asyncio
async def test_premium_model_mock_response(mocker):
    """Test that premium model generates responses (mocked)."""
    # Mock ChatOpenAI.ainvoke directly
    mock_response = MagicMock()
    mock_response.content = "Premium response"

    # Use patch with target string correctly
    from langchain_openai import ChatOpenAI

    mocker.patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock, return_value=mock_response)

    llm = get_premium_llm()
    response = await llm.ainvoke(
        [SystemMessage(content="You are a helpful assistant."), HumanMessage(content="Say hello.")]
    )

    assert response.content == "Premium response"


@pytest.mark.asyncio
async def test_standard_model_mock_response(mocker):
    """Test that standard model generates responses (mocked)."""
    # Mock ChatOpenAI.ainvoke directly
    mock_response = MagicMock()
    mock_response.content = "Standard response"

    # Use patch with target string correctly
    from langchain_openai import ChatOpenAI

    mocker.patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock, return_value=mock_response)

    llm = get_standard_llm()
    response = await llm.ainvoke(
        [SystemMessage(content="You are a helpful assistant."), HumanMessage(content="Say hello.")]
    )

    assert response.content == "Standard response"
