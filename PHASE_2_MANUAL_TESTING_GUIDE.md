# Phase 2 Manual Testing Guide
**TechniqueModal Feature - UI Integration Testing**

**Date:** 2025-12-22
**Component:** TechniqueModal + SessionCard Integration
**Test Duration:** ~15-20 minutes
**Tester:** [Your Name]

---

## Overview

This guide helps you manually verify that the TechniqueModal feature works correctly in the frontend. You'll test clicking techniques in session cards, viewing definitions, and ensuring the modal behaves properly across different scenarios.

**What You're Testing:**
- ✅ Clicking techniques opens the modal
- ✅ Modal displays correct information
- ✅ Modal closes via multiple methods
- ✅ Multiple techniques work correctly
- ✅ Responsive design on different screen sizes
- ✅ Error handling works

---

## Prerequisites

### 1. Start the Backend Server

Open a terminal and run:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting TherapyBridge API
   Environment: development
   Debug mode: True
   Supabase URL: https://your-project.supabase.co
   Breakthrough detection: ✓ Enabled
INFO:     Application startup complete.
```

✅ **Checkpoint:** Backend server is running

---

### 2. Start the Frontend Dev Server

Open a **second terminal** and run:

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
▲ Next.js 16.0.10
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Ready in 2.5s
```

✅ **Checkpoint:** Frontend dev server is running

---

### 3. Navigate to Patient Dashboard

Open your browser and go to:
```
http://localhost:3000/patient
```

or if using dashboard-v3:
```
http://localhost:3000/patient/dashboard-v3/sessions
```

✅ **Checkpoint:** You see session cards displayed

---

## Test Suite

### Test 1: Basic Modal Opening ✅

**Objective:** Verify clicking a technique opens the modal

**Steps:**
1. Find any SessionCard on the dashboard
2. Look at the "Strategies / Action Items" section
3. The **first item** should be underlined with dots (this is the technique)
4. Click on the underlined technique

**Expected Results:**
- [ ] Modal appears with smooth animation (fades in + slight scale)
- [ ] Dark backdrop appears behind modal
- [ ] Modal is centered on screen
- [ ] No page navigation occurs (you stay on dashboard)

**Pass:** ⬜ YES / ⬜ NO

**Notes:**
```
[Any observations]
```

---

### Test 2: Modal Content Display ✅

**Objective:** Verify modal displays correct information

**Using the modal you just opened:**

**Check Header Section:**
- [ ] Top shows modality (e.g., "CBT", "DBT", "ACT") in small gray text
- [ ] Below shows technique name (e.g., "Cognitive Restructuring") in larger bold text
- [ ] X button appears in top-right corner

**Check Definition Section:**
- [ ] Definition text appears (2-4 sentences)
- [ ] Text is readable and professional
- [ ] No loading spinner visible (definition has loaded)
- [ ] No JSON artifacts like `{`, `}`, or `"definition":` visible

**Check Footer:**
- [ ] Blue "Got it" button appears at bottom
- [ ] Button spans full width of modal

**Example - CBT Technique:**
```
Modality: CBT
Technique: Cognitive Restructuring
Definition: The therapeutic process of identifying and challenging
negative and irrational thoughts, then replacing them with more
balanced, realistic alternatives...
```

**Pass:** ⬜ YES / ⬜ NO

**Screenshot:** (Optional - take screenshot of modal)

---

### Test 3: Modal Closing - Backdrop Click ✅

**Objective:** Verify clicking outside modal closes it

**Steps:**
1. With modal open, click on the **dark area outside the modal** (backdrop)
2. Observe modal behavior

**Expected Results:**
- [ ] Modal closes immediately with smooth animation (fades out + slight scale)
- [ ] Backdrop disappears
- [ ] You return to normal dashboard view
- [ ] Session card is still visible

**Pass:** ⬜ YES / ⬜ NO

---

### Test 4: Modal Closing - X Button ✅

**Objective:** Verify X button closes modal

**Steps:**
1. Click the same technique again to reopen modal
2. Click the **X button** in top-right corner
3. Observe modal behavior

**Expected Results:**
- [ ] Modal closes with animation
- [ ] Backdrop disappears
- [ ] Returns to dashboard

**Pass:** ⬜ YES / ⬜ NO

---

### Test 5: Modal Closing - "Got it" Button ✅

**Objective:** Verify "Got it" button closes modal

**Steps:**
1. Click technique again to reopen modal
2. Click the blue **"Got it" button** at bottom
3. Observe modal behavior

**Expected Results:**
- [ ] Modal closes with animation
- [ ] Backdrop disappears
- [ ] Returns to dashboard

**Pass:** ⬜ YES / ⬜ NO

---

### Test 6: Modal Closing - ESC Key ✅

**Objective:** Verify ESC key closes modal

**Steps:**
1. Click technique again to reopen modal
2. Press **ESC** key on keyboard
3. Observe modal behavior

