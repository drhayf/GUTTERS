# Somatic Alignment

**AI-Native iOS App for Self-Mastery**

A personal tool blending metaphysical frameworks (Human Design, Jungian psychology, astrology, Gene Keys, I Ching, chakras, and 15+ more) with somatic intelligence and AI-driven insights. Built with **Expo + Tamagui + Vercel AI SDK + LangChain.js** for dynamic, generative experiences tailored to your biomechanics, energy, and psychology.

---

## 🎯 Core Vision

Somatic Alignment is an **AI-native living system** where intelligent agents replace static databases. Instead of hard-coded interpretations, the app uses:

- **Calculator agents** for precise computations (Human Design charts, astrology transits, numerology)
- **Interpreter agents** for personalized, context-aware insights
- **Synthesizer agents** that weave 20+ frameworks into unified attunements
- **Oracle agents** generating daily guidance from your birth data, health metrics, and journal patterns

The result: A sovereignty-focused tool that adapts to you, without external hardware dependencies.

---

## ✨ Features

### 🧬 Birth Data & Chart Generation
- Secure input with geocoding and timezone validation
- On-demand Human Design bodygraphs (gates, centers, type, strategy, authority)
- Astrology charts with real-time transits
- Numerology paths, I Ching hexagrams, Gene Keys shadow-to-siddhi mappings

### 🧠 Psychometric Assessments
- Conversational AI for MBTI/OEJTS, Enneagram (wings/instincts), Jungian archetypes
- Dynamic mapping of cognitive functions to frameworks (e.g., Ti/Fe → Hero/Sage archetypes)

### 🫀 Somatic & Health Integration
- Apple HealthKit integration (HRV, walking asymmetry, steps)
- Correlations with polyvagal theory, Reichian armoring, chakra states
- Real-time somatic prompts (breathwork, grounding practices)

### 🔮 Metaphysical Frameworks (20+)
Human Design • Astrology • I Ching • Gene Keys • Tarot • Numerology • Kabbalah • Chakras • Ayurveda • Chinese Medicine • Biorhythms • Sacred Geometry • Hero's Journey • Enneagram • Stoicism • Hermetic Principles

### 🌑 Shadow Work & Power Dynamics
- Machiavellian awareness (48 Laws), game theory, rhetoric (ethos/pathos/logos)
- Trauma-informed shadow integration balanced with light aspects

### 📔 Journaling & Pattern Recognition
- Sovereign logs with semantic search (Supabase pgvector + HuggingFace embeddings)
- AI-summarized recurring themes (e.g., "Stress correlates with Kapha imbalance + dorsal vagal states")

### 🌅 Daily Attunements & Oracle
- Morning/evening syntheses blending transits, biorhythms, and your data
- Generative practices (e.g., "Heart-Belly Breath" timed to biological rhythms)

### 💬 Generative AI Chat
- Central hub powered by **Vercel AI SDK** with streaming responses
- Dynamic UI rendering (interactive mandalas, practice timers, visual charts)
- RAG-powered queries (e.g., "Synthesize my Gate 26 with current Mars transit")

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | Expo SDK 54 + React Native 0.82 | iOS-native with hot reload |
| **UI** | Tamagui 1.136 | Performance-optimized components with theme system |
| **Routing** | Expo Router 6.0 | File-based navigation |
| **State** | Jotai 2.15 | Atomic state management |
| **AI Core** | Vercel AI SDK 5.0 | Generative UI + streaming responses |
| **AI Models** | Google Gemini via @ai-sdk/google | Flash/Pro/Lite variants (Gemini 2.5) |
| **Agents** | LangChain.js 1.0 | Multi-agent orchestration + chaining |
| **Database** | Supabase 2.80 | PostgreSQL with pgvector for RAG |
| **Embeddings** | HuggingFace (BAAI/bge-small-en-v1.5) | Semantic search for journals/frameworks |
| **Validation** | Zod 4.1 | Schema validation for agent I/O |
| **Storage** | react-native-mmkv 4.0 | Encrypted local storage |

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** 22+ (dev container runs Ubuntu 24.04)
- **Expo account** (login via `npx expo login`)
- **API Keys**:
  - Google AI Studio (Gemini): `EXPO_PUBLIC_GOOGLE_API_KEY`
  - HuggingFace: `EXPO_PUBLIC_HF_API_KEY`
  - Supabase: `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY`

