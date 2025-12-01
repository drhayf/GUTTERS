# True Fractal Migration Protocol

## Executive Summary

This document provides a **step-by-step execution protocol** for migrating the existing codebase to the True Fractal Pattern. It is designed to be followed by an AI coding agent with maximum scrutiny and fidelity.

**Key Principle**: Migrate ONE vertical slice at a time, verify it works, then proceed.

---

## Phase 0: Pre-Migration Verification

### Step 0.1: Verify Current System Works

Before ANY changes, run the verification script to establish a baseline:

```bash
cd apps/api
python -c "
from src.digital_twin.domains import GenesisDomain, HealthDomain, NutritionDomain, JournalingDomain, FinanceDomain
from src.digital_twin import get_domain_registry
from src.core.swarm_bus import SwarmBus, get_bus
from src.core.orchestrator import SovereignOrchestrator
print('All imports successful - baseline established')
"
```

### Step 0.2: Create Migration Tracking File

Create a tracking file to maintain context across sessions:

```bash
# Create: apps/api/MIGRATION_STATUS.md
```

Contents:
```markdown
# Migration Status Tracker

## Current Phase: 0 - Pre-Migration
## Current Slice: None
## Last Verified: [timestamp]

### Completed Slices
- [ ] traits/categories/ (Phase 1)
- [ ] traits/frameworks/ (Phase 1)
- [ ] traits/schema/ (Phase 1)
- [ ] domains/base/ (Phase 2)
- [ ] domains/registry/ (Phase 2)
- [ ] domains/genesis/ (Phase 3)
- [ ] domains/health/ (Phase 3)
- [ ] domains/nutrition/ (Phase 3)
- [ ] domains/journaling/ (Phase 3)
- [ ] domains/finance/ (Phase 3)
- [ ] awareness/query/ (Phase 4)
- [ ] awareness/events/ (Phase 4)
- [ ] awareness/state/ (Phase 4)
- [ ] integration/probes/ (Phase 5)
- [ ] integration/scenarios/ (Phase 5)
- [ ] swarm/bus/ (Phase 6)
- [ ] swarm/packets/ (Phase 6)
- [ ] agents/sovereign/ (Phase 7)
- [ ] agents/genesis/ (Phase 7)

### Verification Log
[Append each verification result here]
```

---

## Phase 1: Foundation Layer (Traits)

The traits layer has ZERO dependencies on other layers - it's the purest foundation.

### Slice 1.1: TraitCategory Fractal

**Read Current**: `apps/api/src/digital_twin/traits/categories.py`

**Target Structure**:
```
traits/
└── categories/
    ├── __init__.py           # Exports TraitCategory enum + all category modules
    ├── registry.py           # CategoryRegistry for dynamic discovery
    ├── personality/
    │   ├── __init__.py       # Exports PERSONALITY
    │   └── definition.py     # PERSONALITY = "personality"
    ├── archetype/
    │   ├── __init__.py
    │   └── definition.py
    ├── cognition/
    │   ├── __init__.py
    │   └── definition.py
    ├── emotion/
    │   ├── __init__.py
    │   └── definition.py
    ├── shadow/
    │   ├── __init__.py
    │   └── definition.py
    ├── behavior/
    │   ├── __init__.py
    │   └── definition.py
    ├── habit/
    │   ├── __init__.py
    │   └── definition.py
    ├── tendency/
    │   ├── __init__.py
    │   └── definition.py
    ├── energy/
    │   ├── __init__.py
    │   └── definition.py
    ├── rhythm/
    │   ├── __init__.py
    │   └── definition.py
    ├── preference/
    │   ├── __init__.py
    │   └── definition.py
    ├── style/
    │   ├── __init__.py
    │   └── definition.py
    ├── goal/
    │   ├── __init__.py
    │   └── definition.py
    ├── value/
    │   ├── __init__.py
    │   └── definition.py
    ├── wound/
    │   ├── __init__.py
    │   └── definition.py
    ├── gift/
    │   ├── __init__.py
    │   └── definition.py
    ├── health/
    │   ├── __init__.py
    │   └── definition.py
    ├── somatic/
    │   ├── __init__.py
    │   └── definition.py
    ├── demographic/
    │   ├── __init__.py
    │   └── definition.py
    ├── context/
    │   ├── __init__.py
    │   └── definition.py
    ├── calculated/
    │   ├── __init__.py
    │   └── definition.py
    ├── detected/
    │   ├── __init__.py
    │   └── definition.py
    └── stated/
        ├── __init__.py
        └── definition.py
```