**Expected Results:**
- [ ] Modal closes with animation
- [ ] Backdrop disappears
- [ ] Returns to dashboard

**Pass:** ⬜ YES / ⬜ NO

**If failed:** This is a nice-to-have feature. Document but not critical.

---

### Test 7: Multiple Techniques ✅

**Objective:** Verify different techniques show different definitions

**Steps:**
1. Note the technique on the first session card (e.g., "CBT - Cognitive Restructuring")
2. Click it and read the definition
3. Close modal
4. Find a **different session** with a **different technique** (e.g., "DBT - TIPP Skills")
5. Click that technique
6. Compare definitions

**Expected Results:**
- [ ] Second modal opens correctly
- [ ] Definition is **different** from first technique
- [ ] Definition matches the technique name shown
- [ ] No "stale" data from previous modal
- [ ] Both modality and technique name update correctly

**Example Comparison:**

**Session 1:**
- Technique: CBT - Cognitive Restructuring
- Definition: "The therapeutic process of identifying and challenging negative thoughts..."

**Session 2:**
- Technique: DBT - TIPP Skills
- Definition: "Crisis survival skill using physiological interventions..."

**Pass:** ⬜ YES / ⬜ NO

---

### Test 8: Loading State ✅

**Objective:** Verify loading spinner appears briefly

**Steps:**
1. Close any open modal
2. Open your browser's **Developer Tools** (F12)
3. Go to **Network** tab
4. Set throttling to **Slow 3G** (to slow down API call)
5. Click a technique
6. Watch modal as it opens

**Expected Results:**
- [ ] Modal opens immediately
- [ ] **Loading spinner** appears (spinning circle)
- [ ] Spinner is centered in definition area
- [ ] After 1-2 seconds, definition text replaces spinner
- [ ] No error messages

**Pass:** ⬜ YES / ⬜ NO

**If you can't see spinner:** Set Network to "Offline", click technique, you should see spinner indefinitely until you set back to "Online"

---

### Test 9: Click Separation (Card vs Technique) ✅

**Objective:** Verify clicking technique doesn't trigger card navigation

**Steps:**
1. Find a session card
2. Note what happens when you click **outside the technique** (e.g., on the date or summary)
   - Expected: Card navigates to session detail page or expands
3. Go back to dashboard
4. Click **on the technique itself** (underlined text)
   - Expected: Modal opens, NO navigation

**Expected Results:**
- [ ] Clicking card body → Navigates to session detail (normal behavior)
- [ ] Clicking technique → Opens modal ONLY (does not navigate)
- [ ] No double-action occurs (modal + navigation)

**Pass:** ⬜ YES / ⬜ NO

---

### Test 10: Responsive - Desktop (1920x1080) 🖥️

**Objective:** Verify modal looks good on large screens

**Steps:**
1. Make browser window full screen (or press F11)
2. Click a technique to open modal

**Expected Results:**
- [ ] Modal is centered horizontally and vertically
- [ ] Modal width is ~448px (max-width: 28rem = 448px)
- [ ] Modal doesn't stretch across entire screen
- [ ] Text is readable and not too wide
- [ ] Backdrop covers entire screen

**Pass:** ⬜ YES / ⬜ NO

---

### Test 11: Responsive - Tablet (768x1024) 📱

**Objective:** Verify modal works on tablet size

**Steps:**
1. Open Developer Tools (F12)
2. Click the **Toggle Device Toolbar** button (or Ctrl+Shift+M)
3. Select **iPad** or set custom size: 768 x 1024
4. Click a technique

**Expected Results:**
- [ ] Modal is 90% of screen width
- [ ] Modal is still centered
- [ ] Text is readable (not too small)
- [ ] "Got it" button is easily tappable
- [ ] No horizontal scrolling needed

**Pass:** ⬜ YES / ⬜ NO

---

### Test 12: Responsive - Mobile (375x667) 📱

**Objective:** Verify modal works on phone size

**Steps:**
1. In Device Toolbar, select **iPhone SE** or set: 375 x 667
2. Click a technique

**Expected Results:**
- [ ] Modal is 90% of screen width
- [ ] Modal fits on screen without scrolling
- [ ] Text is readable
- [ ] All content visible
- [ ] Buttons are easily tappable (minimum 44x44px touch target)

**Pass:** ⬜ YES / ⬜ NO

---

### Test 13: Visual Polish ✨

**Objective:** Verify animations and styling look professional

**Checklist:**
- [ ] Technique has **dotted underline** in card
- [ ] Underline is visible enough to indicate interactivity
- [ ] Modal has **smooth entrance animation** (fade + scale)
- [ ] Modal has **smooth exit animation**
- [ ] Backdrop dims the background nicely
- [ ] Modal has **subtle shadow** making it pop
- [ ] All text is legible (good contrast)
- [ ] No visual glitches or flashing
- [ ] Animation speed feels natural (not too fast/slow)

