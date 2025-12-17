# Repository Organization Rules

## 🚨 CRITICAL RULE - GIT FIRST, ALWAYS
**BEFORE MAKING ANY CHANGES (deletions, modifications, cleanup):**
1. **STOP** - Do not proceed with any deletions or modifications
2. **CHECK GIT STATUS** - Run `git status` to see what is tracked vs untracked
3. **COMMIT EVERYTHING** - Run `git add -A && git commit -m "Backup before cleanup"`
4. **VERIFY COMMIT** - Run `git log -1` to confirm commit was created
5. **THEN AND ONLY THEN** - Proceed with changes

**This rule applies to:**
- Deleting any files or folders
- Major refactoring or reorganization
- Consolidating documentation
- Cleaning up code
- ANY operation that removes or significantly modifies files

**Why this matters:**
- Untracked files CANNOT be recovered from git
- A commit creates a safety net for ALL files (tracked and untracked)
- Users may have work-in-progress that isn't committed yet
- Better to have an extra commit than lose important work

## Core Principles
1. **Minimize file count** - Every file must earn its place. If info can live in an existing file, it goes there.
2. **One README per component** - Each major folder gets ONE README.md. No additional .md files.
3. **No archive folders** - Old code gets deleted. Git history preserves everything.
4. **No duplicate configs** - Only ONE .claude/ folder at project root.
5. **Value over volume** - Only keep information valuable for project longevity. Delete "might be useful" content.

## What Belongs in a README
- Current state & working features
- Quick start commands
- File structure (if not obvious)
- Key technical decisions & bug fixes worth remembering
- Next steps

## What Does NOT Get Its Own File
- Implementation plans (execute and delete)
- Detailed test logs (summarize critical findings only)
- Removed code archives (use git history)
- Separate "guides" that duplicate README content

## Quality Standard
Before creating any new file, ask:
1. Can this go in an existing README? → Put it there
2. Will this matter in 3 months? → If no, don't create it
3. Does this duplicate existing info? → Delete the duplicate

---

# TherapyBridge - Project State

## Current Focus: Backend AI extraction complete, Frontend dashboard next

**Full Documentation:** See `Project MDs/TherapyBridge.md`

---

## Repository Structure

**Monorepo with 2 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   ├── agents/cl/
│   └── commands/cl/
├── Project MDs/
│   └── TherapyBridge.md       # Master documentation
├── README.md                  # Root README (project overview)
├── .gitignore                 # Root gitignore
├── .python-version            # Root Python version
│
├── audio-transcription-pipeline/  # STANDALONE PROJECT
│   ├── src/
│   │   ├── pipeline.py        # CPU/API pipeline
│   │   ├── pipeline_gpu.py    # GPU/Vast.ai pipeline
│   │   ├── gpu_audio_ops.py
│   │   └── performance_logger.py
│   ├── tests/
│   │   ├── test_*.py
│   │   ├── samples/
│   │   └── outputs/           # JSON only
│   ├── scripts/
│   │   ├── setup.sh
│   │   └── setup_gpu.sh
│   ├── venv/                  # Independent venv
│   ├── .env                   # Pipeline-specific env
│   ├── .env.example
│   ├── .gitignore             # Pipeline-specific
│   ├── .python-version
│   ├── requirements.txt
│   └── README.md
│
└── backend/                   # STANDALONE PROJECT
    ├── app/
    │   ├── main.py
    │   ├── database.py
    │   ├── routers/
    │   ├── models/
    │   └── services/
    ├── tests/
    ├── migrations/
    ├── uploads/audio/         # Runtime only
    ├── venv/                  # Independent venv
    ├── .env                   # Backend-specific env
    ├── .env.example
    ├── .gitignore             # Backend-specific
    ├── .python-version
    ├── requirements.txt
    └── README.md
