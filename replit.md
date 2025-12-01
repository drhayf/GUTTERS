# Project Sovereign - AI-Native Self-Mastery Platform

## Project Overview

**Project Sovereign** (also known as "The Collapse OS") is an AI-native mobile + web application for self-mastery and personal transformation. It builds a "Digital Twin" profile system that deeply understands the user through multiple wisdom frameworks.

Built with Expo + Tamagui + Vercel AI SDK + LangChain.js (frontend) and FastAPI + LangGraph (backend) for dynamic, generative experiences.

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
- **UI**: Tamagui 1.136 (purple/cyan theme)
- **Routing**: Expo Router 6.0
- **State**: Jotai 2.15
- **AI Core**: Vercel AI SDK 5.0
- **AI Models**: Google Gemini 2.5/3.0 (via @ai-sdk/google)
- **Agents** (Native Only): LangChain.js 1.0

### Backend (NEW)
- **Framework**: FastAPI 0.122
- **AI/ML**: LangChain 0.3, LangGraph 1.0, LangChain-Google-GenAI 2.0
- **Streaming**: SSE-Starlette for real-time responses
- **Models**: Gemini 3 Pro Preview, Gemini 2.5 Pro/Flash

### Shared
- **Database**: Supabase 2.80 (with pgvector for RAG)
- **Storage**: react-native-mmkv 4.0

## Architecture

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

### Universal Protocol

All agents communicate using this structure:
```json
{
  "source_agent": "AgentName",
  "target_layer": "Orchestrator",
  "insight_type": "Pattern | Fact | Suggestion",
  "confidence_score": 0.0-1.0,
  "payload": { ... },
  "hrm_validated": boolean
}
```

### HRM (Hierarchical Reasoning Model)

Toggleable deep reasoning layer:
- **Enable/Disable**: Via `ENABLE_HRM_LOGIC` in config
- **Thinking Levels**: "low" (fast) or "high" (deep reasoning)
- **Process**: Expand → Score → Synthesize with beam search

### Plugin Architecture

Agents in `apps/api/src/agents/` are auto-discovered:
- Drop a folder with `manifest.json` + `workflow.py`
- System automatically registers and exposes the agent

## Environment Variables

Required (add as Replit Secrets):
- `EXPO_PUBLIC_GOOGLE_API_KEY` or `GOOGLE_API_KEY`: Google Gemini API key

Optional:
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
| `/chat/stream` | POST | SSE streaming chat |

## Project Structure

```
project-sovereign/
├── app/                          # Expo Router pages
│   ├── (tabs)/                   # Tab navigation
│   └── _layout.tsx               # Root layout
├── apps/
│   └── api/                      # FastAPI Backend
│       ├── main.py               # App entry point
│       ├── requirements.txt      # Python dependencies
│       └── src/
│           ├── agents/           # Agent implementations
│           │   ├── base.py       # BaseAgent class
│           │   ├── registry.py   # Plugin registry
│           │   └── genesis_profiler.py
│           ├── core/             # Core modules
│           │   ├── config.py     # Settings & models
│           │   ├── schemas.py    # Pydantic models
│           │   ├── hrm.py        # Reasoning engine
│           │   └── translator.py # Protocol translator
│           └── routers/          # API routes
│               ├── health.py
│               ├── agents.py
│               └── chat.py
├── components/                   # React components
├── lib/
│   ├── agents/                   # Frontend agent classes
│   │   ├── base-agent.ts         # SOURCE OF TRUTH for schemas
│   │   └── human-design-agent.ts
│   ├── ai/
│   │   └── client.ts             # AI SDK configuration
│   ├── api-client.ts             # Backend API client (NEW)
│   ├── constants.ts              # Model config (NEW)
│   ├── state/                    # Jotai atoms
│   └── supabase/                 # Database & embeddings
├── package.json                  # Dependencies & scripts
└── replit.md                     # This file
```

## Key Agents

### Genesis Profiler (Backend)
- Deep profiling agent for building Digital Twin
- 5 phases: awakening → excavation → mapping → synthesis → activation
- Returns generative UI components dynamically
- Supports HRM for deep reasoning

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

- [ ] Add EXPO_PUBLIC_GOOGLE_API_KEY secret
- [ ] Test Genesis Profiler flow
- [ ] Implement additional wisdom framework agents
- [ ] Add vision module for image analysis
- [ ] Configure Supabase for persistence
