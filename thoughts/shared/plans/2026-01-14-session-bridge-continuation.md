# Session Bridge Backend Integration - Planning Continuation Prompt

**Date:** 2026-01-14
**Previous Session Token Limit:** 120k tokens reached
**Continuation Required:** Yes

---

## Prompt for Next Session

Use this exact prompt to continue planning:

```
Continue Session Bridge backend integration planning.

CONTEXT: Previous session reached 120k token limit during planning phase.

KEY DECISIONS ALREADY MADE:
1. Data structure: {nextSessionTopics: 3, shareProgress: 4, sessionPrep: 4}
2. Model: gpt-5-mini (configurable via env)
3. Input: Last 3 sessions FULL + progressively simpler summary of prior sessions (gradient complexity with recency)
   - Can use previous roadmap as input somewhere in temporal scope
4. Rename ALL "therapist bridge" → "session bridge"
5. Database: patient_session_bridge + session_bridge_versions (YES version history)
6. Generates after Session 1 (uses S1 data to suggest S2 prep)
7. API: /api/demo/session-bridge (aligned with existing /api/demo/roadmap pattern)
8. Cost tracking: Use track_generation_cost() pattern (already in roadmap_generator.py)
9. Priority: Maximize quality (Option B - hierarchical-style compaction, target ~$0.014 per 10-session demo)
10. Error handling: Same as Your Journey and other generations (show previous with warning)

CONTENT GUIDELINES (FROM USER ANSWERS):
- nextSessionTopics: BLEND of "carryover unfinished work" + "new directions based on progress"
  - Example: "Continue work on family boundaries" (carryover) + "Explore workplace perfectionism strategies" (new direction)
- shareProgress: QUALITATIVE insights, focus on INTER-SESSION progress (NOT in-session progress)
  - Things NOT shared with therapist yet OR things outside therapy
  - Does NOT include "emotional regulation during session" (that's in-session, not shareable)
  - Example: "Used assertiveness skills with mother" (outside therapy) ✓
  - Example: "Showed improved emotion regulation during session" (in-session) ✗
  - Eventually uses completed tasks as PRIMARY input, AI suggestions as supplementary
  - For now: Use AI suggestions with fallback logic (tasks integration comes later)
- sessionPrep: PATIENT-FACING reminders ("bring journal entries", "review anxiety journal")
- This is PATIENT DASHBOARD (not therapist-facing) - user confirmed "isnt that clear?"

REFRESH BEHAVIOR:
- Generates after Wave 2 completes (Option A)
- Will also regenerate when To-Do list updates (future: refresh button in corner)
- NOT showing progress across sessions (that's Your Journey)
- Shows inter-session progress to prepare for NEXT session

COMPACTION STRATEGY REQUIREMENT:
"Previous 3 sessions along with summary of any prior sessions in one spot with progressively simpler summary (gradient complexity with recency)"

COMPACTION STRATEGY DESIGN:
Based on user requirement: "Last 3 sessions FULL + progressively simpler summary of prior sessions (gradient complexity with recency)"

**Recommended Strategy: Gradient Hierarchical**
- Tier 1: Last 3 sessions (FULL Wave 1 + Wave 2 data)
- Tier 2: Sessions 4-7 (Medium detail - key insights from deep_analysis)
- Tier 3: Sessions 8+ (Simple summary - one-line per session from prose_analysis)
- Previous Roadmap: Include "Your Journey" summary for journey context
- Completed Tasks: Query tasks completed since last session (for shareProgress)

**Token Estimate:**
- Tier 1: 3 sessions × 750 tokens = 2,250 tokens
- Tier 2: 4 sessions × 150 tokens = 600 tokens (insights only)
- Tier 3: N sessions × 50 tokens = variable (prose first sentence)
- Previous Roadmap: ~800 tokens (summary + achievements)
- Completed Tasks: ~200 tokens
- System/User Prompts: ~500 tokens
- **Total Input: ~4,350-5,500 tokens**
- **Output: ~200 tokens (11 strings)**
- **Total: ~4,550-5,700 tokens per generation**

**Cost Estimate (gpt-5-mini):**
- Input: 5,000 tokens × $0.10 / 1M = $0.0005
- Output: 200 tokens × $0.30 / 1M = $0.00006
- **Total: ~$0.00056 per generation**
- **10 sessions: ~$0.0056 total** (well under $0.014 target)

**Implementation:**
- Create new `build_gradient_hierarchical_context()` function
- Reuse tier extraction helpers from roadmap_generator
- Add previous_roadmap integration
- Add completed_tasks query logic

**Why this strategy:**
✓ Matches user's exact specification (3 full + gradient summary)
✓ High quality (Tier 1 has full recent detail)
✓ Low cost (~5.5K tokens vs 10K for full hierarchical)
✓ Uses existing extraction patterns (insights, prose truncation)
✓ Includes roadmap for journey context
✓ Room for completed tasks without hitting token limits

Create implementation plan with this strategy.

REFERENCES:
- Read .claude/SESSION_LOG.md for PR #3 patterns
- backend/app/services/roadmap_generator.py (cost tracking)
- backend/scripts/generate_roadmap.py (compaction strategies)
- backend/app/services/session_insights_summarizer.py (updated with cost tracking)

SHAREPREOGRESS INTEGRATION:
- shareProgress section uses completed tasks from ToDoCard
- Query: patient_tasks WHERE completed=true AND completed_at > last_session_date
- Include in prompt as evidence of progress

OUTPUT: thoughts/shared/plans/2026-01-14-session-bridge-backend-integration.md
```

