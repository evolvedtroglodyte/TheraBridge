# Coding Conventions

**Analysis Date:** 2026-01-08

## Naming Patterns

**Files:**
- Components: PascalCase (SessionCard.tsx, DeepAnalysisSection.tsx)
- Utilities/helpers: kebab-case (refresh-detection.ts, demo-token-storage.ts)
- Custom hooks: use-prefix with kebab-case in lib (usePatientSessions.ts)
- Deprecated files: UPPERCASE.DEPRECATED suffix (Header.DEPRECATED.tsx)
- Test files: kebab-case.spec.ts (dashboard-fonts.spec.ts)
- Python modules: snake_case (mood_analyzer.py, topic_extractor.py)

**Functions:**
- TypeScript: camelCase (getPatientSessions, analyzeMood)
- Python: snake_case (analyze_session_mood, get_technique_library)
- Async functions: No special prefix (async keyword sufficient)
- Event handlers: handle + EventName (handleClick, handleSubmit)

**Variables:**
- TypeScript: camelCase (selectedSession, isDark, loadingSessions)
- Python: snake_case (session_id, mood_score, analysis_status)
- Constants: UPPERCASE (POLLING_CONFIG, TYPOGRAPHY, MAX_RETRIES)
- Private (Python): _leading_underscore (_format_conversation, _validate_token)

**Types:**
- Interfaces: PascalCase, no I prefix (Session, SessionCardProps, MoodAnalysis)
- Type aliases: PascalCase (ApiResult, SessionId, PatientId)
- Enums: PascalCase for enum name, UPPER_CASE for values (Status.PENDING)
- Dataclasses (Python): PascalCase (MoodAnalysis, SessionMetadata)

## Code Style

**Formatting (TypeScript/JavaScript):**
- Tool: Prettier 3.1.0 (`.pre-commit-config.yaml`)
- Line length: 100 characters max
- Quotes: Single quotes for strings (`'use client'`)
- Semicolons: Always required
- Indentation: 2 spaces
- Arrow functions: Preferred over `function` keyword
- Template literals: Preferred for string interpolation

**Formatting (Python):**
- Tool: Black 23.12.1 (`.pre-commit-config.yaml`)
- Line length: 88 characters (Black default)
- Quotes: Single quotes for strings, triple double quotes for docstrings
- Indentation: 4 spaces
- Type hints: Comprehensive on all function signatures

**Linting:**
- Frontend: ESLint 9 with Next.js TypeScript config (`frontend/eslint.config.mjs`)
- Extends: `next/core-web-vitals`, `next/typescript`
- Excludes: `.next/`, `out/`, `build/`, `next-env.d.ts`
- Run: `npm run lint`

- Backend: No explicit linting (Black + isort enforce style)
- Import sorting: isort 5.13.2 with `--profile black`
- Run: Pre-commit hooks automatically format

## Import Organization

**TypeScript Order:**
```typescript
// Example from SessionCard.tsx:
import { useState } from 'react';                    // 1. React imports
import { motion, AnimatePresence } from 'framer-motion'; // 2. Third-party libraries
import { createPortal } from 'react-dom';            // 3. Additional third-party
import { Session } from '../lib/types';              // 4. Local relative imports
import { useTheme } from '../contexts/ThemeContext'; // 5. Local contexts/hooks
```

**Python Order:**
```python
# Example from mood_analyzer.py:
from dataclasses import dataclass                    # 1. Standard library
from datetime import datetime
from typing import List

from openai import OpenAI                            # 2. Third-party imports
from pydantic import BaseModel

from app.database import get_supabase_admin          # 3. Local imports
```

**Grouping:**
- Blank lines between import groups
- Alphabetical within each group (enforced by isort)
- Type imports last within each group

**Path Aliases:**
- None configured (relative imports only)

## Error Handling

