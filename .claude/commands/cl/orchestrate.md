---
description: Orchestrate complex tasks using intelligent parallel execution
---

# Parallel Task Orchestration

You are executing a parallel orchestration command. When invoked with `/cl:orchestrate [task]`, you MUST follow this protocol:

## 📚 Reference Documentation

**IMPORTANT: Read these files for complete methodology before executing:**

1. **`.claude/DYNAMIC_WAVE_ORCHESTRATION.md`** - Contains:
   - Intelligent auto-scaling algorithm (how to calculate optimal agent count)
   - Task type classification (file_operations, api_calls, deployment, etc.)
   - ROI analysis methodology
   - Extreme scaling scenarios and examples

2. **`.claude/agents/cl/parallel-orchestrator.md`** - Contains:
   - Complete execution protocol
   - Task decomposition methodology (how to break tasks into subtasks)
   - Dependency analysis (how to build DAG)
   - Wave generation rules (how to organize tasks into waves)
   - Tool usage guidelines

**Use these files to inform your decisions when calculating agent counts and structuring waves.**

---

## STEP 1: Wave 0 - Deep Analysis Using Parallel Research Agents (REQUIRED)

**🚨 CRITICAL: Launch parallel research agents BEFORE planning execution waves.**

**DO NOT use surface-level tool calls (Grep/Glob/Read).** Instead, launch specialized parallel agents to conduct deep research.

### Step 1a: Parse User Request

Extract:
- Task description
- Explicit agent count (if user says "using X agents") - MUST honor exactly if specified
- Target files/directories

### Step 1b: Identify Research Needs

Determine what research is required:
- File discovery? → Use `codebase-locator`
- Implementation analysis? → Use `codebase-analyzer`
- Pattern discovery? → Use `codebase-pattern-finder`
- Architecture understanding? → Use `Explore` (very thorough)
- Best practices? → Use `web-search-researcher`

### Step 1c: Launch Wave 0 Research Agents (In Parallel)

**Output format:**
```
🔍 ANALYZING TASK...

Task: [user's task]

📋 RESEARCH REQUIREMENTS IDENTIFIED:
- [Research need 1] (agent type)
- [Research need 2] (agent type)
- [Research need 3] (agent type)

🌊 WAVE 0: PARALLEL RESEARCH ([N] agents launching...)

Launching [N] specialized research agents in parallel:
├─ Agent R1 ([agent-type]): [Research task 1]
├─ Agent R2 ([agent-type]): [Research task 2]
└─ Agent R[N] ([agent-type]): [Research task N]
```

**Then ACTUALLY LAUNCH the agents using multiple Task tool calls in ONE message:**
```xml
<function_calls>
<invoke name="Task">
<parameter name="subagent_type">codebase-locator</parameter>
<parameter name="description">Wave 0.1: Locate relevant files</parameter>
<parameter name="prompt">Find all files and components relevant to: [task]</parameter>
</invoke>
<invoke name="Task">
<parameter name="subagent_type">codebase-analyzer</parameter>
<parameter name="description">Wave 0.2: Analyze implementation</parameter>
<parameter name="prompt">Analyze implementation details for: [task]</parameter>
</invoke>
... (additional research agents)
</function_calls>
```

### Step 1d: Aggregate Research Findings

**After Wave 0 completes, output:**
```
⏳ Waiting for Wave 0 research to complete...

✅ WAVE 0 COMPLETE - Research Findings:

Agent R1 ([agent-type]) found:
- [Specific finding with details]
- [Specific finding with details]

Agent R2 ([agent-type]) discovered:
- [Specific finding with details]

... (all research findings)

📊 PLANNING EXECUTION WAVES...

Based on research findings:
SUBTASKS IDENTIFIED: [count]
├─ [Subtask 1]
├─ [Subtask 2]
├─ [Subtask 3]
└─ ...

DEPENDENCIES: [None/Shallow/Deep]
TASK TYPE: [file_operations/api_calls/deployment/code_analysis/general]
AVG DURATION: [X] minutes per subtask

SCALING DECISION:
├─ System calculated optimal: [N] agents
├─ User requested: [X] agents (if specified, otherwise "auto")
├─ Resource capacity: [Max] agents
└─ Decision: USING [X] AGENTS [reason]
```

