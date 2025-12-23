# Dashboard V3 - Implementation Prompts

**Created:** December 2025
**Purpose:** Parallel-safe prompts for implementing dashboard-v3 changes
**Total Prompts:** 6 (run in order, prompts 1-4 can run in parallel)

---

## Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: PARALLEL EXECUTION (Prompts 1-4)                      │
│  Run these 4 prompts simultaneously in separate sessions        │
├─────────────────────────────────────────────────────────────────┤
│  Prompt 1: SessionCard.tsx (Breakthrough Ribbon)                │
│  Prompt 2: ProgressPatternsCard.tsx (Modal Conversion)          │
│  Prompt 3: Font Unification (ToDoCard, NotesGoalsCard, PP Card) │
│  Prompt 4: TimelineSidebar.tsx (Complete Overhaul)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: INTEGRATION (Prompt 5)                                │
│  Run AFTER Phase 1 completes - requires state lifting           │
├─────────────────────────────────────────────────────────────────┤
│  Prompt 5: Timeline ↔ SessionCardsGrid Integration              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: VERIFICATION (Prompt 6)                               │
│  Run LAST - validates all changes work together                 │
├─────────────────────────────────────────────────────────────────┤
│  Prompt 6: Final Verification & Bug Check                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Ownership (Prevents Conflicts)

| Prompt | Primary Files | Read-Only Dependencies |
|--------|---------------|------------------------|
| 1 | `SessionCard.tsx` | `types.ts`, `mockData.ts` |
| 2 | `ProgressPatternsCard.tsx` | `utils.ts`, `mockData.ts` |
| 3 | `ToDoCard.tsx`, `NotesGoalsCard.tsx` | - |
| 4 | `TimelineSidebar.tsx`, `types.ts` (add duration field) | `mockData.ts` |
| 5 | `page.tsx`, `SessionCardsGrid.tsx`, `TimelineSidebar.tsx` | All above |
| 6 | ALL (read + verify) | - |

---

## PROMPT 1: Breakthrough Ribbon Redesign

**File:** `frontend/app/patient/dashboard-v3/components/SessionCard.tsx`
**Estimated Time:** 15-20 minutes
**Complexity:** Medium

### Context
I'm working on the TherapyBridge Dashboard v3. The session cards have a "Breakthrough" indicator for milestone sessions, but it currently uses a diagonal corner ribbon that overlaps with card content.

### Task
Redesign the breakthrough ribbon to be a **horizontal banner at the top of the card** instead of a diagonal corner ribbon.

### Requirements

1. **Remove the diagonal ribbon** (the `rotate-45` styled element)

2. **Create a horizontal top banner** that:
   - Spans the full width of the card
   - Sits at the very top of the card (inside the border-radius)
   - Does NOT overlap with any text content below it
   - Has a star icon on the left
   - Shows a shortened version of the milestone title (e.g., "Self-compassion discovery")

3. **Banner styling:**
   - Background: Gradient from amber-400 to amber-500 (dark mode: amber-500 to amber-600)
   - Height: ~28-32px
   - Text: 12px, semibold, amber-900
   - Star icon: Sparkles or Star from lucide-react, amber-900
   - Border-radius: Match card's top corners (so banner blends with card edge)

4. **Milestone text logic:**
   - Pull from `session.milestone.title`
   - If title is longer than ~30 characters, truncate with ellipsis
   - Format: "⭐ {shortened milestone title}"

5. **Card layout adjustment:**
   - The banner should push all other content down
   - Ensure metadata row, topics, strategy, and actions all render below the banner without overlap
   - Non-milestone cards should NOT have extra top padding (maintain current spacing)

