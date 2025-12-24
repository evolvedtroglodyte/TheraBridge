# Roadmap: TheraBridge

## Overview

TheraBridge's roadmap focuses on delivering a complete AI-powered therapy session analysis platform. Starting from the validated v1.0 MVP (audio transcription, Wave 1/2 analysis, patient dashboard), we're now enhancing the UI with PR #1 (font standardization, action summarization) and PR #2 (prose analysis toggle). Future phases will add therapist-facing features (analytics dashboard, multi-patient support, session upload) and authentication before moving to advanced features like chatbot integration and timeline visualization in v2.0.

## Domain Expertise

None - TheraBridge is a full-stack web application using established patterns (Next.js, FastAPI, PostgreSQL). No specialized domain skills required beyond standard web development.

## Milestones

- ✅ **v1.0 MVP** - Audio transcription + Wave 1/2 analysis + Patient dashboard (shipped Jan 2026)
- 🚧 **PR #1 Enhancements** - Font standardization + Action summarization + Enhanced SessionDetail (Phase 1 complete, Phase 2 planning)
- 📋 **v1.1 Therapist Features** - Analytics dashboard + Multi-patient + Session upload + Auth (Phases 3-6, planned)
- 📋 **v2.0 Advanced** - Chatbot + Timeline + Multi-language + Mobile (Phases 7-10, future)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>✅ v1.0 MVP - SHIPPED Jan 2026</summary>

### Phase 0: Foundation (Pre-GSD)
**Goal**: Core platform infrastructure and data pipeline
**Status**: Complete ✅

**Delivered:**
- Audio transcription pipeline (Whisper API + pyannote diarization)
- Wave 1 analysis (topic extraction, mood, action items, breakthrough detection)
- Wave 2 analysis (deep_analysis JSONB + prose_analysis TEXT)
- PostgreSQL schema (sessions, transcripts, analysis tables)
- FastAPI backend with analysis orchestration
- Next.js 16 frontend with patient dashboard
- Demo flow with 10 pre-analyzed sessions
- Real-time granular polling with loading overlays
- Railway deployment (backend + DB)

</details>

### 🚧 PR #1: SessionDetail UI Enhancements (In Progress)

**Milestone Goal:** Improve SessionDetail readability and add Wave 1 action summarization

#### Phase 1: Font Standardization + Action Summarization ✅ COMPLETE
**Goal**: Standardize fonts across SessionDetail and add 45-char action summaries
**Depends on**: v1.0 MVP
**Research**: Unlikely (UI refinement + GPT-5-nano integration)
**Plans**: 2 plans

Plans:
- [x] 01-01: Font standardization (Inter + Crimson Pro across SessionDetail and DeepAnalysisSection)
- [x] 01-02: Action summarization + SessionDetail enhancements (mood score, technique definitions, X button, theme toggle)

**Completed**: 2026-01-09

---

#### Phase 2: Prose Analysis UI Toggle 📋 PLANNED
**Goal**: Add tab toggle between prose narrative and structured analysis views
**Depends on**: Phase 1
**Research**: Unlikely (UI component with localStorage persistence)
**Plans**: 1 plan

Plans:
- [ ] 02-01: Implement TabToggle + ProseAnalysisView components with theme-aware colors and Framer Motion transitions

