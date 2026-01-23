---
name: production-implementation-standards
description: Enforces production-ready implementation standards. NO mocks, NO workarounds, NO shortcuts. Use for every implementation to ensure maximum fidelity and sophistication.
---

# Production Implementation Standards

EVERY implementation MUST meet these standards. No exceptions, no shortcuts.

## Core Principles

1. **NO MOCKS in production code** - Only in tests
2. **NO HARDCODED VALUES** - All config from database
3. **NO WORKAROUNDS** - Fix properly or don't implement
4. **FULL TYPE HINTS** - No `Any`, no untyped functions
5. **PYDANTIC SCHEMAS** - All data structures validated
6. **SEPARATION OF CONCERNS** - Clear boundaries

---

## File Organization

### Correct Structure
```
modules/{layer}/{module_name}/
├── __init__.py         # Exports only
├── module.py           # BaseModule subclass
├── schemas.py          # Pydantic models (input/output)
├── service.py          # Business logic (pure functions)
├── models.py           # SQLAlchemy (only if DB tables needed)
├── crud.py             # FastCRUD operations
├── refinement/         # Genesis handlers (if applicable)
│   └── __init__.py
└── tests/
    ├── __init__.py
    └── test_{module}.py
```

### Common Mistakes
❌ Logic in `__init__.py`
❌ Database calls in `schemas.py`
❌ Business logic in `module.py`
❌ Tests outside `tests/` directory

---

## Configuration

### Database Config (REQUIRED)
```python
# CORRECT: Load from database
async def initialize(self):
    async for db in async_get_db():
        result = await db.execute(
            select(SystemConfiguration).where(
                SystemConfiguration.module_name == self.name,
                SystemConfiguration.is_active == True
            )
        )
        config = result.scalar_one_or_none()
        self.config = config.config if config else self.default_config()
```

### Hardcoded Values (NEVER)
```python
# ❌ WRONG
threshold = 8
orb_size = 6.0
strategy = "default"

# ✅ CORRECT
threshold = self.config.get("threshold", 8)
orb_size = self.config.get("orb_size", 6.0)
strategy = self.config.get("strategy", "default")
```

---

## Type Hints

### Full Typing (REQUIRED)
```python
# ❌ WRONG
def calculate(data):
    return result

async def process(items):
    ...

# ✅ CORRECT
def calculate(data: BirthDataComplete) -> ProfileResult:
    return ProfileResult(...)

async def process(items: list[UncertaintyField]) -> list[Hypothesis]:
    ...
```

### No Any (EVER)
```python
# ❌ WRONG
def get_data() -> Any:
def process(data: Any) -> dict:

# ✅ CORRECT
def get_data() -> ProfileData:
def process(data: InputSchema) -> OutputSchema:
```

---

## Error Handling

### Explicit Errors (REQUIRED)
```python
# ❌ WRONG - Silent failure
try:
    result = calculate()
except:
    pass

# ❌ WRONG - Generic error
except Exception as e:
    raise Exception("Error")

# ✅ CORRECT - Specific handling
try:
    result = calculate(input_data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise HTTPException(status_code=422, detail=str(e))
except CalculationError as e:
    logger.error(f"Calculation failed for user {user_id}: {e}")
    # Fallback or re-raise with context
```

### Logging (REQUIRED for errors)
```python
import logging
logger = logging.getLogger(__name__)

# Always log errors with context
logger.error(f"Failed to {action} for user {user_id}: {e}")
logger.warning(f"Fallback used for {context}")
```

---

## Testing Standards

### Coverage (80% minimum)
```python
# MUST test:
# 1. Initialization
# 2. Core calculation/logic
# 3. Edge cases
# 4. Integration points

@pytest.mark.asyncio
async def test_module_initializes():
    """Module loads config from database."""
    
@pytest.mark.asyncio
async def test_calculation_with_known_data():
    """Calculation returns expected result."""
    
@pytest.mark.asyncio
async def test_handles_missing_data():
    """Graceful handling of incomplete input."""
    
@pytest.mark.asyncio
async def test_publishes_events():
    """Events emitted correctly."""
```

### No Mocks for Core Logic
```python
# ❌ WRONG - Mocking the thing you're testing
@patch('module.calculate')
def test_calculate():
    mock_calculate.return_value = expected
    assert calculate() == expected  # Tests nothing!

# ✅ CORRECT - Test actual logic
def test_calculate():
    result = calculate(known_input)
    assert result == expected_output
```

---

## API Endpoints

### Authentication (ALWAYS)
```python
# ❌ WRONG - No auth
@router.get("/{user_id}")
async def get_data(user_id: int):
    ...

# ✅ CORRECT - With auth
@router.get("/{user_id}")
async def get_data(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    # Verify access
    if current_user["id"] != user_id and not current_user.get("is_superuser"):
        raise HTTPException(403, "Not authorized")
```

### Response Schemas (ALWAYS)
```python
# ❌ WRONG - Untyped response
@router.get("/data")
async def get_data():
    return {"some": "data"}

# ✅ CORRECT - Typed response
@router.get("/data", response_model=DataResponse)
async def get_data() -> DataResponse:
    return DataResponse(...)
```

---

## Database Operations

### Transactions (REQUIRED for multi-step)
```python
# ❌ WRONG - No transaction
await crud.create(db, obj1)
await crud.create(db, obj2)  # If this fails, obj1 still exists

# ✅ CORRECT - Transaction
async with db.begin():
    await crud.create(db, obj1)
    await crud.create(db, obj2)
```

### Migrations (REQUIRED for schema changes)
```bash
# ALWAYS create migration for model changes
alembic revision --autogenerate -m "Add {table/column}"
alembic upgrade head
```

---

## Pre-Commit Checklist

Before considering any implementation complete:

- [ ] All functions have full type hints
- [ ] All data structures use Pydantic schemas
- [ ] All config loaded from database (not hardcoded)
- [ ] All errors logged with context
- [ ] All API endpoints have auth + response schemas
- [ ] All tests pass (80%+ coverage)
- [ ] All integrations wired (see `gutters-system-integration` skill)
- [ ] No `Any` types
- [ ] No `pass` in except blocks
- [ ] No TODO/FIXME in production code
- [ ] Migrations created for DB changes