### Installation

```bash
# Clone repo
git clone https://github.com/drisfet/soma2.git
cd soma2

# Install dependencies (Yarn 4.5.0)
yarn install

# Set up environment variables
cp .env.example .env
# Add your API keys to .env
```

### Configuration

The `.env` file should contain:
```bash
EXPO_PUBLIC_GOOGLE_API_KEY=your_google_ai_key
EXPO_PUBLIC_HF_API_KEY=your_huggingface_key
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EXPO_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Run the App

```bash
# Start Expo dev server with tunnel (for Codespaces/remote)
yarn start --tunnel

# Or locally
yarn start

# iOS Simulator
yarn ios

# Web (for quick testing)
yarn web
```

The tunnel command installs `@expo/ngrok` globally and generates a public URL for mobile testing in environments like GitHub Codespaces.

---

## 🧩 Architecture

### AI-Native Agent System

The app uses a **modular agent architecture** where each agent extends a `BaseAgent` class with standardized JSON schemas:

```typescript
// Input Schema
{
  framework: string,
  context: {
    birthData?: { date, time, location },
    healthMetrics?: { hrv, steps, asymmetry },
    journalThemes?: string[]
  }
}

// Output Schema
{
  calculation: any,          // Raw computed data
  correlations: string[],    // Cross-framework mappings
  interpretationSeed: string // Context for AI synthesis
}
```

**Agent Types:**
- **Calculators** (`/lib/agents/human-design-agent.ts`): Compute charts, gates, planetary positions
- **Interpreters**: Generate personalized insights from calculations
- **Synthesizers**: Weave multi-framework outputs into unified attunements
- **Translators**: Convert between formats (e.g., HD gates → chakras)

### Example: Human Design Agent

```typescript
import { BaseAgent } from './base-agent'

class HumanDesignAgent extends BaseAgent {
  async execute(input) {
    // 1. Calculate planetary positions
    const positions = this.calculatePlanetaryPositions(input.birthData)
    
    // 2. Map longitude to gates
    const gates = positions.map(p => this.longitudeToGate(p.longitude))
    
    // 3. Determine centers, type, strategy
    const chart = this.determineType(gates)
    
    // 4. Return structured output
    return {
      calculation: chart,
      correlations: [`Gate ${chart.sunGate} → Hexagram ${chart.sunGate}`],
      interpretationSeed: this.generateInterpretationPrompt(chart, input)
    }
  }
}
```

### RAG Integration

Journal entries and framework knowledge are embedded using **HuggingFace** and stored in **Supabase pgvector**:

```typescript
// lib/supabase/embeddings.ts
export async function storeJournalEntry(text: string, userId: string) {
  const embedding = await generateEmbedding(text) // HuggingFace API
  await supabase.from('journal_entries').insert({
    user_id: userId,
    content: text,
    embedding: embedding // 384-dim vector
  })
}

export async function searchJournalEntries(query: string) {
  const queryEmbedding = await generateEmbedding(query)
  const { data } = await supabase.rpc('match_journal_entries', {
    query_embedding: queryEmbedding,
    match_threshold: 0.7,
    match_count: 5
  })
  return data
}
```

### Generative AI Chat

The chat interface uses **Vercel AI SDK's `generateText()`** for streaming responses:

```typescript
// components/ChatInterface.tsx
import { generateText } from 'ai'
import { chatModel } from '@/lib/ai/client'