**Migration Steps**:

1. **Create the folder structure** (empty folders with `__init__.py`):
   ```python
   # Agent command: Create all folders first
   # DO NOT write any logic yet - just create empty __init__.py files
   ```

2. **Create one category as template** (personality):
   ```python
   # traits/categories/personality/definition.py
   """Personality trait category definition."""
   
   PERSONALITY = "personality"
   DISPLAY_NAME = "Personality"
   DESCRIPTION = "Core personality traits and characteristics"
   ICON = "🎭"
   ```
   
   ```python
   # traits/categories/personality/__init__.py
   """Personality category module."""
   from .definition import PERSONALITY, DISPLAY_NAME, DESCRIPTION, ICON
   
   __all__ = ["PERSONALITY", "DISPLAY_NAME", "DESCRIPTION", "ICON"]
   ```

3. **Create remaining categories** following the same pattern.

4. **Create the registry**:
   ```python
   # traits/categories/registry.py
   """Category registry for dynamic discovery."""
   from typing import Dict, List, Optional
   from pathlib import Path
   import importlib
   
   class CategoryRegistry:
       """Auto-discovers and registers all trait categories."""
       
       _instance: Optional["CategoryRegistry"] = None
       _categories: Dict[str, dict] = {}
       
       def __new__(cls) -> "CategoryRegistry":
           if cls._instance is None:
               cls._instance = super().__new__(cls)
               cls._instance._discover_categories()
           return cls._instance
       
       def _discover_categories(self) -> None:
           """Auto-discover all category folders."""
           categories_dir = Path(__file__).parent
           for folder in categories_dir.iterdir():
               if folder.is_dir() and not folder.name.startswith("_"):
                   try:
                       module = importlib.import_module(
                           f".{folder.name}", 
                           package="src.digital_twin.traits.categories"
                       )
                       if hasattr(module, folder.name.upper()):
                           self._categories[folder.name] = {
                               "value": getattr(module, folder.name.upper()),
                               "display_name": getattr(module, "DISPLAY_NAME", folder.name.title()),
                               "description": getattr(module, "DESCRIPTION", ""),
                               "icon": getattr(module, "ICON", ""),
                           }
                   except ImportError:
                       pass
       
       def get(self, category_id: str) -> Optional[dict]:
           """Get category by ID."""
           return self._categories.get(category_id)
       
       def list_all(self) -> List[str]:
           """List all category IDs."""
           return list(self._categories.keys())
       
       def get_enum_value(self, category_id: str) -> Optional[str]:
           """Get the string value for enum compatibility."""
           cat = self._categories.get(category_id)
           return cat["value"] if cat else None
   
   
   def get_category_registry() -> CategoryRegistry:
       """Get the singleton category registry."""
       return CategoryRegistry()
   ```

5. **Create the main categories __init__.py**:
   ```python
   # traits/categories/__init__.py
   """
   Trait Categories - Fractal Module
   
   Each category is independently addressable and extensible.
   Add new categories by creating a new folder with definition.py.
   """
   from enum import Enum
   from .registry import CategoryRegistry, get_category_registry
   
   # Import all category values for backward compatibility
   from .personality import PERSONALITY
   from .archetype import ARCHETYPE
   from .cognition import COGNITION
   from .emotion import EMOTION
   from .shadow import SHADOW
   from .behavior import BEHAVIOR
   from .habit import HABIT
   from .tendency import TENDENCY
   from .energy import ENERGY
   from .rhythm import RHYTHM
   from .preference import PREFERENCE
   from .style import STYLE
   from .goal import GOAL
   from .value import VALUE
   from .wound import WOUND
   from .gift import GIFT
   from .health import HEALTH
   from .somatic import SOMATIC
   from .demographic import DEMOGRAPHIC
   from .context import CONTEXT
   from .calculated import CALCULATED
   from .detected import DETECTED
   from .stated import STATED
   
   
   # Backward-compatible enum (uses registry under the hood)
   class TraitCategory(str, Enum):
       """Trait categories - backward compatible enum."""
       PERSONALITY = PERSONALITY
       ARCHETYPE = ARCHETYPE
       COGNITION = COGNITION
       EMOTION = EMOTION
       SHADOW = SHADOW
       BEHAVIOR = BEHAVIOR
       HABIT = HABIT
       TENDENCY = TENDENCY
       ENERGY = ENERGY
       RHYTHM = RHYTHM
       PREFERENCE = PREFERENCE
       STYLE = STYLE
       GOAL = GOAL
       VALUE = VALUE
       WOUND = WOUND
       GIFT = GIFT
       HEALTH = HEALTH
       SOMATIC = SOMATIC
       DEMOGRAPHIC = DEMOGRAPHIC
       CONTEXT = CONTEXT
       CALCULATED = CALCULATED
       DETECTED = DETECTED
       STATED = STATED
   
   
   __all__ = [
       "TraitCategory",
       "CategoryRegistry",
       "get_category_registry",
       # Individual categories
       "PERSONALITY", "ARCHETYPE", "COGNITION", "EMOTION", "SHADOW",
       "BEHAVIOR", "HABIT", "TENDENCY", "ENERGY", "RHYTHM",
       "PREFERENCE", "STYLE", "GOAL", "VALUE", "WOUND", "GIFT",
       "HEALTH", "SOMATIC", "DEMOGRAPHIC", "CONTEXT",
       "CALCULATED", "DETECTED", "STATED",
   ]
   ```

