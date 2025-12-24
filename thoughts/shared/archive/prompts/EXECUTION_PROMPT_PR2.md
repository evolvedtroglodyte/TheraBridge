# Execution Prompt: PR #2 - Prose Analysis UI Toggle

**Copy this entire prompt into a NEW Claude Code window**

---

## Context

You are implementing **PR #2: Prose Analysis UI with Toggle** for the TheraBridge project. This PR adds a tab toggle in SessionDetail to switch between prose narrative and structured analysis views.

**Project:** TheraBridge - AI-powered therapy session analysis platform
**Stack:** Next.js 16 + React 19 + TypeScript + Tailwind CSS + Framer Motion
**Dependencies:** PR #1 Complete ✅ (SessionDetail font standardization)

---

## 📋 Implementation Plan

**CRITICAL: Read the full implementation plan first:**

```bash
cat thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md
```

This plan contains:
- Current state analysis with code references
- Phase-by-phase implementation steps (4 phases)
- Complete code snippets for all components
- Testing checklist (17 items)
- Rollback plan
- Success criteria

**Do NOT proceed until you've read the entire plan.**

---

## 🎯 Task Summary

### What You're Building

A **tab toggle component** in SessionDetail with two views:

1. **📖 Narrative View** (NEW - Default)
   - Display `session.prose_analysis` as flowing prose
   - Crimson Pro serif font, line-height 1.8
   - Dobby logo header with confidence score

2. **📊 Structured View** (Existing)
   - Display existing `DeepAnalysisSection` cards
   - No changes to component logic

### Key Requirements

- ✅ localStorage persistence (`therabridge_analysis_view`)
- ✅ Theme-aware colors (teal → purple on dark mode)
- ✅ Framer Motion transitions (fade + slide)
- ✅ Accessibility (ARIA labels, keyboard nav)
- ✅ Disabled tabs when data unavailable
- ✅ Default to "Narrative" view

---

## 📁 Files to Modify

### Primary File (1 file)
1. **`frontend/app/patient/components/SessionDetail.tsx`**
   - Add `AnalysisView` type
   - Add state management (analysisView + localStorage)
   - Add `TabToggle` component (~70 lines)
   - Add `ProseAnalysisView` component (~60 lines)
   - Replace lines 364-372 (deep_analysis rendering)
   - Import `DobbyLogo` component

### Optional File (if animations needed)
2. **`frontend/tailwind.config.ts`**
   - Add `fadeIn` animation (Framer Motion handles this, so optional)

---

## 🚀 Execution Steps

### Step 1: Read the Implementation Plan ✅
```bash
cat thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md
```

**Focus on:**
- Phase 1 (Tab Toggle UI Component) - Lines ~70-150
- Phase 2 (Integrate into SessionDetail) - Lines ~150-250
- Current State Analysis - Lines ~30-80

---

### Step 2: Verify Current State
```bash
# Check SessionDetail structure
cat frontend/app/patient/components/SessionDetail.tsx | grep -A 10 "Deep Clinical Analysis"

# Verify Session type includes prose_analysis
cat frontend/app/patient/lib/types.ts | grep "prose_analysis"

# Verify DobbyLogo exists
ls frontend/app/patient/components/DobbyLogo.tsx
```

**Expected:**
- Deep Analysis section at lines ~364-372
- Session type has `prose_analysis?: string` field
- DobbyLogo component exists

---

### Step 3: Implement Phase 1 - Tab Toggle UI Component

**File:** `frontend/app/patient/components/SessionDetail.tsx`

1. **Add AnalysisView type** (before SessionDetailProps interface)
   - See plan lines ~90-95

2. **Add TabToggle component** (~70 lines)
   - Copy from plan lines ~100-170
   - Includes theme-aware colors, ARIA labels, disabled states

3. **Add ProseAnalysisView component** (~60 lines)
   - Copy from plan lines ~175-240
   - Includes Dobby logo, paragraph splitting, timestamp

**Verification:**
```bash
# Check components added
grep -n "function TabToggle" frontend/app/patient/components/SessionDetail.tsx
grep -n "function ProseAnalysisView" frontend/app/patient/components/SessionDetail.tsx
```

---

### Step 4: Implement Phase 2 - Integrate into SessionDetail

