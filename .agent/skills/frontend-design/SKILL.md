---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme that fits the Intelligence Layer:
  - **Professional Minimalism** (Claude/Co-Star): Soft whites (#fafafa), Inter font, subtle depth, high readability, refined borders.
  - **Cosmic Brutalist**: High contrast, monospaced data, geometric patterns, bold accents.
  - **Luxury/Refined**: Dramatic negative space, premium typography (serif/sans pair), subtle gradients.
- **Constraints**: Technical requirements (Vite/React, PWA, accessibility).
- **Differentiation**: What makes this GUTTERS? (e.g. The 'Reasoning' trace visibility).

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Use `framer-motion` for React. Focus on high-impact moments: staggered reveals on load, smooth transitions for chat bubbles, and layout animations for expanding "Reasoning" traces.
- **Mobile-First Excellence**: GUTTERS is a PWA. Interfaces MUST adapt to mobile constraints.
  - **Keyboard Handling**: Use `useKeyboardHeight` hook to ensure input stays above keyboard.
  - **Viewport**: Ensure 100vh includes address bar adjustments (dvH).
  - **Navigation**: Sidebar on desktop -> Sheet/Drawer on mobile.
- **Intelligence Observability**: Assitant messages should reveal the "Core Layer" reasoning.
  - **Trace Collapsibles**: Use Collapsible components for "View Thought Process".
  - **Source Badges**: Tag modules consulted (Human Design, Transit, etc.).

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

---

## Layout Architecture & Structure Standards

### Viewport & Container Hierarchy

GUTTERS uses a strict **three-layer scroll architecture** to prevent layout breaking and unintended scroll behavior:

**Layer 1: AppShell (NEVER SCROLLS)**
```tsx
<div className="flex h-[100dvh] w-full max-w-[100vw] overflow-hidden">
  {/* Sidebar (Desktop) */}
  <div className="overflow-hidden flex flex-col" />
  
  {/* Main Content */}
  <main className="flex-1 overflow-hidden relative min-w-0 w-full flex flex-col">
    <Outlet /> {/* Page component routes here */}
  </main>
</div>
```

**Key Constraints:**
- `overflow-hidden` - Main container NEVER scrolls
- `h-[100dvh]` - Dynamic viewport height (accounts for mobile address bar)
- `w-full max-w-[100vw]` - Full width with viewport cap (prevents horizontal scroll)
- `flex flex-col` - Base flex layout for all children
- All interactive elements remain in fixed position (header, footer)

**Layer 2: Page Components (Internal Scroll)**
```tsx
<div className="h-full overflow-y-auto overflow-x-hidden w-full min-w-0 flex flex-col">
  {/* Content scrolls here only */}
  <div className="max-w-4xl mx-auto px-4 w-full min-w-0">
    {/* Constrained content */}
  </div>
  {/* Bottom padding for nav */}
  {isMobile && <div className="h-24" />}
</div>
```

**Key Constraints:**
- `h-full overflow-y-auto overflow-x-hidden` - Only vertical scroll, no horizontal
- `w-full min-w-0` - Full width with flex shrinking enabled
- `max-w: [container]` - Centered content with max width
- `px-4` - Consistent edge padding
- `flex flex-col` - For internal layouts

**Layer 3: Chat Interface (Special Case)**
```tsx
<div className="flex flex-col h-full w-full bg-background overflow-hidden touch-none">
  {/* Cosmic Ticker */}
  <div className="shrink-0 h-10 ... pointer-events-auto" />
  
  {/* Messages (uses internal ScrollArea) */}
  <div className="flex-1 overflow-y-auto overflow-x-hidden min-w-0 w-full" />
  
  {/* Command Deck */}
  <div className="shrink-0 ... min-w-0 w-full" />
</div>
```

**Key Constraints:**
- `touch-none` - Prevents accidental swipe scroll behavior
- `shrink-0` - Navbar elements never collapse
- `flex-1` + `overflow-y-auto` - Message area scrolls internally
- All sections have `min-w-0 w-full` - Prevents flex children from expanding

### Preventing Overflow & Layout Breaking

**The Golden Rule: `min-w-0` in Flex Layouts**

Flexbox children have implicit `min-width: auto` which prevents proper shrinking. Always add `min-w-0` to:
1. Flex container parents
2. Message/content wrappers
3. Text containers
4. Any element that contains dynamic content

```tsx
{/* WRONG - Content overflows */}
<div className="flex">
  <div className="max-w-[85%]">
    <div>{longText}</div>
  </div>
</div>

{/* CORRECT - Content respects bounds */}
<div className="flex min-w-0">
  <div className="max-w-[85%] min-w-0">
    <div className="max-w-full min-w-0 break-words overflow-wrap-anywhere">
      {longText}
    </div>
  </div>
</div>
```

**Text Breaking Hierarchy:**
```tsx
className="
  break-words           /* Break at word boundaries first */
  overflow-wrap-anywhere  /* Break long words if necessary */
  word-break-break-word   /* Force word breaks as last resort */
  max-w-full min-w-0      /* Never exceed parent, enable flex shrinking */
"
```

### Mobile-First Scroll Safety

**For Pages/Components:**
```tsx
// Always use internal scroll, never rely on AppShell scroll
<div className="h-full overflow-y-auto overflow-x-hidden">
  <div className="py-6"> {/* Top padding instead of relying on scroll space */}
    {/* Content here */}
  </div>
  {isMobile && <div className="h-24" />} {/* Bottom nav padding */}
</div>
```

**Prevent Rubber-Banding on Mobile:**
```css
main {
  overscroll-behavior: contain;
  -webkit-overscroll-behavior: contain;
}
```

**Prevent Accidental Touch-Scroll Near Inputs:**
```tsx
{/* High-interaction areas should prevent default drag behavior */}
<div className="touch-none"> {/* touch-action: none */}
  <input /> {/* Input won't trigger parent scroll */}
  <textarea /> {/* TextArea won't accidentally drag parent */}
</div>
```

### Responsive Width Management

**Pattern for all content containers:**
```tsx
{/* Desktop: Max width container */}
<div className="max-w-4xl md:max-w-6xl lg:max-w-7xl mx-auto px-4 w-full min-w-0">
  {/* Always centered, responsive, full-width on mobile */}
</div>
```

**Why this pattern:**
- `max-w-[size]` - Desktop width constraint
- `mx-auto` - Center content
- `px-4` - Mobile edge padding (doesn't break with max-w)
- `w-full` - Ensures full viewport width on mobile
- `min-w-0` - Enables flex children to shrink

### Common Anti-Patterns to Avoid

❌ **Using `overflow: auto` at each level**
```tsx
{/* Creates conflicting scroll zones */}
<div className="overflow-auto">
  <div className="overflow-auto"> {/* Problem! Two scroll areas */}
    {/* Content */}
  </div>
</div>
```

✅ **Single scroll zone per page**
```tsx
{/* One scroll area, everything else is fixed */}
<div className="flex flex-col h-full">
  <header className="shrink-0" /> {/* Fixed height, no scroll */}
  <main className="flex-1 overflow-y-auto" /> {/* Only this scrolls */}
  <footer className="shrink-0" /> {/* Fixed height, no scroll */}
</div>
```

❌ **Fixed width containers on mobile**
```tsx
<div className="w-96"> {/* Breaks on mobile! */}
```

✅ **Responsive width constraints**
```tsx
<div className="max-w-md md:max-w-2xl w-full"> {/* Works everywhere */}
```

❌ **Missing `min-w-0` in flex text containers**
```tsx
<div className="flex">
  <div className="max-w-[80%]"> {/* Still overflows due to implicit min-width */}
    <p>{veryLongText}</p>
  </div>
</div>
```

✅ **Proper flex text containment**
```tsx
<div className="flex min-w-0">
  <div className="max-w-[80%] min-w-0">
    <p className="break-words overflow-wrap-anywhere">{veryLongText}</p>
  </div>
</div>
```

### Message Component Text Wrapping

**Chat message bubbles require multi-level constraints:**
```tsx
{/* Root motion div */}
<motion.div className="group max-w-3xl mx-auto w-full min-w-0">
  {/* Flex row with avatar */}
  <div className="flex gap-4 min-w-0">
    <Avatar className="shrink-0" /> {/* Fixed size */}
    
    {/* Message column - critical constraints */}
    <div className="max-w-[85%] md:max-w-[75%] min-w-0">
      {/* Message bubble */}
      <div className="px-4 py-3 rounded-2xl max-w-full min-w-0">
        {/* Text content */}
        <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere max-w-full min-w-0">
          {message.content}
        </div>
      </div>
    </div>
  </div>
</motion.div>
```

**Why each level matters:**
- `motion.div`: `w-full min-w-0` - Enables proper flex shrinking at root
- `flex.div`: `min-w-0` - Allows children to shrink below content size
- `column.div`: `max-w-[85%] min-w-0` - Constrains message width AND enables shrinking
- `bubble.div`: `max-w-full min-w-0` - Respects parent constraints
- `content.div`: `break-words overflow-wrap-anywhere` - Handles long text

### SafeArea & Viewport Edge Handling

**Mobile notch/dynamic island support:**
```tsx
{/* Top safe area */}
<header className="safe-top h-14"> {/* padding-top: env(safe-area-inset-top) */}

{/* Bottom navigation safe area */}
<nav className="safe-bottom"> {/* padding-bottom: env(safe-area-inset-bottom) */}

{/* In content, add bottom padding for fixed nav */}
{isMobile && <div className="h-24" />} {/* Tab bar height + padding */}
```

CSS support (defined in `index.css`):
```css
.safe-top { padding-top: var(--sat); }
.safe-bottom { padding-bottom: var(--sab); }
```

---

## Generative UI Integration

The backend (Phase 7c) generates interactive component specifications alongside chat messages. The frontend MUST render these as native React components.

**Contract:**
- **Trigger**: `QueryResponse` contains a `component` field.
- **Data Structure**:
  ```json
  {
    "component_type": "mood_slider | multi_slider | hypothesis_probe",
    "component_id": "uuid",
    "interaction_time_ms": 0,
    "mood_slider": { "question": "...", "min": 1, "max": 10 },
    "multi_slider": { "sliders": [{ "id": "mood", "label": "Mood" }, ...] }
  }
  ```
- **Submission**:
  - Frontend renders the component (e.g., `<MoodSlider />`).
  - User interacts -> Frontend POSTs to `/api/v1/chat/component/submit`.
  - Payload: `{ "component_id": "...", "component_type": "...", "slider_value": 7 }`

**Component Types to Implement:**
1.  **MoodSlider**: Single value (1-10) with label.
2.  **MultiSlider**: Multiple sliders (Mood, Energy, Anxiety) in a group.
3.  **HypothesisProbe**: Binary or Likert scale questions for Genesis refinement.

**Guidelines:**
- Components should feel like a seamless part of the chat stream.
- Use animations for appearing/disappearing.
- Disable interaction after submission (optimistic UI).