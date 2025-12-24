# Font Standardization - SessionDetail & DeepAnalysis (PR #1)

**Plan Created:** 2025-01-06
**Status:** Planned
**Scope:** 3 files modified, 2 files deprecated
**Phased Rollout:** Phase 1A → Test → Phase 1B

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Typography Specifications](#typography-specifications)
3. [Phase 1A: SessionDetail & DeepAnalysis](#phase-1a-sessiondetail--deepanalysis)
4. [Phase 1B: Header & Timeline Deprecation](#phase-1b-header--timeline-deprecation)
5. [Testing Checklist](#testing-checklist)
6. [Success Criteria](#success-criteria)
7. [Iteration Points](#iteration-points)
8. [PR #2 Preview](#pr-2-preview)

---

## Executive Summary

### Problem
SessionDetail and DeepAnalysisSection currently use `system-ui` fonts instead of the dashboard standard (Inter + Crimson Pro). This creates visual inconsistency when navigating from dashboard cards (correct fonts) to session detail view (wrong fonts).

### Solution
Standardize fonts across all session-related components by:
1. Replacing `system-ui` with proper font families in SessionDetail and DeepAnalysisSection
2. Adding explicit font families to Header navigation buttons
3. Using TYPOGRAPHY constants (not inline imports) for easy iteration
4. Deprecating unused Timeline components

### Impact
- **Files Modified:** 3 (SessionDetail.tsx, DeepAnalysisSection.tsx, Header.tsx)
- **Files Deprecated:** 2 (TimelineSidebar.tsx, HorizontalTimeline.tsx)
- **Visual Consistency:** 100% alignment with dashboard design system
- **Developer Experience:** Single constant object per file for easy font adjustments

### Key Decisions
- **Font Family Constants:** File-local TYPOGRAPHY objects (camelCase, TypeScript `as const`)
- **Inline Styles:** Use `style={{ fontFamily: TYPOGRAPHY.serif }}` (NOT Tailwind classes)
- **Color Palette:** Unified teal/purple theme with analogous + complementary harmony
- **Tab Style:** Underline tabs (structured ⇄ prose toggle in PR #2)
- **Prose Display:** Simple paragraphs with spacing (no background, transparent)
- **Persistence:** localStorage for user preferences (PR #2)

---

## Typography Specifications

### Dashboard Standard Pattern

**Source:** SessionCard.tsx, NotesGoalsCard.tsx, and 4 other dashboard components

```typescript
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
```

### Full Typography Hierarchy

| Element | Font Family | Weight | Size | Line Height | Additional Styles |
|---------|-------------|--------|------|-------------|-------------------|
| **Main Titles** | Crimson Pro | 600 | 24px | 1.3 | - |
| **Section Headers** | Crimson Pro | 600 | 20px | 1.3 | - |
| **Subsection Labels** | Inter | 500 | 11px | 1.2 | uppercase, letter-spacing: 1px |
| **Body Paragraphs** | Crimson Pro | 400 | 14px | 1.6 | - |
| **List Items/Evidence** | Crimson Pro | 400 | 13px | 1.5 | - |
| **Metadata Labels** | Inter | 500 | 11px | 1.2 | - |
| **Metadata Values** | Inter | 500 | 13px | 1.2 | - |
| **Speaker Labels** | Inter | 600 | 13px | 1.3 | - |
| **Timestamps** | Inter | 500 | 11px | 1.2 | - |

### Design Rationale

**Serif (Crimson Pro):**
- Body text, paragraphs, narrative content
- Main titles and section headers
- List items and evidence bullets
- **Why:** Readable, professional, calming (therapy-appropriate)

**Sans-serif (Inter):**
- Labels, metadata, navigation
- Section markers (uppercase, tracked)
- Speaker names and timestamps
- **Why:** Clean, modern, functional

---

## Phase 1A: SessionDetail & DeepAnalysis

### File 1: SessionDetail.tsx

**Path:** `frontend/app/patient/components/SessionDetail.tsx`

#### Current Issues

**Lines 22-23:**
```typescript
const fontSerif = 'system-ui';
const fontSans = 'system-ui';
```

**Result:** All text in SessionDetail uses system-ui (incorrect).

#### Changes Required

**Step 1: Replace Font Constants (Lines 22-23)**

**BEFORE:**
```typescript
const fontSerif = 'system-ui';
const fontSans = 'system-ui';
```

**AFTER:**
```typescript
const TYPOGRAPHY = {
  serif: '"Crimson Pro", Georgia, serif',
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
} as const;
```

**Step 2: Update All Font References**

Find all instances of `fontSerif` and `fontSans` and replace with `TYPOGRAPHY.serif` and `TYPOGRAPHY.sans`.

**Example Replacements:**

**Session Title (Line ~170):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif, fontSize: '24px', fontWeight: 600 }}

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '24px', fontWeight: 600 }}
```

**Metadata Labels (Line ~185):**
```typescript
// BEFORE
style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase' }}

// AFTER
style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase' }}
```

**Speaker Labels in Transcript (Line ~250):**
```typescript
// BEFORE
style={{ fontFamily: fontSans, fontSize: '13px', fontWeight: 600 }}

// AFTER
style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '13px', fontWeight: 600 }}
```

**Dialogue Text in Transcript (Line ~255):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }}

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }}
```

**Timestamps (Line ~260):**
```typescript
// BEFORE
style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500 }}

// AFTER
style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500 }}
```

#### Complete Find & Replace

Use this regex pattern to find all font references:
- Search: `fontSerif`
- Replace: `TYPOGRAPHY.serif`

Then:
- Search: `fontSans`
- Replace: `TYPOGRAPHY.sans`

**Expected Changes:** ~15-20 replacements across SessionDetail.tsx

---

### File 2: DeepAnalysisSection.tsx

**Path:** `frontend/app/patient/components/DeepAnalysisSection.tsx`

#### Current Issues

**Lines 18-19:**
```typescript
const fontSerif = 'system-ui';
const fontSans = 'system-ui';
```

**Result:** All 5 colored cards (Progress/Insights/Skills/Relationship/Recommendations) use system-ui.

#### Current Font Chaos

DeepAnalysisSection currently has **7 different font combinations** due to mixing system-ui constants with Tailwind classes:

1. Section title: `system-ui` + `text-xl font-semibold`
2. Card titles: `system-ui` + `font-semibold`
3. Subsection labels: `system-ui` + `text-xs uppercase tracking-wide`
4. Body paragraphs: `system-ui` + `text-sm`
5. Evidence bullets: `system-ui` + `text-sm`
6. Random Tailwind overrides: `font-inter`, `font-crimson`
7. Inconsistent line heights and weights

**This is a mess and needs complete cleanup.**

#### Changes Required

**Step 1: Replace Font Constants (Lines 18-19)**

**BEFORE:**
```typescript
const fontSerif = 'system-ui';
const fontSans = 'system-ui';
```

**AFTER:**
```typescript
const TYPOGRAPHY = {
  serif: '"Crimson Pro", Georgia, serif',
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
} as const;
```

**Step 2: Standardize All Typography**

**Section Title (Line ~50):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif }}
className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-6"

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '20px', fontWeight: 600 }}
className="text-gray-800 dark:text-gray-100 mb-6"
```

**Card Container (Lines ~60-80):**
No font changes needed, but verify gradient colors align with unified palette.

**Card Title (Line ~100):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif }}
className="font-semibold mb-3 text-gray-800 dark:text-gray-100"

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '16px', fontWeight: 600 }}
className="mb-3 text-gray-800 dark:text-gray-100"
```

