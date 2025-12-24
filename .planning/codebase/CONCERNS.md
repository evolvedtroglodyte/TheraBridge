# Codebase Concerns

**Analysis Date:** 2026-01-08

## Tech Debt

**Large Component Files:**
- Issue: Components exceed 700 lines, mixing multiple concerns
- Files:
  - `frontend/app/patient/components/FullscreenChat/index.tsx` - 737 lines (message handling, UI rendering, share modal)
  - `backend/app/routers/sessions.py` - 1707 lines (all session endpoints, multiple analysis response types)
  - `backend/app/routers/demo.py` - 727 lines (background tasks mixed with route handlers)
- Why: Rapid prototyping during MVP phase, incremental feature additions
- Impact: Difficult to navigate, test, and maintain
- Fix approach: Extract subcomponents (ChatMessageInput, ChatHistory, ShareButton), split routers into service layer (`sessions/analysis.py`, `sessions/crud.py`)

**Deprecated Files Still In Codebase:**
- Issue: 7+ files marked .DEPRECATED still in repository
- Files:
  - `frontend/app/patient/components/Header.DEPRECATED.tsx`
  - `frontend/app/patient/components/TimelineSidebar.DEPRECATED.tsx`
  - `frontend/app/patient/components/HorizontalTimeline.DEPRECATED.tsx`
  - `frontend/app/patient/upload/page_old.tsx`
- Why: Fear of losing work-in-progress code
- Impact: Confusion about which code is active, clutter in file tree
- Fix approach: Remove from repository, rely on git history (commit before deletion)

**In-Memory State in Distributed System:**
- Issue: Demo status tracked in memory, lost on server restart
- Files:
  - `backend/app/routers/demo.py` lines 25-30 - `analysis_status = {}`, `running_processes = {}`
- Why: Quick prototype for demo mode
- Impact: Multiple server instances can't coordinate, orphaned subprocesses on restart
- Fix approach: Move to Redis or database-backed state, implement graceful shutdown handlers

**Excessive Debug Logging:**
- Issue: 714 console.log() calls across 136 files in production
- Files:
  - `frontend/app/patient/components/WaveCompletionBridge.tsx` - 26 console.log calls
  - `frontend/app/patient/lib/usePatientSessions.ts` - 16 console.log calls
- Why: Development debugging not cleaned up
- Impact: Noise in production logs, performance overhead
- Fix approach: Use conditional debug logger (`if (process.env.NEXT_PUBLIC_DEBUG_POLLING) console.log(...)`)

## Known Bugs

**SSE Event Queue Isolation:**
- Symptoms: SSE events never reach frontend despite successful analysis
- Trigger: Demo initialization with background subprocess
- Files:
  - `backend/app/services/pipeline_logger.py` - In-memory `_event_queue` dict
  - `backend/scripts/seed_wave1_analysis.py` - Subprocess writes to separate memory space
- Workaround: Polling fallback via `/api/demo/status` every 5 seconds
- Root cause: Subprocess isolation - parent and child have separate memory spaces
- Fix: Implement database-backed event queue (Redis or PostgreSQL)

**Race Condition in Session Updates:**
- Symptoms: SessionDetail shows stale data for 1-2 seconds after wave completion
- Trigger: User has SessionDetail open when wave completes
- Files:
  - `frontend/app/patient/components/SessionDetail.tsx`
  - `frontend/app/patient/lib/usePatientSessions.ts` - polling detects change, refreshes sessions array
- Workaround: Added 1s delay before refresh to allow backend database writes to complete
- Root cause: Database write + API fetch timing mismatch
- Fix: Use optimistic UI updates or subscribe to database change stream

## Security Considerations

**Exposed .env Files with Secrets:**
- Risk: API keys committed to git history
- Files:
  - `backend/.env` - Contains OPENAI_API_KEY, DATABASE_URL, JWT_SECRET
  - `frontend/.env.local` - Contains API credentials
- Current mitigation: None - .env files are tracked in git
- Recommendations:
  1. Remove .env from git history (`git filter-repo --path backend/.env --invert-paths`)
  2. Add .env to .gitignore (use .env.example only)
  3. Use Railway environment variables for production
  4. Rotate all exposed secrets (OPENAI_API_KEY, DATABASE_URL, JWT_SECRET)

**Server-Side Private Keys in Frontend API Routes:**
- Risk: Frontend API routes can impersonate backend with full privileges
- Files:
  - `frontend/app/api/check-email/route.ts` - Uses `process.env.SUPABASE_SERVICE_ROLE_KEY!`
  - `frontend/app/api/chat/route.ts` - Accesses `process.env.OPENAI_API_KEY`
