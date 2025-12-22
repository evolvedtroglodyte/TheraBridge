# Dashboard v3 - TherapyBridge Patient Dashboard

Comprehensive patient dashboard with AI chat companion, session tracking, and therapy progress visualization.

---

## Overview

Full-featured therapy dashboard with 7 interactive components in a responsive grid layout. Features real-time API integration, dark mode support, and an immersive AI chat experience.

**Key Features:**
- Dobby AI chat companion (collapsed + fullscreen modes)
- Mixed timeline (therapy sessions + major life events)
- Session cards with mood tracking and reflections
- Progress patterns carousel with insights
- Notes, goals, and to-do tracking
- Direct therapist communication bridge

---

## Architecture

### State Management

**Lifted State Pattern:**
- `isChatFullscreen` - Shared between Header "Ask AI" button and AIChatCard
- `selectedSessionId` - Shared between Timeline and SessionCardsGrid for navigation
- `SessionDataProvider` - Global context for real API data across all components

**Why this matters:** State lifting enables cross-component communication (e.g., clicking timeline entry scrolls to session card, clicking "Ask AI" in header opens fullscreen chat).

### Data Flow

```
SessionDataProvider (API layer)
    ├── TimelineSidebar (unified timeline with major events)
    ├── SessionCardsGrid (session summaries + reflections)
    ├── NotesGoalsCard (therapy notes + goals)
    ├── ProgressPatternsCard (insights carousel)
    └── TherapistBridgeCard (therapist profile + quick message)
```

---

## Dobby AI Chat

Complete redesign of the AI chatbot interface with dual-mode support, responsive layouts, and polished UX.

### Features

#### 1. Dual Mode Toggle (AI / Therapist)
**Current Implementation:** UI-only toggle that changes placeholder text.

- **AI Mode:** "Ask Dobby anything..." - Default state
- **Therapist Mode:** "Send a message to your therapist..." - Placeholder change only

**Backend Status:** Therapist mode backend integration is **not yet implemented**. Mode is sent to `/api/chat` endpoint but no routing/notification logic exists.

```typescript
// Mode state (AIChatCard.tsx, FullscreenChat/index.tsx)
const [mode, setMode] = useState<'ai' | 'therapist'>('ai');

// Placeholder changes based on mode
placeholder={mode === 'ai' ? "Ask Dobby anything..." : "Send a message to your therapist..."}
```

#### 2. Therapist Button Styling
**Bug Avoided:** Button was turning orange on hover instead of only when active.

**Fix:** Conditional styling based on active state only:
```typescript
className={`... ${
  mode === 'therapist'
    ? 'bg-gradient-to-br from-[#F4A69D] to-[#E88B7E] text-white'  // Active: orange
    : isDark
      ? 'bg-[#2a2535] text-[#888] hover:bg-[#3a3545]'  // Inactive dark: gray
      : 'bg-[#F0EFEB] text-[#666] hover:bg-[#E5E2DE]'  // Inactive light: gray
}`}
```

#### 3. Message Avatars Always Have Faces
**Bug Avoided:** Initially used different icons per mode, causing faceless geometric icons.

**Fix:** Always use `DobbyLogo` component (with face) regardless of mode:
```typescript
// Collapsed chat - 32px (15% larger than original 28px)
{msg.role === 'assistant' && (
  <DobbyLogo size={32} />
)}

// Fullscreen chat - 37px (15% larger than original 32px)
{msg.role === 'assistant' && (
  <DobbyLogo size={37} />
)}
```

#### 4. Logo Hides After 2 User Messages
**Logic:** Count user messages specifically, hide logo when >= 2, but keep "DOBBY" text visible and clickable.

```typescript
const userMessageCount = messages.filter(m => m.role === 'user').length;
const shouldHideLogo = userMessageCount >= 2;

// Animated logo hide
<AnimatePresence>
  {!shouldHideLogo && (
    <motion.div
      initial={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.3 }}
    >
      <DobbyLogo size={50} />
    </motion.div>
  )}
</AnimatePresence>

// Text always visible
<span className="font-mono text-lg font-medium tracking-[4px] uppercase">
  DOBBY
</span>
```

#### 5. Scroll-to-Top Only (Removed Scroll-to-Bottom)
**File:** `FullscreenChat/index.tsx`

```typescript
const handleLogoClick = () => {
  if (messagesContainerRef.current) {
    messagesContainerRef.current.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
};
```

#### 6. Header Icons Moved to Left Edge
**File:** `Header.tsx`

**Layout:** Flexbox with left icons, centered nav, empty right spacer for balance.

```typescript
<header className="... flex items-center">
  {/* Left: Theme toggle + Home - flush to edge */}
  <div className="flex items-center gap-2 pl-3">
    <button onClick={toggleTheme}>...</button>
    <button onClick={handleHomeClick}>...</button>
  </div>

  {/* Center: Navigation */}
  <div className="flex-1 flex items-center justify-center">
    <nav>...</nav>
  </div>

  {/* Right: Empty spacer for visual balance */}
  <div className="w-[84px] pr-3" />
</header>
```

#### 7. Theme Toggle Position in Fullscreen
**File:** `FullscreenChat/index.tsx`

Positioned next to sidebar icon (72px offset for sidebar width):
```typescript
<div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center gap-2 ml-[72px]">
  <button onClick={toggleTheme}>...</button>
</div>
```

