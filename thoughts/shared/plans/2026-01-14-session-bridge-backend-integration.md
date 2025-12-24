# Session Bridge Backend Integration - Implementation Plan

**Date:** 2026-01-14
**Feature:** Session Bridge card backend integration with gradient hierarchical compaction
**Based on:** PR #3 (Your Journey) implementation patterns
**Model:** gpt-5-mini (configurable via `SESSION_BRIDGE_MODEL_ASSIGNMENTS`)
**Estimated Cost:** ~$0.0056 per 10-session demo

---

## Key Architecture Decisions (From Research & User Confirmation)

**This section summarizes critical decisions confirmed through parallel research and user Q&A.**

**Session Name:** SESSION BRIDGE BACKEND INTEGRATION + MODEL TIER COST SAVINGS

### 1. Cost Tracking - ACTUAL Costs Only
- **Decision:** DELETE `estimate_cost()` function everywhere - use ONLY actual costs from API
- **Confirmation:** Research verified `track_generation_cost()` extracts real token counts from `response.usage`
- **Implementation:**
  - All 9 existing services use ACTUAL costs (verified in model_config.py lines 396-398)
  - `generation_costs` table is authoritative source (centralized cost tracking)
  - `*_versions.cost` column populated with ACTUAL cost (not character-based estimate)
  - DELETE `estimate_cost()` from generate_roadmap.py (lines 342-349, usage at line 169)
  - DO NOT add `estimate_cost()` to generate_session_bridge.py

### 2. Wave 3 Logging - Simple String Format
- **Decision:** Use simple wave names like "your_journey" and "session_bridge" (no prefixes)
- **Confirmation:** Research found existing waves use "mood", "topics", "deep" (NOT "(wave 2) deep")
- **Implementation:**
  - Follow analysis_orchestrator.py pattern (lines 548-574)
  - Logging functions: `_log_analysis_start()`, `_log_analysis_complete()`, `_log_analysis_failure()`
  - Status lifecycle: started → completed OR started → failed
  - Update `analysis_processing_log` CHECK constraint to include "your_journey" and "session_bridge"

### 3. total_sessions - Dynamic Calculation
- **Decision:** Calculate dynamically via query COUNT(*), NOT a dedicated database column
- **Confirmation:** Research found demo.py uses `len(sessions)` pattern (lines 502-503)
- **Implementation:**
  - Calculate in orchestration scripts: `total_sessions = len(all_sessions_result.data)`
  - Store result in metadata JSONB field
  - Empty state check: `total_sessions === 0` means no sessions uploaded yet
  - Increments automatically when sessions uploaded (via query)

### 4. Your Journey Rename - Comprehensive Scope
- **Decision:** Rename ALL "roadmap"/"NotesGoalsCard" references to "Your Journey"/"YourJourneyCard"
- **User confirmation:** "This is worth it"
- **Scope:** ~100+ references across 25+ files (database, backend, frontend, docs)
- **Critical:** Create migration 014 (Your Journey rename) BEFORE migration 015 (Session Bridge)
- **Document:** See `thoughts/shared/YOUR_JOURNEY_RENAME_CHECKLIST.md`

### 5. Inter-Session Progress Fallback Logic
- **Decision:** Use completed tasks as PRIMARY evidence, AI suggestions as fallback
- **User confirmation:** Correct logic is 0 tasks = all AI, 2 tasks = blend, 4+ = tasks only
- **Challenge:** How to detect TRUE inter-session progress vs in-session observations?
- **Solution:** Only completed tasks from To-Do Card are truly inter-session
- **Fallback strategy:**
  - **0 tasks:** Generate ALL 4 shareProgress items via AI (focus on "what therapist wants to hear")
  - **1-2 tasks:** BLEND tasks + AI suggestions
  - **3-4+ tasks:** Use ONLY tasks (minimize AI suggestions)

### 6. LLM Item Count Guarantees
- **Decision:** Use Wave 1 pattern (system prompt + post-validation), no retry logic
- **Confirmation:** Research found topic_extractor.py achieves 95% success rate with:
  - System prompt explicitly states "exactly 3 topics, exactly 4 shareProgress"
  - JSON examples showing correct structure
  - Post-validation truncation (`:3`, `:4`)
  - Post-validation padding (while loops with placeholders)
- **No merging logic needed** - proven pattern from existing services

### 7. Execution & Deployment Strategy (USER ANSWERS Q1-Q6)
- **Q1:** Wait for explicit approval before executing Your Journey rename
- **Q2:** Break into phases as needed with clear success criteria
- **Q3:** Create backup commit before starting any changes
- **Q4:** Pause after Your Journey rename for user review
- **Q5:** Implement Session Bridge in phases (0-7); can use parallel orchestrator with git worktrees if beneficial
- **Q6:** Create migrations in separate sessions (014 rename, then 015 Session Bridge)
- **Deployment:** Deploy immediately to Railway, user will test on deployment (not locally)
- **Testing:** Both backend phases (0-4) AND frontend phases (5-7), with minimal test (1-2 sessions)
- **Rollback:** Rely on git revert (no custom rollback scripts to avoid codebase bloat)

