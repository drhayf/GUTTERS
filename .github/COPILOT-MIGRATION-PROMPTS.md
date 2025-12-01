# AI Agent Session Prompts for True Fractal Migration

This document contains copy-paste ready prompts for guiding an AI coding agent through the True Fractal Migration of Project Sovereign.

---

## Initial Session Prompt (Start the Migration)

```
You are about to begin a meticulous, high-fidelity migration of the Project Sovereign codebase to a True Fractal Pattern architecture. This migration demands PEAK ENGINEERING STANDARDS.

## CRITICAL CONTEXT FILES - READ THESE FIRST

Before doing ANYTHING, read these files completely and thoroughly:

1. `.github/COPILOT-UPGRADE.md` - The complete architecture specification
2. `.github/COPILOT-UPGRADE-ADDENDUM.md` - Additional layers (Awareness, Integration Testing)
3. `.github/COPILOT-MIGRATION-PROTOCOL.md` - Step-by-step execution protocol
4. `.github/copilot-instructions.md` - Project context and current system

## YOUR MISSION

Execute the True Fractal Migration following the COPILOT-MIGRATION-PROTOCOL.md EXACTLY.

## EXECUTION RULES

1. **ONE SLICE AT A TIME** - Never work on multiple slices simultaneously
2. **READ BEFORE WRITE** - Read every file completely before modifying
3. **VERIFY AFTER EACH SLICE** - Run verification commands after each slice
4. **UPDATE TRACKING** - Update MIGRATION_STATUS.md after each slice
5. **NO GUESSING** - If unsure, read more context. Never assume.
6. **PRESERVE COMPATIBILITY** - Old imports must still work via re-exports

## FIRST TASK

1. Read all 4 context files listed above
2. Execute Phase 0 (Pre-Migration Verification)
3. Create the MIGRATION_STATUS.md tracking file
4. Begin Phase 1, Slice 1.1 (TraitCategory Fractal)
5. Verify Slice 1.1 works
6. Update MIGRATION_STATUS.md
7. Report progress and await next instruction

## PACE

Work slowly and methodically. Quality over speed. We are building a system that will last.

Begin by reading the context files.
```

---

## Continuation Session Prompt (Resume Migration)

```
You are continuing the True Fractal Migration of Project Sovereign.

## RESTORE CONTEXT - READ THESE FILES

1. `.github/COPILOT-MIGRATION-PROTOCOL.md` - The execution protocol
2. `apps/api/MIGRATION_STATUS.md` - Current progress and last verified state
3. Read the LAST COMPLETED slice to understand the pattern
4. Read the NEXT slice's current implementation

## YOUR MISSION

Continue from exactly where we left off. Check MIGRATION_STATUS.md to see:
- Which slices are complete
- Which slice is currently in progress
- Any notes from the previous session

## EXECUTION RULES

1. **ONE SLICE AT A TIME** - Complete the current slice before moving on
2. **VERIFY BEFORE PROCEEDING** - Run verification after each slice
3. **UPDATE TRACKING** - Log everything in MIGRATION_STATUS.md
4. **NO GUESSING** - Read actual files, don't assume their contents

## FIRST TASK

1. Read MIGRATION_STATUS.md to find where we are
2. Read the relevant protocol section for the current phase
3. Continue with the next incomplete slice
4. Verify and update status
5. Report progress

Begin by reading MIGRATION_STATUS.md.
```

---

## Slice Completion Prompt (After Each Slice)

```
Slice [NAME] has been completed. Before proceeding:

1. **VERIFY** - Run the verification command for this slice
2. **TEST IMPORTS** - Ensure all old import paths still work
3. **UPDATE STATUS** - Mark this slice complete in MIGRATION_STATUS.md
4. **COMMIT** (optional) - Consider committing this verified slice

Verification command:
```bash
cd apps/api
python -c "
# [Insert slice-specific verification here]
"
```

If verification PASSES:
- Update MIGRATION_STATUS.md
- Proceed to next slice

If verification FAILS:
- STOP immediately
- Identify the issue
- Fix before proceeding
- Do NOT move on with broken code
```

---

## Rollback Prompt (If Something Breaks)

```
ALERT: Something is broken after the last change.

## IMMEDIATE ACTIONS

1. **IDENTIFY** - What was the last slice worked on?
2. **CHECK** - What error is occurring?
3. **COMPARE** - What files were changed?

## ROLLBACK PROCEDURE

If the issue is in the current slice:
1. Review the changes made
2. Identify the specific issue
3. Fix it carefully
4. Re-verify

If the issue requires reverting:
1. Use `git diff` to see all changes
2. Use `git checkout -- <file>` to revert specific files
3. Or `git reset --hard HEAD~1` to revert last commit

## NEVER

- Continue with broken code
- Try to "fix it later"
- Assume the error will go away
- Work around the issue without understanding it

Read the error message carefully. Trace it back to the source.
```

---

## Full System Verification Prompt

```
Run a complete system verification to ensure everything is working:

```bash
cd apps/api
python -c "
print('=' * 60)
print('  FULL SYSTEM VERIFICATION')
print('=' * 60)

