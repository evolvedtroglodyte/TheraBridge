# Maximum Parallelization Orchestration Guide

## Overview

This guide shows you how to **run 10+ Claude Code agents simultaneously** to build TherapyBridge features in record time.

---

## Parallelization Philosophy

**Traditional approach:**
```
Task 1 → Task 2 → Task 3 → Task 4 (4 hours sequential)
```

**Maximum parallelization:**
```
Task 1 ↘
Task 2 → Task 5 (1 hour, 4 agents running simultaneously)
Task 3 ↗
Task 4 ↗
```

**Key principle:** If tasks don't depend on each other, run them at the same time.

---

## Feature 1 (Authentication) - Parallelization Example

### Traditional: 4 Tracks Sequential (3-4 hours)
```
Track 1.1 (Database) → Track 1.2 (Utils) → Track 1.3 (API) → Track 1.4 (Frontend)
```

### Maximum Parallelization: 3 Phases (1.5-2 hours)

#### **Phase 1: Foundation (12 parallel windows)**
Run these subtasks simultaneously - they have NO dependencies on each other:

```
Window 1:  SUBTASK 1.1.1 - User model base
Window 2:  SUBTASK 1.1.2 - User auth fields
Window 3:  SUBTASK 1.1.3 - User role fields
Window 4:  SUBTASK 1.1.4 - User timestamps
Window 5:  SUBTASK 1.1.5 - Session model
Window 6:  SUBTASK 1.2.1 - Auth config
Window 7:  SUBTASK 1.2.2 - Password hashing
Window 8:  SUBTASK 1.2.3 - Access token generation
Window 9:  SUBTASK 1.2.4 - Refresh token generation
Window 10: SUBTASK 1.4.1 - Token storage (frontend)
Window 11: SUBTASK 1.4.8 - Environment variables (frontend)
Window 12: SUBTASK 1.2.6 - Environment variables (backend)
```

**Duration:** ~15 minutes (all complete in parallel)

#### **Phase 2: Integration (8 parallel windows)**
Run after Phase 1 completes:

```
Window 1: SUBTASK 1.1.6 - User-Session relationship (needs 1.1.1-1.1.5)
Window 2: SUBTASK 1.1.7 - User Pydantic schemas (needs 1.1.6)
Window 3: SUBTASK 1.1.8 - Token Pydantic schemas (needs 1.1.7)
Window 4: SUBTASK 1.2.5 - Token verification (needs 1.2.3, 1.2.4)
Window 5: SUBTASK 1.3.1 - Database dependency (needs 1.1.6)
Window 6: SUBTASK 1.4.2 - API client (needs 1.4.1)
Window 7: SUBTASK 1.4.3 - Auth context (needs 1.4.2)
Window 8: SUBTASK 1.1.9 - Alembic migration (needs all 1.1.*)
```

**Duration:** ~20 minutes

#### **Phase 3: API & UI (7 parallel windows)**
Run after Phase 2 completes:

```
Window 1: SUBTASK 1.3.2 - Current user dependency (needs 1.3.1, 1.2.5)
Window 2: SUBTASK 1.3.3 - Role-based access (needs 1.3.2)
Window 3: SUBTASK 1.3.4 - Signup endpoint (needs 1.3.1)
Window 4: SUBTASK 1.3.5 - Login endpoint (needs 1.3.1)
Window 5: SUBTASK 1.4.4 - Login page (needs 1.4.3)
Window 6: SUBTASK 1.4.5 - Signup page (needs 1.4.3)
Window 7: SUBTASK 1.4.6 - Protected route (needs 1.4.3)
```

**Duration:** ~20 minutes

#### **Phase 4: Final Integration (3 parallel windows)**
Run after Phase 3 completes:

```
Window 1: SUBTASK 1.3.6 - Refresh & logout endpoints (needs 1.3.5)
Window 2: SUBTASK 1.3.7 - Get me endpoint + router registration (needs 1.3.6)
Window 3: SUBTASK 1.4.7 - Wrap app with AuthProvider (needs 1.4.3)
```

