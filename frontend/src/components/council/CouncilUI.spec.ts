/**
 * ╔══════════════════════════════════════════════════════════════════════════════╗
 * ║                    COUNCIL OF SYSTEMS UI SPECIFICATION                       ║
 * ║                                                                              ║
 * ║   High-Fidelity UI Components for I-Ching + Cardology Integration            ║
 * ║                                                                              ║
 * ║   Author: GUTTERS Project / Magi OS                                          ║
 * ╚══════════════════════════════════════════════════════════════════════════════╝
 * 
 * This file specifies the React components needed to display the Council of
 * Systems synthesis in the GUTTERS frontend.
 */

// =============================================================================
// API ENDPOINTS
// =============================================================================

/**
 * GET /api/v1/intelligence/council/hexagram
 * Returns current I-Ching hexagram (Sun/Earth gates)
 * 
 * Response:
 * {
 *   "status": "success",
 *   "hexagram": {
 *     "sun_gate": 13,
 *     "sun_line": 4,
 *     "sun_gate_name": "The Gate of the Listener",
 *     "sun_gene_key_gift": "Discernment",
 *     "earth_gate": 7,
 *     "earth_line": 4,
 *     "earth_gate_name": "The Role of the Self",
 *     "earth_gene_key_gift": "Guidance",
 *     "polarity_theme": "Fellowship ↔ Leadership"
 *   }
 * }
 */

/**
 * GET /api/v1/intelligence/council/synthesis
 * Returns full Council synthesis with both systems
 * 
 * Response:
 * {
 *   "status": "success",
 *   "council": {
 *     "macro": { system: "Cardology", current_period: "Uranus", current_card: {...} },
 *     "micro": { system: "I-Ching", sun_gate: 13, earth_gate: 7, ... },
 *     "synthesis": { resonance_score: 0.65, resonance_type: "supportive", ... }
 *   }
 * }
 */

/**
 * GET /api/v1/intelligence/council/resonance
 * Returns current cross-system resonance level
 */

// =============================================================================
// COMPONENT HIERARCHY
// =============================================================================

/**
 * <CouncilDashboard>                    // Main container
 *   ├── <CouncilHeader>                 // "Council of Systems" title + resonance badge
 *   ├── <SystemCardsRow>                // Two system cards side by side
 *   │   ├── <CardologyCard>             // Macro system card
 *   │   │   ├── <PlanetaryPeriodBadge>  // Current planet icon + name
 *   │   │   ├── <PlayingCard>           // Visual card display
 *   │   │   └── <PeriodProgress>        // Days remaining bar
 *   │   └── <IChingCard>                // Micro system card
 *   │       ├── <HexagramDisplay>       // Binary representation
 *   │       ├── <GateInfo>              // Sun/Earth gates
 *   │       └── <GeneKeySpectrum>       // Shadow → Gift → Siddhi
 *   ├── <ResonanceIndicator>            // Visual resonance meter
 *   ├── <SynthesisGuidance>             // Unified guidance text
 *   └── <QuestSuggestions>              // Cross-system quest ideas
 */

// =============================================================================
// COMPONENT SPECIFICATIONS
// =============================================================================

/**
 * CouncilDashboard
 * 
 * Main container for the Council of Systems display.
 * Should be placed on the dashboard or as a dedicated page.
 * 
 * Props:
 * - userId: number
 * 
 * API Calls:
 * - useQuery(['council', 'synthesis'], fetchCouncilSynthesis)
 * - Refresh on mount and every 6 hours (gate transit frequency)
 */

/**
 * CardologyCard (Macro System)
 * 
 * Displays the current 52-day planetary period.
 * 
 * Visual Elements:
 * - Planetary icon (Mercury, Venus, Mars, etc.)
 * - Playing card visual (suit + rank)
 * - Element badge (Fire/Water/Air/Earth)
 * - Progress bar showing days remaining
 * - Period theme text
 * 
 * Colors:
 * - Hearts (♥): Rose/Pink (#EC4899)
 * - Clubs (♣): Emerald/Green (#10B981)
 * - Diamonds (♦): Amber/Gold (#F59E0B)
 * - Spades (♠): Indigo/Purple (#6366F1)
 */

/**
 * IChingCard (Micro System)
 * 
 * Displays the current I-Ching hexagram.
 * 
 * Visual Elements:
 * - Binary hexagram visualization (6 lines, solid/broken)
 * - Sun Gate badge (Gate X.Line)
 * - Earth Gate badge (Gate Y.Line)
 * - Gate names (Human Design)
 * - Gene Key spectrum (Shadow → Gift → Siddhi)
 * - Trigram breakdown (upper/lower)
 * 
 * Colors:
 * - Sun: Warm gold (#FBBF24)
 * - Earth: Deep brown (#78350F)
 * - Solid lines: Current theme color
 * - Broken lines: Muted gray
 */

