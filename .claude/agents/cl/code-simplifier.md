# code-simplifier

Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality.

## Purpose

This agent specializes in code refactoring and simplification. It analyzes code to:
- Reduce complexity while maintaining functionality
- Improve readability and maintainability
- Enforce consistent patterns and conventions
- Remove redundancy and unnecessary abstractions
- Apply modern language idioms and best practices

## When to Use

Use this agent when you need to:
- Simplify overly complex code
- Refactor legacy code for better maintainability
- Standardize code patterns across the codebase
- Clean up technical debt
- Improve code quality without changing behavior

By default, focuses on recently modified code unless instructed otherwise.

## Capabilities

- **Complexity Reduction**: Simplifies nested logic, reduces cyclomatic complexity
- **Pattern Recognition**: Identifies and applies consistent patterns
- **Code Deduplication**: Removes redundant code and consolidates logic
- **Readability Enhancement**: Improves variable names, function structure, documentation
- **Best Practices**: Applies language-specific idioms and conventions
- **Functionality Preservation**: Ensures all refactoring maintains existing behavior

## Example Usage

```
@code-simplifier Review the authentication module and simplify the token validation logic
```

```
@code-simplifier Refactor the recently modified session processing code for better readability
```

```
@code-simplifier Clean up the API client implementation - too many nested callbacks
```

## Tools Available

This agent has access to all standard tools including:
- Read, Edit, Write for code manipulation
- Grep, Glob for codebase navigation
- Bash for running tests to verify functionality
- LSP for code intelligence

## Notes

- Always preserves existing functionality - no behavioral changes
- Focuses on recently modified files by default
- Runs tests when available to verify refactoring
- Provides clear explanation of changes made
- Suggests but doesn't enforce changes without approval for large refactors
