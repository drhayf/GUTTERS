---
name: full-stack-integration-enforcement
description: The "Supervisor" skill. Mandates that EVERY new feature implementation proactively integrates with Genesis, StateTracker, EventBus, and Observability. Enforces "Maximum Scrutiny" on testing fidelity.
---

# Full-Stack Integration Enforcement

**"The Rule of No Surprises"**: The agent must ALREADY know to integrate with all subsystems before writing a single line of business logic. "I'll do it later" is forbidden.

## 1. The Blast Radius Calculation (Pre-Code)

Before writing any implementation code (even a prototype), you MUST map the feature against the Core Five systems.

| System | Integration Required If... | Action Required |
|--------|----------------------------|-----------------|
| **Genesis** | Data is probabilistic, incomplete, or requires refinement? | Create `UncertaintyExtractor` + Registry |
| **StateTracker** | Feature affects profile completeness or user progression? | Update `PROFILE_DOMAINS` in `tracker.py` |
| **EventBus** | Other modules might *eventually* care about this? | Define `Events.CONST` and publish payload |
| **Chat System** | Feature involves user dialogue or cognitive status reports? | Connect to `SessionManager` (Master/Branch) |
| **Observability** | Is this a user-facing or LLM-driven operation? | Add `ActivityLogger` (with Thinking Trace) |

**Constraint:** If you cannot answer "No" to a column, you MUST implement the integration immediately. High-fidelity systems require proactive wiring.

## 2. High Fidelity Mandate (Testing)

**"If it's not tested against Production Infra, it doesn't exist."**

### The Mock Audit
You strictly forbidden from mocking:
- **Core Logic:** Classes under test must be real instances.
- **Persistence:** `ActiveMemory` (Redis) and `SQLAlchemy` (Postgres) must be real.
- **Orchestrators:** Synthesis/Genesis orchestrators must be real.
- **Async Systems:** `EventBus` and `ActiveMemory` MUST be explicitly initialized in tests (`await instance.initialize()`) to ensure stable connection pools.

**Permitted Mocks:** only 3rd party HTTP APIs (e.g., `aiohttp.ClientSession`).

### The Protocol
1. **Reset State:** Use fixtures to flush Redis (`await mem.redis_client.flushdb()`) and drop/create DB tables.
2. **Patch Precision:** verify patch targets using `id()` if tests fail. Do NOT patch `src.app...` if the code imports `app...`. Patch the *definition source*.
3. **Serialization Check:** Ensure all data sent to `ActiveMemory` uses native Python types (no NumPy `float64`), or use a Pydantic model with `model_dump(mode='json')`.

## 3. Implementation Workflow

1. **Map Integrity:** Write the "Integration Matrix" in your plan.
2. **Scaffold Integration:** Create the empty `UncertaintyExtractor` and `StateTracker` entries *first*.
3. **Core Logic:** Implement the feature.
4. **Data Boundary:** Ensure all inputs/outputs are Pydantic models. Convert external library types (NumPy, Pandas) immediately at the boundary.
5. **Verify:** Run HF tests. assert persistence in Redis/DB.

## 4. Self-Correction Prompts

If you find yourself writing:
- `... # TODO: Add genesis integration` -> **STOP.** Do it now.
- `@patch('src.app.core.db')` -> **STOP.** Use real DB fixture.
- `return {"data": np.float64(1.0)}` -> **STOP.** Convert to `float`.
