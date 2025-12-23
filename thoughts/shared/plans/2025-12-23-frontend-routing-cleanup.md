# Frontend Routing Cleanup - Patient-Only Simplified Structure

## Overview

Restructure the frontend to be patient-only with clean, simple routing and no authentication. Transform from a multi-role app with complex nested routes to a streamlined single-purpose dashboard.

## Current State Analysis

**Current routing structure:**
- `/` - Landing page with auto-redirect logic and auth detection (app/page.tsx)
- `/patient` - Dashboard v3 main page (app/patient/page.tsx)
- `/patient/dashboard-v3/sessions` - Sessions page with confusing nested path
- `/patient/upload` - Upload page
- `/auth/login`, `/auth/signup`, `/auth/verify` - Full authentication system
- `/therapist/*` - Complete therapist portal (unused)

**Key discoveries:**
- NavigationBar currently routes to `/patient/dashboard-v3/sessions` (line 70)
- Root page has complex auth detection logic (lines 25-75)
- "Ask AI" button triggers overlay via `onAskAIClick` prop (line 73-77)
- Multiple providers wrap patient pages: ThemeProvider, ProcessingProvider, SessionDataProvider
- FullscreenChat component exists at `app/patient/components/FullscreenChat/index.tsx`

## Desired End State

**New routing structure:**
- `/` - Redirects to `/dashboard`
- `/dashboard` - Main dashboard with 5 cards (Notes/Goals, AI Chat, To-Do, Progress, Therapist Bridge)
- `/sessions` - Session cards grid + timeline
- `/upload` - Audio upload page
- `/ask-ai` - Dedicated chat page (converted from overlay)

**Navigation bar tabs:**
- Dashboard → `/dashboard`
- Sessions → `/sessions`
- Upload → `/upload`
- Ask AI → `/ask-ai`

**Verification:**
1. Visit `localhost:3000` → auto-redirects to `localhost:3000/dashboard`
2. All navigation tabs route to correct pages
3. No auth flows, no therapist routes
4. Build succeeds: `npm run build`
5. No TypeScript errors: `npm run build`

### Key Discoveries:
- Landing page at `app/page.tsx:1-235` contains marketing content and auth logic (delete entirely)
- NavigationBar at `components/NavigationBar.tsx:54-171` has centralized routing logic
- Patient components are scattered in `app/patient/` directory
- Auth routes exist at `app/auth/login`, `app/auth/signup`, `app/auth/verify`
- Therapist routes exist at `app/therapist/` with 4 files

## What We're NOT Doing

- NOT migrating to a different framework
- NOT changing component logic or styling
- NOT modifying backend API integration
- NOT removing mock data functionality
- NOT changing theme system or providers
- NOT modifying database or authentication on backend (only removing frontend auth UI)

## Implementation Approach

Work from outside-in: Remove auth and therapist routes first, then restructure patient routes to root level, then update navigation and root redirect. This minimizes broken imports during transition.

---

## Phase 1: Remove Authentication System

### Overview
Delete all authentication routes, components, and logic from the frontend. This clears the way for direct access to the dashboard.

### Changes Required:

#### 1.1 Delete Auth Routes

**Files to delete:**
- `app/auth/login/page.tsx`
- `app/auth/signup/page.tsx`
- `app/auth/verify/page.tsx`
- `app/auth/` directory (entire folder)

**Command:**
```bash
rm -rf app/auth/
```

#### 1.2 Remove Auth Dependencies from Root Page

**File**: `app/page.tsx`
**Changes**: Will be replaced entirely in Phase 5, but remove auth imports now

Remove these imports (lines 16-17):
```typescript
import { supabase } from '@/lib/supabase';
import { hasExistingAccount } from '@/lib/first-time-detection';
```

#### 1.3 Clean Up Auth Utilities (Optional)

**Files to review** (may be used by backend integration):
- `lib/supabase.ts` - Keep if used for data fetching
- `lib/first-time-detection.ts` - Delete (auth-only)
- `lib/auth-context.tsx` - Delete if exists

**Command** (only if these files exist and are auth-only):
```bash
rm -f lib/first-time-detection.ts lib/auth-context.tsx
```

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] No TypeScript errors related to deleted auth files
- [x] No dangling imports to deleted auth routes