- Current mitigation: None (API routes run server-side but keys shouldn't be in frontend codebase)
- Recommendations: Move to separate backend endpoints with proper auth, don't store server keys in frontend project

**Unsafe Environment Variable Access:**
- Risk: Missing credentials fail silently, requests fail with unclear errors
- Files:
  - `frontend/app/api/chat/route.ts` - `process.env.OPENAI_API_KEY || ''` (silent fallback)
- Current mitigation: None
- Recommendations: Throw error on missing credentials during startup, use Pydantic settings validation

## Performance Bottlenecks

**Polling Configuration Hardcoding:**
- Problem: Aggressive polling intervals with no adaptive backoff
- Files:
  - `frontend/lib/polling-config.ts` - Wave 1: 1s, Wave 2: 3s (hardcoded)
  - `frontend/app/patient/lib/usePatientSessions.ts` - No 429 handling
- Measurement: 1 request/second during Wave 1 (~60s), 1 request/3s during Wave 2 (~9.6min)
- Cause: Fixed intervals with no jitter or exponential backoff
- Improvement path: Add adaptive backoff on 429/500 errors, implement jitter to prevent thundering herd

**N+1 Session Transform Pattern:**
- Problem: Sessions array transformed on every render
- File: `frontend/app/patient/lib/usePatientSessions.ts` lines 235-249
- Measurement: .map() called on full sessions array every render (no profiling data)
- Cause: No memoization of transformed results
- Improvement path: Use `useMemo(() => sessions.map(...), [sessions])` to cache

**Database Query Efficiency:**
- Problem: Fetches all JSONB fields even when not needed
- File: `backend/app/routers/sessions.py` lines 214-219 - `select("*")`
- Measurement: Returns full transcript, deep_analysis, prose_analysis for list view
- Cause: No column selection optimization
- Improvement path: Fetch analysis fields separately for detail view only

## Fragile Areas

**Background Subprocess Orchestration:**
- Files:
  - `backend/app/routers/demo.py` lines 115-250 - subprocess streaming with basic error handling
- Why fragile: Race conditions between process.wait() and stream_output(), orphaned processes on server restart
- Common failures: Subprocess timeout doesn't kill child processes, SIGTERM doesn't cleanup running jobs
- Safe modification: Add signal handlers for graceful shutdown, implement process cleanup on exception
- Test coverage: No integration tests for subprocess lifecycle

**Demo Token Validation:**
- File: `backend/app/middleware/demo_auth.py`
- Why fragile: Only basic UUID format check, no expiry validation
- Common failures: Expired tokens pass validation, malformed Authorization headers crash
- Safe modification: Add comprehensive validation with clear error messages
- Test coverage: No unit tests for edge cases (expired tokens, malformed headers)

## Scaling Limits

**Railway Free Tier:**
- Current capacity: Unknown (no limits documented)
- Limit: Dependent on Railway plan
- Symptoms at limit: 429 rate limit errors, deployment failures
- Scaling path: Upgrade Railway plan

**In-Memory State:**
- Current capacity: Single-instance only
- Limit: Cannot horizontally scale with `analysis_status` dict
- Symptoms at limit: Multiple instances have inconsistent state
- Scaling path: Migrate to Redis for shared state

## Dependencies at Risk

**Python Version Inconsistency:**
- Risk: Scrapping project uses Python 3.11 (legacy)
- Files:
  - `Scrapping/.python-version` - Python 3.11
  - `.python-version`, `backend/.python-version`, `audio-transcription-pipeline/.python-version` - Python 3.13.9
- Impact: Import compatibility issues, deployment complexity
- Migration plan: Upgrade Scrapping to Python 3.13.9, test dependencies

## Missing Critical Features

**Graceful Shutdown of Subprocesses:**
- Problem: No signal handling for SIGTERM in backend
- Current workaround: Processes continue running if server restarts
- Blocks: Clean deployments, prevents resource leaks
- Implementation complexity: Medium (add signal handlers, track process PIDs, implement cleanup)

**Error Context in Async Operations:**
- Problem: Async errors lack contextual information
- Files:
  - `backend/app/middleware/demo_auth.py` line 82 - `asyncio.run()` called in sync function
- Current workaround: Basic try/except with generic error messages
- Blocks: Debugging production issues
- Implementation complexity: Low (add context managers, structured error logging)

## Test Coverage Gaps

**SSE Connection Logic:**
- What's not tested: Connection timeout, reconnection, event handling
- Files: `frontend/hooks/use-pipeline-events.ts`
- Risk: SSE connection failures go unnoticed, polling fallback may not activate correctly
- Priority: Medium
- Difficulty to test: Medium (requires mock EventSource)

**Demo Token Validation:**
- What's not tested: Expired tokens, malformed headers, missing tokens
- File: `backend/app/middleware/demo_auth.py`
- Risk: Invalid tokens may pass validation, security bypass possible
- Priority: High
- Difficulty to test: Low (unit tests with pytest)

**Polling Fallback Behavior:**
- What's not tested: Polling activation when SSE fails, status endpoint error handling
- File: `frontend/app/patient/lib/usePatientSessions.ts`
- Risk: Fallback may not activate correctly, infinite polling on errors
- Priority: High
- Difficulty to test: Medium (requires integration test with mock backend)

## Unfinished TODOs

**Session Action Bar:**
- Files:
  - `frontend/components/session/SessionActionBar.tsx` lines 49, 54
  - `// TODO: Implement download transcript/notes functionality`
  - `// TODO: Implement share functionality`
- Impact: User cannot export or share sessions
- Priority: Medium (feature incomplete)

**Chat Notification System:**
- File: `frontend/app/api/chat/route.ts` line 187
  - `// TODO: In future, flag for therapist notification (with permission)`
- Impact: Therapists miss important patient messages
- Priority: Low (future feature)

**Timeline Export with html2pdf.js:**
- File: `frontend/app/patient/lib/exportTimeline.ts` line 302
  - `// TODO: When implementing with html2pdf.js`
- Impact: PDF export not fully implemented
- Priority: Low (workaround exists)

**Scraper CSS Selectors:**
- Files: `Scrapping/src/scraper/scrapers/upheal_scraper.py` lines 68, 78, 88, 112-187
  - Multiple TODO comments for CSS selector updates
- Impact: Scraper may be non-functional after HTML changes
- Priority: High (if scraper is actively used)

---

*Concerns audit: 2026-01-08*
*Update as issues are fixed or new ones discovered*
