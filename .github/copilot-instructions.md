# Project Sovereign - AI-Native Self-Mastery Platform

## Project Overview

**Project Sovereign** (also known as "The Collapse OS") is an AI-native mobile + web application for self-mastery and personal transformation. It builds a "Digital Twin" profile system that deeply understands the user through multiple wisdom frameworks.

Built with Expo + Tamagui + Vercel AI SDK + LangChain.js (frontend) and FastAPI + LangGraph (backend) for dynamic, generative experiences.

## ⚠️ CRITICAL: Knowledge Verification Directive

**AI assistants working on this project MUST follow these verification rules:**

### 1. Never Assume Information is Outdated or Fictional
- Model names, API versions, SDK versions, and configurations in this codebase may reference **preview, beta, or recently-released** technologies
- Examples: `gemini-3-pro-preview`, `gemini-2.5-flash`, `gemini-2.5-pro` are VALID model names
- Your training data has a cutoff date — **do not assume something doesn't exist just because you haven't seen it**

### 2. Mandatory Web Verification Triggers
Before claiming something is "fictional," "doesn't exist," or "not yet released," you MUST:
1. **Use available tools** (fetch_webpage, browser MCP tools, search tools) to verify current information
2. **Check official documentation** (Google AI docs, npm registries, PyPI, GitHub releases)
3. **Search for the exact string** (model name, package version) on the live web

### 3. When to Perform Web Verification
- When you encounter model names you don't recognize
- When version numbers seem "too new" for your knowledge
- When configurations reference features you're unsure about
- When the user states something contradicts your assumptions
- When making ANY claim about API availability, deprecation, or naming

### 4. Verification Sources (in order of preference)
1. **Official docs**: ai.google.dev, developers.google.com, expo.dev, docs.python.org
2. **Package registries**: npmjs.com, pypi.org
3. **GitHub releases**: Check release notes for latest versions
4. **Web search**: For breaking changes or preview announcements

### 5. Default Behavior
- **Trust the codebase** — if a model name or config exists in the code, assume it's intentional and valid
- **Ask before changing** — if you suspect a typo vs. a new feature, ask the user rather than "fixing" it
- **Log your verification** — when you do check the web, briefly note what you found

### 6. This Project Uses Cutting-Edge Technologies
The following are CONFIRMED VALID in this project (do not question these):
- Google Gemini models: `gemini-3-pro-preview`, `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`
- Expo SDK 54 with React Native 0.82
- Tamagui 1.136
- LangChain 0.3, LangGraph 1.0
- FastAPI 0.122
- Python 3.14 (latest)
- All configurations in `apps/api/src/core/config.py` are intentional

---

## ⚠️ CRITICAL: Fractal Extensibility Directive

**All code in this project MUST follow the Fractal Extensibility Pattern:**

### 1. Engineering Standards
All configurations, coding, functions, and processes must be configured **meticulously with maximum scrutiny and fidelity**. This project demands **peak high-fidelity engineering** that you'd expect to see at the very top of the field.

### 2. The Fractal Extensibility Pattern
Every component must be architected for **infinite expansion** while maintaining clean separation of concerns:

```
Component/
├── feature_a/       # One concern, fully encapsulated
├── feature_b/       # Another concern, independently extensible
├── feature_c/       # Future features slot in seamlessly
└── ...              # The pattern continues infinitely
```

### 3. Design Principles
1. **Modularity First**: Every component must be independently replaceable
2. **Plugin Architecture**: New capabilities added by dropping in new modules
3. **Registry Pattern**: Dynamic discovery and registration of components
4. **Abstract Base Classes**: Define interfaces that implementations conform to
5. **No Monoliths**: Large systems must decompose into smaller, focused units
6. **Clean Contracts**: Components communicate via well-defined interfaces

### 4. The Face Example (Genesis)
The Face system demonstrates this pattern perfectly:
```
Face/
├── voice/           # HOW it speaks (tone, personality, vocabulary)
│   ├── voices.py    # Oracle, Sage, Companion, Challenger, Mirror
│   └── __init__.py  # VoiceRegistry, VoiceSelector, Voice ABC
├── eyes/            # HOW it perceives (future: emotion detection)
├── ears/            # HOW it listens (future: audio processing)
├── expression/      # HOW it emotes (future: visual expressions)
└── memory/          # HOW it remembers context
```

### 5. When Creating New Components
- Ask: "How would someone extend this in 6 months?"
- Ask: "Can this be replaced without touching other code?"
- Ask: "Is there a registry for dynamic discovery?"
- Ask: "Does this have a clear abstract interface?"

### 6. Code Quality Expectations
- **Type Safety**: Full typing with Python type hints and TypeScript
- **Documentation**: Every class/function has docstrings explaining purpose
- **Error Handling**: Graceful degradation, never silent failures
- **Testing Hooks**: Code must be testable in isolation
- **Logging**: Strategic logging for debugging and monitoring

---

## Recent Changes (December 2025)

### Sovereign Agent - The Omniscient Main App Agent

The Sovereign Agent is the **primary interface agent** that knows and understands absolutely everything about the app. It connects to ALL deep systems and serves as the user's intelligent companion throughout the entire app experience.

1. **Architecture** (`apps/api/src/agents/sovereign/`)
   - Fractal 6-module design following extensibility pattern
   - Full integration with HRM, LLM Factory, SwarmBus, Orchestrator, Genesis, and Master Agents

   ```
   sovereign/
   ├── __init__.py       # Exports SovereignAgent
   ├── agent.py          # Main SovereignAgent class (chat, chat_stream, initialize)
   ├── cortex.py         # LLM thinking core (SystemPromptBuilder, ResponseParser)
   ├── memory.py         # Session memory, conversation history, Digital Twin
   ├── tools.py          # 6 tools including GenerateUITool with 10 component types
   ├── router.py         # Routes to specialized agents based on intent
   └── integrations.py   # 6 integration classes for deep system connections
   ```

2. **SovereignAgent Class** (`agent.py`)
   - `initialize(session_id)` - Start new session with greeting
   - `chat(message, session_id)` - Synchronous chat with tool execution
   - `chat_stream(message, session_id)` - SSE streaming with real-time tokens
   - Uses LangChain `ChatGoogleGenerativeAI` with function calling
   - Automatic session management and memory persistence

3. **Cortex - The Thinking Core** (`cortex.py`)
   - `SystemPromptBuilder` - Generates context-aware system prompts
   - `ResponseParser` - Parses LLM output, handles tool calls, extracts components
   - `CortexOutput` - Structured output: text, components, tool_calls, tool_name
   - **Critical Fix**: Gemini returns `response.content` as list of parts, must join into string

4. **Memory System** (`memory.py`)
   - `SovereignMemory` - Session state and conversation history
   - `ConversationTurn` - Individual message with role, content, timestamp, metadata
   - `SessionState` - Current session: phase, turn_count, insights, digital_twin
   - Tracks user profile data accumulated across conversation

5. **Tool System** (`tools.py`)
   - `ToolParameter` - Schema for tool parameters with type, description, required, items
   - **Critical Fix**: Array parameters MUST have `items` field for Gemini function calling
   - 6 Built-in Tools:
     - `GenerateUITool` - Creates UI components (10 types)
     - `GetUserProfileTool` - Retrieves Digital Twin data
     - `RouteToAgentTool` - Delegates to specialized agents
     - `SearchKnowledgeTool` - Queries knowledge base
     - `GetSystemStatusTool` - App health and diagnostics
     - `UpdateUserPreferencesTool` - Modifies user settings

6. **GenerateUITool - 10 Component Types**
   ```python
   UI_COMPONENT_TYPES = [
       "text",              # Simple text display
       "insight_card",      # Rich insight with icon and description
       "input",             # Text input field
       "progress",          # Progress indicator
       "choice",            # Multiple choice options
       "binary_choice",     # Yes/no decision
       "slider",            # Numeric range input
       "cards",             # Grid of selectable cards
       "digital_twin_card", # Digital Twin visualization
       "activation_steps",  # Onboarding steps
   ]
   ```