#### Manual Verification:
- [ ] Visiting `/auth/login` shows 404
- [ ] Visiting `/auth/signup` shows 404
- [ ] No console errors on page load

**Implementation Note**: After completing this phase and all automated verification passes, confirm that no auth-related code remains before proceeding to Phase 2.

---

## Phase 2: Remove Therapist Routes

### Overview
Delete the entire therapist portal since this is now a patient-only application.

### Changes Required:

#### 2.1 Delete Therapist Directory

**Files to delete:**
- `app/therapist/layout.tsx`
- `app/therapist/page.tsx`
- `app/therapist/patients/[id]/page.tsx`
- `app/therapist/sessions/[id]/page.tsx`
- `app/therapist/` directory (entire folder)

**Command:**
```bash
rm -rf app/therapist/
```

#### 2.2 Check for Therapist-Related Components

**Search for therapist references:**
```bash
grep -r "therapist" app/patient/components/ --include="*.tsx" --include="*.ts"
```

If any components reference therapist logic, review and remove those sections.

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] No TypeScript errors related to therapist routes
- [x] No imports referencing deleted therapist files

#### Manual Verification:
- [ ] Visiting `/therapist` shows 404
- [ ] No therapist-related UI elements visible in patient dashboard

**Implementation Note**: After this phase, the app should be patient-only with no therapist code remaining.

---

## Phase 3: Create New Route Structure

### Overview
Create the new clean route structure at root level: `/dashboard`, `/sessions`, `/upload`, `/ask-ai`.

### Changes Required:

#### 3.1 Create Dashboard Route

**File**: `app/dashboard/page.tsx`
**Changes**: Copy from `app/patient/page.tsx` with minimal modifications

```typescript
'use client';

/**
 * Main Dashboard - Patient view with 5 interactive cards
 * - Full dashboard layout with Notes/Goals, AI Chat, To-Do, Progress, Therapist Bridge
 * - Grid-based responsive layout
 * - Warm cream background with therapy-appropriate aesthetics
 * - Full dark mode support
 */

import { useState, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import '../patient/styles.css';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataProvider';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { NotesGoalsCard } from '@/app/patient/components/NotesGoalsCard';
import { AIChatCard } from '@/app/patient/components/AIChatCard';
import { ToDoCard } from '@/app/patient/components/ToDoCard';
import { ProgressPatternsCard } from '@/app/patient/components/ProgressPatternsCard';
import { TherapistBridgeCard } from '@/app/patient/components/TherapistBridgeCard';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';

export default function DashboardPage() {
  const router = useRouter();
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);
  const [showDemoButton, setShowDemoButton] = useState(true);

  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <ProcessingRefreshBridge />
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300 relative">
              <NavigationBar />

              <main className="w-full max-w-[1400px] mx-auto px-12 py-12">
                {/* Top Row - 50/50 Split */}
                <div className="grid grid-cols-2 gap-6 mb-10">
                  <NotesGoalsCard />
                  <AIChatCard
                    isFullscreen={isChatFullscreen}
                    onFullscreenChange={setIsChatFullscreen}
                  />
                </div>

                {/* Middle Row - 3 Equal Cards */}
                <div className="grid grid-cols-3 gap-6 mb-10">
                  <ToDoCard />
                  <ProgressPatternsCard />
                  <TherapistBridgeCard />
                </div>
              </main>
            </div>
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
```

#### 3.2 Create Sessions Route

**File**: `app/sessions/page.tsx`
**Changes**: Copy from `app/patient/dashboard-v3/sessions/page.tsx`

```typescript
'use client';

/**
 * Sessions Page - Dedicated view for session history
 * - Shows session cards grid + timeline
 * - Same cream/dark purple background as dashboard
 */

import { Suspense } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { SessionCardsGrid } from '@/app/patient/dashboard-v3/components/SessionCardsGrid';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function SessionsPage() {
  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <ProcessingRefreshBridge />
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              <NavigationBar />
              <main className="px-12 py-12">
                <SessionCardsGrid />
              </main>
            </div>
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
```

#### 3.3 Create Upload Route

