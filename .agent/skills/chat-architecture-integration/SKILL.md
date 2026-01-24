---
name: chat-architecture-integration
description: Integration patterns for the Master/Branch Chat architecture. Use when adding features that require user dialogue, workspace-specific context, or automated reporting.
---

# Chat Architecture Integration

GUTTERS uses a tiered chat architecture to separate persistent cognitive presence from ephemeral workspace tasks. This is the foundation of "Observable AI".

## 1. Master Chat vs. Branches

Every user interaction or cognitive report MUST follow this separation:

- **Master Chat (Multi-Threaded)**:
    - **Purpose**: Persistent cognitive presence, system alerts, status updates, and Genesis refinement probes.
    - **Lifecycle**: Users can have multiple Master threads (e.g., "Work", "Health"). Always has full module access.
    - **Contribute to Memory**: Always `True`.
- **Branch Chats (Ephemeral)**:
    - **Purpose**: Topic-specific workspaces (Journal entry, Nutrition deep-dive, Finance audit).
    - **Lifecycle**: Created for a specific short-term task.
    - **Contribute to Memory**: Optional (Toggleable).

## 2. Using the SessionManager

ALWAYS use the `SessionManager` service to interact with chats. Never query `ChatSession` models directly in business logic.

```python
from src.app.modules.features.chat.session_manager import SessionManager

manager = SessionManager()

# 1. Get Default or Specific Master Session
# For generic access:
master = await manager.get_default_master_conversation(user_id=user_id, db=db)

# For specific conversation topic:
work_chat = await manager.create_master_conversation(
    user_id=user_id, 
    conversation_name="Work Planning", 
    db=db
)

# 2. Add message to session with high-fidelity metadata
message = await manager.add_message(
    session_id=master.id,
    role="assistant",
    content="The solar storm is peaking. Confidence in intuition +15%.",
    meta={
        "activity_type": "cosmic_alert",
        "model_used": "anthropic/claude-3.5-sonnet",
        "thinking_steps": ["analyze_solar_flux", "cross_reference_natal_moon"]
    },
    db=db
)

# 3. Create a workspace branch
branch = await manager.create_branch_session(
    user_id=user_id,
    session_type="dream_log",
    name="Dream Interpretation: Red Forest",
    contribute_to_memory=True,
    db=db
)
```

## 3. Metadata & Observability (Phase 7b)

The `ChatMessage.meta` JSONB field is critical for Phase 7b "Thinking Visualization".

**Recommended payload for complex operations:**
```json
{
  "thinking_steps": ["query_astrology", "cross_reference_hd", "synthesize_advice"],
  "tools_used": ["swiss_ephemeris", "active_memory"],
  "confidence_score": 0.85,
  "prompt_id": "natal_advice_v2"
}
```

## 4. Integration with Intelligence Layer

Intelligence modules (Synthesis, Oracle) should use chat history as a primary data source when `contribute_to_memory` is `True`.

- **Synthesis**: Ingests sessions marked for memory.
- **Oracle**: Searched the Vector Index of previous messages to answer user questions about their own history.

## 5. Checklist

- [ ] Does this belong in **Master** (ambient) or a **Branch** (focused)?
- [ ] Is `contribute_to_memory` set appropriately?
- [ ] Are thinking steps logged in `meta`?
- [ ] Is the `SessionManager` being used (not direct SQL)?
- [ ] Are messages timestamped with UTC-aware datetimes (handled by manager)?
