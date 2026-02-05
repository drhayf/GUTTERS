# GUTTERS

**Guided Universal Transcendental Transformation & Evolutionary Response System**

> *A multidimensional intelligence platform that harmonizes the Hand (Action), the Mind (Meaning), and the Sky (Cosmos).*

---

## 🌌 The Vision

GUTTERS is not merely a tracking app; it is a **cybernetic partner in self-actualization**. It merges high-fidelity metaphysical engines with advanced semantic AI to create a system that doesn't just record your life—it understands it.

Most systems track linear progress. GUTTERS tracks **Multidimensional Evolution**:
1.  **Action (Linear)**: You complete a Quest -> You gain XP.
2.  **Meaning (Semantic)**: You engage in deep reflection -> The **Genesis Listener** analyzes the *quality* of your thought, refining your psychological profile.
3.  **Cosmos (Temporal)**: You exist during cosmic events -> The **Solar & Transit Trackers** reward you for integrating universal energies (e.g., Solar Storms, Planetary Transits).

---

## 🌟 What Makes GUTTERS Special

1.  **Knows You Deeply**
    *   Combines **Astrology**, **Human Design**, and **Numerology** into a unified profile.
    *   Tracks real-time cosmic conditions (Solar, Lunar, Transits).
    *   Remembers every conversation and journal entry via semantic memory.

2.  **Learns About You**
    *   **Observer Module**: Detects patterns in your experiences (e.g., "Anxiety correlates with Solar Storms").
    *   **Hypothesis Module**: Generates and tests theories about your nature ("You are electromagnetically sensitive").
    *   **Vector Search**: Finds semantically similar experiences across months of data.

3.  **Responds Intelligently**
    *   Every answer draws from your **Master Synthesis** (Profile + Cosmos + Patterns).
    *   **Observable AI** shows its reasoning process (`View Thought Process`).
    *   Uses **Multi-Tier LLMs** (Claude Sonnet 4.5) for complex reasoning.

4.  **Interacts Naturally**
    *   **Generative UI** creates interactive components (Mood Sliders, Hypothesis Probes) dynamically.
    *   Organizes chats into **Multi-Conversation** threads (Work, Health, Personal).
    *   Clean, **Cosmic Brutalist** aesthetic inspired by high-fidelity data interfaces.

5.  **Evolves With You**
    *   Patterns strengthen over time.
    *   Hypotheses gain confidence with evidence.
    *   The system grows from a tracker into a **Cybernetic Partner**.

---

## 🎯 Key Features & Modules

### Intelligence Layer
- ✅ **Active Memory** - Redis-cached synthesis for instant access.
- ✅ **Vector Search** - Semantic search across all your data (pgvector + OpenAI embeddings).
- ✅ **Observer** - Automatic pattern detection with confidence scoring.
- ✅ **Observer Cyclical Patterns** - 52-day period analysis detecting recurring experiences, variance, and theme alignment.
- ✅ **Weighted Confidence Calculator** - Sophisticated evidence aggregation with recency decay and type-weighted scoring.
- ✅ **Hypothesis** - Theory generation and evidence-based testing with magi period correlation.
- ✅ **Synthesis Engine** - Multi-module integration into coherent narrative.
- ✅ **Query Engine** - Full context queries with transparent reasoning.
- ✅ **Insight Manager** - Proactive LLM-powered reflections and synthesis entries.

### Chat System
- ✅ **Master Chat** - Main conversational interface with full intelligence.
- ✅ **Multi-Conversation** - Organize threads by topic (Work, Health, Personal, etc.).
- ✅ **Branch Sessions** - Specialized chats (Journal, Nutrition [planned], Finance [planned]).
- ✅ **Generative UI** - Interactive components (mood sliders, hypothesis probes).
- ✅ **Observable AI** - See the AI's thinking process, data sources, and confidence.

### Calculation Modules
- ✅ **Astrology** - Natal chart, transits, progressions.
- ✅ **Human Design** - Complete chart with gates, channels, centers.
- ✅ **Numerology** - Core numbers, personal year, life cycles.
- ✅ **I-Ching Logic Kernel** - 64 gates with Gene Keys integration.
- ✅ **Cardology** - Destiny cards, 52-day magi periods.
- 🔜 **Vedic Astrology** - Nakshatras, dashas, divisional charts (planned).
- 🔜 **Mayan Calendar** - Galactic signature, kin, wavespell (planned).