**Pass:** ⬜ YES / ⬜ NO

---

### Test 14: Error Handling (Optional) ⚠️

**Objective:** Verify graceful error handling

**Steps:**
1. **Stop the backend server** (Ctrl+C in backend terminal)
2. Click a technique
3. Observe modal behavior

**Expected Results:**
- [ ] Modal still opens
- [ ] Shows error message: "Definition not available."
- [ ] Error is in red text
- [ ] Modal is still closeable
- [ ] No browser console errors (check F12 Console)
- [ ] App doesn't crash

**Steps to recover:**
1. Close modal
2. Restart backend server
3. Click technique again → Should work normally

**Pass:** ⬜ YES / ⬜ NO

---

## Console Error Check 🔍

**Important:** Throughout all tests, keep Developer Tools open

**Steps:**
1. Open Developer Tools (F12)
2. Go to **Console** tab
3. Perform all tests above
4. Check for any errors (red text)

**Expected:**
- [ ] No errors appear during normal operation
- [ ] No warnings about React hooks
- [ ] No "404 Not Found" errors
- [ ] No "Failed to fetch" errors (except during error handling test)

**If errors appear:**
```
[Copy any error messages here]
```

---

## Summary & Sign-Off

### Test Results Summary

| Test # | Test Name | Result |
|--------|-----------|--------|
| 1 | Basic modal opening | ⬜ PASS / ⬜ FAIL |
| 2 | Modal content display | ⬜ PASS / ⬜ FAIL |
| 3 | Backdrop click close | ⬜ PASS / ⬜ FAIL |
| 4 | X button close | ⬜ PASS / ⬜ FAIL |
| 5 | "Got it" button close | ⬜ PASS / ⬜ FAIL |
| 6 | ESC key close | ⬜ PASS / ⬜ FAIL |
| 7 | Multiple techniques | ⬜ PASS / ⬜ FAIL |
| 8 | Loading state | ⬜ PASS / ⬜ FAIL |
| 9 | Click separation | ⬜ PASS / ⬜ FAIL |
| 10 | Desktop responsive | ⬜ PASS / ⬜ FAIL |
| 11 | Tablet responsive | ⬜ PASS / ⬜ FAIL |
| 12 | Mobile responsive | ⬜ PASS / ⬜ FAIL |
| 13 | Visual polish | ⬜ PASS / ⬜ FAIL |
| 14 | Error handling | ⬜ PASS / ⬜ FAIL |

**Total Passed:** _____ / 14

---

### Critical Tests (Must Pass)

These tests are **required** for approval:
- [ ] Test 1: Modal opens
- [ ] Test 2: Content displays correctly
- [ ] Test 3, 4, or 5: At least one close method works
- [ ] Test 7: Multiple techniques work
- [ ] Test 12: Works on mobile

**Critical Pass Rate:** _____ / 5

---

### Issues Found

**Critical Issues (Blocking):**
```
[List any critical bugs that prevent feature from working]
```

**Minor Issues (Non-blocking):**
```
[List any minor issues or polish items]
```

**Enhancement Ideas:**
```
[Optional improvements for future]
```

---

### Final Verdict

⬜ **PHASE 2 APPROVED** - All critical tests passed, feature is production-ready

⬜ **PHASE 2 APPROVED WITH NOTES** - Minor issues found but acceptable

⬜ **PHASE 2 NEEDS FIXES** - Critical issues must be resolved before approval

---

### Tester Information

**Name:** ______________________

**Date:** ______________________

**Testing Duration:** ______________________

**Browser Tested:** ⬜ Chrome  ⬜ Firefox  ⬜ Safari  ⬜ Edge

**OS:** ⬜ Mac  ⬜ Windows  ⬜ Linux

---

## Next Steps

### If Approved ✅
- Notify team: "Phase 2 manual testing complete - APPROVED"
- Ready for production deployment
- Update implementation plan with completion status

### If Issues Found ⚠️
- Create detailed bug reports for each issue
- Assign priority (Critical / Major / Minor)
- Re-test after fixes are deployed

---

## Quick Reference: Common Techniques to Test

Based on your mock data, here are techniques you can test:

1. **CBT - Cognitive Restructuring** (Session 4, 12)
2. **CBT - Safety Planning** (Session 1)
3. **DBT - TIPP Skills** (Session 2)
4. **ACT - Cognitive Defusion** (Session 5, 11)
5. **ACT - Acceptance** (Session 7)
6. **ACT - Values Clarification** (Session 9)
7. **DBT - DEAR MAN** (Session 8)
8. **Mindfulness-Based - Mindfulness Meditation** (Session 6)
9. **Other - Psychoeducation** (Session 3)
10. **Other - Validation** (Session 10)

**Test Tip:** Try at least 3-4 different techniques to ensure variety works correctly!

---

**End of Manual Testing Guide**

Good luck with your testing! 🚀