6. **VERIFY THIS SLICE**:
   ```bash
   cd apps/api
   python -c "
   from src.digital_twin.traits.categories import TraitCategory, get_category_registry
   print(f'TraitCategory.PERSONALITY = {TraitCategory.PERSONALITY.value}')
   registry = get_category_registry()
   print(f'Registry categories: {registry.list_all()}')
   print('Slice 1.1 VERIFIED')
   "
   ```

7. **Update MIGRATION_STATUS.md**:
   - Mark `traits/categories/` as complete
   - Log verification result

### Slice 1.2: TraitFramework Fractal

**Same pattern as categories**, but for frameworks:
- human_design/, jungian/, gene_keys/, mbti/, enneagram/
- astrology/, vedic/, numerology/
- somatic/, somatic_awareness/, ayurveda/
- big_five/, attachment/
- health_metrics/, biometrics/
- behavioral_patterns/, core_patterns/
- sovereign/, general/

### Slice 1.3: TraitSchema Fractal

Migrate the TraitSchema dataclass to its own folder structure.

---

## Phase 2: Domain Foundation

### Slice 2.1: BaseDomain Fractal

Migrate `domains/base.py` to `domains/base/` folder.

### Slice 2.2: DomainRegistry Fractal

Migrate `domains/registry.py` to `domains/registry/` folder.

---

## Phase 3: Domain Migration (One at a Time)

### For Each Domain (genesis, health, nutrition, journaling, finance):

1. **Read the current domain implementation**
2. **Create the fractal folder structure**
3. **Migrate each concern to its own sub-folder**
4. **Update imports in the domain's __init__.py**
5. **Verify the domain works in isolation**
6. **Verify cross-domain communication still works**
7. **Update MIGRATION_STATUS.md**

---

## Phase 4: Awareness Layer (New)

This is a NEW layer - no migration, just creation.

### Slice 4.1: Query System

Create `awareness/query/` with:
- parsers/ (for query language parsing)
- executors/ (for running queries)
- cache/ (for query result caching)

### Slice 4.2: Event System

Create `awareness/events/` with:
- bus/ (event bus implementation)
- handlers/ (event handlers)
- types/ (event type definitions)

### Slice 4.3: State System

Create `awareness/state/` with:
- store/ (state storage)
- selectors/ (state selectors)
- reducers/ (state mutations)

---

## Phase 5: Integration Testing Layer (New)

Create `integration/` following the COPILOT-UPGRADE-ADDENDUM.md spec.

---

## Phase 6: SwarmBus Migration

Migrate the existing SwarmBus to fractal structure.

---

## Phase 7: Agent Migration

Migrate Sovereign Agent and Genesis Agent to fractal structure.

---

## Execution Rules for AI Agent

### Rule 1: One Slice at a Time
NEVER work on multiple slices simultaneously. Complete one, verify, then proceed.

### Rule 2: Read Before Write
Before modifying ANY file, read its current contents completely.

### Rule 3: Verify After Each Slice
After completing each slice, run the verification script.

### Rule 4: Update Tracking
After each slice, update MIGRATION_STATUS.md with:
- Completion status
- Verification result
- Any issues encountered

