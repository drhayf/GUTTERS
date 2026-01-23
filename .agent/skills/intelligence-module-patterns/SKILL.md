---
name: intelligence-module-patterns
description: Patterns for building intelligence layer modules (Synthesis, Query, etc.) that consume data from calculation modules via ModuleRegistry. Use when creating any intelligence layer component.
---

# Intelligence Module Patterns

Intelligence modules sit above calculation modules in the GUTTERS architecture. They consume, synthesize, and query data from multiple calculation modules.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Intelligence Layer                  │
│  ┌──────────────┐  ┌───────────────┐            │
│  │  Synthesis   │  │     Query     │            │
│  │   Module     │  │    Module     │            │
│  └──────┬───────┘  └───────┬───────┘            │
│         │                  │                     │
│         ▼                  ▼                     │
│  ┌──────────────────────────────────┐           │
│  │        ModuleRegistry            │           │
│  │ (auto-registration via BaseModule)│          │
│  └──────────────┬───────────────────┘           │
└─────────────────│───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Calculation Layer                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Astrology│  │   HD     │  │Numerology│       │
│  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────┘
```

---

## ModuleRegistry Integration

Every module auto-registers via `BaseModule.__init__`. Intelligence modules consume this registry.

### Getting Modules
```python
from src.app.modules.registry import ModuleRegistry

# Get all registered modules
all_modules = ModuleRegistry.get_all_modules()

# Filter by layer
calc_modules = ModuleRegistry.get_all_calculation_modules()
intel_modules = ModuleRegistry.get_all_intelligence_modules()

# Get specific module
astro = ModuleRegistry.get_module("astrology")

# Get modules that have calculated data for a user
calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)

# Get user's profile data from a specific module
astro_data = await ModuleRegistry.get_user_profile_data(user_id, db, "astrology")
```

### Auto-Registration (Happens Automatically)
```python
# In BaseModule.__init__:
if self.name:
    from src.app.modules.registry import ModuleRegistry
    ModuleRegistry.register(self)
```

---

## Intelligence Module Directory Structure

```
modules/intelligence/{module_name}/
├── __init__.py          # Re-exports
├── manifest.json        # Module metadata + LLM config
├── module.py            # Inherits BaseModule
├── schemas.py           # Pydantic models
├── {brain}.py           # Core logic (synthesizer.py, engine.py)
└── tests/
    ├── __init__.py
    └── test_{module}.py
```

---

## Synthesis Module Pattern

Aggregates data from all calculation modules into unified profile.

### manifest.json
```json
{
  "name": "synthesis",
  "layer": "intelligence",
  "subscriptions": ["module.profile_calculated"],
  "provides": ["unified_profile"],
  "llm": {
    "default_model": "anthropic/claude-3.5-sonnet",
    "temperature": 0.7
  }
}
```

### synthesizer.py Pattern
```python
from src.app.modules.registry import ModuleRegistry
from src.app.core.ai.llm_factory import get_llm

ALLOWED_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-opus-4.5-20251101",
    "qwen/qwen-2.5-72b-instruct:free",
]
DEFAULT_MODEL = ALLOWED_MODELS[0]