#### 8. Card Height Increase (25%)
**Files:** `NotesGoalsCard.tsx`, `AIChatCard.tsx`

Original: 420px → New: 525px
```typescript
className="... h-[525px] ..."
```

---

## Timeline Enhancement

Comprehensive timeline system with mixed events (therapy sessions + major life events), search, and export functionality.

**Key Features:**
- Mixed timeline: therapy sessions + major life events
- Visual distinction: mood-colored dots (sessions) vs purple diamonds (events)
- Search across topics, strategies, summaries
- PDF export + shareable link generation
- Reflection add/edit for both sessions and events

**Files:**
- `TimelineSidebar.tsx` - Mixed timeline with compact/expanded modes
- `MajorEventModal.tsx` - Major event detail modal
- `ExportDropdown.tsx` - Export menu (PDF + share link)
- `lib/timelineSearch.ts` - Search/filter utilities
- `lib/exportTimeline.ts` - PDF generation + share link

**Test Coverage:** 42 E2E tests across 4 Playwright spec files

---

## Component Reference

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Dobby AI Chat** |
| AIChatCard | `components/AIChatCard.tsx` | Collapsed Dobby chat in dashboard |
| FullscreenChat | `components/FullscreenChat/index.tsx` | Fullscreen chat modal |
| DobbyLogo | `components/DobbyLogo.tsx` | Dobby icon with face |
| DobbyLogoGeometric | `components/DobbyLogoGeometric.tsx` | Geometric logo for mode toggle |
| HeartSpeechIcon | `components/HeartSpeechIcon.tsx` | Heart speech bubble icon |
| **Timeline** |
| TimelineSidebar | `components/TimelineSidebar.tsx` | Mixed timeline (sessions + events) |
| MajorEventModal | `components/MajorEventModal.tsx` | Major event detail modal |
| ExportDropdown | `components/ExportDropdown.tsx` | Export menu dropdown |
| **Sessions** |
| SessionCardsGrid | `components/SessionCardsGrid.tsx` | Grid of session cards |
| SessionCard | `components/SessionCard.tsx` | Individual session card |
| **Dashboard Cards** |
| NotesGoalsCard | `components/NotesGoalsCard.tsx` | Notes/Goals card |
| ToDoCard | `components/ToDoCard.tsx` | To-do list card |
| ProgressPatternsCard | `components/ProgressPatternsCard.tsx` | Progress insights carousel |
| TherapistBridgeCard | `components/TherapistBridgeCard.tsx` | Therapist profile + quick message |
| **Layout** |
| Header | `components/Header.tsx` | Dashboard top navigation |
| DashboardSkeleton | `components/DashboardSkeleton.tsx` | Loading skeleton |

---

## Key Patterns Used

### 1. State Separation
Mode state controls behavior (placeholder, button styling) but NOT visual elements (avatars stay consistent).

### 2. Conditional Styling
Used ternary operators for theme-aware and state-aware styling:
```typescript
className={condition ? 'style-a' : isDark ? 'dark-style' : 'light-style'}
```

### 3. Framer Motion for Animations
- `AnimatePresence` for exit animations
- `motion.div` with opacity/scale transitions
- Spring animations for modals

### 4. User Message Counting
```typescript
messages.filter(m => m.role === 'user').length
```
More precise than counting all messages for UI logic triggers.

---

## Running the Project

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000/patient/dashboard-v3
```

---

## Build Verification

All changes verified with `npm run build` - no errors or warnings.

---

## Test Coverage

**Playwright E2E Tests:**
- Timeline mixed events: 8 tests
- Major event modal: 14 tests
- Timeline search: 11 tests
- Timeline export: 9 tests
- Card styling: Font alignment + text overflow
- Modal positioning: Center alignment verification

**Total:** 42+ E2E tests

**Run tests:**
```bash
npm run test:e2e
```

---

## API Integration Status

**Connected:**
- Session data (via SessionDataProvider)
- Patient data (name, therapist info)
- Timeline data (sessions + major events)

**Not Connected (Mocked):**
- Dobby AI chat responses (uses fallback messages)
- Therapist mode backend (UI-only, no routing)
- Real-time updates (refresh required)

**Feature Flags:**
- `NEXT_PUBLIC_USE_REAL_API` - Toggle real vs mock backend (see root README)

---

## Future Enhancements

- [ ] Implement therapist mode backend (message routing, notifications)
- [ ] Add real-time updates via WebSocket
- [ ] Implement chat history persistence
- [ ] Add voice input for Dobby chat
- [ ] Export timeline to multiple formats (CSV, JSON)
- [ ] Add timeline filtering by date range
- [ ] Implement collaborative reflection editing

---

## Design System

**Colors:**
- Primary (Light): `#5AB9B4` (teal)
- Primary (Dark): `#B794D4` (purple)
- Therapist Mode: `#F4A69D` → `#E88B7E` (orange gradient)
- Background (Light): `#F8F7F4` (warm cream)
- Background (Dark): `#1a1625` (deep purple-black)

**Typography:**
- Mono: System mono stack (Dobby branding)
- Sans: DM Sans (body text)
- Serif: Crimson Pro (headings)

**Spacing:**
- Card height: 525px (25% increase from original 420px)
- Logo sizes: 32px (collapsed), 37px (fullscreen), 50px (header)
- Grid gap: 1.5rem (24px)

---

*Last updated: 2025-12-21*
