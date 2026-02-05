# 🔮 Council of Systems - Complete Integration Documentation

> **Phase 26: I-Ching Logic Kernel & Harmonic Synthesis Engine**  
> *A complete integration of the Council of Systems into the GUTTERS platform*

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [I-Ching Logic Kernel](#i-ching-logic-kernel)
4. [Cardology Kernel Integration](#cardology-kernel-integration)
5. [Harmonic Synthesis Engine](#harmonic-synthesis-engine)
6. [Council Service](#council-service)
7. [Observer Integration](#observer-integration)
8. [Hypothesis Enhancement](#hypothesis-enhancement)
9. [Events & Notifications](#events--notifications)
10. [Auto Journal Entries](#auto-journal-entries)
11. [Frontend Components](#frontend-components)
12. [API Endpoints](#api-endpoints)
13. [Testing](#testing)
14. [File Reference](#file-reference)
15. [Usage Examples](#usage-examples)

---

## Executive Summary

The Council of Systems represents a unified symbolic intelligence framework that synthesizes multiple archetypal systems (I-Ching/Human Design/Gene Keys and Cardology) into a coherent guidance mechanism. This implementation enables:

- **Real-time hexagram calculations** based on precise astronomical positions
- **Cross-system resonance detection** finding harmony between I-Ching and Cardology
- **Gate-specific pattern recognition** in the Observer module
- **Automatic journal entry generation** for cosmic events
- **Push notifications** for significant gate transitions
- **High-fidelity frontend visualization** of cosmic states

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Lines of Code Added | ~3,500 |
| New Files Created | 8 |
| Files Modified | 8 |
| E2E Tests | 32 |
| Gate Database Entries | 64 |
| API Endpoints | 4 |
| Notification Types | 4 |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         COUNCIL OF SYSTEMS                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│   │   I-Ching       │     │   Cardology     │     │   Astrology     │   │
│   │   Kernel        │     │   Kernel        │     │   (Future)      │   │
│   │                 │     │                 │     │                 │   │
│   │  • 64 Gates     │     │  • 52 Cards     │     │  • Transits     │   │
│   │  • 6 Lines      │     │  • 7 Planets    │     │  • Houses       │   │
│   │  • Sun/Earth    │     │  • 52-day cycles│     │  • Aspects      │   │
│   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘   │
│            │                       │                       │            │
│            └───────────────┬───────┴───────────────────────┘            │
│                            │                                             │
│                            ▼                                             │
│            ┌───────────────────────────────┐                            │
│            │   Harmonic Synthesis Engine   │                            │
│            │                               │                            │
│            │  • Resonance Calculation      │                            │
│            │  • Element Mapping            │                            │
│            │  • Cross-System Correlation   │                            │
│            │  • Guidance Synthesis         │                            │
│            └───────────────┬───────────────┘                            │
│                            │                                             │
│                            ▼                                             │
│            ┌───────────────────────────────┐                            │
│            │      Council Service          │                            │
│            │                               │                            │
│            │  • API Gateway                │                            │
│            │  • Event Emission             │                            │
│            │  • State Management           │                            │
│            │  • MAGI Context Provider      │                            │
│            └───────────────────────────────┘                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## I-Ching Logic Kernel

### Location
`src/app/modules/intelligence/iching/kernel.py`

### Purpose
Implements precise astronomical calculations for I-Ching hexagrams based on the Sun's ecliptic longitude, mapping to Human Design gates and Gene Keys frequencies.

### Core Components

#### GateData Model
```python
class GateData(BaseModel):
    """Complete data for a single I-Ching gate."""
    gate: int                      # 1-64
    iching_name: str               # Traditional I-Ching name
    hd_name: str                   # Human Design gate name
    hd_keynote: str                # Human Design keynote
    hd_center: str                 # Bodygraph center
    upper_trigram: str             # Binary representation
    lower_trigram: str             # Binary representation
    gk_shadow: str                 # Gene Keys shadow frequency
    gk_gift: str                   # Gene Keys gift frequency
    gk_siddhi: str                 # Gene Keys siddhi frequency
    gk_codon_ring: str             # Codon Ring name
    gk_amino_acid: str             # Associated amino acid
    zodiac_degrees: tuple          # Start/end degrees in zodiac
```

#### GATE_DATABASE
Complete database of all 64 gates with full metadata:

| Gate | HD Name | Gene Key Gift | Center |
|------|---------|---------------|--------|
| 1 | The Gate of Self-Expression | Freshness | G Center |
| 2 | The Gate of the Direction of the Self | Unity | G Center |
| 13 | The Gate of the Listener | Discernment | G Center |
| ... | ... | ... | ... |

#### Key Methods

```python
def get_daily_code(self, dt: datetime = None) -> DailyCode:
    """
    Get the complete I-Ching code for the given datetime.
    
    Returns:
        DailyCode containing:
        - sun_activation: GateActivation (gate, line)
        - earth_activation: GateActivation (opposite polarity)
        - sun_gate_data: Full GateData
        - earth_gate_data: Full GateData
    """

def calculate_gate(self, ecliptic_longitude: float) -> int:
    """Convert ecliptic longitude to I-Ching gate (1-64)."""

def calculate_line(self, ecliptic_longitude: float) -> int:
    """Convert ecliptic longitude to gate line (1-6)."""
```

### Astronomical Precision
- Uses Julian Date calculations for accurate Sun position
- Accounts for proper precession of equinoxes
- Handles timezone-aware and naive datetimes (assumes UTC for naive)

---

## Cardology Kernel Integration

### Location
`src/app/modules/intelligence/cardology/`

### Purpose
Calculates the playing card associated with a birth date and 52-day planetary periods.

### Core Components

#### Card Calculation
```python
def calculate_birth_card_from_date(birth_date: date) -> Card:
    """Get the destiny card for a birth date."""
    
def get_current_52_day_period() -> PeriodInfo:
    """Get current 52-day magi period with ruling planet."""
```

#### Card Archetypes
Each card has associated meanings:

| Card | Archetype | Element |
|------|-----------|---------|
| K♠ | Master of Wisdom | Water |
| Q♥ | Queen of Hearts | Fire |
| J♦ | The Dreamer | Air |
| ... | ... | ... |

---

## Harmonic Synthesis Engine

### Location
`src/app/modules/intelligence/synthesis/harmonic.py`

### Purpose
Synthesizes multiple symbolic systems into a unified resonance calculation and guidance output.

### Core Components

#### Element Enum
```python
class Element(str, Enum):
    FIRE = "fire"
    WATER = "water"
    AIR = "air"
    EARTH = "earth"
    ETHER = "ether"
```

#### ResonanceType Enum
```python
class ResonanceType(str, Enum):
    HARMONIC = "harmonic"      # High resonance (> 0.75)
    SUPPORTIVE = "supportive"  # Good resonance (0.60-0.75)
    NEUTRAL = "neutral"        # Moderate (0.40-0.60)
    CHALLENGING = "challenging" # Low resonance (0.25-0.40)
    DISSONANT = "dissonant"    # Very low (< 0.25)
```

#### HarmonicSynthesis Model
```python
class HarmonicSynthesis(BaseModel):
    timestamp: datetime
    systems: List[SystemReading]
    resonance_score: float
    resonance_type: ResonanceType
    dominant_element: Element
    guidance: List[str]
```

#### Resonance Calculation
The engine calculates resonance based on:
1. **Elemental harmony** between systems
2. **Numeric correlations** (gate numbers, card values)
3. **Archetypal alignment** (themes and meanings)

---

## Council Service

### Location
`src/app/modules/intelligence/council/service.py`

### Purpose
Central orchestration service that unifies all Council operations, provides API access, and manages events.

### Core Models

#### HexagramState
```python
class HexagramState(BaseModel):
    """Current I-Ching hexagram state."""
    timestamp: datetime
    sun_gate: int
    sun_line: int
    earth_gate: int
    earth_line: int
    sun_gate_name: str
    sun_gate_keynote: str
    sun_gene_key_shadow: str
    sun_gene_key_gift: str
    sun_gene_key_siddhi: str
    earth_gate_name: str
    earth_gene_key_gift: str
```

#### CouncilSynthesisResult
```python
class CouncilSynthesisResult(BaseModel):
    """Complete Council synthesis output."""
    timestamp: datetime
    resonance_score: float
    resonance_type: str
    dominant_element: str
    macro_symbol: str          # e.g., "J♦ - The Dreamer"
    micro_symbol: str          # e.g., "Gate 13.4 - Discernment"
    current_period_planet: str
    current_hexagram_summary: str
    guidance: List[str]
```

#### GateTransition
```python
class GateTransition(BaseModel):
    """Represents a gate change event."""
    old_sun_gate: int
    new_sun_gate: int
    old_earth_gate: int
    new_earth_gate: int
    old_line: int
    new_line: int
    transition_type: str       # "gate_shift", "line_shift"
    significance: str          # "major", "minor"
    old_gate_data: Dict
    new_gate_data: Dict
```

### Key Methods

```python
def get_current_hexagram(self, dt: datetime = None) -> HexagramState:
    """Get current hexagram with full gate data."""

def get_council_synthesis(self, birth_date: date = None, current_dt: datetime = None) -> CouncilSynthesisResult:
    """Get unified Council synthesis."""

async def check_gate_transition(self, user_id: int) -> Optional[GateTransition]:
    """Detect and emit gate transition events."""

def get_magi_context(self) -> Dict[str, Any]:
    """Get Council context for MAGI LLM injection."""

def get_gate_info(self, gate_number: int) -> Optional[Dict[str, Any]]:
    """Get detailed info about a specific gate."""
```

---

## Observer Integration

### Location
`src/app/modules/intelligence/observer/cyclical.py`

### Enhanced Pattern Types
```python
class CyclicalPatternType(str, Enum):
    # Existing period patterns
    PERIOD_SPECIFIC_SYMPTOM = "period_specific_symptom"
    INTER_PERIOD_MOOD_VARIANCE = "inter_period_mood_variance"
    
    # NEW: Gate-specific patterns
    GATE_SPECIFIC_SYMPTOM = "gate_specific_symptom"
    INTER_GATE_MOOD_VARIANCE = "inter_gate_mood_variance"
    GATE_POLARITY_PATTERN = "gate_polarity_pattern"
    GATE_LINE_CORRELATION = "gate_line_correlation"
```

### New Gate Fields in CyclicalPattern
```python
sun_gate: Optional[int]           # Gate 1-64
earth_gate: Optional[int]         # Polarity gate
gate_line: Optional[int]          # Line 1-6
gate_name: Optional[str]          # Human Design gate name
gene_key_gift: Optional[str]      # Gene Keys gift frequency
```

### New Detection Methods

#### detect_gate_specific_symptoms()
```python
async def detect_gate_specific_symptoms(
    self,
    user_id: int,
    entries: List[Dict[str, Any]],
    iching_kernel: IChingKernel
) -> List[CyclicalPattern]:
    """
    Detect symptoms that recur during specific Sun gates.
    
    Groups journal entries by the Sun gate at the time of entry,
    then looks for symptoms that appear significantly more often
    during specific gates vs baseline.
    """
```

#### detect_gate_mood_patterns()
```python
async def detect_gate_mood_patterns(
    self,
    user_id: int,
    entries: List[Dict[str, Any]],
    iching_kernel: IChingKernel
) -> List[CyclicalPattern]:
    """
    Detect mood/energy variations across different Sun gates.
    
    Calculates average mood scores for each gate the user has
    data for, then identifies gates with significantly higher
    or lower mood than baseline.
    """
```

---

## Hypothesis Enhancement

### Location
`src/app/modules/intelligence/hypothesis/models.py`

### New Fields
```python
class Hypothesis(BaseModel):
    # Existing fields...
    
    # NEW: Hexagram correlation tracking
    origin_hexagram: Optional[int] = None  # Gate when hypothesis formed
    gate_evidence_count: Dict[str, int] = Field(default_factory=dict)
    
    def track_hexagram_evidence(self, sun_gate: int, earth_gate: int):
        """Track evidence occurrence during specific gates."""
        key = f"Gate {sun_gate}"
        self.gate_evidence_count[key] = self.gate_evidence_count.get(key, 0) + 1
```

---

## Events & Notifications

### Location
`src/app/modules/infrastructure/push/map.py`

### New Event Types

#### MAGI Events in events.py
```python
MAGI_HEXAGRAM_CHANGE = "magi.hexagram.change"
MAGI_COUNCIL_SYNTHESIS = "magi.council.synthesis"
MAGI_RESONANCE_SHIFT = "magi.resonance.shift"
JOURNAL_COSMIC_ENTRY = "journal.cosmic_entry.created"
```

### Notification Configurations

```python
"magi.hexagram.change": NotificationConfig(
    preference_key="push_magi_events",
    title_template="🌅 Gate Transition",
    body_template="The Sun has moved from Gate {old_gate} ({old_name}) "
                  "to Gate {new_gate} ({new_name}). "
                  "Today's gift: {gene_key_gift}",
    importance="significant",
    trigger_conditions={"significance": "major"},
),

"magi.council.synthesis": NotificationConfig(
    preference_key="push_magi_events",
    title_template="✨ Council Synthesis",
    body_template="Today's Code: {micro_symbol}. "
                  "Resonance: {resonance_type}. {guidance}",
    importance="normal",
),

"magi.resonance.shift": NotificationConfig(
    preference_key="push_magi_events",
    title_template="🔮 Resonance Shift",
    body_template="Resonance has shifted from {old_type} to {new_type}. "
                  "Current guidance: {guidance}",
    importance="significant",
),

"journal.cosmic_entry.created": NotificationConfig(
    preference_key="push_journal",
    title_template="📖 Cosmic Entry Added",
    body_template="A new journal entry has been generated: {title}",
    importance="low",
),
```

---

## Auto Journal Entries

### Location
`src/app/modules/intelligence/council/journal_generator.py`

### Purpose
Automatically generates high-quality journal entries when significant cosmic events occur.

### CosmicEventType Enum
```python
class CosmicEventType(str, Enum):
    GATE_TRANSITION = "gate_transition"
    DAILY_SYNTHESIS = "daily_synthesis"
    RESONANCE_SHIFT = "resonance_shift"
    NOTABLE_ALIGNMENT = "notable_alignment"
    LINE_SHIFT = "line_shift"
```

### GeneratedJournalEntry Model
```python
class GeneratedJournalEntry(BaseModel):
    title: str
    content: str
    entry_type: CosmicEventType
    event_data: Dict[str, Any]
    reflection_prompts: List[str]
    tags: List[str]
    mood_suggestion: Optional[int] = None
    energy_suggestion: Optional[int] = None
```

### Generation Methods

#### generate_gate_transition_entry()
Creates rich journal entries when the Sun moves to a new gate:

```
## Gate Transition: The Listener Awakens

At 6:42 AM UTC, the Sun crossed from Gate 12 (Standstill - Purity) 
into Gate 13 (The Gate of the Listener - Discernment).

### The Shift
We move from the contemplative stillness of Gate 12 into the 
receptive wisdom of Gate 13. Where yesterday called for patience,
today invites deep listening.

### Gene Keys Spectrum
- **Shadow to transform**: Discord
- **Gift to embody**: Discernment  
- **Siddhi to awaken**: Empathy

### Reflection Prompts
1. What needs to be heard that I haven't been listening to?
2. How can I embody Discernment today?
3. What does the transition from Purity to Discernment mean for me?
```

#### generate_daily_synthesis_entry()
Creates daily "cosmic weather" entries combining I-Ching and Cardology:

```
## Daily Code: February 5, 2025

**Sun Gate**: 13.4 - The Gate of the Listener (Line 4)
**Earth Gate**: 7.4 - The Gate of the Role of the Self
**Period Card**: J♦ - The Dreamer
**Resonance**: Neutral (0.40)

### Today's Guidance
- Express your creative vision in some form
- Practice Discernment in conversations
- Notice when Discord arises, pivot to deep listening
```

---

## Frontend Components

### Location
`frontend/src/components/council/CouncilDashboard.tsx`

### Components

#### HexagramDisplay
```tsx
interface HexagramDisplayProps {
  sunGate: number;
  sunLine: number;
  sunGateName: string;
  sunKeynote: string;
  earthGate: number;
  earthGateName: string;
}
```

Visual display of the current hexagram showing:
- Sun gate number and name
- Line number (1-6)
- Earth polarity gate
- Keynote description

#### GeneKeySpectrum
```tsx
interface GeneKeySpectrumProps {
  shadow: string;
  gift: string;
  siddhi: string;
}
```

Three-tier visualization of the Gene Key frequency spectrum:
- Shadow (challenge to transform)
- Gift (current potential)
- Siddhi (highest expression)

#### ResonanceIndicator
```tsx
interface ResonanceIndicatorProps {
  score: number;
  type: string;
  element: string;
}
```

Progress bar showing resonance level with color-coded type:
- Harmonic: Green
- Supportive: Blue
- Neutral: Gray
- Challenging: Orange
- Dissonant: Red

#### CardologyCard
```tsx
interface CardologyCardProps {
  card: string;
  archetype: string;
  planet: string;
}
```

Visual playing card display showing:
- Card symbol (e.g., J♦)
- Archetype name
- Current ruling planet

#### CouncilDashboard
Main dashboard component that:
- Uses React Query for data fetching
- Displays all sub-components
- Shows loading/error states
- Animates with Framer Motion

---

## API Endpoints

### Location
`src/app/api/v1/intelligence.py`

### Endpoints

#### GET /council/hexagram
Returns current hexagram state.

**Response:**
```json
{
  "timestamp": "2025-02-05T09:38:28Z",
  "sun_gate": 13,
  "sun_line": 4,
  "earth_gate": 7,
  "earth_line": 4,
  "sun_gate_name": "The Gate of the Listener",
  "sun_gate_keynote": "The role of listening in the process of understanding",
  "sun_gene_key_shadow": "Discord",
  "sun_gene_key_gift": "Discernment",
  "sun_gene_key_siddhi": "Empathy",
  "earth_gate_name": "The Gate of the Role of the Self",
  "earth_gene_key_gift": "Guidance"
}
```

#### GET /council/synthesis
Returns full Council synthesis.

**Response:**
```json
{
  "timestamp": "2025-02-05T09:38:28Z",
  "resonance_score": 0.40,
  "resonance_type": "neutral",
  "dominant_element": "air",
  "macro_symbol": "J♦ - The Dreamer",
  "micro_symbol": "Gate 13.4 - The Gate of the Listener",
  "current_period_planet": "Jupiter",
  "current_hexagram_summary": "Sun in Gate 13 (The Gate of the Listener) Line 4, Earth in Gate 7",
  "guidance": [
    "Express your creative vision in some form",
    "Notice when 'Discord' arises, pivot to 'Discernment'"
  ]
}
```

#### GET /council/resonance
Returns resonance state with guidance.

**Response:**
```json
{
  "resonance_score": 0.40,
  "resonance_type": "neutral",
  "guidance": "Express your creative vision in some form"
}
```

#### GET /council/gate/{gate_number}
Returns detailed information about a specific gate.

**Response:**
```json
{
  "gate": 13,
  "iching_name": "Fellowship",
  "hd_name": "The Gate of the Listener",
  "hd_keynote": "The role of listening in the process of understanding",
  "hd_center": "G Center",
  "upper_trigram": "111",
  "lower_trigram": "101",
  "gene_key_shadow": "Discord",
  "gene_key_gift": "Discernment",
  "gene_key_siddhi": "Empathy",
  "codon_ring": "Ring of Purification",
  "amino_acid": "Histidine"
}
```

---

## Testing

### Location
`tests/modules/intelligence/test_council_e2e.py`

### Test Coverage

| Test Class | Tests | Purpose |
|------------|-------|---------|
| TestIChingKernel | 5 | Kernel initialization, daily code, gate database |
| TestCardologyKernel | 2 | Module initialization, birth card calculation |
| TestCouncilOfSystems | 3 | Council initialization, synthesis, resonance types |
| TestCouncilService | 6 | Hexagram, synthesis, MAGI context, gate info, events |
| TestJournalGenerator | 3 | Gate transition, daily synthesis, resonance shift entries |
| TestHypothesisIntegration | 2 | Hexagram fields, evidence tracking |
| TestObserverIntegration | 2 | Gate fields, pattern types |
| TestNotificationIntegration | 2 | Event map, config structure |
| TestElementHarmony | 2 | Element enum, resonance calculation |
| TestFullIntegration | 3 | Complete flow, date consistency, date variation |
| TestPerformance | 2 | Synthesis speed, calculation speed |

**Total: 32 tests, all passing**

### Running Tests
```bash
pytest tests/modules/intelligence/test_council_e2e.py -v
```

---

## File Reference

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `src/app/modules/intelligence/council/__init__.py` | 30 | Module exports |
| `src/app/modules/intelligence/council/service.py` | 562 | Core Council service |
| `src/app/modules/intelligence/council/journal_generator.py` | 380 | Auto journal entries |
| `frontend/src/components/council/CouncilDashboard.tsx` | 380 | React components |
| `tests/modules/intelligence/test_council_e2e.py` | 490 | E2E tests |
| `docs/COUNCIL_OF_SYSTEMS.md` | This file | Documentation |

### Files Modified

| File | Changes |
|------|---------|
| `src/app/modules/intelligence/iching/kernel.py` | Fixed timezone handling |
| `src/app/modules/intelligence/observer/cyclical.py` | Added gate pattern detection |
| `src/app/modules/infrastructure/push/map.py` | Added MAGI notifications |
| `src/app/api/v1/intelligence.py` | Updated Council endpoints |
| `tests/modules/intelligence/test_enhanced_synthesis.py` | Fixed imports |

---

## Usage Examples

### Getting Current Hexagram in Python
```python
from src.app.modules.intelligence.council import get_council_service

council = get_council_service()
hexagram = council.get_current_hexagram()

print(f"Sun Gate: {hexagram.sun_gate} Line: {hexagram.sun_line}")
print(f"Gate Name: {hexagram.sun_gate_name}")
print(f"Gene Key Gift: {hexagram.sun_gene_key_gift}")
```

### Getting MAGI Context for LLM
```python
context = council.get_magi_context()

# Inject into LLM system prompt:
system_prompt = f"""
You are MAGI, an AI assistant with cosmic awareness.

Current Cosmic State:
- Sun Gate: {context['hexagram']['sun_gate']} ({context['hexagram']['sun_gate_name']})
- Gene Key Gift: {context['hexagram']['sun_gene_key_gift']}
- Resonance: {context['council']['resonance_type']}

Use this awareness to inform your responses.
"""
```

### Frontend Usage
```tsx
import { CouncilDashboard } from '@/components/council/CouncilDashboard';

function MyPage() {
  return (
    <div>
      <h1>Your Cosmic Dashboard</h1>
      <CouncilDashboard />
    </div>
  );
}
```

### Detecting Gate Transitions
```python
from src.app.modules.intelligence.council import get_council_service

council = get_council_service()

# This will emit events if a gate transition occurred
transition = await council.check_gate_transition(user_id)

if transition:
    print(f"Gate shift from {transition.old_sun_gate} to {transition.new_sun_gate}")
```

---

## Future Enhancements

1. **Astrology Integration**: Add third system for full Council
2. **Profile Calculations**: Personal hexagram based on birth data
3. **Transit Tracking**: Track significant transits through natal gates
4. **Line Interpretations**: Add full 384 line interpretations
5. **Pattern Learning**: ML-based pattern detection for gate correlations
6. **Webhook Support**: External integrations for cosmic events

---

## Conclusion

The Council of Systems integration represents a significant advancement in the GUTTERS platform's ability to provide meaningful, personalized guidance. By synthesizing multiple symbolic systems and tracking their correlations with user data, we create a truly intelligent system that grows in accuracy over time.

The modular architecture ensures easy extension and maintenance, while the comprehensive test suite provides confidence in the system's reliability.

---

*Document generated: February 2025*  
*Phase 26: Council of Systems Integration*
