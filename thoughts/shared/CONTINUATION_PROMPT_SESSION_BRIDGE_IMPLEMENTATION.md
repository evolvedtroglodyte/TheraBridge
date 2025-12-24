# Session Bridge Backend Integration - Implementation Continuation Prompt

**Copy this entire prompt into your new Claude Code session to begin implementation.**

---

## Context: Session Bridge Backend Integration + MODEL_TIER + BaseAIGenerator

You are continuing implementation of three major architectural improvements to the TheraBridge backend that were comprehensively planned in a previous 3-hour session (2026-01-18).

**Planning Status:** ✅ COMPLETE
- 120 clarifying questions answered (Q1-Q120)
- 14 research agents deployed (4 rounds of parallel research)
- Database verified: 10 patient_roadmap + 56 roadmap_versions rows (production data)
- Implementation sequence approved: 19-step execution plan
- Planning document: 2100+ lines with full architecture

**Your task:** Execute the 19-step implementation plan, following the architecture decisions documented in the planning doc.

---

## Critical Files to Reference

1. **Planning Document (MUST READ FIRST):**
   - Path: `thoughts/shared/plans/2026-01-14-session-bridge-backend-integration.md`
   - Size: 2100+ lines
   - Contains: All 120 Q&A answers, architecture specs, implementation sequence, code examples

2. **Research Document:**
   - Path: `thoughts/shared/research/2026-01-18-session-bridge-architecture-research.md`
   - Size: 600+ lines
   - Contains: Base class patterns, metadata architecture, dual logging, MODEL_TIER research

3. **Session Log:**
   - Path: `.claude/SESSION_LOG.md`
   - Contains: Complete chronological history of planning session (2026-01-18 entry)

4. **Repository Documentation:**
   - Path: `.claude/CLAUDE.md`
   - Contains: Git rules, project structure, current status

---

## Implementation Priority: Follow This Exact Order

The user approved this 19-step sequence. **DO NOT deviate without asking:**

### Phase 1: Migrations (Steps 1-3)
1. ✅ Create migration 014 SQL file (Your Journey rename - ALTER TABLE preserves 66 rows)
2. ✅ Create migration 015 SQL file (Session Bridge tables + generation_metadata + polymorphic FKs)
3. ✅ Create migration 016 SQL file (analysis_processing_log Wave 3 enum extensions)

### Phase 2: Apply Migrations (Steps 4-6)
4. Apply migration 014 via Supabase MCP
5. Verify production data preserved (10 patient_roadmap + 56 roadmap_versions rows)
6. Apply migrations 015 and 016 via Supabase MCP

### Phase 3: MODEL_TIER Foundation (Steps 7-9) - **IMPLEMENT THIS FIRST**
7. Create `backend/app/services/model_config.py` with tier system (precision/balanced/rapid)
8. Create `backend/app/models/model_tier.py` Pydantic enum (ModelTier)
9. Create test file `backend/tests/test_model_tier.py` and verify all 9 services can load tiers

### Phase 4: BaseAIGenerator Refactor (Steps 10-13) - **PILOT WITH 2 SERVICES**
10. Create `backend/app/services/base_ai_generator.py` (ABC with Generic[ClientType])
11. **PILOT:** Refactor `mood_analyzer.py` to inherit from BaseAIGenerator (async client)
12. **PILOT:** Refactor `deep_analyzer.py` to inherit from BaseAIGenerator (sync client)
13. Test both services, verify cost tracking still works, verify no regressions

### Phase 5: Complete Refactor (Steps 14-15) - **AFTER PILOT SUCCESS**
14. Refactor remaining 7 services to inherit from BaseAIGenerator
15. Test all 9 services with MODEL_TIER overrides (precision/balanced/rapid)

### Phase 6: Wave3Logger (Steps 16-17)
16. Create `backend/app/services/wave3_logger.py` (dual logging: PipelineLogger + DB)
17. Integrate Wave3Logger into roadmap_generator.py (replace PipelineLogger)

### Phase 7: Session Bridge Integration (Steps 18-19)
18. Create `backend/app/services/session_bridge_generator.py` (implements BaseAIGenerator)
19. Create orchestration script `backend/scripts/generate_session_bridge.py` (compaction + generation)