---

## To-Do Card Backend Integration - Future Session Prompt

```
Plan To-Do Card backend integration aligned with Your Journey and Session Bridge implementations.

CONTEXT FROM EXISTING CARDS:
**Your Journey (NotesGoalsCard) - PR #3:**
- Service: RoadmapGenerator (gpt-5.2)
- Strategy: Hierarchical compaction (3 tiers)
- Cost: $0.033 per 10-session demo
- Trigger: After each Wave 2 via subprocess.Popen
- Polling: roadmap_updated_at timestamp
- Database: patient_roadmap + roadmap_versions
- Frontend: API fetch, loading overlay, error states

**Session Bridge (SessionBridgeCard) - Just Implemented:**
- Service: SessionBridgeGenerator (gpt-5-mini)
- Strategy: Gradient hierarchical (3 full + progressive summary)
- Cost: $0.0056 per 10-session demo
- Structure: {nextSessionTopics: 3, shareProgress: 4, sessionPrep: 4}
- **CRITICAL:** shareProgress uses completed tasks as PRIMARY input (future)
- Trigger: After each Wave 2 + on To-Do list update
- Polling: session_bridge_updated_at timestamp
- Database: patient_session_bridge + session_bridge_versions

**To-Do Card (ToDoCard) - CURRENT STATE:**
- Frontend only: Local state with mock data
- Mock: 9 tasks (5 completed, 4 active)
- Structure: {id, text, completed, sessionId, sessionDate}
- UI: Checkbox toggles, progress bar (X% complete), Active/Completed sections
- Location: frontend/app/patient/components/ToDoCard.tsx
- No backend connection yet

IMPLEMENTATION REQUIREMENTS:

**Phase 1: Task Extraction from Wave 2**
- Create TaskExtractor service following patterns from mood_analyzer.py and topic_extractor.py
- Model: gpt-5-mini or gpt-5-nano (configurable via env - add to TASK_MODEL_ASSIGNMENTS)
- Input: deep_analysis JSONB + action_items from Wave 1
- Output: List of 3-5 tasks with {text, priority, category, rationale}
- Trigger: During Wave 2 orchestration (in seed_wave2_analysis.py after deep_analysis)
- Database: Add tasks JSONB column to therapy_sessions table
- Cost tracking: Use track_generation_cost() pattern
- Cost target: <$0.002 per session

**Phase 2: Patient Task Management**
- Database: Create patient_tasks table with columns:
  - id (UUID), patient_id (UUID), session_id (UUID), text (TEXT)
  - completed (BOOLEAN), completed_at (TIMESTAMP), created_at (TIMESTAMP)
  - No versioning table needed (tasks are current state only)
- API endpoints (new file: backend/app/routers/tasks.py):
  - GET /api/patients/{id}/tasks - Fetch all tasks
  - PATCH /api/tasks/{id}/complete - Toggle completion
  - POST /api/tasks - Manual task creation by patient (optional)
- Frontend: Update ToDoCard.tsx to use real API (remove mock data)
- Polling: Add tasks_updated_at to /api/demo/status response
- Context: Add tasksRefreshTrigger to SessionDataContext
- Loading: Use LoadingOverlay pattern (like Your Journey)

**Phase 3: Session Bridge Integration (CRITICAL BIDIRECTIONAL SYNC)**
This is the KEY integration point - Session Bridge shareProgress depends on completed tasks.

**3A. Session Bridge Query Logic:**
- When generating Session Bridge, query completed tasks since last session:
  ```sql
  SELECT * FROM patient_tasks
  WHERE patient_id = ?
    AND completed = true
    AND completed_at > last_session_date
    AND completed_at <= current_session_date
  ORDER BY completed_at DESC
  ```
- Pass completed_tasks to SessionBridgeGenerator.generate_bridge()
- Update SessionBridgeGenerator prompt to use tasks as PRIMARY evidence
- Store completed_tasks in session_bridge_versions.generation_context (for debugging)

**3B. Fallback Logic:**
- If no completed tasks: Use AI-generated progress suggestions (current behavior)
- If 1-2 completed tasks: Blend completed tasks + AI suggestions
- If 3+ completed tasks: Prioritize completed tasks, minimize AI suggestions

**3C. Prompt Integration:**
Example prompt section for shareProgress:
```
COMPLETED TASKS SINCE LAST SESSION:
✓ "Practice saying no to one request" (completed 2 days ago)
✓ "Journal about family boundary conversation" (completed yesterday)

