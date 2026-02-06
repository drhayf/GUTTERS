"""
GUTTERS Intelligence Layer E2E Test

Tests the complete flow: registry → synthesis → query
Verifies extensibility with mock modules.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestIntelligenceE2E:
    """End-to-end tests for intelligence layer."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        from app.modules.registry import ModuleRegistry
        ModuleRegistry.clear()
        yield
        ModuleRegistry.clear()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session with profile data."""
        db = AsyncMock()

        # Mock profile with calculation data
        mock_profile = MagicMock()
        mock_profile.data = {
            "astrology": {
                "planets": [
                    {"name": "Sun", "sign": "Leo", "house": 5},
                    {"name": "Moon", "sign": "Cancer", "house": 4},
                ],
                "ascendant": {"sign": "Scorpio"}
            },
            "human_design": {
                "type": "Projector",
                "strategy": "Wait for Invitation",
                "authority": "Emotional",
                "profile": "4/6"
            },
            "numerology": {
                "life_path": {"number": 7},
                "expression": {"number": 3},
                "soul_urge": {"number": 5}
            }
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        db.execute.return_value = mock_result
        db.commit = AsyncMock()

        return db

    @pytest.fixture
    def register_mock_modules(self):
        """Register mock calculation modules."""
        from app.modules.registry import ModuleRegistry

        modules = []
        for name in ["astrology", "human_design", "numerology"]:
            module = MagicMock()
            module.name = name
            module.layer = "calculation"
            module.version = "1.0.0"
            module.description = f"Test {name} module"
            ModuleRegistry.register(module)
            modules.append(module)

        return modules

    @pytest.mark.asyncio
    async def test_registry_discovery(self, register_mock_modules):
        """Registry should discover all calculation modules."""
        from app.modules.registry import ModuleRegistry

        calc_modules = ModuleRegistry.get_all_calculation_modules()

        assert len(calc_modules) == 3
        names = {m.name for m in calc_modules}
        assert names == {"astrology", "human_design", "numerology"}

    @pytest.mark.asyncio
    async def test_calculated_modules_for_user(self, mock_db, register_mock_modules):
        """Should identify which modules have calculated for user."""
        from app.modules.registry import ModuleRegistry

        calculated = await ModuleRegistry.get_calculated_modules_for_user(1, mock_db)

        assert "astrology" in calculated
        assert "human_design" in calculated
        assert "numerology" in calculated

    @pytest.mark.asyncio
    async def test_synthesis_integration(self, mock_db, register_mock_modules):
        """Synthesis should work with all modules."""
        from app.modules.intelligence.synthesis import ProfileSynthesizer

        mock_llm_response = MagicMock()
        mock_llm_response.content = "Your Leo Sun and Projector type create a unique blend..."

        with patch('app.modules.intelligence.synthesis.synthesizer.get_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_get_llm.return_value = mock_llm

            synthesizer = ProfileSynthesizer()
            result = await synthesizer.synthesize_profile(1, mock_db)

            assert len(result.modules_included) == 3
            assert "astrology" in result.modules_included
            assert "Leo Sun" in result.synthesis or len(result.synthesis) > 0

    @pytest.mark.asyncio
    async def test_query_integration(self, mock_db, register_mock_modules):
        """Query should search across all modules."""
        from app.modules.intelligence.query import QueryEngine

        mock_llm_response = MagicMock()
        mock_llm_response.content = "Based on your Projector type, you struggle with..."

        mock_classify_response = MagicMock()
        mock_classify_response.content = '["astrology", "human_design"]'

        with patch('app.modules.intelligence.query.engine.get_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=[
                mock_classify_response,  # Classification
                mock_llm_response,  # Answer
            ])
            mock_get_llm.return_value = mock_llm

            engine = QueryEngine()
            result = await engine.answer_query(
                1,
                "Why do I struggle with authority?",
                mock_db
            )

            assert len(result.modules_consulted) > 0
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_extensibility_new_module(self, mock_db, register_mock_modules):
        """Adding new module should auto-integrate."""
        from app.modules.registry import ModuleRegistry

        # Add new "Gene Keys" module
        new_module = MagicMock()
        new_module.name = "gene_keys"
        new_module.layer = "calculation"
        new_module.version = "1.0.0"
        ModuleRegistry.register(new_module)

        # Verify it's now discoverable
        calc_modules = ModuleRegistry.get_all_calculation_modules()

        assert len(calc_modules) == 4
        names = {m.name for m in calc_modules}
        assert "gene_keys" in names

    @pytest.mark.asyncio
    async def test_full_flow(self, mock_db, register_mock_modules):
        """Test complete flow: discover → synthesize → query."""
        from app.modules.intelligence.query import QueryEngine
        from app.modules.intelligence.synthesis import ProfileSynthesizer
        from app.modules.registry import ModuleRegistry

        # 1. Discover modules
        modules = ModuleRegistry.get_all_calculation_modules()
        assert len(modules) == 3

        # 2. Get calculated modules
        calculated = await ModuleRegistry.get_calculated_modules_for_user(1, mock_db)
        assert len(calculated) == 3

        # 3. Synthesize (mocked LLM)
        mock_synthesis_response = MagicMock()
        mock_synthesis_response.content = "Unified synthesis of your cosmic design..."

        with patch('app.modules.intelligence.synthesis.synthesizer.get_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_synthesis_response)
            mock_get_llm.return_value = mock_llm

            synthesizer = ProfileSynthesizer()
            synthesis = await synthesizer.synthesize_profile(1, mock_db)

            assert synthesis.modules_included == calculated

        # 4. Query (mocked LLM)
        mock_classify_response = MagicMock()
        mock_classify_response.content = '["astrology"]'
        mock_query_response = MagicMock()
        mock_query_response.content = "Your question answered..."

        with patch('app.modules.intelligence.query.engine.get_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=[
                mock_classify_response,
                mock_query_response,
            ])
            mock_get_llm.return_value = mock_llm

            engine = QueryEngine()
            answer = await engine.answer_query(1, "What is my purpose?", mock_db)

            assert len(answer.answer) > 0


class TestModelSelection:
    """Test multi-model LLM support."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_user_preferred_model_default(self, mock_db):
        """Should return default when no preference set."""
        from app.modules.intelligence.synthesis import DEFAULT_MODEL, get_user_preferred_model

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        model = await get_user_preferred_model(1, mock_db)

        assert model == DEFAULT_MODEL

    @pytest.mark.asyncio
    async def test_get_user_preferred_model_custom(self, mock_db):
        """Should return user's preference when set."""
        from app.modules.intelligence.synthesis import get_user_preferred_model

        mock_profile = MagicMock()
        mock_profile.data = {
            "preferences": {
                "llm_model": "anthropic/claude-opus-4.5-20251101"
            }
        }
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute.return_value = mock_result

        model = await get_user_preferred_model(1, mock_db)

        assert model == "anthropic/claude-opus-4.5-20251101"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