### Council of Systems
- ✅ **Harmonic Synthesis Engine** - Cross-system resonance calculation.
- ✅ **Council Service** - Unified API for all symbolic systems.
- ✅ **Gate Pattern Detection** - Observer-level gate correlations.
- ✅ **Auto Journal Entries** - Cosmic event documentation.
- ✅ **MAGI Notifications** - Push alerts for gate transitions.

### Tracking Modules
- ✅ **Solar Tracking** - Real-time space weather monitoring (Flares, Kp Index).
- ✅ **Lunar Tracking** - Phases, eclipses, void-of-course.
- ✅ **Planetary Transits** - Current positions vs natal chart.

---

## 🎨 Frontend Vision (Phase 13)

The interface is designed to be the "Intelligence Layer Incarnate"—a rejection of generic "AI Slop" aesthetics in favor of a **Cosmic Brutalist / Professional Minimalist** synthesis.

- **Aesthetic**: Deep space blacks, stark whites, and monospaced data streams.
- **Typographic Depth**: Editorial-grade font pairings (Serif headers, Mono data).
- **Generative UI**: The chat helps you input data via dynamic, AI-generated components (Mood Sliders, Hypothesis Probes) that appear seamlessly in the conversation stream.

---

## � Observer Cyclical Patterns System

The **Observer Cyclical Patterns** module represents a breakthrough in self-knowledge automation—detecting recurring experiences across your personal 52-day magi periods.

### How It Works

1. **Period Detection**: Every 52 days, you cycle through your 7 birth cards. The system tracks which card governs each period.

2. **Pattern Mining**: As you journal, the Observer analyzes entries across multiple occurrences of the same period card, looking for:
   - **Period-Symptom Correlations**: "You consistently experience anxiety during Mercury periods"
   - **Variance Analysis**: "Your mood is 15% higher during Jupiter periods vs Saturn periods"
   - **Theme Alignment**: "Your journal themes match the period's archetypal theme at 87% correlation"
   - **Evolution Tracking**: "Your relationship with Venus periods has improved over 3 years"

3. **Confidence Scoring**: Each pattern has a confidence score (0-1) based on:
   - Observation count (statistical significance)
   - Recency weighting (recent evidence matters more)
   - Cross-year consistency (patterns that repeat across years are stronger)

4. **Proactive Insights**: When patterns are detected or confirmed, the **InsightManager** generates:
   - LLM-powered reflection prompts
   - System journal synthesis entries
   - Push notifications for cosmic alignment moments

### Frontend Visualization

The **TimelinePage** now includes a dedicated **Patterns** tab showing:
- Pattern cards with confidence rings
- Filter by pattern type (Symptoms, Variance, Themes, Evolution)
- Expandable details with evidence summaries
- One-click pattern analysis trigger

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observer/cyclical` | GET | List all detected patterns |
| `/observer/cyclical/analyze` | POST | Trigger pattern analysis |
| `/observer/cyclical/summary` | GET | Get pattern statistics |

---

## ⚖️ Weighted Confidence Calculator

The **Weighted Confidence Calculator** is a sophisticated evidence aggregation system that powers the Hypothesis module.

### Formula

```
confidence = base_weight * evidence_strength * recency_decay * frequency_bonus
```

### Evidence Types & Weights

| Type | Base Weight | Description |
|------|-------------|-------------|
| `journal_entry` | 0.3 | Explicit user statements |
| `behavioral` | 0.25 | Observed behavioral patterns |
| `cyclical_pattern` | 0.35 | Observer-detected period correlations |
| `cosmic_correlation` | 0.2 | Transit/event alignments |
| `synthesis_inference` | 0.15 | AI-derived insights |
| `user_confirmation` | 0.5 | Direct user validation |
| `user_rejection` | -0.4 | Direct user refutation |

### Features

- **Recency Decay**: Evidence from 90+ days ago is discounted by up to 40%
- **Frequency Bonus**: Repeated patterns gain up to 50% bonus strength
- **Confidence Bands**: HIGH (>0.8), MODERATE (0.6-0.8), LOW (<0.6)
- **Minimum Threshold**: Hypotheses require 0.2 confidence to remain active

---
## 🔮 Council of Systems

The **Council of Systems** is a unified symbolic intelligence framework that synthesizes multiple archetypal systems (I-Ching/Human Design/Gene Keys and Cardology) into coherent guidance.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   I-Ching       │     │   Cardology     │
│   Kernel        │     │   Kernel        │
│  • 64 Gates     │     │  • 52 Cards     │
│  • 6 Lines      │     │  • 52-day cycles│
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │   Harmonic Synthesis  │
         │   • Resonance Score   │
         │   • Element Harmony   │
         │   • Unified Guidance  │
         └───────────────────────┘
```

