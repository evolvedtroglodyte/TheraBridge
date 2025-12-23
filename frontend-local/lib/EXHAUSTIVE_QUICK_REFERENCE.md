# Exhaustive Type Checking - Quick Reference

**Import:**
```typescript
import { assertNever, buildExhaustive, match, matchWith } from '@/lib/exhaustive';
```

## When to Use

| Situation | Solution | Example |
|-----------|----------|---------|
| **Switch statement** handling all cases | Add `default: assertNever(value)` | See below |
| **Lookup/config object** for enum | Use `buildExhaustive<Type, ValueType>()` | See below |
| **Pattern matching** without switch | Use `match(value, handlers)` | See below |
| **Passing data** through handlers | Use `matchWith(value, data, handlers)` | See below |

## 5-Second Examples

### assertNever (Switch Statement)
```typescript
switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Result />;
  case 'error': return <Error />;
  default: return assertNever(status); // ← Add this line
}
```

### buildExhaustive (Lookup Table)
```typescript
const config = buildExhaustive<Status, ConfigType>({
  loading: { label: 'Loading', icon: <Spinner /> },
  success: { label: 'Success', icon: <Check /> },
  error: { label: 'Error', icon: <Alert /> },
  // ← TypeScript error if any Status value is missing!
});

const { label, icon } = config[status];
```

### match (Pattern Matching)
```typescript
const message = match(status, {
  loading: () => 'Loading...',
  success: () => 'Done!',
  error: () => 'Error!',
});
```

### matchWith (With Data)
```typescript
const greeting = matchWith(role, user, {
  admin: (u) => `Admin: ${u.name}`,
  user: (u) => `User: ${u.name}`,
  guest: (u) => `Guest: ${u.name}`,
});
```

## Common Patterns

### React Component with Status
```typescript
function StatusComponent({ status }: { status: Status }) {
  const config = buildExhaustive<Status, { label: string; color: string }>({
    idle: { label: 'Ready', color: 'gray' },
    loading: { label: 'Loading', color: 'blue' },
    success: { label: 'Done', color: 'green' },
    error: { label: 'Error', color: 'red' },
  });

  const { label, color } = config[status];
  return <div style={{ color }}>{label}</div>;
}
```

### Role-Based Access
```typescript
const permissions = buildExhaustive<Role, Permission>({
  admin: ALL_PERMISSIONS,
  user: LIMITED_PERMISSIONS,
  guest: NO_PERMISSIONS,
});

const userPerms = permissions[userRole];
```

### If-Else Chain
```typescript
if (status === 'active') {
  return <Active />;
} else if (status === 'pending') {
  return <Pending />;
} else if (status === 'inactive') {
  return <Inactive />;
} else {
  return assertNever(status); // ← Guarantees all cases handled
}
```

## What Happens When Cases are Missing?

**With exhaustive checking:**
```typescript
type Status = 'loading' | 'success' | 'error';

switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Result />;
  // ← TypeScript ERROR: missing 'error' case
  default: return assertNever(status);
}
```

**Without exhaustive checking:**
```typescript
switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Result />;
  // ← No error, but will crash at runtime if status='error'
}
```

## Real Examples in Codebase

**1. async-states.ts** - Switch with assertNever
```typescript
export function match<T, E, R>(
  state: AsyncState<T, E>,
  handlers: { idle: () => R; loading: () => R; success: (data: T) => R; error: (error: E) => R }
): R {
  switch (state.status) {
    case 'idle': return handlers.idle();
    case 'loading': return handlers.loading();
    case 'success': return handlers.success(state.data);
    case 'error': return handlers.error(state.error);
    default: return assertNever(state);  // ← Added exhaustiveness check
  }
}
```

**2. SessionStatusBadge.tsx** - Lookup table with buildExhaustive
```typescript
const config = buildExhaustive<SessionStatus, ConfigType>({
  uploading: { label: 'Uploading', icon: <Loader2 /> },
  transcribing: { label: 'Transcribing', icon: <Loader2 /> },
  transcribed: { label: 'Transcribed', icon: null },
  extracting_notes: { label: 'Extracting Notes', icon: <Loader2 /> },
  processed: { label: 'Processed', icon: null },
  failed: { label: 'Failed', icon: null },
  // ← All 6 SessionStatus values covered
});
```

**3. MoodIndicator.tsx** - Multiple configs
```typescript
const moodConfig = buildExhaustive<SessionMood, ConfigType>({
  very_low: { emoji: '😢', label: 'Very Low', color: 'bg-red-600' },
  low: { emoji: '😔', label: 'Low', color: 'bg-orange-500' },
  neutral: { emoji: '😐', label: 'Neutral', color: 'bg-gray-400' },
  positive: { emoji: '🙂', label: 'Positive', color: 'bg-green-400' },
  very_positive: { emoji: '😊', label: 'Very Positive', color: 'bg-green-600' },
});
```

## Checklist for Adding to Your Code

- [ ] Identify the union type or enum you're handling
- [ ] Choose the right utility (assertNever, buildExhaustive, match)
- [ ] Add import: `import { assertNever, buildExhaustive } from '@/lib/exhaustive'`
- [ ] Wrap your code with the utility
- [ ] Verify TypeScript compilation: `npx tsc --noEmit`
- [ ] Add comment explaining what's exhaustively checked
- [ ] Test the component/function works correctly

## Common Mistakes to Avoid

❌ **Don't:**
```typescript
// Missing case, no error checking
switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Result />;
}
```

✓ **Do:**
```typescript
// All cases covered with exhaustiveness guarantee
switch (status) {
  case 'loading': return <Spinner />;
  case 'success': return <Result />;
  case 'error': return <Error />;
  default: return assertNever(status);
}
```

❌ **Don't:**
```typescript
// Missing some enum values
const config = {
  loading: { ... },
  success: { ... },
  // Forgot 'error'!
};
```

✓ **Do:**
```typescript
// All values required
const config = buildExhaustive<Status, ConfigType>({
  loading: { ... },
  success: { ... },
  error: { ... },
  // TypeScript error if any value is missing
});
```

## Performance

- **Runtime cost:** Zero
- **Bundle size impact:** None (compiles away)
- **Type checking:** Compile time only
- **Usage:** Free to use everywhere

## Related Docs

- **Full Guide:** `/lib/EXHAUSTIVE_CHECKING.md`
- **Examples:** `/lib/exhaustive.examples.ts`
- **Summary:** `/EXHAUSTIVE_CHECKING_SUMMARY.md`
- **Implementation:** `/lib/exhaustive.ts`

## Questions?

Refer to `/lib/EXHAUSTIVE_CHECKING.md` for detailed explanations and examples.
