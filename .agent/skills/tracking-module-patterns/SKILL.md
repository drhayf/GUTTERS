---
name: tracking-module-patterns
description: Standard pattern for GUTTERS tracking modules (Solar, Lunar, Transit, etc.). Focuses on history storage and data extraction for the Observer module.
---

# Tracking Module Patterns

Tracking modules ingest real-time cosmic data and store it in the user's history for downstream intelligence analysis (correlation detection).

## Architecture

Tracking modules inherit from `BaseTrackingModule` (if implemented) or use the following pattern:

1. **Inbound Data**: Receive data from external APIs or system events.
2. **State Update**: Update the user's current profile with the latest snapshot.
3. **History Persistence**: Append the entry to `UserProfile.data['tracking_history']` for pattern detection.

## Core Implementation Pattern

### 1. Base Logic (Tracking Module)
```python
from src.app.modules.tracking.base import BaseTrackingModule

class SolarTracker(BaseTrackingModule):
    async def update(self, user_id: int, db: AsyncSession, data: Dict):
        # 1. Update current state
        await self._update_profile_state(user_id, db, data)
        
        # 2. Store in history (CRITICAL for Observer)
        await self._store_in_history(user_id, db, "solar_tracking", data)
```

### 2. History Storage Implementation
```python
async def _store_in_history(self, user_id, db, tracking_key, data):
    # Load profile
    profile = await get_profile(user_id, db)
    
    if "tracking_history" not in profile.data:
        profile.data["tracking_history"] = {}
    
    if tracking_key not in profile.data["tracking_history"]:
        profile.data["tracking_history"][tracking_key] = []
        
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    
    # Append and prune (keep last 180 days/entries)
    profile.data["tracking_history"][tracking_key].append(entry)
    profile.data["tracking_history"][tracking_key] = \
        profile.data["tracking_history"][tracking_key][-180:]
        
    flag_modified(profile, "data")
    await db.commit()
```

## Integration with Observer

Observer modules expect historical data to be in specific keys:
- `solar_tracking`
- `lunar_tracking`
- `transit_tracking`

## Gotchas

- **Naive Datetimes**: ALWAYS use `dt.datetime.now(dt.timezone.utc).isoformat()` for entry timestamps. `utcnow()` is banned.
- **Session Isolation**: Pass the `db` session through to all internal helpers.
- **JSONB Flag**: Remember `flag_modified(profile, "data")` after updating deep JSON fields.

## Checklist

- [ ] Extends profile history in `UserProfile.data['tracking_history']`
- [ ] Uses UTC-aware timestamps
- [ ] Passing existing `db` session to all methods
- [ ] Prunes history to avoid JSONB bloat
- [ ] Matches keys expected by `Observer`