const response = await generateText({
  model: chatModel, // gemini-2.5-flash
  prompt: agentResult.interpretationSeed,
  system: 'You are a compassionate guide for somatic awareness...'
})
```

**Available Models:**
- `chatModel`: gemini-2.5-flash (fast, 22 reasoning tokens avg)
- `synthesisModel`: gemini-2.5-pro (deep reasoning, 1307 reasoning tokens)
- `quickModel`: gemini-2.5-flash-lite (lightest/fastest)

---

## 📂 Project Structure

```
soma2/
├── app/                        # Expo Router pages
│   ├── (tabs)/                 # Tab navigation
│   │   ├── index.tsx           # Main chat screen
│   │   ├── two.tsx             # Secondary tab
│   │   └── _layout.tsx         # Tab layout
│   ├── modal.tsx               # Modal screen
│   └── _layout.tsx             # Root layout
├── components/
│   ├── ChatInterface.tsx       # AI chat with streaming
│   ├── CurrentToast.tsx        # Toast notifications
│   └── Provider.tsx            # Tamagui provider
├── lib/
│   ├── agents/                 # Agent classes
│   │   ├── base-agent.ts       # BaseAgent with schemas
│   │   └── human-design-agent.ts
│   ├── ai/
│   │   └── client.ts           # Gemini model configs
│   ├── supabase/
│   │   ├── client.ts           # Supabase connection
│   │   └── embeddings.ts       # RAG functions
│   └── state/
│       └── atoms.ts            # Jotai state atoms
├── test-ai-integration.ts      # AI SDK test script
├── package.json
├── tsconfig.json
└── .env                        # API keys (gitignored)
```

---

## 🧪 Testing AI Integration

Run the test script to verify Vercel AI SDK and LangChain:

```bash
yarn test:ai
```

**What it tests:**
- ✅ Gemini 2.5 Flash, Pro, and Lite models
- ✅ LangChain basic invocation
- ✅ System messages and multi-turn conversations
- ✅ Reasoning token counts (Gemini 2.5's internal "thinking")

**Expected output:**
```
=== Testing Vercel AI SDK ===
✓ Chat Model (gemini-2.5-flash): 156 tokens, 22 reasoning
✓ Synthesis Model (gemini-2.5-pro): 423 tokens, 1307 reasoning
✓ Quick Model (gemini-2.5-flash-lite): 89 tokens, 0 reasoning

=== Testing LangChain ===
✓ Basic Invocation: "Ahoy there, matey! 🏴‍☠️"
✓ Multi-turn Conversation: Context maintained
```

---

## 🔐 Privacy & Sovereignty

- **On-device first**: Birth data and journals stored locally via MMKV (encrypted)
- **Selective cloud**: Only anonymous embeddings sent to Supabase for RAG
- **No external hardware**: Uses Apple HealthKit for biometrics (HRV via camera PPG)
- **User control**: All data deletable; agents query locally when possible

---

## 🛠️ Development Workflow

### Adding New Agents

1. **Create agent file** in `/lib/agents/`:
```typescript
// lib/agents/numerology-agent.ts
import { BaseAgent, AgentInput, AgentOutput } from './base-agent'

export class NumerologyAgent extends BaseAgent {
  async execute(input: AgentInput): Promise<AgentOutput> {
    const lifePath = this.calculateLifePath(input.context.birthData)
    return {
      calculation: { lifePath, expression: '...' },
      correlations: [`Life Path ${lifePath} → HD Type correlation`],
      interpretationSeed: `Interpret Life Path ${lifePath}...`
    }
  }
}
```

2. **Import in chat interface**:
```typescript
// components/ChatInterface.tsx
import { NumerologyAgent } from '@/lib/agents/numerology-agent'

if (message.includes('numerology')) {
  const agent = new NumerologyAgent()
  const result = await agent.execute({ framework: 'numerology', context })
}
```

3. **Update Supabase schema** if needed (for embeddings)

### Updating Package Versions

```bash
# Update all packages to latest
yarn up expo expo-router react-native tamagui ai @ai-sdk/google langchain