**File**: `app/upload/page.tsx`
**Changes**: Copy from `app/patient/upload/page.tsx`

```typescript
'use client';

/**
 * Upload Page - Audio file upload interface
 */

import { Suspense } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { UploadPageContent } from '@/app/patient/upload/UploadPageContent';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function UploadPage() {
  return (
    <ThemeProvider>
      <ProcessingProvider>
        <Suspense fallback={<DashboardSkeleton />}>
          <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
            <NavigationBar />
            <UploadPageContent />
          </div>
        </Suspense>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
```

**Note**: If `UploadPageContent` doesn't exist as a separate component, extract the content from the current upload page.

#### 3.4 Create Ask AI Route

**File**: `app/ask-ai/page.tsx`
**Changes**: New page using FullscreenChat as main content (not overlay)

```typescript
'use client';

/**
 * Ask AI Page - Dedicated chat interface with Dobby
 * - Full page chat experience (not overlay)
 * - Same providers as other pages
 */

import { Suspense, useState } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { FullscreenChat, ChatMessage, ChatMode } from '@/app/patient/components/FullscreenChat';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function AskAIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              <NavigationBar />

              {/* Chat as main content (always open, not overlay) */}
              <FullscreenChat
                isOpen={true}
                onClose={() => {}} // No-op since it's a dedicated page
                messages={messages}
                setMessages={setMessages}
                mode={mode}
                setMode={setMode}
                conversationId={conversationId}
                setConversationId={setConversationId}
              />
            </div>
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
```

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] All 4 new routes compile without errors
- [x] No missing import errors

#### Manual Verification:
- [ ] `/dashboard` loads and shows 5 cards
- [ ] `/sessions` loads and shows session grid
- [ ] `/upload` loads upload interface
- [ ] `/ask-ai` loads chat interface (always visible, not overlay)

**Implementation Note**: After this phase, new routes exist but NavigationBar still points to old paths. We'll fix that in Phase 4.

---

## Phase 4: Update NavigationBar

### Overview
Update NavigationBar to route to new simplified paths and change "Ask AI" from overlay trigger to page navigation.

### Changes Required:

#### 4.1 Update NavigationBar Routes

**File**: `components/NavigationBar.tsx`
**Changes**: Update all route handlers and active page detection

Replace navigation handlers (lines 65-81):

```typescript
// Navigation handlers - CENTRALIZED ROUTING
const handleDashboardClick = () => {
  router.push('/dashboard');
};

const handleSessionsClick = () => {
  router.push('/sessions');
};

const handleAskAIClick = () => {
  router.push('/ask-ai');
};

const handleUploadClick = () => {
  router.push('/upload');
};
```

Update active page detection (lines 59-62):

```typescript
// Determine active page
const isSessionsPage = pathname === '/sessions';
const isDashboardPage = pathname === '/dashboard';
const isUploadPage = pathname === '/upload';
const isAskAIPage = pathname === '/ask-ai';
```

Update "Ask AI" button (lines 157-162):

```typescript
<button
  onClick={handleAskAIClick}
  className={`text-sm font-medium transition-all pb-1 border-b-2 ${
    isAskAIPage
      ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
      : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
  }`}
  style={isAskAIPage ? {
    filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
  } : {}}
>
  Ask AI
</button>
```

#### 4.2 Remove onAskAIClick Prop

**File**: `components/NavigationBar.tsx`
**Changes**: Remove the prop interface (lines 50-52)

Remove:
```typescript
interface NavigationBarProps {
  onAskAIClick?: () => void;
}
```

Change to:
```typescript
export function NavigationBar() {
  // No props needed anymore
```

Update function signature (line 54):
```typescript
export function NavigationBar() {
```

#### 4.3 Update All NavigationBar Usages

**Files to update:**
- `app/dashboard/page.tsx` - Remove `onAskAIClick` prop
- `app/sessions/page.tsx` - Remove `onAskAIClick` prop
- `app/upload/page.tsx` - Remove `onAskAIClick` prop
- `app/ask-ai/page.tsx` - Remove `onAskAIClick` prop

Change from:
```typescript
<NavigationBar onAskAIClick={() => setIsChatFullscreen(true)} />
```

