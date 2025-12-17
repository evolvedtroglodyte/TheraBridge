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

## STEP 3: Initialize Agent Pool with Clear Roles (REQUIRED)

**🚨 CRITICAL: Create ALL agents upfront with descriptive roles. Reuse them across waves.**

### Agent Pool Strategy:

1. **Parse user request** - Check if explicit agent count specified
2. **Determine pool size using MAXIMUM strategy**:
   - **If user specified count**: Pool size = user-requested count (MUST honor exactly)
   - **If auto-scaling**: Pool size = MAXIMUM agents needed across ALL waves (not average, MAXIMUM)
   - **Goal**: Maximize agent reuse across multiple waves
   - **Example**: If Wave 1 needs 15 agents, Wave 2 needs 8, Wave 3 needs 12 → Create 15-agent pool (not 8 or 12)
3. **Assign clear roles to each agent** based on tasks:
   - File operations → "File Reader #1-N", "File Processor #1-N", "Consolidator"
   - Database → "Database Analyst", "Migration Engineer #1-N", "Schema Validator"
   - Backend → "Backend Dev #1-N", "API Developer #1-N", "Service Builder"
   - Frontend → "Frontend Dev #1-N", "Component Engineer #1-N", "UI Specialist #1-N"
   - Testing → "Test Engineer #1-N", "QA Validator #1-N", "Integration Tester"
   - Security → "Security Engineer", "Audit Specialist", "Vulnerability Analyst"
   - DevOps → "DevOps Engineer", "Deployment Specialist", "Infrastructure"
   - Documentation → "Documentation Specialist", "README Writer"
4. **Create agent pool manifest** - Map each agent instance (I1, I2, etc.) to its role
5. **Initialize TodoWrite** - Include agent roles and wave assignments
6. **Execute waves** - Assign specific agents by role to tasks

**🚨 CRITICAL RULES:**
- **ALL agents created upfront** - No on-demand agent creation during execution
- **Clear descriptive roles** - Every agent has a specific job title
- **Agent persistence** - Same agent instances used across multiple waves
- **Role-based assignment** - Tasks assigned to agents by their role/expertise

### Execution Steps:

**Step 3a: Create Agent Pool Manifest (REQUIRED)**

Before executing any waves, create a manifest mapping agents to roles:

```
🏊 AGENT POOL INITIALIZATION:

Creating pool of [N] agents with assigned roles:

| Instance | Role | Specialty | Waves Assigned |
|----------|------|-----------|----------------|
| I1 | Backend Dev #1 | API endpoints | W1, W3 |
| I2 | Backend Dev #2 | Services layer | W1, W3 |
| I3 | Frontend Dev #1 | Components | W2, W4 |
| I4 | Frontend Dev #2 | Hooks/utils | W2, W4 |
| I5 | Test Engineer #1 | Unit tests | W5 |
| I6 | Test Engineer #2 | Integration tests | W5 |
| I7 | Security Engineer | Auditing | W6 |
| I8 | Documentation Specialist | README/guides | W7 |
| ... | ... | ... | ... |

Pool Statistics:
├─ Total agents: [N]
├─ Total waves: [W]
├─ Agent reuse rate: [X]% (Y agents work multiple waves)
├─ Average tasks per agent: [Z]
└─ Pool efficiency: [E]% ✅
```

**Step 3b: Output Pool Strategy**

**Auto-scaling mode:**
```
🏊 AGENT POOL STRATEGY:
├─ Pool size: [N] agents (based on largest wave)
├─ Total waves: [W]
├─ Total agent slots: [X] (sum across all waves)
├─ Without pooling: [X] agents created
├─ With pooling: [N] agents created (reuse [Y]%)
└─ Overhead saved: [Z]s ♻️
```

**User-requested agent count:**
```
🏊 AGENT POOL STRATEGY:
├─ User requested: [X] agents 🎯
├─ Pool size: [X] agents (honoring user request exactly)
├─ System optimal: [N] agents
├─ Total waves: [W]
├─ Decision: Creating pool of [X] agents as requested ✅
└─ Note: [More/Fewer] than optimal, but user preference honored
```

**Step 3c: Execute Wave 1 (Pool Initialization with Roles)**

```
🌊 WAVE 1: [Description]
├─ Agents needed: [N]
├─ Pool status: Creating fresh pool of [N] agents with roles
├─ Assignments:
│   ├─ I1 (Backend Dev #1): [Specific task]
│   ├─ I2 (Backend Dev #2): [Specific task]
│   ├─ I3 (Frontend Dev #1): [Specific task]
│   └─ ... (N agents total)
└─ Status: Launching [N] agents in parallel... 🆕

[Launch N agents in parallel - ONE message with N Task calls]
[Each Task description includes: "Wave 1.X: [Role] - [Task description]"]
```

**🚨 CRITICAL: Agent roles MUST be in the prompt at launch, not just in description**