---

## Critical Architecture Decisions (From Q&A)

### Database Design
- **Polymorphic FK approach:** Two nullable FK columns with CHECK constraint (exactly one must be set)
- **Migration 014:** Use `ALTER TABLE RENAME` to preserve 66 rows of production data (10 + 56 rows verified via MCP)
- **generation_metadata table:** Shared metadata with editing utilities, polymorphic FK to versions tables
- **analysis_processing_log:** Extend Wave enum with YOUR_JOURNEY_GENERATION and SESSION_BRIDGE_GENERATION

### MODEL_TIER System
- **Tiers:** precision (gpt-5.2), balanced (gpt-5), rapid (gpt-5-mini)
- **Override method:** `get_model_name(task_name, override_model)` in model_config.py
- **Configuration:** Module-level cache with lazy loading for tier configs
- **Cost savings:** Balanced tier = 72% savings ($0.65 → $0.18), Rapid tier = 94% savings ($0.04)

### BaseAIGenerator Pattern
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

    @abstractmethod
    def generate(self, *args, **kwargs): pass

    def _call_api(self, user_prompt, **openai_params):
        # Concrete helper - accepts all OpenAI parameters
        pass
```

### Wave3Logger Pattern
```python
class Wave3Logger:
    EVENT_MAP = {
        "your_journey": LogEvent.YOUR_JOURNEY_GENERATION,
        "session_bridge": LogEvent.SESSION_BRIDGE_GENERATION,
    }

    def log_generation_start(self, session_id, wave_name, ...):
        # 1. Log to PipelineLogger (SSE)
        # 2. Log to analysis_processing_log (database)