To:
```typescript
<NavigationBar />
```

Also remove related state variables like `isChatFullscreen` from dashboard and sessions pages.

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] No TypeScript errors about missing/unused props
- [x] All navigation buttons compile correctly

#### Manual Verification:
- [ ] Clicking "Dashboard" navigates to `/dashboard`
- [ ] Clicking "Sessions" navigates to `/sessions`
- [ ] Clicking "Upload" navigates to `/upload`
- [ ] Clicking "Ask AI" navigates to `/ask-ai` (not overlay)
- [ ] Active tab highlighting works on all pages

**Implementation Note**: After this phase, navigation should work correctly across all new routes.

---

## Phase 5: Update Root Page Redirect

### Overview
Replace the complex landing page with a simple redirect to `/dashboard`.

### Changes Required:

#### 5.1 Replace Root Page

**File**: `app/page.tsx`
**Changes**: Replace entire file with redirect logic

```typescript
'use client';

/**
 * Root Route - Redirects to Dashboard
 * No auth, no landing page, just redirect to /dashboard
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  // Show minimal loading state during redirect
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-secondary">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mx-auto animate-pulse">
          <svg className="w-10 h-10 text-primary-foreground" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <p className="text-muted-foreground">Loading TheraBridge...</p>
      </div>
    </div>
  );
}
```

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] No unused imports or dead code warnings

#### Manual Verification:
- [ ] Visiting `localhost:3000` redirects to `localhost:3000/dashboard`
- [ ] Redirect happens instantly (no visible landing page)
- [ ] Dashboard loads correctly after redirect

**Implementation Note**: After this phase, the root route should cleanly redirect to dashboard.

---

## Phase 6: Clean Up Old Patient Directory Structure

### Overview
Remove the old `/patient` directory structure now that everything has been moved to root-level routes.

### Changes Required:

#### 6.1 Verify All Components Are Still Accessible

Before deleting, ensure all imports in new routes point to correct locations:

**Search for imports from old structure:**
```bash
grep -r "from '@/app/patient/" app/dashboard/ app/sessions/ app/upload/ app/ask-ai/
```

Make sure all imports still resolve correctly.

#### 6.2 Delete Old Route Files

**Files to delete** (components will stay, only routes):
- `app/patient/page.tsx` - Replaced by `/dashboard`
- `app/patient/dashboard-v3/sessions/page.tsx` - Replaced by `/sessions`
- `app/patient/upload/page.tsx` - Replaced by `/upload`

**Do NOT delete yet:**
- `app/patient/components/` - Still referenced by new routes
- `app/patient/contexts/` - Still referenced by new routes
- `app/patient/lib/` - Still referenced by new routes
- `app/patient/hooks/` - Still referenced by new routes
- `app/patient/dashboard-v3/components/` - Still referenced by `/sessions`

#### 6.3 Clean Up Empty Directories

After deleting route files:

```bash
# Remove empty dashboard-v3 directory if only sessions/ was in it
rmdir app/patient/dashboard-v3/sessions/
rmdir app/patient/dashboard-v3/

# Check if patient directory structure can be cleaned up
ls -la app/patient/
```

### Success Criteria:

#### Automated Verification:
- [x] Build succeeds: `npm run build`
- [x] No broken imports
- [x] All components still accessible

#### Manual Verification:
- [ ] All 4 routes still work (`/dashboard`, `/sessions`, `/upload`, `/ask-ai`)
- [ ] No duplicate route warnings in console
- [ ] Old patient routes return 404 (`/patient`, `/patient/upload`, etc.)

**Implementation Note**: Keep patient components/contexts/lib/hooks for now since they're still used. Consider reorganizing in a future refactor.

---

## Phase 7: Final Cleanup and Verification

### Overview
Remove development bypass flags, clean up unused code, and verify the entire application works.

### Changes Required:

#### 7.1 Remove Dev Bypass References

**Search for dev bypass usage:**
```bash
grep -r "NEXT_PUBLIC_DEV_BYPASS_AUTH" app/
```

**File**: `app/dashboard/page.tsx`
**Changes**: Remove demo button section if it references auth bypass

Remove the demo button section (lines 71-147 in old patient/page.tsx) since auth is gone.

