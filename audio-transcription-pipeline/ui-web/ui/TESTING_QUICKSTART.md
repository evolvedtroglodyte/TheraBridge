# Integration Testing - Quick Start Guide

Fast reference for running integration tests on the GPU Pipeline UI/Server.

---

## Prerequisites

1. **Install server dependencies:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
pip install fastapi uvicorn[standard] python-multipart
```

2. **Ensure test audio files exist:**
```bash
ls tests/samples/*.mp3  # Should show audio files
```

---

## Quick Test (30 seconds)

### 1. Start the server
```bash
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python server.py
```

Server will start on: http://localhost:8000

### 2. Run integration tests (in new terminal)
```bash
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python test_integration.py
```

**Expected:** 9/9 tests pass ✅

### 3. Stop the server
```bash
# In server terminal, press Ctrl+C
```

---

## Full Pipeline Test (5+ minutes)

Tests the complete flow with real audio processing.

```bash
# 1. Start server (terminal 1)
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python server.py

# 2. Run full test (terminal 2)
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python test_integration.py --full-test
```

**What it tests:**
1. Upload real audio file (12 MB)
2. Monitor processing in real-time
3. Wait for completion (3-5 minutes)
4. Fetch and validate results
5. Cleanup job

---

## Browser Testing

### 1. Start server
```bash
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python server.py
```

### 2. Open UI in browser
```
http://localhost:8000
```

### 3. Test upload flow
1. Click "Browse Files" or drag-and-drop audio file
2. Click "Process Audio"
3. Watch progress bar update
4. See results when complete

### 4. Run JavaScript tests (optional)
Open browser console and paste:
```javascript
// Load test script
var script = document.createElement('script');
script.src = '/static/test_integration.js';
document.head.appendChild(script);

// Run tests (after script loads)
setTimeout(() => GPUPipelineTests.runAllTests(), 1000);
```

---

## Manual API Testing

### Health Check
```bash
curl http://localhost:8000/health | python -m json.tool
```

### Upload File
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/samples/your-audio.mp3" \
  -F "num_speakers=2"
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "queued",
  "message": "File uploaded successfully. Processing started."
}
```

### Check Status
```bash
JOB_ID="abc-123-def-456"
curl http://localhost:8000/api/status/$JOB_ID | python -m json.tool
```

### Get Results
```bash
curl http://localhost:8000/api/results/$JOB_ID | python -m json.tool
```

### List All Jobs
```bash
curl http://localhost:8000/api/jobs | python -m json.tool
```

### Delete Job
```bash
curl -X DELETE http://localhost:8000/api/jobs/$JOB_ID
```

---

## Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
pip install fastapi uvicorn[standard] python-multipart
```

---

### Tests fail with "Connection refused"

**Problem:** Server is not running

**Fix:**
```bash
# Start server in separate terminal
cd audio-transcription-pipeline/ui
source ../venv/bin/activate
python server.py
```

---

### Pipeline script not found

**Error:** `"pipeline_exists": false` in health check

**Fix:**
Check pipeline script exists:
```bash
ls ../src/pipeline_gpu.py  # Should exist
```

---

### Upload fails with "Invalid file type"

**Problem:** Wrong file extension

**Fix:** Use supported formats:
- .mp3
- .wav
- .m4a
- .flac
- .ogg
- .webm
- .mp4

---

### Processing stuck at 10%

**Possible causes:**
1. Pipeline dependencies not installed
2. GPU not available (falls back to CPU)
3. Audio file corrupted

**Debug:**
```bash
# Check server logs
tail -f ui/server.log

# Test pipeline directly
cd src
python pipeline_gpu.py ../tests/samples/your-audio.mp3 --num-speakers 2
```

---

## Test Coverage Summary

### Python Test Suite (`test_integration.py`)
- ✅ Server health check
- ✅ CORS configuration
- ✅ Invalid file upload rejection
- ✅ Valid file upload
- ✅ Status polling
- ✅ Invalid job ID handling
- ✅ Job listing
- ✅ Job deletion
- ✅ Static file serving
- ✅ Full pipeline (with --full-test)

### JavaScript Test Suite (`test_integration.js`)
- ✅ Server connectivity
- ✅ File upload
- ✅ Status polling
- ✅ Invalid job ID
- ✅ Job listing
- ✅ Error handling
- ✅ CORS headers

---

## Test Automation in CI/CD

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        cd audio-transcription-pipeline
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install fastapi uvicorn python-multipart

    - name: Start server
      run: |
        cd audio-transcription-pipeline/ui
        source ../venv/bin/activate
        python server.py &
        sleep 5

    - name: Run tests
      run: |
        cd audio-transcription-pipeline/ui
        source ../venv/bin/activate
        python test_integration.py

    - name: Stop server
      run: pkill -f "python server.py"
```

---

## Performance Benchmarks

**Typical Test Times:**

| Test Suite | Duration | Tests |
|------------|----------|-------|
| Quick API tests | 30 seconds | 9 |
| Full pipeline test | 3-5 minutes | 10 |
| Manual browser test | 1 minute | N/A |

**Processing Times (real audio):**

| Audio Length | Processing Time | RTF |
|--------------|-----------------|-----|
| 1 minute | 45 seconds | 0.75 |
| 5 minutes | 3 minutes | 0.60 |
| 15 minutes | 8 minutes | 0.53 |

*RTF = Real-Time Factor (lower is faster)*

---

## Quick Command Reference

```bash
# Start server
python ui/server.py

# Run quick tests
python ui/test_integration.py

# Run full test
python ui/test_integration.py --full-test

# Custom server URL
python ui/test_integration.py --url http://localhost:9000

# Check server health
curl http://localhost:8000/health

# View API docs
# Open browser to: http://localhost:8000/docs
```

---

## Related Documentation

- **API Integration Guide:** `ui/API_INTEGRATION.md`
- **Server README:** `ui/SERVER_README.md`
- **Full Test Report:** `ui/WAVE4_INTEGRATION_TESTING_REPORT.md`
- **Architecture Overview:** `ui/ARCHITECTURE.md`

---

**Last Updated:** December 20, 2025
**Tested On:** Python 3.13.9, FastAPI 0.115.0+
