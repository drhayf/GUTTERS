# GUTTERS

AI-powered cosmic intelligence system for metaphysical self-knowledge. 18+ modular systems (astrology, Human Design, numerology, etc.) with event-driven architecture and master AI synthesis.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Next.js 14  
**Package Manager:** `uv`

## Project Structure
```
src/app/
├── core/              # Event bus, Active Memory, AI synthesis
├── models/            # SQLAlchemy (all JSONB for flexibility)
├── schemas/           # Pydantic validation
├── modules/           # 18+ independent modules
│   ├── calculation/   # Birth data (10 modules)
│   ├── tracking/      # Cosmic data (3 modules)
│   └── intelligence/  # AI synthesis (5+ modules)
└── migrations/        # Alembic
```

## Commands
```bash
# Development
uv run uvicorn app.main:app --reload

# Tests (REQUIRED before commit)
uv run pytest
uv run pytest --cov=app tests/

# Migrations (ALWAYS after model changes)
cd src && uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Type check
uv run mypy src/app

# Lint/format
uv run ruff check src/app
uv run ruff format src/app
```

## Critical Rules

### NEVER (Production Quality Only)

❌ **Hardcode configurations** - Use `system_configurations` table (JSONB)  
❌ **Hardcode prompts** - Load from database  
❌ **Mock/placeholder data** - All implementations complete  
❌ **Static configurations** - Everything dynamic, database-driven  
❌ **Skip type hints** - Every function fully typed  
❌ **Use `any` types** - Defeats type safety  
❌ **Skip tests** - Minimum 80% coverage  
❌ **Bypass migrations** - ALWAYS generate after model changes  
❌ **Hardcode orbs, thresholds, parameters** - Database JSONB configs  
❌ **Commit secrets** - Use `.env` (gitignored)

### ALWAYS (Non-Negotiable)

✅ **Load configs from database** - `system_configurations.config` (JSONB)  
✅ **Full type annotations** - `async def func(param: Type) -> ReturnType:`  
✅ **Pydantic validation** - All API inputs/outputs  
✅ **Async/await** - All I/O operations  
✅ **Test before commit** - `uv run pytest` must pass  
✅ **Migration after models** - Review auto-generated SQL  
✅ **Dynamic everything** - No hardcoded magic numbers  
✅ **Production-ready** - Complete implementations, no shortcuts

## Module Development Pattern

**Every module MUST inherit `BaseModule` and follow this structure:**
```
modules/{layer}/{name}/
├── module.py      # Inherits BaseModule
├── schemas.py     # Pydantic validation
├── service.py     # Business logic
└── tests/
```

**Required methods:**
- `async def initialize()` - Load config from DB, subscribe to events
- `async def contribute_to_synthesis(user_id)` - Return structured data

**See:** `skills/module-implementation/SKILL.md` for complete pattern

## Database Standards

**Models:**
- Use `Mapped[type]` annotations (SQLAlchemy 2.0)
- JSONB for flexible data (profiles, configs, observations)
- Always: `id`, `created_at`, `updated_at`
- Foreign keys indexed

**Migrations:**
```bash
# After ANY model change
cd src && uv run alembic revision --autogenerate -m "add X table"
# REVIEW generated SQL before applying
uv run alembic upgrade head
```

## Configuration Management

**Environment secrets (.env):**
```bash
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_SERVER=db.supabase.co
OPENROUTER_API_KEY=sk-or-v1-...
SECRET_KEY=<openssl rand -hex 32>
```

**Module configs (database JSONB):**
```python
# Load from system_configurations table
config = await db.query(SystemConfiguration).filter(
    SystemConfiguration.module_name == "astrology"
).first()

orb = config.config.get("orb_tolerance", 8)  # NEVER hardcode
```

## Type Safety
```python
# CORRECT
async def calculate_chart(
    birth_datetime: datetime,
    latitude: float,
    longitude: float
) -> NatalChartData:
    # Fully typed

# WRONG
async def calculate_chart(birth_datetime, latitude, longitude):
    # No types - NEVER do this
```

## Event Communication
```python
# Publish
from app.core.events import event_bus
await event_bus.publish("cosmic.storm.detected", {"kp": 8})

# Subscribe (in module.initialize())
event_bus.subscribe("cosmic.storm.detected", self.handle_storm)
```

## Testing Standards
```python
@pytest.mark.asyncio
async def test_calculation_accuracy():
    """Test against KNOWN data (e.g., verified birth chart)."""
    result = await calculate_natal_chart(
        datetime(1955, 2, 24, 19, 15, tzinfo=ZoneInfo("America/Los_Angeles")),
        lat=37.7749, lon=-122.4194
    )
    assert result.sun.sign == "Pisces"  # Known value
```

## Code Style

- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Docstrings:** Google style for all public APIs

## Questions Before Implementing

1. Is this config in database or hardcoded? (MUST be DB)
2. Are all types annotated?
3. Is there a migration?
4. Are there tests?
5. Is it production-ready or a placeholder?

## Additional Resources

- Module pattern: `skills/module-implementation/SKILL.md`
- Database: `skills/database-patterns/SKILL.md`
- Events: `skills/event-communication/SKILL.md`
- Testing: `skills/testing-standards/SKILL.md`

---

**Build production-quality AI for self-knowledge. No shortcuts. No mocks. No placeholders.**