**Subsection Labels (Line ~110):**
```typescript
// BEFORE
style={{ fontFamily: fontSans }}
className="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400 mb-2"

// AFTER
style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }}
className="text-gray-600 dark:text-gray-400 mb-2"
```

**Body Paragraphs (Line ~120):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif }}
className="text-sm text-gray-700 dark:text-gray-300 mb-3"

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }}
className="text-gray-700 dark:text-gray-300 mb-3"
```

**Evidence Bullets (Line ~130):**
```typescript
// BEFORE
style={{ fontFamily: fontSerif }}
className="text-sm text-gray-700 dark:text-gray-300"

// AFTER
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '13px', fontWeight: 400, lineHeight: 1.5 }}
className="text-gray-700 dark:text-gray-300"
```

#### Complete Cleanup

**Remove ALL Tailwind font classes:**
- Remove: `font-semibold`, `font-medium`, `font-normal`
- Remove: `text-xl`, `text-sm`, `text-xs`
- Keep: Color classes (`text-gray-800`), spacing (`mb-3`), dark mode (`dark:text-gray-100`)

**Move ALL font styling to inline styles:**
- fontFamily
- fontSize
- fontWeight
- lineHeight (where applicable)
- textTransform (for labels)
- letterSpacing (for labels)

**Expected Changes:** ~25-30 replacements across DeepAnalysisSection.tsx

---

### Color Palette Verification

While implementing Phase 1A, **verify** that all 5 colored cards use colors from the unified palette:

**Unified Palette (Teal/Purple Theme):**
- **Primary Teal:** `#5AB9B4` (light mode) / `#3d8b87` (dark mode)
- **Primary Purple:** `#a78bfa` (both modes)
- **Analogous Blue:** `#5A9BB4` (light mode) / `#3d6d87` (dark mode)
- **Analogous Lavender:** `#9b87fa` (both modes)
- **Complementary Coral:** `#fa8787` (both modes)