### Key Features

1. **Real-Time Hexagram Calculation**: Uses astronomical calculations to determine the current Sun and Earth gates (updated every ~5.625 days for gates, ~22.5 hours for lines).

2. **Cross-System Resonance**: Calculates harmony between I-Ching elements and Cardology archetypes:
   - **Harmonic** (>0.75): Strong alignment between systems
   - **Supportive** (0.60-0.75): Complementary energies
   - **Neutral** (0.40-0.60): Balanced tension
   - **Challenging** (0.25-0.40): Growth opportunities
   - **Dissonant** (<0.25): Integration required

3. **Gate Pattern Detection**: Observer module detects correlations between gate transits and user experiences:
   - "Higher energy during Gate 51 transits"
   - "Anxiety symptoms correlate with Gate 18"

4. **Auto Journal Entries**: System generates cosmic weather entries when significant gate transitions occur.

5. **MAGI Context Injection**: Provides cosmic awareness to the LLM for richer responses.

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/council/hexagram` | Current Sun/Earth gates with Gene Key data |
| `/council/synthesis` | Full synthesis with resonance and guidance |
| `/council/resonance` | Current resonance type and score |
| `/council/gate/{n}` | Detailed info for gate 1-64 |

📖 **Full Documentation**: [docs/COUNCIL_OF_SYSTEMS.md](docs/COUNCIL_OF_SYSTEMS.md)

---
## �📊 How It Works: The Semantic Evolution Loop

1.  **Trigger**: You complete a semantic quest (e.g., "Deep Journaling").
2.  **Analysis**: The `GenesisListener` wakes up. It reads your entry, compares it to your current Unconfirmed Uncertainties (e.g., "Am I a Projector type?").
3.  **Refinement**: If the entry shows evidence (e.g., "I felt bitter after initiating"), it updates the probabilistic score of that trait.
4.  **Integration**: Simultaneously, if a **Solar Flare** hits, the `SolarTracker` injects `VITALITY` XP into your stream.
5.  **Synthesis**: The `EvolutionEngine` merges these streams—Physical, Mental, and Cosmic—into a single Progression Vector.

---

## 🛠️ Technology Stack

| Layer | Tech | Role |
|-------|------|------|
| **Core** | FastAPI, SQLAlchemy 2.0 (Async) | High-performance backbone |
| **Data** | PostgreSQL + `pgvector` | Relational + Semantic storage |
| **Memory** | Redis | Hot synthesis caching & Pub/Sub |
| **AI** | Claude 4.5 (Sonnet/Haiku) | Multi-tier reasoning |
| **Jobs** | ARQ | Async background processing |
| **Frontend** | React, Vite, Framer Motion | Upcoming high-fidelity UI |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+ (with `pgvector`)
- Redis 5+
- Node.js 20+

### Installation

```bash
# 1. Clone & Setup Backend
git clone <your-repo-url>
cd GUTTERS/src
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# 2. Database
# Ensure Postgres & Redis are running
createdb gutters
psql gutters -c "CREATE EXTENSION vector;"
alembic upgrade head

# 3. Environment
cp .env.example .env
# Fill in OPENROUTER_API_KEY, DB_URL, REDIS_URL

