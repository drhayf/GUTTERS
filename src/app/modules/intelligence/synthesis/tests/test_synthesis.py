"""
Tests for ProfileSynthesizer

Verifies synthesis logic with mocked LLM.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestProfileSynthesizer:
    """Test ProfileSynthesizer functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response."""
        response = MagicMock()
        response.content = """Your cosmic profile reveals a powerful combination.

Your Leo Sun (Astrology) shines brightest when recognized for your creative leadership,
while your Projector type (Human Design) reminds you to wait for recognition rather than
pushing forward. Together, these create a unique dynamic: you have the fire and presence
of a natural leader, but your greatest success comes through invitation.

Your Life Path 3 (Numerology) adds creative expression to this mix, suggesting that your
leadership style is most magnetic when you're expressing yourself authentically.

The theme of recognition runs through all three systems - you're designed to be seen,
valued, and invited into positions of influence."""
        return response

    @pytest.mark.asyncio
    async def test_synthesize_with_no_modules(self, mock_db):
        """Should return placeholder when no modules calculated."""
        from src.app.modules.intelligence.synthesis import ProfileSynthesizer

        with patch('src.app.modules.intelligence.synthesis.synthesizer.ModuleRegistry') as mock_registry:
            mock_registry.get_calculated_modules_for_user = AsyncMock(return_value=[])

            synthesizer = ProfileSynthesizer()
            result = await synthesizer.synthesize_profile(1, mock_db)

            assert result.modules_included == []
            assert "No cosmic profiles" in result.synthesis

    @pytest.mark.asyncio
    async def test_extract_astrology_insights(self):
        """Should extract key insights from astrology data."""
        from src.app.modules.intelligence.synthesis import ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        astro_data = {
            "planets": [
                {"name": "Sun", "sign": "Leo", "house": 5},
                {"name": "Moon", "sign": "Cancer", "house": 4},
            ],
            "ascendant": {"sign": "Scorpio"}
        }

        insights = synthesizer._extract_key_insights("astrology", astro_data)

        assert insights.module_name == "astrology"
        assert any("Sun in Leo" in p for p in insights.key_points)
        assert any("Moon in Cancer" in p for p in insights.key_points)
        assert any("Scorpio" in p for p in insights.key_points)

    @pytest.mark.asyncio
    async def test_extract_human_design_insights(self):
        """Should extract key insights from Human Design data."""
        from src.app.modules.intelligence.synthesis import ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        hd_data = {
            "type": "Projector",
            "strategy": "Wait for Invitation",
            "authority": "Emotional",
            "profile": "4/6"
        }

        insights = synthesizer._extract_key_insights("human_design", hd_data)

        assert insights.module_name == "human_design"
        assert any("Projector" in p for p in insights.key_points)
        assert any("Wait for Invitation" in p for p in insights.key_points)

    @pytest.mark.asyncio
    async def test_extract_numerology_insights(self):
        """Should extract key insights from numerology data."""
        from src.app.modules.intelligence.synthesis import ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        num_data = {
            "life_path": {"number": 7},
            "expression": {"number": 3},
            "soul_urge": {"number": 5}
        }

        insights = synthesizer._extract_key_insights("numerology", num_data)

        assert insights.module_name == "numerology"
        assert any("Life Path: 7" in p for p in insights.key_points)
        assert any("Expression: 3" in p for p in insights.key_points)

    @pytest.mark.asyncio
    async def test_extract_themes_from_synthesis(self, mock_llm_response):
        """Should extract themes from synthesis text."""
        from src.app.modules.intelligence.synthesis import ProfileSynthesizer

        synthesizer = ProfileSynthesizer()
        themes = synthesizer._extract_themes(mock_llm_response.content)

        # Should find some themes
        assert isinstance(themes, list)
        assert len(themes) <= 5  # Limited to 5

    @pytest.mark.asyncio
    async def test_build_synthesis_prompt(self):
        """Should build formatted prompt."""
        from src.app.modules.intelligence.synthesis import ModuleInsights, ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        insights = {
            "astrology": ModuleInsights(
                module_name="astrology",
                key_points=["Sun in Leo", "Moon in Cancer"],
                raw_data={}
            )
        }

        prompt = synthesizer._build_synthesis_prompt(insights)

        assert "Sun in Leo" in prompt
        assert "Moon in Cancer" in prompt
        assert "Astrology" in prompt

    @pytest.mark.asyncio
    async def test_fallback_synthesis(self):
        """Should generate fallback when LLM fails."""
        from src.app.modules.intelligence.synthesis import ModuleInsights, ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        insights = {
            "astrology": ModuleInsights(
                module_name="astrology",
                key_points=["Sun in Leo"],
                raw_data={}
            )
        }

        fallback = synthesizer._fallback_synthesis(insights)

        assert "Sun in Leo" in fallback
        assert "Astrology" in fallback


class TestSynthesisPatterns:
    """Test pattern extraction."""

    @pytest.mark.asyncio
    async def test_detect_fire_generator_pattern(self):
        """Should detect fire sign + Generator pattern."""
        from src.app.modules.intelligence.synthesis import ModuleInsights, ProfileSynthesizer

        synthesizer = ProfileSynthesizer()

        insights = {
            "astrology": ModuleInsights(
                module_name="astrology",
                key_points=["Sun in Leo"],  # Fire sign
                raw_data={}
            ),
            "human_design": ModuleInsights(
                module_name="human_design",
                key_points=["Type: Generator"],  # Generator
                raw_data={}
            )
        }

        patterns = synthesizer._extract_patterns(insights)

        assert len(patterns) >= 1
        assert any(p.pattern_name == "Energetic Powerhouse" for p in patterns)

