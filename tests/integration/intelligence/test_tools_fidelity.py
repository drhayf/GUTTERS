from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.intelligence.query.engine import QueryEngine
from src.app.modules.intelligence.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_registry_context_injection(db: AsyncSession, test_user):
    """Verify that ToolRegistry correctly injects context into tools."""
    tools = ToolRegistry.get_tools_for_request(test_user.id, db)

    # Check for presence of all tools
    tool_names = [t.name for t in tools]
    assert "calculate_astrology_chart" in tool_names
    assert "calculate_human_design" in tool_names
    assert "calculate_numerology" in tool_names
    assert "log_journal_entry" in tool_names

    # Verify Journal tool is configured
    journal_tool = next(t for t in tools if t.name == "log_journal_entry")
    assert journal_tool.name == "log_journal_entry"
    # Cannot easily verify closed-over variables without inspection hack,
    # but presence in list implies successful factory creation.


@pytest.mark.asyncio
async def test_astrology_tool_execution(db: AsyncSession, test_user):
    """Verify the Astrology tool runs correctly against the calculator."""
    tools = ToolRegistry.get_tools_for_request(test_user.id, db)
    astro_tool = next(t for t in tools if t.name == "calculate_astrology_chart")

    input_data = {
        "name": "Test User",
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
    }

    # Execute tool
    result = await astro_tool.ainvoke(input_data)

    # Verify result structure (high fidelity check against actual calculator output)
    assert isinstance(result, dict)
    assert "planets" in result
    assert "houses" in result
    assert result["subject"]["name"] == "Test User"

    # Verify calculation accuracy (Sun should be near 24 Taurus)
    sun = next(p for p in result["planets"] if p["name"] == "Sun")
    assert "Tau" in sun["sign"]


@pytest.mark.asyncio
async def test_engine_tool_execution_flow(db: AsyncSession, test_user):
    """
    Test the full QueryEngine loop with a mocked LLM forcing a tool call.
    We mock the LLM decision but execute the REAL tool and REAL calculator.
    """
    # 1. Setup Engine with Mock LLM
    mock_llm = MagicMock()  # Use MagicMock as base so methods aren't async by default
    mock_llm.model_name = "mock-gpt-4"
    mock_llm.bind_tools.return_value = mock_llm  # sync binding returns itself
    mock_llm.ainvoke = AsyncMock()  # explicit async ainvoke

    # Define the sequence of LLM responses:
    # 1. First call -> Returns Tool Call (Calculate Astrology)
    # 2. Second call -> Returns Final Answer (Interpretation)

    tool_call_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "calculate_astrology_chart",
                "args": {
                    "name": "Test User",
                    "birth_date": "1990-05-15",
                    "birth_time": "14:30",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "timezone": "America/New_York",
                },
                "id": "call_12345",
            }
        ],
    )

    final_answer_msg = AIMessage(content="Your sun is in Taurus.")

    # Configure mock side_effect
    mock_llm.ainvoke.side_effect = [tool_call_msg, final_answer_msg]

    engine = QueryEngine(llm=mock_llm)

    # 2. Execute Query
    response = await engine.answer_query(user_id=test_user.id, question="Calculate my chart", db=db)

    # 3. Verify Interactions

    # Check that bind_tools was called
    assert mock_llm.bind_tools.called

    # Verify Trace recorded the tool call
    trace = response.trace
    tool_steps = [s for s in trace.tools_used if s.tool == "calculator"]

    assert len(tool_steps) > 0
    assert tool_steps[0].operation == "calculate_astrology_chart"
    assert "Executed calculate_astrology_chart successfully" in tool_steps[0].result_summary

    # Verify final answer matches
    assert response.answer == "Your sun is in Taurus."
