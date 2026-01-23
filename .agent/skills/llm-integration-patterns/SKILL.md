---
name: llm-integration-patterns
description: Patterns for LLM integration in GUTTERS. Covers factory usage, prompt engineering, fallbacks, and activity logging.
---

# LLM Integration Patterns

Standard patterns for LLM usage in GUTTERS modules.

## LLM Factory

```python
from app.core.ai.llm_factory import get_llm

# Get configured LLM
llm = get_llm(
    model_id="anthropic/claude-3-haiku",  # Or from config
    temperature=0.7,  # Task-appropriate
)

# Async invocation (preferred)
response = await llm.ainvoke(prompt)
content = response.content
```

## Temperature Guidelines

| Task | Temperature | Why |
|------|-------------|-----|
| JSON generation | 0.3-0.5 | Needs structure consistency |
| Conversational probes | 0.7 | Natural variation |
| Creative synthesis | 0.8-1.0 | Unique insights |
| Classification | 0.0-0.3 | Deterministic |

## Prompt Engineering

### JSON Output Pattern
```python
prompt = f"""You are helping determine {field} for {context}.

Requirements:
- Return ONLY valid JSON
- No markdown formatting
- Include all required fields

Return JSON:
{{
    "field1": "...",
    "field2": [...],
    "mappings": {{...}}
}}

Generate now:"""
```

### Parsing JSON from LLM
```python
def _parse_llm_response(content: str) -> dict:
    import json
    
    try:
        # Try markdown block first
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "{" in content:
            # Find JSON bounds
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
        else:
            raise ValueError("No JSON found")
        
        return json.loads(json_str)
    except Exception:
        # Return minimal fallback
        return {"error": "parse_failed", "raw": content[:200]}
```

## Fallback Pattern

ALWAYS have fallback when LLM fails:

```python
async def generate_with_llm(input_data: InputData) -> Result:
    try:
        response = await llm.ainvoke(prompt)
        result = parse_response(response.content)
        return Result(**result)
        
    except Exception as e:
        logger.warning(f"LLM failed, using fallback: {e}")
        return _fallback_result(input_data)

def _fallback_result(input_data: InputData) -> Result:
    """Template-based fallback when LLM unavailable."""
    return Result(
        content=f"Default for {input_data.type}...",
        source="fallback",
    )
```

## Activity Logging (REQUIRED)

Every LLM call MUST be logged:

```python
from app.core.activity.logger import get_activity_logger

logger = get_activity_logger()

# Before call
await logger.log_activity(
    trace_id=trace_id,
    agent="module.component",
    activity_type="llm_call_started",
    details={
        "model": model_id,
        "prompt_length": len(prompt),
        "purpose": "generate_probe",
    }
)

# After call
await logger.log_llm_call(
    trace_id=trace_id,
    model_id=model_id,
    prompt=prompt[:500],  # Truncate for storage
    response=response.content[:500],
    duration_ms=duration,
    tokens_used=token_count,
    reasoning=reasoning,
)
```

## Error Handling

```python
from langchain_core.exceptions import OutputParserException

try:
    response = await llm.ainvoke(prompt)
except OutputParserException as e:
    logger.error(f"LLM output parsing failed: {e}")
    return fallback()
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    # Log to activity
    await logger.log_activity(
        agent="module",
        activity_type="llm_call_failed",
        details={"error": str(e)}
    )
    return fallback()
---

## Multi-Model User Preferences

Allow users to select their preferred LLM model.

### Allowed Models
```python
ALLOWED_MODELS = [
    "anthropic/claude-3.5-sonnet",      # Default
    "anthropic/claude-opus-4.5-20251101",  # Premium
    "qwen/qwen-2.5-72b-instruct:free",  # Testing
]
DEFAULT_MODEL = ALLOWED_MODELS[0]
```

### Storing Preferences
```python
# Store in UserProfile.data['preferences']['llm_model']
from sqlalchemy.orm.attributes import flag_modified

async def update_user_preference(user_id: int, key: str, value: Any, db: AsyncSession):
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

### Retrieving Preferences
```python
async def get_user_preferred_model(user_id: int, db: AsyncSession) -> str:
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile and profile.data:
        model = profile.data.get("preferences", {}).get("llm_model")
        if model in ALLOWED_MODELS:
            return model
    
    return DEFAULT_MODEL
```

### Per-Request Override
```python
@router.post("/query")
async def query(
    question: str,
    model: str | None = None,  # Optional override
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    user_id = current_user["id"]
    
    # Priority: request param > user preference > default
    if model and model in ALLOWED_MODELS:
        model_id = model
    else:
        model_id = await get_user_preferred_model(user_id, db)
    
    engine = QueryEngine(model_id=model_id)
    return await engine.answer_query(user_id, question, db)
```

---

## Checklist

- [ ] Use `get_llm()` factory (never instantiate directly)
- [ ] Set appropriate temperature for task
- [ ] Parse JSON with fallback handling
- [ ] Implement template fallback for failures
- [ ] Log activity before and after LLM calls
- [ ] Truncate prompts/responses for storage
- [ ] Handle all exception types
- [ ] Support user model preferences (if user-facing)
- [ ] Validate model against ALLOWED_MODELS

