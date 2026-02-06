"""
Tests for ModuleRegistry

Verifies module registration, retrieval, and filtering.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestModuleRegistry:
    """Test ModuleRegistry functionality."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        from src.app.modules.registry import ModuleRegistry
        ModuleRegistry.clear()
        yield
        ModuleRegistry.clear()

    @pytest.fixture
    def mock_module(self):
        """Create a mock module."""
        module = MagicMock()
        module.name = "test_module"
        module.layer = "calculation"
        module.version = "1.0.0"
        module.description = "Test module"
        return module

    def test_register_module(self, mock_module):
        """Should register a module by name."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)

        assert "test_module" in ModuleRegistry.get_module_names()
        assert ModuleRegistry.get_module("test_module") == mock_module

    def test_register_module_without_name(self):
        """Should skip module without name."""
        from src.app.modules.registry import ModuleRegistry

        module = MagicMock()
        module.name = ""

        ModuleRegistry.register(module)

        assert len(ModuleRegistry.get_module_names()) == 0

    def test_get_module_not_found(self):
        """Should return None for unknown module."""
        from src.app.modules.registry import ModuleRegistry

        result = ModuleRegistry.get_module("nonexistent")

        assert result is None

    def test_get_all_modules(self, mock_module):
        """Should return all registered modules."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)

        module2 = MagicMock()
        module2.name = "module2"
        module2.layer = "intelligence"
        ModuleRegistry.register(module2)

        all_modules = ModuleRegistry.get_all_modules()

        assert len(all_modules) == 2
        names = {m.name for m in all_modules}
        assert names == {"test_module", "module2"}

    def test_get_all_calculation_modules(self, mock_module):
        """Should filter by calculation layer."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)

        intel_module = MagicMock()
        intel_module.name = "intel"
        intel_module.layer = "intelligence"
        ModuleRegistry.register(intel_module)

        calc_modules = ModuleRegistry.get_all_calculation_modules()

        assert len(calc_modules) == 1
        assert calc_modules[0].name == "test_module"

    def test_get_all_intelligence_modules(self, mock_module):
        """Should filter by intelligence layer."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)

        intel_module = MagicMock()
        intel_module.name = "intel"
        intel_module.layer = "intelligence"
        ModuleRegistry.register(intel_module)

        intel_modules = ModuleRegistry.get_all_intelligence_modules()

        assert len(intel_modules) == 1
        assert intel_modules[0].name == "intel"

    def test_unregister_module(self, mock_module):
        """Should unregister a module."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)
        assert "test_module" in ModuleRegistry.get_module_names()

        ModuleRegistry.unregister("test_module")

        assert "test_module" not in ModuleRegistry.get_module_names()

    def test_clear_registry(self, mock_module):
        """Should clear all modules."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_module)
        assert len(ModuleRegistry.get_module_names()) > 0

        ModuleRegistry.clear()

        assert len(ModuleRegistry.get_module_names()) == 0


class TestModuleRegistryWithDatabase:
    """Test registry methods that require database."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        from src.app.modules.registry import ModuleRegistry
        ModuleRegistry.clear()
        yield
        ModuleRegistry.clear()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_calc_module(self):
        """Create mock calculation module."""
        module = MagicMock()
        module.name = "astrology"
        module.layer = "calculation"
        return module

    @pytest.mark.asyncio
    async def test_get_calculated_modules_empty(self, mock_db, mock_calc_module):
        """Should return empty list when no profile exists."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_calc_module)

        # Mock no profile found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        calculated = await ModuleRegistry.get_calculated_modules_for_user(1, mock_db)

        assert calculated == []

    @pytest.mark.asyncio
    async def test_get_calculated_modules_with_data(self, mock_db, mock_calc_module):
        """Should return modules that have data."""
        from src.app.modules.registry import ModuleRegistry

        ModuleRegistry.register(mock_calc_module)

        # Mock profile with astrology data
        mock_profile = MagicMock()
        mock_profile.data = {"astrology": {"sun": "Leo"}}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute.return_value = mock_result

        calculated = await ModuleRegistry.get_calculated_modules_for_user(1, mock_db)

        assert "astrology" in calculated

    @pytest.mark.asyncio
    async def test_get_user_profile_data(self, mock_db):
        """Should get profile data for user."""
        from src.app.modules.registry import ModuleRegistry

        mock_profile = MagicMock()
        mock_profile.data = {
            "astrology": {"sun": "Leo"},
            "human_design": {"type": "Projector"}
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute.return_value = mock_result

        # Get all data
        all_data = await ModuleRegistry.get_user_profile_data(1, mock_db)
        assert "astrology" in all_data
        assert "human_design" in all_data

        # Get specific module
        mock_db.execute.return_value = mock_result
        astro_data = await ModuleRegistry.get_user_profile_data(1, mock_db, "astrology")
        assert astro_data == {"sun": "Leo"}

