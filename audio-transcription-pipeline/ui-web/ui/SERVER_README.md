# GPU Pipeline Web Server

Lightweight FastAPI server that bridges the web UI with the GPU transcription pipeline.

## Features

- **RESTful API** with 3 main endpoints
- **File upload handling** with validation (500MB max, audio formats only)
- **Background processing** via subprocess execution
- **Progress tracking** with real-time status updates
- **Auto-cleanup** of temporary files
- **Static file serving** for the web UI
- **CORS enabled** for local development

## Architecture

```
Browser → FastAPI Server → GPU Pipeline (subprocess) → Results
   ↓           ↓                    ↓                     ↓
Upload    Validate/Save      Run pipeline_gpu.py    Return JSON
```

## Installation

### 1. Install server dependencies

```bash
# From the ui/ directory
pip install -r requirements-server.txt
```

### 2. Ensure pipeline dependencies are installed

```bash
# From the audio-transcription-pipeline/ root
pip install -r requirements.txt
pip install -r requirements_gpu.txt  # If using GPU
```

### 3. Set up environment variables

Create `.env` in the project root (if not already present):

```bash
# Required for GPU pipeline
OPENAI_API_KEY=your_openai_key
HF_TOKEN=your_huggingface_token
```

## Usage

### Start the server

```bash
# From the ui/ directory
python server.py
```

The server will start on `http://localhost:8000`

### Access the UI

Open your browser to:
- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Health Check**: http://localhost:8000/health

### Development mode

The server runs with auto-reload enabled by default. Any changes to `server.py` will automatically restart the server.

## API Endpoints

### POST /api/upload

Upload an audio file for processing.

**Request:**
- `file`: Audio file (multipart/form-data)
- `num_speakers`: Number of speakers (optional, default: 2)

**Response:**
```json
{
  "job_id": "abc123-...",
  "status": "queued",
  "message": "File uploaded successfully. Processing started."
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/upload?num_speakers=2" \
  -F "file=@audio.mp3"
```

### GET /api/status/{job_id}

Get processing status for a job.

**Response:**
```json
{
  "job_id": "abc123-...",
  "status": "processing",
  "progress": 65,
  "step": "Transcribing with Whisper",
  "error": null
}
```

**Statuses:**
- `queued` - Job accepted, waiting to start
- `processing` - Currently running
- `completed` - Finished successfully
- `failed` - Error occurred

**Example (curl):**
```bash
curl "http://localhost:8000/api/status/abc123-..."
```

### GET /api/results/{job_id}

Get transcription results for a completed job.

**Response:**
```json
{
  "job_id": "abc123-...",
  "status": "completed",
  "segments": [...],
  "aligned_segments": [...],
  "full_text": "...",
  "language": "en",
  "duration": 2718.0,
  "speaker_turns": [...],
  "provider": "vast",
  "performance_metrics": {...}
}
```

**Example (curl):**
```bash
curl "http://localhost:8000/api/results/abc123-..."
```

### Additional Endpoints

- **GET /api/jobs** - List all jobs (debugging)
- **DELETE /api/jobs/{job_id}** - Delete a job and its results
- **GET /health** - Server health check

## File Structure

```
ui/
├── server.py                    # FastAPI server (this file)
├── requirements-server.txt      # Server dependencies
├── index.html                   # Web UI
├── app.js                       # Frontend JavaScript
├── styles.css                   # UI styles
├── uploads/                     # Auto-created
│   ├── temp/                    # Temporary upload storage
│   └── results/                 # JSON results storage
└── SERVER_README.md            # This file
```

## Configuration

Edit these constants at the top of `server.py`:

```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mp4'}
```

## Error Handling

The server handles:
- **Invalid file types** (400 Bad Request)
- **Files too large** (413 Payload Too Large)
- **Missing jobs** (404 Not Found)
- **Pipeline execution errors** (500 Internal Server Error)

Errors are logged to console and returned in API responses.

## Production Deployment

For production, consider:

1. **Disable auto-reload**:
   ```python
   uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
   ```

2. **Use production ASGI server**:
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 server:app
   ```

3. **Enable HTTPS** (use nginx reverse proxy)

4. **Restrict CORS** origins:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

5. **Use persistent storage** (replace in-memory `jobs` dict with Redis/PostgreSQL)

6. **Add authentication** (JWT tokens, API keys)

7. **Set up log rotation** and monitoring

## Troubleshooting

### Server won't start

1. Check port 8000 is available:
   ```bash
   lsof -i :8000
   ```

2. Verify dependencies installed:
   ```bash
   pip list | grep fastapi
   ```

### Pipeline fails to run

1. Check pipeline script exists:
   ```bash
   ls -la ../src/pipeline_gpu.py
   ```

2. Verify environment variables:
   ```bash
   cat ../.env | grep -E "OPENAI|HF_TOKEN"
   ```

3. Test pipeline manually:
   ```bash
   cd ..
   python src/pipeline_gpu.py tests/samples/sample.mp3
   ```

### Upload fails

1. Check file size (max 500MB)
2. Verify file extension is allowed
3. Ensure `uploads/` directory is writable

### CORS errors in browser

If frontend is on different port/domain, update CORS settings in `server.py`:
```python
allow_origins=["http://localhost:3000"]  # Your frontend URL
```

## Development Notes

- **In-memory storage**: Jobs are stored in-memory. Server restart = all jobs lost.
- **No authentication**: Development server has no auth. Add for production.
- **Single-threaded**: One pipeline process runs at a time. Use task queue for parallel processing.
- **Auto-cleanup**: Temp files deleted after job completes (success or failure).

## Next Steps

1. Integrate with frontend (`app.js` needs to call these endpoints)
2. Add authentication (JWT tokens)
3. Implement persistent job storage (Redis/PostgreSQL)
4. Add WebSocket support for real-time progress updates
5. Implement job queue for parallel processing (Celery, RQ)

## License

Part of TherapyBridge audio transcription pipeline.
