# Local Setup Guide

Complete guide for setting up the Audio Transcription Web UI on your local development machine.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Automated)](#quick-start-automated)
- [Manual Setup](#manual-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Verifying the Setup](#verifying-the-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

1. **Python 3.13+**
   ```bash
   python --version
   # Should output: Python 3.13.x or higher
   ```

   Installation:
   - macOS: `brew install python@3.13`
   - Ubuntu: `sudo apt install python3.13`
   - Windows: Download from [python.org](https://www.python.org/)

2. **Node.js 20+**
   ```bash
   node --version
   # Should output: v20.x.x or higher
   ```

   Installation:
   - macOS: `brew install node@20`
   - Ubuntu: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`
   - Windows: Download from [nodejs.org](https://nodejs.org/)

3. **FFmpeg** (for audio processing)
   ```bash
   ffmpeg -version
   # Should output version information
   ```

   Installation:
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH

### API Keys

You'll need the following API keys:

1. **OpenAI API Key** (for Whisper transcription)
   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Go to API Keys section
   - Create a new key
   - Requires billing setup (pay-per-use)

2. **HuggingFace Token** (for speaker diarization)
   - Sign up at [huggingface.co](https://huggingface.co/)
   - Go to Settings → Access Tokens
   - Create a new token (read access is sufficient)
   - Accept terms for `pyannote/speaker-diarization-3.1` model

> **Note**: The HuggingFace token is free. You must accept the model's terms of use at [huggingface.co/pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

## Quick Start (Automated)

The fastest way to get started is using the setup script:

```bash
# Navigate to the ui-web directory
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline/ui-web

# Run the setup script
./scripts/setup-local.sh
```

The script will:
- Create environment configuration files
- Set up Python virtual environment for backend
- Install all Python dependencies
- Install all Node.js dependencies
- Display next steps

After running the script, **edit `backend/.env`** to add your API keys:

```bash
# Open the environment file
nano backend/.env  # or use your preferred editor

# Add your keys:
OPENAI_API_KEY=sk-proj-...your-key-here...
HUGGINGFACE_TOKEN=hf_...your-token-here...
```

Then proceed to [Running the Application](#running-the-application).

## Manual Setup

If you prefer to set up manually or the script doesn't work:

### 1. Clone/Navigate to Project

```bash
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline/ui-web
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Deactivate for now
deactivate
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from ui-web root)
cd frontend

# Install dependencies
npm install

# Optional: Check for updates
npm outdated
```

### 4. Environment Configuration

#### Backend Environment (.env)

```bash
# Create backend/.env from template
cd backend
cp .env.example .env
```

Edit `backend/.env` with your configuration:

```env
# OpenAI API Key (required for Whisper transcription)
OPENAI_API_KEY=sk-proj-...your-key-here...

# HuggingFace Token (required for speaker diarization)
HUGGINGFACE_TOKEN=hf_...your-token-here...

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# File Upload
MAX_UPLOAD_SIZE_MB=100

# Processing
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT_SECONDS=3600

# Logging
LOG_LEVEL=INFO
```

#### Frontend Environment (.env.local)

```bash
# Create frontend/.env.local
cd ../frontend
touch .env.local
```

Add the following to `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Environment Configuration

### Configuration Options Explained

#### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for Whisper transcription |
| `HUGGINGFACE_TOKEN` | Yes | - | HuggingFace token for speaker diarization |
| `API_HOST` | No | `0.0.0.0` | Host to bind the API server |
| `API_PORT` | No | `8000` | Port for the API server |
| `API_DEBUG` | No | `true` | Enable debug mode (auto-reload) |
| `CORS_ORIGINS` | No | See above | Comma-separated allowed origins |
| `MAX_UPLOAD_SIZE_MB` | No | `100` | Maximum file upload size in MB |
| `MAX_CONCURRENT_JOBS` | No | `3` | Number of parallel transcription jobs |
| `JOB_TIMEOUT_SECONDS` | No | `3600` | Job timeout (1 hour) |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

#### Frontend (.env.local)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | - | Backend API base URL |
| `VITE_WS_URL` | Yes | - | WebSocket base URL |

> **Important**: For local development, backend runs on port 8000 and frontend on port 5173. Make sure these ports are not in use.

## Running the Application

You'll need **two terminal windows** - one for backend, one for frontend.

### Terminal 1: Start Backend

```bash
# Navigate to backend directory
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline/ui-web/backend

# Activate virtual environment
source venv/bin/activate

# Start the backend server
python -m app.main
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

> **Tip**: The backend will auto-reload when you make changes to Python files (if `API_DEBUG=true`).

### Terminal 2: Start Frontend

```bash
# Navigate to frontend directory
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline/ui-web/frontend

# Start the development server
npm run dev
```

You should see:
```
  VITE v6.0.1  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:5173
```

You should see the Audio Transcription UI with the file upload interface.

## Verifying the Setup

### 1. Check Backend Health

Open in browser or use curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "pipeline_path": "../../src/pipeline.py",
  "upload_dir": "./uploads",
  "results_dir": "./results"
}
```

### 2. Check API Documentation

Navigate to:
```
http://localhost:8000/docs
```

You should see the interactive API documentation (Swagger UI).

### 3. Test File Upload

1. Go to http://localhost:5173
2. Click "Choose File" or drag-and-drop an audio file
3. Supported formats: MP3, WAV, M4A, OGG, FLAC, AAC
4. File should upload and processing should start
5. You'll see real-time progress updates

### 4. Check WebSocket Connection

In the browser console (F12), you should see:
```
WebSocket connected for job: <job-id>
```

If you see connection errors, verify the `VITE_WS_URL` in frontend `.env.local`.

## Troubleshooting

### Backend Issues

#### "ModuleNotFoundError: No module named 'app'"

**Solution**: Make sure you're in the `backend/` directory and the virtual environment is activated:
```bash
cd backend
source venv/bin/activate
python -m app.main
```

#### "ERROR: Could not find a version that satisfies the requirement..."

**Solution**: Check Python version (must be 3.13+):
```bash
python --version
# If wrong version, ensure you're using python3.13
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### "ffmpeg not found"

**Solution**: Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

#### "OpenAI API key not found"

**Solution**: Ensure `OPENAI_API_KEY` is set in `backend/.env`:
```bash
# Check if key is present
cat backend/.env | grep OPENAI_API_KEY

# If missing, edit the file
nano backend/.env
```

#### Port 8000 already in use

**Solution**: Kill the process using port 8000 or change the port:
```bash
# Find process using port 8000
lsof -i :8000

# Kill it (replace PID with actual process ID)
kill -9 <PID>

# OR change port in backend/.env
API_PORT=8001
```

### Frontend Issues

#### "npm: command not found"

**Solution**: Install Node.js:
```bash
# macOS
brew install node@20

# Verify installation
node --version
npm --version
```

#### "Cannot find module" errors during npm install

**Solution**: Clear npm cache and reinstall:
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Frontend not connecting to backend

**Solution**:
1. Verify backend is running on port 8000
2. Check `frontend/.env.local` has correct URLs:
   ```env
   VITE_API_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000
   ```
3. Check CORS settings in `backend/.env`:
   ```env
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

#### WebSocket connection failed

**Solution**:
1. Ensure WebSocket URL uses `ws://` not `http://`
2. Check browser console for detailed error
3. Verify backend WebSocket endpoint is accessible:
   ```bash
   # Test WebSocket (requires websocat or similar)
   websocat ws://localhost:8000/ws/transcription/test-job-id
   ```

### Upload Issues

#### "File too large" error

**Solution**: Increase max upload size in `backend/.env`:
```env
MAX_UPLOAD_SIZE_MB=200  # Default is 100
```

#### Upload fails with no error message

**Solution**: Check backend logs for detailed errors:
```bash
# Backend terminal should show error details
# If LOG_LEVEL=INFO doesn't show enough, try:
LOG_LEVEL=DEBUG
```

#### Processing stalls at certain stage

**Solution**:
1. Check API keys are correct and have quota
2. Verify internet connection (required for API calls)
3. Check backend logs for timeout errors
4. Increase timeout if needed:
   ```env
   JOB_TIMEOUT_SECONDS=7200  # 2 hours
   ```

### Performance Issues

#### Transcription is very slow

**Solution**:
- This is expected for CPU/API pipeline
- For large files (>10 minutes), consider using GPU pipeline
- Check your internet speed (Whisper API requires upload/download)
- Monitor OpenAI API status: [status.openai.com](https://status.openai.com)

#### Out of memory errors

**Solution**: Reduce concurrent jobs:
```env
MAX_CONCURRENT_JOBS=1  # Process one file at a time
```

### Database/File Issues

#### Results not appearing after completion

**Solution**: Check file permissions:
```bash
# Ensure results directory exists and is writable
ls -la backend/results
chmod 755 backend/results
```

#### Old jobs cluttering the interface

**Solution**: Delete old transcriptions:
```bash
# Via API
curl -X DELETE http://localhost:8000/api/transcriptions/<job-id>

# Or manually delete files
rm backend/results/*.json
rm backend/uploads/*
```

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Backend**: Changes to `.py` files trigger auto-restart (if `API_DEBUG=true`)
- **Frontend**: Changes to `.tsx`/`.ts` files trigger instant reload

### Viewing Logs

Backend logs appear in Terminal 1. To save logs to file:
```bash
python -m app.main 2>&1 | tee backend.log
```

Frontend logs appear in browser console (F12 → Console tab).

### Testing Different Audio Files

Sample audio files for testing:
```bash
# Create test directory
mkdir -p tests/audio

# Download sample files (example)
curl -o tests/audio/sample.mp3 [sample-url]
```

Recommended test cases:
- Short file (< 1 minute)
- Medium file (5-10 minutes)
- Multiple speakers
- Different languages
- Various audio formats

### Stopping the Application

1. **Frontend**: Press `Ctrl+C` in Terminal 2
2. **Backend**: Press `Ctrl+C` in Terminal 1
3. **Deactivate venv**: Type `deactivate` in Terminal 1

## Next Steps

After successful setup:

1. **Test the full pipeline** with a sample audio file
2. **Review the [User Guide](user-guide.md)** to understand all features
3. **Check the [API Reference](api-reference.md)** for integration options
4. **Read the [Architecture Overview](architecture.md)** to understand the system
5. **Explore deployment options** in the [Deployment Guide](deployment-guide.md)

## Getting Help

If you encounter issues not covered here:

1. Check backend logs in Terminal 1
2. Check browser console (F12) for frontend errors
3. Review the [API documentation](http://localhost:8000/docs) for endpoint details
4. Consult the main repository README for pipeline-specific issues
5. Create an issue in the repository with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, Python version, Node version)

---

**Setup complete!** You should now have a fully functional local development environment.