**Duration:** ~15 minutes

#### **Phase 5: Testing**
```
Window 1: Run INTEGRATION TEST prompt
```

**Duration:** ~30 minutes

---

## Total Time Comparison

| Method | Time | Agents | Efficiency |
|--------|------|--------|------------|
| Sequential (1 window) | 4 hours | 1 | 1x |
| Track-based (4 windows) | 2.5 hours | 4 | 1.6x |
| **Maximum Parallel** | **1.5 hours** | **12** | **2.7x** |

**Time saved:** 2.5 hours (62% faster)

---

## Multi-Feature Parallelization

You can work on **multiple features simultaneously** by running different features in different window groups.

### Example: Building Features 1 + 6 Together

**Setup:**
- Windows 1-12: Feature 1 Phase 1 subtasks
- Windows 13-18: Feature 6 Phase 1 subtasks
- **Total: 18 parallel windows**

**Timeline:**
```
0:00 - Start both features simultaneously
0:15 - Phase 1 of both features complete
0:35 - Phase 2 of both features complete
1:00 - Both features complete!
```

**Traditional approach:** 4 hours (Feature 1) + 1.5 hours (Feature 6) = 5.5 hours
**Parallel approach:** 1 hour
**Time saved:** 4.5 hours (82% faster)

---

## Tools for Managing Many Windows

### Option 1: Browser Tabs (Simple)
- Open Claude Code in 10+ browser tabs
- Label tabs: "F1-1.1.1", "F1-1.1.2", etc.
- Paste prompts and monitor progress
- **Pros:** Simple, visual
- **Cons:** Tab management gets messy

### Option 2: Terminal Multiplexer (Advanced)
Use `tmux` or `screen` to manage multiple Claude Code CLI sessions:

```bash
# Install tmux
brew install tmux

# Create session with 12 windows
tmux new-session -s therapybridge
# Press Ctrl+B then C to create new window
# Repeat 12 times

# In each window, run:
claude-code

# Navigate between windows: Ctrl+B then window number (0-11)
```

**Pros:** Keyboard-driven, efficient, can detach/reattach
**Cons:** Learning curve

### Option 3: VS Code with Multiple Terminals
- Open VS Code
- Split terminal into 4 columns, 3 rows = 12 terminals
- Each terminal runs one subtask
- **Pros:** Visual, IDE integration
- **Cons:** Screen space limited

### Option 4: Multiple Monitors (Recommended)
- Monitor 1: 6 Claude Code windows (Feature 1, Phase 1)
- Monitor 2: 6 Claude Code windows (Feature 1, Phase 1)
- Monitor 3: Code editor (to review generated code)
- **Pros:** Maximum visibility, easy to monitor
- **Cons:** Requires multiple monitors

---

## Orchestration Workflow

### Step 1: Preparation (5 minutes)
1. Read the feature's PARALLELIZATION MAP
2. Identify how many phases it has
3. Count maximum parallel windows needed
4. Open that many Claude Code windows/tabs
5. Label each window with subtask ID

### Step 2: Phase 1 Execution (Variable time)
1. Copy each Phase 1 subtask prompt
2. Paste into corresponding window
3. Press Enter on all windows (within ~30 seconds of each other)
4. Monitor progress:
   - Green checkmarks = task complete
   - Red errors = investigate immediately
   - Yellow warnings = note for later
5. Wait for ALL Phase 1 windows to complete

### Step 3: Validation Check (2 minutes)
1. For each completed subtask, check VALIDATION checklist
2. If any validation fails, fix immediately before Phase 2
3. Run quick smoke test (e.g., import the file, check syntax)

### Step 4: Phase 2 Execution
Repeat Step 2 with Phase 2 subtasks

### Step 5: Continue Until All Phases Complete