### 8. Cost Tracking & Historical Data (USER ANSWERS Q7-Q11)
- **Q7:** Leave historical `roadmap_versions` cost data as-is (don't backfill NULL)
- **Q8:** Add comment in schema noting cost column contains ACTUAL costs moving forward
- **Q9:** No backfill script needed - just ensure future costs use actual source
- **Q10:** Keep `cost` column in `*_versions` tables, populate with ACTUAL cost from track_generation_cost()
- **Q11:** No CHECK constraint needed to validate cost accuracy across tables

### 9. Wave 3 Logging Architecture (USER ANSWERS Q12-Q16 + RESEARCH)
- **Q12:** Create shared logging utility `backend/app/utils/wave_logging.py` - abstract as much as possible
- **Q13:** Use same async Supabase client pattern (only if it already works and isn't broken)
- **Q14:** Logging in ORCHESTRATION layer (scripts), NOT service layer - matches existing Wave 1/2 pattern
- **Q15:** Create NEW migration (016 or later) for CHECK constraint update (separate from 014/015)
- **Q16:** REMOVE CHECK constraint entirely to allow future wave names without migrations
- **Research finding:** Services are pure (no logging), scripts use PipelineLogger, follow exact pattern

### 10. Inter-Session Progress & AI Prompts (USER ANSWERS Q17-Q20)
- **Q17:** SPECULATIVE tone for 0-task AI fallback ("You might share...")
- **Q18:** AI suggestions should introduce UNRELATED progress areas (not expand on tasks)
- **Q19:** Add visual indicator (lightbulb icon) for AI-suggested shareProgress items
- **Q20:** Senior developer decision: Add task integration skeleton to SessionBridgeGenerator.generate_bridge() method with commented code + TODO comments

### 11. Tier 1 Context Extraction (USER ANSWERS Q21-Q23)
- **Q21:** Senior developer decision on extraction strategy (LLM vs rule-based vs separate utility)
- **Q22:** Use LLM call (GPT-5-mini) for extraction - better tailored to Session Bridge needs
- **Q23:** Cache insights in database (new column), generate NEW insights on every bridge generation

### 12. Frontend Integration Details (USER ANSWERS Q24-Q28)
- **Q24:** Manual refresh triggers ONLY SessionBridge (not Your Journey - doesn't track tasks)
- **Q25:** Keep 500ms loading overlay delay for visual consistency
- **Q26:** Button HIDDEN when NEXT_PUBLIC_ENABLE_MANUAL_REFRESH=false
- **Q27:** Empty state check in SessionDataContext (centralized)
- **Q28:** If sessions uploaded but no Wave 2: Show "Analysis in progress" (not "No sessions analyzed yet")

### 13. Database Schema & Metadata Strategy (USER ANSWERS Q29-Q33)
- **Q29:** Session Bridge metadata has SAME fields as Your Journey - abstract for shared editing
- **Q30:** Metadata should be SEPARATE SQL COLUMNS (not JSONB) with defined schema
- **Q31:** JSONB indexes explanation: GIN indexes on JSONB allow fast queries on nested fields (e.g., `WHERE metadata->>'sessions_analyzed' > 5`), but user needs clarification on implementation
- **Q32:** Unlimited version history (no retention policy for now - edge case won't be hit soon)
- **Q33:** Document deletion options in DECISIONS_AND_FEATURES.md, no actual deletion for now

### 14. Testing & Documentation (USER ANSWERS Q34-Q36)
- **Q34:** Test backend phases (0-4) first, THEN frontend phases (5-7) - both sequential testing
- **Q35:** Senior developer decision on test plan format (create MD if needed with clear scope in name)
- **Q36:** Minimal test (1-2 sessions) for Session Bridge

### 15. Environment Variables & Feature Flags (USER ANSWERS Q39-Q40 + RESEARCH)
- **Q39:** Session Bridge works with existing config - NO new env vars needed (verified via research)
- **Q40:** Always run after Wave 2 completes - NO feature flag needed (not configurable)
- **Research confirmation:** Wave 2 and Your Journey run without feature flags, Session Bridge follows same pattern

### 16. MODEL_TIER Feature - Cost Savings (NEW FEATURE REQUEST)
**User Request:** 3 model modes for testing and cost savings

**Mode Definitions (Q47 - names based on speed/quality, not money):**
- **Mode 1: TBD** - Existing setup (gpt-5.2, gpt-5, gpt-5-mini, gpt-5-nano) - $0.0423/session - HIGHEST quality, SLOWEST speed
- **Mode 2: TBD** - Replace gpt-5.2 & gpt-5 → gpt-5-mini - $0.0116/session (-73%) - BALANCED quality/speed
- **Mode 3: TBD** - Replace all → gpt-5-nano - $0.0034/session (-92%) - FASTEST speed, LOWER quality

**Implementation (Q46 - BEFORE Session Bridge):**
- Single env var: `MODEL_TIER=mode1|mode2|mode3` (names TBD based on speed/quality)
- Modify `get_model_name()` in `model_config.py` to check MODEL_TIER before returning model
- Add `MODEL_TIER_OVERRIDES` dict mapping tiers to model replacements
- Log tier selection on backend startup
- **Documentation (Q48):** Create `MODEL_TIER.md` (optional - only if beneficial, otherwise document in SESSION_LOG.md and CLAUDE.md)

**Use Cases:**
- Development: Mode 3 (fastest) for rapid iteration
- Staging/QA: Mode 2 (balanced) for pre-production testing
- Production: Mode 1 (highest quality) for customer-facing

**Research findings:** All services support `override_model` parameter, infrastructure-level change only

**Naming Research Needed:** Deploy agent to suggest names based on speed/quality (e.g., `precision`/`balanced`/`rapid`, `quality`/`standard`/`fast`, etc.)

---

## Final User Answers (Q41-Q56)

### Metadata Migration Strategy (Q41-Q43)
- **Q41:** Senior developer decision on migration sequence (A or B approach)
- **Q42:** Senior developer decision on JSONB → SQL migration approach (keep old column temporarily vs immediate drop)
- **Q43:** Metadata should be NESTED TABLE (not columns in main tables) - abstracted for shared editing
  - **CRITICAL ARCHITECTURE CHANGE:** Create `generation_metadata` table with foreign keys to `*_versions` tables
  - Abstract metadata handling so editing one affects both Your Journey and Session Bridge

### CHECK Constraint & Logging (Q44-Q45, Q49-Q51)
- **Q44:** Option A confirmed - UPDATE constraint to add new wave names (maintains data integrity)
- **Q45:** Senior developer decision on which migration gets CHECK constraint update
- **Q49:** Use BOTH PipelineLogger (pipeline_events) AND custom logging (analysis_processing_log)
- **Q50:** EXTEND LogPhase and LogEvent enums in pipeline_logger.py
- **Q51:** Create SHARED logging utility `backend/app/utils/wave_logging.py`

### Service Architecture (Q52-Q53)
- **Q52:** CREATE base class for services (code duplication is NEVER preferred) - abstract common patterns
- **Q53:** Use LLM call (gpt-5-mini) for Tier 1 extraction (Option A confirmed)

### Migration & Testing (Q54-Q56)
- **Q54:** Confirmed migration sequence is acceptable
- **Q55:** Use existing demo (10 sessions) but verify only first 2 sessions (Option B)
- **Q56:** Test each phase independently (Phase 0 → test → Phase 1 → test → ...) (Option B)

**CRITICAL RESEARCH NEEDED:**
1. Base class patterns for services (Q52 contradicts earlier research - need to design base class)
2. Nested metadata table architecture (Q43 - major schema change)
3. Dual logging implementation (Q49 - both PipelineLogger and analysis_processing_log)
4. MODEL_TIER naming based on speed/quality (Q47)

---

## Research Findings (2026-01-18)

**Research Document**: `thoughts/shared/research/2026-01-18-session-bridge-architecture-research.md`

### Summary

Comprehensive codebase research completed for all 4 critical architecture decisions. Key findings:

#### 1. Base Class Patterns ✅ RESEARCHED

**Current State**: NO base classes exist. All 9 AI services duplicate identical `__init__()` and cost tracking patterns (80+ lines of duplication).

**Recommendation**: Create `BaseAIGenerator` class to eliminate duplication.

**Key Pattern Found**:
- All services: OpenAI client initialization (async or sync)
- All services: `get_model_name(task_name, override_model)` for model selection
- All services: `track_generation_cost()` for cost tracking
- All services: Similar result structure `{data_key: data, metadata: {...}, cost_info: {...}}`

**Proposed Implementation**:
```python
# backend/app/services/base_generator.py
class BaseAIGenerator:
    def __init__(self, task_name, api_key=None, override_model=None, use_async_client=False)
    def build_result(self, data_key, data, metadata, cost_info)
    def track_cost(self, response, start_time, session_id, metadata)
```

**Benefits**: Eliminates 80+ lines of duplicate code, centralized client logic, consistent error handling.

#### 2. Nested Metadata Table Architecture ✅ RESEARCHED

**Current State**: Metadata stored as JSONB columns in `*_versions` tables (patient_roadmap.metadata, roadmap_versions.metadata).

**Recommendation**: Create `generation_metadata` table with polymorphic foreign keys.

**Proposed Schema**:
```sql
CREATE TABLE generation_metadata (
    id UUID PRIMARY KEY,
    your_journey_version_id UUID REFERENCES your_journey_versions(id),
    session_bridge_version_id UUID REFERENCES session_bridge_versions(id),
    sessions_analyzed INT NOT NULL,
    total_sessions INT NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    generation_timestamp TIMESTAMP NOT NULL,
    generation_duration_ms INT NOT NULL,
    -- CHECK: exactly one FK must be set
    CHECK (
        (your_journey_version_id IS NOT NULL AND session_bridge_version_id IS NULL) OR
        (your_journey_version_id IS NULL AND session_bridge_version_id IS NOT NULL)
    )
);
```

**Abstraction Layer**: `backend/app/utils/generation_metadata.py` with functions:
- `create_generation_metadata(db, your_journey_version_id=None, session_bridge_version_id=None, ...)`
- `get_generation_metadata(db, metadata_id)`
- `update_generation_metadata(db, metadata_id, updates)`

**Benefits**: Normalized data, shared editing ("editing one edits both"), eliminates JSONB index concerns.

#### 3. Dual Logging Implementation ✅ RESEARCHED

**Current State**: TWO independent logging systems exist:
- **PipelineLogger**: Logs to `pipeline_events` table (SSE events, demo orchestration)
  - Phases: TRANSCRIPT, WAVE1, WAVE2
  - Events: START, COMPLETE, FAILED, MOOD_ANALYSIS, TOPIC_EXTRACTION, etc.
- **analysis_processing_log**: Wave-specific status tracking
  - Wave names: "mood", "topics", "breakthrough", "deep" (simple strings, NO prefixes)
  - Status lifecycle: started → completed OR started → failed

**Recommendation**: Create `Wave3Logger` utility that logs to BOTH systems simultaneously.

**Proposed Implementation**:
```python
# backend/app/utils/wave_logging.py
class Wave3Logger:
    def __init__(self, patient_id, db)
    def log_generation_start(self, session_id, wave_name, event_type)  # Logs to BOTH systems
    def log_generation_complete(self, session_id, wave_name, event_type, duration_ms)
    def log_generation_failure(self, session_id, wave_name, event_type, error_message)
```

**Required Changes**:
1. Extend PipelineLogger enums:
   - Add `LogPhase.WAVE3`
   - Add `LogEvent.YOUR_JOURNEY_GENERATION`
   - Add `LogEvent.SESSION_BRIDGE_GENERATION`
2. Use simple wave names: "your_journey", "session_bridge" (match existing pattern)
3. No CHECK constraint on `analysis_processing_log.wave` (per Q16 - allow future waves)

**Benefits**: Single function call logs to both systems, consistent wave naming, centralized error handling.

#### 4. MODEL_TIER Naming ✅ RESEARCHED

**Current State**: Fixed model assignments per task (no tier system exists).

**Recommendation**: Implement 3-tier system with speed/quality-based names.

**Proposed Names**: `precision` / `balanced` / `rapid`

**Rationale**:
- "Precision" = highest accuracy (current production setup)
- "Balanced" = quality/speed middle ground
- "Rapid" = fastest processing
- Industry-standard terminology (ML/AI uses "precision" for accuracy)
- Clear progression without mentioning cost

**Implementation**:
```python
# backend/app/config/model_config.py
MODEL_TIER = os.getenv("MODEL_TIER", "precision")  # Default: highest quality

MODEL_TIER_OVERRIDES = {
    "precision": {},  # Use existing assignments
    "balanced": {
        # Replace gpt-5.2 & gpt-5 → gpt-5-mini (73% cost reduction)
        "deep_analysis": "gpt-5-mini",
        "prose_generation": "gpt-5-mini",
        "roadmap_generation": "gpt-5-mini",
        # ...
    },
    "rapid": {
        # Replace all → gpt-5-nano (92% cost reduction)
        "deep_analysis": "gpt-5-nano",
        "roadmap_generation": "gpt-5-nano",
        # ...
    }
}

def get_model_name(task, override_model=None):
    if override_model:
        return override_model
    tier = MODEL_TIER.lower()
    if tier in MODEL_TIER_OVERRIDES and task in MODEL_TIER_OVERRIDES[tier]:
        return MODEL_TIER_OVERRIDES[tier][task]
    return TASK_MODEL_ASSIGNMENTS.get(task, "gpt-5-mini")
```

**Cost Comparison** (10-session demo):
- Precision: $0.65 (baseline)
- Balanced: $0.18 (72% savings)
- Rapid: $0.04 (94% savings)

### User Answers (Q57-Q73) - FINAL ARCHITECTURE DECISIONS

**Q57**: Polymorphic (use polymorphic FK approach with CHECK constraint)
**Q58**: Yes, all (commit and push before starting refactor)
**Q59**: Editing the SCHEMA of metadata (can change table structure, abstraction handles both features)
**Q60**: You decide (base class type: abstract vs concrete vs mixin)
**Q61**: ALL 9 services should be refactored (commit and push before starting)
**Q62**: You decide (base class name)
**Q63-Q68**: You decide (event distribution, migration sequence, etc.)
**Q69**: All of the above (all architectural improvements apply)
**Q70**: Option A (implement MODEL_TIER BEFORE Session Bridge)
**Q71**: Use precision/balanced/rapid (approved - names from research)
**Q72**: You decide (remaining decisions)
**Q73**: You decide (remaining decisions)

**CRITICAL INSTRUCTION**: "Going forward before answering questions finish your research after thinking about my answers"

**REFACTOR SEQUENCE CONFIRMED**:
1. Commit and push current state (backup before refactor)
2. Implement MODEL_TIER feature FIRST (Q70 = Option A)
3. Refactor ALL 9 services to use base class (Q61 = ALL)
4. Then proceed with Session Bridge implementation

### User Answers (Q74-Q89) - IMPLEMENTATION DETAILS

**Base Class Design:**
- **Q74**: Abstract class (enforces contract, prevents direct instantiation)
- **Q75**: Approved "BaseAIGenerator" name
- **Q76**: Single class handles both sync and async clients (via `use_async_client` parameter)

**Event Distribution:**
- **Q77**: Approved distribution - ALL events go to BOTH systems (PipelineLogger + analysis_processing_log)
- **Q78**: Wave3Logger utility REQUIRED - refactor existing `generate_roadmap.py` to use it

**Migration Sequence:**
- **Q79**: Create all 3 migrations (014, 015, 016) BEFORE implementing
- **Q80**: REMOVE CHECK constraint entirely (maximum flexibility, no migrations for future waves)

**MODEL_TIER Implementation:**
- **Q81**: Separate `model_tier_config.json` file (more flexible, easier to update)
- **Q82**: Log info message only (no warning - "Using MODEL_TIER=balanced")
- **Q83**: Tier applies globally to all tasks (simpler)

**Service Refactor Testing:**
- **Q84**: Test each service individually (refactor one → test in demo → continue)
- **Q85**: 1-session test per service (verify output matches pre-refactor)

**Abstraction Layer:**
- **Q86**: CRUD + editing utilities (e.g., `update_sessions_analyzed()`, `update_model_used()`)
- **Q87**: Edit only affects `generation_metadata` table (normalized source of truth)

**Implementation Scope:**
- **Q88**: Confirmed - ALL improvements apply to both Your Journey AND Session Bridge

**Remaining Decisions:**
- **Q89**: Ask follow-up questions for each remaining decision (more collaborative)

### User Answers (Q90-Q108) - FINAL IMPLEMENTATION DECISIONS

**BaseAIGenerator Implementation:**
- **Q90**: Keep base class minimal (validation helpers in subclasses)
- **Q91**: Class constant with validation in `__init__` (simpler)
- **Q92**: Delete old code immediately (trust git history)
- **Q93**: Accept all OpenAI parameters (refer to docs via context7 MCP server)

**model_tier_config.json:**
- **Q94**: Read dynamically per request (allows runtime tier changes)
- **Q95**: Keep simple - tier applies globally (follows Q83)
- **Q96**: Log tier names and override counts on successful load

**generation_metadata Utilities:**
- **Q97**: Trust callers, let database enforce types (simpler)
- **Q98**: Require UUID objects only (strict type safety)
- **Q99**: Use `.single()` and return dict (enforces constraint)

**Wave3Logger:**
- **Q100**: No retries - log error and continue (logging failures don't block generation)
- **Q101**: Strict validation (only allow mapped wave names)
- **Q102**: Optional session_date parameter (matches PipelineLogger pattern)

**Migration Strategy:**
- **Q103**: Create all 3 SQL files now, apply in sequence (014 → 015 → 016)
- **Q104**: You decide (migration 016 optional vs required)
- **Q105**: Tables NOT empty - need to check via MCP and make data migration decision

**Implementation Sequence:**
- **Q106**: Complete sequence as needed (all phases listed)
- **Q107**: Test after each phase (safer, catches issues early)
- **Q108**: Use git commits and planning doc only (avoid extra file)

### Database Check Results (Q105 - Migration 014 Data)

**Query Results via Supabase MCP**:
- `patient_roadmap`: **10 rows** (production data exists)
- `roadmap_versions`: **56 rows** (version history exists)

**Decision on Q105 (Data Migration Strategy)**:
- **Strategy**: Use `ALTER TABLE RENAME` (automatic data preservation)
- **Rationale**: PostgreSQL `ALTER TABLE ... RENAME TO` preserves all data, indexes, and constraints automatically
- **No manual data migration needed**: Renaming tables is a metadata operation only
- **Foreign key updates**: Use `ALTER TABLE ... RENAME CONSTRAINT` to update FK names

**Migration 014 Structure**:
```sql
-- Rename tables (data preserved automatically)
ALTER TABLE patient_roadmap RENAME TO patient_your_journey;
ALTER TABLE roadmap_versions RENAME TO your_journey_versions;

-- Update foreign key constraint names for clarity
ALTER TABLE patient_your_journey
RENAME CONSTRAINT patient_roadmap_patient_id_fkey
TO patient_your_journey_patient_id_fkey;

ALTER TABLE your_journey_versions
RENAME CONSTRAINT roadmap_versions_patient_id_fkey
TO your_journey_versions_patient_id_fkey;
```

**Decision on Q104 (Migration 016 Optional vs Required)**:
- **Decision**: Migration 016 is **REQUIRED** for Wave 3
- **Rationale**: Without removing CHECK constraint, cannot insert wave='your_journey' or wave='session_bridge' into analysis_processing_log
- **Alternative rejected**: Updating constraint to add wave names defeats purpose (future waves would still need migrations)
- **Final approach**: REMOVE constraint entirely per Q80 decision

**CRITICAL NEXT STEPS**:
1. ✅ Update planning docs with Q90-Q108 answers (COMPLETE)
2. ✅ Check database for migration 014 data needs via Supabase MCP (COMPLETE - 10 + 56 rows found)
3. ✅ Make decision on Q104 (REQUIRED - must remove constraint for Wave 3)
4. ✅ Make decision on Q105 (ALTER TABLE RENAME - auto-preserves data)
5. ✅ Deploy Round 3 research agents (COMPLETE - 4 agents)
6. ✅ Ask final clarifying questions Q109-Q120 (COMPLETE)
7. Update planning docs with Q109-Q120 answers
8. Deploy final implementation prep research agents
9. Begin implementation

### User Answers (Q109-Q120) - FINAL EXECUTION DECISIONS

**Migration Execution & Testing:**
- **Q109**: Approved proposed sequence (014 → code updates → test → 016 → test → 015 → test)
- **Q110**: Two commits (migration 014 SQL → apply → code updates → commit)
- **Q111**: Run verification queries (check row counts match, data accessible)
- **Q112**: Prepare rollback SQL, apply manually only if issues found

**BaseAIGenerator Implementation:**
- **Q113**: MODEL_TIER first (follows Q70 decision)
- **Q114**: Pilot with 2 services (speaker_labeler + action_items_summarizer)
- **Q115**: DeepAnalyzer overrides `__init__()` to add `db` parameter
- **Q116**: Keep same file name (cleaner git history)

**MODEL_TIER Implementation:**
- **Q117**: Commit to git (configuration as code, version controlled)
- **Q118**: Single config file (use MODEL_TIER env var to switch)

**Documentation & Tracking:**
- **Q119**: Update SESSION_LOG.md after each major phase (incremental)
- **Q120**: Add "Implementation Progress" section + use git commits

---

## Implementation Progress

**Status**: Ready to begin implementation

**Execution Sequence** (approved Q109):
1. ☐ Create all 3 migration SQL files (014, 015, 016)
2. ☐ Apply migration 014 (Your Journey rename)
3. ☐ Verify production data (10 + 56 rows preserved)
4. ☐ Update backend code references (10 refs in 3 files)
5. ☐ Commit code updates
6. ☐ Test renamed tables work correctly
7. ☐ Apply migration 016 (remove CHECK constraint)
8. ☐ Test Wave 3 logging can insert new wave names
9. ☐ Implement MODEL_TIER feature
10. ☐ Test MODEL_TIER with 1-session demo
11. ☐ Implement BaseAIGenerator abstract class
12. ☐ Pilot refactor: speaker_labeler + action_items_summarizer
13. ☐ Test pilot services with 1-session demo
14. ☐ Refactor remaining 7 services
15. ☐ Test all 9 services with full demo
16. ☐ Implement Wave3Logger utility
17. ☐ Apply migration 015 (Session Bridge + generation_metadata)
18. ☐ Implement generation_metadata utilities
19. ☐ Implement Session Bridge backend

**Current Phase**: Pre-implementation research complete

**Next Action**: Deploy final research agents for implementation prep

---

## Round 2 Research Results (2026-01-18) - Implementation Details

### Agent 1: Abstract Class Patterns ✅ COMPLETE

**Research Focus**: Python ABC patterns for BaseAIGenerator design

**Key Findings**:

1. **Abstract vs Concrete Methods**:
   - **Abstract**: `generate()`, `_get_system_prompt()`, `_create_user_prompt()` - must be implemented by subclasses
   - **Concrete**: `_call_api()`, `_call_api_async()`, client initialization - shared implementation

2. **Client Initialization Pattern**:
   ```python
   from abc import ABC, abstractmethod
   from typing import TypeVar, Generic
   from openai import AsyncOpenAI, OpenAI

   ClientType = TypeVar('ClientType', OpenAI, AsyncOpenAI)

   class BaseAIGenerator(ABC, Generic[ClientType]):
       TASK_NAME: str = None  # Subclasses must override

       def __init__(self, api_key=None, override_model=None, use_async_client=False):
           if use_async_client:
               self.client: AsyncOpenAI = AsyncOpenAI(api_key=api_key)
           else:
               self.client: OpenAI = OpenAI(api_key=api_key)

           self.model = get_model_name(self.TASK_NAME, override_model)
   ```

3. **Type Hinting Strategy**:
   - Use `Generic[ClientType]` with `TypeVar` for client type safety
   - Subclasses declare: `MoodAnalyzer(BaseAIGenerator[AsyncOpenAI])`
   - Prevents `Union[AsyncOpenAI, OpenAI]` incompatibility issues

4. **Code Savings**:
   - **~25 lines saved per service** (client init, cost tracking, error handling)
   - **225 total lines eliminated** across 9 services
   - Centralized bug fixes (fix once vs 9 times)

5. **Migration Order** (recommended):
   - Async services first (lower risk): MoodAnalyzer → TopicExtractor → BreakthroughDetector → ActionItemsSummarizer
   - Sync services: SpeakerLabeler → SessionInsightsSummarizer → RoadmapGenerator → DeepAnalyzer → ProseGenerator

### Agent 2: model_tier_config.json Pattern ✅ COMPLETE

**Research Focus**: JSON configuration loading patterns for MODEL_TIER

**Key Findings**:

1. **File Location**: `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/config/model_tier_config.json`
   - Matches existing pattern: `technique_library.json` is in `backend/config/`
   - **NOT** in `backend/app/config/` (that's for Python modules)

2. **Loading Pattern** (from technique_library.py):
   ```python
   # Module-level cache (loaded once on first import)
   _tier_overrides_cache: Optional[Dict[str, Dict[str, str]]] = None

   def _load_tier_overrides() -> Dict[str, Dict[str, str]]:
       global _tier_overrides_cache

       if _tier_overrides_cache is not None:
           return _tier_overrides_cache

       # Path: backend/config/model_tier_config.json
       config_path = Path(__file__).parent.parent.parent / "config" / "model_tier_config.json"

       try:
           with open(config_path, 'r') as f:
               data = json.load(f)
           _tier_overrides_cache = data.get("tier_overrides", {})
           return _tier_overrides_cache
       except FileNotFoundError:
           logger.warning(f"Model tier config not found. Using defaults.")
           _tier_overrides_cache = {}
           return _tier_overrides_cache
   ```

3. **JSON Structure**:
   ```json
   {
     "metadata": {
       "version": "1.0.0",
       "available_tiers": ["precision", "balanced", "rapid"]
     },
     "tier_overrides": {
       "precision": {},
       "balanced": {
         "deep_analysis": "gpt-5-mini",
         "prose_generation": "gpt-5-mini"
       },
       "rapid": {
         "deep_analysis": "gpt-5-nano"
       }
     }
   }
   ```

4. **Error Handling**: Graceful degradation (FileNotFoundError → empty dict, no crashes)

5. **Integration**: Update `get_model_name()` to accept optional `tier` parameter:
   ```python
   def get_model_name(task, override_model=None, tier=None):
       if override_model:
           return override_model
       if tier and tier in tier_overrides and task in tier_overrides[tier]:
           return tier_overrides[tier][task]
       return TASK_MODEL_ASSIGNMENTS[task]
   ```

### Agent 3: CRUD + Editing Utilities ✅ COMPLETE

**Research Focus**: generation_metadata utility function patterns

**Key Findings**:

1. **Type Hints**:
   ```python
   from supabase import Client
   from uuid import UUID
   from typing import Optional

   def create_generation_metadata(
       db: Client,
       your_journey_version_id: Optional[UUID] = None,
       session_bridge_version_id: Optional[UUID] = None,
       ...
   ) -> dict:
   ```

2. **CRUD Operations**:
   - `create_generation_metadata()` - INSERT with polymorphic FK validation
   - `get_generation_metadata(db, metadata_id)` - SELECT by ID (.single())
   - `get_generation_metadata_by_version(db, your_journey_version_id=None, ...)` - SELECT by FK
   - `delete_generation_metadata(db, metadata_id)` - DELETE by ID
   - `update_generation_metadata(db, metadata_id, **updates)` - Generic UPDATE

3. **Editing Utilities** (per Q86):
   - `update_sessions_analyzed(db, metadata_id, new_count)` - Update specific field
   - `update_model_used(db, metadata_id, new_model)` - Update model field
   - `update_generation_timestamp(db, metadata_id, new_timestamp)` - Update timestamp
   - All wrap generic `update_generation_metadata()` for cleaner API

4. **Polymorphic FK Validation**:
   ```python
   def validate_exactly_one_fk(your_journey_version_id, session_bridge_version_id):
       fks_set = sum([
           your_journey_version_id is not None,
           session_bridge_version_id is not None
       ])
       if fks_set == 0:
           raise ValueError("Must provide exactly one version_id")
       elif fks_set > 1:
           raise ValueError("Cannot set both FKs")
   ```

5. **Error Handling**:
   - Record not found: `HTTPException(status_code=404)`
   - Database errors: Log with `logger.error()`, re-raise as `HTTPException(500)`
   - Validation errors: Raise `ValueError`

6. **Edit Constraints** (per Q87):
   - **Allowed fields**: sessions_analyzed, total_sessions, model_used, generation_timestamp, generation_duration_ms
   - **Forbidden fields**: FKs are immutable after creation (prevents orphaned metadata)

### Agent 4: Wave3Logger Dual Logging ✅ COMPLETE

**Research Focus**: Dual logging pattern (PipelineLogger + analysis_processing_log)

**Key Findings**:

1. **Wave3Logger Class**:
   ```python
   class Wave3Logger:
       EVENT_MAP = {
           "your_journey": LogEvent.YOUR_JOURNEY_GENERATION,
           "session_bridge": LogEvent.SESSION_BRIDGE_GENERATION,
       }

       def __init__(self, patient_id, db, pipeline_logger=None):
           self.pipeline_logger = pipeline_logger or PipelineLogger(patient_id, LogPhase.WAVE3)
           self.db = db

       def log_generation_start(self, session_id, wave_name, ...):
           # 1. Log to PipelineLogger (SSE)
           # 2. Log to analysis_processing_log (database)

       def log_generation_complete(self, session_id, wave_name, duration_ms, ...):
           # 1. Log complete to PipelineLogger
           # 2. UPDATE analysis_processing_log (status='completed')

       def log_generation_failure(self, session_id, wave_name, error_message, ...):
           # 1. Log failure to PipelineLogger
           # 2. UPDATE analysis_processing_log (status='failed')
   ```

2. **Required PipelineLogger Changes**:
   - Add `LogPhase.WAVE3` to enum
   - Add `LogEvent.YOUR_JOURNEY_GENERATION` to enum
   - Add `LogEvent.SESSION_BRIDGE_GENERATION` to enum

3. **Database Pattern** (from analysis_orchestrator.py):
   - Start: INSERT with status='started'
   - Complete: UPDATE status='completed' WHERE status='started'
   - Failure: UPDATE status='failed' WHERE status='started'

4. **Error Handling**: Graceful degradation
   - If PipelineLogger fails → log error, continue to database
   - If database fails → log error, SSE events still sent
   - Both failures logged, but don't crash generation

5. **Wave Names**: Simple strings ("your_journey", "session_bridge") - NO prefixes like "(wave 3)"

### Agent 5: Migration 016 Constraint Removal ✅ COMPLETE

**Research Focus**: How to remove CHECK constraint from analysis_processing_log

**Key Findings**:

1. **Current Constraint** (from migration 004):
   ```sql
   CONSTRAINT check_wave CHECK (wave IN ('mood', 'topics', 'breakthrough', 'deep'))
   ```

2. **Removal SQL**:
   ```sql
   ALTER TABLE analysis_processing_log
   DROP CONSTRAINT IF EXISTS check_wave;
   ```

3. **Idempotency**: `IF EXISTS` ensures migration can run multiple times safely

4. **Backward Compatibility**:
   - Existing data unchanged (no data migration needed)
   - Constraint removal only affects future INSERT/UPDATE operations
   - Can be re-added later (but shouldn't be - defeats purpose)

5. **Alternative Validation**: Application-level validation in service layer (each service defines its own wave constant)

6. **Migration File**: `backend/supabase/migrations/016_remove_wave_check_constraint.sql`

---

## Parallel Research Results (2026-01-18)

### Agent 1: Polymorphic FK Patterns ✅ COMPLETE

**Research Focus**: Polymorphic foreign key patterns, CHECK constraints, indexing strategies

**Key Findings**:

1. **Polymorphic FK Pattern**: Two nullable FK columns with CHECK constraint ensuring exactly one is set
   ```sql
   CHECK (
       (your_journey_version_id IS NOT NULL AND session_bridge_version_id IS NULL) OR
       (your_journey_version_id IS NULL AND session_bridge_version_id IS NOT NULL)
   )
   ```

2. **Indexing Strategy**: Partial indexes for optimal query performance
   ```sql
   CREATE INDEX idx_metadata_yj ON generation_metadata(your_journey_version_id)
       WHERE your_journey_version_id IS NOT NULL;
   CREATE INDEX idx_metadata_sb ON generation_metadata(session_bridge_version_id)
       WHERE session_bridge_version_id IS NOT NULL;
   ```

3. **Abstraction Layer**: Utility functions in `backend/app/utils/generation_metadata.py`
   - `create_generation_metadata(db, your_journey_version_id=None, session_bridge_version_id=None, ...)`
   - `get_generation_metadata(db, metadata_id)`
   - `update_generation_metadata(db, metadata_id, updates)`
   - Validates exactly one FK is set
   - Provides clean API for both features

4. **Benefits**: Normalized data, shared editing logic, eliminates JSONB duplication

### Agent 2: Abstract/Concrete Class Patterns ❌ EXPECTED FAILURE

**Research Focus**: Python abstract vs concrete class patterns for base class design

**Result**: Backend code not found in repository (expected - not committed yet)

**Recommendation**: Use research findings from existing service file patterns instead

### Agent 3: Service Refactor Strategy ✅ COMPLETE

**Research Focus**: Analyze all 9 AI services for safe refactoring

**Key Findings**:

1. **Services to Refactor (ALL 9)**:
   - mood_analyzer.py
   - topic_extractor.py
   - action_items_summarizer.py
   - breakthrough_detector.py
   - deep_analyzer.py
   - prose_generator.py
   - session_insights_summarizer.py
   - roadmap_generator.py
   - speaker_labeler.py

2. **Common Patterns Found**:
   - All use OpenAI client initialization (async or sync)
   - All use `get_model_name(task_name, override_model)` for model selection
   - All use `track_generation_cost()` for cost tracking
   - All return similar result structure: `{data_key: data, metadata: {...}, cost_info: {...}}`

3. **Dependencies**:
   - Services are independent (no circular dependencies)
   - All depend on `model_config.py` (safe to refactor after base class created)
   - Some services used by orchestration scripts (test after refactor)

4. **Test Coverage**:
   - No unit tests exist for services (manual testing required)
   - Integration tests via orchestration scripts
   - Test strategy: Refactor one service → test in demo → continue

5. **Recommended Refactor Order** (least risky → most risky):
   1. speaker_labeler.py (used only in transcription pipeline)
   2. action_items_summarizer.py (simple, Wave 1)
   3. topic_extractor.py (simple, Wave 1)
   4. mood_analyzer.py (simple, Wave 1)
   5. breakthrough_detector.py (simple, Wave 1)
   6. session_insights_summarizer.py (medium, Wave 2)
   7. deep_analyzer.py (complex, Wave 2, has DB dependency)
   8. prose_generator.py (medium, Wave 2)
   9. roadmap_generator.py (complex, Wave 3)

6. **Safety Measures**:
   - Commit and push before starting (per Q58, Q61)
   - Refactor one service at a time
   - Test each service after refactor
   - Use same model selection logic (no behavior changes)
   - Preserve cost tracking integration

### Agent 4: Event Logging Patterns ✅ COMPLETE

**Research Focus**: Dual logging implementation (PipelineLogger + analysis_processing_log)

**Key Findings**:

1. **PipelineLogger System** (`backend/app/utils/pipeline_logger.py`):
   - Logs to `pipeline_events` table (SSE events for frontend)
   - Phases: TRANSCRIPT, WAVE1, WAVE2 (add WAVE3 for Your Journey + Session Bridge)
   - Events: START, COMPLETE, FAILED, plus specific events (MOOD_ANALYSIS, etc.)
   - Used in demo orchestration scripts
   - Real-time event queue for SSE streaming

2. **analysis_processing_log System** (`backend/supabase/migrations/004_add_deep_analysis.sql`):
   - Logs to `analysis_processing_log` table (historical status tracking)
   - Wave names: "mood", "topics", "breakthrough", "deep" (simple strings, NO prefixes)
   - Status lifecycle: started → completed OR started → failed
   - Used by analysis_orchestrator.py
   - Methods: `_log_analysis_start()`, `_log_analysis_complete()`, `_log_analysis_failure()`

3. **Recommended Wave3Logger Utility** (`backend/app/utils/wave_logging.py`):
   ```python
   class Wave3Logger:
       def __init__(self, patient_id, db)
       def log_generation_start(self, session_id, wave_name, event_type)
       def log_generation_complete(self, session_id, wave_name, event_type, duration_ms)
       def log_generation_failure(self, session_id, wave_name, event_type, error_message)
   ```

4. **Required Changes**:
   - Extend PipelineLogger enums: `LogPhase.WAVE3`, `LogEvent.YOUR_JOURNEY_GENERATION`, `LogEvent.SESSION_BRIDGE_GENERATION`
   - Use simple wave names: "your_journey", "session_bridge"
   - No CHECK constraint on wave names (per Q16 - allow future waves)

5. **Benefits**: Single function call logs to both systems, consistent wave naming, centralized error handling

### Agent 5: Migration Dependencies ✅ COMPLETE

**Research Focus**: Analyze all migrations to determine safe execution sequence

**Key Findings**:

1. **Current Migrations (001-013)**:
   - 001: Initial schema (patients, therapists, sessions)
   - 002: Deep analysis fields
   - 003: Mood + topics
   - 004: analysis_processing_log table
   - 005-008: Various indexes and constraints
   - 009: generation_costs table
   - 010-012: Prose analysis, speaker labeling
   - 013: Your Journey (roadmap) tables

2. **Recommended Migration Sequence**:
   - **014**: Your Journey rename (patient_roadmap → patient_your_journey, etc.)
   - **015**: Session Bridge tables + generation_metadata table
   - **016**: UPDATE analysis_processing_log CHECK constraint (or REMOVE entirely per Q16)

3. **Migration 014 Prerequisites** (Your Journey Rename):
   - Must run BEFORE 015 (Session Bridge depends on renamed tables)
   - Renames: patient_roadmap → patient_your_journey, roadmap_versions → your_journey_versions
   - Updates all foreign key references
   - Zero data loss (just renaming)

4. **Migration 015 Structure** (Session Bridge + Metadata):
   ```sql
   -- Session Bridge tables (patient_session_bridge, session_bridge_versions)
   -- generation_metadata table with polymorphic FKs to your_journey_versions + session_bridge_versions
   ```

5. **Migration 016 Options**:
   - Option A: UPDATE CHECK constraint to add "your_journey", "session_bridge"
   - Option B: REMOVE CHECK constraint entirely (per Q16 - allow future waves)
   - Recommendation: Option B (more flexible, no migration needed for future waves)

6. **Safety Notes**:
   - All migrations are reversible (DROP TABLE, ALTER TABLE)
   - No data deletion required
   - Migrations can be tested on development branch first
   - Supabase MCP applies migrations safely

---

## Overview

Connect the Session Bridge card (currently using mock data in `TherapistBridgeCard.tsx`) to a real backend service that generates session preparation content after each Wave 2 analysis completes. The service will use **gradient hierarchical compaction** to provide cumulative context while managing token costs efficiently.

### Data Structure

```typescript
{
  "nextSessionTopics": [
    "Continue work on family boundaries",
    "Explore workplace perfectionism strategies",
    "Review progress with assertiveness skills"
  ],
  "shareProgress": [
    "Used assertiveness technique with mother during difficult conversation",
    "Practiced 4-7-8 breathing during anxiety episode at work",
    "Completed anxiety journal entries for 5 consecutive days",
    "Initiated social plans with friend (first time in 2 months)"
  ],
  "sessionPrep": [
    "Bring completed anxiety journal for review",
    "Be prepared to discuss family boundary conversation outcome",
    "Review notes from last session's homework assignment",
    "Consider examples of workplace perfectionism triggers"
  ]
}
```

**Content Guidelines (CONFIRMED):**
- **nextSessionTopics** (3 items): Blend of "carryover unfinished work" + "new directions based on progress"
- **shareProgress** (4 items): QUALITATIVE insights about INTER-SESSION progress ONLY
  - **STRICTLY EXCLUDE** all in-session observations
  - Things NOT shared with therapist yet OR things outside therapy
  - Example: "Used assertiveness skills with mother" ✓ (outside therapy)
  - Example: "Showed improved emotion regulation during session" ✗ (in-session, EXCLUDED)
  - **Initial implementation**: AI-generated with fallback (no task integration yet)
- **sessionPrep** (4 items): PATIENT-FACING reminders for next session

**Compaction Strategy (CONFIRMED):**
- **Gradient Hierarchical** (overrides "previous 3 sessions" specification)
  - Tier 1: Last 3 sessions - insights extracted (not full Wave 1 + Wave 2)
  - Tier 2: Sessions 4-7 - prose summaries (300 chars)
  - Tier 3: Sessions 8+ - journey arc (first sentence)
  - Previous Roadmap: Included for generation quality

---

## Implementation Clarifications (From Q&A Session)

### Retry & Error Handling Strategy
- **No retry logic** - Fail fast like other services (orchestrator-level retry will be abstracted later)
- **Safeguards instead of retries:**
  - **Pre-LLM validation**: Validate input structure and lengths
  - **Post-LLM validation**: Truncation + padding (replicate topic_extractor.py pattern)
- **Item count handling (CONFIRMED FROM WAVE 1 RESEARCH):**
  - **System prompt** explicitly states "exactly 3 topics, exactly 4 shareProgress, exactly 4 sessionPrep"
  - **Post-validation truncation**: `[:3]` and `[:4]` ensure maximum counts
  - **Post-validation padding**: While loops add generic placeholders if too few items
  - **No merging logic needed**: Wave 1 services achieve ~95% correct count without merging
  - **No second API call**: Single call + validation (proven pattern from topic_extractor.py)
- **LLM Prompt Strategy (all three approaches confirmed):**
  1. Clear count requirements in system prompt
  2. JSON examples showing exact structure with correct counts
  3. Validation warnings in prompt ("MUST return exactly X items")
- **Fail fast** - Log errors, track in `analysis_processing_log` table as "wave_3", don't retry

### Cost Tracking Architecture (CONFIRMED FROM RESEARCH)
- **CRITICAL:** Add exact same cost tracking as other 9 services (see SESSION_LOG.md 2026-01-14 entry)
- Pattern: `start_time` → API call → `track_generation_cost()` → persist to `generation_costs` table
- Task name: `"session_bridge"`
- Return `cost_info` in result dict
- **DELETE `estimate_cost()` everywhere** - Only use ACTUAL cost from API response
- All services use actual token counts from OpenAI API response:
  - `response.usage.prompt_tokens` (line 396 in model_config.py)
  - `response.usage.completion_tokens` (line 397 in model_config.py)
- **Dual Storage System (CONFIRMED):**
  - `generation_costs` table: Authoritative source (ACTUAL costs from API)
  - `*_versions.cost` column: Previously used ESTIMATED costs (character-based)
  - **Decision:** Use ACTUAL costs only, populate versions.cost with actual cost (remove estimate_cost)
- **Files to modify:**
  - DELETE `estimate_cost()` from `generate_roadmap.py` (lines 342-349)
  - DELETE usage of `estimate_cost()` from `generate_roadmap.py` (line 169)
  - DO NOT add `estimate_cost()` to `generate_session_bridge.py` (use actual cost only)
  - Populate `session_bridge_versions.cost` with `cost_info.cost` from track_generation_cost()

### Manual Refresh Button
- **Implementation:** Create new pattern (doesn't exist in codebase currently)
- **Icon:** `RotateCw` (single rotation) from lucide-react
- **Position:** Top-right corner (`absolute top-6 right-6`) - placeholder until design review
- **Behavior:** Direct API call with immediate state update (NO debounce)
- **Implementation approach:** `manualRefresh()` → `apiClient.getSessionBridge()` → update state
- **Config:** `NEXT_PUBLIC_ENABLE_MANUAL_REFRESH` (frontend env var) - button HIDDEN when false
- **Note:** Added to `DECISIONS_AND_FEATURES.md` - may move to header later

### Task Integration & Inter-Session Progress Fallback (CONFIRMED FROM USER)
- **Status:** Skeleton implementation (complete in PR #5)
- **Approach:** Add both commented-out code AND TODO comments
- **Query logic:** No `completed_at > last_session_date` requirement (tasks may be completed same day)
- **Data structure:** Match ToDoCard mock data structure
- **Integration plan:** Added to `DECISIONS_AND_FEATURES.md`

**Inter-Session Progress Detection & Fallback Logic (CONFIRMED):**
- **Primary source:** Completed tasks from To-Do Card (PR #5 integration)
- **Challenge:** How to detect TRUE inter-session progress vs in-session observations?
- **Solution:** Only completed tasks are truly inter-session (patient action outside therapy)
- **Fallback strategy when no completed tasks:**
  - **0 completed tasks:** Generate ALL 4 shareProgress items via AI
    - Focus on "what therapist wants to hear" (progress updates patient could share)
    - Examples: "Noticed anxiety triggers", "Thought about family boundaries"
    - Avoid quantitative metrics, avoid in-session observations
  - **1-2 completed tasks:** BLEND tasks + AI suggestions
    - Use completed tasks as primary evidence
    - Fill remaining slots with AI-generated progress items
  - **3-4+ completed tasks:** Use ONLY completed tasks (prioritize real evidence)
    - Truncate to 4 items max
    - Minimize AI suggestions (only if needed for context)
- **Prompt engineering:**
  - When tasks exist: "Based on these completed tasks, generate qualitative insights..."
  - When no tasks: "Generate 4 shareProgress items focusing on what the patient might share with therapist about progress outside therapy..."
- **Future enhancement (PR #5):** Action items from Wave 1 → To-Do tasks → Completed tasks → shareProgress evidence

### Tier 1 Context
- **Data source:** Insights extracted from `deep_analysis` (Option A)
- **Extraction logic:** NEW extraction (specific to Session Bridge needs)
  - Focus on: Actionable items for next session, recent behavioral changes, skills practiced outside therapy
  - Extract from: `breakthrough_patterns`, `themes`, `emotional_states`, `therapeutic_moments`
  - Prioritize inter-session relevance (not in-session observations)
- **Insight count:** Top 5 per session (limit to prevent token bloat while maintaining quality)

### Model Configuration
- **Location:** Existing `model_config.py` → `TASK_MODEL_ASSIGNMENTS["session_bridge"] = "gpt-5-mini"`
- **Configurable parameters:** Add as needed (retry attempts, backoff, counts, etc.)

### Compaction Details
- **Function name:** `build_gradient_hierarchical_context()` (distinguishes from roadmap's hierarchical)
- **Previous roadmap:** Include in separate prompt section for generation quality (full JSON, not truncated)

### Database Migration
- **Number:** `015_create_session_bridge_tables.sql` (after Your Journey rename migration 014)
- **Migration 014:** Your Journey rename MUST be applied first (see YOUR_JOURNEY_RENAME_CHECKLIST.md)
- **Application:** Run `mcp__supabase__apply_migration` immediately after creating SQL
- **Last confirmed migration:** 013 (checked migrations folder)

### Empty State & total_sessions Implementation (CONFIRMED FROM RESEARCH)
- **Primary message:** "Upload therapy sessions to generate your session preparation content"
- **Secondary message:** "Session preparation content will appear after analysis"
- **Logic:** Empty state ONLY shows when `total_sessions === 0` (no sessions uploaded)
- **After upload:** Show secondary message only (or loading if analysis in progress)

**total_sessions Implementation (CONFIRMED):**
- **NOT a database column** - calculated dynamically from query results
- **Calculation method (from demo.py lines 502-503):**
  ```python
  sessions = sessions_response.data or []
  session_count = len(sessions)
  ```
- **Storage:** Result stored in metadata JSONB field AFTER calculation
- **Frontend usage:** Passed via API response, displayed in session counter
- **Empty state check:** `total_sessions === 0` means no sessions in database yet
- **Increments automatically:** When sessions uploaded via COUNT(*) query

**Action required:**
  1. Fix NotesGoalsCard ("Your Journey" card) empty state logic to check `total_sessions === 0`
  2. Ensure "Your Journey" terminology is used (not "NotesGoalsCard")
  3. Update all database references to use "Your Journey" naming
  4. Session Bridge uses same pattern: calculate via `len(all_sessions_result.data)` in orchestration script
  5. **Execute comprehensive rename BEFORE Session Bridge implementation** (see checklist below)

**Your Journey Rename Checklist:**
- **Document:** `thoughts/shared/YOUR_JOURNEY_RENAME_CHECKLIST.md`
- **Scope:** ~100+ references across 25+ files (database, backend, frontend, docs)
- **Critical:** Create migration 014 FIRST (before Session Bridge migration 015)
- **Estimated time:** 2-3 hours with testing
- **User confirmed:** "This is worth it"

### Parallel Execution & Wave 3 Logging (CONFIRMED FROM RESEARCH)
- **Timing:** Roadmap + Session Bridge run exactly simultaneously (two `subprocess.Popen()` calls back-to-back)
- **Race conditions:** Unlikely (roadmap takes longer), will fix if occurs
- **Error independence:** Both fail independently, just log errors
- **Tracking:** All errors tracked in `analysis_processing_log` table

**Wave 3 Logging Pattern (CONFIRMED):**
- **Table:** `analysis_processing_log` (migration 004_add_deep_analysis.sql, lines 28-40)
- **Wave column:** VARCHAR(20) with simple strings (NOT prefixed with "(wave N)")
- **Existing wave names:** "mood", "topics", "breakthrough", "deep" (confirmed from analysis_orchestrator.py)
- **Wave 3 names for Session Bridge:** `"your_journey"` and `"session_bridge"`
  - Use "your_journey" (NOT "roadmap") - renamed throughout codebase
  - Use "session_bridge" for Session Bridge
- **Logging functions pattern (from analysis_orchestrator.py lines 548-574):**
  - `_log_analysis_start(session_id, wave, retry_count)` - status="started"
  - `_log_analysis_complete(session_id, wave, processing_duration_ms)` - status="completed"
  - `_log_analysis_failure(session_id, wave, error_message, retry_count)` - status="failed"
- **Status lifecycle:** started → completed OR started → failed
- **Implementation:** Add same logging pattern to generate_roadmap.py and generate_session_bridge.py

### Component Rename
- **Action:** `git mv TherapistBridgeCard.tsx SessionBridgeCard.tsx`
- **Scope:** Update ALL references, comments, variable names

### Loading States
- **Pattern:** Match existing implementation (NotesGoalsCard)
  - `isLoading` - initial load
  - `isRefreshing` - refresh overlay
  - `loadingSessionBridge` - context flag

---

## Phase 0: Database Schema & Migration

**CRITICAL:** Execute Your Journey rename (migration 014) BEFORE this phase. See `thoughts/shared/YOUR_JOURNEY_RENAME_CHECKLIST.md`.

### Tables to Create

**Current State Table: `patient_session_bridge`**

```sql
CREATE TABLE IF NOT EXISTS patient_session_bridge (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    bridge_data JSONB NOT NULL,  -- {nextSessionTopics: [], shareProgress: [], sessionPrep: []}
    metadata JSONB NOT NULL,  -- {sessions_analyzed, total_sessions, model_used, generation_timestamp, last_session_id, generation_duration_ms}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_session_bridge_patient ON patient_session_bridge(patient_id);
CREATE INDEX idx_session_bridge_updated ON patient_session_bridge(updated_at);

COMMENT ON TABLE patient_session_bridge IS 'Current session bridge data for each patient';
COMMENT ON COLUMN patient_session_bridge.metadata IS 'Metadata: {sessions_analyzed: int, total_sessions: int, model_used: str, generation_timestamp: str, last_session_id: uuid, generation_duration_ms: int}';
```

**Version History Table: `session_bridge_versions`**

```sql
CREATE TABLE IF NOT EXISTS session_bridge_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    version INT NOT NULL,  -- Incremental version number (1, 2, 3...)
    bridge_data JSONB NOT NULL,
    metadata JSONB NOT NULL,
    generation_context JSONB,  -- LLM input context for debugging
    cost FLOAT,  -- Estimated generation cost
    generation_duration_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(patient_id, version)
);

CREATE INDEX idx_session_bridge_versions_patient ON session_bridge_versions(patient_id);
CREATE INDEX idx_session_bridge_versions_created ON session_bridge_versions(created_at);

COMMENT ON TABLE session_bridge_versions IS 'Version history of all session bridge generations';
COMMENT ON COLUMN session_bridge_versions.generation_context IS 'Context passed to LLM for debugging (tier1, tier2, tier3, previous_roadmap, completed_tasks)';
```

### Migration File

**Filename:** `backend/supabase/migrations/015_create_session_bridge_tables.sql`

**Prerequisites:**
- Migration 014 (Your Journey rename) MUST be applied first
- Verify migration 014 completed: `SELECT * FROM supabase_migrations WHERE name = 'rename_roadmap_to_your_journey'`

**Apply via Supabase MCP:**
```bash
mcp__supabase__apply_migration(
  name="create_session_bridge_tables",
  query="<full SQL above>"
)
```

**Success Criteria:**
- [ ] Both tables created in Supabase
- [ ] Indexes created successfully
- [ ] Foreign key constraints enforced
- [ ] UNIQUE constraint on (patient_id, version) works

---

## Phase 1: Backend Service (SessionBridgeGenerator)

### File: `backend/app/services/session_bridge_generator.py`

**Pattern:** Replicate `roadmap_generator.py` structure exactly

#### Class Structure

```python
import os
import json
import time
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
import openai

from app.config.model_config import get_model_name, track_generation_cost, GenerationCost

CompactionStrategy = Literal["gradient_hierarchical"]

class SessionBridgeGenerator:
    """
    Generates session bridge content for patient dashboard.

    Session Bridge prepares patient for next therapy session by:
    - Suggesting topics to continue/explore (nextSessionTopics)
    - Highlighting inter-session progress to share (shareProgress)
    - Providing session preparation reminders (sessionPrep)
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize session bridge generator with OpenAI client.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
        """
        # Only pass api_key if explicitly provided, otherwise let OpenAI use env var
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var

        self.model = get_model_name("session_bridge", override_model=override_model)
        self.strategy: CompactionStrategy = "gradient_hierarchical"  # Only strategy supported

    def generate_bridge(
        self,
        patient_id: UUID,
        current_session: dict,  # Current session wave1 + wave2 data
        context: dict,  # Gradient hierarchical context
        sessions_analyzed: int,
        total_sessions: int,
        completed_tasks: list[dict] = None  # Future: tasks completed since last session
    ) -> dict:
        """
        Generate session bridge using gradient hierarchical compaction.

        Args:
            patient_id: Patient UUID
            current_session: Current session data (wave1 + wave2)
            context: Gradient hierarchical context from orchestration script
            sessions_analyzed: Number of sessions analyzed (for counter display)
            total_sessions: Total sessions uploaded (for counter display)
            completed_tasks: Tasks completed since last session (future integration)

        Returns:
            Bridge dict:
            {
                "bridge": {
                    "nextSessionTopics": [str, str, str],  # 3 topics
                    "shareProgress": [str, str, str, str],  # 4 progress items
                    "sessionPrep": [str, str, str, str]  # 4 prep items
                },
                "metadata": {
                    "sessions_analyzed": int,
                    "total_sessions": int,
                    "model_used": str,
                    "generation_timestamp": str,
                    "generation_duration_ms": int
                },
                "cost_info": dict  # Token usage and cost
            }
        """
        start_time = time.time()

        # Build prompt with gradient hierarchical context
        prompt = self._build_gradient_hierarchical_prompt(
            patient_id,
            current_session,
            context,
            sessions_analyzed,
            total_sessions,
            completed_tasks
        )

        # Call GPT-5-mini
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Track cost and timing
        cost_info = track_generation_cost(
            response=response,
            task="session_bridge",
            model=self.model,
            start_time=start_time,
            session_id=str(patient_id),
            metadata={"sessions_analyzed": sessions_analyzed}
        )

        # Parse and validate response
        bridge_data = json.loads(response.choices[0].message.content)
        bridge_data = self._validate_bridge_structure(bridge_data)

        # Return bridge with metadata and cost info
        return {
            "bridge": bridge_data,
            "metadata": {
                "sessions_analyzed": sessions_analyzed,
                "total_sessions": total_sessions,
                "model_used": self.model,
                "generation_timestamp": datetime.now().isoformat(),
                "generation_duration_ms": cost_info.duration_ms
            },
            "cost_info": cost_info.to_dict() if cost_info else None
        }

    def _get_system_prompt(self) -> str:
        """System prompt defining session bridge generation task"""
        return """You are a therapeutic session preparation assistant for mental health care.

Your task: Generate a "Session Bridge" that helps a patient prepare for their next therapy session.

The session bridge structure:
{
  "nextSessionTopics": [
    "Topic 1 (short phrase, 5-8 words)",
    "Topic 2 (short phrase, 5-8 words)",
    "Topic 3 (short phrase, 5-8 words)"
  ],
  "shareProgress": [
    "Progress 1 (1 sentence, qualitative insight)",
    "Progress 2 (1 sentence, qualitative insight)",
    "Progress 3 (1 sentence, qualitative insight)",
    "Progress 4 (1 sentence, qualitative insight)"
  ],
  "sessionPrep": [
    "Prep 1 (1 sentence, patient-facing reminder)",
    "Prep 2 (1 sentence, patient-facing reminder)",
    "Prep 3 (1 sentence, patient-facing reminder)",
    "Prep 4 (1 sentence, patient-facing reminder)"
  ]
}

Guidelines for nextSessionTopics:
- Blend of "carryover unfinished work" + "new directions based on progress"
- Short phrases (5-8 words max)
- Example: "Continue work on family boundaries"
- Example: "Explore workplace perfectionism strategies"

Guidelines for shareProgress:
- Focus on INTER-SESSION progress (NOT in-session progress)
- Things that happened OUTSIDE therapy OR things NOT yet shared with therapist
- QUALITATIVE insights (not quantitative metrics)
- Example: "Used assertiveness skills with mother during difficult conversation" ✓
- Example: "Showed improved emotion regulation during session" ✗ (in-session)
- Example: "Practiced 4-7-8 breathing during anxiety episode at work" ✓
- Example: "Mood score improved from 4 to 7" ✗ (quantitative)

Guidelines for sessionPrep:
- PATIENT-FACING reminders (not therapist notes)
- Concrete actions or things to bring
- Example: "Bring completed anxiety journal for review"
- Example: "Be prepared to discuss family boundary conversation outcome"

Tone: Supportive, encouraging, specific, actionable
Audience: Patient (not therapist)

Return your response as a JSON object with the session bridge structure.
"""

    def _build_gradient_hierarchical_prompt(
        self,
        patient_id: UUID,
        current_session: dict,
        context: dict,
        sessions_analyzed: int,
        total_sessions: int,
        completed_tasks: list[dict] = None
    ) -> str:
        """Build prompt with gradient hierarchical context."""

        # Build header
        header = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Gradient Hierarchical
You have access to:
- Tier 1: Last 3 sessions (FULL detail from Wave 1 + Wave 2)
- Tier 2: Sessions 4-7 (Medium detail - key insights)
- Tier 3: Sessions 8+ (Simple summary - one-line per session)
- Previous Roadmap: "Your Journey" summary for context
- Completed Tasks: Tasks completed since last session (future)
"""

        # Build tier sections
        tier_sections = []

        # Tier 3: Long-term trajectory (sessions 8+)
        tier3_summary = context.get("tier3_summary")
        if tier3_summary:
            tier_sections.append(f"TIER 3 - LONG-TERM TRAJECTORY (Sessions 8+):\n{tier3_summary}")

        # Tier 2: Mid-range summaries (sessions 4-7)
        tier2_summaries = context.get("tier2_summaries", {})
        if tier2_summaries:
            tier2_lines = ["TIER 2 - MID-RANGE HISTORY (Sessions 4-7):"]
            for session_range, summary in tier2_summaries.items():
                tier2_lines.append(f"\n{session_range}: {summary}")
            tier_sections.append("\n".join(tier2_lines))

        # Tier 1: Recent session insights (last 3 sessions)
        tier1_summaries = context.get("tier1_summaries", {})
        if tier1_summaries:
            tier1_lines = ["TIER 1 - RECENT SESSIONS (detailed insights from Wave 2):"]
            for session_key, insights in tier1_summaries.items():
                tier1_lines.append(f"\n{session_key}:")
                for insight in insights:
                    tier1_lines.append(f"  - {insight}")
            tier_sections.append("\n".join(tier1_lines))

        # Previous roadmap (Your Journey summary for context)
        previous_roadmap = context.get("previous_roadmap")
        if previous_roadmap:
            tier_sections.append(f"PREVIOUS ROADMAP (Your Journey - for context):\n{json.dumps(previous_roadmap, indent=2)}")

        # Completed tasks (future integration with To-Do card)
        if completed_tasks:
            task_lines = ["COMPLETED TASKS (since last session):"]
            for task in completed_tasks:
                task_lines.append(f"  ✓ \"{task['text']}\" (completed {task['completed_at']})")
            tier_sections.append("\n".join(task_lines))

        tier_context = "\n\n".join(tier_sections) + "\n\n" if tier_sections else ""

        # Build full prompt
        return f"""{header}

{tier_context}CURRENT SESSION DATA (Session {sessions_analyzed}):
{json.dumps(current_session, indent=2)}

Generate a "Session Bridge" that prepares the patient for their NEXT therapy session.

Focus on:
1. nextSessionTopics - What should continue or be explored next? (3 topics)
   - Blend carryover work + new directions based on recent progress

2. shareProgress - What inter-session progress can patient share? (4 items)
   - ONLY things that happened OUTSIDE therapy or NOT yet discussed
   - QUALITATIVE insights (not metrics)
   - Examples: "Practiced breathing during work anxiety", "Had boundary conversation with family"

3. sessionPrep - What should patient prepare or bring? (4 items)
   - Patient-facing reminders
   - Examples: "Bring journal entries", "Review homework notes"

Return your response as a JSON object with the session bridge structure.
"""

    def _validate_bridge_structure(self, bridge: dict) -> dict:
        """Validate and fix bridge structure with defensive defaults"""

        # Validate nextSessionTopics (expect 3)
        bridge.setdefault("nextSessionTopics", [])
        if not isinstance(bridge["nextSessionTopics"], list):
            bridge["nextSessionTopics"] = []
        bridge["nextSessionTopics"] = self._normalize_list(
            bridge["nextSessionTopics"],
            3,
            "Continue therapeutic work",
            "topics"
        )

        # Validate shareProgress (expect 4)
        bridge.setdefault("shareProgress", [])
        if not isinstance(bridge["shareProgress"], list):
            bridge["shareProgress"] = []
        bridge["shareProgress"] = self._normalize_list(
            bridge["shareProgress"],
            4,
            "Continued practice of skills outside therapy",
            "progress items"
        )

        # Validate sessionPrep (expect 4)
        bridge.setdefault("sessionPrep", [])
        if not isinstance(bridge["sessionPrep"], list):
            bridge["sessionPrep"] = []
        bridge["sessionPrep"] = self._normalize_list(
            bridge["sessionPrep"],
            4,
            "Review notes from previous session",
            "prep items"
        )

        return bridge

    def _normalize_list(self, items: list, expected_count: int, placeholder: str, field_name: str) -> list:
        """Normalize a list to expected count by padding or truncating"""
        if len(items) < expected_count:
            print(f"[WARNING] SessionBridgeGenerator: Expected {expected_count} {field_name}, got {len(items)}")
            items.extend([placeholder] * (expected_count - len(items)))
        return items[:expected_count]
```

**Model Configuration Update:**

**File:** `backend/app/config/model_config.py`

Add to `TASK_MODEL_ASSIGNMENTS` (around line 98):
```python
"session_bridge": "gpt-5-mini",  # Session bridge generation
```

Add to `ESTIMATED_TOKEN_USAGE` (around line 112):
```python
"session_bridge": {"input": 5500, "output": 200},  # ~$0.00056 per generation
```

**Success Criteria:**
- [ ] Service class created with correct initialization pattern
- [ ] `generate_bridge()` method returns correct structure
- [ ] System prompt defines QUALITATIVE inter-session progress rules
- [ ] Validation ensures 3 topics, 4 progress, 4 prep items
- [ ] Cost tracking integrated via `track_generation_cost()`
- [ ] Model configured as gpt-5-mini in `model_config.py`

---

## Phase 2: Orchestration Script

### File: `backend/scripts/generate_session_bridge.py`

**Pattern:** Replicate `generate_roadmap.py` structure exactly

```python
#!/usr/bin/env python3
"""
Generate Session Bridge for patient after Wave 2 analysis completes.

Usage: python scripts/generate_session_bridge.py <patient_id> <session_id>
"""

import sys
import os
import json
from datetime import datetime
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_supabase_admin
from app.services.session_bridge_generator import SessionBridgeGenerator

# --- Logging Helpers (for Railway) ---

def log_step(step: str, message: str) -> None:
    """Print a formatted step message with flush for Railway logs."""
    print(f"[{step}] {message}", flush=True)

def log_success(message: str) -> None:
    """Print a success message with flush for Railway logs."""
    print(f"  ✓ {message}", flush=True)

def log_error(message: str) -> None:
    """Print an error message with flush for Railway logs."""
    print(f"[ERROR] {message}", flush=True)

# --- Main Orchestration ---

def generate_session_bridge_for_session(patient_id: str, session_id: str) -> None:
    """Generate session bridge for a specific session."""

    print("\n" + "="*60)
    print("SESSION BRIDGE GENERATION")
    print("="*60 + "\n")

    supabase = get_supabase_admin()

    # Step 1: Fetch current session
    log_step("Step 1/4", "Fetching session data...")

    session_result = supabase.table("therapy_sessions") \
        .select("*") \
        .eq("id", session_id) \
        .execute()

    if not session_result.data:
        log_error(f"Session {session_id} not found")
        return

    current_session = session_result.data[0]

    # Verify Wave 2 complete
    if not current_session.get("prose_analysis"):
        log_error(f"Session {session_id} Wave 2 not complete (no prose_analysis)")
        return

    log_success(f"Session {session_id[:8]} loaded")

    # Step 2: Build gradient hierarchical context
    log_step("Step 2/4", "Building gradient hierarchical context...")

    context = build_gradient_hierarchical_context(patient_id, session_id, supabase)

    log_success(f"Context built ({len(json.dumps(context))} characters)")

    # Step 3: Count sessions for metadata
    log_step("Step 3/4", "Counting sessions...")

    all_sessions_result = supabase.table("therapy_sessions") \
        .select("id, prose_analysis") \
        .eq("patient_id", patient_id) \
        .execute()

    sessions_with_wave2 = [s for s in all_sessions_result.data if s.get("prose_analysis")]
    sessions_analyzed = len(sessions_with_wave2)
    total_sessions = len(all_sessions_result.data)

    log_success(f"{sessions_analyzed}/{total_sessions} sessions analyzed")

    # Step 4: Generate session bridge
    log_step("Step 4/4", "Generating session bridge...")

    generator = SessionBridgeGenerator()

    # Build current session data for bridge
    current_session_data = {
        "wave1": {
            "session_id": session_id,
            "session_date": current_session["session_date"],
            "mood_score": current_session["mood_score"],
            "topics": current_session["topics"],
            "action_items": current_session["action_items"],
            "technique": current_session["technique"],
            "summary": current_session["summary"],
        },
        "wave2": current_session["deep_analysis"]
    }

    result = generator.generate_bridge(
        patient_id=UUID(patient_id),
        current_session=current_session_data,
        context=context,
        sessions_analyzed=sessions_analyzed,
        total_sessions=total_sessions,
        completed_tasks=None  # Future: query completed tasks
    )

    bridge_data = result["bridge"]
    metadata = result["metadata"]

    log_success(f"Bridge generated ({metadata['generation_duration_ms']}ms)")

    # Step 5: Update database
    log_step("Step 5/5", "Updating database...")

    # Get current version number
    versions_result = supabase.table("session_bridge_versions") \
        .select("version") \
        .eq("patient_id", patient_id) \
        .order("version", desc=True) \
        .limit(1) \
        .execute()

    current_version = versions_result.data[0]["version"] if versions_result.data else 0
    new_version = current_version + 1

    # Insert new version
    supabase.table("session_bridge_versions").insert({
        "patient_id": patient_id,
        "version": new_version,
        "bridge_data": bridge_data,
        "metadata": metadata,
        "generation_context": context,
        "cost": result["cost_info"]["cost"] if result.get("cost_info") else None,
        "generation_duration_ms": metadata["generation_duration_ms"]
    }).execute()

    log_success(f"Version {new_version} saved to session_bridge_versions")

    # Upsert to patient_session_bridge (latest version)
    supabase.table("patient_session_bridge").upsert({
        "patient_id": patient_id,
        "bridge_data": bridge_data,
        "metadata": metadata,
        "updated_at": datetime.now().isoformat()
    }, on_conflict="patient_id").execute()

    log_success("Latest bridge saved to patient_session_bridge")

    # Log cost info
    if result.get("cost_info"):
        cost_info = result["cost_info"]
        log_success(f"Cost tracked: ${cost_info['cost']:.6f} (input: {cost_info['input_tokens']} tokens, output: {cost_info['output_tokens']} tokens)")

    # Print summary
    print("\n" + "="*60)
    print(f"✓ Session Bridge v{new_version} generated successfully")
    print(f"  Duration: {metadata['generation_duration_ms']}ms")
    print(f"  Model: {metadata['model_used']}")
    print(f"  Sessions: {sessions_analyzed}/{total_sessions}")
    print("="*60 + "\n")

# --- Context Building (Gradient Hierarchical Only) ---

def build_gradient_hierarchical_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """
    Build gradient hierarchical context for session bridge.

    Tier structure:
    - Tier 1: Last 3 sessions (FULL Wave 1 + Wave 2 data)
    - Tier 2: Sessions 4-7 (first 300 chars of prose_analysis)
    - Tier 3: Sessions 8+ (first sentence of prose_analysis)
    - Previous Roadmap: "Your Journey" summary for context
    """

    # Get all previous sessions with Wave 2 complete
    sessions_result = supabase.table("therapy_sessions") \
        .select("id, session_date, mood_score, topics, action_items, technique, summary, deep_analysis, prose_analysis") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    sessions_with_wave2 = [s for s in sessions_result.data if s.get("prose_analysis")]
    num_sessions = len(sessions_with_wave2)

    # Get previous roadmap if exists (for context)
    roadmap_result = supabase.table("patient_roadmap") \
        .select("roadmap_data") \
        .eq("patient_id", patient_id) \
        .execute()

    previous_roadmap = roadmap_result.data[0]["roadmap_data"] if roadmap_result.data else None

    # Distribute sessions into tiers (from most recent backwards)
    sessions_reversed = list(reversed(sessions_with_wave2))

    # Tier 1: Last 3 sessions (FULL Wave 1 + Wave 2 data) - dict format
    tier1_summaries = {}
    for session in sessions_reversed[:3]:
        session_key = f"Session {session['session_date'][:10]}"
        tier1_summaries[session_key] = {
            "mood_score": session.get("mood_score"),
            "topics": session.get("topics"),
            "action_items": session.get("action_items"),
            "technique": session.get("technique"),
            "summary": session.get("summary"),
            "deep_analysis": session.get("deep_analysis")
        }

    # Tier 2: Sessions 4-7 (paragraph summaries - first 300 chars)
    tier2_summaries = {}
    if num_sessions >= 4:
        for session in sessions_reversed[3:7]:
            session_range = f"Session {session['session_date'][:10]}"
            tier2_summaries[session_range] = truncate_prose(session.get("prose_analysis", ""), 300)

    # Tier 3: Sessions 8+ (journey arc - first sentence per session)
    tier3_summary = None
    if num_sessions >= 8:
        arc_pieces = [
            f"{session['session_date'][:10]}: {session.get('prose_analysis', '').split('.')[0]}"
            for session in sessions_reversed[7:]
        ]
        tier3_summary = " | ".join(arc_pieces)

    return {
        "tier1_summaries": tier1_summaries,
        "tier2_summaries": tier2_summaries,
        "tier3_summary": tier3_summary,
        "previous_roadmap": previous_roadmap
    }

def truncate_prose(prose: str, max_length: int) -> str:
    """Truncate prose to max_length, adding ellipsis if needed."""
    if not prose:
        return ""
    if len(prose) <= max_length:
        return prose
    return prose[:max_length] + "..."

# NOTE: estimate_cost() function REMOVED - use actual cost from track_generation_cost()
# Cost is now tracked accurately via OpenAI API response (response.usage.prompt_tokens/completion_tokens)
# Cost stored in generation_costs table and populated to versions.cost field

# --- CLI Entry Point ---

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/generate_session_bridge.py <patient_id> <session_id>")
        sys.exit(1)

    patient_id = sys.argv[1]
    session_id = sys.argv[2]

    generate_session_bridge_for_session(patient_id, session_id)
```

**Integration with Wave 2 Completion:**

**File:** `backend/scripts/seed_wave2_analysis.py`

Add after roadmap generation (around line 445):

```python
# Generate session bridge (non-blocking, detached process)
session_bridge_script = os.path.join(os.path.dirname(__file__), "generate_session_bridge.py")
subprocess.Popen(
    [sys.executable, session_bridge_script, patient_id, session['id']],
    stdout=None,  # Inherit parent's stdout (Railway captures this)
    stderr=None,  # Inherit parent's stderr
    env=os.environ.copy(),  # Pass environment variables (OPENAI_API_KEY, etc.)
    start_new_session=True  # Detach from parent process group
)
print(f"    [Session Bridge] Non-blocking generation initiated for session {session['id'][:8]}")
```

**Success Criteria:**
- [ ] Script runs standalone: `python scripts/generate_session_bridge.py <patient_id> <session_id>`
- [ ] Gradient hierarchical context builds correctly (3 tiers + roadmap)
- [ ] SessionBridgeGenerator called with correct parameters
- [ ] Database writes succeed (versions table + current table)
- [ ] Logs appear in Railway console
- [ ] Non-blocking execution works (Wave 2 script exits immediately)

---

## Phase 3: API Endpoint

### File: `backend/app/main.py`

Add endpoint (around line 85, after `/roadmap` endpoint):

```python
@app.get("/api/patients/{patient_id}/session-bridge")
async def get_session_bridge(patient_id: str, db=Depends(get_supabase)):
    """
    Get current session bridge for patient.

    Returns 404 if no session bridge exists (0 sessions analyzed).
    Frontend treats 404 as success with null data (empty state).
    """
    result = db.table("patient_session_bridge") \
        .select("bridge_data, metadata") \
        .eq("patient_id", patient_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Session bridge not found")

    return {
        "bridge": result.data[0]["bridge_data"],
        "metadata": result.data[0]["metadata"]
    }
```

**Status Endpoint Integration:**

**File:** `backend/app/routers/demo.py`

Update `/api/demo/status` endpoint (around line 570):

```python
# Fetch session bridge timestamp
session_bridge_response = db.table("patient_session_bridge") \
    .select("updated_at") \
    .eq("patient_id", patient_id) \
    .execute()

status["session_bridge_updated_at"] = (
    session_bridge_response.data[0]["updated_at"]
    if session_bridge_response.data
    else None
)
```

**Success Criteria:**
- [ ] `GET /api/patients/{patient_id}/session-bridge` returns bridge data
- [ ] 404 returned when no bridge exists
- [ ] `/api/demo/status` includes `session_bridge_updated_at` timestamp
- [ ] CORS configured correctly for frontend access

---

## Phase 4: Frontend API Client Integration

### File: `frontend/lib/api-client.ts`

Add method (around line 549, after `getRoadmap`):

```typescript
/**
 * Get session bridge for patient
 */
async getSessionBridge(patientId: string): Promise<{ success: boolean; data?: any; error?: string }> {
  const result = await this.get<any>(`/api/patients/${patientId}/session-bridge`);

  if (result.success) {
    return { success: true, data: result.data };
  }

  // 404 means no session bridge yet - treat as success with null data
  if (result.status === 404) {
    return { success: true, data: null };
  }

  return { success: false, error: result.error };
}
```

### File: `frontend/lib/types.ts`

Add interfaces (around line 363, after `RoadmapResponse`):

```typescript
export interface SessionBridgeData {
  readonly nextSessionTopics: string[];       // Array of 3 topics
  readonly shareProgress: string[];           // Array of 4 progress items
  readonly sessionPrep: string[];             // Array of 4 prep items
}

export interface SessionBridgeMetadata {
  readonly sessions_analyzed: number;
  readonly total_sessions: number;
  readonly model_used: string;
  readonly generation_timestamp: string;
  readonly generation_duration_ms: number;
}

export interface SessionBridgeResponse {
  readonly bridge: SessionBridgeData;
  readonly metadata: SessionBridgeMetadata;
}
```

**Success Criteria:**
- [ ] API client method returns correct type structure
- [ ] 404 responses transformed to `{ success: true, data: null }`
- [ ] TypeScript interfaces match backend response structure
- [ ] No build errors

---

## Phase 5: Frontend Context Integration

### File: `frontend/app/patient/contexts/SessionDataContext.tsx`

Add to context interface (around line 42):

```typescript
interface SessionDataContextType {
  // ... existing fields ...

  /** Increments when session bridge data should be refetched */
  sessionBridgeRefreshTrigger: number;
  /** Trigger session bridge refresh (for SSE handler when Wave 2 completes) */
  setSessionBridgeRefreshTrigger: React.Dispatch<React.SetStateAction<number>>;
  /** Backend is generating session bridge (shows loading state) */
  loadingSessionBridge: boolean;
}
```

### File: `frontend/app/patient/lib/usePatientSessions.ts`

Add state and return value (around line 170 and 545):

```typescript
// Add state
const [sessionBridgeRefreshTrigger, setSessionBridgeRefreshTrigger] = useState<number>(0);

// Add to return value
return {
  // ... existing fields ...
  sessionBridgeRefreshTrigger,
  setSessionBridgeRefreshTrigger,
  loadingSessionBridge: false  // Future: detect from SSE events
};
```

**Success Criteria:**
- [ ] Context exposes `sessionBridgeRefreshTrigger`
- [ ] Context exposes `setSessionBridgeRefreshTrigger`
- [ ] Context exposes `loadingSessionBridge`
- [ ] No TypeScript errors
- [ ] Existing components still render

---

## Phase 6: Frontend Component Integration

### File: `frontend/app/patient/components/SessionBridgeCard.tsx`

**Rename from TherapistBridgeCard.tsx:**
```bash
git mv frontend/app/patient/components/TherapistBridgeCard.tsx frontend/app/patient/components/SessionBridgeCard.tsx
```

**Replace entire file:**

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionData } from '../contexts/SessionDataContext';
import { apiClient } from '@/lib/api-client';
import { SessionBridgeData, SessionBridgeMetadata } from '@/lib/types';
import { LoadingOverlay } from './LoadingOverlay';

// Font configuration
const fontSans = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const fontSerif = 'Charter, "Bitstream Charter", Georgia, serif';

// Shared styles
const cardBaseClasses = "bg-[#ECEAE5] dark:bg-[#1A1625] p-8 rounded-2xl relative h-[400px] flex flex-col";

interface PlaceholderCardProps {
  message: string;
  secondaryMessage?: string;
  isError?: boolean;
  showOverlay?: boolean;
}

function PlaceholderCard({ message, secondaryMessage, isError, showOverlay }: PlaceholderCardProps): React.ReactElement {
  const messageClass = isError ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400';

  return (
    <div className={`relative ${cardBaseClasses}`}>
      {showOverlay && <LoadingOverlay visible={true} />}
      <div className="flex flex-col items-center justify-center h-full text-center">
        <CardTitle />
        <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className={`${messageClass} mb-2`}>
          {message}
        </p>
        {secondaryMessage && (
          <p style={{ fontFamily: fontSans, fontSize: '12px' }} className="text-gray-500 dark:text-gray-500">
            {secondaryMessage}
          </p>
        )}
      </div>
    </div>
  );
}

function CardTitle(): React.ReactElement {
  return (
    <h2
      style={{ fontFamily: fontSans, fontSize: '18px', fontWeight: 600 }}
      className="text-gray-900 dark:text-white mb-6"
    >
      Session Bridge
    </h2>
  );
}

interface BulletListProps {
  items: string[];
  bulletSize?: 'small' | 'medium';
}

function BulletList({ items, bulletSize = 'small' }: BulletListProps): React.ReactElement {
  const sizeClasses = bulletSize === 'small' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  return (
    <ul className="space-y-2">
      {items.map((item, idx) => (
        <li key={idx} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
          <span className={`${sizeClasses} rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0`} />
          <span style={{ fontFamily: fontSerif, fontSize: '14px' }}>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function getSessionCounterText(sessionsAnalyzed: number, totalSessions: number): string {
  const plural = totalSessions !== 1 ? 's' : '';
  return `Based on ${sessionsAnalyzed} out of ${totalSessions} uploaded session${plural}`;
}

export function SessionBridgeCard(): React.ReactElement {
  const { patientId, loadingSessionBridge, sessionBridgeRefreshTrigger } = useSessionData();
  const [bridgeData, setBridgeData] = useState<SessionBridgeData | null>(null);
  const [metadata, setMetadata] = useState<SessionBridgeMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch session bridge data on mount, when patientId changes, OR when sessionBridgeRefreshTrigger increments
  useEffect(() => {
    if (!patientId) return;

    async function fetchSessionBridge(): Promise<void> {
      if (!patientId) return; // Guard for TypeScript

      // Determine if this is a refresh (we already have data) or initial load
      const hasExistingData = bridgeData !== null;

      if (hasExistingData) {
        setIsRefreshing(true); // Show overlay on existing card
      } else {
        setIsLoading(true); // Replace with placeholder card
      }

      const result = await apiClient.getSessionBridge(patientId);

      if (!result.success) {
        setError(result.error || 'Failed to load session bridge');
        setIsLoading(false);
        setIsRefreshing(false);
        return;
      }

      setBridgeData(result.data?.bridge ?? null);
      setMetadata(result.data?.metadata ?? null);
      setError(null);
      setIsLoading(false);

      // Keep refresh overlay visible briefly for visual feedback
      if (hasExistingData) {
        setTimeout(() => setIsRefreshing(false), 500);
      }
    }

    fetchSessionBridge();
  }, [patientId, sessionBridgeRefreshTrigger]); // Re-run when trigger increments

  // Render placeholder card for initial load or during generation
  const isInitialLoad = isLoading && !bridgeData;
  if (isInitialLoad || loadingSessionBridge) {
    const message = isInitialLoad ? 'Loading session bridge...' : 'Generating session bridge...';
    return <PlaceholderCard message={message} showOverlay />;
  }

  // Render placeholder card for error state
  if (error) {
    return <PlaceholderCard message={error} isError />;
  }

  // Render placeholder card for empty state (no data yet)
  if (!bridgeData || !metadata) {
    return (
      <PlaceholderCard
        message="Upload therapy sessions to generate your session preparation content"
        secondaryMessage="Your session bridge will appear here after your first session is analyzed"
      />
    );
  }

  // Render full card with data
  return (
    <>
      <div className={`${cardBaseClasses} cursor-pointer`} onClick={() => setIsModalOpen(true)}>
        {/* Loading overlay for refresh (shows on top of existing content) */}
        <LoadingOverlay visible={isRefreshing} />

        <div className="flex-shrink-0">
          <CardTitle />
          <p
            style={{ fontFamily: fontSans, fontSize: '12px' }}
            className="text-gray-500 dark:text-gray-500 mt-1"
          >
            {getSessionCounterText(metadata.sessions_analyzed, metadata.total_sessions)}
          </p>
        </div>

        <div className="flex-1 overflow-hidden mt-6">
          {/* Next Session Topics */}
          <div className="mb-5">
            <h3
              style={{ fontFamily: fontSans, fontSize: '14px', fontWeight: 600 }}
              className="text-gray-900 dark:text-white mb-2"
            >
              Next Session Topics
            </h3>
            <BulletList items={bridgeData.nextSessionTopics.slice(0, 2)} />
          </div>

          {/* Share Progress */}
          <div className="mb-5">
            <h3
              style={{ fontFamily: fontSans, fontSize: '14px', fontWeight: 600 }}
              className="text-gray-900 dark:text-white mb-2"
            >
              Share Progress
            </h3>
            <BulletList items={bridgeData.shareProgress.slice(0, 2)} />
          </div>

          {/* Session Prep */}
          <div>
            <h3
              style={{ fontFamily: fontSans, fontSize: '14px', fontWeight: 600 }}
              className="text-gray-900 dark:text-white mb-2"
            >
              Session Prep
            </h3>
            <BulletList items={bridgeData.sessionPrep.slice(0, 2)} />
          </div>
        </div>

        <div
          style={{ fontFamily: fontSans, fontSize: '12px' }}
          className="text-gray-500 dark:text-gray-500 text-right mt-4"
        >
          Click to view all
        </div>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#ECEAE5] dark:bg-[#1A1625] p-8 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <CardTitle />
              <p
                style={{ fontFamily: fontSans, fontSize: '12px' }}
                className="text-gray-500 dark:text-gray-500 mb-6"
              >
                {getSessionCounterText(metadata.sessions_analyzed, metadata.total_sessions)}
              </p>

              {/* Next Session Topics (all 3) */}
              <div className="mb-6">
                <h3
                  style={{ fontFamily: fontSans, fontSize: '16px', fontWeight: 600 }}
                  className="text-gray-900 dark:text-white mb-3"
                >
                  Next Session Topics
                </h3>
                <BulletList items={bridgeData.nextSessionTopics} bulletSize="medium" />
              </div>

              {/* Share Progress (all 4) */}
              <div className="mb-6">
                <h3
                  style={{ fontFamily: fontSans, fontSize: '16px', fontWeight: 600 }}
                  className="text-gray-900 dark:text-white mb-3"
                >
                  Share Progress
                </h3>
                <BulletList items={bridgeData.shareProgress} bulletSize="medium" />
              </div>

              {/* Session Prep (all 4) */}
              <div className="mb-6">
                <h3
                  style={{ fontFamily: fontSans, fontSize: '16px', fontWeight: 600 }}
                  className="text-gray-900 dark:text-white mb-3"
                >
                  Session Prep
                </h3>
                <BulletList items={bridgeData.sessionPrep} bulletSize="medium" />
              </div>

              <button
                onClick={() => setIsModalOpen(false)}
                style={{ fontFamily: fontSans, fontSize: '14px' }}
                className="mt-4 px-6 py-2 bg-[#5AB9B4] dark:bg-[#a78bfa] text-white rounded-lg hover:opacity-90 transition"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
```

**Update Dashboard Import:**

**File:** `frontend/app/patient/page.tsx`

Update import (around line 10):

```typescript
import { SessionBridgeCard } from './components/SessionBridgeCard';  // Renamed from TherapistBridgeCard
```

**Success Criteria:**
- [ ] Card fetches data from API on mount
- [ ] Loading overlay shows during initial load
- [ ] Loading overlay shows during refresh (with 500ms delay)
- [ ] Empty state shown when no data exists
- [ ] Error state shown on API failure
- [ ] Compact card shows 2 items per section
- [ ] Modal shows all items (3 topics, 4 progress, 4 prep)
- [ ] Session counter displays correctly
- [ ] No console errors

---

## Phase 7: SSE Integration

### File: `frontend/app/patient/components/WaveCompletionBridge.tsx`

Update `onWave2SessionComplete` handler (around line 165):

```typescript
onWave2SessionComplete: async (sessionId, sessionDate) => {
  console.log(`[Wave2] ✅ Wave 2 complete for ${sessionDate}`);

  // Refresh session data first
  await refresh();

  // Trigger roadmap refresh (roadmap is generated after each Wave 2 completion)
  console.log(`[Roadmap] 🔄 Triggering roadmap refresh after Wave 2 for ${sessionDate}`);
  setRoadmapRefreshTrigger(prev => prev + 1);

  // Trigger session bridge refresh (session bridge is generated after each Wave 2 completion)
  console.log(`[SessionBridge] 🔄 Triggering session bridge refresh after Wave 2 for ${sessionDate}`);
  setSessionBridgeRefreshTrigger(prev => prev + 1);

  // Clean up loading overlay
  setTimeout(() => {
    setLoadingOverlays((prev) => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });
  }, 1000);
},
```

**Success Criteria:**
- [ ] Session bridge refresh triggered after Wave 2 events
- [ ] Card updates with new data automatically
- [ ] No duplicate API calls
- [ ] Console logs visible for debugging

---

## Testing Checklist

### Backend Tests

**Service Tests:**
- [ ] SessionBridgeGenerator initializes correctly
- [ ] generate_bridge() returns correct structure (3 topics, 4 progress, 4 prep)
- [ ] Validation pads missing items with placeholders
- [ ] Validation truncates extra items to expected counts
- [ ] Cost tracking writes to generation_costs table
- [ ] Model uses gpt-5-mini from config

**Orchestration Tests:**
- [ ] Script runs standalone: `python scripts/generate_session_bridge.py <patient_id> <session_id>`
- [ ] Context building creates correct tier structure (dict format)
- [ ] Tier 1 includes full Wave 1 + Wave 2 data (last 3 sessions)
- [ ] Tier 2 includes 300-char prose (sessions 4-7)
- [ ] Tier 3 includes first sentence arc (sessions 8+)
- [ ] Previous roadmap included for context
- [ ] Version numbering increments correctly
- [ ] Database writes succeed (both tables updated)
- [ ] Script logs appear in Railway console

**Integration Tests:**
- [ ] Wave 2 completion triggers session bridge generation
- [ ] subprocess.Popen() detaches correctly (non-blocking)
- [ ] Bridge generates after Session 1 (uses S1 data to suggest S2 prep)
- [ ] Bridge updates after each subsequent session

### Frontend Tests

**Component Tests:**
- [ ] Card renders empty state when no data
- [ ] Card renders error state on API failure
- [ ] Card renders loading state during initial fetch
- [ ] Card renders loading overlay during refresh
- [ ] Compact card shows 2 items per section
- [ ] Modal shows all items (3 topics, 4 progress, 4 prep)
- [ ] Session counter displays correctly
- [ ] Click to open modal works
- [ ] Close modal button works

**Integration Tests:**
- [ ] SSE triggers refresh after Wave 2 completion
- [ ] Card updates with new data automatically
- [ ] Refresh overlay shows briefly (500ms)
- [ ] No duplicate API calls during refresh
- [ ] Context provides correct trigger values
- [ ] Multiple refreshes work correctly

### End-to-End Tests

**Production Flow:**
1. [ ] Upload Session 1 → Wait for Wave 2 complete
2. [ ] Session bridge generates automatically
3. [ ] Card updates with first bridge data
4. [ ] Bridge shows 3 topics, 4 progress (empty or AI-generated), 4 prep
5. [ ] Upload Session 2 → Wait for Wave 2 complete
6. [ ] Session bridge regenerates with updated context
7. [ ] Card refreshes with new data (loading overlay shows)
8. [ ] Bridge now references Session 1 + Session 2 insights
9. [ ] Upload Session 10 → Verify all 3 tiers working
10. [ ] Verify cost tracking in generation_costs table

---

## Cost Analysis

### Per-Generation Cost (gpt-5-mini)

**Token Breakdown:**
- **Input Tokens:** ~5,500
  - Tier 1 (3 sessions × 750 tokens): 2,250 tokens
  - Tier 2 (4 sessions × 150 tokens): 600 tokens
  - Tier 3 (N sessions × 50 tokens): variable
  - Previous Roadmap: ~800 tokens
  - System/User Prompts: ~500 tokens
- **Output Tokens:** ~200 (11 strings)

**Cost Calculation:**
- Input: 5,500 × $0.10 / 1M = $0.00055
- Output: 200 × $0.30 / 1M = $0.00006
- **Total:** ~$0.00061 per generation

**10-Session Demo:** ~$0.0061 total (well under $0.014 target)

### Compared to PR #3 (Your Journey)

| Feature | Model | Strategy | Input Tokens | Cost per Gen | Cost per 10 Sessions |
|---------|-------|----------|--------------|--------------|----------------------|
| **Your Journey** | gpt-5.2 | Hierarchical | ~12K | ~$0.033 | ~$0.33 |
| **Session Bridge** | gpt-5-mini | Gradient Hierarchical | ~5.5K | ~$0.00061 | ~$0.0061 |

**Session Bridge is 54x cheaper** due to:
- Smaller model (gpt-5-mini vs gpt-5.2)
- Simpler output (11 strings vs full JSON with 5 sections)
- Efficient compaction (gradient hierarchical)

---

## Rollback Plan

If issues arise, rollback can be done table-by-table:

1. **Database rollback:**
   ```sql
   DROP TABLE IF EXISTS session_bridge_versions;
   DROP TABLE IF EXISTS patient_session_bridge;
   ```

2. **Remove backend files:**
   - `backend/app/services/session_bridge_generator.py`
   - `backend/scripts/generate_session_bridge.py`

3. **Remove API endpoint:**
   - Delete `/api/patients/{patient_id}/session-bridge` from `main.py`
   - Remove `session_bridge_updated_at` from `demo.py`

4. **Frontend rollback:**
   - Revert `SessionBridgeCard.tsx` to mock data version
   - Remove API client method
   - Remove context trigger fields

5. **Git revert:**
   ```bash
   git log --oneline  # Find commit hash
   git revert <commit-hash>
   ```

---

## Success Metrics

**Functional:**
- [ ] Session bridge generates after each Wave 2 completion
- [ ] All 3 compaction tiers working correctly
- [ ] Frontend displays data with correct formatting
- [ ] SSE triggers automatic refresh
- [ ] Version history preserved in database

**Performance:**
- [ ] Generation completes in <5 seconds
- [ ] Database writes complete without errors
- [ ] Frontend refresh completes in <1 second
- [ ] No memory leaks or stuck processes

**Cost:**
- [ ] Cost per generation ≤ $0.00061
- [ ] 10-session demo cost ≤ $0.0061
- [ ] Cost tracking accurate in database

**User Experience:**
- [ ] Empty state guides user to upload sessions
- [ ] Loading states provide clear feedback
- [ ] Error states display helpful messages
- [ ] Modal provides full detail on click
- [ ] Content follows QUALITATIVE inter-session guidelines

---

## Files Modified/Created

### Backend Files

**Created:**
- `backend/app/services/session_bridge_generator.py` (500+ lines)
- `backend/scripts/generate_session_bridge.py` (350+ lines)
- `backend/supabase/migrations/0XX_create_session_bridge_tables.sql`

**Modified:**
- `backend/app/config/model_config.py` (add task assignments)
- `backend/app/main.py` (add API endpoint)
- `backend/app/routers/demo.py` (add timestamp to status)
- `backend/scripts/seed_wave2_analysis.py` (trigger generation)

### Frontend Files

**Created:**
- None (renamed existing file)

**Renamed:**
- `frontend/app/patient/components/TherapistBridgeCard.tsx` → `SessionBridgeCard.tsx`

**Modified:**
- `frontend/lib/api-client.ts` (add getSessionBridge method)
- `frontend/lib/types.ts` (add SessionBridge interfaces)
- `frontend/app/patient/contexts/SessionDataContext.tsx` (add trigger state)
- `frontend/app/patient/lib/usePatientSessions.ts` (add trigger return value)
- `frontend/app/patient/components/WaveCompletionBridge.tsx` (trigger refresh)
- `frontend/app/patient/page.tsx` (update import)

---

## Implementation Order

**Recommended execution sequence:**

1. **Phase 0:** Database schema (create tables via Supabase MCP)
2. **Phase 1:** Backend service (SessionBridgeGenerator)
3. **Phase 2:** Orchestration script (generate_session_bridge.py)
4. **Manual Test:** Run script standalone to verify end-to-end generation
5. **Phase 3:** API endpoint (add to main.py + demo.py)
6. **Phase 4:** Frontend API client (add method + types)
7. **Phase 5:** Frontend context (add trigger state)
8. **Phase 6:** Frontend component (convert to real API)
9. **Phase 7:** SSE integration (trigger refresh)
10. **End-to-End Test:** Upload session → verify automatic generation + refresh

---

## Next Steps After Completion

Once Session Bridge backend is deployed and verified:

1. **Archive PR #4 documentation** (similar to PR #1, PR #2, PR #3)
2. **Update .claude/SESSION_LOG.md** with implementation details
3. **Update Project MDs/TheraBridge.md** with feature status
4. **Plan PR #5:** To-Do Card backend integration
   - Use continuation prompt at `thoughts/shared/plans/2026-01-14-session-bridge-continuation.md`
   - Follow same phase pattern (database → service → orchestration → API → frontend)
   - Implement bidirectional sync with Session Bridge (shareProgress uses completed tasks)
