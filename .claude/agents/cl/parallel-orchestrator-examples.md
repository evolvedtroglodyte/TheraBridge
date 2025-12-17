# Parallel Orchestrator - Practical Examples

This document provides real-world examples demonstrating the intelligent scaling and wave orchestration capabilities of the parallel-orchestrator agent.

---

## Example 1: Automatic Scaling for Repository Cleanup

**User Prompt:**
```
@parallel-orchestrator Clean up all unused imports and dead code across the repository
```

**Expected Behavior:**
- Agent analyzes codebase size (~150 files across frontend, backend, pipeline)
- Determines optimal agent count: **12 agents** (auto-scaled based on file count)
- Groups files by directory for efficient parallel processing

**Wave Structure:**

```
Wave 1 (Discovery & Analysis) - 12 agents in parallel
├── Agent 1: Scan frontend/components/*.tsx for unused imports
├── Agent 2: Scan frontend/app/**/*.tsx for unused imports
├── Agent 3: Scan frontend/lib/*.ts for dead code
├── Agent 4: Scan frontend/hooks/*.ts for dead code
├── Agent 5: Scan backend/app/routers/*.py for unused imports
├── Agent 6: Scan backend/app/models/*.py for unused imports
├── Agent 7: Scan backend/app/services/*.py for dead code
├── Agent 8: Scan backend/tests/*.py for dead code
├── Agent 9: Scan pipeline/src/*.py for unused imports
├── Agent 10: Scan pipeline/tests/*.py for unused imports
├── Agent 11: Analyze import dependency graph
└── Agent 12: Identify unreferenced utility functions

Wave 2 (Cleanup Execution) - 8 agents in parallel
├── Agent 1: Remove unused imports from frontend (30 files)
├── Agent 2: Remove unused imports from backend (22 files)
├── Agent 3: Remove unused imports from pipeline (15 files)
├── Agent 4: Delete dead utility functions (frontend/lib)
├── Agent 5: Delete dead utility functions (backend/app/utils)
├── Agent 6: Update test files with import changes
├── Agent 7: Run ESLint fix on modified files
└── Agent 8: Verify build passes after cleanup

Wave 3 (Verification) - 3 agents in parallel
├── Agent 1: Run frontend build and verify
├── Agent 2: Run backend tests and verify
└── Agent 3: Generate cleanup report
```

**Why This Scaling:**
- 150 files across 3 projects → 12 agents provides good parallelization without overhead
- Wave 2 reduces to 8 agents (cleanup is faster than discovery)
- Wave 3 reduces to 3 agents (one per project for verification)

---

## Example 2: Explicit 50 Agents for Large-Scale Refactor

**User Prompt:**
```
@parallel-orchestrator with 50 agents Migrate entire codebase from JavaScript to TypeScript with strict mode enabled
```

**Expected Behavior:**
- User explicitly requests 50 agents
- Orchestrator uses all 50 agents in Wave 1 for maximum parallelization
- Subsequent waves scale down based on dependency bottlenecks

**Wave Structure:**

```
Wave 1 (File Conversion) - 50 agents in parallel
├── Agents 1-25: Convert 250 frontend files (.js → .ts, .jsx → .tsx)
│   ├── Agent 1: components/auth/*.jsx (10 files)
│   ├── Agent 2: components/dashboard/*.jsx (12 files)
│   ├── Agent 3: components/session/*.jsx (8 files)
│   └── ... (22 more agents for remaining components)
└── Agents 26-50: Convert 200 backend files (.js → .ts)
    ├── Agent 26: routers/*.js (15 files)
    ├── Agent 27: services/*.js (18 files)
    └── ... (24 more agents for remaining backend)

Wave 2 (Type Definition) - 30 agents in parallel
├── Agents 1-15: Add TypeScript types to frontend files
├── Agents 16-30: Add TypeScript types to backend files
└── (Reduced from 50 → 30 because type inference can batch smaller files)

Wave 3 (Strict Mode Migration) - 20 agents in parallel
├── Agents 1-10: Enable strict mode and fix frontend errors
├── Agents 11-20: Enable strict mode and fix backend errors
└── (Further reduced because strict mode fixes depend on types being complete)

Wave 4 (Configuration & Testing) - 5 agents in parallel
├── Agent 1: Update tsconfig.json for all projects
├── Agent 2: Update build configs (webpack, vite, etc.)
├── Agent 3: Run frontend type checks and fix errors
├── Agent 4: Run backend type checks and fix errors
└── Agent 5: Update CI/CD pipeline for TypeScript

Wave 5 (Verification) - 3 agents in parallel
├── Agent 1: Run all frontend tests
├── Agent 2: Run all backend tests
└── Agent 3: Generate migration report
```

