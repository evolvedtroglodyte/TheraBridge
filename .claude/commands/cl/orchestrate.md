---
description: Orchestrate complex tasks using intelligent parallel execution
---

# Parallel Task Orchestration

You are executing a parallel orchestration command. When invoked with `/cl:orchestrate [task]`, you MUST follow this protocol:

## STEP 1: Output Task Analysis (REQUIRED)

```
🔍 ANALYZING TASK...

Task: [user's task]

SUBTASKS: [count]
├─ Subtask 1
├─ Subtask 2
└─ ...

DEPENDENCIES: [None/Shallow/Deep]
AGENT COUNT: [N] agents (auto-calculated)
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