class ProfileSynthesizer:
    def __init__(self, model_id: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model_id = model_id
        self.temperature = temperature
        self._llm = None  # Lazy load
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm(self.model_id, self.temperature)
        return self._llm
    
    async def synthesize_profile(self, user_id: int, db: AsyncSession):
        # 1. Get calculated modules for this user
        calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
        
        if not calculated:
            return self._empty_synthesis()
        
        # 2. Gather data from each module
        module_data = {}
        for module_name in calculated:
            data = await ModuleRegistry.get_user_profile_data(user_id, db, module_name)
            module_data[module_name] = data
        
        # 3. Extract insights per module
        insights = {name: self._extract_insights(name, data) 
                   for name, data in module_data.items()}
        
        # 4. Build LLM prompt and call
        try:
            prompt = self._build_synthesis_prompt(insights)
            response = await self.llm.ainvoke([...])
            return self._parse_response(response)
        except Exception:
            return self._fallback_synthesis(insights)
```

---

## Query Module Pattern

Answers natural language questions by searching relevant modules.

### engine.py Pattern
```python
class QueryEngine:
    async def answer_query(self, user_id: int, question: str, db: AsyncSession):
        # 1. Classify which modules are relevant
        relevant_modules = await self._classify_question(question)
        
        # 2. Get calculated modules that match
        calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
        matching = [m for m in relevant_modules if m in calculated]
        
        # 3. Build context from matching modules
        context = await self._build_context(user_id, matching, db)
        
        # 4. Generate answer with LLM
        answer = await self._generate_answer(question, context)
        
        return QueryResponse(
            answer=answer,
            modules_consulted=matching,
            confidence=self._calculate_confidence(context, matching)
        )
    
    async def _classify_question(self, question: str) -> list[str]:
        """Use LLM to determine which modules are relevant."""
        prompt = f"""Which systems are relevant to answer: "{question}"?
        Options: astrology, human_design, numerology
        Return JSON array only: ["system1", "system2"]"""
        
        try:
            response = await self.llm.ainvoke([...])
            return self._parse_json_list(response.content)
        except Exception:
            # Fallback: consult all
            return ["astrology", "human_design", "numerology"]
```

---

## Multi-Model User Preferences

Store and retrieve user's preferred LLM model.

### Storage Location
```python
# In UserProfile.data['preferences']['llm_model']
{
    "astrology": {...},
    "human_design": {...},
    "preferences": {
        "llm_model": "anthropic/claude-3.5-sonnet"
    }
}
```

### Helper Functions
```python
async def get_user_preferred_model(user_id: int, db: AsyncSession) -> str:
    """Get user's preferred LLM model or default."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile and profile.data:
        prefs = profile.data.get("preferences", {})
        model = prefs.get("llm_model")
        if model in ALLOWED_MODELS:
            return model
    
    return DEFAULT_MODEL

async def update_user_preference(
    user_id: int, 
    key: str, 
    value: Any, 
    db: AsyncSession
):
    """Update a user preference in UserProfile.data."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise ValueError(f"No profile for user {user_id}")
    
    if not profile.data:
        profile.data = {}
    
    if "preferences" not in profile.data:
        profile.data["preferences"] = {}
    
    profile.data["preferences"][key] = value
    flag_modified(profile, "data")
    await db.commit()
```

---

## API Endpoint Pattern

Intelligence modules expose endpoints under `/api/v1/intelligence/`.

```python
from fastapi import APIRouter, Depends
from src.app.api.dependencies import get_current_user, async_get_db

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.post("/profile/synthesis")
async def trigger_synthesis(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    model: str | None = None,  # Optional override
):
    user_id = current_user["id"]
    
    # Get model (override > preference > default)
    if model and model in ALLOWED_MODELS:
        model_id = model
    else:
        model_id = await get_user_preferred_model(user_id, db)
    
    synthesizer = ProfileSynthesizer(model_id=model_id)
    result = await synthesizer.synthesize_profile(user_id, db)
    return result
```

---

## Checklist

- [ ] Inherits `BaseModule` with `layer = "intelligence"`
- [ ] Uses `ModuleRegistry` to access calculation module data
- [ ] Implements `contribute_to_synthesis()` (even if empty for query-only modules)
- [ ] Has `_fallback_*` methods for LLM failures
- [ ] Stores user preferences in `UserProfile.data['preferences']`
- [ ] API endpoints have auth dependencies
- [ ] Tests patch `get_llm` at module import location

---

## Key Imports

```python
# Always use src.app prefix from project root
from src.app.modules.registry import ModuleRegistry
from src.app.modules.base import BaseModule
from src.app.core.ai.llm_factory import get_llm
from src.app.models.user_profile import UserProfile
```
