# The Cosmic Nervous System (Notification Infrastructure)

> **Status**: Production Ready (Phase 21.5)
> **Architecture**: Event-Driven, Declarative, High-Fidelity
> **Key Feature**: Infinite Extensibility via `EVENT_MAP`

The **GUTTERS Nervous System** is a sophisticated, push-based notification infrastructure designed to connect the user ("The Pilot") with the system's internal states, cosmic events, and agent directives. It is built on the principle of **Declarative Observability**—if an event is mapped, the system knows how to route it without custom code.

---

## 1. Architectural Overview

The system follows a linear, high-fidelity data flow:

1.  **Event Origin**: Any module (Solar, Quest, Evolution) emits a `Packet` to the `EventBus`.
2.  **The Spine (Listeners)**: The `NotificationRouter` listens to *all* events defined in the `EVENT_MAP`.
3.  **The Brain (Router & Map)**:
    *   **Lookup**: The router finds the event config in `map.py`.
    *   **Filter**: Appeals to global logic (e.g., "Is Kp Index > 5?").
    *   **Preference Check**: Queries `UserProfile` to see if the user has opted out of this specific channel.
4.  **The Synapse (Service & VAPID)**: If approved, it signs a secure payload using VAPID keys and pushes it to the browser's Service Worker.
5.  **The Sensation (Frontend)**: The browser displays the system notification.

### Components

| Component | Path | Responsibility |
| :--- | :--- | :--- |
| **Event Map** | `src/app/modules/infrastructure/push/map.py` | **Single Source of Truth**. Defines events, templates, and preference keys. |
| **Router** | `src/app/modules/infrastructure/push/router.py` | Generic dispatcher. Handles filtering, preferences, and formatting. |
| **Listeners** | `src/app/modules/infrastructure/push/listeners.py` | Dynamically subscribes to EventBus based on the Map. |
| **Control Panel** | `frontend/src/features/settings/NotificationSettingsPage.tsx` | UI for managing subscription keys and granular preferences. |

---

## 2. Extensibility Guide: How to Add a Notification

To add a new notification type (e.g., "Nutrition Alert"), you simply update the **Map**. No other backend code changes are required.

### Step 1: Add to `EVENT_MAP`
Open `src/app/modules/infrastructure/push/map.py` and add an entry:

```python
    "nutrition.alert": NotificationConfig(
        preference_key="wellness",  # New or existing category
        title_template="Hydration Check",
        body_template="You have consumed {water_ml}ml today.",
        deep_link="/wellness"
    ),
```

### Step 2: (Optional) Frontend Toggle
If you used a *new* `preference_key` (e.g., `wellness`), update `NotificationSettingsPage.tsx` to include a toggle for it:

```typescript
{ id: 'wellness', label: 'Body Health', icon: Heart, ... }
```

**That's it.** The `listeners.py` will automatically subscribe to `"nutrition.alert"` on restart, and `router.py` will handle routing logic.

---

## 3. Granular Channels

The system currently supports 5 high-fidelity channels:

1.  **Cosmic & Lunar** (`cosmic`): High-intensity solar storms (Kp > 5) and significant Moon phases.
2.  **Mission Control** (`quests`): New agent directives and completion rewards.
3.  **Evolution** (`evolution`): Level-ups and Rank progressions.
4.  **System Intelligence** (`intelligence`):
    *   **Hypothesis**: "My understanding of YOU has changed."
    *   **Synthesis**: "I have generated a new psychological profile."
5.  **Journal Archive** (`journal`): Confirmation of secure entry storage.

---

## 4. Security & Re-Sync Protocol

The system uses **VAPID (Voluntary Application Server Identification)** to secure the link between the backend and browser.

*   **Key Rotation**: If the server's Private Key changes (e.g., for security rotation), all existing browser subscriptions become invalid.
*   **The "Cosmic Link" Switch**: The Master Switch in the Frontend manages this complexity. Toggling it OFF and ON:
    1.  Unsubscribes the stale endpoint.
    2.  Fetches the *new* Public Key from API.
    3.  Re-subscribes with the browser.
    4.  Syncs the new endpoint to the Database.

---

## 5. Verification Standards

All changes to this system must pass the **High-Fidelity Integration Suite**:
`tests/integration/test_notification_fidelity.py`

This suite enforces:
*   **Real Persistence**: Preferences must be saved to PostgreSQL.
*   **Real Logic**: The generic router must correctly filter events based on the dynamic map.
*   **No Mocks (mostly)**: Only the external `send_to_user` call is patched; all internal routing logic is executed for real.
