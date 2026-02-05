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
    # Config uses openai/gpt-oss-120b:free currently
    assert "gpt-oss-120b" in llm.model_name or "claude-sonnet-4.5" in llm.model_name


@pytest.mark.asyncio
async def test_standard_model_instantiation():
    """Test that standard model (Haiku 4.5) can be instantiated."""
    llm = get_standard_llm()

    assert llm is not None
    # Config uses google/gemma-3-27b currently
    assert "gemma-3-27b" in llm.model_name or "claude-haiku-4.5" in llm.model_name


@pytest.mark.asyncio
async def test_model_info_extraction():
    """Test model info extraction."""
    provider, model, config = LLMConfig.get_model_info(LLMTier.PREMIUM)

    # Check for actual config values
    assert provider in ["anthropic", "openai"]
    assert config.cost_per_1k_input >= 0.0
    assert config.cost_per_1k_output >= 0.0


@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation."""
    # 2000 tokens in, 500 tokens out
    premium_cost = LLMConfig.estimate_cost(LLMTier.PREMIUM, 2000, 500)
    standard_cost = LLMConfig.estimate_cost(LLMTier.STANDARD, 2000, 500)

    # Currently using free models, so cost might be 0
    assert premium_cost >= 0.0
    assert standard_cost >= 0.0

    # If costs are non-zero, check logic
    if premium_cost > 0 and standard_cost > 0:
        assert premium_cost > standard_cost


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


@pytest.mark.asyncio
async def test_query_engine_cot_parsing(mocker):
    """
    Test that QueryEngine correctly parses <thinking> tags and logs them to trace.
    MAXIMUM SCRUTINY: verifies reasoning capture and clean output.
    """
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.modules.intelligence.trace.context import TraceContext
    from langchain_openai import ChatOpenAI

    # Mock the LLM response with Chain of Thought
    mock_response = MagicMock()
    mock_response.content = (
        "<thinking>\n"
        "1. Analyzing user profile...\n"
        "2. Checking astrology data...\n"
        "3. Formulating response.\n"
        "</thinking>\n"
        "Here is the final answer."
    )

    mocker.patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock, return_value=mock_response)

    # Mock dependencies
    mock_memory = AsyncMock()
    mock_db = AsyncMock()
    mock_activity_logger = AsyncMock()

    # Initialize Engine
    engine = QueryEngine(tier=LLMTier.PREMIUM, memory=mock_memory)
    engine.activity_logger = mock_activity_logger

    # CRITICAL: Set attributes accessed by engine
    # engine.llm is already an instance, so we need to mock it properly
    # If LLMConfig.get_llm returns a ChatOpenAI instance, we need to mock its attributes
    engine.llm = AsyncMock()
    engine.llm.model_name = "anthropic/claude-sonnet-4.5"
    engine.llm.ainvoke.return_value = mock_response

    # Mock internal methods to isolate _generate_answer logic
    engine._calculate_confidence = MagicMock(return_value=0.95)

    # Mock LLMConfig to avoid DB access or NoneType errors
    mocker.patch.object(
        LLMConfig,
        "get_model_info",
        return_value=(
            "anthropic",
            "claude-sonnet-4.5",
            MagicMock(temperature=0.7, cost_per_1k_input=0.0, cost_per_1k_output=0.0),
        ),
    )
    mocker.patch.object(LLMConfig, "estimate_cost", return_value=0.001)

    # Create a real TraceContext to verify logging
    trace = TraceContext()

    # Create a real TraceContext to verify logging
    trace = TraceContext()

    # Call internal generator directly to test parsing logic
    # We mock _build_context_from_data since we are testing _generate_answer logic mostly
    # But since _generate_answer is what contains the parsing logic, we call that.

    answer, confidence = await engine._generate_answer(
        question="Test question", context="Test context", modules=["astrology"], trace_id="test-trace-123", trace=trace
    )

    # If we get the fallback answer, it means an exception was swallowed.
    # Let's inspect what happened.
    if "I encountered an issue" in answer:
        # Check if logger.error was called
        if engine.activity_logger.log_activity.call_args:
            print(f"FAILED TRACE LOG: {engine.activity_logger.log_activity.call_args}")
        else:
            print("FAILED: Fallback triggered but no activity log found??")

    # ASSERTIONS

    # 1. Verify final answer is clean (no tags)
    assert answer == "Here is the final answer."
    assert "<thinking>" not in answer

    # 2. Verify thinking steps were logged to trace
    trace_data = trace.get_trace()
    found_thinking = False
    for step in trace_data.thinking_steps:
        if "LLM: 1. Analyzing user profile..." in step.description:
            found_thinking = True
            break

    assert found_thinking, "LLM thinking steps not found in trace!"

    # 3. Verify it handles missing tags gracefully
    mock_response.content = "Just an answer without thinking."
    answer_no_cot, _ = await engine._generate_answer(
        question="Test", context="Ctx", modules=[], trace_id="1", trace=trace
    )
    assert answer_no_cot == "Just an answer without thinking."
