# Parallel Orchestrator Agent - Test Cases

Test suite for validating parallel task orchestration, agent allocation, dependency analysis, and wave execution planning.

---

## Test: Explicit Agent Count Override

**Input:**
```
Refactor the authentication system across 8 files. Use exactly 5 agents to parallelize this work.
```

**Expected Outputs:**
- Agent count: 5 (user-specified override)
- Wave count: 2-3 (depending on dependencies)
- Key validations:
  - User-specified count takes precedence over auto-calculation
  - Task distribution balances workload across 5 agents
  - No agent sits idle while work remains

**Success Criteria:**
- Orchestrator acknowledges "5 agents" explicitly
- Wave plan uses exactly 5 agents max in parallel
- All 8 files covered in execution plan

---

## Test: Auto-Scaling with Independent Tasks

**Input:**
```
Update all API endpoint documentation across these files:
- backend/app/routers/auth.py
- backend/app/routers/sessions.py
- backend/app/routers/patients.py
- backend/app/routers/therapists.py
- backend/app/routers/analytics.py
```

**Expected Outputs:**
- Agent count: 5 (auto-calculated, one per file)
- Wave count: 1 (all independent)
- Key validations:
  - No cross-file dependencies detected
  - All tasks execute in parallel wave
  - Agent count equals task count for independent work

**Success Criteria:**
- Dependency graph shows 0 edges
- Single wave contains all 5 tasks
- Execution time optimized for full parallelization

---

## Test: Sequential Dependency Chain

**Input:**
```
Implement new database migration system:
1. Create migration schema in database.py
2. Build migration runner in migrations/runner.py
3. Add CLI commands in scripts/migrate.py
4. Update main.py to auto-run migrations on startup
5. Add migration tests in tests/test_migrations.py
```

**Expected Outputs:**
- Agent count: 5 (auto-calculated)
- Wave count: 5 (strict sequential chain)
- Key validations:
  - Each task depends on previous completion
  - Wave N+1 cannot start until Wave N completes
  - Linear dependency graph detected

**Success Criteria:**
- Dependency graph shows linear chain (1→2→3→4→5)
- Each wave contains exactly 1 task
- Orchestrator warns about limited parallelization opportunity

---

## Test: Diamond Dependency Pattern

**Input:**
```
Refactor error handling system:
- Create base exception classes (exceptions/base.py)
- Implement API error handlers (routers/error_handlers.py) [depends on base]
- Implement service error handlers (services/error_handlers.py) [depends on base]
- Add global error middleware (middleware/errors.py) [depends on both handlers]
```

**Expected Outputs:**
- Agent count: 4 (auto-calculated)
- Wave count: 3
- Key validations:
  - Wave 1: base.py (1 agent)
  - Wave 2: Both handler files (2 agents in parallel)
  - Wave 3: middleware/errors.py (1 agent)
  - Diamond dependency correctly identified

**Success Criteria:**
- Dependency graph shows diamond shape (1→2, 1→3, 2→4, 3→4)
- Wave 2 parallelizes the two independent handlers
- No deadlocks or circular dependencies

---

## Test: Resource Constraint Validation

**Input:**
```
Migrate entire codebase to TypeScript using 20 agents.
Files to convert:
- 15 React components
- 10 utility files
- 5 API client files
```

**Expected Outputs:**
- Agent count: 20 (user-specified, but capped at system max)
- Wave count: 2-3
- Key validations:
  - System enforces max agent limit (e.g., 10)
  - Warning issued about reduced agent count
  - Task distribution adapts to actual available agents

**Success Criteria:**
- Orchestrator warns "Requested 20 agents, using maximum of 10"
- All 30 files still covered in execution plan
- Wave structure optimized for available resources

---

## Test: Mixed Dependencies with Partial Parallelization

**Input:**
```
Build new analytics dashboard:
1. Create analytics database models (models/analytics.py)
2. Build data aggregation service (services/analytics.py) [depends on #1]
3. Create chart components (components/charts/) [independent]
4. Build dashboard API endpoints (routers/analytics.py) [depends on #2]
5. Build frontend dashboard page (pages/analytics.tsx) [depends on #3 and #4]
```

**Expected Outputs:**
- Agent count: 5 (auto-calculated)
- Wave count: 4
- Key validations:
  - Wave 1: models/analytics.py
  - Wave 2: services/analytics.py AND components/charts/ (2 parallel)
  - Wave 3: routers/analytics.py
  - Wave 4: pages/analytics.tsx
  - Mixed sequential and parallel execution

**Success Criteria:**
- Tasks #2 and #3 execute in same wave (parallel)
- Task #5 waits for both #3 and #4 to complete
- Dependency graph correctly models join point at task #5

---

## Test: Single Large Task with No Parallelization

**Input:**
```
Refactor the main application entry point (app/main.py) to use dependency injection.
```

**Expected Outputs:**
- Agent count: 1 (auto-calculated)
- Wave count: 1
- Key validations:
  - Single atomic task identified
  - No decomposition possible
  - Orchestrator suggests sequential execution

**Success Criteria:**
- Orchestrator acknowledges single task limitation
- No artificial task splitting occurs
- Clear message: "This task cannot be parallelized"

---

## Test: Complex Multi-Wave Optimization

**Input:**
```
Implement comprehensive test suite with 3 agents:
- Unit tests for auth service
- Unit tests for session service
- Unit tests for patient service
- Integration tests for API endpoints [depends on all unit tests]
- E2E tests for user flows [depends on integration tests]
- Performance tests [independent]
- Security tests [independent]
```

**Expected Outputs:**
- Agent count: 3 (user-specified)
- Wave count: 4
- Key validations:
  - Wave 1: 3 unit test files (max parallelization with 3 agents)
  - Wave 2: integration tests (1 agent, waiting on wave 1)
  - Wave 3: E2E tests, performance tests, security tests (3 agents, 2 independent tasks batched with dependent task)
  - Optimal wave packing given agent constraint

**Success Criteria:**
- Unit tests properly parallelize across available 3 agents
- Performance and security tests scheduled optimally (not delayed unnecessarily)
- Wave 3 intelligently combines dependent and independent work
- No agent idles while parallelizable work exists

---

## Test: Circular Dependency Detection

**Input:**
```
Refactor module system:
- Update auth module to use new session utilities
- Update session module to use new auth utilities
- Update database module to use both
```

**Expected Outputs:**
- Agent count: N/A (error state)
- Wave count: N/A (error state)
- Key validations:
  - Circular dependency detected between auth and session
  - Orchestrator rejects invalid dependency graph
  - Clear error message with cycle path

**Success Criteria:**
- Execution blocked with error: "Circular dependency detected: auth → session → auth"
- Orchestrator suggests breaking the cycle
- No execution plan generated

---

## Additional Validation Tests

### Edge Case: Zero Tasks
**Input:** Empty task list
**Expected:** Error message, no agents allocated

### Edge Case: Negative Agent Count
**Input:** "Use -5 agents"
**Expected:** Error or default to auto-calculation

### Edge Case: Extremely Large Agent Request
**Input:** "Use 1000 agents for 10 tasks"
**Expected:** Cap at system maximum, warn user

---

## Performance Benchmarks

For each test case, measure:
- Dependency graph generation time
- Wave optimization time
- Total orchestration overhead
- Actual vs theoretical speedup

**Target:** Orchestration overhead < 5% of total execution time
