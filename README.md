# TherapyBridge - Monorepo

AI-powered therapy session transcription and analysis platform.

## Project Structure

This monorepo contains two independent projects:

```
peerbridge proj/
├── audio-transcription-pipeline/    # Standalone audio processing
├── backend/                          # Standalone FastAPI server
└── Project MDs/TherapyBridge.md     # Master documentation
```

### Projects

**1. Audio Transcription Pipeline** (`audio-transcription-pipeline/`)
- Converts therapy audio to speaker-labeled transcripts
- CPU/API and GPU/Vast.ai implementations
- Standalone - can be used independently
- See: `audio-transcription-pipeline/README.md`

**2. Backend API** (`backend/`)
- FastAPI server for session management
- AI-powered note extraction (GPT-4o)
- PostgreSQL database integration
- Standalone - can be deployed independently
- See: `backend/README.md`

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

- **Master docs**: `Project MDs/TherapyBridge.md`
- **Organization rules**: `.claude/CLAUDE.md`
- **Pipeline docs**: `audio-transcription-pipeline/README.md`
- **Backend docs**: `backend/README.md`

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
- **Frontend**: Next.js 14 (pending)

## Development

Each project has independent development:
- Separate virtual environments
- Separate dependencies
- Separate test suites
- Can be deployed independently

## License

Proprietary - TherapyBridge Project