/**
 * ResonanceIndicator
 * 
 * Visual meter showing cross-system harmony.
 * 
 * Display Modes:
 * - Circular gauge (0-100%)
 * - Animated glow based on resonance type
 * - Color gradient:
 *   - HARMONIC (70%+): Emerald glow
 *   - SUPPORTIVE (50-70%): Blue glow
 *   - NEUTRAL (30-50%): Gray neutral
 *   - CHALLENGING (10-30%): Amber warning
 *   - DISSONANT (<10%): Red tension
 * 
 * Animation:
 * - Pulse animation matching resonance level
 * - Transition smoothly between states
 */

/**
 * HexagramDisplay
 * 
 * Visual representation of the current hexagram.
 * 
 * Structure:
 * - 6 horizontal lines (bottom to top, like traditional I-Ching)
 * - Solid line: ━━━━━━━ (yang, 1)
 * - Broken line: ━━ ━━ (yin, 0)
 * - Current line (Sun position) highlighted
 * 
 * Styling:
 * - Width: 80px
 * - Line height: 8px
 * - Gap: 6px
 * - Border radius on ends
 */

/**
 * GeneKeySpectrum
 * 
 * Shows the Shadow → Gift → Siddhi progression.
 * 
 * Visual:
 * - Horizontal gradient bar
 * - Three labeled points
 * - Marker showing current frequency (based on XP if available)
 * 
 * Colors:
 * - Shadow zone: Dark/muted
 * - Gift zone: Vibrant/clear
 * - Siddhi zone: Luminous/transcendent
 */

// =============================================================================
// EXAMPLE USAGE
// =============================================================================

/**
 * import { CouncilDashboard } from '@/components/council';
 * 
 * function Dashboard() {
 *   return (
 *     <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 *       <ProgressionCard />
 *       <CouncilDashboard userId={user.id} />
 *       <QuestList />
 *       <JournalSummary />
 *     </div>
 *   );
 * }
 */

// =============================================================================
// MOCK DATA FOR DEVELOPMENT
// =============================================================================

export const MOCK_COUNCIL_DATA = {
  macro: {
    system: "Cardology",
    cycle: "52-day",
    current_period: "Uranus",
    current_card: {
      symbol: "J♦",
      name: "Jack of Diamonds",
      suit: "Diamonds",
      rank: "J",
    },
    days_remaining: 23,
    theme: "Creative innovation and unexpected breakthroughs",
  },
  micro: {
    system: "I-Ching",
    cycle: "~6-day",
    sun_gate: 13,
    sun_line: 4,
    sun_gate_name: "The Gate of the Listener",
    sun_gene_key_gift: "Discernment",
    earth_gate: 7,
    earth_line: 4,
    earth_gate_name: "The Role of the Self",
    earth_gene_key_gift: "Guidance",
    polarity_theme: "Fellowship ↔ Leadership",
  },
  synthesis: {
    resonance_score: 0.65,
    resonance_type: "supportive",
    elemental_profile: {
      fire: 0.2,
      water: 0.1,
      air: 0.3,
      earth: 0.4,
      ether: 0.0,
    },
    synthesis_guidance: "The Jack of Diamonds in Uranus period combines with Gate 13 (The Listener) to create powerful opportunities for breakthrough insights through deep listening. Let unexpected connections reveal new value.",
    quest_suggestions: [
      "Practice deep listening in your next conversation",
      "Journal about unexpected financial insights",
      "Explore a creative project with no defined outcome",
    ],
  },
};

// =============================================================================
// IMPLEMENTATION NOTES
// =============================================================================

/**
 * 1. POLLING STRATEGY
 *    - Initial load: Fetch all council data
 *    - Refresh every 6 hours (gate transit) or on user action
 *    - Use React Query with staleTime: 6 * 60 * 60 * 1000
 * 
 * 2. ANIMATION LIBRARY
 *    - Use Framer Motion for resonance indicator
 *    - Animate hexagram line transitions
 *    - Subtle pulse on resonance gauge
 * 
 * 3. ACCESSIBILITY
 *    - All visual elements have ARIA labels
 *    - Resonance level announced to screen readers
 *    - Gate information readable in text form
 * 
 * 4. RESPONSIVE DESIGN
 *    - Mobile: Stack cards vertically
 *    - Tablet: Side by side with smaller cards
 *    - Desktop: Full width with expanded details
 * 
 * 5. THEME INTEGRATION
 *    - Use existing GUTTERS color tokens
 *    - Match current dark/light mode
 *    - Element colors consistent with other modules
 */