### Step 6: Integration Testing (30 minutes)
1. Run the INTEGRATION TEST prompt in one window
2. Follow all test scenarios
3. Fix any issues discovered
4. Celebrate! 🎉

---

## Monitoring Strategy

### Use a Tracking Spreadsheet

Create a simple spreadsheet to track progress:

| Window | Subtask | Status | Start Time | End Time | Duration | Notes |
|--------|---------|--------|------------|----------|----------|-------|
| 1 | 1.1.1 | ✅ Done | 10:00 | 10:07 | 7 min | |
| 2 | 1.1.2 | 🔄 Running | 10:00 | - | - | |
| 3 | 1.1.3 | ⏳ Waiting | - | - | - | |
| 4 | 1.1.4 | ❌ Error | 10:00 | 10:05 | 5 min | Import error |

**Legend:**
- ✅ Done: VALIDATION checklist passed
- 🔄 Running: Agent actively working
- ⏳ Waiting: Blocked on dependency
- ❌ Error: Needs manual intervention

### Use Slack/Discord Notifications (Optional)

Set up a private channel and post updates:
```
10:05 - Window 1: ✅ SUBTASK 1.1.1 complete (7 min)
10:05 - Window 4: ❌ SUBTASK 1.1.4 error - import issue
10:12 - Window 2: ✅ SUBTASK 1.1.2 complete (12 min)
```

This helps if you step away and come back.

---

## Error Handling in Parallel Execution

### Strategy 1: Pause & Fix (Recommended)
When an error occurs:
1. **Don't panic** - other windows keep running
2. Note which subtask failed
3. Let other windows complete
4. After all windows done, fix failed subtasks
5. Re-run only the failed subtasks