**Why This Scaling:**
- 50 agents fully utilized in Wave 1 (450+ files = parallelization heaven)
- Wave 2-3 scale down as tasks become more interdependent
- Wave 4-5 bottleneck on build/test operations (can't parallelize beyond project count)

---

## Example 3: Automatic Scaling for Single Bug Fix (Intelligent Reduction)

**User Prompt:**
```
@parallel-orchestrator Fix the authentication token expiry bug that's causing logout issues
```

**Expected Behavior:**
- Agent analyzes task complexity (single bug fix, limited scope)
- Determines optimal agent count: **3 agents** (intelligently scaled DOWN)
- Recognizes this is NOT a parallelization-friendly task

**Wave Structure:**

```
Wave 1 (Investigation) - 3 agents in parallel
├── Agent 1: Analyze auth token implementation (backend/app/services/auth.py)
├── Agent 2: Analyze token validation logic (frontend/lib/auth.ts)
└── Agent 3: Review related test files for expected behavior

Wave 2 (Root Cause Analysis) - 1 agent
└── Agent 1: Synthesize findings and identify root cause
    (Sequential because it requires all Wave 1 results)

Wave 3 (Fix Implementation) - 2 agents in parallel
├── Agent 1: Fix backend token expiry logic
└── Agent 2: Fix frontend token refresh logic

Wave 4 (Testing) - 2 agents in parallel
├── Agent 1: Add backend test for token expiry edge cases
└── Agent 2: Add frontend test for token refresh flow

Wave 5 (Verification) - 1 agent
└── Agent 1: Run integration tests and verify fix
```

**Why This Scaling:**
- Bug fixes are inherently sequential (investigate → diagnose → fix → test)
- 3 agents in Wave 1 is optimal (backend code, frontend code, tests)
- Most waves reduce to 1-2 agents because of dependency chains
- Total: 9 agent invocations across 5 waves (NOT 50+ agents)

**Key Insight:**
The orchestrator is smart enough to recognize when MORE agents would slow things down. A 50-agent swarm for a single bug fix would create coordination overhead with no benefit.

---

## Example 4: Explicit 100 Agents for Test Coverage Analysis

**User Prompt:**
```
@parallel-orchestrator with 100 agents Analyze test coverage across the entire codebase and identify untested code paths
```

**Expected Behavior:**
- User explicitly requests 100 agents
- Orchestrator uses all 100 agents for embarrassingly parallel coverage analysis
- Waves maintain high parallelization throughout (analysis is independent)

**Wave Structure:**

```
Wave 1 (Coverage Data Collection) - 100 agents in parallel
├── Agents 1-50: Analyze 500 frontend files
│   ├── Agent 1: components/auth/*.tsx (10 files) → identify functions, branches, paths
│   ├── Agent 2: components/dashboard/*.tsx (12 files) → identify functions, branches, paths
│   └── ... (48 more agents)
└── Agents 51-100: Analyze 400 backend files
    ├── Agent 51: routers/*.py (20 files) → identify functions, branches, paths
    └── ... (49 more agents)

Wave 2 (Test-to-Code Mapping) - 100 agents in parallel
├── Agents 1-50: Map frontend tests to source code
│   ├── Agent 1: Match tests/__tests__/auth.test.tsx to components/auth/*.tsx
│   └── ... (49 more agents)
└── Agents 51-100: Map backend tests to source code
    ├── Agent 51: Match tests/test_routers.py to routers/*.py
    └── ... (49 more agents)

Wave 3 (Coverage Gap Analysis) - 100 agents in parallel
├── Each agent analyzes 9 files (900 files / 100 agents)
├── Identifies:
│   ├── Untested functions
│   ├── Untested branches (if/else, try/catch)
│   ├── Untested error paths
│   └── Dead code
└── Generates per-file coverage reports

Wave 4 (Priority Calculation) - 50 agents in parallel
├── Agents 1-25: Calculate risk scores for frontend untested code
├── Agents 26-50: Calculate risk scores for backend untested code
└── (Reduced from 100 → 50 because risk calculation can batch multiple files)

Wave 5 (Report Generation) - 10 agents in parallel
├── Agent 1: Generate frontend coverage summary
├── Agent 2: Generate backend coverage summary
├── Agent 3: Generate pipeline coverage summary
├── Agent 4: Create prioritized test recommendations (critical paths)
├── Agent 5: Create test gap heatmap visualization
├── Agent 6: Generate CI/CD integration recommendations
├── Agent 7: Identify quick wins (easy-to-test functions)
├── Agent 8: Identify complex untested areas (needs design)
├── Agent 9: Compare coverage against industry benchmarks
└── Agent 10: Generate executive summary report
```

**Why This Scaling:**
- 900 files → 100 agents = 9 files per agent (perfect parallelization)
- Coverage analysis is embarrassingly parallel (no cross-file dependencies)
- All 5 waves maintain high agent counts (80+ agents each)
- Total: ~460 agent invocations (highly efficient use of parallelization)

---

## Example 5: Automatic Scaling for Multi-Server Deployment

**User Prompt:**
```
@parallel-orchestrator Deploy the latest backend changes to all production servers and verify health
```

**Expected Behavior:**
- Agent queries infrastructure to discover server count
- Detects 15 production servers across 3 regions
- Determines optimal agent count: **15 agents** (one per server)

**Wave Structure:**

```
Wave 1 (Pre-Deployment Checks) - 3 agents in parallel
├── Agent 1: Run full test suite
├── Agent 2: Build production artifacts
└── Agent 3: Verify database migration scripts

Wave 2 (Deployment) - 15 agents in parallel
├── Agents 1-5: Deploy to US-East region (5 servers)
│   ├── Agent 1: server-us-east-1.prod → pull image, stop old, start new
│   ├── Agent 2: server-us-east-2.prod → pull image, stop old, start new
│   └── ...
├── Agents 6-10: Deploy to US-West region (5 servers)
└── Agents 11-15: Deploy to EU-West region (5 servers)

Wave 3 (Health Verification) - 15 agents in parallel
├── Each agent monitors its deployed server:
│   ├── Check HTTP 200 on /health endpoint
│   ├── Verify database connectivity
│   ├── Check Redis connection
│   ├── Validate API response times < 200ms
│   └── Monitor error logs for 2 minutes

Wave 4 (Load Balancer Integration) - 3 agents in parallel
├── Agent 1: Re-enable US-East servers in load balancer
├── Agent 2: Re-enable US-West servers in load balancer
└── Agent 3: Re-enable EU-West servers in load balancer

Wave 5 (Post-Deployment Validation) - 5 agents in parallel
├── Agent 1: Run smoke tests against production
├── Agent 2: Verify metrics dashboard shows green
├── Agent 3: Check distributed tracing for errors
├── Agent 4: Monitor user-facing error rates
└── Agent 5: Generate deployment report and notify team
```

**Why This Scaling:**
- 15 servers → 15 agents (1:1 mapping for deployment)
- Wave 1 uses 3 agents (pre-flight checks are independent)
- Wave 2-3 maintain 15 agents (per-server operations)
- Wave 4 reduces to 3 agents (per-region load balancer operations)
- Wave 5 uses 5 agents (validation tasks are independent)

**Key Insight:**
The orchestrator automatically scales to match infrastructure. If the user later adds 35 more servers (50 total), running the same prompt would auto-scale to 50 agents in Wave 2-3.

---

## Pattern Summary

| Example | Task Type | Agent Count | Scaling Reason |
|---------|-----------|-------------|----------------|
| 1. Repo Cleanup | Auto | 12 agents | Matches file distribution across 3 projects |
| 2. TS Migration | Explicit | 50 agents | User requested, maximizes parallelization for 450+ files |
| 3. Bug Fix | Auto | 3 agents | Intelligently reduces for sequential debugging task |
| 4. Coverage Analysis | Explicit | 100 agents | User requested, perfect for embarrassingly parallel analysis |
| 5. Deployment | Auto | 15 agents | Dynamically matches infrastructure (15 servers) |

**Golden Rules:**
1. **Automatic mode** analyzes task complexity and scales appropriately
2. **Explicit mode** honors user request but optimizes wave structure
3. **Sequential tasks** (debugging, root cause analysis) use fewer agents
4. **Parallel tasks** (file processing, server operations) use many agents
5. **Later waves** often reduce agent count due to dependency bottlenecks
