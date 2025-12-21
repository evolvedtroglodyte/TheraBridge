# TherapyBridge

**AI-powered therapy session transcription and analysis platform**

Transform therapy sessions into actionable insights with automatic transcription, speaker diarization, and intelligent analysis.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Node.js 20+
- Supabase account (free tier)
- OpenAI API key

### Setup

1. **Clone and install**
   ```bash
   git clone <your-repo>
   cd "peerbridge proj/frontend"
   npm install
   ```

2. **Configure environment**
   ```bash
   # Edit frontend/.env.local with your credentials:
   # - NEXT_PUBLIC_SUPABASE_URL
   # - NEXT_PUBLIC_SUPABASE_ANON_KEY
   # - OPENAI_API_KEY
   ```

3. **Set up Supabase**
   - Create project at [supabase.com](https://supabase.com)
   - Run `supabase/schema.sql` in SQL Editor
   - Copy URL and anon key to `.env.local`

4. **Run development server**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000/patient/dashboard-v3](http://localhost:3000/patient/dashboard-v3)

---

## 📦 Deployment (Hackathon-Ready)

**Deploy in 10 minutes:** See [DEPLOYMENT.md](./DEPLOYMENT.md)

**Stack:**
- ✅ **Vercel** - Next.js hosting + serverless functions (FREE)
- ✅ **Supabase** - PostgreSQL + file storage (FREE)
- ⚠️ **OpenAI** - Whisper API + GPT-4 (~$0.40 per session)

---

## ✨ Features

### Patient Dashboard
- **Session Timeline** - Chronological view of all therapy sessions
- **AI Chat (Dobby)** - Ask questions about your therapy journey
- **Notes & Goals** - Track progress and treatment plans
- **Progress Patterns** - Visualize mood and topic trends
- **Upload Page** - Drag-drop audio files for processing

### Audio Processing
- **Automatic Transcription** - OpenAI Whisper API (accurate, fast)
- **Speaker Diarization** - Identify Therapist vs. Client
- **Session Analysis** - GPT-4 extracts:
  - Overall mood/tone
  - Main topics discussed
  - Key insights
  - Action items
  - Brief summary

### Real-Time Progress
- Live progress bar during processing
- Status polling every 2 seconds
- Estimated completion time

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│   Next.js 16 + React 19         │
│   - App Router                  │
│   - Server Components           │
│   - API Routes (Serverless)     │
└───────────┬─────────────────────┘
            │
            ├─► Supabase
            │   - PostgreSQL (sessions, users, notes)
            │   - Storage (audio files)
            │   - Row Level Security
            │
            └─► OpenAI APIs
                - Whisper (transcription)
                - GPT-4 (analysis)
```

### Database Schema

**Core Tables:**
- `users` - Therapists and patients
- `patients` - Extended patient info
- `therapy_sessions` - Session metadata + results
- `session_notes` - AI-extracted clinical notes
- `treatment_goals` - Goal tracking

**Storage:**
- `audio-sessions` bucket - Uploaded audio files

---

## Project Structure

```
peerbridge proj/
├── frontend/                      # Next.js application
│   ├── app/
│   │   ├── api/                   # Serverless API routes
│   │   │   ├── upload/            # File upload endpoint
│   │   │   ├── process/           # Audio processing
│   │   │   ├── status/[id]/       # Status polling
│   │   │   └── trigger-processing/ # Async trigger
│   │   └── patient/dashboard-v3/  # Main dashboard
│   │       ├── upload/            # Upload page
│   │       └── components/        # UI components
│   ├── lib/
│   │   ├── supabase.ts            # Supabase client + types
│   │   └── api-client.ts          # API helpers
│   └── package.json
│
├── audio-transcription-pipeline/  # Original pipeline (reference)
│   ├── src/
│   │   ├── pipeline.py            # CPU/API pipeline
│   │   └── pipeline_gpu.py        # GPU pipeline (legacy)
│   └── ui-web/                    # React UI (reference)
│
├── supabase/
│   └── schema.sql                 # Database schema
│
├── DEPLOYMENT.md                  # Deployment guide
└── README.md                      # This file
```

## Quick Start

Each project is self-contained with its own:
- Virtual environment (`venv/`)
- Dependencies (`requirements.txt`)
- Configuration (`.env`, `.python-version`)
- Tests and documentation

**Run Pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

**Run Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Documentation

- **Master documentation**: `Project MDs/TherapyBridge.md` (start here!)
- **Organization rules**: `.claude/CLAUDE.md`
- **Orchestration methodology**: `.claude/DYNAMIC_WAVE_ORCHESTRATION.md`
- **Pipeline docs**: `audio-transcription-pipeline/README.md`
- **Backend docs**: `backend/README.md`
- **Frontend docs**: `frontend/README.md`

## Environment Setup

Each project needs its own `.env` file:

**Pipeline:**
```bash
cd audio-transcription-pipeline
cp .env.example .env
# Edit .env with your OpenAI and HuggingFace keys
```

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env with your database URL and OpenAI key
```

## Repository Organization

This repo follows strict organization rules (see `.claude/CLAUDE.md`):
- Minimize file count
- One README per component
- No implementation plans (execute and delete)
- No duplicate configs
- Value over volume

## Tech Stack

- **Transcription**: OpenAI Whisper API / faster-whisper (GPU)
- **Diarization**: pyannote.audio 3.1
- **Backend**: FastAPI + PostgreSQL (Neon)
- **AI Extraction**: OpenAI GPT-4o
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS

## Development

Each project has independent development:
- Separate virtual environments
- Separate dependencies
- Separate test suites
- Can be deployed independently

## License

Proprietary - TherapyBridge Project