### Strategy 2: Immediate Fix (For Critical Errors)
If an error blocks many downstream tasks:
1. **Pause all dependent windows** (don't start Phase 2)
2. Fix the error immediately
3. Verify fix works
4. Resume Phase 1, then continue to Phase 2

### Common Errors & Quick Fixes

**Error:** "Module not found: app.database"
- **Fix:** Create the missing database.py file first
- **Cause:** Skipped a dependency subtask

**Error:** "Table 'users' already exists"
- **Fix:** Drop the table or skip migration
- **Cause:** Ran migration twice

**Error:** "Invalid token type"
- **Fix:** Check token generation logic in utils.py
- **Cause:** Token payload mismatch

---

## Advanced: Swarm Mode (10+ Features Simultaneously)

For the truly ambitious, you can build multiple features in parallel:

### Swarm Configuration: 40 Parallel Windows

**Feature 1 (Windows 1-12):** Phase 1
**Feature 2 (Windows 13-20):** Phase 1
**Feature 3 (Windows 21-26):** Phase 1
**Feature 6 (Windows 27-32):** Phase 1
**Feature 8 (Windows 33-38):** Phase 1
**Monitoring Dashboard (Windows 39-40):** Track progress

**Timeline:**
```
0:00 - Start all 5 features simultaneously
0:20 - All Phase 1s complete
0:40 - All Phase 2s complete
1:10 - All features complete (except Feature 2, which is larger)
2:00 - Feature 2 complete
```

**Traditional approach:** 20 hours (all features sequential)
**Swarm approach:** 2 hours
**Time saved:** 18 hours (90% faster)

---

## Best Practices

### ✅ Do This:
- **Start small:** Try 3-4 parallel windows first, then scale up
- **Use phases:** Don't run dependent tasks in parallel
- **Monitor actively:** Check windows every 5 minutes
- **Validate frequently:** Check VALIDATION lists before next phase
- **Take breaks:** Parallel execution is intense, rest between phases
- **Document errors:** Track what went wrong for learning

### ❌ Don't Do This:
- **Don't ignore dependencies:** Running 1.3.4 before 1.1.* will fail
- **Don't start too many windows:** More than 15 becomes hard to track
- **Don't skip validation:** Errors compound in later phases
- **Don't run different features' subtasks in same window:** Keep windows dedicated
- **Don't rush Phase 1:** It's the foundation for everything

---

## Example Session: Feature 1 with 12 Windows

### Setup (5 minutes)
```bash
# Open 12 browser tabs, label them:
Tab 1: F1-1.1.1
Tab 2: F1-1.1.2
Tab 3: F1-1.1.3
...
Tab 12: F1-1.2.6
```

### Phase 1 Execution (15 minutes)
```
10:00 - Paste all 12 prompts, press Enter on all tabs
10:07 - Tab 1 done ✅
10:09 - Tab 6 done ✅
10:11 - Tab 2 done ✅
...
10:15 - All 12 tabs done ✅
```

### Validation (2 minutes)
```
10:15 - Check VALIDATION for Tab 1 ✅
10:16 - Check VALIDATION for Tab 2 ✅
...
10:17 - All validations pass ✅
```

### Phase 2 Execution (20 minutes)
```
10:17 - Paste 8 new prompts into Tabs 1-8, press Enter
10:22 - Tab 5 done ✅
10:25 - Tab 1 done ✅
...
10:37 - All 8 tabs done ✅
```

### Continue through Phase 3, 4, 5...

### Integration Testing (30 minutes)
```
11:20 - Start integration test in Tab 1
11:50 - All tests pass ✅
```

**Total time:** 1 hour 50 minutes (vs. 4 hours sequential)

---

## Time Estimates by Feature (Maximum Parallelization)

| Feature | Subtasks | Max Parallel | Phases | Time (Parallel) | Time (Sequential) | Speedup |
|---------|----------|--------------|--------|-----------------|-------------------|---------|
| 1. Auth | 29 | 12 | 5 | 1.5h | 4h | 2.7x |
| 2. Analytics | 28 | 10 | 6 | 2h | 5h | 2.5x |
| 3. Notes | 16 | 8 | 4 | 1.5h | 3h | 2x |
| 4. Treatment | 22 | 9 | 5 | 2h | 4h | 2x |
| 5. Timeline | 13 | 6 | 4 | 1h | 2h | 2x |
| 6. Goals | 11 | 5 | 3 | 0.75h | 1.5h | 2x |
| 7. Export | 14 | 7 | 4 | 1.25h | 2.5h | 2x |
| 8. Compliance | 9 | 4 | 3 | 0.75h | 1.5h | 2x |
| **Total** | **142** | **12** | - | **~11h** | **~23h** | **2.1x** |

**Note:** "Max Parallel" is the maximum windows needed in any single phase.

---

## Recommended Build Order (Maximum Efficiency)

### Week 1: Core Features (Sequential)
- **Day 1:** Feature 1 (Auth) - 1.5 hours
- **Day 1:** Feature 6 (Goals) - 0.75 hours
- **Day 2:** Feature 8 (Compliance) - 0.75 hours
- **Day 2:** Feature 5 (Timeline) - 1 hour
- **Total:** 4 hours over 2 days

### Week 2: Complex Features (Parallel Swarm)
- **Day 3:** Features 2 + 3 simultaneously - 2 hours
- **Day 4:** Features 4 + 7 simultaneously - 2 hours
- **Total:** 4 hours over 2 days

### Week 3: Integration & Polish
- **Day 5:** Full integration testing - 2 hours
- **Day 6:** Bug fixes and deployment - 1 hour
- **Total:** 3 hours

**Grand Total:** 11 hours (vs. 23 hours sequential)

---

## Next Steps

1. **Read Feature 1 PARALLELIZATION MAP** (being generated now)
2. **Decide how many parallel windows you can manage** (start with 4-6)
3. **Start Feature 1 Phase 1** with your chosen window count
4. **Scale up** as you get comfortable

The agent is generating detailed parallelization maps for all features. You'll have specific guidance for each one!

Ready to start? 🚀