#### 7.2 Update Environment Variables

**File**: `.env.local`
**Changes**: Remove auth-related environment variables

Remove:
- `NEXT_PUBLIC_DEV_BYPASS_AUTH` (no longer needed)
- Any Supabase auth-related variables (unless used for data fetching)

#### 7.3 Check for Unused Dependencies

**File**: `package.json`
**Review**: Check if these can be removed
- `@supabase/auth-helpers-nextjs` - Remove if only used for auth
- `@supabase/supabase-js` - Keep if used for data fetching

Run:
```bash
npm uninstall @supabase/auth-helpers-nextjs
```

Only if auth helpers are not used for data fetching.

#### 7.4 Final Build Verification

Run full build and check for warnings:
```bash
npm run build
```

Check for:
- Unused imports
- Dead code elimination
- Bundle size (should be smaller without auth code)

### Success Criteria:

#### Automated Verification:
- [x] Clean build: `npm run build` with no errors
- [x] No unused imports warnings
- [x] TypeScript compilation successful: `npm run build`
- [ ] ESLint passes: `npm run lint` (or skip if too many pre-existing errors)

#### Manual Verification:
- [ ] Root `/` redirects to `/dashboard` ✓
- [ ] `/dashboard` shows 5 dashboard cards ✓
- [ ] `/sessions` shows session grid + timeline ✓
- [ ] `/upload` shows upload interface ✓
- [ ] `/ask-ai` shows chat interface (not overlay) ✓
- [ ] NavigationBar tabs work on all pages ✓
- [ ] Theme toggle works across all pages ✓
- [ ] No 404 errors in browser console ✓
- [ ] No auth-related errors or redirects ✓

**Implementation Note**: After this phase, the frontend should be fully restructured as a patient-only app with clean routing.

---

## Testing Strategy

### Unit Tests:
- No unit tests required (this is a routing/structure refactor)
- Existing component tests should still pass if they exist

### Integration Tests:
- If Playwright tests exist, update them to use new routes:
  - Change `/patient` → `/dashboard`
  - Change `/patient/dashboard-v3/sessions` → `/sessions`
  - Change `/patient/upload` → `/upload`
  - Add tests for `/ask-ai` navigation

### Manual Testing Steps:

1. **Root redirect test:**
   - Visit `localhost:3000`
   - Verify auto-redirect to `/dashboard`
   - Confirm dashboard cards load

2. **Navigation test:**
   - Click each tab in NavigationBar
   - Verify correct page loads
   - Verify active tab highlighting

3. **Direct URL test:**
   - Type each URL directly in browser
   - Verify pages load without redirect
   - Check for console errors

4. **Theme persistence test:**
   - Toggle dark mode on `/dashboard`
   - Navigate to `/sessions`
   - Verify theme persists

5. **404 test:**
   - Visit old routes: `/patient`, `/auth/login`, `/therapist`
   - Verify all show 404

## Performance Considerations

- Bundle size should decrease with removed auth code (~50KB savings expected)
- Fewer route segments means faster navigation
- Simpler routing means faster initial page load
- No auth checks means no async delays on root route

## Migration Notes

**If users have bookmarks to old routes:**
- `/patient` → will 404 (could add redirect in middleware if needed)
- `/patient/upload` → will 404 (could add redirect)
- `/patient/dashboard-v3/sessions` → will 404 (could add redirect)

**Optional: Add middleware redirects** (create `middleware.ts` in root):
```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Redirect old routes to new structure
  if (pathname === '/patient') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  if (pathname === '/patient/upload') {
    return NextResponse.redirect(new URL('/upload', request.url));
  }
  if (pathname.startsWith('/patient/dashboard-v3/sessions')) {
    return NextResponse.redirect(new URL('/sessions', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/patient/:path*'],
};
```

## References

- Current NavigationBar: `components/NavigationBar.tsx:54-171`
- Current root page: `app/page.tsx:1-235`
- Current dashboard: `app/patient/page.tsx:29-154`
- Current sessions page: `app/patient/dashboard-v3/sessions/page.tsx:22-69`
- FullscreenChat component: `app/patient/components/FullscreenChat/index.tsx`