**TypeScript Patterns:**
- Strategy: Discriminated union return type (`ApiResult<T>`)
- Success/failure types explicitly handled
- Async: try/catch with typed error responses
- Example:
```typescript
type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: NetworkError | TimeoutError | ValidationError | ServerError };
```

**Python Patterns:**
- Strategy: Raise HTTPException at boundaries, catch in routers
- Custom errors: Extend Exception class with PascalCase names
- Async: try/except with comprehensive logging
- Example:
```python
if not session_id:
    raise HTTPException(status_code=400, detail="Session ID required")
```

**Error Types:**
- TypeScript: Network, Timeout, Validation, Server (discriminated union)
- Python: HTTPException with status codes (400, 404, 500)
- When to throw: Invalid input, missing dependencies, invariant violations
- When to return: Expected failures use Result<T, E> pattern

**Logging:**
- Backend: `print(..., flush=True)` for Railway visibility + Python logging
- Frontend: Conditional `console.log()` via `NEXT_PUBLIC_DEBUG_POLLING` flag
- Avoid: console.log in committed production code (714 instances need cleanup)

## Logging

**Framework:**
- Backend: Python `logging` module + `print(..., flush=True)`
- Frontend: Browser console (conditional debug mode)

**Patterns:**
- Backend: Structured logging with context
  ```python
  logger.info(f"Analyzing session {session_id}")
  print(f"[MoodAnalyzer] Session {session_id} complete", flush=True)
  ```
- Frontend: Module prefix for debugging
  ```typescript
  console.log('[usePatientSessions] Fetching sessions:', patientId);
  ```

**When to Log:**
- Backend: State transitions, external API calls, errors, subprocess events
- Frontend: Debug mode only (NEXT_PUBLIC_DEBUG_POLLING=true)
- Avoid: Logging in utility functions (only at service boundaries)

## Comments

**When to Comment:**
- Explain why, not what
- Document business logic, algorithms, edge cases
- Explain non-obvious patterns or workarounds
- Avoid obvious comments like `// increment counter`

**TypeScript JSDoc:**
```typescript
/**
 * SessionCard - Two card variants for therapy sessions
 * 1. Normal Session Card - with mood emoji
 * 2. Breakthrough Session Card - illuminated gold star
 */
```

**Python Docstrings:**
```python
class MoodAnalyzer:
    """
    AI-powered mood analysis for therapy sessions.

    Uses GPT-4o-mini to analyze patient mood by examining:
    - Emotional language and sentiment
    - Self-reported feelings and experiences
    - Energy level indicators (sleep, appetite, motivation)
    """
```

**TODO Comments:**
- Format: `// TODO: description` (TypeScript) or `# TODO: description` (Python)
- Tracking: Not linked to issues (direct implementation recommended)
- Examples:
  - `// TODO: Implement download transcript functionality`
  - `# TODO: Add retry logic for API failures`

## Function Design

**Size:**
- Keep under 50 lines where possible
- Extract helpers for complex logic
- One level of abstraction per function

**Parameters:**
- TypeScript: Max 3 parameters, use object for more
- Python: Max 3 parameters, use dataclass for complex inputs
- Destructure objects in parameter list:
  ```typescript
  function process({ id, name }: ProcessParams) { ... }
  ```

**Return Values:**
- TypeScript: Explicit return types, discriminated unions for errors
- Python: Type hints on all return values
- Return early for guard clauses

## Module Design

**Exports:**
- TypeScript: Named exports preferred, default exports for React components only
- Python: No default exports (named imports only)
- Export public API from barrel files (not used extensively)

**Barrel Files:**
- TypeScript: Use index.ts to re-export public API (minimal usage)
- Python: Use __init__.py for package exports (not used)
- Avoid circular dependencies

**File Organization:**
- Feature-based grouping (components/, services/, routers/)
- Utility grouping (lib/, utils/)
- Test colocation or parallel tests/ directory

---

*Convention analysis: 2026-01-08*
*Update when patterns change*