7. **Router** (`router.py`)
   - Intent classification via LLM
   - Routes to specialized agents: Genesis, Vision, Finance, Health
   - Returns consolidated responses from sub-agents
   - Fallback handling for unknown intents

8. **Deep System Integrations** (`integrations.py`)
   - `HRMIntegration` - Hierarchical Reasoning Model access
   - `LLMFactoryIntegration` - Multi-provider model creation
   - `SwarmBusIntegration` - Agent communication bus
   - `OrchestratorIntegration` - Central routing brain
   - `GenesisIntegration` - Profiling agent access
   - `MasterAgentsIntegration` - Hypothesis Engine and Scout

9. **API Endpoints** (`apps/api/src/routers/sovereign.py`)
   ```
   POST /sovereign/chat         - Synchronous chat
   POST /sovereign/chat/stream  - SSE streaming chat
   GET  /sovereign/tools        - List available tools
   GET  /sovereign/agents       - List connected agents
   GET  /sovereign/capabilities - Full capability report
   ```

10. **SSE Streaming Protocol**
    ```python
    # Backend yields events:
    {"type": "start", "data": {"session_id": "..."}}
    {"type": "chunk", "data": "token text"}           # Individual tokens
    {"type": "component", "data": {...}}              # UI component
    {"type": "tool_call", "data": {"name": "...", "args": {...}}}
    {"type": "complete", "data": {"text": "...", "components": [...]}}
    {"type": "error", "data": {"message": "..."}}
    ```

11. **Frontend Integration** (`lib/api-client.ts`)
    ```typescript
    async sovereignChatStream(
      message: string,
      sessionId: string,
      onToken: (token: string) => void,
      onComponent: (component: any) => void,
      onComplete: (response: any) => void,
      onError: (error: string) => void
    )
    ```

12. **GlobalAgentShell UI** (`components/GlobalAgentShell.tsx`)
    - **Floating overlay pattern** using `position: 'absolute'`
    - Covers full screen but allows touch passthrough with `pointerEvents: 'box-none'`
    - Renders GenerativeRenderer for AI-generated components
    - Collapsible/expandable chat interface

    ```typescript
    const styles = StyleSheet.create({
      container: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        top: 0,
        pointerEvents: 'box-none',
      },
    });
    ```

13. **Test Suite** (`apps/api/test_sovereign_agent.py`)
    - 17 unit tests + integration tests (15/15 passing)
    - Tests: initialization, chat, streaming, tools, routing, integrations
    - Run with: `python test_sovereign_agent.py`

### GenerativeRenderer Component Updates

Enhanced to support Sovereign Agent's UI components:

1. **Added `insight_card` Support** (`components/genesis/GenerativeRenderer.tsx`)
   ```typescript
   case 'insight_card':
     return (
       <YStack backgroundColor="$blue3" padding="$4" borderRadius="$4">
         <XStack alignItems="center" gap="$2">
           <Text fontSize="$6">{component.icon || '💡'}</Text>
           <Text fontWeight="bold" color="$blue11">{component.title}</Text>
         </XStack>
         <Text color="$gray11">{component.description}</Text>
       </YStack>
     );
   ```

2. **Component Props at Root Level**
   - **CORRECT**: `{"type": "insight_card", "title": "...", "description": "..."}`
   - **WRONG**: `{"type": "insight_card", "props": {"title": "..."}}`
   - All component data lives at root level, NOT nested in `props`

---

## Recent Changes (November 30, 2025)

### Voice System Architecture (Genesis Face)

The Genesis Face now has a modular, extensible voice system:

1. **Face Structure** (`apps/api/src/agents/genesis/face/`)
   - Fractal architecture following the extensibility pattern
   - `voice/` - Complete voice system with 5 built-in voices
   - Future: `eyes/`, `ears/`, `expression/`, `memory/`

2. **Voice Components** (`face/voice/`)
   - `Voice` - Abstract base class defining voice interface
   - `VoiceIdentity` - Metadata (name, description, icon, tones, phases)
   - `VoiceModifiers` - Dynamic adjustments (intensity, formality, warmth, mystery)
   - `VoiceRegistry` - Plugin-based discovery and registration
   - `VoiceSelector` - Intelligent selection (manual, adaptive, dynamic, hybrid)
   - `BlendedVoice` - Composite pattern for mixing voices

3. **Built-in Voices** (`face/voice/voices.py`)
   - **Oracle** 🔮 - Ancient wisdom, symbolic language, penetrating questions
   - **Sage** 📚 - Calm, measured, practical wisdom and clear explanations
   - **Companion** 💚 - Warm, supportive, emotionally attuned presence
   - **Challenger** ⚡ - Direct, provocative, pushes boundaries
   - **Mirror** 🪞 - Reflective, echoes back with minimal interpretation

4. **Voice Selection Modes**
   - `MANUAL` - User explicitly chooses their preferred voice
   - `ADAPTIVE` - System learns preference over time via feedback
   - `DYNAMIC` - Context-aware switching based on phase/state/content
   - `HYBRID` - Combines adaptive preferences with dynamic context

5. **FaceOrchestrator** (`face/__init__.py`)
   - Central coordinator for all Face components
   - `get_voice()` - Get voice for current context
   - `get_system_prompt()` - Get complete prompt from selected voice
   - `record_feedback()` - Train adaptive selection
   - `list_available_voices()` - Get all voices with metadata

6. **FaceFactory** - Preset configurations
   - `create_default()` - Dynamic selection, Oracle fallback
   - `create_therapeutic()` - Emphasizes Companion and Mirror
   - `create_coaching()` - Emphasizes Challenger and Sage
   - `create_mystical()` - Oracle only, high mystery

### Profile Storage System

Persistent storage for Digital Twin profiles with save/load/resume functionality:

1. **Storage Module** (`apps/api/src/storage/`)
   - Fractal architecture with clean separation of concerns
   - File-based persistence in `apps/api/data/` directory
   - Auto-save during profiling for crash recovery

2. **Profile Storage** (`storage/profile_storage.py`)
   - `ProfileStorage` - Main storage engine class
   - `SavedProfile` - Full profile data (slot + state + digital_twin)
   - `ProfileSlot` - Metadata for listing (name, status, phase, completion)
   - `ProfileStatus` - Enum: `in_progress`, `completed`, `archived`

3. **Storage Structure**
   ```
   apps/api/data/
   ├── profiles/           # Completed/saved profiles
   │   ├── slot_1.json
   │   ├── slot_2.json
   │   └── ...
   ├── sessions/           # In-progress sessions (auto-saved)
   │   ├── {session_id}.json
   │   └── ...
   └── exports/            # Shareable exports
       └── {name}_{timestamp}.json
   ```

4. **API Endpoints** (`routers/profiles.py`)
   - `GET /profiles/` - List all saved profiles
   - `GET /profiles/{slot_id}` - Load a specific profile
   - `POST /profiles/save` - Save current session to profile
   - `POST /profiles/{slot_id}/resume` - Resume from saved profile
   - `DELETE /profiles/{slot_id}` - Delete a profile
   - `POST /profiles/{slot_id}/export` - Export to JSON file
   - `GET /profiles/{slot_id}/download` - Download exported file

5. **Frontend Integration**
   - `lib/api-client.ts` - API client methods for all endpoints
   - `app/settings/profiles.tsx` - Profile management UI
   - `app/genesis/index.tsx` - Save button in header (💾)
   - Settings → "Saved Profiles" - View and manage all profiles

6. **Key Features**
   - **10 Profile Slots**: Save up to 10 different profiles
   - **Auto-Save**: Sessions saved automatically for crash recovery
   - **Resume**: Pick up exactly where you left off
   - **Export/Import**: Share profiles via JSON files
   - **Digital Twin**: Completed profiles include full Digital Twin export