**Current Card Colors (Lines ~60-150):**

| Card | Current Color | Should Be |
|------|---------------|-----------|
| Progress | `bg-gradient-to-br from-teal-50 to-teal-100` | ✅ Keep (primary teal) |
| Insights | `bg-gradient-to-br from-purple-50 to-purple-100` | ✅ Keep (primary purple) |
| Skills | `bg-gradient-to-br from-blue-50 to-blue-100` | ✅ Keep (analogous blue) |
| Relationship | `bg-gradient-to-br from-pink-50 to-pink-100` | ⚠️ Verify against coral |
| Recommendations | `bg-gradient-to-br from-indigo-50 to-indigo-100` | ⚠️ Verify against lavender |

**Action:** If colors don't match unified palette, update in Phase 1A (minimal change, same file).

---

## Phase 1B: Header & Timeline Deprecation

**Execute AFTER Phase 1A testing is complete.**

### File 3: Header.tsx

**Path:** `frontend/app/patient/components/Header.tsx`

#### Current Issue

Navigation buttons have **no explicit font family**. They inherit from parent, which may be incorrect.

**Lines ~40-80 (Navigation Buttons):**
```typescript
<button className="px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
  Dashboard
</button>
```

No `fontFamily` style property exists.

#### Changes Required

**Step 1: Add TYPOGRAPHY Constant (After imports, ~line 15)**

**ADD:**
```typescript
const TYPOGRAPHY = {
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
} as const;
```

**Step 2: Add Font to Navigation Buttons**

**BEFORE (Line ~40):**
```typescript
<button className="px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
  Dashboard
</button>
```

**AFTER:**
```typescript
<button
  style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '14px', fontWeight: 500 }}
  className="px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
>
  Dashboard
</button>
```

**Repeat for all 4 navigation buttons:**
1. Dashboard
2. Sessions
3. Ask AI
4. Upload

**Typography Specs for Header:**
- Font: Inter 500, 14px
- Line height: Default (no override needed)
- Letter spacing: Default (no override needed)

**Expected Changes:** 4 button updates in Header.tsx

---

### File 4 & 5: Timeline Deprecation

**Path 1:** `frontend/app/patient/components/TimelineSidebar.tsx`
**Path 2:** `frontend/app/patient/components/HorizontalTimeline.tsx`

#### Verification Complete

**Grep Search Results:** No active imports found in codebase.

```bash
# Search performed:
grep -r "TimelineSidebar\|HorizontalTimeline" frontend/app --include="*.tsx" --include="*.ts"

# Results: 0 active imports (safe to deprecate)
```

#### Changes Required

**Step 1: Rename Files**

```bash
# From:
frontend/app/patient/components/TimelineSidebar.tsx
frontend/app/patient/components/HorizontalTimeline.tsx

# To:
frontend/app/patient/components/TimelineSidebar.DEPRECATED.tsx
frontend/app/patient/components/HorizontalTimeline.DEPRECATED.tsx
```

**Step 2: Add Deprecation Comment**

**Add to top of BOTH files (after 'use client' if present):**

