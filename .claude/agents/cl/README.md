# Claude Code Agents

## Overview

This directory contains specialized AI agents that help you work with your codebase more effectively. Each agent is optimized for specific tasks and can be invoked with natural language prompts.

## Available Agents

### codebase-analyzer

**Purpose:** Analyzes implementation details and explains how code works

**When to use:**
- Understanding how specific components work
- Tracing data flow through the system
- Identifying architectural patterns
- Getting detailed technical documentation

**Tools:** Read, Grep, Glob, LS

**Example:**
```
@codebase-analyzer Explain how the authentication flow works in the backend API
```

---

### codebase-locator

**Purpose:** Finds files, directories, and components relevant to a feature

**When to use:**
- Locating code related to a specific feature
- Finding test files for a component
- Discovering configuration files
- Understanding project organization

**Tools:** Grep, Glob, LS

**Example:**
```
@codebase-locator Find all files related to session management
```

---

### codebase-pattern-finder

**Purpose:** Discovers existing code patterns and usage examples

**When to use:**
- Finding similar implementations to model after
- Discovering established conventions
- Locating test patterns
- Understanding how features are typically built

**Tools:** Grep, Glob, Read, LS

**Example:**
```
@codebase-pattern-finder Show me how pagination is implemented in this codebase
```

---

### web-search-researcher

**Purpose:** Researches information from web sources

**When to use:**
- Finding documentation for libraries/APIs
- Researching best practices
- Looking up technical solutions
- Getting current information beyond AI training data

**Tools:** WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS

**Example:**
```
@web-search-researcher Find the latest FastAPI documentation on WebSocket connections
```

---

### parallel-orchestrator (Advanced)

**Purpose:** Executes complex multi-step tasks using parallel AI agents

The parallel-orchestrator enables large-scale operations by breaking them into coordinated subtasks executed across multiple agents working in parallel waves. It uses intelligent auto-scaling to determine the optimal number of agents (1 to unlimited) based on cost-benefit analysis.

**When to use:**
- Large-scale refactoring or migrations across many files
- Multi-file analysis or bulk modifications
- Complex tasks requiring 5+ independent operations
- Any operation that benefits from parallel execution

**Usage Modes:**

1. **Automatic Scaling (Recommended):**
   ```
   @parallel-orchestrator Refactor all React components to use TypeScript strict mode
   ```
   System automatically determines optimal agent count based on task complexity, dependencies, and ROI.

2. **Explicit Agent Count:**
   ```
   @parallel-orchestrator with 50 agents Clean up and organize the entire repository
   ```
   Specify exact number of agents for precise control.

**Key Features:**
- Intelligent auto-scaling (1 to unlimited agents)
- Cost-benefit analysis and ROI calculation
- Resource-aware scaling (CPU, memory, disk, network)
- Task-specific optimization (file I/O, API calls, deployments)
- Real-time adaptive execution
- Multi-wave coordination with dependency management

**Example Prompts:**
```
@parallel-orchestrator Migrate all database queries from raw SQL to ORM
@parallel-orchestrator with 100 agents Analyze test coverage across entire codebase
@parallel-orchestrator Deploy to all production servers with health checks
```

**Full Documentation:** See `.claude/DYNAMIC_WAVE_ORCHESTRATION.md` for complete methodology and advanced usage.

---

## Tips

- Be specific in your prompts for better results
- Agents document what exists without making judgments
- Multiple agents can work together on complex tasks
- Use parallel-orchestrator for large-scale operations