```

### Services to Refactor (9 total)
**Async clients (5):**
- mood_analyzer.py (gpt-5-nano)
- topic_extractor.py (gpt-5-mini)
- breakthrough_detector.py (gpt-5)
- action_items_summarizer.py (gpt-5-nano)

**Sync clients (4):**
- deep_analyzer.py (gpt-5.2)
- prose_generator.py (gpt-5.2)
- speaker_labeler.py (gpt-5-mini)
- session_insights_summarizer.py (gpt-5.2)
- roadmap_generator.py (gpt-5.2)

---

## Testing Strategy (User-Approved)

1. **Test after each phase** (Q107: Option A approved - safer approach)
2. **Pilot BaseAIGenerator with 2 services** (Q114: Option A approved - mood_analyzer + deep_analyzer)
3. **Verify cost tracking still works** after BaseAIGenerator refactor
4. **Test MODEL_TIER overrides** with all 3 tiers (precision/balanced/rapid)
5. **Verify production data preserved** after migration 014 (10 + 56 rows)

---

## Documentation Requirements

1. **Update SESSION_LOG.md after each major phase** (Q119: Option A approved)
   - Add entry after Phase 1 complete (migrations created)
   - Add entry after Phase 2 complete (migrations applied)
   - Add entry after Phase 3 complete (MODEL_TIER working)
   - Add entry after Phase 4 complete (BaseAIGenerator pilot successful)
   - Add entry after Phase 5 complete (all services refactored)
   - Add entry after Phase 6 complete (Wave3Logger integrated)
   - Add entry after Phase 7 complete (Session Bridge live)

2. **Update planning doc with implementation learnings** (user instruction):
   - Document any deviations from plan
   - Document solutions to unexpected issues
   - Update code examples if approach changes

3. **Git commits after each phase** (Q118: Option A approved):
   - Commit after Phase 1: "feat: Create migrations 014, 015, 016"
   - Commit after Phase 2: "feat: Apply migrations for Session Bridge + Your Journey rename"
   - Commit after Phase 3: "feat: Implement MODEL_TIER system with 3-tier configs"
   - Commit after Phase 4: "refactor: Pilot BaseAIGenerator with mood_analyzer + deep_analyzer"
   - Commit after Phase 5: "refactor: Migrate all 9 services to BaseAIGenerator"
   - Commit after Phase 6: "feat: Implement Wave3Logger for dual logging"
   - Commit after Phase 7: "feat: Implement Session Bridge generation with compaction"

---

## Critical Rules from User

1. **ALWAYS provide intelligent suggestions** with every question/decision
   - User feedback: "the fact that you are intelligently giving suggestions is amazing. make sure you do that all the time"
   - Format: Option A (recommended): [rationale], Option B: [rationale]

2. **Update planning docs with what you learn** during implementation
   - If you hit problems, document solutions in planning doc
   - If you need different approach, update architecture section

3. **Test thoroughly before proceeding**
   - Pilot BaseAIGenerator before refactoring all services
   - Verify cost tracking after refactors
   - Test MODEL_TIER overrides with all 3 tiers

4. **Commit BEFORE major refactors** (Q61: explicit instruction)
   - Git commit and push BEFORE starting BaseAIGenerator refactor
   - Creates safety net for rollback if needed

5. **Follow git commit dating rules** (from CLAUDE.md)
   - All commits backdated to December 23, 2025
   - Check last commit timestamp: `git log --format="%ci" -n 1`
   - Add 30 seconds to timestamp for new commit

---

## Expected Outcomes

**After Phase 1-2 (Migrations):**
- 3 migration files created (014, 015, 016)
- Migration 014 applied (Your Journey renamed, 66 rows preserved)
- Migrations 015-016 applied (Session Bridge tables + enums added)

**After Phase 3 (MODEL_TIER):**
- model_config.py with tier system working
- All 9 services can load tier configs
- Test file verifying precision/balanced/rapid tiers

**After Phase 4-5 (BaseAIGenerator):**
- 225 lines of duplicate code eliminated across 9 services
- All services inherit from BaseAIGenerator
- Cost tracking still works
- Both async and sync clients supported

**After Phase 6 (Wave3Logger):**
- Dual logging to PipelineLogger (SSE) + analysis_processing_log (database)
- roadmap_generator.py using Wave3Logger

**After Phase 7 (Session Bridge):**
- session_bridge_generator.py service complete
- generate_session_bridge.py orchestration script with compaction
- Ready for frontend integration

---

## Migration 014 Critical Details (MUST FOLLOW)

**Database has production data:**
- 10 rows in patient_roadmap
- 56 rows in roadmap_versions
- **TOTAL: 66 rows to preserve**

**Migration 014 SQL (VERIFIED SAFE):**
```sql
-- Rename tables (data preserved automatically by PostgreSQL)
ALTER TABLE patient_roadmap RENAME TO patient_your_journey;
ALTER TABLE roadmap_versions RENAME TO your_journey_versions;

-- Update foreign key constraint names for clarity
ALTER TABLE patient_your_journey
RENAME CONSTRAINT patient_roadmap_patient_id_fkey
TO patient_your_journey_patient_id_fkey;

ALTER TABLE your_journey_versions
RENAME CONSTRAINT roadmap_versions_patient_id_fkey
TO your_journey_versions_patient_id_fkey;

ALTER TABLE your_journey_versions
RENAME CONSTRAINT roadmap_versions_roadmap_id_fkey
TO your_journey_versions_roadmap_id_fkey;
```

**Verification after applying migration 014:**
```sql
SELECT COUNT(*) FROM patient_your_journey;  -- Should return 10
SELECT COUNT(*) FROM your_journey_versions;  -- Should return 56
```

**DO NOT create manual data migration - ALTER TABLE RENAME preserves all data automatically.**

---

## Migration 015 Schema (Session Bridge Tables)

```sql
-- Session Bridge main table (1 per patient)
CREATE TABLE patient_session_bridge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL UNIQUE REFERENCES patients(id) ON DELETE CASCADE,
    current_version_id UUID REFERENCES session_bridge_versions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Session Bridge versions table (append-only history)