```typescript
/**
 * ⚠️ DEPRECATED - DO NOT USE
 *
 * This component has been deprecated as of 2025-01-06.
 * Timeline navigation has been replaced by session list view.
 *
 * This file is kept for reference only and will be removed in a future cleanup.
 * See SessionCard.tsx for current session navigation patterns.
 */
```

**Step 3: Verify No Broken Imports**

After renaming, run:
```bash
npm run build
```

Expected result: Clean build with no errors.

---

## Testing Checklist

### Phase 1A Testing

**After implementing SessionDetail.tsx + DeepAnalysisSection.tsx:**

#### Visual Testing

- [ ] **Dashboard to SessionDetail transition**
  - Navigate from dashboard session card to SessionDetail
  - Verify fonts remain consistent (no visual "jump" or change)
  - Check both light and dark mode

- [ ] **SessionDetail layout**
  - Session title: Crimson Pro 600, 24px ✓
  - Metadata labels: Inter 500, 11px, uppercase ✓
  - Metadata values: Inter 500, 13px ✓
  - Speaker labels: Inter 600, 13px ✓
  - Dialogue text: Crimson Pro 400, 14px, line-height 1.6 ✓
  - Timestamps: Inter 500, 11px ✓

- [ ] **DeepAnalysisSection cards**
  - Section title: Crimson Pro 600, 20px ✓
  - Card titles: Crimson Pro 600, 16px ✓
  - Subsection labels: Inter 500, 11px, uppercase, tracked ✓
  - Body paragraphs: Crimson Pro 400, 14px, line-height 1.6 ✓
  - Evidence bullets: Crimson Pro 400, 13px, line-height 1.5 ✓

- [ ] **Color palette verification**
  - All 5 cards use unified teal/purple theme
  - Gradients appear smooth and professional
  - Dark mode colors are appropriately muted

#### Responsive Testing

- [ ] **Large monitors (1920px+)**
  - Text remains readable
  - Line lengths don't exceed ~80 characters
  - Cards don't scale beyond 1.0x

- [ ] **Laptop screens (1366px)**
  - Layout adapts correctly
  - Font sizes remain legible

- [ ] **Tablet (768px-1024px)**
  - Two-column layout stacks if needed
  - Font sizes adjust appropriately

#### Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

#### Dark Mode Testing

- [ ] Toggle between light/dark mode in SessionDetail
- [ ] Verify all text remains readable
- [ ] Check gradient backgrounds adjust correctly
- [ ] Verify border colors are visible

---

### Phase 1B Testing

**After implementing Header.tsx + Timeline deprecation:**

#### Visual Testing

- [ ] **Header navigation**
  - All 4 buttons use Inter 500, 14px ✓
  - Buttons remain clickable and styled correctly
  - Hover states work as expected
  - Active state styling preserved

- [ ] **Full flow consistency**
  - Dashboard → Header nav → SessionDetail
  - All fonts align with design system
  - No visual inconsistencies

#### Build Testing

- [ ] **npm run build**
  - Build completes successfully
  - No TypeScript errors
  - No ESLint errors related to font changes

- [ ] **Timeline deprecation**
  - No broken imports detected
  - No runtime errors from missing components
  - Build size unchanged (files still exist, just renamed)

---

## Success Criteria

### Automated Checks

- [ ] **Build Success**
  ```bash
  npm run build
  # Expected: ✓ Compiled successfully
  ```

- [ ] **TypeScript Validation**
  ```bash
  npm run type-check
  # Expected: No errors
  ```

- [ ] **No Console Errors**
  - Open browser DevTools
  - Navigate through dashboard → session detail
  - Console should be clean (no font loading errors)

### Manual Validation

- [ ] **Font Family Verification**
  - Inspect any text element in SessionDetail
  - Computed style shows: `"Crimson Pro", Georgia, serif` or `"Inter", ...`
  - NO elements show `system-ui`

- [ ] **Typography Hierarchy**
  - Section headers are clearly larger than body text
  - Labels are distinct from values
  - Hierarchy is immediately obvious

- [ ] **Visual Consistency**
  - SessionDetail matches SessionCard visual style
  - Dashboard cards match SessionDetail cards
  - No "jarring" font changes when navigating

- [ ] **Dark Mode Parity**
  - Light and dark mode have identical typography hierarchy
  - Only colors change, not font sizes/weights

### Before/After Screenshots

**Capture these for documentation:**