**File:** `frontend/app/patient/components/SessionDetail.tsx`

1. **Import DobbyLogo** (top of file, line ~18)
   ```tsx
   import { DobbyLogo } from './DobbyLogo';
   ```

2. **Add state management** (after theme state, lines ~80-90)
   - Copy from plan lines ~250-270
   - Includes localStorage persistence

3. **Replace Deep Analysis rendering** (lines 364-372)
   - Copy from plan lines ~290-360
   - Includes tab toggle, view switching, fallbacks

**Verification:**
```bash
# Check state management added
grep -n "analysisView" frontend/app/patient/components/SessionDetail.tsx

# Check localStorage usage
grep -n "therabridge_analysis_view" frontend/app/patient/components/SessionDetail.tsx

# Check tab toggle rendering
grep -n "TabToggle" frontend/app/patient/components/SessionDetail.tsx
```

---

### Step 5: Build & Test

#### 5.1 TypeScript Compilation
```bash
cd frontend
npm run build
```

**Expected:** Zero TypeScript errors

**If errors:**
- Check import paths
- Verify `DobbyLogo` import
- Check `AnalysisView` type usage

#### 5.2 Local Development Server
```bash
cd frontend
npm run dev
```

**Navigate to:** `http://localhost:3000`

#### 5.3 Manual Testing (17-item checklist)

**See plan Section 4.1 (lines ~380-450) for full checklist**

**Critical tests:**
1. ✅ Click "Narrative" tab → Shows prose_analysis text
2. ✅ Click "Structured" tab → Shows DeepAnalysisSection cards
3. ✅ Refresh page → localStorage preserves view preference
4. ✅ Toggle theme (sun/moon icon) → Tab colors switch (teal → purple)
5. ✅ Open session with only prose → Structured tab disabled
6. ✅ Open session with only deep_analysis → Narrative tab disabled
7. ✅ Transitions are smooth (fade + slide)

**Test in production (Railway):**
- Patient ID: `35c92da4-88b1-4bb9-af24-c28ff3e46f84`
- URL: `https://therabridge.up.railway.app`
- Sessions: All 10 sessions have prose_analysis from Wave 2

---

### Step 6: Regression Testing

**Verify no existing features broken:**
- [ ] SessionDetail opens/closes correctly
- [ ] Transcript viewer scrolls properly
- [ ] Scroll preservation works when data updates
- [ ] Loading overlay appears during updates
- [ ] X button closes modal
- [ ] Theme toggle (sun/moon) works
- [ ] Mood score + emoji display correctly
- [ ] Technique definitions show
- [ ] Action items summary displays

**Run full build:**
```bash
cd frontend
npm run build
```

**Expected:** Zero errors, zero warnings (ESLint warnings ok)

---

### Step 7: Git Commit (with Backdating)

**CRITICAL: Follow git commit dating rules from CLAUDE.md**

```bash
# Step 1: Check last commit timestamp
git log --format="%ci" -n 1

# Step 2: Add 30 seconds to that timestamp
# Example: Last commit was 2025-12-23 22:40:22 -0600
# Next commit should be 2025-12-23 22:40:52 -0600

# Step 3: Stage changes
git add -A

# Step 4: Commit with calculated timestamp
GIT_COMMITTER_DATE="2025-12-23 22:40:52 -0600" \
git commit -m "Feature: PR #2 - Prose analysis UI toggle with localStorage persistence" --date="2025-12-23 22:40:52 -0600"

# Step 5: Verify commit
git log -1 --format="%ci"

# Step 6: Push to remote
git push
```

**Commit Message Format:**
```
Feature: PR #2 - Prose analysis UI toggle with localStorage persistence

- Add TabToggle component with theme-aware colors (teal/purple)
- Add ProseAnalysisView component with Dobby logo header
- Integrate tab toggle into SessionDetail (replace deep_analysis section)
- Add localStorage persistence for view preference (therabridge_analysis_view)
- Add Framer Motion transitions (fade + slide)
- Add accessibility features (ARIA labels, keyboard nav)
- Disabled tabs when data unavailable
- Default to Narrative view for patient-friendly UX
- Zero cost impact (frontend-only, no new LLM calls)

Files modified:
- frontend/app/patient/components/SessionDetail.tsx (+150 lines, -8 lines)

Testing:
- Manual testing: 17-item checklist complete
- Regression testing: All existing features verified
- Browser testing: Chrome, Safari, Firefox
- Production testing: therabridge.up.railway.app (patient 35c92da4)
```