# Check compatibility
yarn start --tunnel
```

**Current Versions (as of Nov 2025):**
- Expo SDK: 54.0.23
- React: 19.1.0 (matches react-native-renderer 19.1.1)
- React Native: 0.82.1 (may show 0.81.5 expected - forward compatible)
- Expo Router: 6.0.14
- Tamagui: 1.136.6

---

## 🐛 Troubleshooting

### React Version Mismatch
**Error:** `Incompatible React versions: react 19.2.0 vs react-native-renderer 19.1.1`

**Fix:**
```bash
yarn add react@19.1.0 react-dom@19.1.0
```

### Metro Bundler Cache Issues
```bash
yarn start --clear
```

### Splash Screen Errors (Expo Go)
These are warnings, not blockers:
```
ERROR: No native splash screen registered...
```
**Fix:** Ignore for Expo Go; resolved in production builds.

### Tunnel Connection Fails
```bash
# Reinstall ngrok
npm install --global @expo/ngrok@^4.1.0

# Restart with tunnel
yarn start --tunnel
```

---

## 📚 Key Resources

- [Vercel AI SDK Docs](https://sdk.vercel.ai/docs)
- [LangChain.js Docs](https://js.langchain.com/)
- [Expo Router Guide](https://docs.expo.dev/router/introduction/)
- [Tamagui Documentation](https://tamagui.dev/)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/ai/vector-columns)
- [Human Design Gate Reference](https://www.mybodygraph.com/)

---

## 🎨 Design Philosophy

### Empathetic, Trauma-Informed Language
Agents use compassionate framing:
- ❌ "You have a vulnerability in Gate 26"
- ✅ "Your undefined Ego center invites rest, not comparison—titrate with pendulation"

### Balance Light & Shadow
- **Light**: Healing, integration, higher-self connection
- **Shadow**: Protection, boundaries, awareness of manipulation

### Emergent Insights
Agents discover correlations not hard-coded:
- Example: "Your Kapha imbalance + undefined Root center + dorsal vagal state → grounding breathwork"

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- ✅ Expo + Tamagui setup
- ✅ Vercel AI SDK + Gemini integration
- ✅ Human Design agent (gates, centers, type)
- ✅ Chat interface with streaming
- ✅ Supabase RAG with HuggingFace embeddings

### Phase 2: Framework Expansion
- [ ] Astrology agent (transits, houses)
- [ ] Gene Keys agent (shadows → gifts → siddhis)
- [ ] I Ching agent (hexagram generation + interpretations)
- [ ] Numerology agent (life path, expression, destiny)
- [ ] Chakra agent (7-9 centers with HD correlations)

### Phase 3: Somatic Integration
- [ ] HealthKit data ingestion (HRV, walking asymmetry)
- [ ] Polyvagal state detection
- [ ] Breathwork/movement practice generation

### Phase 4: Advanced Synthesis
- [ ] Multi-agent chaining (LangChain workflows)
- [ ] Cross-framework synthesizer agent
- [ ] Daily attunement oracle
- [ ] Pattern recognition from journals

### Phase 5: Privacy & Production
- [ ] End-to-end encryption for birth data
- [ ] On-device model execution (Executorch)
- [ ] iOS App Store submission
- [ ] User authentication (Supabase Auth)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- **Expo Team** for the incredible developer experience
- **Tamagui** for performance-first React Native UI
- **Vercel** for the AI SDK that makes generative UI seamless
- **LangChain** for multi-agent orchestration
- **Supabase** for RAG-ready PostgreSQL

Inspired by the vision of **sovereignty through somatic awareness** and the integration of ancient wisdom with modern AI.

---

**Built by [Hayford Ayirebih](https://github.com/drisfet)** • Last Updated: November 8, 2025