1. SessionDetail title area (before/after)
2. DeepAnalysisSection full view (before/after)
3. Single colored card closeup (before/after)
4. Header navigation (before/after)
5. Side-by-side dashboard card + session detail (after only)

---

## Iteration Points

**TYPOGRAPHY constants are designed for easy iteration.**

### How to Adjust Typography

**Example: Make all body text larger**

**In SessionDetail.tsx:**
```typescript
const TYPOGRAPHY = {
  serif: '"Crimson Pro", Georgia, serif',
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  sizes: {
    body: '16px',  // Changed from 14px
  }
} as const;
```

Then update all body text:
```typescript
style={{ fontFamily: TYPOGRAPHY.serif, fontSize: TYPOGRAPHY.sizes.body }}
```

**This change propagates everywhere instantly.**

### Common Adjustments

**If user feedback suggests:**

1. **"Body text is too small"**
   - Add `sizes` object to TYPOGRAPHY
   - Update all `fontSize: '14px'` to `fontSize: TYPOGRAPHY.sizes.body`
   - Change constant value once

2. **"Headers need more weight"**
   - Add `weights` object to TYPOGRAPHY
   - Update all `fontWeight: 600` to `fontWeight: TYPOGRAPHY.weights.header`

3. **"Line height is too tight"**
   - Add `lineHeights` object to TYPOGRAPHY
   - Update all `lineHeight: 1.6` to `lineHeight: TYPOGRAPHY.lineHeights.body`

4. **"Need a third font for quotes"**
   - Add `quote: '"Merriweather", Georgia, serif'` to TYPOGRAPHY
   - Use for emphasized sections

### Future Design Token Migration

When TheraBridge eventually creates a centralized theme system:

**Step 1:** Create `lib/design-tokens.ts`
```typescript
export const DESIGN_TOKENS = {
  fonts: {
    serif: '"Crimson Pro", Georgia, serif',
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  fontSizes: { /* ... */ },
  fontWeights: { /* ... */ },
} as const;
```

**Step 2:** Import in all components
```typescript
import { DESIGN_TOKENS } from '@/lib/design-tokens';

const TYPOGRAPHY = {
  serif: DESIGN_TOKENS.fonts.serif,
  sans: DESIGN_TOKENS.fonts.sans,
} as const;
```

**This PR lays the groundwork for that future centralization.**

---

## PR #2 Preview

**Prose Analysis UI with Toggle (Future Work)**

### Context

Backend currently generates **two analysis formats:**
1. **Structured Analysis** (JSONB): 5 colored cards with sections
2. **Prose Analysis** (TEXT): 500-750 words, 5 paragraphs, plain text with `\n\n` separators

**Frontend only displays structured analysis.** Prose is generated but never shown.

### Proposed Solution

**Tab Toggle UI in DeepAnalysisSection:**

```
[ Structured ] [ Prose ]  ← Underline tabs (selected = underline)
```

**Structured View (Current):**
- 5 colored cards with subsections and bullets
- Current implementation (no changes)

**Prose View (New):**
- Simple paragraphs with spacing
- No background color (transparent)
- Same typography as body paragraphs (Crimson Pro 400, 14px, line-height 1.6)
- Paragraph spacing: 16px (mb-4)

### Implementation Notes

**Phase 1A typography work makes PR #2 easier:**
- Prose paragraphs will use `TYPOGRAPHY.serif` constant
- Typography hierarchy already defined
- Color palette already unified

**Key Decisions (Locked In):**
- Tab style: Underline (not pills, not boxes)
- Prose background: Transparent (not colored, not bordered)
- Prose paragraphs: Simple with spacing (not complex layout)
- Persistence: localStorage (tab selection persists across sessions)

**Scope:**
- 1 file modified: DeepAnalysisSection.tsx
- ~150 lines added (toggle UI + prose display logic)
- No backend changes needed (data already exists)

**This is a separate PR to keep changes focused and testable.**

---

## Implementation Workflow

### Phase 1A: Core Font Changes

1. **Read the full plan** (this file)
2. **Read CLAUDE.md** (git commit rules, repository structure)
3. **Read TheraBridge.md** (current project state)
4. **Create feature branch** (if not already on one)
5. **Implement SessionDetail.tsx**
   - Replace TYPOGRAPHY constant
   - Find/replace all font references
   - Verify ~15-20 changes
