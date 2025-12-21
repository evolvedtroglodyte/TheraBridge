# Quick Start: GPU Pipeline Web Server

Get the server running in 3 minutes.

## Prerequisites

1. Python 3.13+ installed
2. Pipeline dependencies installed (see main README)
3. Environment variables configured (.env file)

## Installation

```bash
# From the ui/ directory
pip install -r requirements-server.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- python-multipart (file upload handling)

## Start the Server

```bash
# From the ui/ directory
python server.py
```

You should see:

```
============================================================
GPU Transcription Pipeline Server
============================================================
UI: http://localhost:8000
API Docs: http://localhost:8000/docs
Pipeline: /path/to/pipeline_gpu.py
Upload Dir: /path/to/uploads
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Test the Server

### Option 1: Use the Web UI

1. Open browser: http://localhost:8000
2. Drag and drop an audio file
3. Click "Start Processing"
4. Watch progress and view results

### Option 2: Use the API Documentation

1. Open browser: http://localhost:8000/docs
2. Interactive Swagger UI with all endpoints
3. Try out endpoints directly in browser

### Option 3: Use curl

```bash
# Upload file
curl -X POST "http://localhost:8000/api/upload?num_speakers=2" \
  -F "file=@/path/to/audio.mp3"

# Response:
# {
#   "job_id": "abc123-...",
#   "status": "queued",
#   "message": "File uploaded successfully. Processing started."
# }

# Check status
curl "http://localhost:8000/api/status/abc123-..."

# Get results (when complete)
curl "http://localhost:8000/api/results/abc123-..."
```

### Option 4: Run Test Script

```bash
# From the ui/ directory
python test_server.py
```

This tests all API endpoints (without GPU processing).

## Troubleshooting

### Port 8000 already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill it or use a different port in server.py
```

### ModuleNotFoundError: fastapi

```bash
pip install -r requirements-server.txt
```

### Pipeline fails to run

1. Check environment variables:
   ```bash
   cd ..
   cat .env | grep -E "OPENAI|HF_TOKEN"
   ```

2. Test pipeline directly:
   ```bash
   cd ..
   python src/pipeline_gpu.py tests/samples/sample.mp3
   ```

3. Check pipeline dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### CORS errors in browser

If running frontend on a different port, update CORS in server.py:
```python
allow_origins=["http://localhost:3000"]
```

## Next Steps

1. **Integrate with Frontend**: See `api-integration-example.js` for code examples
2. **Test with Real Audio**: Upload a real MP3/WAV file via the UI
3. **Monitor Logs**: Server logs show pipeline progress in real-time
4. **Explore API**: Visit http://localhost:8000/docs for interactive docs

## File Structure

```
ui/
├── server.py                    # FastAPI server ← START HERE
├── requirements-server.txt      # Server dependencies
├── index.html                   # Web UI
├── app.js                       # Frontend (currently mock)
├── api-integration-example.js   # Real API integration code
├── test_server.py              # API test script
├── uploads/                     # Auto-created on first upload
│   ├── temp/                    # Temporary file storage
│   └── results/                 # JSON results
└── SERVER_README.md            # Full documentation
```

## Common Commands

```bash
# Start server
python server.py

# Test server (while running)
python test_server.py

# Check server health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# View active jobs
curl http://localhost:8000/api/jobs
```

## What Happens When You Upload?

1. **Upload** → File saved to `uploads/temp/{job_id}/`
2. **Validation** → File type and size checked
3. **Queue** → Job added to processing queue
4. **Processing** → Pipeline runs as subprocess
5. **Progress** → Status updated in real-time
6. **Results** → JSON saved to `uploads/results/{job_id}.json`
7. **Cleanup** → Temp files deleted automatically

## Development Tips

- **Auto-reload**: Server restarts on code changes (reload=True)
- **Logs**: Pipeline output shown in terminal
- **Debugging**: Add `print()` statements in server.py
- **API Testing**: Use Swagger UI at /docs for interactive testing

## Production Notes

This is a **development server**. For production:

1. Disable auto-reload
2. Use production ASGI server (gunicorn)
3. Add authentication
4. Use persistent storage (Redis/PostgreSQL)
5. Set up HTTPS (nginx reverse proxy)
6. Implement job queue (Celery)

See `SERVER_README.md` for production deployment guide.

## Need Help?

- **Server logs**: Check terminal output
- **API errors**: Visit http://localhost:8000/docs
- **Pipeline errors**: Check `uploads/` directory
- **Integration**: See `api-integration-example.js`

## Success!

If you can access http://localhost:8000 and see the UI, you're ready to go!

Next step: Upload an audio file and watch the magic happen. ✨