### Natural Voice Layer (Default Voice)

The default voice that makes Genesis feel approachable:

1. **NaturalVoice** (`face/voice/natural.py`)
   - Transforms Oracle/Sage questions into casual conversation
   - Removes metaphors, symbolic language, formal tone
   - Makes Genesis feel like talking to a friend

2. **SophisticationAnalyzer**
   - Tracks user depth via patterns in responses
   - Metrics: introspective_depth, emotional_openness, vocabulary_level
   - Threshold: When score > 0.6, switches to Oracle/Sage voices

3. **Voice Progression**
   - Start: Natural voice for all users (score = 0)
   - Progress: As user shows depth, sophistication score increases
   - Transition: At threshold, sophisticated voices become available
   - Dynamic: Can blend Natural with Oracle/Sage for gradual transition

### Global Overlay System Architecture

A new app-wide overlay system enables generative UI to appear from **anywhere** in the app:

1. **Global UI Atoms** (`lib/state/global-ui-atoms.ts`)
   - Priority-based overlay queue with FIFO processing
   - Overlay types: `game`, `notification`, `insight`, `challenge`, `custom`
   - Helper functions: `createGameOverlay()`, `createNotificationOverlay()`, `createInsightOverlay()`, `createChallengeOverlay()`
   - Atoms: `overlayQueueAtom`, `activeOverlayAtom`, `pushOverlayAtom`, `dismissOverlayAtom`, `clearAllOverlaysAtom`

2. **GlobalOverlayProvider** (`components/GlobalOverlayProvider.tsx`)
   - Wraps entire app at root level (inside Jotai Provider)
   - Renders overlays via Modal with proper styling per type
   - Handles game completion/timeout with automatic result saving
   - Auto-close support for notifications via `autoCloseMs`

3. **Integration Pattern**
   ```typescript
   import { useSetAtom } from 'jotai';
   import { pushOverlayAtom, createGameOverlay } from '../lib/state/global-ui-atoms';
   
   const pushOverlay = useSetAtom(pushOverlayAtom);
   pushOverlay(createGameOverlay(gameDefinition));
   ```

### Micro-Games System

Cognitive assessment games that can appear during profiling or on-demand:

1. **Game Types** (`lib/games/types.ts`)
   - `reflex_tap`: Reaction time measurement
   - `pattern_match`: Pattern recognition (planned)
   - `memory_flash`: Working memory (planned)
   - `speed_choice`: Decision speed (planned)
   - Difficulty levels: `easy`, `medium`, `hard`

2. **Game Storage** (`lib/games/storage.ts`)
   - AsyncStorage persistence with key `@sovereign/game_results`
   - Functions: `saveGameResult()`, `getGameResults()`, `getGameStats()`, `clearGameResults()`
   - Stats tracking: total games, average score, best score, average reaction time

3. **Game Scheduler** (`lib/games/scheduler.ts`)
   - `GameScheduler` class for triggering games during profiling
   - Configurable intervals and phase-based game selection
   - Callback system for game triggering

4. **ReflexTapComponent** (`components/genesis/ReflexTapComponent.tsx`)
   - Animated tap-timing game using react-native-reanimated
   - Visual feedback: pulsing rings, color transitions, score display
   - Difficulty-based timing (easy: 5s, medium: 3s, hard: 2s)
   - Results: reaction time, accuracy, completion status

5. **Mini-Games Lab** (Home Screen)
   - Accessible from home screen for testing during development
   - Difficulty selector (Easy/Medium/Hard)
   - Stats display (games played, average score)
   - Uses global overlay system for game display

### HRM (Hierarchical Reasoning Model) Frontend Integration

Complete frontend configuration UI for the backend HRM system:

1. **HRM Settings Screen** (`app/settings/hrm.tsx`)
   - Full configuration UI for all HRM parameters
   - Grouped sections: Core, Cycles, Depth Limits, Beam Search, Debug
   - Real-time parameter updates with AsyncStorage persistence
   - Reset to defaults functionality

2. **HRM Atoms** (`lib/state/hrm-atoms.ts`)
   - `HRMConfig` interface with all parameters:
     - `enabled`: boolean - Toggle HRM on/off
     - `thinkingLevel`: 'low' | 'high' - Reasoning depth
     - `hCycles` / `lCycles`: number - Processing cycles
     - `maxReasoningDepth`: number - Maximum depth
     - `haltThreshold`: number - Early stopping threshold
     - `candidateCount`: number - Candidates per expansion
     - `beamSize`: number - Beam search width
     - `scoreThreshold`: number - Minimum score threshold
     - `showReasoningTrace`: boolean - Show reasoning steps
     - `verboseLogging`: boolean - Detailed logging
   - `hrmApiConfigAtom`: Transforms camelCase → snake_case for backend
   - `initHrmConfigAtom`: Loads config from AsyncStorage on app start
   - Persistence key: `@sovereign/hrm_config`

3. **HRM API Integration**
   - HRM config included in chat requests to `/api/python/chat/stream`
   - Backend respects all frontend-configured parameters
   - Thinking level affects processing depth and response quality

### Model Configuration System (Multi-Provider LLM Support)

Complete multi-model selection system with frontend UI and backend LLM Factory:

1. **Model Configuration Screen** (`app/settings/models.tsx`)
   - Full UI for selecting models for each purpose
   - Preset buttons: Balanced, Performance, Economy
   - Real-time persistence with AsyncStorage
   - Shows all available models with metadata (tier, speed, quality)

2. **Model Config Atoms** (`lib/state/model-config-atoms.ts`)
   - `ModelConfig` interface with role-based model assignments:
     - `primary`: Main conversation model (highest quality)
     - `fast`: Real-time operations (pattern detection, probes)
     - `synthesis`: Deep insight generation
     - `fallback`: Backup when primary fails
   - Preset configurations:
     - `default`: Balanced Gemini defaults
     - `performance`: Best models (Gemini 3 Pro Preview)
     - `economy`: Fastest/cheapest (Gemini Flash Lite)
   - Persistence key: `@sovereign/model_config`