6. **Keep the inline star indicator** in the metadata row for redundancy (it's accessible and helps users scanning)

### Current Code Location
The diagonal ribbon is at lines 53-68 in SessionCard.tsx:
```tsx
{/* Milestone Corner Ribbon - positioned inside card, top-right corner */}
{session.milestone && (
  <div className="absolute top-0 right-0 overflow-hidden w-24 h-24 pointer-events-none">
    ...
  </div>
)}
```

### Expected Outcome
- Milestone sessions show a clean horizontal banner at top with star + milestone title
- No text overlap or visual collision
- Smooth appearance in both light and dark modes
- Maintains accessibility (already has aria-label mentioning breakthrough)

### Testing
After implementation:
1. Verify milestone cards (Dec 10, Nov 26, Nov 12, etc.) show the banner correctly
2. Verify non-milestone cards have NO banner and normal spacing
3. Check dark mode renders properly
4. Ensure card click still opens session detail

---

## PROMPT 2: Progress Patterns Modal Conversion

**File:** `frontend/app/patient/dashboard-v3/components/ProgressPatternsCard.tsx`
**Estimated Time:** 25-30 minutes
**Complexity:** High

### Context
I'm working on the TherapyBridge Dashboard v3. The Progress Patterns card currently expands to a full-screen sidebar layout (`fixed inset-4`), but it should expand to a **centered modal** like the other cards (ToDoCard, NotesGoalsCard, TherapistBridgeCard).

### Task
Convert the Progress Patterns expanded state from full-screen sidebar to a centered modal with all 4 metrics stacked vertically.

### Requirements

1. **Remove the full-screen sidebar layout** (the `fixed inset-4` with sidebar navigation)

2. **Create a centered modal** matching other cards:
   ```tsx
   className="fixed w-[800px] max-h-[85vh] bg-white dark:bg-[#2a2435] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-gray-300 dark:border-gray-600"
   style={{
     top: '50%',
     left: '50%',
     transform: 'translate(-50%, -50%)',
     margin: 0
   }}
   ```

3. **Modal content layout (stacked vertically, scrollable):**
   - Header: "Progress Patterns" title with close X button
   - All 4 metrics displayed in collapsible sections (like PAGE_LAYOUT_ARCHITECTURE.md describes):
     - Mood Trend
     - Homework Impact
     - Session Consistency
     - Strategy Effectiveness
   - Each section has:
     - Collapsible header with chevron indicator
     - Larger chart (250px height)
     - Detailed insight text below chart

4. **Collapsible section behavior:**
   - Default: First section (Mood Trend) open, others collapsed
   - Click header to toggle open/close
   - Smooth animation on collapse/expand
   - ChevronDown icon rotates when section is open

5. **Use existing `modalVariants` and `backdropVariants`** from utils.ts for animation consistency

6. **Maintain accessibility:**
   - Keep the `useModalAccessibility` hook
   - Keep `role="dialog"`, `aria-modal="true"`, `aria-labelledby`

7. **Update z-index:**
   - Change backdrop from `z-40` to `z-[1000]` (match other cards)
   - Change modal from `z-50` to `z-[1001]` (match other cards)

### Current Code Location
The full-screen sidebar is at lines 289-402. The key parts to replace:
- `className="fixed inset-4 md:inset-10 z-50 ...` → centered modal
- The sidebar navigation div → collapsible sections
- Keep the chart rendering logic (`renderChart` function)

### Expected Outcome
- Click Progress Patterns card → opens centered modal (not full-screen)
- Modal shows all 4 metrics in collapsible sections
- Charts render correctly at larger size
- Dark mode works properly
- Escape key and click-outside close the modal

### Testing
After implementation:
1. Click the Progress Patterns card → verify centered modal opens
2. Verify all 4 metrics are visible (with scroll if needed)
3. Click each section header → verify collapse/expand works
4. Verify charts render correctly
5. Test dark mode
6. Test Escape key closes modal
7. Test click outside closes modal

---

## PROMPT 3: Font Unification (font-light)

**Files:**
- `frontend/app/patient/dashboard-v3/components/ToDoCard.tsx`
- `frontend/app/patient/dashboard-v3/components/NotesGoalsCard.tsx`
- `frontend/app/patient/dashboard-v3/components/ProgressPatternsCard.tsx` (compact card only)

**Estimated Time:** 15-20 minutes
**Complexity:** Low

### Context
I'm working on the TherapyBridge Dashboard v3. The TherapistBridgeCard uses `font-light` styling throughout, giving it a calm, therapy-appropriate aesthetic. The other middle-row cards (To-Do, Notes/Goals, Progress Patterns) use heavier font weights that feel inconsistent.

### Task
Update the font styling in ToDoCard, NotesGoalsCard, and ProgressPatternsCard (compact state only) to use `font-light` like TherapistBridgeCard.

### Requirements

1. **ToDoCard (compact card only):**
   - Card title "To-Do": Change from `font-medium` to `font-light`
   - Task text: Change from default to `font-light`
   - Keep the progress bar and percentage text as-is

2. **NotesGoalsCard (compact card only):**
   - Card title "Notes / Goals": Keep `font-semibold` for the serif font (Crimson Pro)
   - Body text and achievement bullets: Change to `font-light`
   - "Current focus:" label: Keep `font-medium`
   - Focus items text: Change to `font-light`

3. **ProgressPatternsCard (compact card only):**
   - Metric title in header: Change from `font-semibold` to `font-light`
   - Description text: Already uses `font-medium`, change to `font-light`
   - Insight pill text: Change from `font-medium` to `font-light`
   - Keep chart labels and navigation controls as-is

4. **DO NOT change:**
   - Expanded modal styling (keep modals with their current typography)
   - TherapistBridgeCard (already uses font-light)
   - Header components
   - Session cards

### Specific Class Changes

**ToDoCard.tsx:**
- Line 45: `font-medium` → `font-light`
- Lines 84-89: Add `font-light` to task text spans

**NotesGoalsCard.tsx:**
- Line 42: Add `font-light` to paragraph text
- Lines 46-50: Add `font-light` to achievement list items
- Line 55: Add `font-light` to current focus items

**ProgressPatternsCard.tsx (compact only):**
- Line 204: `font-semibold` → `font-light`
- Line 207: `font-medium` → `font-light`
- Line 247: `font-medium` → `font-light`

### Expected Outcome
- All 3 middle-row cards have a consistent, light typography feel
- Matches the calm, therapy-appropriate aesthetic of TherapistBridgeCard
- Expanded modals retain their current (slightly heavier) typography for readability

### Testing
After implementation:
1. Visual comparison: All 4 middle-row cards should have similar font weight
2. Text remains readable in both light and dark modes
3. Hover effects still work
4. Click to expand still works

---

## PROMPT 4: Timeline Sidebar Complete Overhaul

**Files:**
- `frontend/app/patient/dashboard-v3/components/TimelineSidebar.tsx`
- `frontend/app/patient/dashboard-v3/lib/types.ts` (add duration field)
- `frontend/app/patient/dashboard-v3/lib/mockData.ts` (add duration to timeline data)

**Estimated Time:** 35-45 minutes
**Complexity:** High

### Context
I'm working on the TherapyBridge Dashboard v3. The Timeline sidebar needs to match the PAGE_LAYOUT_ARCHITECTURE.md specification more closely, with enhanced popovers and better visual design.

### Reference Architecture (from PAGE_LAYOUT_ARCHITECTURE.md)
```
Timeline Sidebar Popover should show:
- Session number + date
- Duration (e.g., "45 minutes")
- Mood with colored dot
- Topics discussed
- Strategy used
- Milestone info (if applicable)
- "View Full Session →" button that opens fullscreen session detail
```

### Task
Overhaul the Timeline sidebar to match the architecture specification.

### Requirements

1. **Update types.ts** - Add duration to TimelineEntry:
   ```typescript
   export interface TimelineEntry {
     sessionId: string;
     date: string;
     duration: string;  // ADD THIS - e.g., "45 min"
     topic: string;
     strategy: string;  // ADD THIS
     mood: MoodType;
     milestone?: Milestone;
   }
   ```

2. **Update mockData.ts** - Add duration and strategy to timelineData entries

3. **Enhanced Popover content:**
   ```
   ┌──────────────────────────────┐
   │  Session 9 - Dec 10         │
   │                              │
   │  Duration: 45 minutes        │
   │  Mood: ● Positive            │
   │                              │
   │  Topics:                     │
   │  • Self-worth exploration    │
   │  • Past relationships        │
   │                              │
   │  Strategy:                   │
   │  Laddering technique         │
   │                              │
   │  ⭐ Breakthrough:             │
   │  Self-compassion discovery   │
   │                              │
   │  [View Full Session →]       │
   └──────────────────────────────┘
   ```

4. **Popover styling improvements:**
   - Width: 280-300px
   - Padding: 16-20px
   - Section spacing: Clear visual separation between Duration/Mood, Topics, Strategy, Milestone
   - "View Full Session" button: Styled as a subtle button, not just text link
   - Arrow/pointer: Should point to the timeline entry (already partially implemented)

5. **"View Full Session" button behavior:**
   - For now, just close the popover when clicked
   - Add a prop/callback that will be used later for integration (Phase 2)
   - Button should accept an `onViewSession?: (sessionId: string) => void` callback

6. **Timeline compact state improvements:**
   - Keep the gradient connector line
   - Keep mood-colored dots and star icons for milestones
   - Add subtle hover effect on entries (already present, but enhance if needed)

7. **Maintain accessibility:**
   - Keep keyboard navigation support
   - Popover should be focusable and closeable with Escape

### Current Popover (lines 81-144)
The current popover shows: Session number, date, mood, topic, milestone. It's missing: duration, strategy, and a proper "View Full Session" button.

### Expected Outcome
- Timeline popover matches architecture spec with all fields
- Visual design is polished and consistent with dashboard theme
- "View Full Session" button is present and ready for integration
- Duration and strategy data available in timeline entries

### Testing
After implementation:
1. Click each timeline entry → verify popover shows all fields
2. Verify milestone entries show the breakthrough section
3. Verify non-milestone entries don't show breakthrough section
4. Test "View Full Session" button closes popover (integration comes later)
5. Test dark mode rendering
6. Test Escape key closes popover

---

## PROMPT 5: Timeline ↔ Session Integration

**Files:**
- `frontend/app/patient/dashboard-v3/page.tsx`
- `frontend/app/patient/dashboard-v3/components/SessionCardsGrid.tsx`
- `frontend/app/patient/dashboard-v3/components/TimelineSidebar.tsx`

**Estimated Time:** 25-30 minutes
**Complexity:** High

### Context
I'm working on the TherapyBridge Dashboard v3. The Timeline sidebar now has a "View Full Session" button in its popover (from Prompt 4). We need to integrate it so clicking this button opens the SessionDetail fullscreen view.

### Prerequisite
**PROMPT 4 MUST BE COMPLETED FIRST** - The TimelineSidebar should have the `onViewSession` callback prop ready.

### Task
Lift state to page.tsx and wire up Timeline → Session integration.

### Requirements

1. **page.tsx - Add state management:**
   ```tsx
   // Add state for which session is being viewed in fullscreen
   const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
   ```

2. **page.tsx - Pass callback to TimelineSidebar:**
   ```tsx
   <TimelineSidebar
     onViewSession={(sessionId) => setSelectedSessionId(sessionId)}
   />
   ```

3. **page.tsx - Pass selectedSessionId to SessionCardsGrid:**
   ```tsx
   <SessionCardsGrid
     externalSelectedSessionId={selectedSessionId}
     onSessionClose={() => setSelectedSessionId(null)}
   />
   ```

4. **SessionCardsGrid.tsx - Accept external session selection:**
   - Add props: `externalSelectedSessionId?: string | null` and `onSessionClose?: () => void`
   - When `externalSelectedSessionId` is set, find that session and open SessionDetail
   - When SessionDetail closes, call both internal close AND `onSessionClose` if provided

5. **TimelineSidebar.tsx - Wire up the callback:**
   - Accept `onViewSession?: (sessionId: string) => void` prop
   - When "View Full Session" button is clicked:
     1. Close the popover
     2. Call `onViewSession(entry.sessionId)`

6. **Scroll-to-card behavior (from architecture doc):**
   - When clicking a timeline entry (not "View Full Session" button), scroll the session card into view
   - Add a `scrollToSession` function that uses `document.getElementById()` and `scrollIntoView({ behavior: 'smooth' })`
   - Add `id={`session-${session.id}`}` to session cards in SessionCardsGrid

### Architecture Reference
From PAGE_LAYOUT_ARCHITECTURE.md:
- "Clicking entry scrolls to corresponding session card in grid"
- "'View Full Session' button opens fullscreen session detail"

These are TWO different behaviors:
- Click timeline entry → scroll to card
- Click "View Full Session" button → open fullscreen detail

### Expected Outcome
- Click timeline entry → page scrolls to that session card
- Click "View Full Session" in popover → opens fullscreen SessionDetail
- State is properly managed at page.tsx level
- No prop drilling issues

### Testing
After implementation:
1. Click timeline entry for "Dec 10" → page scrolls to Dec 10 session card
2. Click "View Full Session" button → SessionDetail fullscreen opens
3. Close SessionDetail → returns to dashboard normally
4. Test multiple timeline entries
5. Test that session card click still works independently

---

## PROMPT 6: Final Verification & Bug Check

**Files:** ALL dashboard-v3 files
**Estimated Time:** 20-25 minutes
**Complexity:** Medium (testing, not coding)

### Context
I've completed implementing changes to the TherapyBridge Dashboard v3:
1. Breakthrough ribbon redesign (horizontal banner)
2. Progress Patterns modal conversion (centered modal)
3. Font unification (font-light across cards)
4. Timeline complete overhaul (enhanced popover)
5. Timeline ↔ Session integration (scroll + view fullscreen)

### Task
Verify all changes work correctly together, check for bugs, and fix any issues.

### Verification Checklist

#### 1. Breakthrough Ribbon (SessionCard.tsx)
- [ ] Milestone sessions (Dec 10, Nov 26, Nov 12, Oct 22) show horizontal banner
- [ ] Banner displays star icon + shortened milestone title
- [ ] No text overlap with content below banner
- [ ] Non-milestone sessions have NO banner
- [ ] Dark mode renders correctly
- [ ] Card click opens session detail

#### 2. Progress Patterns Modal (ProgressPatternsCard.tsx)
- [ ] Click card → centered modal opens (NOT fullscreen sidebar)
- [ ] All 4 metrics shown in collapsible sections
- [ ] Mood Trend section is expanded by default
- [ ] Clicking section headers toggles expand/collapse
- [ ] Charts render correctly in modal
- [ ] Escape key closes modal
- [ ] Click outside closes modal
- [ ] Dark mode renders correctly

#### 3. Font Unification
- [ ] ToDoCard compact: Title and task text use font-light
- [ ] NotesGoalsCard compact: Body text uses font-light
- [ ] ProgressPatternsCard compact: Title and insight use font-light
- [ ] All 4 middle-row cards have consistent typography
- [ ] Text remains readable
- [ ] Modals still have appropriate (heavier) typography

#### 4. Timeline Overhaul (TimelineSidebar.tsx)
- [ ] Popover shows: Duration, Mood, Topics, Strategy, Milestone (if applicable)
- [ ] "View Full Session" button is visible and styled
- [ ] Dark mode renders correctly
- [ ] Escape closes popover

#### 5. Timeline Integration
- [ ] Click timeline entry → scrolls to session card in grid
- [ ] Click "View Full Session" → opens SessionDetail fullscreen
- [ ] Closing SessionDetail returns to dashboard
- [ ] No state bugs (can repeat actions multiple times)

#### 6. General Health Checks
- [ ] No console errors in browser developer tools
- [ ] No TypeScript errors (run `npm run build`)
- [ ] All modals use z-index 1000/1001 (consistent)
- [ ] Only one modal/fullscreen open at a time
- [ ] Dark mode toggle works globally
- [ ] Page doesn't crash on any interaction

### Bug Fix Approach
If issues are found:
1. Identify the specific file and line causing the issue
2. Describe the expected vs actual behavior
3. Fix the issue
4. Re-verify that fix doesn't break other functionality

### Expected Outcome
- All 5 feature changes verified working
- Any bugs discovered are fixed
- Dashboard is stable and production-ready

### Output
After verification, provide:
1. Summary of all tests passed
2. Any bugs found and fixed
3. Any remaining issues or recommendations

---

## Quick Reference

### File Locations
```
frontend/app/patient/dashboard-v3/
├── page.tsx
├── components/
│   ├── SessionCard.tsx         # Prompt 1
│   ├── SessionCardsGrid.tsx    # Prompt 5
│   ├── ProgressPatternsCard.tsx # Prompt 2, 3
│   ├── ToDoCard.tsx            # Prompt 3
│   ├── NotesGoalsCard.tsx      # Prompt 3
│   ├── TherapistBridgeCard.tsx # Reference (font-light)
│   └── TimelineSidebar.tsx     # Prompt 4, 5
├── lib/
│   ├── types.ts                # Prompt 4
│   ├── mockData.ts             # Prompt 4
│   └── utils.ts
└── hooks/
    └── useModalAccessibility.ts
```

### Key Style Tokens
```
Colors (Light):
- Primary: #5AB9B4 (teal)
- Secondary: #B8A5D6 (lavender)
- Accent: #F4A69D (coral)
- Milestone: amber-400/500

Colors (Dark):
- Primary: #a78bfa (purple)
- Secondary: #c084fc (lighter purple)
- Background: #1a1625, #2a2435
- Border: #3d3548

Z-Index:
- Backdrop: z-[1000]
- Modal: z-[1001]
```

---

**End of Prompt Plan Document**