---

### Step 8: Documentation Updates

**Update 3 files:**

#### 8.1 SESSION_LOG.md
```bash
# Add new entry at the top
cat >> .claude/SESSION_LOG.md << 'EOF'

---

## 2026-01-11 - PR #2 Implementation - Prose Analysis UI Toggle ✅ COMPLETE

**Context:** Implemented tab toggle in SessionDetail to switch between prose narrative and structured analysis views. Frontend-only change with localStorage persistence.

**Features Implemented:**

1. **TabToggle Component** (~70 lines)
   - Theme-aware colors (teal in light, purple in dark)
   - Emoji icons (📖 Narrative, 📊 Structured)
   - ARIA labels for accessibility
   - Disabled state when data unavailable

2. **ProseAnalysisView Component** (~60 lines)
   - Dobby logo header with confidence score
   - Crimson Pro serif font (15px, line-height 1.8)
   - Paragraph splitting for multi-paragraph prose
   - Timestamp footer

3. **State Management**
   - localStorage: `therabridge_analysis_view` (prose | structured)
   - Default: "prose" (patient-friendly)
   - Persistence across sessions and page refreshes

4. **Integration**
   - Replaced deep_analysis rendering (lines 364-372)
   - Added Framer Motion transitions (fade + slide, 200ms)
   - Fallback messages for missing data

**Testing Results:**
- ✅ Manual testing: 17-item checklist complete
- ✅ Regression testing: No existing features broken
- ✅ Browser testing: Chrome, Safari, Firefox verified
- ✅ Production testing: Verified on Railway (patient 35c92da4)
- ✅ Accessibility: Keyboard navigation + screen reader support
- ✅ Dark mode: Theme colors switch correctly (teal → purple)

**Technical Details:**
- Files modified: 1 (SessionDetail.tsx)
- Lines added: ~150
- Lines removed: ~8
- Cost impact: Zero (no backend changes)
- Build: TypeScript compiles with zero errors

**Commit:** `<COMMIT_HASH>` - Feature: PR #2 - Prose analysis UI toggle with localStorage persistence

**Next Steps:**
- [ ] Monitor production usage (which view do users prefer?)
- [ ] Consider adding print-friendly prose view
- [ ] Consider markdown rendering support for future prose enhancements

EOF
```

#### 8.2 TheraBridge.md
```bash
# Update "Development Status" section (line ~88)
# Change PR #2 status from "Planned" to "Complete"
```

**Before:**
```markdown
### Planned PRs
- **PR #2:** Prose Analysis UI with Toggle
  - Status: Planned (depends on PR #1)
```

**After:**
```markdown
### Completed PRs
- **PR #2:** Prose Analysis UI with Toggle
  - Status: Complete ✅ (2026-01-11)
  - Plan: `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
  - Session: SESSION_LOG.md (2026-01-11)
  - Scope: 1 file modified (SessionDetail.tsx)
  - Features: Tab toggle, localStorage persistence, theme-aware colors
  - Commit: `<COMMIT_HASH>`
```

#### 8.3 CLAUDE.md
```bash
# Update "Current Focus" section at the top
```

**Before:**
```markdown
## Current Focus: SessionDetail UI Improvements + Wave 1 Action Summarization (PR #1)

**PR #1 Status:** ✅ COMPLETE - All features verified in production (Phase 2-4 complete)
```

**After:**
```markdown
## Current Focus: Feature Development Pipeline

**PR #1 Status:** ✅ COMPLETE - SessionDetail UI Improvements + Wave 1 Action Summarization
**PR #2 Status:** ✅ COMPLETE - Prose Analysis UI Toggle (2026-01-11)

**Next:** Analytics Dashboard (Feature 2)
```

---

### Step 9: Final Verification

**Run this checklist:**

```bash
# 1. Verify commit created
git log -1 --oneline

# 2. Verify commit pushed to remote
git log --branches --not --remotes

