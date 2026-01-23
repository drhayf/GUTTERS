---
name: project-import-conventions
description: Import paths and test conventions for GUTTERS codebase. Critical for avoiding common errors with module resolution and test mocking.
---

# Project Import Conventions

This codebase has specific import patterns. Following them prevents debugging time waste.

## Import Path Rules

### From Project Root (tests, scripts, commands)
```python
# ALWAYS use src.app prefix
from src.app.models.user import User
from src.app.modules.registry import ModuleRegistry
from src.app.core.ai.llm_factory import get_llm
from src.app.api.v1.intelligence import router
```

### Within src/app (relative imports OK)
```python
# In src/app/modules/intelligence/synthesis/synthesizer.py
from ....core.ai.llm_factory import get_llm       # Up 4 levels
from ....models.user_profile import UserProfile
from ...registry import ModuleRegistry            # Up 3 levels
from .schemas import SynthesisResponse            # Same directory
```

### Relative Import Depth Reference
```
src/app/modules/intelligence/synthesis/synthesizer.py
         │      │            │         └── . (same dir)
         │      │            └────────── .. (synthesis/)
         │      │            └────────── ... (intelligence/)
         │      └─────────────────────── .... (modules/)
         └────────────────────────────── ..... (app/)
```

---

## Test File Locations

### Module-Level Tests
```
src/app/modules/{layer}/{module}/tests/
├── __init__.py          # REQUIRED (empty is fine)
└── test_{module}.py
```

### Integration/E2E Tests
```
src/tests/integration/
├── __init__.py
└── test_{feature}_e2e.py
```

### Project Root Tests
```
tests/
├── conftest.py          # Fixtures using src.app imports
└── test_*.py
```

---

## Test Import Pattern

### In Test Files (ALWAYS use src.app)
```python
# ✅ CORRECT - Always use full path from project root
from src.app.modules.intelligence.synthesis import ProfileSynthesizer
from src.app.modules.registry import ModuleRegistry

# ❌ WRONG - Will fail with "No module named 'app'"
from app.modules.intelligence.synthesis import ProfileSynthesizer
```

### Running Tests
```bash
# From project root (c:\dev\FastAPI-boilerplate)
pytest src/app/modules/tests/test_registry.py -v

# NOT from src/ directory!
```

---

## Test Mocking Patterns

### Mocking Factory Functions (CORRECT)
```python
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_with_mocked_llm():
    """Patch factory at module import location."""
    from src.app.modules.intelligence.query import QueryEngine
    
    # Create mock LLM
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
        content='["astrology", "human_design"]'
    ))
    
    # Patch where it's IMPORTED, not where it's DEFINED
    with patch('src.app.modules.intelligence.query.engine.get_llm', 
               return_value=mock_llm):
        engine = QueryEngine()  # Create INSIDE the patch
        result = await engine._classify_question("test", "trace")
        assert "astrology" in result
```

### Common Mocking Mistakes
```python
# ❌ WRONG - Patching object attribute (property doesn't exist yet)
engine = QueryEngine()
with patch.object(engine, 'llm') as mock_llm:  # KeyError!
    ...

# ❌ WRONG - Patching at definition location
with patch('src.app.core.ai.llm_factory.get_llm', ...):  # Won't work
    ...

# ✅ CORRECT - Patch at import location
with patch('src.app.modules.intelligence.query.engine.get_llm', ...):
    ...
```

### Mocking Registry
```python
@pytest.mark.asyncio
async def test_with_mocked_registry():
    with patch('src.app.modules.intelligence.synthesis.synthesizer.ModuleRegistry') as mock_reg:
        mock_reg.get_calculated_modules_for_user = AsyncMock(return_value=["astrology"])
        mock_reg.get_user_profile_data = AsyncMock(return_value={"sun": "Leo"})
        
        synthesizer = ProfileSynthesizer()
        result = await synthesizer.synthesize_profile(1, mock_db)
```

---

## Conftest Pattern

### tests/conftest.py
```python
from src.app.core.config import settings
from src.app.main import app

# Note: uses src.app imports
```

### Module-Level conftest.py
```python
# src/app/modules/intelligence/synthesis/tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    """Mock async database session."""
    return AsyncMock()
```

---

## Common Errors and Fixes

### ModuleNotFoundError: No module named 'app'
**Cause:** Using `from app.` instead of `from src.app.`
**Fix:** Always use `src.app.` prefix in test files

### KeyError when patching object
**Cause:** Trying to patch a property on an instance
**Fix:** Patch the factory function at import location

### Tests pass locally but fail in CI
**Cause:** Running from wrong directory
**Fix:** Always run pytest from project root

---

## Quick Reference

| Context | Import Pattern |
|---------|----------------|
| Test files | `from src.app.modules...` |
| Within module | Relative `from .schemas import...` |
| scripts/ | `from src.app...` |
| Conftest | `from src.app...` |

| What to Mock | Where to Patch |
|--------------|----------------|
| `get_llm` in synthesizer | `src.app.modules.intelligence.synthesis.synthesizer.get_llm` |
| `get_llm` in engine | `src.app.modules.intelligence.query.engine.get_llm` |
| ModuleRegistry | `src.app.modules.{module}.{file}.ModuleRegistry` |
