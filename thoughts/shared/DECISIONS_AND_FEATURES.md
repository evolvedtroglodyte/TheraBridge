# Decisions & Features Log

This document tracks UI/UX decisions and feature implementations that may need design iteration or refinement later.

---

## Session Bridge - Manual Refresh Button

**Date:** 2026-01-14
**Status:** Placeholder Implementation (awaiting design review)
**PR:** #4 (Session Bridge Backend Integration)

### Current Implementation
- **Position:** Top-right corner of SessionBridgeCard (`absolute top-6 right-6`)
- **Icon:** `RotateCw` from lucide-react (single rotation arrow)
- **Size:** 44px × 44px (`w-11 h-11`)
- **Styling:** Circular button with hover state (matches close button pattern)
- **Behavior:** Triggers manual refresh via separate function (bypasses SSE debounce)
- **Config:** Hidden when `NEXT_PUBLIC_ENABLE_MANUAL_REFRESH=false`

### Potential Future Changes
- [ ] **Move to header:** Consider moving refresh button to card header (next to "Session Bridge" title) for better discoverability
- [ ] **Icon change:** May need different icon based on design review
- [ ] **Animation:** Add rotation animation on click
- [ ] **Tooltip:** Add hover tooltip explaining "Manually refresh session preparation"
- [ ] **Positioning:** May conflict with other buttons if more are added

### Design Questions to Address
- Should button be visible in all states (empty, loading, error)?
- Should it pulse or animate to draw attention?
- Should there be a cooldown period between manual refreshes?

---

## Session Bridge - Task Integration (Skeleton)

**Date:** 2026-01-14
**Status:** Skeleton Implementation (complete in PR #5 - To-Do Card)
**PR:** #4 (Session Bridge Backend Integration)

### Current Implementation
- **Database Query:** Skeleton code added in `generate_session_bridge.py` (commented out)
- **LLM Prompt:** Placeholder section for completed tasks (commented out)
- **Service Method:** `completed_tasks` parameter accepted but defaults to `None`

### Integration Plan (PR #5)
- Query `patient_tasks` table for completed tasks
- Filter: `completed=true` (removed `completed_at > last_session_date` requirement)
- Pass tasks to SessionBridgeGenerator
- LLM uses tasks as PRIMARY evidence for `shareProgress` section
- Fallback to AI suggestions when no tasks completed

### Technical Notes
- Tasks may be completed same day as session (not necessarily different day)
- Task completion timestamp NOT required to be after previous session
- Integration will be bidirectional: To-Do Card ↔ Session Bridge

---

## Empty State Logic - Session Counter Requirement

**Date:** 2026-01-14
**Status:** Implementation Required
**PR:** #4 (Session Bridge Backend Integration)

### Requirement
Empty state should ONLY show when:
- **No sessions uploaded yet** (first few seconds of demo initialization)
- Database has 0 sessions for patient

Once sessions exist (even if not analyzed), show:
- Secondary message only ("Your session bridge will appear here after your first session is analyzed")
- Or loading state if analysis in progress

### Applies To
- [ ] SessionBridgeCard - verify empty state logic
- [ ] NotesGoalsCard - verify empty state logic (may need fix)

### Implementation Check
Verify that empty state checks `total_sessions === 0`, not just `bridgeData === null`

---

## Version History Retention Policy

**Date:** 2026-01-14
**Status:** Documented for future implementation
**Decision:** Document options, no implementation now (edge case won't be hit soon)

### Current Implementation
- Unlimited version history for all `*_versions` tables
- No automatic cleanup or retention policy
- All historical data preserved indefinitely

### Future Considerations
When version history becomes problematic (likely years away):

**Option A: Row Count Limit**
- Keep last N versions per patient (e.g., 100)
- Delete oldest versions when limit exceeded
- Implementation: Trigger or cron job

**Option B: Time-Based Retention**
- Keep versions for X months (e.g., 12 months)
- Archive or delete older versions
- Implementation: Scheduled cleanup job

**Option C: Soft Delete**
- Add `deleted_at` timestamp column
- Mark old versions as deleted instead of removing
- Allows recovery if needed
- Requires filtering `WHERE deleted_at IS NULL` in queries

---

## Data Deletion Strategy

**Date:** 2026-01-14
**Status:** Documented for future implementation
**Decision:** Use hard deletes for now (simpler, meets current needs)

### Current Implementation
- Hard deletes via `ON DELETE CASCADE` foreign key constraints
- No soft delete mechanism
- No audit trail for deleted records

### Future Soft Delete Pattern
```sql
ALTER TABLE therapy_sessions ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE patients ADD COLUMN deleted_at TIMESTAMPTZ;
```

**Pros:**
- Recoverable deletions
- Audit trail preserved
- Can restore accidentally deleted data

**Cons:**
- Requires filtering all queries (`WHERE deleted_at IS NULL`)
- Database bloat over time
- More complex query logic

---

## AI-Suggested ShareProgress Visual Indicator

**Date:** 2026-01-14
**Status:** To be implemented in PR #4
**Decision:** Add lightbulb icon to AI-suggested shareProgress items

### Implementation
- **Icon:** Lightbulb from lucide-react
- **Placement:** Next to shareProgress item text (small, subtle)
- **Purpose:** Distinguish AI suggestions from task-based evidence
- **Show when:** shareProgress item generated by AI (0-task or 1-2 task fallback scenarios)
- **Hide when:** shareProgress item derived from completed tasks (3-4+ tasks scenario)

### Technical Approach
- SessionBridgeGenerator returns metadata indicating which items are AI-suggested
- Frontend renders lightbulb icon conditionally based on metadata
- Tooltip on hover: "AI-suggested based on session insights"

---

## Future Decisions (TBD)

Add new decisions here as they arise during implementation...
