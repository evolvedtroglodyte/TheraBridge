# Getting Started with Audio Transcription Web UI

Welcome! This guide will get you up and running in **under 10 minutes**.

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Python 3.13+** installed (`python3 --version`)
- [ ] **Node.js 20+** installed (`node --version`)
- [ ] **FFmpeg** installed (`ffmpeg -version`)
- [ ] **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- [ ] **HuggingFace Token** ([Get one here](https://huggingface.co/settings/tokens))

## Quick Start (3 Steps)

### Step 1: Run Setup Script

```bash
cd ui-web
./scripts/setup-local.sh
```

This will:
- Install Python dependencies in a virtual environment
- Install Node.js dependencies
- Create `.env` files from examples

### Step 2: Add Your API Keys

Edit `backend/.env` and add your keys:

```bash
# Open in your favorite editor
nano backend/.env

# Or
code backend/.env
```

Add these lines:
```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
HUGGINGFACE_TOKEN=hf_your-actual-token-here
```

Save and close the file.

### Step 3: Start the Application

**Terminal 1** - Start Backend:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m app.main
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2** - Start Frontend:
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v6.0.1  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Open your browser**: http://localhost:5173

🎉 **You're done!** The app is now running.

---

## Your First Transcription

1. **Prepare an audio file** (MP3, WAV, M4A, OGG, FLAC, or AAC)
   - Max size: 100MB
   - Recommended: Clear audio with 2 distinct speakers

2. **Upload the file**:
   - Drag and drop onto the upload area
   - Or click "Browse files" to select

3. **Watch the progress**:
   - Preprocessing (5-10 seconds)
   - Transcription (30 sec per hour of audio)
   - Diarization (10-30 sec per hour of audio)
   - Alignment (< 1 second)

4. **View your results**:
   - Searchable transcript with speaker labels
   - Audio player with waveform
   - Speaker timeline visualization
   - Export options (JSON, TXT, SRT)

---

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

**Error**: `ImportError: No module named 'pydub'`

**Solution**: FFmpeg not installed
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

---

**Error**: `401 Unauthorized` from OpenAI API

**Solution**: Check your API key
```bash
# Verify your .env file has the correct key
cat backend/.env | grep OPENAI_API_KEY
```

---

### Frontend won't start

**Error**: `Cannot find module 'vite'`

**Solution**: Install dependencies
```bash
cd frontend
npm install
```

---

**Error**: `Failed to fetch` when uploading

**Solution**: Backend not running
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it:
cd backend
source venv/bin/activate
python -m app.main
```

---

### Upload fails

**Error**: File size too large

**Solution**: Reduce file size or increase limit in `backend/.env`:
```env
MAX_UPLOAD_SIZE_MB=200
```

---

**Error**: WebSocket connection failed

**Solution**:
1. Check browser console for errors (F12)
2. Verify backend is running
3. Check CORS settings in `backend/.env`:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Next Steps

### Learn More
- Read the [User Guide](docs/user-guide.md) for detailed features
- Check the [API Reference](docs/api-reference.md) to integrate with other tools
- See [Architecture](docs/architecture.md) to understand how it works

### Deploy to Production
- Follow the [Deployment Guide](docs/deployment-guide.md)
- Options: Docker Compose, Railway, Fly.io
- Estimated setup time: 15-30 minutes

### Customize
- Modify frontend components in `frontend/src/components/`
- Add custom API endpoints in `backend/app/api/routes/`
- Update styling in `frontend/src/index.css`

---

## Quick Reference

### Useful Commands

**Backend**:
```bash
# Start backend
cd backend && source venv/bin/activate && python -m app.main

# Run tests
cd backend && source venv/bin/activate && pytest

# View logs
# Logs appear in terminal where backend is running
```

**Frontend**:
```bash
# Start dev server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Preview production build
cd frontend && npm run preview

# Lint code
cd frontend && npm run lint
```

**Docker**:
```bash
# Start with Docker Compose
cd deployment && docker-compose up

# Stop
cd deployment && docker-compose down

# View logs
cd deployment && docker-compose logs -f
```

---

### File Locations

**Configuration**:
- Backend config: `backend/.env`
- Frontend config: `frontend/.env.local`

**Uploads**:
- Uploaded files: `backend/uploads/{job_id}/`
- Results: `backend/results/{job_id}.json`

**Logs**:
- Backend: Terminal output (or `backend/logs/` if configured)
- Frontend: Browser console (F12)

---

### API Endpoints

Once running, visit:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:5173

---

## Support

**Documentation**: See `docs/` directory
- [Local Setup Guide](docs/local-setup.md) - Detailed setup instructions
- [Deployment Guide](docs/deployment-guide.md) - Production deployment
- [API Reference](docs/api-reference.md) - Complete API docs
- [Architecture](docs/architecture.md) - Technical details
- [User Guide](docs/user-guide.md) - Using the interface

**Common Issues**: See [Troubleshooting](#troubleshooting) above

**Still stuck?**: Check the main repository issues or create a new one.

---

## What's Next?

### Immediate Next Steps
1. ✅ Set up API keys
2. ✅ Run the app locally
3. ✅ Upload a test file
4. ✅ Explore the features

### Future Enhancements
- [ ] Add user authentication
- [ ] Support GPU mode (Vast.ai)
- [ ] Implement job persistence
- [ ] Add batch upload
- [ ] Deploy to production

---

**Happy transcribing!** 🎙️✨
