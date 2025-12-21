# Audio Transcription Web UI

A modern web interface for the audio transcription pipeline with speaker diarization, built with React, TypeScript, FastAPI, and WebSocket for real-time updates.

## Features

- 🎙️ **Audio Upload**: Drag-and-drop interface for audio files (MP3, WAV, M4A, OGG, FLAC, AAC)
- ⚡ **Real-Time Progress**: WebSocket-powered live updates during transcription
- 🎯 **Speaker Diarization**: Automatic speaker identification and labeling
- 🎵 **Audio Player**: Waveform visualization with transcript synchronization
- 🔍 **Searchable Transcripts**: Filter by speaker or search text
- 📊 **Visual Timeline**: Color-coded speaker timeline
- 💾 **Multiple Export Formats**: JSON, TXT, SRT subtitles
- 📱 **Responsive Design**: Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 20+
- OpenAI API key (for Whisper transcription)
- HuggingFace token (for speaker diarization)
- FFmpeg (for audio processing)

### Local Development

1. **Run the setup script**:
   ```bash
   cd ui-web
   ./scripts/setup-local.sh
   ```

2. **Configure environment variables**:
   - Edit `backend/.env` and add your API keys:
     ```
     OPENAI_API_KEY=your_key_here
     HUGGINGFACE_TOKEN=your_token_here
     ```

3. **Start the backend** (Terminal 1):
   ```bash
   cd backend
   source venv/bin/activate
   python -m app.main
   ```

4. **Start the frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

5. **Open your browser**: http://localhost:5173

## Architecture

```
┌─────────────────┐      HTTP/WebSocket      ┌──────────────────┐
│  React Frontend │◄──────────────────────────┤  FastAPI Backend │
│   (Port 5173)   │                           │   (Port 8000)    │
└─────────────────┘                           └────────┬─────────┘
                                                       │
                                                       │ Calls
                                                       ▼
                                              ┌────────────────────┐
                                              │ Existing Pipeline  │
                                              │   (src/pipeline.py)│
                                              └────────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- WaveSurfer.js (audio visualization)
- react-dropzone (file upload)

**Backend:**
- FastAPI (async Python framework)
- Uvicorn (ASGI server)
- WebSocket (real-time updates)
- In-memory job queue (concurrency control)

**Pipeline Integration:**
- Wraps existing `src/pipeline.py`
- No modifications to core pipeline code
- Preserves 100% speaker identification accuracy

## Project Structure

```
ui-web/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # FastAPI app entry point
│   │   ├── api/routes/  # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── models/      # Pydantic models
│   │   └── core/        # Configuration
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── lib/         # API client, WebSocket
│   │   ├── types/       # TypeScript types
│   │   ├── App.tsx      # Main app
│   │   └── main.tsx     # Entry point
│   ├── package.json
│   └── Dockerfile
│
├── deployment/          # Deployment configs
│   ├── docker-compose.yml
│   ├── railway.json
│   └── fly.toml
│
├── docs/               # Documentation
│   ├── local-setup.md
│   ├── deployment-guide.md
│   ├── api-reference.md
│   └── architecture.md
│
└── scripts/
    └── setup-local.sh  # Local setup script
```

## API Endpoints

### Upload
- `POST /api/upload` - Upload audio file for transcription

### Transcriptions
- `GET /api/transcriptions/{job_id}` - Get transcription result
- `GET /api/transcriptions/{job_id}/status` - Get job status with progress
- `GET /api/transcriptions` - List all transcriptions
- `DELETE /api/transcriptions/{job_id}` - Delete transcription

### WebSocket
- `WS /ws/transcription/{job_id}` - Real-time progress updates

### Health
- `GET /health` - Health check endpoint
- `GET /` - API information

## Deployment

### Docker Compose (Recommended for Local)

```bash
cd deployment
docker-compose up
```

Access the app at http://localhost

### Railway (Recommended for Remote)

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and deploy:
   ```bash
   railway login
   railway init
   railway up
   ```

3. Set environment variables in Railway dashboard:
   - `OPENAI_API_KEY`
   - `HUGGINGFACE_TOKEN`

See [docs/deployment-guide.md](docs/deployment-guide.md) for detailed instructions.

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Configuration

### Backend (.env)
```env
OPENAI_API_KEY=your_key
HUGGINGFACE_TOKEN=your_token
API_PORT=8000
MAX_CONCURRENT_JOBS=3
MAX_UPLOAD_SIZE_MB=100
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Troubleshooting

### Backend not starting
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.13+)
- Check that FFmpeg is installed: `ffmpeg -version`

### Frontend not connecting to backend
- Verify backend is running on port 8000
- Check CORS settings in `backend/.env`
- Ensure `VITE_API_URL` matches backend URL

### WebSocket connection failed
- Verify WebSocket URL format: `ws://` (not `http://`)
- Check browser console for errors
- Ensure backend WebSocket endpoint is accessible

### Upload fails
- Check file size (max 100MB by default)
- Verify file format is supported
- Check backend logs for detailed errors

## Documentation

- [Local Setup Guide](docs/local-setup.md)
- [Deployment Guide](docs/deployment-guide.md)
- [API Reference](docs/api-reference.md)
- [Architecture Overview](docs/architecture.md)

## License

This project is part of the audio-transcription-pipeline monorepo.

## Support

For issues and questions, please check the documentation or create an issue in the main repository.
