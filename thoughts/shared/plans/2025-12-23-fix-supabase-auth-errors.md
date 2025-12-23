# Fix Supabase Authentication Errors Implementation Plan

## Overview

The frontend is experiencing "Failed to fetch" errors from Supabase Auth when running in development mode with `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`. The Supabase client is trying to refresh non-existent sessions, causing console spam and potential performance issues.

## Current State Analysis

### What exists now:
- Supabase client is always initialized in `lib/supabase.ts` (lines 16-19)
- `AuthContext.tsx` creates mock users when dev bypass is enabled (lines 57-116)
- Supabase client still attempts session refresh even in bypass mode
- Middleware bypasses auth checks correctly (lines 14-17)

### Key Discoveries:
- **Problem**: Supabase client initialization is unconditional - it always tries to connect
- **Root cause**: When `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`, the app uses mock users but Supabase client still attempts to refresh auth tokens from a non-existent session
- **Impact**: Console spam, unnecessary network requests, potential performance degradation
- **Pattern to follow**: Next.js environment variable access pattern (process.env.NEXT_PUBLIC_*)

## Desired End State

### Success Criteria:

#### Automated Verification:
- [ ] No console errors when running dev server: `npm run dev`
- [ ] Build completes without errors: `npm run build`
- [ ] Type checking passes: `npm run type-check` (if available)
- [ ] Linting passes: `npm run lint` (if available)

#### Manual Verification:
- [ ] No "Failed to fetch" errors in browser console when `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`
- [ ] Mock user authentication works correctly in bypass mode
- [ ] Real Supabase authentication works when bypass is disabled
- [ ] Session refresh attempts are suppressed in dev bypass mode
- [ ] Auth state changes are handled correctly in both modes

**Specification**: After implementation, the Supabase client should only initialize and attempt authentication when `NEXT_PUBLIC_DEV_BYPASS_AUTH` is not `true`. In bypass mode, the client should either be disabled or configured to prevent automatic session refresh attempts.

## What We're NOT Doing

- NOT modifying the backend authentication system
- NOT changing the overall auth flow or user experience
- NOT removing Supabase entirely (still needed for production)
- NOT changing environment variable names or configuration structure
- NOT modifying the mock user implementation
- NOT adding new dependencies or packages

## Implementation Approach

We'll implement a **conditional Supabase client initialization** strategy:
1. Add environment variable check to Supabase client creation
2. Configure auth client to skip auto-refresh in dev bypass mode
3. Update AuthContext to prevent subscription in bypass mode

This approach is minimal, surgical, and maintains backward compatibility.

---

## Phase 1: Conditional Supabase Client Configuration

### Overview
Modify the Supabase client initialization to respect the dev bypass flag and prevent automatic session refresh attempts.

### Changes Required:

#### 1.1 Update Supabase Client Configuration

**File**: `lib/supabase.ts`
**Changes**: Add conditional auto-refresh configuration based on dev bypass flag

```typescript
/**
 * Supabase client configuration
 * Handles authentication and database queries
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';

// Only validate at runtime, not during build
if (typeof window !== 'undefined' && (!supabaseUrl || !supabaseAnonKey)) {
  console.error('Missing Supabase environment variables');
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
  {
    auth: {
      // Disable auto-refresh in dev bypass mode to prevent "Failed to fetch" errors
      autoRefreshToken: !devBypass,
      persistSession: !devBypass,
      detectSessionInUrl: !devBypass,
    },
  }
);

// Rest of the file remains unchanged...
```

**Rationale**: By disabling `autoRefreshToken`, `persistSession`, and `detectSessionInUrl` when dev bypass is enabled, we prevent the Supabase client from making unnecessary auth requests.

### Success Criteria:

#### Automated Verification:
- [ ] No TypeScript errors after modification: `npm run type-check`
- [ ] Build succeeds: `npm run build`
- [ ] Dev server starts without errors: `npm run dev`

#### Manual Verification:
- [ ] Check browser console for "Failed to fetch" errors (should be gone)
- [ ] Verify mock user still works in dev bypass mode
- [ ] Check Network tab - no auth refresh requests when bypass is enabled
- [ ] Ensure Supabase client still works when bypass is disabled

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Optimize AuthContext Subscription Behavior

### Overview
Update the AuthContext to skip Supabase auth state subscription entirely when dev bypass is enabled, preventing the subscription from even being created.

### Changes Required:

#### 2.1 Conditional Auth State Subscription

**File**: `contexts/AuthContext.tsx`
**Changes**: Skip Supabase subscription setup when in dev bypass mode

