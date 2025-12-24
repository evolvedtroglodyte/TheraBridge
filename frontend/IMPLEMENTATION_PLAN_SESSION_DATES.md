# Implementation Plan: Session Date Ordering & Formatting

## Problem Statement
Session 1 from the database is currently displaying at the **newest** position (index 0), but it should display at the **oldest** position (index 9) since it occurred on January 10, 2025. The sessions need to be sorted in **descending order** (newest first) with proper date formatting.

## Session Date Mapping (from mock-therapy-data)
```
Session 1:  January 10, 2025  (2025-01-10)  ← OLDEST
Session 2:  January 17, 2025  (2025-01-17)
Session 3:  January 31, 2025  (2025-01-31)
Session 4:  February 14, 2025 (2025-02-14)
Session 5:  February 28, 2025 (2025-02-28)
Session 6:  March 14, 2025    (2025-03-14)
Session 7:  April 4, 2025     (2025-04-04)
Session 8:  April 18, 2025    (2025-04-18)
Session 9:  May 2, 2025       (2025-05-02)
Session 10: May 9, 2025       (2025-05-09)   ← NEWEST (currently in database)
```

## Current Issues
1. ✅ Mock sessions (2-10) are already in descending order in `mockData.ts`
2. ❌ Session 1 is being inserted at index 0 (newest position): `[session1Data, ...mockSessions.slice(1)]`
3. ❌ Session 1 should be inserted at index 9 (oldest position)
4. ❌ Date format inconsistency: backend returns ISO timestamp, frontend displays string
5. ❌ No sorting logic based on actual dates

## Implementation Plan

### Phase 1: Update Session Type Definition
**File:** `frontend/app/patient/lib/types.ts`

**Changes:**
- Add `rawDate?: Date` field to Session interface for sorting
- Keep `date: string` for display purposes
- This allows sorting by Date while displaying formatted strings

**Example:**
```typescript
export interface Session {
  id: string;
  date: string;           // Display format: "Jan 10" or "May 9"
  rawDate?: Date;         // For sorting
  duration: string;
  mood: MoodType;
  // ... rest of fields
}
```

**Success Criteria:**
- TypeScript compilation passes
- No ESLint errors
- Session type includes both `date` (string) and `rawDate` (Date)

---

### Phase 2: Update Mock Data with Raw Dates
**File:** `frontend/app/patient/lib/mockData.ts`

**Changes:**
- Add `rawDate: new Date('2025-MM-DD')` to each mock session
- Keep existing `date` strings for display
- Use session date mapping from above

**Example:**
```typescript
{
  id: 'session_10',
  date: 'May 9',
  rawDate: new Date('2025-05-09'),
  duration: '60 min',
  // ... rest
},
{
  id: 'session_09',
  date: 'May 2',
  rawDate: new Date('2025-05-02'),
  // ... rest
}
```

**Success Criteria:**
- All 10 mock sessions have `rawDate` field
- Dates match the session date mapping above
- Mock sessions remain in descending order (Session 10 first, Session 2 last)

---

### Phase 3: Update Backend SQL Function
**File:** Create new Supabase SQL migration

**Changes:**
- Update `seed_demo_v2()` function to use fixed session dates
- Session 1 should use `'2025-01-10'::date` instead of random date
- Ensures consistency between mock and database data

**SQL Example:**
```sql
CREATE OR REPLACE FUNCTION seed_demo_v3(p_demo_token TEXT)
RETURNS TABLE (
  patient_id UUID,
  session_ids UUID[]
) AS $$
DECLARE
  -- ... existing declarations
BEGIN
  -- ... existing user/patient creation

  -- Create Session 1 with FIXED DATE
  INSERT INTO therapy_sessions (
    id, patient_id, therapist_id, session_date,
    duration_minutes, status, created_at, updated_at
  ) VALUES (
    gen_random_uuid(),
    v_patient_id,
    v_therapist_id,
    '2025-01-10'::date,  -- FIXED DATE for Session 1
    60,
    'completed',
    NOW(),
    NOW()
  ) RETURNING id INTO v_session_id;

  -- ... rest of function
END;
$$ LANGUAGE plpgsql;
```

**Success Criteria:**
- SQL function creates Session 1 with date `2025-01-10`
- Function test returns session with correct date
- No SQL errors

---