# 3. Verify documentation updated
grep -n "PR #2" .claude/SESSION_LOG.md
grep -n "PR #2" "Project MDs/TheraBridge.md"
grep -n "PR #2" .claude/CLAUDE.md

# 4. Verify build successful
cd frontend && npm run build

# 5. Verify Railway deployment (wait 2-3 min after push)
# Visit: https://therabridge.up.railway.app
# Test: Open session, verify tab toggle works
```

**Expected:**
- ✅ Commit exists with backdated timestamp
- ✅ Commit pushed to remote (no unpushed commits)
- ✅ All 3 documentation files updated
- ✅ Build successful (zero TypeScript errors)
- ✅ Railway deployment successful

---

## 🎯 Success Criteria

Mark these as complete before finishing:

- [ ] TabToggle component renders correctly
- [ ] ProseAnalysisView displays prose text (Crimson Pro serif)
- [ ] Structured view shows DeepAnalysisSection (unchanged)
- [ ] localStorage persists view preference across refreshes
- [ ] Framer Motion transitions work (fade + slide)
- [ ] Theme colors switch correctly (teal → purple)
- [ ] Accessibility: keyboard navigation + ARIA labels work
- [ ] Disabled tabs when data unavailable
- [ ] No regressions in existing SessionDetail features
- [ ] TypeScript compiles with zero errors
- [ ] Documentation updated (SESSION_LOG, TheraBridge, CLAUDE)
- [ ] Git commit created with backdated timestamp
- [ ] Commit pushed to remote
- [ ] Production deployment verified

---

## ⚠️ Important Reminders

### From CLAUDE.md Rules:

1. **Git First, Always:**
   - Commit after implementation complete
   - Backdate to December 23, 2025 (add 30 seconds to last commit)
   - Push to remote immediately

2. **Change Logging:**
   - Create detailed SESSION_LOG entry
   - Update TheraBridge.md Development Status
   - Update CLAUDE.md Current Focus

3. **Testing Required:**
   - Manual testing (17-item checklist)
   - Regression testing (existing features)
   - Production verification (Railway)

4. **No Speculation:**
   - Read files before modifying
   - Use exact code from implementation plan
   - Verify types match between components

---

## 🐛 Troubleshooting

### If TypeScript errors:
```bash
# Check DobbyLogo import path
ls frontend/app/patient/components/DobbyLogo.tsx

# Check Session type
grep "prose_analysis" frontend/app/patient/lib/types.ts

# Check DeepAnalysisSection import
grep "DeepAnalysisSection" frontend/app/patient/components/SessionDetail.tsx
```

### If Framer Motion animations not working:
```bash
# Verify framer-motion installed
grep "framer-motion" frontend/package.json

# Check AnimatePresence wrapping
grep "AnimatePresence" frontend/app/patient/components/SessionDetail.tsx
```

### If localStorage not persisting:
```bash
# Check browser console for errors
# localStorage.getItem('therabridge_analysis_view') should return "prose" or "structured"
```

### If tab colors not switching:
```bash
# Verify useTheme hook usage
grep "useTheme" frontend/app/patient/components/SessionDetail.tsx

# Check theme context provider in layout
grep "ThemeProvider" frontend/app/patient/layout.tsx
```

---

## 📚 Reference Files

### Must Read:
1. **Implementation Plan:** `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
2. **Current SessionDetail:** `frontend/app/patient/components/SessionDetail.tsx`
3. **Session Types:** `frontend/app/patient/lib/types.ts`

### Supporting Docs:
4. **CLAUDE.md:** `.claude/CLAUDE.md` (git rules, project structure)
5. **SESSION_LOG.md:** `.claude/SESSION_LOG.md` (recent sessions)
6. **TheraBridge.md:** `Project MDs/TheraBridge.md` (project state)

---

## 🎬 Ready to Start?

**Your task:**
1. Read the implementation plan (`thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`)
2. Follow Steps 1-9 above
3. Complete all success criteria
4. Report back with results

**Expected time:** ~2 hours (implementation + testing)

**Cost impact:** Zero (frontend-only, no LLM calls)

---

**Good luck! 🚀**

---

## Quick Start Command

```bash
# Copy-paste this to get started:
cat thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md
```

Then proceed with Step 2 (Verify Current State).