```typescript
useEffect(() => {
  // Check if dev bypass is enabled
  const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';

  if (devBypass) {
    // Dev bypass mode - use mock user immediately, no Supabase interaction
    const mockUser: User = {
      id: 'dev-bypass-user-id',
      email: 'dev@therapybridge.local',
      first_name: 'Dev',
      last_name: 'User',
      role: 'patient',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setUser(mockUser);
    console.log('🔓 Using mock user (dev bypass mode)');
    setLoading(false);
    return; // Exit early - no subscription needed
  }

  // Production mode - use Supabase auth
  supabase.auth.getSession().then(({ data: { session } }) => {
    setSession(session);
    if (session?.user) {
      setUser(authUserToUser(session.user));
    }
    setLoading(false);
  });

  // Listen for auth changes (only in production mode)
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(async (_event, session) => {
    setSession(session);
    if (session?.user) {
      setUser(authUserToUser(session.user));
    } else {
      setUser(null);
    }
    setLoading(false);
  });

  return () => {
    subscription.unsubscribe();
  };
}, []);
```

**Rationale**: By returning early in dev bypass mode, we completely avoid creating the Supabase auth subscription, which prevents any auth-related network requests.

### Success Criteria:

#### Automated Verification:
- [ ] No TypeScript errors: `npm run type-check`
- [ ] Build succeeds: `npm run build`
- [ ] No runtime errors in dev mode: `npm run dev`

#### Manual Verification:
- [ ] Mock user appears immediately in dev bypass mode
- [ ] Console shows "🔓 Using mock user (dev bypass mode)" message
- [ ] Network tab shows zero auth requests in bypass mode
- [ ] Real auth flow still works when bypass is disabled
- [ ] Auth state changes propagate correctly in production mode

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Add Development Mode Logging (Optional)

### Overview
Add helpful console logging to make it clear when dev bypass is active and why auth errors aren't appearing.

### Changes Required:

#### 3.1 Enhanced Development Logging

**File**: `lib/supabase.ts`
**Changes**: Add informative console message when dev bypass is detected

```typescript
export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
  {
    auth: {
      autoRefreshToken: !devBypass,
      persistSession: !devBypass,
      detectSessionInUrl: !devBypass,
    },
  }
);

// Log dev bypass status (development only)
if (typeof window !== 'undefined' && devBypass) {
  console.log('🔓 Supabase client: Dev bypass mode - auth auto-refresh disabled');
}
```

**Rationale**: This makes it immediately obvious when the dev bypass is active and helps developers understand why Supabase auth is behaving differently.

### Success Criteria:

#### Automated Verification:
- [ ] Build succeeds: `npm run build`
- [ ] No console warnings or errors: `npm run dev`

#### Manual Verification:
- [ ] Console shows dev bypass message when `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`
- [ ] Console does NOT show message when bypass is disabled
- [ ] Message appears before any auth-related operations

**Implementation Note**: This phase is optional and can be skipped if verbose logging is not desired. After completing this phase and all automated verification passes, pause here for manual confirmation.

---

## Testing Strategy

### Unit Tests:
- Test Supabase client creation with dev bypass enabled
- Test Supabase client creation with dev bypass disabled
- Verify client options are set correctly based on environment variable

### Integration Tests:
- Full auth flow with dev bypass enabled (mock user)
- Full auth flow with dev bypass disabled (real Supabase)
- Auth state persistence across page reloads in both modes

### Manual Testing Steps:
1. **Dev Bypass Mode Testing**:
   - Set `NEXT_PUBLIC_DEV_BYPASS_AUTH=true` in `.env.local`
   - Run `npm run dev`
   - Open browser console
   - Verify no "Failed to fetch" errors appear
   - Verify mock user is created immediately
   - Check Network tab - should see zero auth refresh requests
   - Navigate between pages - verify mock user persists

2. **Production Mode Testing**:
   - Set `NEXT_PUBLIC_DEV_BYPASS_AUTH=false` in `.env.local`
   - Run `npm run dev`
   - Test signup flow with real credentials
   - Test login flow with real credentials
   - Test password reset flow
   - Verify auth state persists across page reloads
   - Test logout flow

3. **Edge Cases**:
   - Toggle between dev bypass enabled/disabled and verify clean transitions
   - Test with missing Supabase environment variables
   - Test with invalid Supabase credentials
   - Verify error messages are still shown for real auth failures

## Performance Considerations

### Before Implementation:
- ~5-10 failed network requests per minute in dev bypass mode
- Console spam affecting debuggability
- Unnecessary CPU cycles spent on failed auth attempts

### After Implementation:
- Zero auth-related network requests in dev bypass mode
- Clean console output
- Reduced CPU usage from avoided network requests
- Faster initial page load in dev bypass mode

## Migration Notes

### For Developers:
- No action required - changes are backwards compatible
- Existing `.env.local` files work without modification
- Dev bypass behavior remains the same (just cleaner)

### For Production:
- No changes needed to production environment variables
- Production builds are unaffected
- Auth flow remains identical

## References

- Supabase client configuration: https://supabase.com/docs/reference/javascript/initializing
- Supabase auth options: https://supabase.com/docs/reference/javascript/auth-api
- Next.js environment variables: https://nextjs.org/docs/basic-features/environment-variables
- Current AuthContext implementation: `contexts/AuthContext.tsx`
- Current Supabase config: `lib/supabase.ts`
- Dev bypass guide: `DEV_BYPASS_GUIDE.md`
