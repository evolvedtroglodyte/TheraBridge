# Timeline Enhancement Implementation Plan (Revised)

## Overview

Transform the timeline from a "session-only viewer" into a "patient journey narrative" that includes:
1. **Sessions** (from audio transcripts) - with milestones/breakthroughs highlighted
2. **Major Events** (from chatbot) - AI-detected significant life events, patient-confirmed

Key features: Search functionality, export (PDF + shareable link), reflection capability on major events.

---

## Scope Summary

**Timeline Event Types (2 total):**

| Type | Source | Highlighted? | Click Action |
|------|--------|--------------|--------------|
| Session | Audio transcript | Milestones highlighted (existing) | Opens session detail |
| Major Event | Chatbot (AI-detected, patient-confirmed) | Always highlighted | Opens event modal |

**Removed from original plan:**
- ~~Weekly summaries~~
- ~~Manual patient input~~
- ~~Chatbot breakthroughs~~ (breakthroughs only from audio transcripts)
- ~~Filter tabs~~ (only 2 event types, not enough variety)
- ~~Mood overlay~~ (removed per user request)
- ~~Phase clustering~~ (removed per user request)

**Kept:**
- Search functionality
- Export (PDF + shareable link)
- Reflection on major events

---

## Phase 1: Data Foundation & Types

**Goal:** Establish the data models and mock data for timeline events.

### 1.1 Update Type Definitions (`lib/types.ts`)

```typescript
// Timeline event types
type TimelineEventType = 'session' | 'major_event';

// Base timeline event (shared fields)
interface BaseTimelineEvent {
  id: string;
  date: string;           // Display date (e.g., "Dec 17")
  timestamp: Date;        // For sorting
  eventType: TimelineEventType;
}

// Session event (extends existing TimelineEntry)
interface SessionTimelineEvent extends BaseTimelineEvent {
  eventType: 'session';
  sessionId: string;
  duration: string;
  topic: string;
  strategy: string;
  mood: MoodType;
  milestone?: Milestone;  // Breakthrough/milestone from transcript
}

// Major event (from chatbot, AI-detected)
interface MajorEventEntry extends BaseTimelineEvent {
  eventType: 'major_event';
  title: string;
  summary: string;        // AI-generated context summary
  chatContext: string;    // Summarized chat context (not full conversation)
  relatedSessionId?: string;  // Optional link to related session
  confirmedByPatient: boolean;
  reflection?: string;    // Patient-added reflection
}

// Union type for all timeline events
type TimelineEvent = SessionTimelineEvent | MajorEventEntry;
```

### 1.2 Create Mock Data for Major Events (`lib/mockData.ts`)

Add 3-4 major events that integrate with the existing session timeline:

**Example mock major events:**
1. "Got promoted at work" - Dec 14 (between sessions, relates to work stress sessions)
2. "Had difficult conversation with mother" - Nov 22 (relates to boundary work)
3. "Started daily meditation practice" - Nov 8 (relates to coping strategies)

**Files to modify:**
- `lib/types.ts` - Add new type definitions
- `lib/mockData.ts` - Add major event mock data

**Estimated changes:** ~80 lines

---

## Phase 2: Major Event Modal Component

**Goal:** Create a modal for displaying major events with reflection capability.

### 2.1 Create `MajorEventModal.tsx`

**Modal Contents:**
- Title (prominent, top)
- Date
- AI-generated summary
- Context snippet (from chatbot conversation)
- Related session link (if applicable) - click navigates to session
- Reflection section:
  - If no reflection: Text area + "Save Reflection" button
  - If has reflection: Display text + "Edit" button

**Visual Design:**
- Consistent with existing card modals (same animation, backdrop, close behavior)
- Distinctive icon: Flag or diamond (differentiates from session stars)
- Accent color: Purple/violet (differentiates from session teal/mood colors)

### 2.2 Accessibility

- Focus trap
- Escape to close
- Keyboard navigation
- ARIA labels

**Files to create:**
- `components/MajorEventModal.tsx`

**Estimated changes:** ~150 lines

---

## Phase 3: Update TimelineSidebar for Mixed Events

**Goal:** Modify sidebar to display both sessions and major events.

### 3.1 Visual Hierarchy