### Rule 5: Preserve Backward Compatibility
Every migrated module MUST maintain the same public API. Old imports should still work via the `__init__.py` re-exports.

### Rule 6: Create Empty Structure First
When migrating a slice:
1. Create all folders with empty `__init__.py` first
2. Then add the actual code file by file
3. Then update the `__init__.py` exports
4. Then verify

### Rule 7: No Deletion Until Verified
Do NOT delete old files until the new structure is verified working.

---

## Verification Commands

### After Each Slice
```bash
cd apps/api
python -c "
# Specific verification for the slice
# This should be customized for each slice
"
```

### Full System Verification
```bash
cd apps/api
python -c "
print('=' * 60)
print('  FULL SYSTEM VERIFICATION')
print('=' * 60)

# 1. All domains
from src.digital_twin.domains import (
    GenesisDomain, HealthDomain, NutritionDomain, 
    JournalingDomain, FinanceDomain
)
print('✓ All domains import')

# 2. Registry
from src.digital_twin import get_domain_registry
registry = get_domain_registry()()
print(f'✓ Registry: {len(registry._domains)} domains')

# 3. SwarmBus
from src.core.swarm_bus import SwarmBus, get_bus
print('✓ SwarmBus imports')

# 4. Orchestrator
from src.core.orchestrator import SovereignOrchestrator
print('✓ Orchestrator imports')

# 5. Sovereign Agent
from src.agents.sovereign import SovereignAgent
print('✓ Sovereign Agent imports')

# 6. Genesis Agent
from src.agents.genesis import GenesisCore
print('✓ Genesis Agent imports')

print('=' * 60)
print('  ALL SYSTEMS VERIFIED')
print('=' * 60)
"
```

---

## Context Preservation Strategy

### For Multi-Session Migrations

1. **Start each session by reading**:
   - MIGRATION_STATUS.md (to know where you left off)
   - The current slice being worked on
   - The previous slice (for context)

2. **At the end of each session**:
   - Update MIGRATION_STATUS.md
   - Note any incomplete work
   - Document next steps

3. **Session Prompt Template**:
   ```
   I am continuing the True Fractal Migration of Project Sovereign.
   
   Please read:
   1. .github/COPILOT-UPGRADE.md (architecture spec)
   2. .github/COPILOT-UPGRADE-ADDENDUM.md (additional layers)
   3. .github/COPILOT-MIGRATION-PROTOCOL.md (this file)
   4. apps/api/MIGRATION_STATUS.md (current progress)
   
   Then continue from where we left off, following the protocol exactly.
   Work on ONE SLICE at a time. Verify before proceeding.
   ```

---

## Rollback Strategy

If something breaks:

1. **Check git status** - what files were changed?
2. **Identify the breaking change** - which slice caused it?
3. **Revert that slice** - `git checkout -- <files>`
4. **Re-attempt with more care**

Always commit after each verified slice:
```bash
git add -A
git commit -m "Migrate [slice-name] to True Fractal Pattern - VERIFIED"
```

---

## Estimated Timeline

| Phase | Slices | Estimated Time |
|-------|--------|----------------|
| 0 - Pre-Migration | 2 | 15 minutes |
| 1 - Traits | 3 | 2-3 hours |
| 2 - Domain Foundation | 2 | 1 hour |
| 3 - Domain Migration | 5 | 4-5 hours |
| 4 - Awareness Layer | 3 | 2-3 hours |
| 5 - Integration Testing | 3 | 2-3 hours |
| 6 - SwarmBus | 2 | 1-2 hours |
| 7 - Agents | 2 | 2-3 hours |
| **TOTAL** | **22 slices** | **15-20 hours** |

This should be done across multiple sessions, not all at once.

---

## Success Criteria

The migration is complete when:

1. ✓ All slices in MIGRATION_STATUS.md are checked
2. ✓ Full system verification passes
3. ✓ All tests pass (run existing test suite)
4. ✓ Frontend can communicate with backend normally
5. ✓ Genesis profiling flow works end-to-end
6. ✓ New folders can be added without touching existing code

---

## The Golden Rule

**If you're ever unsure, STOP and READ more context.**

Don't guess. Don't assume. Read the actual files.

The goal is ZERO hallucination, ZERO breaking changes, and COMPLETE fidelity to the True Fractal Pattern.
