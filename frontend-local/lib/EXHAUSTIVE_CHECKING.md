# Exhaustive Type Checking Guide

This document explains how to use exhaustive type checking in the frontend codebase to ensure all enum and union type cases are handled at compile time.

## Overview

Exhaustive checking is a TypeScript pattern that guarantees all possible values of a union type or enum are handled in switch statements or conditional chains. This prevents runtime errors caused by missing cases when new values are added to a type.

## The Problem It Solves

Without exhaustive checking:

```typescript
type Status = 'loading' | 'success' | 'error';

function renderStatus(status: Status) {
  switch (status) {
    case 'loading':
      return <Spinner />;
    case 'success':
      return <Result />;
    // Missing 'error' case - but TypeScript doesn't complain!
  }
}
```

Later, if someone adds a new status value and forgets to update all the switch statements, you'll get a runtime error instead of a compile-time error.

## The Solution: assertNever()

The `assertNever` helper function enforces exhaustive checking:

```typescript
import { assertNever } from '@/lib/exhaustive';

type Status = 'loading' | 'success' | 'error';

function renderStatus(status: Status) {
  switch (status) {
    case 'loading':
      return <Spinner />;
    case 'success':
      return <Result />;
    case 'error':
      return <ErrorMessage />;
    default:
      return assertNever(status); // TypeScript error if any case is missing
  }
}
```

If you add a new status value but forget to handle it, TypeScript will show a compilation error immediately.

## Usage Examples

### 1. Switch Statements

```typescript
import { assertNever } from '@/lib/exhaustive';

type Color = 'red' | 'green' | 'blue';

const getHexColor = (color: Color): string => {
  switch (color) {
    case 'red':
      return '#FF0000';
    case 'green':
      return '#00FF00';
    case 'blue':
      return '#0000FF';
    default:
      return assertNever(color);
  }
};
```

### 2. If-Else Chains

```typescript
import { assertNever } from '@/lib/exhaustive';

type UserRole = 'admin' | 'moderator' | 'user';

function getPermissionLevel(role: UserRole): number {
  if (role === 'admin') {
    return 100;
  } else if (role === 'moderator') {
    return 50;
  } else if (role === 'user') {
    return 10;
  } else {
    return assertNever(role);
  }
}
```

### 3. Object/Lookup Tables with buildExhaustive()

The `buildExhaustive()` helper ensures you provide configuration for every enum/union value:

```typescript
import { buildExhaustive } from '@/lib/exhaustive';

type SessionStatus = 'uploading' | 'processing' | 'completed' | 'failed';

const statusConfig = buildExhaustive<SessionStatus, { label: string; color: string }>({
  uploading: { label: 'Uploading...', color: 'blue' },
  processing: { label: 'Processing...', color: 'yellow' },
  completed: { label: 'Completed', color: 'green' },
  failed: { label: 'Failed', color: 'red' },
  // TypeScript error if you forget any key!
});

function StatusBadge({ status }: { status: SessionStatus }) {
  const { label, color } = statusConfig[status];
  return <div style={{ backgroundColor: color }}>{label}</div>;
}
```

### 4. Real Component Example

From `SessionStatusBadge.tsx`:

```typescript
import { buildExhaustive } from '@/lib/exhaustive';
import type { SessionStatus } from '@/lib/types';

export function SessionStatusBadge({ status }: { status: SessionStatus }) {
  // This ensures all SessionStatus values are covered
  const config = buildExhaustive<SessionStatus, ConfigType>({
    uploading: { label: 'Uploading', className: 'bg-blue-100', icon: <Loader2 /> },
    transcribing: { label: 'Transcribing', className: 'bg-yellow-100', icon: <Loader2 /> },
    transcribed: { label: 'Transcribed', className: 'bg-purple-100', icon: null },
    extracting_notes: { label: 'Extracting Notes', className: 'bg-purple-100', icon: <Loader2 /> },
    processed: { label: 'Processed', className: 'bg-green-100', icon: null },
    failed: { label: 'Failed', className: 'bg-red-100', icon: null },
  });

  const { label, className, icon } = config[status];
  return <Badge className={className}>{icon} {label}</Badge>;
}
```

## Available Utilities

### assertNever(x: never): never

The core function. Use in `default` cases of switch statements or at the end of if-else chains.