3. **Available Models**
   - **Google Gemini**:
     - `gemini-3-pro-preview` (flagship, slow, highest quality)
     - `gemini-2.5-pro` (advanced, medium speed)
     - `gemini-2.5-flash` (fast, good quality)
     - `gemini-2.5-flash-lite` (fastest, adequate quality)
   - **OpenRouter**:
     - `x-ai/grok-4.1-fast:free` (xAI's agentic model, 2M context, free tier)

4. **LLM Factory** (`apps/api/src/core/llm_factory.py`)
   - Central factory for creating LLM instances from any provider
   - Auto-routes by model ID (`/` in ID = OpenRouter, else = Google)
   - Provider-specific configuration (headers, base URLs)
   - Caching to avoid recreating LLMs
   - Methods:
     - `get_llm(model, temperature, max_tokens)` - Get LLM instance
     - `get_available_models()` - Models grouped by provider
     - `get_default_model(role)` - Best available for role

5. **API Integration**
   - Frontend sends `models_config` in chat requests
   - Backend `ModelConfig` class validates and applies configuration
   - Automatic fallback on rate limits when `auto_fallback` enabled

### Genesis Session Persistence Fix

Fixed issue where Genesis would start at question 2 instead of 1 on return:

1. **StoredSession Extended** (`app/genesis/index.tsx`)
   - Added `lastPayload` field to store displayed components
   - Session saves payload on each agent response
   - On return, restores exact question/components displayed

2. **Persistence Flow**
   - Save: `saveSession({ lastPayload: payload, phase: payload.phase })`
   - Load: Checks for `lastPayload.components` and restores if present
   - Prevents session advancement without user interaction

### SSE Streaming with react-native-sse

Using `react-native-sse` package for Server-Sent Events (NOT EventSource polyfills):

1. **API Client** (`lib/api-client.ts`)
   - `chatStream()` method uses `EventSource` from react-native-sse
   - Proper event listeners: `open`, `message`, `error`
   - Streaming text overlay during AI response generation
   - Request/response logging for debugging

2. **Backend SSE Format** (`apps/api/src/routers/chat.py`)
   - Uses `sse_starlette.EventSourceResponse` for streaming
   - **CRITICAL**: Yield dicts with `{'data': json.dumps({...})}` format
   - Do NOT manually add `data:` prefix - `sse_starlette` handles it
   - SSE delimiter is `\r\n\r\n` (not `\n\n`)

3. **Usage Pattern**
   ```typescript
   import EventSource from 'react-native-sse';
   
   const es = new EventSource(url, { headers, method: 'POST', body });
   es.addEventListener('message', (event) => { /* handle */ });
   ```

### Frontend-Backend Contract Fixes (Critical)

Fixed critical contract mismatches between frontend and backend:

1. **Component Data at ROOT Level** (`apps/api/src/agents/genesis_profiler.py`)
   - **WRONG**: `{"type": "digital_twin_card", "props": {"digital_twin": {...}}}`
   - **CORRECT**: `{"type": "digital_twin_card", "digital_twin": {...}}`
   - Frontend `GenerativeRenderer.tsx` reads data at ROOT level, not in `props` wrapper
   - Applies to: `digital_twin_card`, `activation_steps`, `completion_transition`

2. **ActiveSignal Class** (`apps/api/src/agents/genesis/state.py`)
   - Uses plain strings for `signal_type`, NOT an enum
   - Fields: `source`, `content`, `signal_type`, `confidence`, `suggested_traits`, `timestamp`
   - `to_dict()` returns format matching `SessionInsight` interface

3. **Voice System Method Names** (`apps/api/src/agents/genesis/face/voice/`)
   - `VoiceRegistry.list_ids()` - NOT `list_voice_ids()`
   - `VoiceSelector.select(context, history)` - NOT `select_voice(phase)`
   - `FaceOrchestrator.get_voice(context, history)` - NOT `get_voice(phase=)`

4. **ChatRequest Schema** (`apps/api/src/core/schemas.py`)
   - Field is `message`, NOT `user_message`
   - Full schema: `{message: str, session_id?: str, enable_hrm: bool, models_config?: ModelsConfig, context?: AgentContext}`

### Test Infrastructure

Comprehensive test suites for contract validation:

1. **Live System Tests** (`apps/api/test_live_system.py`)
   - Tests ACTUAL running API with real HTTP requests
   - Verifies: health, agents, opening message, conversation flow, SSE streaming, session persistence
   - Run with: `python test_live_system.py`

2. **Contract Validation Tests** (`apps/api/test_contract_validation.py`)
   - Validates frontend-backend type contracts match
   - Tests: ActiveSignal, Digital Twin Export, Completion Components, Voice System, Component Registry
   - Run with: `python test_contract_validation.py`

3. **Completion Flow Tests** (`apps/api/test_completion_flow.py`)
   - Tests Digital Twin export, activation steps generation, completion components
   - Validates SwarmBus integration methods exist
   - Run with: `python test_completion_flow.py`

4. **Full Genesis Tests** (`apps/api/test_genesis_full_flow.py`)
   - Comprehensive 74-test suite for all Genesis functionality
   - Run with: `python test_genesis_full_flow.py`

---

## Recent Changes (November 29, 2025)

### Import.meta & Premature Close Error Fixes

1. **Fixed "Premature close" and "import.meta" Errors**
   - Root cause: react-native-web 0.21.x ships ESM-only code with `import.meta` syntax that Metro in Expo SDK 54 doesn't transpile
   - When browser hit the parse error, it dropped connections causing Metro to log "Premature close"
   - Solution: Downgraded react-native-web to 0.19.13 (last CommonJS version)
   - This eliminates the need for babel-plugin-transform-import-meta workarounds

2. **Fixed Animated.View Web Rendering**
   - Animated.View from react-native-reanimated doesn't render correctly on web
   - Homepage now uses standard React Native View components instead
   - This ensures consistent rendering across web and native platforms

3. **Enhanced Error Logging**
   - `lib/utils/error-logger.ts` - Comprehensive logging utility with timestamps, component tracking
   - `lib/api-client.ts` - Added detailed request/response logging for API calls and SSE streams

### Metro Bundler & File Watcher Fixes

1. **Fixed ENOSPC File Watcher Limit**
   - Patched Metro file watchers (`FallbackWatcher.js`, `NodeWatcher.js`) to skip watching node_modules directories
   - This prevents hitting the inotify file watcher limit in Replit's environment
   - Files patched in: `node_modules/metro-file-map/`, `node_modules/metro/node_modules/metro-file-map/`, etc.

2. **Simplified Metro Configuration**
   - `metro.config.js` - Cleaned up, removed custom resolveRequest function
   - Maintained blockList for non-essential directories (attached_assets, .venv, etc.)

## Recent Changes (November 28, 2025)

### Genesis Profiler High-Fidelity Frontend

1. **Void Theme UI** - Deep dark aesthetic (#050505) with Samsung Edge-style pulsing borders
   - `components/genesis/PulsingBorder.tsx` - Animated edge glow using react-native-reanimated
   - Pulse colors change based on AI state: cyan (listening), purple (thinking), gold (excavation), red (alert)

2. **Generative UI Renderer**
   - `components/genesis/GenerativeRenderer.tsx` - Maps backend JSON specs to Tamagui components
   - Supports: text, input, slider, choice cards, progress indicators
   - Phase-aware theming with smooth AnimatePresence transitions

3. **SSE Streaming Integration**
   - `app/genesis/index.tsx` - Real-time streaming from backend via Server-Sent Events
   - `lib/api-client.ts` - Frontend API client with chatStream method
   - Streaming text overlay during AI response generation

4. **AI State Management**
   - `lib/state/genesis-atoms.ts` - Jotai atoms for reactive AI states
   - States: listening, thinking, idle, alert
   - Phase tracking: awakening → excavation → mapping → synthesis → activation

### FastAPI Backend Integration

1. **Added FastAPI Backend** (`apps/api/`)
   - Python-based API server running on port 8000
   - Serves under `/api/python` prefix
   - CORS configured for Replit domains
   - HRM (Hierarchical Reasoning Model) logic layer for deep reasoning

2. **Shared Agent Contract**
   - `lib/agents/base-agent.ts` is the SOURCE OF TRUTH for schemas
   - Pydantic models in `apps/api/src/core/schemas.py` exactly match TypeScript schemas
   - Universal Protocol for inter-agent communication

3. **Updated Start Script**
   - `yarn start` now uses production static export (`expo export`) to avoid file watcher limits
   - Uses `concurrently` to run both Expo (port 5000) and FastAPI (port 8000)
   - Individual commands: `yarn start:expo`, `yarn start:api`, `yarn start:dev` (dev mode)

4. **Key Files**
   - `lib/constants.ts` - Configurable model settings (Gemini 3 Pro Preview support)
   - `lib/api-client.ts` - Frontend API client for backend communication
   - `packages/ui/registry/index.ts` - Component registry for generative UI
   - `apps/api/` - Complete FastAPI backend with agents, routers, HRM

## Tech Stack

### Frontend
- **Framework**: Expo SDK 54 + React Native 0.82
- **UI**: Tamagui 1.136 (purple/cyan void theme)
- **Routing**: Expo Router 6.0
- **State**: Jotai 2.15 with AsyncStorage persistence
- **AI Core**: Vercel AI SDK 5.0
- **AI Models**: Google Gemini 2.5/3.0, OpenRouter (Grok 4.1 Fast)
- **SSE**: react-native-sse for streaming responses
- **Animations**: react-native-reanimated for game UIs
- **Agents** (Native Only): LangChain.js 1.0

### Backend
- **Framework**: FastAPI 0.122 (Python 3.14)
- **AI/ML**: LangChain 0.3, LangGraph 1.0, LangChain-Google-GenAI 2.0, LangChain-OpenAI
- **LLM Factory**: Multi-provider routing (Google, OpenRouter)
- **Streaming**: SSE-Starlette for real-time responses
- **Models**: Gemini 3 Pro Preview, Gemini 2.5 Pro/Flash, Grok 4.1 Fast (OpenRouter)
- **Reasoning**: HRM (Hierarchical Reasoning Model) with beam search

### Shared
- **Database**: Supabase 2.80 (with pgvector for RAG)
- **Storage**: AsyncStorage for state persistence, react-native-mmkv 4.0 for high-performance

## Architecture

### The Sovereign Swarm - Hybrid Agent Architecture

The backend implements a **Hybrid Swarm** pattern that combines:
1. **Orchestrator-Centric Control** - Single source of truth, intelligent routing
2. **SwarmBus Parallel Processing** - Async message passing, scalable execution

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              HYBRID ARCHITECTURE                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║                        ┌─────────────────────────┐                           ║
║                        │      ORCHESTRATOR       │                           ║
║                        │    (LangGraph Brain)    │                           ║
║                        │  • Intent Classification │                           ║
║                        │  • State Management      │                           ║
║                        │  • Final Synthesis       │                           ║
║                        └───────────┬─────────────┘                           ║
║                                    │                                          ║
║                                    ▼                                          ║
║                        ┌─────────────────────────┐                           ║
║                        │       SWARM BUS         │                           ║
║                        │  • Priority Queues      │                           ║
║                        │  • Parallel Execution   │                           ║
║                        │  • Auto-Discovery       │                           ║
║                        └───────────┬─────────────┘                           ║
║                                    │                                          ║
║         ┌──────────────────────────┼──────────────────────────┐              ║
║         ▼                          ▼                          ▼              ║
║  ┌─────────────┐          ┌─────────────────┐          ┌─────────────┐       ║
║  │   MASTER    │          │     MASTER      │          │   MASTER    │       ║
║  │ HYPOTHESIS  │◄────────►│     SCOUT       │◄────────►│   (Future)  │       ║
║  │   ENGINE    │          │  (Digital Twin) │          │             │       ║
║  └──────┬──────┘          └────────┬────────┘          └─────────────┘       ║
║         │                          │                                          ║
║         └──────────────────────────┼──────────────────────────┐              ║
║                                    │                          │              ║
║         ┌──────────────────────────┼──────────────────────────┤              ║
║         ▼                          ▼                          ▼              ║
║  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐          ║
║  │   GENESIS   │          │   VISION    │          │   FINANCE   │          ║
║  │  (Profile)  │          │   (Eyes)    │          │  (Tracker)  │          ║
║  └─────────────┘          └─────────────┘          └─────────────┘          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Key Principle: "Orchestrator DECIDES, SwarmBus EXECUTES"

The Orchestrator is the **brain** that decides what to do:
- Receives user requests
- Classifies intent
- Routes to appropriate agents
- Synthesizes final responses

The SwarmBus is the **nervous system** that executes:
- Parallel message delivery to multiple agents
- Priority-based queue processing
- Agent discovery via capability registration
- Escalation and delegation patterns

### Agent Hierarchy (5 Tiers)

```
TIER -1: SOVEREIGN AGENT (NEW)
  └── The omniscient main app agent
  └── User's primary interface to ALL systems
  └── Full access to every integration
  └── LangChain + Gemini with function calling

TIER 0: ORCHESTRATOR
  └── The central brain, makes all routing decisions
  └── Uses LangGraph StateGraph for stateful conversations
  └── Receives all cross-domain traffic

TIER 1: MASTER AGENTS
  └── MasterHypothesisEngine - Cross-domain hypothesis coordination
  └── MasterScout - Digital Twin aggregation
  └── Subscribe to SwarmBus with tier=MASTER

TIER 2: DOMAIN AGENTS
  └── Genesis - Profiling & onboarding
  └── Vision - Image analysis
  └── Finance - Financial tracking
  └── Health - Health monitoring

TIER 3: SUB AGENTS
  └── genesis.profiler - Pattern detection
  └── genesis.hypothesis - Confidence probing
  └── genesis.face - Voice & personality
```

### SwarmBus Communication Patterns

```python
# 1. DIRECT: Point-to-point
await bus.send(
    source_agent_id="genesis.profiler",
    target_agent_id="genesis.hypothesis",
    payload={"signal": detected_pattern},
)

# 2. ESCALATION: Child → Parent
await bus.escalate(
    source_agent_id="genesis.hypothesis",
    payload={"need_help": "complex_pattern"},
    priority=PacketPriority.HIGH,
)

# 3. DELEGATION: Parent → Child
await bus.delegate(
    source_agent_id="master.hypothesis",
    target_capability="profiling",
    payload={"task": "probe_user"},
)

# 4. BROADCAST: One → Many
await bus.broadcast(
    source_agent_id="orchestrator",
    target_domain="genesis",
    payload={"command": "refresh_state"},
)

# 5. COLLECT: Aggregate from multiple
await bus.send(
    source_agent_id="orchestrator",
    target_tier=AgentTier.DOMAIN,
    routing_pattern=RoutingPattern.COLLECT,
    payload={"request": "status"},
    expects_response=True,
)
```

### Adding New Agents (Easy Extensibility)

Adding a new agent is simple:

```python
# 1. Create your agent class
class MyNewAgent:
    async def handle_message(self, envelope: SwarmEnvelope) -> Optional[Dict]:
        # Process the message
        return {"result": "processed"}

# 2. Subscribe to the SwarmBus
bus = await get_bus()
await bus.subscribe(
    agent_id="mydomain.myagent",
    handler=my_agent.handle_message,
    agent_tier=AgentTier.SUB,
    domain="mydomain",
    capability="my_capability",
)

# 3. That's it! The agent is now discoverable and routable
```

The system automatically:
- Indexes by domain, capability, and tier
- Routes messages based on targeting criteria
- Handles priority queuing
- Tracks message lifecycle
- Provides dead letter handling

### Universal Protocol (SovereignPacket)

All agents communicate via a standardized packet format (`apps/api/src/shared/protocol.py`):

```python
@dataclass
class SovereignPacket:
    packet_id: str           # Unique identifier
    source_agent: str        # e.g., "genesis.profiler"
    target_layer: TargetLayer # Orchestrator, Genesis, Vision, Logic, UI, User
    insight_type: InsightType # Pattern, Fact, Suggestion, Question, Hypothesis, etc.
    confidence_score: float  # 0.0 - 1.0
    payload: dict            # The actual data
    hrm_validated: bool      # Whether deep reasoning has vetted this
    voice_config: VoiceConfig # Voice & Expression configuration (NEW)
    session_id: str          # For multi-turn conversations
    timestamp: datetime
```

**VoiceConfig** (Adaptive Intelligence for Face output):
- `voice_id`: Which voice persona (oracle, sage, companion, challenger, mirror)
- `intensity`: Voice intensity (0.0-1.0)
- `warmth`: Emotional warmth (0.0-1.0)
- `mystery`: Cryptic vs plain speaking (0.0-1.0)
- `expression`: UI hints (pulse_color, mood, intensity, pulse_speed)

**Auto-mapping InsightType → Voice**:
- `Pattern` → Oracle (mysterious, purple pulse)
- `Fact` → Sage (calm, blue pulse)
- `Question` → Oracle (curious, cyan pulse)
- `Hypothesis` → Sage (thoughtful, gold pulse)
- `Synthesis` → Oracle (profound, red pulse)
- `Alert` → Challenger (urgent, fast red pulse)
- `Suggestion` → Companion (encouraging, green pulse)

**InsightTypes** (determine routing behavior):
- `Pattern`: Detected behavioral/psychological pattern → Hypothesis Engine
- `Fact`: Verified data point → Store directly
- `Question`: Probe for more info → UI component generation
- `Hypothesis`: Unverified suspicion → Needs probing
- `Synthesis`: Combined insight → High-value storage

**TargetLayers** (fractal hierarchy):
- `Orchestrator`: Master coordinator
- `Genesis`: Profiling layer
- `Vision`: Image analysis
- `Logic`: HRM deep reasoning
- `Memory`: Long-term storage
- `UI`: Frontend rendering

### Genesis Fractal Structure

The Genesis agent has its own internal fractal structure (`apps/api/src/agents/genesis/`):

```
genesis/
├── __init__.py          # Exports all components
├── core.py              # The "Face" - Conversational interface (Oracle persona)
├── profiler.py          # The "Scout" - Silent pattern detection
├── hypothesis.py        # The "Logic" - Confidence-based probing
├── state.py             # The "Memory" - ProfileRubric & session state
└── graph.py             # The "Wiring" - LangGraph orchestration
```

**GenesisCore** (The Face):
- Implements the "Oracle" persona
- Manages 5-phase profiling flow
- Generates conversational responses with Generative UI
- Coordinates Profiler and Hypothesis Engine

**GenesisProfiler** (The Scout):
- Runs silently on every user message
- Uses regex + LLM for pattern detection
- Emits `Signal` objects to Hypothesis Engine
- Tracks HD Type, Jungian functions, energy patterns

**HypothesisEngine** (The Logic):
- Maintains list of suspected traits with confidence scores
- Generates probing questions when confidence < 0.80
- Supports multiple probe types: Binary Choice, Slider, Confirmation, Reflection
- Resolves hypotheses when confidence >= 0.80 or max probes reached

**ProfileRubric** (The Memory):
- Structured container for Digital Twin data
- Tracks all trait detections with confidence
- Organized by framework: HD, Jungian, Somatic, Core Patterns
- Calculates completion percentage

### Orchestrator (Central Router)

The Orchestrator (`apps/api/src/core/orchestrator.py`) routes all traffic:

```python
class SovereignOrchestrator:
    """Central brain using LangGraph StateGraph."""
    
    # Routing nodes:
    # - route_request: Intent classification
    # - call_genesis: Profile-related queries
    # - call_logic_engine: Deep reasoning requests
    # - synthesize: Combine multi-agent outputs
```

### Shared Schema Contract

Frontend (`lib/agents/base-agent.ts`) and Backend (`apps/api/src/core/schemas.py`) share identical schemas:

```typescript
// AgentInput
{
  framework: string,
  context: {
    birthData?: { date, time, location: { latitude, longitude } },
    healthMetrics?: Record<string, any>,
    journalThemes?: string[],
    userQuery?: string
  }
}

// AgentOutput
{
  calculation?: any,
  correlations?: string[],
  interpretationSeed: string,
  visualizationData?: any,
  method: string,
  confidence?: number (0-1)
}
```

### HRM (Hierarchical Reasoning Model)

Toggleable deep reasoning layer with full frontend configuration:

**Backend Configuration** (`apps/api/src/core/config.py`):
- `ENABLE_HRM_LOGIC`: Master toggle for HRM processing
- `DEFAULT_THINKING_LEVEL`: "low" (fast) or "high" (deep reasoning)
- `H_CYCLES` / `L_CYCLES`: Processing cycles per level
- `MAX_REASONING_DEPTH`: Maximum tree depth
- `HALT_THRESHOLD`: Early stopping threshold
- `CANDIDATE_COUNT`: Candidates per beam expansion
- `BEAM_SIZE`: Beam search width
- `SCORE_THRESHOLD`: Minimum candidate score

**Frontend Configuration** (`app/settings/hrm.tsx` + `lib/state/hrm-atoms.ts`):
- Full UI for all HRM parameters
- AsyncStorage persistence with `@sovereign/hrm_config` key
- Automatic camelCase → snake_case transformation for API
- Syncs with backend on every chat request

**Process**: Expand → Score → Synthesize with beam search

### Global Overlay System

App-wide overlay system for generative UI (`lib/state/global-ui-atoms.ts` + `components/GlobalOverlayProvider.tsx`):
- Priority-based queue (higher priority shows first)
- Types: `game`, `notification`, `insight`, `challenge`, `custom`
- Auto-close support for timed notifications
- Handles game completion with result persistence

### Plugin Architecture

Agents in `apps/api/src/agents/` are auto-discovered:
- Drop a folder with `manifest.json` + `workflow.py`
- System automatically registers and exposes the agent

## Environment Variables

Required (add as Replit Secrets):
- `EXPO_PUBLIC_GOOGLE_API_KEY` or `GOOGLE_API_KEY`: Google Gemini API key

Optional:
- `OPENROUTER_API_KEY`: OpenRouter API key (for Grok 4.1 Fast and other models)
- `EXPO_PUBLIC_SUPABASE_URL`: Supabase project URL
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key
- `LANGCHAIN_API_KEY`: LangSmith for agent debugging
- `LANGCHAIN_TRACING_V2`: Set to `true` for tracing

## API Endpoints

All endpoints prefixed with `/api/python`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with model info |
| `/agents/` | GET | List all registered agents |
| `/agents/{name}` | GET | Get agent manifest |
| `/agents/{name}/execute` | POST | Execute agent with AgentInput |
| `/chat/` | POST | Chat with Genesis Profiler |
| `/chat/stream` | POST | SSE streaming chat with HRM config |
| `/chat/sessions/{session_id}` | GET | Get session info |
| `/chat/sessions/{session_id}` | DELETE | Clear session state |
| `/sovereign/chat` | POST | Sovereign Agent synchronous chat |
| `/sovereign/chat/stream` | POST | Sovereign Agent SSE streaming |
| `/sovereign/tools` | GET | List Sovereign Agent tools |
| `/sovereign/agents` | GET | List connected agents |
| `/sovereign/capabilities` | GET | Full capability report |

### ChatRequest Schema
```python
{
    "message": str,              # User message (required)
    "session_id": str | None,    # Optional session ID
    "enable_hrm": bool = True,   # Enable HRM reasoning
    "models_config": {           # Optional model overrides
        "primary_model": str,
        "fast_model": str,
        "synthesis_model": str,
        "fallback_model": str,
        "auto_fallback": bool
    },
    "context": AgentContext      # Optional agent context
}
```

---

## Digital Twin Domain System

### Overview

The Digital Twin is the **Single Source of Truth** for all user identity data. It implements a fractal, infinitely extensible domain system where each domain encapsulates a specific aspect of the user's identity.

### Domain Architecture

```
digital_twin/
├── domains/                    # All identity domains
│   ├── __init__.py            # Exports all domains + DomainRegistry
│   ├── base.py                # BaseDomain ABC (all domains inherit)
│   ├── registry.py            # DomainRegistry for dynamic discovery
│   ├── genesis.py             # Core profiling domain (14 traits)
│   ├── health.py              # Health & biometrics (6 traits)
│   ├── nutrition/             # FRACTAL EXAMPLE - Folder structure
│   │   ├── __init__.py        # Exports NutritionDomain + all sub-modules
│   │   ├── domain.py          # NutritionDomain class
│   │   ├── schema.py          # Nutrition-specific data types
│   │   ├── tracker/           # Meal tracking
│   │   ├── analysis/          # Nutritional analysis
│   │   ├── preferences/       # Dietary preferences
│   │   └── patterns/          # Eating patterns
│   ├── journaling/            # Journaling domain (folder)
│   │   ├── __init__.py
│   │   ├── domain.py          # JournalingDomain class
│   │   ├── schema.py          # Entry types, moods, emotions
│   │   ├── tracker/           # Entry tracking
│   │   ├── analysis/          # Emotion analysis
│   │   ├── prompts/           # Prompt generation
│   │   └── patterns/          # Journaling patterns
│   └── finance/               # Finance domain (folder)
│       ├── __init__.py
│       ├── domain.py          # FinanceDomain class
│       ├── schema.py          # Transactions, categories
│       ├── tracker/           # Transaction tracking
│       ├── budget/            # Budget management
│       ├── goals/             # Financial goals
│       └── patterns/          # Spending patterns
├── traits/                    # Trait system
│   ├── categories.py          # TraitCategory + TraitFramework enums
│   └── schema.py              # TraitSchema dataclass
├── access/                    # Unified accessor
├── events/                    # Event bus for real-time sync
└── identity/                  # Identity store
```

### Domain Types

```python
class DomainType(str, Enum):
    CORE = "core"         # Required domains (Genesis, Health, Journaling)
    SUB = "sub"           # Child domains (Nutrition under Health)
    OPTIONAL = "optional" # User-enabled domains (Finance)
```

### Creating a New Domain

#### 1. Simple Domain (Single File)

```python
# domains/my_domain.py
from .base import BaseDomain, DomainType, DomainCapability
from .registry import DomainSchema
from ..traits.categories import TraitCategory, TraitFramework
from ..traits.schema import TraitSchema

class MyDomain(BaseDomain):
    domain_id = "my_domain"
    display_name = "My Domain"
    description = "Description of what this domain tracks"
    version = "1.0.0"
    domain_type = DomainType.OPTIONAL
    capabilities = {DomainCapability.TRACK, DomainCapability.ANALYZE}
    
    def get_schema(self) -> DomainSchema:
        schema = DomainSchema(domain_id=self.domain_id)
        
        schema.add_trait(TraitSchema(
            name="my_trait",
            display_name="My Trait",
            description="What this trait represents",
            value_type="string",
            category=TraitCategory.BEHAVIOR,
            frameworks=[TraitFramework.BEHAVIORAL_PATTERNS],
            priority=50,
            icon="🎯",
        ))
        
        return schema
```

#### 2. Complex Domain (Folder Structure)

Follow the Nutrition domain as reference:

```
my_domain/
├── __init__.py       # Export domain + all sub-modules
├── domain.py         # MyDomain class with get_schema()
├── schema.py         # Domain-specific dataclasses/enums
├── tracker/          # Tracking functionality
│   └── __init__.py   # MyTracker, MyHistory classes
├── analysis/         # Analysis functionality  
│   └── __init__.py   # MyAnalyzer classes
└── patterns/         # Pattern detection
    └── __init__.py   # PatternDetector, InsightGenerator
```

### TraitSchema Parameters

```python
@dataclass
class TraitSchema:
    # Required
    name: str                    # Unique identifier (e.g., "hd_type")
    display_name: str            # Human-readable name
    description: str             # What this trait represents
    
    # Type
    value_type: str = "string"   # string, int, float, bool, enum, list, scale
    enum_options: List[str] = None  # For enum types
    scale_min: float = None      # For scale types
    scale_max: float = None
    
    # Classification
    category: TraitCategory = TraitCategory.DETECTED
    frameworks: List[TraitFramework] = field(default_factory=list)
    
    # Metadata
    priority: int = 50           # 0-100, higher = more important
    is_required: bool = False
    is_sensitive: bool = False
    icon: str = None
```

### Valid TraitCategories

```python
class TraitCategory(str, Enum):
    # Core Identity
    PERSONALITY = "personality"
    ARCHETYPE = "archetype"
    
    # Cognitive
    COGNITION = "cognition"
    EMOTION = "emotion"
    SHADOW = "shadow"
    
    # Behavioral
    BEHAVIOR = "behavior"
    HABIT = "habit"
    TENDENCY = "tendency"
    
    # Energy & Rhythm
    ENERGY = "energy"
    RHYTHM = "rhythm"
    
    # Values & Goals
    PREFERENCE = "preference"
    STYLE = "style"
    GOAL = "goal"
    VALUE = "value"
    
    # Wounds & Gifts
    WOUND = "wound"
    GIFT = "gift"
    
    # Health & Body
    HEALTH = "health"
    SOMATIC = "somatic"
    
    # Meta
    DEMOGRAPHIC = "demographic"
    CONTEXT = "context"
    CALCULATED = "calculated"
    DETECTED = "detected"
    STATED = "stated"
```

### Valid TraitFrameworks

```python
class TraitFramework(str, Enum):
    # Primary Frameworks
    HUMAN_DESIGN = "human_design"
    JUNGIAN = "jungian"
    GENE_KEYS = "gene_keys"
    MBTI = "mbti"
    ENNEAGRAM = "enneagram"
    
    # Astrological
    ASTROLOGY = "astrology"
    VEDIC = "vedic_astrology"
    NUMEROLOGY = "numerology"
    
    # Somatic/Body
    SOMATIC = "somatic"
    SOMATIC_AWARENESS = "somatic_awareness"
    AYURVEDA = "ayurveda"
    
    # Modern Psychology
    BIG_FIVE = "big_five"
    ATTACHMENT = "attachment_theory"
    
    # Health
    HEALTH_METRICS = "health_metrics"
    BIOMETRICS = "biometrics"
    
    # Patterns
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    CORE_PATTERNS = "core_patterns"
    
    # Custom
    SOVEREIGN = "sovereign"
    GENERAL = "general"
```

### Current Domains (5 Total)

| Domain | Type | Traits | Description |
|--------|------|--------|-------------|
| `genesis` | CORE | 14 | Core profiling (HD, Jungian, core patterns) |
| `health` | CORE | 6 | Health metrics & biometrics |
| `nutrition` | SUB | 11 | Nutrition tracking & analysis |
| `journaling` | CORE | 11 | Journal entries & emotion analysis |
| `finance` | OPTIONAL | 12 | Financial tracking & patterns |

### Accessing the Digital Twin

```python
from src.digital_twin import get_domain_registry
from src.digital_twin.domains import GenesisDomain, NutritionDomain

# Get registry instance
registry = get_domain_registry()()

# List all domains
domains = registry.list_domains()  # ['genesis', 'health', 'nutrition', ...]

# Get specific domain
genesis = registry.get_domain('genesis')
schema = genesis.get_schema()

# Iterate traits
for trait_name, trait in schema.traits.items():
    print(f"{trait.display_name}: {trait.description}")
```

---

## Project Structure

```
project-sovereign/
├── app/                          # Expo Router pages
│   ├── (tabs)/                   # Tab navigation
│   │   └── index.tsx             # Home screen with Mini-Games Lab
│   ├── genesis/                  # Genesis Profiler screens
│   │   └── index.tsx             # Main profiling flow with session persistence
│   ├── settings/                 # Settings screens
│   │   ├── index.tsx             # Main settings
│   │   ├── hrm.tsx               # HRM configuration UI
│   │   └── models.tsx            # Model configuration UI
│   └── _layout.tsx               # Root layout with GlobalOverlayProvider
├── apps/
│   └── api/                      # FastAPI Backend
│       ├── main.py               # App entry point
│       ├── requirements.txt      # Python dependencies
│       └── src/
│           ├── shared/           # Shared modules
│           │   ├── __init__.py
│           │   └── protocol.py   # SovereignPacket + Hybrid Architecture docs
│           ├── agents/           # Agent implementations
│           │   ├── base.py       # BaseAgent class
│           │   ├── registry.py   # Plugin registry with auto-discovery
│           │   ├── genesis_profiler.py  # Genesis with Face/Voice
│           │   ├── master_hypothesis_engine.py  # Cross-domain hypothesis coordination
│           │   ├── master_scout.py      # Digital Twin aggregation
│           │   ├── sovereign/    # Sovereign Agent (Main App Agent)
│           │   │   ├── __init__.py   # Exports SovereignAgent
│           │   │   ├── agent.py      # Main class with chat, chat_stream
│           │   │   ├── cortex.py     # LLM thinking core
│           │   │   ├── memory.py     # Session memory & conversation history
│           │   │   ├── tools.py      # 6 tools with 10 UI component types
│           │   │   ├── router.py     # Intent routing to sub-agents
│           │   │   └── integrations.py # 6 deep system integrations
│           │   └── genesis/      # Genesis Fractal Structure
│           │       ├── __init__.py
│           │       ├── core.py       # The "Face" - Oracle persona
│           │       ├── profiler.py   # The "Scout" - Pattern detection
│           │       ├── hypothesis.py # The "Logic" - Confidence probing
│           │       ├── state.py      # The "Memory" - ProfileRubric
│           │       ├── graph.py      # The "Wiring" - LangGraph
│           │       └── face/         # Extensible Face Layer
│           │           ├── __init__.py   # FaceOrchestrator, FaceFactory
│           │           └── voice/        # Voice personality system
│           │               ├── __init__.py   # Voice ABC, VoiceRegistry, VoiceSelector
│           │               └── voices.py     # Oracle, Sage, Companion, Challenger, Mirror
│           ├── core/             # Core modules
│           │   ├── config.py     # Settings & models (HRM config)
│           │   ├── schemas.py    # Pydantic models
│           │   ├── hrm.py        # Reasoning engine
│           │   ├── llm_factory.py # Multi-provider LLM factory (Google, OpenRouter)
│           │   ├── orchestrator.py # Central Orchestrator (LangGraph brain)
│           │   ├── swarm_bus.py  # Parallel async message bus
│           │   └── translator.py # Protocol translator
│           ├── digital_twin/     # Digital Twin Domain System
│           │   ├── __init__.py   # Main exports & convenience functions
│           │   ├── core.py       # DigitalTwinCore class
│           │   ├── domains/      # Fractal domain system
│           │   │   ├── __init__.py      # Domain exports & registry
│           │   │   ├── base.py          # BaseDomain ABC
│           │   │   ├── registry.py      # DomainRegistry, DomainSchema
│           │   │   ├── genesis.py       # Core profiling (14 traits)
│           │   │   ├── health.py        # Health domain (6 traits)
│           │   │   ├── nutrition/       # Fractal folder domain (11 traits)
│           │   │   ├── journaling/      # Fractal folder domain (11 traits)
│           │   │   └── finance/         # Fractal folder domain (12 traits)
│           │   ├── traits/       # Trait definitions
│           │   │   ├── categories.py    # TraitCategory, TraitFramework enums
│           │   │   └── schema.py        # TraitSchema dataclass
│           │   ├── access/       # Unified accessor
│           │   ├── events/       # Event bus for real-time sync
│           │   ├── identity/     # Identity store
│           │   └── integrations/ # Sovereign integration
│           └── routers/          # API routes
│               ├── health.py
│               ├── agents.py
│               ├── chat.py
│               └── sovereign.py  # Sovereign Agent endpoints
├── components/                   # React components
│   ├── GlobalOverlayProvider.tsx # App-wide overlay system
│   ├── GlobalAgentShell.tsx      # Floating Sovereign Agent UI overlay
│   └── genesis/                  # Genesis-specific components
│       ├── GenerativeRenderer.tsx # Maps JSON → Tamagui components
│       ├── PulsingBorder.tsx     # Animated edge glow
│       └── ReflexTapComponent.tsx # Reflex game with animations
├── lib/
│   ├── agents/                   # Frontend agent classes
│   │   ├── base-agent.ts         # SOURCE OF TRUTH for schemas
│   │   ├── sovereign-protocol.ts # TypeScript mirror of protocol.py
│   │   └── human-design-agent.ts
│   ├── ai/
│   │   └── client.ts             # AI SDK configuration
│   ├── api-client.ts             # Backend API client with SSE
│   ├── constants.ts              # Model config
│   ├── games/                    # Micro-games system
│   │   ├── types.ts              # GameDefinition, GameResult interfaces
│   │   ├── storage.ts            # AsyncStorage persistence for results
│   │   └── scheduler.ts          # Game triggering during profiling
│   ├── state/                    # Jotai atoms
│   │   ├── atoms.ts              # Core app state
│   │   ├── genesis-atoms.ts      # Genesis AI states
│   │   ├── global-ui-atoms.ts    # Overlay queue management
│   │   ├── hrm-atoms.ts          # HRM configuration state
│   │   ├── model-atom.ts         # Selected AI model (legacy)
│   │   └── model-config-atoms.ts # Multi-model configuration (PRIMARY, FAST, SYNTHESIS, FALLBACK)
│   ├── storage/                  # Storage utilities
│   │   └── model-storage.ts      # Model persistence
│   ├── supabase/                 # Database & embeddings
│   └── utils/                    # Utility functions
│       └── error-logger.ts       # Comprehensive error logging
├── packages/
│   └── ui/
│       └── registry/             # Component registry for generative UI
│           └── index.ts
├── package.json                  # Dependencies & scripts
└── replit.md                     # Environment documentation
```

## Key Agents

### Master Agents (Tier 1)
- **MasterHypothesisEngine** (`master_hypothesis_engine.py`)
  - Aggregates hypotheses from ALL domains
  - Correlates cross-domain patterns (e.g., health affecting finance)
  - Resolves conflicts between domains
  - Escalates uncertain cases to Orchestrator
  
- **MasterScout** (`master_scout.py`)
  - Builds unified Digital Twin from all domain insights
  - Detects macro-patterns spanning multiple domains
  - Maintains profile coherence
  - Tracks user evolution over time

### Genesis Profiler (Backend - Fractal Structure)
- Deep profiling agent for building Digital Twin
- 5 phases: awakening → excavation → mapping → synthesis → activation
- Returns generative UI components dynamically
- Supports HRM for deep reasoning
- Fractal architecture with Core, Profiler, Hypothesis Engine, and State modules
- **Voice System**: Oracle, Sage, Companion, Challenger, Mirror personas

### Human Design Calculator (Frontend)
- Calculates HD chart from birth data
- Determines Type, Strategy, Authority, Profile
- Maps centers, gates, channels
- AI-driven interpretation

## How to Use

### Starting Development

```bash
yarn start  # Launches BOTH Expo and FastAPI
```

- **Expo** (Frontend): Port 5000 - Web preview in Replit
- **FastAPI** (Backend): Port 8000 - API server

### Individual Servers

```bash
yarn start:expo  # Expo only
yarn start:api   # FastAPI only
yarn start:dev   # Dev mode with hot reload
```

### Testing API

```bash
# Health check
curl http://localhost:8000/api/python/health

# List agents
curl http://localhost:8000/api/python/agents/

# Execute Genesis Profiler
curl -X POST http://localhost:8000/api/python/agents/genesis_profiler/execute \
  -H "Content-Type: application/json" \
  -d '{"framework": "genesis", "context": {"userQuery": "Tell me about myself"}}'
```

## Development Workflow

1. Make code changes
2. Both servers auto-reload on changes
3. Test API endpoints directly or through frontend
4. For mobile: Scan QR code with Expo Go

## User Preferences

- Primary focus: iOS mobile app with Python backend
- Development environment: Replit
- Access method: Expo Go for mobile, web preview for testing
- AI Models: Latest Gemini 3 Pro Preview when available

## Next Steps

- [x] Add EXPO_PUBLIC_GOOGLE_API_KEY secret
- [x] Test Genesis Profiler flow
- [x] Wire in Sovereign Agent (omniscient main app agent)
- [ ] Implement additional wisdom framework agents
- [ ] Add vision module for image analysis
- [ ] Configure Supabase for persistence