# 1. Trait Categories
from src.digital_twin.traits.categories import TraitCategory, get_category_registry
print(f'✓ TraitCategory enum: {len(TraitCategory)} values')

# 2. Trait Frameworks
from src.digital_twin.traits.categories import TraitFramework
print(f'✓ TraitFramework enum: {len(TraitFramework)} values')

# 3. All domains
from src.digital_twin.domains import (
    GenesisDomain, HealthDomain, NutritionDomain, 
    JournalingDomain, FinanceDomain
)
print('✓ All 5 domains import')

# 4. Domain Registry
from src.digital_twin import get_domain_registry
registry = get_domain_registry()()
domains = list(registry._domains.keys())
print(f'✓ Registry: {domains}')

# 5. Total traits
total = sum(len(registry.get_domain(d).get_schema().traits) for d in domains)
print(f'✓ Total traits: {total}')

# 6. SwarmBus
from src.core.swarm_bus import SwarmBus, get_bus
print('✓ SwarmBus imports')

# 7. Orchestrator
from src.core.orchestrator import SovereignOrchestrator
print('✓ Orchestrator imports')

# 8. Sovereign Agent
try:
    from src.agents.sovereign import SovereignAgent
    print('✓ Sovereign Agent imports')
except ImportError as e:
    print(f'⚠ Sovereign Agent: {e}')

# 9. Genesis Agent
from src.agents.genesis import GenesisCore
print('✓ Genesis Agent imports')

print('=' * 60)
print('  ALL SYSTEMS VERIFIED')
print('=' * 60)
"
```

If any check fails, stop and investigate before proceeding.
```

---

## End of Session Prompt

```
Before ending this session, ensure:

1. **MIGRATION_STATUS.md is updated** with:
   - All completed slices marked
   - Current in-progress slice noted
   - Any issues or blockers documented
   - Timestamp of last verification

2. **All changes are committed** (if using git):
   ```bash
   git add -A
   git status
   git commit -m "True Fractal Migration: [describe completed slices]"
   ```

3. **Document next steps**:
   - What slice is next?
   - Any special considerations?
   - Any dependencies to resolve?

This ensures the next session can resume seamlessly.
```

---

## Emergency Context Recovery Prompt

```
I've lost context on the True Fractal Migration. Help me recover.

## PLEASE READ

1. `.github/COPILOT-UPGRADE.md` - Architecture spec
2. `.github/COPILOT-UPGRADE-ADDENDUM.md` - Additional layers
3. `.github/COPILOT-MIGRATION-PROTOCOL.md` - Execution protocol
4. `apps/api/MIGRATION_STATUS.md` - Current progress

## THEN ANALYZE

1. What phase are we in?
2. What slice are we working on?
3. What was last verified as working?
4. What's the next step?

## FINALLY

Provide a summary of:
- Migration progress (X of 22 slices complete)
- Current working slice
- Any blockers or issues
- Recommended next action

I need to understand the full picture before continuing.
```

---

## Specific Phase Prompts

### Phase 1 Prompt (Traits Foundation)

```
We are in Phase 1: Traits Foundation.

This phase migrates the trait system to fractal folders:
- traits/categories/ - Each category as a folder
- traits/frameworks/ - Each framework as a folder  
- traits/schema/ - TraitSchema as a folder

These have ZERO dependencies on other layers - they're pure foundations.

Current slice: [CHECK MIGRATION_STATUS.md]

Read the current implementation at:
- apps/api/src/digital_twin/traits/categories.py
- apps/api/src/digital_twin/traits/schema.py

Then create the fractal version following the protocol.
```

### Phase 3 Prompt (Domain Migration)

```
We are in Phase 3: Domain Migration.

For the [DOMAIN] domain:

1. Read current implementation:
   - apps/api/src/digital_twin/domains/[domain]/

2. Identify all concerns (tracker, analysis, patterns, etc.)

3. Create fractal sub-folders for each concern

4. Migrate code preserving all functionality

5. Update __init__.py to re-export everything

6. Verify the domain works in isolation

7. Verify cross-domain communication

Remember: Each concern becomes its own folder with the standard template.
```

### Phase 4 Prompt (Awareness Layer - New)

```
We are in Phase 4: Awareness Layer (NEW CREATION).

This is a new layer, not a migration. Create from scratch following:
- .github/COPILOT-UPGRADE-ADDENDUM.md (detailed spec)

Create the awareness/ folder with:
- query/ - Unified query interface
- events/ - Event bus system
- state/ - State management
- notifications/ - Push notifications
- introspection/ - Self-inspection
- correlation/ - Pattern correlation

Each sub-folder follows the standard fractal template.
```

---

## Tips for Effective Execution

1. **Start small** - Begin with the simplest slice (traits/categories)
2. **Build confidence** - Each verified slice builds momentum
3. **Don't rush** - This is a multi-session project
4. **Document everything** - Future you will thank present you
5. **Test constantly** - Verify after EVERY change, not just at the end
6. **Use git** - Commit after each verified slice for easy rollback

The goal is a perfectly fractal, infinitely extensible system. Take the time to do it right.