CREATE TABLE session_bridge_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    session_bridge_id UUID NOT NULL REFERENCES patient_session_bridge(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    bridge_data JSONB NOT NULL,
    model_used VARCHAR(50),
    generation_metadata_id UUID REFERENCES generation_metadata(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(patient_id, version_number)
);

-- Generation metadata table (polymorphic FK to version tables)
CREATE TABLE generation_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    your_journey_version_id UUID REFERENCES your_journey_versions(id) ON DELETE CASCADE,
    session_bridge_version_id UUID REFERENCES session_bridge_versions(id) ON DELETE CASCADE,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    api_cost DECIMAL(10, 6),
    model_tier VARCHAR(20),
    generation_duration_ms INTEGER,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (your_journey_version_id IS NOT NULL AND session_bridge_version_id IS NULL) OR
        (your_journey_version_id IS NULL AND session_bridge_version_id IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_session_bridge_versions_patient ON session_bridge_versions(patient_id);
CREATE INDEX idx_session_bridge_versions_session_bridge ON session_bridge_versions(session_bridge_id);
CREATE INDEX idx_generation_metadata_your_journey ON generation_metadata(your_journey_version_id);
CREATE INDEX idx_generation_metadata_session_bridge ON generation_metadata(session_bridge_version_id);
```

---

## Migration 016 Schema (Wave Enum Extensions)

```sql
-- Extend LogEvent enum in analysis_processing_log
ALTER TYPE "LogEvent" ADD VALUE 'YOUR_JOURNEY_GENERATION';
ALTER TYPE "LogEvent" ADD VALUE 'SESSION_BRIDGE_GENERATION';
```

**Note:** PostgreSQL doesn't allow removing enum values, only adding. These values are safe to add.

---

## How to Begin

1. **Read the planning document FIRST:**
   ```
   Read thoughts/shared/plans/2026-01-14-session-bridge-backend-integration.md
   ```

2. **Review the research document:**
   ```
   Read thoughts/shared/research/2026-01-18-session-bridge-architecture-research.md
   ```

3. **Check current git status:**
   ```bash
   git status
   git log --format="%ci" -n 1  # Check last commit timestamp for dating
   ```

4. **Create TODO list:**
   ```
   Use TodoWrite to create checklist with 19 implementation steps
   ```

5. **Start with Phase 1:**
   - Create migration 014 SQL file (Your Journey rename)
   - Create migration 015 SQL file (Session Bridge tables)
   - Create migration 016 SQL file (Wave enum extensions)
   - Commit: "feat: Create migrations 014, 015, 016"

6. **Always update docs as you go:**
   - Planning doc: Document deviations or learnings
   - SESSION_LOG.md: Add entry after each phase
   - CLAUDE.md: Update current status

---

## Success Criteria

**Phase 1-2 Complete:**
- [ ] 3 migration files created and committed
- [ ] Migration 014 applied, 66 rows verified preserved
- [ ] Migrations 015-016 applied successfully

**Phase 3 Complete:**
- [ ] MODEL_TIER system working with all 3 tiers
- [ ] All 9 services can load tier configs
- [ ] Test file passing

**Phase 4-5 Complete:**
- [ ] BaseAIGenerator ABC created with Generic[ClientType]
- [ ] mood_analyzer + deep_analyzer pilot successful
- [ ] All 9 services refactored and tested
- [ ] Cost tracking verified working
- [ ] 225 lines of duplicate code eliminated

**Phase 6 Complete:**
- [ ] Wave3Logger class created
- [ ] roadmap_generator.py using Wave3Logger
- [ ] Dual logging verified (SSE + database)

**Phase 7 Complete:**
- [ ] session_bridge_generator.py service created
- [ ] generate_session_bridge.py orchestration script created
- [ ] Session Bridge generation working end-to-end

---

## Questions? Remember to Provide Intelligent Suggestions

If you encounter issues or need clarification:
1. Check planning doc Q&A sections first (120 questions answered)
2. Check research doc for technical patterns
3. If still unclear, ask with **intelligent suggestions**:
   - Option A (recommended): [detailed rationale]
   - Option B: [detailed rationale]
   - Clear recommendation with reasoning

User feedback: "the fact that you are intelligently giving suggestions is amazing. make sure you do that all the time"

---

## Ready to Begin

You now have full context to begin implementation. Start with Phase 1 (create migration files), test thoroughly, commit after each phase, and update documentation as you go.

**Good luck!** 🚀