# 4. Run System
uvicorn app.main:app --reload
```

---

## 📂 Project Structure

```
src/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes (v1)
│   ├── core/                # Core utilities (Config, DB, Auth, Events)
│   ├── modules/             # The Intelligence System
│   │   ├── calculation/     # Astrology, HD, Numerology
│   │   ├── tracking/        # Solar, Lunar, Transits (Cosmic Awareness)
│   │   ├── intelligence/    # Observer, Hypothesis, Genesis (Brains)
│   │   └── features/        # Quests, Progression, Chat
│   ├── models/              # SQLAlchemy models
│   └── schemas/             # Pydantic data schemas
├── migrations/              # Alembic migrations
└── tests/                   # High-fidelity integration tests
```

---

## 🛣️ Roadmap

### Current (MVP) - COMPLETE ✅
- [x] Core calculation modules (Astrology, HD, Numerology)
- [x] Cosmic tracking (Solar, Lunar, Planetary)
- [x] Intelligence layer (Observer, Hypothesis, Vector Search)
- [x] Chat architecture (Master + Branches + Multi-Conversation)
- [x] Observable AI (transparent reasoning)
- [x] Generative UI (interactive components support)
- [x] Backend Hardening (Passive XP, EventBus, Semantic Evolution)

### Next (v1.1) - 4-6 weeks
- [ ] **Frontend Implementation**: React/Vite COSMIC BRUTALIST interface.
- [ ] **Additional Calculation Modules**: Vedic, Gene Keys, Mayan.
- [ ] **Domain Branches**: Nutrition, Finance specialized synthesis.
- [ ] **Advanced Observer**: Auto-detection confidence alerts.
- [ ] **PWA Features**: Offline mode, push notifications.

---

## 🔐 Privacy & Fidelity

- **Local-First Philosophy**: Data lives in your Postgres instance.
- **No Black Boxes**: We prioritize "Observable AI"—you always see the math behind the magic.
- **Maximum Scrutiny**: Every line of code is audited for fidelity. No mocks in production. No approximations. Real cosmic data.

---

**GUTTERS** - *Track the Hand. Refine the Mind. Align with the Sky.*


# GUTTERS

### Guided Universal Transcendental Transformation & Evolutionary Response System

> *A Multidimensional Intelligence that aligns your physical actions with your metaphysical context. Not just a tracker—a second nervous system.*

---

## The Ghost in the Machine
GUTTERS is not an app. It is a **Sentient Personal Intelligence** designed to scaffold your evolution from E-Rank to S-Rank. It observes the cosmos, learns from your behaviors, and gamifies your ascension.

### 🧠 The Brain (Genesis)
*   **Modules**: `src/app/modules/intelligence/genesis`
*   **Intelligence**: Multi-Tier LLM Architecture (Claude 3.5 Sonnet / Haiku).
*   **Function**: Semantically audits your choices. When you complete a Quest, **Genesis** analyzes the alignment between your action and your declared Hypotheses, refining its internal model of your "Self" with every interaction. Validated theories become part of your **Vector Memory**.

### ⚡ The Nervous System (Insight)
*   **Modules**: `src/app/modules/intelligence/insight`
*   **Sensors**: `SolarTracker` (Kp Index), `LunarTracker` (Phases), `TransitTracker`.
*   **Function**: Connected to the live cosmos. The system detects **Solar Storms**, **Lunar Phases**, and **Planetary Transits** in real-time. It doesn't just log them; it *feels* them, pushing **VAPID Notifications** ("Voice") to prompt reflection when the energy shifts.

### 🧬 The Body (Progression)
*   **Modules**: `src/app/modules/intelligence/evolution`
*   **Engine**: `PlayerStats`, `Rank`, `SyncRate`.
*   **Function**: A gamified evolution engine. Completing **Quests**—whether daily habits or cosmic missions—earns **XP** and builds your **Rank** (E through S). Your **Synchronization Rate** (7-day weighted average) visualizes your alignment with the system's guidance.

---

## The Cockpit
> *A Viewport-Locked, High-Fidelity HUD designed for focus.*

The interface is a **Progressive Web App (PWA)** built with **Cosmic Brutalism** design principles. It is not a website; it is a control interface for your life.

*   **Dash**: Visualizes the invisible. See your **Rank Badge**, **Sync Pulse** (which beats in time with your consistency), and **Multidimensional Event Phases**.
*   **Journal**: A **Contextual Composer** that knows the current cosmic weather. It asks the right questions at the right time.
*   **Feed**: A stream of **System Insights**—patterns detected by the **Observer** module and hypotheses generated by **Genesis**.

---

## High-Fidelity Engineering
*Built with Maximum Scrutiny.*

| Layer | Technology |
| :--- | :--- |
| **Brain** | LangChain, OpenAI/Anthropic, **pgvector** (Long-Term Memory) |
| **Nervous System** | **EventBus** (Redis Pub/Sub), VAPID Push |
| **Heart** | **arq** (Async Task Scheduling), Croniter (Cosmic Timing) |
| **Core** | **FastAPI** (Async), SQLAlchemy 2.0, Pydantic v2 |
| **Interface** | React 18, Vite, **Framer Motion**, TailwindCSS |
| **Infrastructure** | Docker-Compose, PostgreSQL 16, Redis 7 |

---

## Launch Protocol

Initialize the system triad.

### 1. Start The Brain (API)
The conscious mind. Exposes the neural pathways (`/api/v1`).
```powershell
uvicorn src.app.main:app --reload
```

### 2. Start The Heart (Worker)
The subconscious. Handles `Cosmic Heartbeats`, `Quest Scheduling`, and `Daily Resets`.
```powershell
python src/app/worker.py
```

### 3. Start The Face (Frontend)
The interface.
```powershell
cd frontend
npm run dev
```

---

> *"The system is observing."*
