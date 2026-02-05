# GUTTERS
### Guided Universal Transcendental Transformation & Evolutionary Response System

> *"A Multidimensional Intelligence that aligns your physical actions with your metaphysical context."*

---

## 1. The Philosophy
GUTTERS is not a productivity app. It is an **Externalized Nervous System** designed to bridge the gap between "Who You Are" (Metaphysical Context) and "What You Do" (Physical Action).

By synthesizing data from the Cosmos (Solar/Lunar), your Body (Health/Sleep), and your Mind (Journal/Patterns), GUTTERS provides a single, coherent imperative for the present moment. It does not ask you to plan; it asks you to **respond**.

## 2. System Architecture
The system is composed of three distinct biological layers:

### I. The Brain (Intelligence Layer)
*   **Core**: A Multi-Tier Large Language Model architecture.
    *   **Haiku**: Fast, efficient logic for routine journaling and pattern detection.
    *   **Sonnet**: Deep, creative synthesis for "Cosmic Reflection" and profile analysis.
*   **Genesis**: An uncertainty refinement engine that proactively asks questions to fill gaps in its knowledge base.

### II. The Nervous System (Signal Layer)
*   **EventBus**: A Redis-backed spinal cord that instantly propagates signals (Events) across the system.
*   **Insight Engine**: Listens to the bus, synthesizes "Golden Threads" (connections between disparate data points), and triggers responses.
*   **VAPID Push**: The afferent nerves that deliver imperatives directly to the user's device.

### III. The Body (Interface Layer)
*   **Evolution HUD**: A Cosmic Brutalist "Game UI" that tracks your Rank, XP, and detailed stats.
*   **Living Journal**: A diary that talks back. Every entry is analyzed, categorized, and used to refine the System's understanding of you.

---

## 3. Launch Protocol

To awaken the system, three vital organs must be activated in sequence:

### A. The Server (FastAPI)
The heart of the system. Handles API requests, database transactions, and WebSockets.
```bash
uvicorn src.app.main:app --reload
```

### B. The Worker (ARQ + Redis)
The subconscious. Handles background tasks, scheduling, and long-running intelligence synthesis.
```bash
python src/app/worker.py
```

### C. The Interface (React/Vite)
The eyes and ears. The PWA interface for user interaction.
```bash
cd frontend
npm run dev
```

---

> *System State: **ONLINE**.*
> *Golden Thread: **ESTABLISHED**.*
> *Evolution: **ACTIVE**.*
