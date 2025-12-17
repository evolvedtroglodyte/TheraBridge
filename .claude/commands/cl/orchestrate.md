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

## STEP 1: Output Task Analysis (REQUIRED)

**First, read `.claude/DYNAMIC_WAVE_ORCHESTRATION.md` to understand the intelligent_auto_scale() algorithm.**

**CRITICAL: Parse user request for explicit agent count:**
- If user says "using X agents" or "with X agents" → MUST use exactly X agents
- If no explicit count specified → Use intelligent auto-scaling

Then output:

```
🔍 ANALYZING TASK...

Task: [user's task]

SUBTASKS: [count]
├─ Subtask 1
├─ Subtask 2
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

Show what was accomplished, including agent pool statistics.

### Final Report Format:

```
✅ ORCHESTRATION COMPLETE

📊 EXECUTION SUMMARY:
├─ Task: [task description]
├─ Total waves: [W]
├─ Total tasks: [X]
├─ Execution time: [Y] minutes
└─ Sequential time: [Z] minutes (saved [Z-Y] minutes)

📊 AGENT POOL STATISTICS:
├─ Total agents created: [N]
├─ Total tasks completed: [X]
├─ Average tasks per agent: [X/N]
├─ Agent utilization:
│   ├─ Agent 1: [T1] tasks (Wave [list])
│   ├─ Agent 2: [T2] tasks (Wave [list])
│   └─ Agents [3-N]: [T] task(s) each
├─ Reuse rate: [Y]% ([R] of [X] task slots reused agents)
├─ Overhead saved: [Z]s (vs creating [X] fresh agents)
└─ Pool efficiency: [E]% ✅

RESULTS:
[What was accomplished]
```

**Example:**
```
✅ ORCHESTRATION COMPLETE

📊 EXECUTION SUMMARY:
├─ Task: Consolidate security files into Project MDs/
├─ Total waves: 3
├─ Total tasks: 8
├─ Execution time: 6 minutes
└─ Sequential time: 16 minutes (saved 10 minutes)

📊 AGENT POOL STATISTICS:
├─ Total agents created: 6
├─ Total tasks completed: 8
├─ Average tasks per agent: 1.3
├─ Agent utilization:
│   ├─ Agent 1: 2 tasks (Wave 1, 2)
│   ├─ Agent 2: 2 tasks (Wave 1, 3)
│   └─ Agents 3-6: 1 task each (Wave 1 only)
├─ Reuse rate: 25% (2 of 8 task slots reused agents)
├─ Overhead saved: 0.6s (vs creating 8 fresh agents)
└─ Pool efficiency: 83% ✅

RESULTS:
- Created Project MDs/Security-Report.md (40 KB, 1,519 lines)
- Removed 6 scattered security files
- All security documentation consolidated into single comprehensive report
```

---

**CRITICAL:** Steps 1 and 2 MUST be output before any execution. This is non-negotiable.
