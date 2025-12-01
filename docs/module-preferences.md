# Module Preferences System

This document describes the Module Preferences system - a comprehensive, fractal-extensible capability management layer for Project Sovereign.

## Architecture Overview

```
lib/state/module-preferences-atoms.ts    # State management with Jotai
app/settings/modules.tsx                  # Settings UI screen
app/_layout.tsx                           # Initialization on app start
lib/api-client.ts                         # API integration
apps/api/src/core/schemas.py              # Backend schema
```

## Core Concepts

### 1. AgentCapability Enum

The `AgentCapability` enum from `sovereign-protocol.ts` defines all available capabilities:

```typescript
export const AgentCapability = z.enum([
  'profiling',      // Genesis core - CANNOT be disabled
  'archetypes',     // Jungian archetypes
  'human_design',   // HD chart calculation
  'gene_keys',      // Gene Keys system (BETA)
  'astrology',      // Birth chart analysis (BETA)
  'numerology',     // Numerological patterns
  'vision',         // Image analysis - CORE
  'food_analysis',  // Nutrition tracking
  'health_metrics', // Health data (BETA)
  'finance',        // Financial tracking (BETA)
  'journaling',     // Reflective journaling
  'synthesis',      // Cross-domain synthesis - CORE
  'hrm_reasoning',  // Deep reasoning (toggleable)
]);
```

### 2. Module Categories

Modules are grouped into categories for UI organization:

- **Wisdom** (🔮 purple): Archetypal frameworks (archetypes, human_design, gene_keys, etc.)
- **Health** (💚 green): Physical wellness (food_analysis, health_metrics)
- **Life** (📊 amber): Life management (finance, journaling)
- **System** (⚙️ gray): Core capabilities (profiling, vision, synthesis, hrm_reasoning)

### 3. Module Definition

Each module has rich metadata:

```typescript
interface ModuleDefinition {
  id: AgentCapability;           // Unique identifier
  name: string;                   // Human-readable name
  description: string;            // Brief description
  longDescription?: string;       // Detailed explanation
  icon: string;                   // Emoji icon
  category: ModuleCategory;       // Group
  isCore: boolean;                // Cannot be disabled?
  dependencies: AgentCapability[]; // Auto-enabled modules
  isBeta?: boolean;               // Experimental?
  requiresSetup?: boolean;        // Needs configuration?
  order: number;                  // Display order
}
```

### 4. Dependency Management

- When enabling a module, its dependencies are **auto-enabled**
- When disabling a module, its dependents are **auto-disabled**
- Core modules (profiling, vision, synthesis) **cannot be disabled**

Example:
- Enabling `gene_keys` auto-enables `profiling` and `human_design`
- Disabling `human_design` auto-disables `gene_keys`

### 5. Presets

Quick configurations for common use cases:

- **Minimal**: Core capabilities only
- **Balanced**: Essential modules for daily use
- **Full Suite**: All modules enabled
- **Wisdom Focus**: All wisdom frameworks
- **Health Focus**: Health and wellness modules

## Usage in Components

### Reading Enabled Modules

```typescript
import { useAtomValue } from 'jotai';
import { enabledModulesAtom } from '../lib/state/module-preferences-atoms';

function MyComponent() {
  const enabledModules = useAtomValue(enabledModulesAtom);
  
  // Check if a specific module is enabled
  const hasHumanDesign = enabledModules.includes('human_design');
}
```

### Toggling Modules

```typescript
import { useSetAtom } from 'jotai';
import { toggleModuleAtom } from '../lib/state/module-preferences-atoms';

function ModuleToggle({ moduleId }) {
  const toggleModule = useSetAtom(toggleModuleAtom);
  
  return (
    <Switch
      value={isEnabled}
      onValueChange={() => toggleModule(moduleId)}
    />
  );
}
```

### Sending to Backend

```typescript
import { useAtomValue } from 'jotai';
import { enabledModulesAtom } from '../lib/state/module-preferences-atoms';

function useChat() {
  const enabledModules = useAtomValue(enabledModulesAtom);
  
  await apiClient.chatStream({
    message: 'Hello',
    enabled_capabilities: enabledModules,
  });
}
```

## Backend Integration

The backend receives `enabled_capabilities` in the `ChatRequest`:

```python
class ChatRequest(BaseModel):
    message: str
    enabled_capabilities: Optional[list[str]] = None
```

The Orchestrator and agents can filter their behavior based on enabled capabilities:

```python
def process_request(request: ChatRequest):
    enabled = set(request.enabled_capabilities or [])
    
    if 'human_design' in enabled:
        # Include HD analysis
        pass
    
    if 'food_analysis' in enabled:
        # Enable nutrition features
        pass
```

## Extending the System

### Adding a New Module

1. Add to `AgentCapability` enum in `sovereign-protocol.ts`
2. Add definition to `MODULE_REGISTRY` in `module-preferences-atoms.ts`
3. Backend: Handle the capability in relevant agents

Example:

```typescript
// In sovereign-protocol.ts
export const AgentCapability = z.enum([
  // ... existing
  'meditation',  // NEW
]);

// In module-preferences-atoms.ts
meditation: {
  id: 'meditation',
  name: 'Meditation Tracker',
  description: 'Track meditation practice',
  icon: '🧘',
  category: 'health',
  isCore: false,
  dependencies: ['profiling'],
  order: 3,
},
```

### Adding a New Category

1. Add to `ModuleCategory` type
2. Add to `MODULE_CATEGORIES` object
3. Add section in `modules.tsx` UI

## Storage

Preferences are persisted to AsyncStorage with key `@sovereign/module_preferences`.

Format:
```json
{
  "profiling": { "enabled": true, "enabledAt": "2025-11-30T..." },
  "human_design": { "enabled": true, "enabledAt": "2025-11-30T..." },
  "gene_keys": { "enabled": false }
}
```

## Initialization

On app start, `initModulePreferencesAtom` is called in `StateInitializer`:

```typescript
function StateInitializer({ children }) {
  const initModulePreferences = useSetAtom(initModulePreferencesAtom);
  
  useEffect(() => {
    initModulePreferences();
  }, []);
  
  return <>{children}</>;
}
```

This loads saved preferences and merges with defaults (handling new modules).