**Throws:** Error with message about exhaustive check failure.

### buildExhaustive<T, V>(obj: Record<T, V>): Record<T, V>

Helper for creating exhaustive lookup/configuration objects.

### match<T, R>(value: T, handlers: Record<T, () => R>): R

Utility function for exhaustive pattern matching without a switch statement.

```typescript
const result = match(status, {
  loading: () => <Spinner />,
  success: () => <Success />,
  error: () => <Error />,
});
```

### matchWith<T, D, R>(value: T, data: D, handlers: Record<T, (data: D) => R>): R

Like `match()` but passes data to each handler:

```typescript
const result = matchWith(role, userData, {
  admin: (user) => `Admin: ${user.name}`,
  user: (user) => `User: ${user.name}`,
});
```

### isValidValue<T>(value: unknown, validValues: T[]): value is T

Type guard for checking if a value is in an allowed set.

```typescript
type Status = 'active' | 'inactive' | 'pending';

if (isValidValue(status, ['active', 'pending'])) {
  // status is now 'active' | 'pending'
}
```

## Best Practices

1. **Always use exhaustive checking for union types**
   - Don't rely on implicit behavior
   - Add `default: assertNever(value)` to every switch statement

2. **Use `buildExhaustive()` for lookup tables**
   - More type-safe than object literals
   - Prevents missing cases when types change

3. **Name it clearly**
   - Use comments like `// Exhaustive config for SessionStatus`
   - Makes the intent obvious to other developers

4. **Update when adding new values**
   - Adding a new enum/union value should cause TypeScript errors everywhere it's used
   - This is a feature, not a bug! It forces you to handle new cases

5. **Don't use `any` to silence errors**
   - If TypeScript complains about exhaustiveness, handle the missing case
   - Don't work around the type system

## Common Patterns in Codebase

### Status Badge Components

```typescript
const statusConfig = buildExhaustive<SessionStatus, BadgeConfig>({
  // one entry per status
});
const { label, icon } = statusConfig[status];
```

### Conditional Rendering

```typescript
switch (state.status) {
  case 'idle':
    return <Initial />;
  case 'loading':
    return <Spinner />;
  case 'success':
    return <Content data={state.data} />;
  case 'error':
    return <Error error={state.error} />;
  default:
    return assertNever(state);
}
```

### Role-Based Access

```typescript
const permissions = buildExhaustive<UserRole, Permission>({
  admin: ALL_PERMISSIONS,
  user: LIMITED_PERMISSIONS,
  guest: NO_PERMISSIONS,
});
```

## Related Files

- `/lib/exhaustive.ts` - Main utilities (implementation and documentation)
- `/lib/async-states.ts` - Uses `assertNever` in the `match()` function
- `/components/SessionStatusBadge.tsx` - Uses `buildExhaustive` for status configuration
- `/components/MoodIndicator.tsx` - Uses `buildExhaustive` for mood and trajectory configs

## Migration Guide

If you have existing code without exhaustive checking:

### Before
```typescript
function renderStatus(status: SessionStatus) {
  if (status === 'loading') {
    return <Spinner />;
  } else if (status === 'success') {
    return <Result />;
  }
  // What about other cases?
}
```

### After
```typescript
import { assertNever } from '@/lib/exhaustive';

function renderStatus(status: SessionStatus) {
  if (status === 'loading') {
    return <Spinner />;
  } else if (status === 'success') {
    return <Result />;
  } else {
    return assertNever(status); // TypeScript enforces all cases handled
  }
}
```

## Troubleshooting

### "Type is not assignable to type 'never'"

This is intentional! It means you have an unhandled case. Add handling for the missing value:

```typescript
switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Success />;
  case 'error': return <Error />;
  // TypeScript error here means you forgot a case
  default: return assertNever(status);
}
```

### "Property 'xyz' is missing in type"

When using `buildExhaustive()`, make sure you have an entry for every value:

```typescript
// Error: missing 'error' case
const config = buildExhaustive<Status>({
  loading: { ... },
  success: { ... },
  // Add: error: { ... }
});
```

## Performance

Zero runtime cost. These are pure TypeScript compile-time utilities that compile to JavaScript with no overhead.

## See Also

- TypeScript Handbook: [Exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-func.html#unions)
- Never type documentation
- Discriminated unions pattern
