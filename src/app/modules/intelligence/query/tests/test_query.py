"""
Tests for QueryEngine

Verifies question classification and answer generation.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestQueryEngine:
    """Test QueryEngine functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response."""
        response = MagicMock()
        response.content = "Based on your Leo Sun (Astrology) and Projector type (Human Design), you struggle with authority because..."
        return response

    @pytest.mark.asyncio
    async def test_classify_question_boundaries(self):
        """Should classify boundary question to relevant modules."""
        from src.app.modules.intelligence.query import QueryEngine

        # Create a mock LLM that returns the expected response
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '["astrology", "human_design"]'
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        # Patch get_llm at the module where it's imported
        with patch('src.app.modules.intelligence.query.engine.get_llm', return_value=mock_llm):
            engine = QueryEngine()
            modules = await engine._classify_question("Why do I struggle with boundaries?", "trace-123")

            assert "astrology" in modules or "human_design" in modules

    @pytest.mark.asyncio
    async def test_classify_question_fallback(self):
        """Should return all modules on classification failure."""
        from src.app.modules.intelligence.query import QueryEngine

        # Create a mock LLM that raises an exception
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM failed"))

        # Patch get_llm at the module where it's imported
        with patch('src.app.modules.intelligence.query.engine.get_llm', return_value=mock_llm):
            engine = QueryEngine()
            modules = await engine._classify_question("What is my purpose?", "trace-123")

            # Should fallback to all modules
            assert "astrology" in modules
            assert "human_design" in modules
            assert "numerology" in modules

    @pytest.mark.asyncio
    async def test_parse_json_list_valid(self):
        """Should parse valid JSON list."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        result = engine._parse_json_list('["astrology", "human_design"]')

        assert result == ["astrology", "human_design"]

    @pytest.mark.asyncio
    async def test_parse_json_list_with_markdown(self):
        """Should extract JSON from markdown response."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        content = 'Here are the relevant systems: ["astrology", "numerology"]'
        result = engine._parse_json_list(content)

        assert "astrology" in result
        assert "numerology" in result

    @pytest.mark.asyncio
    async def test_parse_json_list_invalid(self):
        """Should return empty list for invalid JSON."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        result = engine._parse_json_list("not valid json at all")

        assert result == []

    @pytest.mark.asyncio
    async def test_format_astrology_context(self):
        """Should format astrology data into context."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        data = {
            "planets": [
                {"name": "Sun", "sign": "Leo", "house": 5},
                {"name": "Moon", "sign": "Cancer", "house": 4},
            ],
            "ascendant": {"sign": "Scorpio"}
        }

        context = engine._format_astrology_context(data)

        assert "Sun: Leo" in context
        assert "Moon: Cancer" in context
        assert "Scorpio" in context

    @pytest.mark.asyncio
    async def test_format_human_design_context(self):
        """Should format Human Design data into context."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        data = {
            "type": "Projector",
            "strategy": "Wait for Invitation",
            "authority": "Emotional",
            "profile": "4/6"
        }

        context = engine._format_human_design_context(data)

        assert "Projector" in context
        assert "Wait for Invitation" in context

    @pytest.mark.asyncio
    async def test_format_numerology_context(self):
        """Should format numerology data into context."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        data = {
            "life_path": {"number": 7},
            "expression": {"number": 3},
            "soul_urge": {"number": 5}
        }

        context = engine._format_numerology_context(data)

        assert "Life Path: 7" in context
        assert "Expression: 3" in context

    @pytest.mark.asyncio
    async def test_calculate_confidence(self):
        """Should calculate confidence based on context."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        # Good context
        confidence = engine._calculate_confidence("x" * 600, ["astrology", "human_design", "numerology"])
        assert confidence > 0.8

        # Poor context
        confidence = engine._calculate_confidence("short", ["astrology"])
        assert confidence < 0.5

    @pytest.mark.asyncio
    async def test_fallback_answer(self):
        """Should generate fallback answer."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        answer = engine._fallback_answer(
            "Why am I like this?",
            "Sun in Leo, Projector type"
        )

        assert "Why am I like this?" in answer
        assert "Sun in Leo" in answer

    @pytest.mark.asyncio
    async def test_answer_query_no_modules(self, mock_db):
        """Should return error when no calculated modules."""
        from src.app.modules.intelligence.query import QueryEngine

        engine = QueryEngine()

        with patch('src.app.modules.intelligence.query.engine.ModuleRegistry') as mock_registry:
            mock_registry.get_calculated_modules_for_user = AsyncMock(return_value=[])

            # Mock classification to return modules
            with patch.object(engine, '_classify_question', return_value=["astrology"]):
                response = await engine.answer_query(1, "Why am I like this?", mock_db)

                assert response.confidence == 0.0
                assert "not have enough" in response.answer.lower() or len(response.modules_consulted) == 0

