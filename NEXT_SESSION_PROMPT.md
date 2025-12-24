# Prompt for Next Implementation Session

Copy and paste this into your next Claude Code session:

---

I want to implement the plan in `IMPLEMENTATION_PLAN_SESSION_1_VERTICAL.md`

Please read the plan file completely, then execute it phase by phase:

**Phase 1:** Create demo token storage utility
**Phase 2:** Add API client methods for demo initialization
**Phase 3:** Implement hybrid data hook (Session 1 real + 2-10 mock)
**Phase 4:** Test and validate

After completing each phase, run ALL success criteria checks (automated + manual) before moving to the next phase.

Ask me for confirmation before proceeding between phases.

**Important:**
- Follow the git workflow specified in the plan
- ALL commits must be backdated to December 23, 2025, starting at 21:00:00
- Use format: `git commit -m "message" && git commit --amend --date="2025-12-23 21:00:00"`
- Increment time by 1 minute for each commit (21:00, 21:01, 21:02, etc.)

---

## Quick Context

**Goal:** Display real summary for Session 1 from database, keep Sessions 2-10 as mock data

**Files to create:**
- `frontend/lib/demo-token-storage.ts`

**Files to modify:**
- `frontend/lib/api-client.ts`
- `frontend/app/patient/lib/usePatientSessions.ts`

**Expected result:**
Session 1 card shows: "Crisis intake for recent breakup with passive SI, safety plan created"
