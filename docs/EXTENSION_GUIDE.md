# The Architect's Handbook: Extending GUTTERS
> **Technical Protocol Level: Senior Engineer**
> **Scope: Notification System, Modules, and Journaling**

This document outlines the strict protocols for extending the GUTTERS system. All extensions must adhere to the "Golden Thread" architecture: **Event -> Insight -> Notification**.

---

## 1. The "Golden Thread" Protocol (Adding Notifications)
To add a new notification (e.g., "Nutrition Alert"), you must modify the system in four specific locations. Failure to complete the loop will result in a "Ghost Signal" (Event emitted but never felt).

### Step 1: The Protocol (Event Definition)
Define the connection point. Add a new constant to `src/app/protocol/events.py`.
```python
# src/app/protocol/events.py

NUTRITION_LOGGED = "nutrition.logged"
"""User logged a meal. Payload: {calories: int, macros: dict}"""
```

### Step 2: The Emitter (Signal Injection)
Inject the signal into the relevant Manager or Tracker.
```python
# src/app/modules/features/nutrition/manager.py

await self.bus.publish(
    events.NUTRITION_LOGGED,
    {"user_id": user_id, "calories": 500, "macros": {...}},
    user_id=str(user_id)
)
```

### Step 3: The Map (Translation Layer)
**CRITICAL**: You must map the event to a human-readable template in `src/app/modules/infrastructure/push/map.py`.
*   `preference_key`: Must match a key the user can toggle (see Step 4).
*   `deep_link`: Where the user goes when they tap.

```python
# src/app/modules/infrastructure/push/map.py

EVENT_MAP = {
    # ... existing ...
    "nutrition.logged": NotificationConfig(
        preference_key="nutrition",  # New key
        title_template="Meal Tracked",
        body_template="{calories} kcal logged.",
        deep_link="/nutrition",
    ),
}
```

### Step 4: The Switch (User Control)
If you introduced a NEW `preference_key` (like "nutrition") in Step 3, you must add a toggle to the Frontend.
*   **Location**: `frontend/src/features/settings/NotificationSettingsPage.tsx`
*   **Action**: Add to the `categories` array.

```tsx
// NotificationSettingsPage.tsx
const categories = [
    // ...
    { 
        id: 'nutrition', // MUST MATCH preference_key
        label: 'Nutrition', 
        icon: Apple, 
        desc: 'Dietary tracking updates', 
        color: 'text-green-500', 
        bg: 'bg-green-500/10' 
    },
]
```

---

## 2. Adding New Intelligence Modules
To add a module that contributes to the User's Profile (e.g., "SleepTracker"), use the Registry Pattern.

### Registration
Decorate your main calculation class. This ensures `Genesis` and `Synthesis` can find your data.
```python
from src.app.core.registry.module_registry import CalculationModuleRegistry

@CalculationModuleRegistry.register(
    name="sleep_tracker",
    layer="body",
    dependencies=["cosmic"]
)
class SleepTracker:
    # ... implementation ...
```

### Awarding XP (Gamification)
To reward the user for using your module, emit a `PROGRESSION_EXPERIENCE_GAIN` packet.
```python
from src.app.protocol import events
from src.app.protocol.packet import ProgressionPacket

packet = ProgressionPacket(
    user_id=user.id,
    amount=50,
    reason="Logged 8 hours of sleep",
    category="HEALTH"
)
await self.bus.publish(events.PROGRESSION_EXPERIENCE_GAIN, packet)
```

---

## 3. The System Journal
To log events into the user's "Living Archive" (Journal) with a high-fidelity "System Log" appearance:

### Usage
Use the `SystemJournalist` singleton. It handles LLM generation and Database insertion.
**Note**: It listens to `PROGRESSION_EXPERIENCE_GAIN` automatically. For custom events, you may need to manually invoke it or add a listener in `system_journal.py`.

```python
# src/app/modules/features/journal/system_journal.py

# To add a NEW listener:
async def initialize(self):
    await self.bus.subscribe(events.NUTRITION_LOGGED, self.handle_nutrition_log)

async def handle_nutrition_log(self, payload: dict):
    # Retrieve context, generate LLM log, save to DB.
    # See handle_experience_gain() for the reference implementation.
```

### Frontend Rendering
The frontend (`JournalEntryList.tsx`) automatically detects `source="SYSTEM"` and applies the "Terminal/Tech" visual theme. No frontend changes are needed unless you want a special icon for your specific event type.