| Event Type | Timeline Indicator | Color |
|------------|-------------------|-------|
| Session | Mood-colored dot | Green/Blue/Rose (existing) |
| Session + Milestone | Amber star | Amber glow (existing) |
| Major Event | Purple diamond/flag | Purple (#a78bfa) |

### 3.2 Click Behavior

```
Session → Opens session detail (existing behavior)
Major Event → Opens MajorEventModal (new)
```

### 3.3 Compact Entry Display

**Session (existing):**
- Date, topic (truncated), mood indicator

**Major Event (new):**
- Date, title (truncated), purple diamond icon

### 3.4 Sorting

All events sorted chronologically by `timestamp` (newest first or oldest first based on current behavior).

**Files to modify:**
- `components/TimelineSidebar.tsx`

**Estimated changes:** ~80 lines modified

---

## Phase 4: Enhanced Expanded Timeline

**Goal:** Add search functionality and export to the fullscreen timeline.

### 4.1 Search Bar

**Location:** Top of expanded timeline modal, below header

**Features:**
- Text input with search icon (left)
- Clear button (right, visible when text present)
- Placeholder: "Search sessions and events..."
- Debounced search (300ms delay)

**Search targets:**
- Session: topic, strategy, milestone title
- Major Event: title, summary

**Empty state:** "No results found for '[query]'"

### 4.2 Export Button

**Location:** Top-right of expanded timeline, next to close button

**Dropdown options:**
1. "Download PDF Summary"
2. "Copy Shareable Link"

### 4.3 Layout Structure (Revised)

```
┌─────────────────────────────────────────────────┐
│  Timeline                    [Export ▼] [X]     │
├─────────────────────────────────────────────────┤
│  [🔍 Search sessions and events...]             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ◆ Dec 14 - Major Event: Got promoted...       │
│  ● Dec 10 - Session: Self-worth, Past...  ⭐   │
│  ◆ Nov 22 - Major Event: Difficult conv...     │
│  ● Nov 19 - Session: Depression, Isolation     │
│  ...                                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Files to modify:**
- `components/TimelineSidebar.tsx` (expanded modal section)

**New utility file:**
- `lib/timelineSearch.ts` - Search filtering logic

**Estimated changes:** ~120 lines

---

## Phase 5: Export Functionality

**Goal:** Enable PDF export and shareable link generation.

### 5.1 Export Dropdown Component

Simple dropdown with two options:
- Download PDF Summary
- Copy Shareable Link

### 5.2 PDF Generation

**Library:** `html2pdf.js` (lightweight, client-side)

**PDF Contents:**
1. **Header:** "My Therapy Journey" + date range
2. **Summary Stats:** Total sessions, milestones count, major events count
3. **Timeline Entries:** Chronological list
   - Sessions: Date, topic, strategy, milestone (if any)
   - Major Events: Date, title, summary
4. **Footer:** Generated date, TherapyBridge branding

### 5.3 Shareable Link

**For mock implementation:**
- Generate a mock shareable URL
- Copy to clipboard
- Show success toast: "Link copied to clipboard"

**Note:** Full shareable link requires backend (deferred to future).

**Files to create:**
- `lib/exportTimeline.ts` - PDF generation + share link logic
- `components/ExportDropdown.tsx` - Dropdown UI

**Dependencies to add:**
- `html2pdf.js`

**Estimated changes:** ~150 lines

---

## Phase 6: Integration & Polish

**Goal:** Wire everything together, ensure smooth UX.

### 6.1 State Management Updates

Update data flow to provide unified timeline:
- Merge sessions + major events into single sorted array
- Provide to TimelineSidebar

### 6.2 Modal State Management

Track which modal is open:
- `selectedSessionId` (existing) → session detail
- `selectedMajorEventId` (new) → major event modal

### 6.3 Reflection Persistence

For mock: Store reflections in local state (will be backend-persisted later).

### 6.4 Animation Consistency

- Major event modal uses same spring animation as other modals
- Search results fade in/out smoothly
- Export dropdown uses existing dropdown patterns

### 6.5 Accessibility Audit

- All new interactive elements keyboard accessible
- Screen reader announcements for search results
- Focus management between modals

**Files to modify:**
- `page.tsx` - State management for major event modal
- `contexts/SessionDataContext.tsx` - Unified timeline data
- `lib/utils.ts` - Any new animation variants

**Estimated changes:** ~100 lines

---

## Phase 7: Playwright Testing

**Goal:** Comprehensive E2E tests for all new functionality.

### 7.1 Test File Structure

```
tests/
├── timeline-mixed-events.spec.ts    # Both event types display & interact correctly
├── timeline-major-event-modal.spec.ts # Major event modal functionality
├── timeline-search.spec.ts          # Search functionality
├── timeline-export.spec.ts          # Export functionality
└── timeline-reflection.spec.ts      # Reflection add/edit
```

### 7.2 Test Scenarios

**timeline-mixed-events.spec.ts:**
- [ ] Sidebar displays both sessions and major events
- [ ] Sessions show mood-colored dots
- [ ] Sessions with milestones show amber star
- [ ] Major events show purple diamond icon
- [ ] Events sorted chronologically
- [ ] Session click opens session detail
- [ ] Major event click opens major event modal
- [ ] Expanded timeline shows both event types

**timeline-major-event-modal.spec.ts:**
- [ ] Modal opens when major event clicked
- [ ] Modal displays title, date, summary
- [ ] Modal displays chat context
- [ ] Related session link works (if present)
- [ ] Modal close works (X button)
- [ ] Modal close works (backdrop click)
- [ ] Modal close works (Escape key)
- [ ] Focus trap works correctly
- [ ] Modal is centered on screen

**timeline-search.spec.ts:**
- [ ] Search bar visible in expanded timeline
- [ ] Typing filters results
- [ ] Search finds sessions by topic
- [ ] Search finds sessions by strategy
- [ ] Search finds major events by title
- [ ] Search finds major events by summary
- [ ] Clear button resets search
- [ ] Empty state shows when no results
- [ ] Search is debounced (no flicker)

**timeline-export.spec.ts:**
- [ ] Export button visible in expanded timeline
- [ ] Dropdown opens on click
- [ ] "Download PDF" option triggers download
- [ ] "Copy Link" option copies to clipboard
- [ ] Success feedback shown after copy
- [ ] Dropdown closes after selection

**timeline-reflection.spec.ts:**
- [ ] Reflection section visible in major event modal
- [ ] Empty state shows text area + save button
- [ ] Can type reflection text
- [ ] Save button saves reflection
- [ ] Saved reflection displays in modal
- [ ] Edit button allows modifying reflection
- [ ] Updated reflection persists

### 7.3 Visual Regression Tests

Capture screenshots for:
- Sidebar with mixed events (sessions + major events)
- Expanded timeline with search
- Major event modal (without reflection)
- Major event modal (with reflection)
- Export dropdown open
- Search with results
- Search empty state

**Estimated test files:** 5 files, ~400 lines total

---

## Implementation Order Summary

| Phase | Description | Dependencies | Est. Lines |
|-------|-------------|--------------|------------|
| 1 | Data Foundation & Types | None | ~80 |
| 2 | Major Event Modal | Phase 1 | ~150 |
| 3 | Update TimelineSidebar | Phase 1, 2 | ~80 |
| 4 | Search in Expanded Timeline | Phase 3 | ~120 |
| 5 | Export Functionality | Phase 4 | ~150 |
| 6 | Integration & Polish | All above | ~100 |
| 7 | Playwright Testing | All above | ~400 |

**Total estimated:** ~1080 lines of code

---

## Decision Points for User Input

During implementation, I'll pause for your input on:

1. **Phase 2:** Major event modal layout preferences (especially reflection UX)
2. **Phase 5:** PDF layout and branding decisions

---

## Success Criteria

- [ ] Timeline displays both sessions and major events
- [ ] Each event type has distinct visual identity
- [ ] Session milestones highlighted correctly
- [ ] Major event modal opens with full details
- [ ] Search filters timeline effectively
- [ ] Export produces useful PDF
- [ ] Shareable link copies to clipboard
- [ ] Reflections can be added to major events
- [ ] All features pass Playwright tests
- [ ] Accessibility standards met

---

## Notes

- All new features use mock data initially
- Backend integration points clearly marked for future
- Existing session functionality preserved
- Design consistent with current dashboard aesthetic
- Scope reduced from ~2000 lines to ~1080 lines