**If user specified agent count:**
```
SCALING DECISION:
├─ User requested: [X] agents 🎯
├─ System calculated optimal: [N] agents
└─ Decision: USING [X] AGENTS (user override - honored exactly) ✅
```

## STEP 2: Output Wave Structure (REQUIRED)

```
🌊 WAVE STRUCTURE:

Wave 1: [Description] ([N] agents - parallel)
├─ Agent 1.1: [task]
├─ Agent 1.2: [task]
└─ ...

Wave 2: [Description] ([N] agents - parallel)
└─ ...

Total: [N] agents across [W] waves
Estimated: [X] min vs [Y] min sequential
```

## STEP 3: Execute with Agent Pooling

**🚨 CRITICAL: Use persistent agent pool with maximum reuse across waves.**

### Agent Pool Strategy:

1. **Parse user request** - Check if explicit agent count specified
2. **Determine pool size**:
   - **If user specified count**: Pool size = user-requested count (MUST honor exactly)
   - **If auto-scaling**: Pool size = max agents needed in any wave
3. **Output pool statistics** - Show reuse rate and overhead savings
4. **Initialize TodoWrite** - Include pool information in wave descriptions
5. **Execute waves** - Reuse agents from pool instead of creating new ones

**🚨 CRITICAL RULE: If user requests X agents, create exactly X agents in the pool, even if fewer would be optimal.**

### Execution Steps:

**Before Wave 1 (Auto-scaling mode):**
```
🏊 AGENT POOL STRATEGY:
├─ Pool size: [N] agents (based on largest wave)
├─ Total waves: [W]
├─ Total agent slots: [X] (sum across all waves)
├─ Without pooling: [X] agents created
├─ With pooling: [N] agents created (reuse [Y]%)
└─ Overhead saved: [Z]s ♻️
```

**Before Wave 1 (User-requested agent count):**
```
🏊 AGENT POOL STRATEGY:
├─ User requested: [X] agents 🎯
├─ Pool size: [X] agents (honoring user request exactly)
├─ System optimal: [N] agents
├─ Total waves: [W]
├─ Decision: Creating pool of [X] agents as requested ✅
└─ Note: [More/Fewer] than optimal, but user preference honored
```

**Wave 1 (Pool Initialization):**
```
🌊 WAVE 1: [Description]
├─ Agents needed: [N]
├─ Pool status: Creating fresh pool of [N] agents
├─ Reused agents: 0 (first wave)
└─ New agents: [N] 🆕

[Launch N agents in parallel - ONE message with N Task calls]
```

**Wave 2+ (Reuse from Pool):**
```
🌊 WAVE [X]: [Description]
├─ Agents needed: [M]
├─ Pool status: [N] agents available
├─ Reused agents: [M] ♻️ (from pool)
└─ New agents: 0

[Assign tasks to M agents from pool - reuse, no initialization]
```

**If wave needs MORE agents than pool capacity:**
```
🌊 WAVE [X]: [Description]
├─ Agents needed: [P]
├─ Pool capacity: [N] agents
├─ Reused agents: [N] ♻️ (all from pool)
├─ New agents: [P-N] 🆕 (expanding pool)
└─ Pool expanded to: [P] agents

[Reuse all N from pool + create P-N new agents]
```

### Key Rules:

1. **Create pool once** - Based on maximum wave size
2. **Reuse agents** - Don't create new agents if pool has capacity
3. **Keep agents alive** - Don't destroy between waves
4. **Expand only when needed** - If wave exceeds pool capacity
5. **Track utilization** - Report which agents did multiple tasks

## STEP 4: Report Results

**🚨 MANDATORY FORMAT: Use detailed agent tracking table with roles, waves, and deliverables.**

### Required Reporting Format:

```
## 📊 EXECUTION SUMMARY
### ✅ Agents Completed: [N]/[N]

| Instance | Role | Waves | Status | Key Deliverables |
|----------|------|-------|--------|------------------|
| I1 | [Role Name] | W[X] | ✅ COMPLETE | [Specific deliverable with metrics] |
| I2 | [Role Name] | W[X] | ✅ COMPLETE | [Specific deliverable with metrics] |
| I3 | [Role Name] | W[X]-W[Y] | ✅ COMPLETE | [Specific deliverable with metrics] |
| ... | ... | ... | ... | ... |

### 📈 Performance Metrics:
- **Total Waves Executed:** [W]
- **Execution Time:** [X] minutes
- **Sequential Time:** [Y] minutes
- **Time Saved:** [Z] minutes ([P]% faster)
- **Agent Reuse Rate:** [R]%
- **Pool Efficiency:** [E]%

### 🎯 Final Results:
[Detailed list of what was accomplished]
```