```

**Key principle:** Each subproject is self-contained and can be deployed independently.

---

## Current Status

**Transcription Pipeline:**
- ✅ Audio preprocessing (CPU & GPU)
- ✅ Whisper transcription (API & local GPU)
- ✅ Speaker diarization (pyannote 3.1)
- ✅ Therapist/Client role labeling

**Backend API:**
- ✅ FastAPI structure
- ✅ Database schema (Neon PostgreSQL)
- ✅ AI note extraction service (GPT-4o)
- ✅ Session endpoints

**Frontend (Initial Prototype):**
- ✅ Next.js 16 + React 19 + Tailwind CSS setup
- ✅ Therapist dashboard with patient cards
- ✅ Patient dashboard with session summaries
- ✅ Session detail pages with transcript viewer
- ✅ Error boundary for crash prevention
- ✅ API client layer (real & mock modes)
- ✅ Upload modal with processing indicator
- ⏳ Backend API integration (toggle via env flag)

---

## Quick Commands

**Run transcription pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

**Run backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

---

## Next Steps

- [ ] **CURRENT**: Test frontend with live backend (set NEXT_PUBLIC_USE_REAL_API=true)
- [ ] Fix remaining ESLint errors in pre-existing components
- [ ] Deploy backend to AWS Lambda
- [ ] Add authentication (Auth.js)
- [ ] Test Vast.ai GPU pipeline for production workloads

---

## Session Log

### 2025-12-11 - Frontend Fixes & API Integration Layer
- **Fixed server crashes**: Added ErrorBoundary component wrapping all pages
- **Fixed disabled buttons**: Created ComingSoonButton with hover tooltips
- **Created API layer**: api-config.ts + api-client.ts for backend communication
- **Created useSessionProcessing hook**: Real API polling for upload progress
- **Created useSessionData hook**: Fetch session details from backend
- **Created UploadModal component**: Modal UI for audio upload flow
- **Feature flag**: NEXT_PUBLIC_USE_REAL_API toggles between mock and real backend
- **Build verified**: npm run build passes successfully

**New files created:**
- components/error-boundary.tsx
- components/providers.tsx
- components/ui/coming-soon-button.tsx
- components/session/UploadModal.tsx
- hooks/use-session-processing.ts
- hooks/use-session-data.ts
- lib/api-config.ts
- lib/api-client.ts
- .env.local (API_URL + USE_REAL_API flags)

### 2025-12-10 - Vast.ai GPU Pipeline Clarification
- **Corrected**: Project uses Vast.ai for GPU instances, NOT Google Colab
- Vast.ai billing: charged per second, must destroy instance to stop charges
- GPU pipeline files: pipeline_gpu.py, gpu_audio_ops.py, transcribe_gpu.py
- Requirements: requirements.txt (contains GPU dependencies)
- Cleanup: Removed incorrect Colab references from documentation

### 2025-12-10 - Major Cleanup & Monorepo Organization
- Deleted duplicate .claude/ folders in subfolders
- Consolidated 6 scattered Project MDs into TherapyBridge.md
- Removed thoughts/ folder (implementation plans)
- Deleted unused GPU provider scripts (Lambda, Paperspace, RunPod)
- Deleted docker/ folder and README_GPU.md (redundant)
- Cleaned test outputs (removed HTML/MD, kept JSON)
- Removed __pycache__ files from backend
- Created .env.example files for both projects
- Created .gitignore and .python-version for backend
- Updated root .gitignore for monorepo structure
- Created root README.md explaining monorepo organization
- Updated CLAUDE.md with accurate structure showing independent projects
- File count reduced by 50+ files
- Final result: Clean monorepo with 2 standalone, deployable projects

### 2025-12-08 - Repository Cleanup
- Added organization rules to CLAUDE.md
- Consolidated all docs into single TherapyBridge.md
- Deleted archive/, docs/, duplicate .claude/, scattered MDs
- Simplified to minimal, high-quality structure

---

## Parallel Workflow Orchestration

**What it does:**
- Automatically parallelizes complex tasks using multiple Claude agents (10x+ faster on large tasks)
- Intelligently breaks down work into independent operations
- Executes in dependency-aware waves (e.g., Wave 1: search, Wave 2: modify based on results)
- Calculates optimal agent count automatically
- Provides real-time progress tracking and consolidated results

**When to use:**
1. Large-scale refactoring or migrations across multiple files
2. Repository-wide security audits or vulnerability fixes
3. Adding comprehensive documentation or tests to entire codebase
4. Multi-service deployments with environment-specific configurations
5. Mass data migrations or batch processing operations

**How to use:**
Simply invoke with your task - parallelization happens automatically:
```
@parallel-orchestrator [task description]
```

**Example prompts:**
- `@parallel-orchestrator Clean up and enhance navigability of this repo`
- `@parallel-orchestrator Migrate all React class components to functional components`
- `@parallel-orchestrator Add comprehensive error handling to all API endpoints`
- `@parallel-orchestrator Deploy backend, frontend, and pipeline to staging environments`

**Optional: Manual agent count override**
If you want to specify the exact number of agents (not recommended - automatic is usually better):
```
@parallel-orchestrator [task] using [N] agents
```

**Documentation:**
- `.claude/DYNAMIC_WAVE_ORCHESTRATION.md` - Complete methodology & algorithms
- `.claude/agents/cl/parallel-orchestrator-examples.md` - Real-world examples with timing benchmarks
- `.claude/agents/cl/parallel-orchestrator-tests.md` - Test cases & validation results
