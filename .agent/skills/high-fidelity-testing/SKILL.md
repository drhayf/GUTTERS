---
name: high-fidelity-testing
description: Standards for real-world service integration testing in GUTTERS. NO mocks, NO workarounds. Ensures tests use real DB, Redis, and actual system logic.
---

# High-Fidelity Testing standards

High-fidelity tests in GUTTERS verify the actual system logic against real hardware (PostgreSQL, Redis) and external APIs. These are "Service Integration Tests" that prove the app works exactly as it would in production.

## Core Mandates

1.  **NO Mocks for Core Logic:** If you are testing a module, use the real class instance.
2.  **Real Infrastructure:** Use the actual PostgreSQL (Supabase) and Redis instances from `.env`.
3.  **No Persistence Mocks:** Verify data actually exists in the database/cache after an operation.
4.  **Full Loop Mastery:** Tests must respect the async lifecycle and singleton resets.
5.  **UTC-Aware Datetimes:** NEVER compare naive and aware datetimes. Use `datetime.now(timezone.utc)`.
6.  **Session Isolation:** Modules MUST accept a `db` session and use it, rather than opening their own via `async_get_db`.

## Infrastructure Patterns

### 1. Database Connectivity (pgbouncer)
When testing against Supabase (pgbouncer), standardPrepared Statements often fail.
- **Port:** Use `5432` (Session Mode) in test engines.
- **Pool:** Use `NullPool` and set `statement_cache_size=0`.
- **Pre-ping:** Set `pool_pre_ping=False` to avoid async loop conflicts.

### 2. Singleton Cleanup (CRITICAL)
Singletons bind to the event loop they are created in. In `pytest-asyncio`, loops are often function-scoped. You MUST reset singletons between tests.

```python
# conftest.py
@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_state():
    yield
    # Dispose engine
    from src.app.core.db.database import async_engine
    await async_engine.dispose()
    
    # Nullify singletons
    from src.app.core.memory.active_memory import ActiveMemory
    ActiveMemory._active_memory = None
    
    from src.app.core.memory.synthesis_orchestrator import SynthesisOrchestrator
    SynthesisOrchestrator._orchestrator = None
```

### 3. Redis Hygiene (CRITICAL)
Tests share the same Redis instance. You MUST flush the cache between tests to prevent data bleeding (state pollution).

```python
# conftest.py
@pytest_asyncio.fixture
async def memory():
    """Get ActiveMemory instance with real Redis connection."""
    mem = get_active_memory()
    await mem.initialize()
    
    # FLUSH REDIS to ensure clean slate
    if mem.redis_client:
        await mem.redis_client.flushdb()
        
    return mem
```

### 4. Mapper Configuration (CRITICAL for Circular Dependencies)
When models have circular string references (e.g., `User` <-> `ChatSession`), SQLAlchemy mappers must be explicitly configured before use in tests to prevent `InvalidRequestError` or `UnboundExecutionError`.

```python
# conftest.py
@pytest_asyncio.fixture(scope="session", autouse=True)
def configure_mappers_session():
    """Ensure all SQLAlchemy mappers are initialized for the session."""
    from sqlalchemy.orm import configure_mappers
    from src.app.models.user import User
    from src.app.models.chat_session import ChatSession
    configure_mappers()
```

### 5. Datetime Standardization
PostgreSQL stores `DateTime(timezone=True)` as UTC.
- **Seeding:** Always use aware objects: `datetime.now(timezone.utc)`.
- **Parsing:** Ensure ISO strings are treated as UTC-aware: `datetime.fromisoformat(ts_str.replace('Z', '+00:00'))`.

## Test Structure

### 1. Deterministic Seeding
Instead of mocking responses, seed the database with the data the real module expects.

```python
# ✅ CORRECT
await db.execute(insert(UserProfile).values(user_id=user_id, data={"astrology": {...}}))
```

### 2. Patching Best Practices
When you *must* patch (only for avoiding external side effects like synthesis triggers or heavy computations you want to isolate), check imports carefully.

- **The Import Trap:** If `module.py` does `from app.core import x`, and you patch `src.app.core.x`, it might NOT work due to aliasing. Patch the **source definition**.
- **Verification:** Use `id()` in debug prints to verify the object usage.

```python
# ✅ CORRECT (Patch the source definition if aliasing is ambiguous)
with patch("app.core.memory.synthesis_orchestrator.get_orchestrator", ...)
```

## Gotchas

- **Serialization Errors:** `ActiveMemory.set_json` expects Pydantic models. `ActiveMemory.set` handles dicts/strings. BEWARE `numpy` types - convert to standard Python types before storing.
- **Unicode Errors:** Avoid checkmarks (✓) or emojis in test print statements on Windows.
- **DetachedInstanceError:** Always read required fields (like `id`) before closing the DB session in a fixture.
- **Initialization Failure:** `RuntimeError: EventBus not initialized`. Fix: `await get_event_bus().initialize()` in `conftest.py` or the test.
- **Circular Imports:** Collection fails with `AttributeError`. Fix: Use deferred imports inside methods.

### 6. Phase 7+ End-to-End (E2E) Verification

The E2E suite (`tests/integration/test_end_to_end.py`) is the ultimate proof of work. It verifies:
1. Registration -> Calculation flow.
2. Synthesis creation & Active Memory storage.
3. Master Chat with full context retrieval.
4. Generative UI component lifecycle.
5. Intelligence layer detection (Observer/Hypothesis).

**Gold Standard**: Every major backend PR must pass the E2E suite with zero warnings.

### 6. Semantic Retrieval Verification

Testing vector search requires verifying relevance without brittle exact-match logic.

- **Similarity Thresholds**: Assert that results meet a minimum baseline (e.g., `> 0.3`).
- **Data Presence**: Verify that seeded data is actually indexed before searching (check DB count).
- **Hybrid Grouping**: If using hybrid search, verify all expected categories have at least one result.

```python
# ✅ CORRECT - Testing Vector Search
results = await engine.search(user_id, query_vector, db)

# 1. Verify index isn't empty
count = await db.scalar(select(func.count()).select_from(Embedding))
assert count > 0

# 2. Verify top result relevance
assert results[0]['similarity'] > 0.3
assert "expected keyword" in results[0]['content'].lower()

# 3. Verify hybrid coverage
grouped = await engine.hybrid_search(user_id, query_vector, db)
assert len(grouped['journal_entries']) > 0
```

## Verification Checklist

- [ ] Does the test use the real database (no `mock_db`)?
- [ ] Are singletons being reset in `conftest.py`?
- [ ] Is Redis flushed (`flushdb`) in the memory fixture?
- [ ] Are external API calls actually firing (or using the `VCR`/`aiohttp` patch)?
