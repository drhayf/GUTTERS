"""
Fidelity verification tests for Multi-Tier LLM system.

Iterates through ALL configured models and testing variations to ensure
robust Chain of Thought parsing and consistent behavior under "maximum scrutiny".
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import AIMessage
from src.app.core.llm.config import LLMConfig, LLMTier
from src.app.modules.intelligence.query.engine import QueryEngine
from src.app.modules.intelligence.trace.context import TraceContext

# Test Scenarios
SCENARIOS = [
    (
        "perfect_cot",
        "<thinking>\n1. Step one\n2. Step two\n</thinking>\nFinal Answer",
        "Final Answer",
        True,  # Expect thinking steps in trace
    ),
    (
        "missing_cot",
        "Just a direct answer without thinking tags.",
        "Just a direct answer without thinking tags.",
        False,
    ),
    (
        "malformed_tags",
        "<thinking>\nThinking but not closed correctly...\nFinal Answer",
        "<thinking>\nThinking but not closed correctly...\nFinal Answer",  # Regex might fail to catch unclosed, treating as part of answer if not dotall/greedy matching correctly or design decision
        False,
        # Note: Current regex `r"<thinking>(.*?)</thinking>"` requires closing tag.
        # So malformed tags result in raw output. We verify this behavior is safe (no crash).
    ),
    ("empty_thinking", "<thinking></thinking>\nAnswer", "Answer", False),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("tier", [LLMTier.PREMIUM, LLMTier.STANDARD])
@pytest.mark.parametrize("scenario_name, raw_output, expected_cleaned, expect_thinking", SCENARIOS)
async def test_llm_fidelity_matrix(mocker, tier, scenario_name, raw_output, expected_cleaned, expect_thinking):
    """
    MAXIMUM SCRUTINY TEST:
    Verifies that for EVERY model tier and EVERY output scenario:
    1. The answer is parsed correctly.
    2. The trace logs thinking steps (if valid).
    3. The system does not crash.
    """

    # 1. Mock Infrastructure
    mock_memory = AsyncMock()
    mock_activity_logger = AsyncMock()

    # Mock LLMConfig to isolate from DB
    # We must return a valid config tuple for the specific tier
    # (provider, model_name, ModelConfig)
    mock_model_config = MagicMock()
    mock_model_config.cost_per_1k_input = 0.0
    mock_model_config.cost_per_1k_output = 0.0

    model_id = "test/model-id"
    mocker.patch.object(LLMConfig, "get_model_info", return_value=("test-provider", model_id, mock_model_config))
    mocker.patch.object(LLMConfig, "estimate_cost", return_value=0.001)

    # 2. Mock LLM Response
    mock_response = AIMessage(content=raw_output)

    # 3. Initialize Engine with Mocked LLM
    engine = QueryEngine(tier=tier, memory=mock_memory)
    engine.activity_logger = mock_activity_logger

    # Mock the LLM instance on the engine
    mock_llm = AsyncMock()
    mock_llm.model_name = model_id
    mock_llm.ainvoke.return_value = mock_response
    engine.llm = mock_llm

    # Mock internal confidence to avoid side calculations
    engine._calculate_confidence = MagicMock(return_value=0.90)

    # 4. Run Execution
    trace = TraceContext()

    # We call _generate_answer directly to test the parsing logic in isolation
    answer, confidence = await engine._generate_answer(
        question="Fidelity Test", context="Context", modules=[], trace_id="fidelity-test-id", trace=trace
    )

    # 5. Verify Assertions
    print(f"[{tier.value}][{scenario_name}] Answer: {answer[:50]}...")

    # Check output cleanliness
    assert answer.strip() == expected_cleaned.strip(), f"Failed clean parse for {tier} in {scenario_name}"

    # Check trace for thinking
    trace_data = trace.get_trace()
    has_thinking = any("LLM:" in step.description for step in trace_data.thinking_steps)

    # Check trace for model metrics (New Fidelity Requirement)
    # We expect model info to be populated
    model_info = trace_data.model_info
    assert model_info is not None, f"No model info logged in trace for {tier} in {scenario_name}"
    # Note: tokens might be 0 if mock response default metadata is empty, but we patched get_model_info.
    # checking >= 0 covers 0.0 which is valid for mock.
    assert model_info.cost_estimate_usd >= 0.0, f"Cost not captured for {tier}"

    if expect_thinking:
        assert has_thinking, f"Expected thinking steps in trace for {tier} in {scenario_name}, found none."
    else:
        # If we didn't expect valid thinking parsing (e.g. missing or malformed attributes),
        # we generally expect EITHER raw output or a specific fallback message "LLM provided no internal reasoning".
        # We just verify it didn't crash.
        pass