**Plan Location**: `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
**Execution Prompt**: `thoughts/shared/EXECUTION_PROMPT_PR2.md`

---

### 📋 v1.1: Therapist Features (Planned)

**Milestone Goal:** Enable therapists to manage multiple patients and upload new sessions

#### Phase 3: Analytics Dashboard
**Goal**: Build therapist analytics dashboard with progress metrics and trend visualization
**Depends on**: Phase 2
**Research**: Likely (chart library selection, data aggregation patterns)
**Research topics**:
- Chart library comparison (Recharts vs Chart.js vs Victory)
- Progress metric definitions (symptom reduction, skill proficiency trends)
- Data aggregation strategies (multi-session, multi-patient)
**Plans**: 3 plans

Plans:
- [ ] 03-01: Chart infrastructure + metric definitions
- [ ] 03-02: Patient progress visualization (mood trends, skill development)
- [ ] 03-03: Therapist insights panel (breakthrough detection, engagement metrics)

---

#### Phase 4: Session Upload Pipeline
**Goal**: Allow therapists to upload audio files with processing pipeline integration
**Depends on**: Phase 3
**Research**: Likely (file upload patterns, background job processing)
**Research topics**:
- Next.js file upload (multipart/form-data, progress tracking)
- Background job queue (Redis + Celery vs Railway cron jobs)
- Audio file validation (format, duration, size limits)
**Plans**: 2 plans

Plans:
- [ ] 04-01: Upload UI + file validation
- [ ] 04-02: Background processing integration (transcription → Wave 1 → Wave 2)

---

#### Phase 5: Multi-Patient Support
**Goal**: Enable therapists to view and manage multiple patients
**Depends on**: Phase 4
**Research**: Unlikely (CRUD patterns, database relationships)
**Plans**: 2 plans

Plans:
- [ ] 05-01: Therapist dashboard with patient list
- [ ] 05-02: Patient session aggregation and filtering

---

#### Phase 6: Authentication System
**Goal**: Implement JWT-based auth for therapists and patients
**Depends on**: Phase 5
**Research**: Likely (auth strategy, session management)
**Research topics**:
- Auth provider selection (NextAuth.js vs Supabase Auth vs custom JWT)
- Role-based access control (therapist vs patient permissions)
- Session refresh strategies
**Plans**: 2 plans

Plans:
- [ ] 06-01: Auth infrastructure (JWT generation, refresh tokens, middleware)
- [ ] 06-02: Login/signup flows + protected routes

---

### 📋 v2.0: Advanced Features (Future)

**Milestone Goal:** Add chatbot, timeline visualization, and platform expansion

#### Phase 7: Chatbot Integration
**Goal**: AI chatbot for patient reflection with major event detection
**Depends on**: Phase 6
**Research**: Likely (conversational AI, event detection)
**Research topics**:
- Conversational context management (chat history, session context)
- Major event detection (GPT-5 prompt engineering)
- Patient confirmation flows
**Plans**: TBD

---

#### Phase 8: Timeline Visualization
**Goal**: Mixed timeline of therapy sessions and major life events
**Depends on**: Phase 7
**Research**: Unlikely (UI patterns)
**Plans**: TBD

---

#### Phase 9: Multi-Language Support
**Goal**: Internationalization (i18n) for non-English therapy sessions
**Depends on**: Phase 6
**Research**: Likely (i18n libraries, translation workflows)
**Research topics**:
- Next.js i18n patterns
- Multi-language AI analysis (GPT-5 multilingual capabilities)
**Plans**: TBD

---

#### Phase 10: Mobile Optimization
**Goal**: Mobile-responsive design and PWA support
**Depends on**: Phase 6
**Research**: Unlikely (responsive patterns)
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 0. Foundation | v1.0 MVP | - | Complete | Jan 2026 |
| 1. Font + Action Summarization | PR #1 | 2/2 | Complete | 2026-01-09 |
| 2. Prose Toggle | PR #1 | 0/1 | Planning | - |
| 3. Analytics Dashboard | v1.1 | 0/3 | Not started | - |
| 4. Session Upload | v1.1 | 0/2 | Not started | - |
| 5. Multi-Patient | v1.1 | 0/2 | Not started | - |
| 6. Authentication | v1.1 | 0/2 | Not started | - |
| 7. Chatbot | v2.0 | 0/TBD | Not started | - |
| 8. Timeline | v2.0 | 0/TBD | Not started | - |
| 9. Multi-Language | v2.0 | 0/TBD | Not started | - |
| 10. Mobile | v2.0 | 0/TBD | Not started | - |

---

## Notes

**Current Focus:** Phase 2 (Prose Analysis UI Toggle)
- Plan created: `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
- Execution prompt ready: `thoughts/shared/EXECUTION_PROMPT_PR2.md`
- Ready for implementation in separate Claude window

**Deferred Features:**
- SSE real-time updates → Using polling fallback (subprocess isolation bug)
- Timeline feature → Out of scope until chatbot integration (Phase 7)
- Email notifications → Not needed for MVP

**Key Architectural Decisions:**
- Default to prose view (user research shows patients prefer narrative)
- localStorage for UI preferences (simple client-side persistence)
- Framer Motion for all UI transitions
- GPT-5 series for all AI analysis (cost-effective, high quality)

---

*Last updated: 2026-01-11 after PR #2 planning phase*