Based on these completed tasks and session analysis, generate 4 shareProgress items
that highlight inter-session progress the patient can share with their therapist.
Focus on QUALITATIVE insights about what these completions reveal.
```

**Phase 4: Real-time Updates & Bidirectional Sync**
**4A. Wave 2 → Tasks → Session Bridge:**
- Wave 2 completes → TaskExtractor runs → Save tasks to patient_tasks
- Increment tasks_updated_at in demo status
- ToDoCard polls → Detects timestamp change → Refreshes task list
- Session Bridge generation includes newly available tasks

**4B. Task Completion → Session Bridge Refresh:**
- Patient toggles task completion via PATCH /api/tasks/{id}/complete
- Update tasks_updated_at timestamp
- ToDoCard refreshes immediately (optimistic update + confirmation)
- **Option 1 (Future):** Manual refresh button on Session Bridge card
- **Option 2 (Future):** Auto-regenerate Session Bridge when tasks complete (expensive)
- For initial implementation: Use manual refresh button approach

**Phase 5: Task Completion NOT in Mock Data by Default**
IMPORTANT: Unlike mock data (5/9 completed), real tasks start as ACTIVE:
- Tasks extracted from Wave 2 → completed = false
- Patient must manually toggle completion
- Session Bridge shareProgress will be empty initially (no completed tasks)
- This creates natural user flow: Do tasks → Mark complete → See in Session Bridge

ARCHITECTURE ALIGNMENT:
Follow PR #3 and Session Bridge patterns exactly:
- ✅ Service class with __init__(api_key, override_model)
- ✅ Async method with cost tracking (track_generation_cost)
- ✅ Database migration via Supabase MCP
- ✅ API endpoints with error handling
- ✅ TypeScript interfaces (TaskData, TaskMetadata, TaskResponse)
- ✅ Frontend polling with timestamp detection
- ✅ Loading overlay with LoadingOverlay component
- ✅ Context integration (add to SessionDataContext)

FILES TO CREATE:
- backend/app/services/task_extractor.py (LLM service)
- backend/app/routers/tasks.py (API endpoints)
- backend/supabase/migrations/0XX_create_patient_tasks.sql
- Add to frontend/lib/types.ts (TaskData, TaskMetadata interfaces)
- Add to frontend/lib/api-client.ts (getTasks, completeTask methods)

FILES TO MODIFY:
- backend/app/config/model_config.py (add "task_extraction" to TASK_MODEL_ASSIGNMENTS)
- backend/scripts/seed_wave2_analysis.py (call TaskExtractor after deep_analysis)
- backend/app/routers/demo.py (add tasks_updated_at to /api/demo/status)
- backend/app/services/session_bridge_generator.py (accept completed_tasks param)
- backend/scripts/generate_session_bridge.py (query tasks, pass to generator)
- frontend/app/patient/components/ToDoCard.tsx (replace mock with API)
- frontend/app/patient/contexts/SessionDataContext.tsx (add tasksRefreshTrigger)
- frontend/app/patient/lib/usePatientSessions.ts (detect tasks_updated_at changes)

SUCCESS CRITERIA:
✅ Tasks auto-extracted after each Wave 2 completes
✅ Patient can toggle task completion via checkbox in UI
✅ Completed tasks persist across sessions and page refreshes
✅ Session Bridge shareProgress reflects completed tasks (qualitative insights)
✅ ToDoCard updates in real-time when new session analyzed
✅ Cost <$0.002 per session for task extraction
✅ No regressions in existing Your Journey or Session Bridge features
✅ Loading states work correctly (overlay during fetch)
✅ Empty state shown when no tasks exist yet

TESTING CHECKLIST:
- [ ] Extract tasks from Session 1 Wave 2
- [ ] Verify tasks appear in ToDoCard as ACTIVE (not completed)
- [ ] Toggle task completion → Verify persistence
- [ ] Generate Session Bridge → Verify shareProgress is empty (no completed tasks)
- [ ] Complete 2-3 tasks → Regenerate Session Bridge → Verify shareProgress uses tasks
- [ ] Upload Session 2 → Verify new tasks extracted
- [ ] Verify tasks from Session 1 still visible in ToDoCard
- [ ] Test polling (complete task in one tab, see update in another)

REFERENCE SESSION_LOG.md ENTRIES:
- PR #3 Phase 1: Backend infrastructure (service + database)
- PR #3 Phase 3: Frontend integration (API client + polling)
- PR #3 Phase 5: Orchestration script integration
- Session Bridge implementation (just completed)

OUTPUT FILE: thoughts/shared/plans/YYYY-MM-DD-todo-card-backend-integration.md
```