**Example Task invocations:**
```xml
<function_calls>
<invoke name="Task">
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="description">Wave 1.1: Backend Dev #1 - Implement auth endpoint</parameter>
<parameter name="prompt">You are Backend Dev #1 (Instance I1) working on Wave 1.

Your role: Backend developer specializing in authentication endpoints
Your task: Implement the authentication endpoint at backend/app/routers/auth.py

Context: You are part of a 6-agent team implementing a full-stack feature. Your specialty is backend API development.

Requirements:
- Create POST /auth/login endpoint
- Validate email/password input
- Return JWT token on success
- Follow existing patterns in auth.py

Success criteria: Endpoint functional, follows project patterns, returns proper JWT token

When complete, report your deliverables with specific metrics (e.g., "Created /auth/login endpoint, 45 lines, JWT token generation with 24h expiry").</parameter>
</invoke>
<invoke name="Task">
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="description">Wave 1.2: Backend Dev #2 - Implement session endpoint</parameter>
<parameter name="prompt">You are Backend Dev #2 (Instance I2) working on Wave 1.

Your role: Backend developer specializing in session management
Your task: Implement the session creation endpoint at backend/app/routers/sessions.py

Context: You are part of a 6-agent team. Backend Dev #1 is working on auth, you're handling sessions.

Requirements:
- Create POST /sessions/create endpoint
- Accept session data payload
- Store in database
- Return session ID

Success criteria: Endpoint functional, database integration working

When complete, report your deliverables with specific metrics.</parameter>
</invoke>
... (more agents with roles in prompts)
</function_calls>
```

**Step 3d: Execute Wave 2+ (Reuse Agents by Role)**

```
🌊 WAVE [X]: [Description]
├─ Agents needed: [M]
├─ Pool status: [N] agents available for reuse
├─ Assignments:
│   ├─ I1 (Backend Dev #1): [New task] ♻️ REUSED
│   ├─ I3 (Frontend Dev #1): [New task] ♻️ REUSED
│   └─ ... (M agents total)
└─ Status: Assigning tasks to agents from pool...

[Assign tasks to M agents from pool by their roles]
[Tasks given to agents match their expertise/role]
```

**Step 3e: After Wave Completion - Provide Continuation Prompt**

**🚨 CRITICAL: After EVERY wave completes, if there are pending waves remaining, provide the user with a continuation prompt to work in another window.**

After wave completes and before launching next wave:

```
✅ WAVE [X] COMPLETE

[Summary of what was accomplished in this wave]

📋 REMAINING WORK:
- Wave [X+1]: [Description] ([N] agents)
- Wave [X+2]: [Description] ([M] agents)
- ... ([Y] waves remaining)

💡 CONTINUATION PROMPT (copy to another window if needed):

Continue the orchestration from Wave [X+1]:

Current state:
- Pool: [N] agents initialized with roles (I1-I[N])
- Completed: Waves 1-[X]
- Next: Wave [X+1] - [Description]

Agent pool status:
- I1 (Backend Dev #1): Available for Wave [X+1] task
- I2 (Backend Dev #2): Available for Wave [X+1] task
- ...

Ready to proceed with Wave [X+1]? (yes/no)
```

**Example:**
```
✅ WAVE 1 COMPLETE

Accomplished:
- I1 (Backend Dev #1): Created /auth/login endpoint (45 lines, JWT generation)
- I2 (Backend Dev #2): Created /auth/signup endpoint (52 lines, password hashing)
- I3 (Backend Dev #3): Created /sessions/create endpoint (38 lines)
- I4 (Frontend Dev #1): Created LoginForm component (120 lines)
- I5 (Frontend Dev #2): Created SignupForm component (135 lines)
- I6 (Frontend Dev #3): Created SessionCard component (95 lines)

📋 REMAINING WORK:
- Wave 2: Add validation and error handling (4 agents)
- Wave 3: Write tests (2 agents)
- Wave 4: Documentation (1 agent)
(3 waves remaining)

💡 CONTINUATION PROMPT (copy to another window if needed):

Continue the orchestration from Wave 2:

Current state:
- Pool: 6 agents initialized (I1-I6)
- Completed: Wave 1 (backend/frontend endpoints implemented)
- Next: Wave 2 - Add validation and error handling

Agent pool status:
- I1 (Backend Dev #1): Available for validation work
- I2 (Backend Dev #2): Available for validation work
- I4 (Frontend Dev #1): Available for error handling
- I5 (Frontend Dev #2): Available for error handling

Task: Add input validation to login/signup endpoints and error handling to forms.

Ready to proceed with Wave 2? (yes/no)
```

This allows you to:
1. **Pause between waves** without losing context
2. **Continue in a new window** if main window is running low on context
3. **Resume from any wave** with full agent pool state
4. **Parallelize orchestration work** across multiple Claude windows

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
