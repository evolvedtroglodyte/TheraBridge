# PR #2: Quick Start Guide

**For opening in a new Claude Code window**

---

## 📋 Copy This Prompt

```
I need to implement PR #2: Prose Analysis UI Toggle for the TheraBridge project.

Please read the execution prompt and implementation plan:

1. Read execution instructions:
   cat thoughts/shared/EXECUTION_PROMPT_PR2.md

2. Read detailed implementation plan:
   cat thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md

3. Execute the implementation following the 9-step process in the execution prompt.

Key requirements:
- Add tab toggle to SessionDetail (Narrative vs Structured views)
- localStorage persistence for view preference
- Theme-aware colors (teal → purple)
- Framer Motion transitions
- Accessibility (ARIA labels, keyboard nav)
- Default to Narrative view

Files to modify:
- frontend/app/patient/components/SessionDetail.tsx (primary)

Success criteria:
- 17-item testing checklist complete
- Zero TypeScript errors
- Production verification on Railway
- Documentation updated (SESSION_LOG, TheraBridge, CLAUDE)
- Git commit with backdated timestamp

Start with Step 1: Read the full implementation plan.
```

---

## 📁 Key Files

1. **Execution Prompt:** `thoughts/shared/EXECUTION_PROMPT_PR2.md`
2. **Implementation Plan:** `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
3. **Target File:** `frontend/app/patient/components/SessionDetail.tsx`

---

## ⏱️ Timeline

- **Implementation:** 1 hour
- **Testing:** 30-60 min
- **Documentation:** 15 min
- **Total:** ~2 hours

---

## ✅ Checklist

- [ ] Read execution prompt
- [ ] Read implementation plan
- [ ] Verify current state (Step 2)
- [ ] Implement Phase 1 (TabToggle + ProseAnalysisView)
- [ ] Implement Phase 2 (Integration)
- [ ] Build & test (17-item checklist)
- [ ] Regression testing
- [ ] Git commit (backdated)
- [ ] Update documentation (3 files)
- [ ] Production verification

---

**Good luck! 🚀**