### Role Assignment Rules:

**Assign each agent a clear, descriptive role based on their task:**
- File operations → "File Processor", "Reader", "Writer", "Consolidator"
- Database tasks → "Database Analyst", "Migration Engineer", "Data Specialist"
- Backend work → "Backend Dev #1", "API Developer", "Endpoint Engineer"
- Security → "Security Engineer", "Audit Specialist"
- Testing → "Test Engineer #1", "Integration Tester", "QA Validator"
- DevOps → "DevOps", "Deployment Specialist", "CI/CD Engineer"
- Documentation → "Documentation", "Doc Writer", "README Specialist"
- Coordination → "Coordinator", "Orchestrator", "Backup Specialist"
- Code Review → "Code Reviewer", "Security Auditor"
- Cleanup → "Cleanup Specialist", "Maintenance Engineer"

### Wave Notation:

- Single wave: `W1`, `W2`, `W3`
- Multiple waves: `W1-W3`, `W2, W5`, `W1, W3-W5`
- Indicate if agent worked across multiple waves

### Deliverables Format:

**Be SPECIFIC with metrics:**
- ✅ "Schema analysis (users: 7 cols, auth_sessions: 6 cols)"
- ✅ "22 integration tests, pytest fixtures"
- ✅ "Security audit 9.5/10 - APPROVED for production"
- ✅ "Git backup (commit 3b2aa4e)"
- ❌ "Created tests" (too vague)
- ❌ "Updated documentation" (too vague)

**Example Report:**

```
## 📊 EXECUTION SUMMARY
### ✅ Agents Completed: 6/6

| Instance | Role | Waves | Status | Key Deliverables |
|----------|------|-------|--------|------------------|
| I1 | File Reader #1 | W1 | ✅ COMPLETE | Read SECURITY_ANALYSIS.md (11 KB, SQL injection findings) |
| I2 | File Reader #2 | W1 | ✅ COMPLETE | Read SECURITY_SUMMARY.txt (12 KB, compliance status) |
| I3 | File Reader #3 | W1 | ✅ COMPLETE | Read SECURITY_REPORT_INDEX.md (7.2 KB, navigation guide) |
| I4 | File Reader #4 | W1 | ✅ COMPLETE | Read VULNERABILITY_CHECKLIST.md (20+ components audited) |
| I5 | File Reader #5 | W1 | ✅ COMPLETE | Read SECURITY_FIX_PATCH.py (393 lines, remediation code) |
| I6 | File Reader #6 | W1 | ✅ COMPLETE | Read SECURITY_REPORT_EXECUTIVE_SUMMARY.txt (CVSS 8.6 findings) |
| I1 | Consolidator | W2 | ✅ COMPLETE | Created Security-Report.md (40 KB, 1,519 lines, 6 sources merged) |
| I2 | Cleanup Specialist | W3 | ✅ COMPLETE | Removed 6 scattered files, verified consolidation |

### 📈 Performance Metrics:
- **Total Waves Executed:** 3
- **Execution Time:** 6 minutes
- **Sequential Time:** 16 minutes
- **Time Saved:** 10 minutes (62% faster)
- **Agent Reuse Rate:** 25% (2 agents reused across waves)
- **Pool Efficiency:** 83%

### 🎯 Final Results:
- ✅ Created comprehensive Security-Report.md (40 KB, 1,519 lines)
- ✅ Consolidated 6 security files into single authoritative source
- ✅ Eliminated redundancy while preserving all unique information
- ✅ Removed scattered files: SECURITY_ANALYSIS.md, SECURITY_SUMMARY.txt, SECURITY_REPORT_INDEX.md, VULNERABILITY_CHECKLIST.md, SECURITY_FIX_PATCH.py, SECURITY_REPORT_EXECUTIVE_SUMMARY.txt
```

---

**CRITICAL:** Steps 1 and 2 MUST be output before any execution. This is non-negotiable.