### Phase 4: Update usePatientSessions Hook
**File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Changes:**
1. Transform backend `session_date` to both display string AND Date object
2. Insert Session 1 at correct position based on date sorting
3. Sort final array by `rawDate` in descending order

**Implementation:**
```typescript
// Transform backend session to frontend Session type
const backendSession = sessionResult.data;
const sessionDate = new Date(backendSession.session_date);

session1Data = {
  id: backendSession.id,
  date: sessionDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  }), // "Jan 10"
  rawDate: sessionDate, // Date object for sorting
  duration: `${backendSession.duration_minutes || 60} min`,
  therapist: 'Dr. Rodriguez',
  mood: 'neutral' as const,
  topics: backendSession.topics || [],
  strategy: backendSession.technique || 'Not yet analyzed',
  actions: backendSession.action_items || [],
  summary: backendSession.summary || 'Summary not yet generated.',
  transcript: backendSession.transcript || [],
  extraction_confidence: backendSession.extraction_confidence,
  topics_extracted_at: backendSession.topics_extracted_at,
};

// Merge Session 1 + mock sessions, then sort by date
const allSessions = [session1Data, ...mockSessions.slice(1)];
const sortedSessions = allSessions.sort((a, b) => {
  if (!a.rawDate || !b.rawDate) return 0;
  return b.rawDate.getTime() - a.rawDate.getTime(); // Descending order
});

setSessions(sortedSessions);
```

**Success Criteria:**
- Session 1 appears at index 9 (oldest position)
- Sessions are sorted newest to oldest
- Date displays as "Jan 10" on session cards
- Console log confirms: "Session 1 (Jan 10) at position 9"

---

### Phase 5: Update Session Detail Modal (Full Date Format)
**File:** `frontend/app/patient/components/SessionModal.tsx` (or similar)

**Changes:**
- Display full date format on session detail: "January 10, 2025"
- Use `rawDate` to generate full format

**Implementation:**
```typescript
const fullDate = session.rawDate?.toLocaleDateString('en-US', {
  month: 'long',
  day: 'numeric',
  year: 'numeric'
}); // "January 10, 2025"
```

**Success Criteria:**
- Session cards show short format: "Jan 10"
- Session detail modal shows full format: "January 10, 2025"
- Both formats are generated from the same `rawDate` field

---

## Git Workflow
All commits must be backdated to **December 23, 2025**, starting at **21:02:00** and incrementing by 1 minute per commit.

**Commit structure:**
1. 21:02 - Phase 1: Update Session type definition
2. 21:03 - Phase 2: Update mock data with raw dates
3. 21:04 - Phase 3: Update backend SQL function
4. 21:05 - Phase 4: Update usePatientSessions hook + sorting logic
5. 21:06 - Phase 5: Update session detail modal (full date format)

**Commit message format:**
```
Phase X: [Description]

- Change 1
- Change 2
- Change 3

Success criteria met:
✓ Criterion 1
✓ Criterion 2
```

---

## Testing Checklist
After all phases complete:

### Frontend Tests:
- [ ] Session 1 displays at position 9 (last card)
- [ ] Session 10 displays at position 0 (first card)
- [ ] Sessions are in descending order by date
- [ ] Session cards show short date format: "Jan 10", "May 9"
- [ ] Session detail shows full date format: "January 10, 2025"
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] `npm run build` passes

### Backend Tests:
- [ ] SQL function creates Session 1 with date `2025-01-10`
- [ ] API returns correct session_date in ISO format
- [ ] Demo initialization succeeds

### Console Output:
```
[Demo] ✓ Initialized: { patient_id: "...", sessionCount: 1 }
[Session1] Fetching from API: ...
[Session1] ✓ Loaded date: 2025-01-10
[Session1] ✓ Position: 9 (oldest)
[Sessions] ✓ Sorted: Session 10 (May 9) → Session 1 (Jan 10)
```

---

## Rollback Plan
If issues occur:
1. Revert git commits in reverse order (Phase 5 → Phase 1)
2. SQL: Drop `seed_demo_v3`, restore `seed_demo_v2`
3. Frontend: Remove `rawDate` field, restore original sorting

---

## Notes
- Session dates are **fixed** (from mock-therapy-data folder)
- Session 1 is always January 10, 2025
- Sessions span January through May 2025
- Sorting happens in `usePatientSessions` hook (not in individual components)
- Date format uses native `toLocaleDateString()` (no external libraries)
