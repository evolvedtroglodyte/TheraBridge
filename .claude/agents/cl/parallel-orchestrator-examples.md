# Parallel Orchestrator Agent - Example Prompts

This document contains practical examples demonstrating how to use the parallel-orchestrator agent for various development workflows.

---

## Example 1: Automatic Scaling - Repository Cleanup

**Prompt:**
```
Clean up all unused imports across the entire codebase. Remove any imports that aren't being used in each file.
```

**Expected Behavior:**
The orchestrator will:
1. Scan the repository to identify all code files (Python, JavaScript, TypeScript, etc.)
2. Automatically determine optimal agent count based on file count
3. Distribute files across agents for parallel analysis
4. Each agent identifies and removes unused imports in their assigned files
5. Consolidate results and report total files modified

---

## Example 2: Explicit Agent Count - Large-Scale Deployment

**Prompt:**
```
Using 50 parallel agents, update all API endpoint configurations to point to the new production domain (api.newdomain.com instead of api.olddomain.com). Check configuration files, environment examples, documentation, and code comments.
```

**Expected Behavior:**
The orchestrator will:
1. Spawn exactly 50 parallel agents as requested
2. Search for all occurrences of the old domain across the repository
3. Distribute files containing the old domain across the 50 agents
4. Each agent updates their assigned files with the new domain
5. Verify no references to the old domain remain
6. Generate a summary report of all files modified

---

## Example 3: Repository Maintenance - Dependency Updates

**Prompt:**
```
Audit all package.json and requirements.txt files in the repository for outdated dependencies. Generate a report showing current versions and latest available versions for each dependency.
```

**Expected Behavior:**
The orchestrator will:
1. Locate all package.json and requirements.txt files across the repository
2. Automatically scale agent count based on number of dependency files
3. Each agent checks their assigned files for current dependency versions
4. Agents query package registries (npm, PyPI) for latest versions
5. Compile a comprehensive report showing:
   - Current version
   - Latest version
   - Version difference (major/minor/patch)
   - Breaking change warnings
6. Organize report by priority (major updates vs patch updates)

---

## Example 4: Code Refactoring - Function Signature Changes

**Prompt:**
```
Using 30 parallel agents, refactor all calls to the deprecated `getUserData(userId)` function to use the new `fetchUserProfile(userId, options)` function with default options. Update function calls, tests, and documentation.
```

**Expected Behavior:**
The orchestrator will:
1. Spawn 30 parallel agents as specified
2. Search for all occurrences of `getUserData` across code, tests, and docs
3. Distribute files across agents for parallel refactoring
4. Each agent:
   - Replaces function calls with the new signature
   - Adds default options parameter where appropriate
   - Updates associated tests
   - Updates inline documentation/comments
5. Run tests to verify refactoring didn't break functionality
6. Report all files modified and any test failures

---

## Example 5: Large-Scale Code Migration

**Prompt:**
```
Migrate all React class components to functional components with hooks. Identify all class components, convert them to functional components, replace lifecycle methods with appropriate hooks (useEffect, useState, etc.), and ensure prop types are preserved.
```

**Expected Behavior:**
The orchestrator will:
1. Scan repository for all React component files
2. Identify files containing class components (extends React.Component)
3. Automatically scale agent count based on number of class components found
4. Distribute components across agents for parallel conversion
5. Each agent:
   - Converts class component to functional component
   - Transforms state to useState hooks
   - Converts componentDidMount/Update/WillUnmount to useEffect
   - Preserves prop types and TypeScript interfaces
   - Maintains component logic and behavior
6. Run component tests to verify conversions are correct
7. Generate detailed report showing:
   - Number of components converted
   - Conversion patterns used
   - Any manual review needed (complex lifecycle logic)
   - Test results

---

## Tips for Using the Parallel Orchestrator

1. **Let it auto-scale**: For most tasks, let the orchestrator determine optimal agent count
2. **Specify count for large operations**: Use explicit agent counts (30-100) for repository-wide changes
3. **Be specific**: Clear prompts lead to better work distribution
4. **Include verification**: Ask the orchestrator to verify changes (run tests, check builds)
5. **Complex refactoring**: Break very complex tasks into sequential steps rather than one massive parallel operation
