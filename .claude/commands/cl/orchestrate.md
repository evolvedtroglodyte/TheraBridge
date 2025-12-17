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
├─ Resource capacity: [Max] agents
└─ Decision: USING [N] AGENTS [reason]
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

## STEP 3: Execute

1. Initialize TodoWrite with all waves
2. Launch Wave 1 agents (parallel Task calls in ONE message)
3. Wait for completion
4. Launch Wave 2 agents
5. Repeat until done

## STEP 4: Report Results

Show what was accomplished.

---

**CRITICAL:** Steps 1 and 2 MUST be output before any execution. This is non-negotiable.