6. **Implement DeepAnalysisSection.tsx**
   - Replace TYPOGRAPHY constant
   - Remove Tailwind font classes
   - Standardize all typography
   - Verify color palette alignment
   - Verify ~25-30 changes
7. **Run manual testing checklist** (Phase 1A section)
8. **Capture before/after screenshots**
9. **Commit changes** (backdated to Dec 23, 2025 + 30s increment)
10. **Update TheraBridge.md** (PR #1 status: Planned → Testing)
11. **Post testing results in conversation**

### Phase 1B: Header + Deprecation

**Execute AFTER Phase 1A is confirmed working.**

1. **Implement Header.tsx**
   - Add TYPOGRAPHY constant
   - Update 4 navigation buttons
2. **Deprecate Timeline components**
   - Rename TimelineSidebar.tsx → TimelineSidebar.DEPRECATED.tsx
   - Rename HorizontalTimeline.tsx → HorizontalTimeline.DEPRECATED.tsx
   - Add deprecation comments
3. **Run build test** (`npm run build`)
4. **Run manual testing checklist** (Phase 1B section)
5. **Commit changes** (backdated to Dec 23, 2025 + 30s increment)
6. **Update TheraBridge.md** (PR #1 status: Testing → Review)
7. **Post completion summary**

### Final Steps

1. **Update SESSION_LOG.md** (add Phase 1A complete entry, then Phase 1B complete entry)
2. **Update CLAUDE.md** (move PR #1 from Active → Completed)
3. **Push to remote** (`git push`)
4. **Mark PR #1 as Merged** in TheraBridge.md
5. **Deploy to production** (if applicable)
6. **Mark PR #1 as Deployed** in TheraBridge.md

---

## Questions to Ask User After Implementation

**After Phase 1A implementation:**

1. **Typography feel:**
   - "How does the typography feel? Too large, too small, or just right?"
   - "Are the section headers distinct enough from body text?"
   - "Is the line height comfortable for reading long transcripts?"

2. **Visual hierarchy:**
   - "Can you immediately distinguish labels from values in the metadata section?"
   - "Do the 5 colored cards feel balanced and organized?"
   - "Is there any text that feels 'out of place' or inconsistent?"

3. **Color palette:**
   - "Do the card colors feel cohesive as a set?"
   - "Are there any colors that feel too bright or too muted?"
   - "Does dark mode feel professional and easy on the eyes?"

4. **Performance:**
   - "Did the page load quickly? Any lag or font flashing?"
   - "Does navigating between dashboard and session detail feel smooth?"

**After Phase 1B implementation:**

5. **Header navigation:**
   - "Do the header buttons feel clickable and well-styled?"
   - "Is the font size/weight appropriate for navigation?"

6. **Overall consistency:**
   - "Does the entire app now feel like a unified design system?"
   - "Are there any other components that feel inconsistent?"

**For PR #2 planning:**

7. **Prose analysis interest:**
   - "Would you like to see the prose analysis view implemented next (PR #2)?"
   - "How important is the toggle feature compared to other priorities?"

---

## End of Plan

**This plan is comprehensive and ready for implementation.**

**Key Files Referenced:**
- `frontend/app/patient/components/SessionDetail.tsx`
- `frontend/app/patient/components/DeepAnalysisSection.tsx`
- `frontend/app/patient/components/Header.tsx`
- `frontend/app/patient/components/TimelineSidebar.tsx`
- `frontend/app/patient/components/HorizontalTimeline.tsx`
- `Project MDs/TheraBridge.md`
- `.claude/SESSION_LOG.md`
- `.claude/CLAUDE.md`

**Git Commit Rules:**
- All commits backdated to Dec 23, 2025
- Check most recent commit timestamp first
- Add exactly 30 seconds to previous commit
- Use GIT_COMMITTER_DATE and --date flags

**Success Criteria:**
- All text in SessionDetail uses Crimson Pro or Inter (NOT system-ui)
- Typography hierarchy is immediately obvious
- Dashboard and SessionDetail are visually consistent
- Dark mode works perfectly
- Build completes with no errors
- Timeline components safely deprecated

**Ready to implement. Good luck! 🚀**
