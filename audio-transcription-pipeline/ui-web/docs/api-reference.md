# API Reference

Complete API documentation for the Audio Transcription Web UI backend.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Upload Endpoints](#upload-endpoints)
- [Transcription Endpoints](#transcription-endpoints)
- [WebSocket Protocol](#websocket-protocol)
- [Health Check](#health-check)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Audio Transcription API is a RESTful API built with FastAPI that provides:
- Audio file upload
- Asynchronous transcription processing
- Real-time progress updates via WebSocket
- Transcription result retrieval
- Job management

**API Version**: 1.0.0

**Interactive Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Base URL

### Local Development
```
http://localhost:8000
```

### Production
Replace with your deployment URL:
```
https://your-app.railway.app
https://your-app.fly.dev
https://your-domain.com
```

## Authentication

**Current Version**: No authentication required

> **Note**: Future versions may implement API key authentication or OAuth2. For production deployments, consider adding authentication at the reverse proxy level (Nginx, Cloudflare, etc.)

## Upload Endpoints

### Upload Audio File

Upload an audio file for transcription processing.

**Endpoint**: `POST /api/upload`

**Content-Type**: `multipart/form-data`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Audio file to transcribe |

**Supported Formats**:
- MP3 (`.mp3`)
- WAV (`.wav`)
- M4A (`.m4a`)
- OGG (`.ogg`)
- FLAC (`.flac`)
- AAC (`.aac`)

**Maximum File Size**: 100MB (configurable via `MAX_UPLOAD_SIZE_MB`)

**Request Example**:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/audio.mp3"
```

**Response** (200 OK):

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "File 'audio.mp3' uploaded successfully. Processing started."
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique identifier for the transcription job |
| `status` | string | Job status: `pending`, `processing`, `completed`, `failed` |
| `message` | string | Human-readable status message |

**Error Responses**:

```json
// 400 Bad Request - Invalid file
{
  "detail": "File type not supported. Supported formats: mp3, wav, m4a, ogg, flac, aac"
}

// 413 Payload Too Large
{
  "detail": "File size exceeds maximum allowed size of 100MB"
}

// 500 Internal Server Error
{
  "detail": "Failed to save uploaded file"
}
```

## Transcription Endpoints

### Get Transcription Result

Retrieve the complete transcription result for a job.

**Endpoint**: `GET /api/transcriptions/{job_id}`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string (path) | Yes | Job ID returned from upload |

**Request Example**:

```bash
curl http://localhost:8000/api/transcriptions/550e8400-e29b-41d4-a716-446655440000
```

**Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "audio.mp3",
  "created_at": "2025-12-21T10:30:00.000Z",
  "completed_at": "2025-12-21T10:32:30.000Z",
  "metadata": {
    "source_file": "audio.mp3",
    "file_size_mb": 5.2,
    "duration": 180.5,
    "language": "english",
    "timestamp": "2025-12-21T10:30:00.000Z",
    "pipeline_type": "CPU_API"
  },
  "performance": {
    "total_processing_time_seconds": 150.3,
    "api_latency_seconds": 120.5,
    "computation_time_seconds": 29.8,
    "current_memory_mb": 245.6
  },
  "speakers": [
    {
      "id": "0",
      "label": "SPEAKER_00",
      "total_duration": 95.3,
      "segment_count": 15
    },
    {
      "id": "1",
      "label": "SPEAKER_01",
      "total_duration": 85.2,
      "segment_count": 12
    }
  ],
  "segments": [
    {
      "start": 0.0,
      "end": 5.5,
      "text": "Hello, welcome to our conversation.",
      "speaker_id": "0",
      "confidence": 0.95
    },
    {
      "start": 6.0,
      "end": 10.2,
      "text": "Thank you for having me.",
      "speaker_id": "1",
      "confidence": 0.92
    }
  ],
  "quality": {
    "overall_confidence": 0.94,
    "speaker_separation_quality": "high"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Job ID |
| `status` | string | Job status: `completed`, `failed`, etc. |
| `filename` | string | Original filename |
| `created_at` | datetime | Job creation timestamp |
| `completed_at` | datetime | Job completion timestamp (null if not complete) |
| `metadata` | object | File and processing metadata |
| `performance` | object | Performance metrics |
| `speakers` | array | List of detected speakers |
| `segments` | array | Transcription segments with timing and speaker info |
| `quality` | object | Quality metrics (optional) |
| `error` | string | Error message (only if status is `failed`) |

**Metadata Object**:

| Field | Type | Description |
|-------|------|-------------|
| `source_file` | string | Original filename |
| `file_size_mb` | float | File size in megabytes |
| `duration` | float | Audio duration in seconds |
| `language` | string | Language (e.g., "english") |
| `timestamp` | string | Processing timestamp |
| `pipeline_type` | string | Pipeline type used (e.g., "CPU_API") |

**Performance Object**:

| Field | Type | Description |
|-------|------|-------------|
| `total_processing_time_seconds` | float | Total time from upload to completion |
| `api_latency_seconds` | float | Time spent in API calls |
| `computation_time_seconds` | float | Local computation time |
| `current_memory_mb` | float | Memory usage during processing |

**Speaker Object**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Speaker ID (0, 1, 2, ...) |
| `label` | string | Speaker label (SPEAKER_00, SPEAKER_01, ...) |
| `total_duration` | float | Total speaking time in seconds |
| `segment_count` | integer | Number of segments for this speaker |

**Segment Object**:

| Field | Type | Description |
|-------|------|-------------|
| `start` | float | Segment start time in seconds |
| `end` | float | Segment end time in seconds |
| `text` | string | Transcribed text |
| `speaker_id` | string | Speaker ID for this segment |
| `confidence` | float | Transcription confidence (0.0 - 1.0) |

**Error Responses**:

```json
// 404 Not Found
{
  "detail": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}

// 500 Internal Server Error (Job Failed)
{
  "detail": "Job failed: OpenAI API error: Rate limit exceeded"
}
```

---

### Get Job Status

Get the current status and progress of a transcription job.

**Endpoint**: `GET /api/transcriptions/{job_id}/status`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string (path) | Yes | Job ID returned from upload |

**Request Example**:

```bash
curl http://localhost:8000/api/transcriptions/550e8400-e29b-41d4-a716-446655440000/status
```

**Response** (200 OK):

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.65,
  "stage": "diarization",
  "error": null
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Job ID |
| `status` | string | Current status: `pending`, `processing`, `completed`, `failed` |
| `progress` | float | Progress percentage (0.0 - 1.0) |
| `stage` | string | Current processing stage (see stages below) |
| `error` | string | Error message (null if no error) |

**Processing Stages**:

| Stage | Description | Progress Range |
|-------|-------------|----------------|
| `preprocessing` | Audio format conversion | 0.0 - 0.1 |
| `transcription` | Whisper API transcription | 0.1 - 0.5 |
| `diarization` | Speaker diarization | 0.5 - 0.9 |
| `postprocessing` | Combining results | 0.9 - 1.0 |
| `completed` | Processing complete | 1.0 |

**Error Responses**:

```json
// 404 Not Found
{
  "detail": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

### List All Transcriptions

Retrieve a list of all transcription jobs.

**Endpoint**: `GET /api/transcriptions`

**Request Example**:

```bash
curl http://localhost:8000/api/transcriptions
```

**Response** (200 OK):

```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "filename": "audio1.mp3",
      "created_at": "2025-12-21T10:30:00.000Z",
      "completed_at": "2025-12-21T10:32:30.000Z",
      "metadata": { ... },
      "speakers": [ ... ],
      "segments": [ ... ]
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "processing",
      "filename": "audio2.wav",
      "created_at": "2025-12-21T11:00:00.000Z",
      "completed_at": null,
      "metadata": null,
      "speakers": [],
      "segments": []
    }
  ],
  "total": 2
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `jobs` | array | Array of transcription job objects |
| `total` | integer | Total number of jobs |

---

### Delete Transcription

Delete a transcription job and all associated files.

**Endpoint**: `DELETE /api/transcriptions/{job_id}`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string (path) | Yes | Job ID to delete |

**Request Example**:

```bash
curl -X DELETE http://localhost:8000/api/transcriptions/550e8400-e29b-41d4-a716-446655440000
```

**Response** (200 OK):

```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**Error Responses**:

```json
// 404 Not Found
{
  "detail": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Side Effects**:
- Cancels the job if currently processing
- Deletes uploaded audio file
- Deletes transcription result file
- Removes job from queue

## WebSocket Protocol

Real-time progress updates via WebSocket connection.

### Connect to WebSocket

**Endpoint**: `WS /ws/transcription/{job_id}`

**Protocol**: WebSocket (ws:// for HTTP, wss:// for HTTPS)

**URL Format**:
```
ws://localhost:8000/ws/transcription/{job_id}
wss://your-app.railway.app/ws/transcription/{job_id}
```

### Connection Example

**JavaScript**:
```javascript
const jobId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/ws/transcription/${jobId}`);

ws.onopen = () => {
  console.log("WebSocket connected");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket disconnected");
};

// Keep-alive (optional)
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send("ping");
  }
}, 30000);
```

**Python**:
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Progress: {data['progress']:.0%} - {data['stage']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connected")

job_id = "550e8400-e29b-41d4-a716-446655440000"
ws_url = f"ws://localhost:8000/ws/transcription/{job_id}"

ws = websocket.WebSocketApp(
    ws_url,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
```

### Message Types

#### 1. Progress Update

Sent periodically during processing.

```json
{
  "type": "progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "transcription",
  "progress": 0.35
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Message type: `progress` |
| `job_id` | string | Job ID |
| `stage` | string | Current processing stage |
| `progress` | float | Progress (0.0 - 1.0) |

#### 2. Completion

Sent when job completes successfully.

```json
{
  "type": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "filename": "audio.mp3",
    "metadata": { ... },
    "speakers": [ ... ],
    "segments": [ ... ]
  }
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Message type: `completed` |
| `job_id` | string | Job ID |
| `result` | object | Full transcription result |

#### 3. Error

Sent when job fails.

```json
{
  "type": "error",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "OpenAI API error: Rate limit exceeded"
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Message type: `error` |
| `job_id` | string | Job ID |
| `error` | string | Error message |

### Client Messages

Clients can send messages to the server:

#### Ping (Keep-Alive)

```javascript
ws.send("ping");
```

**Response**:
```
pong
```

## Health Check

### Health Check Endpoint

Check if the API is running and properly configured.

**Endpoint**: `GET /health`

**Request Example**:

```bash
curl http://localhost:8000/health
```

**Response** (200 OK):

```json
{
  "status": "healthy",
  "pipeline_path": "../../src/pipeline.py",
  "upload_dir": "./uploads",
  "results_dir": "./results"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status: `healthy` or `unhealthy` |
| `pipeline_path` | string | Path to transcription pipeline |
| `upload_dir` | string | Upload directory path |
| `results_dir` | string | Results directory path |

---

### Root Endpoint

Get API information.

**Endpoint**: `GET /`

**Request Example**:

```bash
curl http://localhost:8000/
```

**Response** (200 OK):

```json
{
  "message": "Audio Transcription API",
  "docs": "/docs",
  "version": "1.0.0"
}
```

## Error Handling

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request (wrong file type, missing parameters) |
| 404 | Not Found | Resource not found (job ID doesn't exist) |
| 413 | Payload Too Large | File exceeds maximum size |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error or job processing failure |
| 503 | Service Unavailable | Too many concurrent jobs |

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors (422):

```json
{
  "detail": [
    {
      "loc": ["body", "file"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `File type not supported` | Unsupported audio format | Use MP3, WAV, M4A, OGG, FLAC, or AAC |
| `File size exceeds maximum` | File too large | Reduce file size or increase `MAX_UPLOAD_SIZE_MB` |
| `Job {id} not found` | Invalid job ID | Check job ID is correct |
| `OpenAI API error: Rate limit exceeded` | API rate limit hit | Wait and retry, or upgrade OpenAI plan |
| `Too many concurrent jobs` | Queue is full | Wait for jobs to complete or increase `MAX_CONCURRENT_JOBS` |

## Rate Limiting

**Current Version**: No rate limiting implemented

**Recommended for Production**:

Implement rate limiting at the application or reverse proxy level:

```python
# Example with slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
@router.post("/upload")
async def upload_audio(...):
    ...
```

Or use Nginx/Cloudflare rate limiting.

## Examples

### Complete Upload & Poll Workflow

**JavaScript**:

```javascript
async function transcribeAudio(file) {
  // 1. Upload file
  const formData = new FormData();
  formData.append('file', file);

  const uploadResponse = await fetch('http://localhost:8000/api/upload', {
    method: 'POST',
    body: formData
  });

  const { job_id } = await uploadResponse.json();
  console.log(`Job ID: ${job_id}`);

  // 2. Connect WebSocket for real-time updates
  const ws = new WebSocket(`ws://localhost:8000/ws/transcription/${job_id}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
      console.log(`Progress: ${(data.progress * 100).toFixed(0)}% - ${data.stage}`);
    } else if (data.type === 'completed') {
      console.log('Transcription complete!', data.result);
      ws.close();
    } else if (data.type === 'error') {
      console.error('Error:', data.error);
      ws.close();
    }
  };

  // 3. Alternatively, poll for status (without WebSocket)
  // const pollStatus = setInterval(async () => {
  //   const statusResponse = await fetch(`http://localhost:8000/api/transcriptions/${job_id}/status`);
  //   const status = await statusResponse.json();
  //
  //   console.log(`Progress: ${(status.progress * 100).toFixed(0)}% - ${status.stage}`);
  //
  //   if (status.status === 'completed') {
  //     clearInterval(pollStatus);
  //     const result = await fetch(`http://localhost:8000/api/transcriptions/${job_id}`);
  //     console.log('Result:', await result.json());
  //   } else if (status.status === 'failed') {
  //     clearInterval(pollStatus);
  //     console.error('Job failed:', status.error);
  //   }
  // }, 2000);
}
```

### Fetch and Display Transcript

**JavaScript**:

```javascript
async function displayTranscript(jobId) {
  const response = await fetch(`http://localhost:8000/api/transcriptions/${jobId}`);
  const data = await response.json();

  if (data.status !== 'completed') {
    console.log('Transcription not ready yet');
    return;
  }

  // Display segments
  data.segments.forEach(segment => {
    const speaker = data.speakers.find(s => s.id === segment.speaker_id);
    console.log(
      `[${formatTime(segment.start)} - ${formatTime(segment.end)}] ` +
      `${speaker.label}: ${segment.text}`
    );
  });
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
```

### Export to SRT Format

**JavaScript**:

```javascript
function exportToSRT(transcriptionData) {
  let srt = '';
  let counter = 1;

  transcriptionData.segments.forEach(segment => {
    const startTime = formatSRTTime(segment.start);
    const endTime = formatSRTTime(segment.end);
    const speaker = transcriptionData.speakers.find(s => s.id === segment.speaker_id);

    srt += `${counter}\n`;
    srt += `${startTime} --> ${endTime}\n`;
    srt += `${speaker.label}: ${segment.text}\n\n`;
    counter++;
  });

  return srt;
}

function formatSRTTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const millis = Math.floor((seconds % 1) * 1000);

  return `${hours.toString().padStart(2, '0')}:` +
         `${minutes.toString().padStart(2, '0')}:` +
         `${secs.toString().padStart(2, '0')},` +
         `${millis.toString().padStart(3, '0')}`;
}
```

### Delete Old Jobs

**Bash**:

```bash
#!/bin/bash
# Delete all completed jobs older than 7 days

# Get all jobs
JOBS=$(curl -s http://localhost:8000/api/transcriptions | jq -r '.jobs[].id')

# Delete each job
for JOB_ID in $JOBS; do
  echo "Deleting job: $JOB_ID"
  curl -X DELETE http://localhost:8000/api/transcriptions/$JOB_ID
done
```

## API Changelog

### Version 1.0.0 (Current)

**Released**: December 2025

**Features**:
- Audio file upload
- Asynchronous transcription processing
- Real-time WebSocket progress updates
- Speaker diarization
- Transcription result retrieval
- Job management (list, delete)
- Health check endpoint

**Known Limitations**:
- No authentication
- No rate limiting
- In-memory job queue (lost on restart)
- No persistent database
- Maximum 100MB file size

### Future Roadmap

**Version 1.1.0** (Planned):
- API key authentication
- Rate limiting
- Persistent job queue (Redis)
- Database for job history (PostgreSQL)
- Batch upload support

**Version 2.0.0** (Planned):
- User accounts and multi-tenancy
- Custom vocabulary support
- Advanced speaker labeling
- Audio quality enhancement
- GPU pipeline integration

---

**Need help?** Check the [interactive API documentation](http://localhost:8000/docs) or refer to the [User Guide](user-guide.md).
