# Level 3 Prompts - Ready for Parallel Execution

These are the **final, executable prompts** to copy-paste into 6 separate Claude windows. Each agent will work independently and produce their deliverables.

---

## 🎯 PROMPT 1: FRONTEND DEVELOPMENT AGENT (Level 3)

```
You are the Frontend Development Agent. Your task is to create a complete React + TypeScript web UI for an audio transcription pipeline.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/
- Create new folder: ui-web/frontend/
- Existing pipeline: audio-transcription-pipeline/ (DO NOT MODIFY)
- Backend will be built by another agent (API contract provided below)

YOUR DELIVERABLES:

1. Initialize React + TypeScript + Vite project:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj"
mkdir -p ui-web/frontend
cd ui-web/frontend
npm create vite@latest . -- --template react-ts
npm install
```

2. Install dependencies:
```bash
npm install react-query zustand react-dropzone wavesurfer.js @tanstack/react-query axios
npm install -D @types/node tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

3. Create these EXACT files:

**src/types/transcription.ts**:
```typescript
export interface TranscriptionJob {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  current_stage?: 'preprocessing' | 'transcription' | 'diarization' | 'alignment';
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  error?: string;
  processing_time_seconds?: number;
}

export interface DiarizedSegment {
  start: number;
  end: number;
  text: string;
  speaker: 'SPEAKER_00' | 'SPEAKER_01' | 'UNKNOWN';
  overlap_ratio?: number;
  interpolated?: boolean;
}

export interface SpeakerTurn {
  speaker: string;
  start: number;
  end: number;
}

export interface TranscriptionMetadata {
  duration: number;
  language: string;
  num_segments: number;
  num_speaker_turns: number;
  unknown_segments_percent: number;
  alignment_algorithm: string;
  processing_time_seconds: number;
}

export interface TranscriptionResult {
  job_id: string;
  metadata: TranscriptionMetadata;
  diarized_segments: DiarizedSegment[];
  speaker_turns: SpeakerTurn[];
}
```

**src/lib/api-client.ts**:
```typescript
import axios from 'axios';
import type { TranscriptionJob, TranscriptionResult } from '../types/transcription';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  uploadFile: async (file: File): Promise<{ file_id: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/api/upload`, formData);
    return response.data;
  },

  startTranscription: async (fileId: string): Promise<{ job_id: string }> => {
    const response = await axios.post(`${API_BASE_URL}/api/transcribe`, { file_id: fileId });
    return response.data;
  },

  getJobStatus: async (jobId: string): Promise<TranscriptionJob> => {
    const response = await axios.get(`${API_BASE_URL}/api/jobs/${jobId}`);
    return response.data;
  },

  getResult: async (jobId: string): Promise<TranscriptionResult> => {
    const response = await axios.get(`${API_BASE_URL}/api/results/${jobId}`);
    return response.data;
  },

  createWebSocket: (jobId: string): WebSocket => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    return new WebSocket(`${wsUrl}/ws/jobs/${jobId}`);
  }
};
```

**src/components/UploadZone.tsx** - File upload with drag & drop
**src/components/ProgressTracker.tsx** - Real-time progress with WebSocket
**src/components/TranscriptViewer.tsx** - Speaker-colored transcript display
**src/App.tsx** - Main application layout

4. Configure Tailwind CSS (tailwind.config.js):
- Use teal (#1abc9c) for THERAPIST (SPEAKER_00)
- Use orange (#e67e22) for CLIENT (SPEAKER_01)
- Use gray (#95a5a6) for UNKNOWN

5. Create .env.local:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

6. Verify build:
```bash
npm run build
```

SUCCESS CRITERIA:
✅ npm run build completes without errors
✅ All TypeScript types defined matching API contract
✅ UploadZone accepts MP3/WAV/M4A files
✅ ProgressTracker shows 4 stages (preprocessing, transcription, diarization, alignment)
✅ TranscriptViewer displays color-coded speakers
✅ WebSocket connection handling implemented

CONSTRAINTS:
- Use ONLY the API contract provided above
- DO NOT modify anything in audio-transcription-pipeline/
- DO NOT start any servers (just build the code)
- File size limit: 100 MB

START NOW. Create all files and verify the build passes.
```

---

## 🎯 PROMPT 2: BACKEND API AGENT (Level 3)

```
You are the Backend API Agent. Your task is to create a FastAPI wrapper around the existing audio transcription pipeline.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/
- Create new folder: ui-web/backend/
- Existing pipeline location: audio-transcription-pipeline/src/
- CRITICAL: Use improved_alignment.py for 100% speaker identification
- DO NOT MODIFY the existing pipeline code

YOUR DELIVERABLES:

1. Create Python virtual environment:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj"
mkdir -p ui-web/backend
cd ui-web/backend
python3 -m venv venv
source venv/bin/activate
```

2. Create requirements.txt:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.5.3
websockets==12.0
```

3. Create these EXACT files:

**app/main.py**:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uuid
from pathlib import Path
from .services.pipeline_service import PipelineService
from .models.schemas import TranscriptionJob, TranscriptionResult

app = FastAPI(title="Audio Transcription API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline_service = PipelineService()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate file size (100 MB max)
    # Save to uploads/ directory
    # Return file_id
    pass

@app.post("/api/transcribe")
async def start_transcription(request: dict):
    # Start background task for transcription
    # Return job_id
    pass

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    # Return current job status with progress
    pass

@app.get("/api/results/{job_id}")
async def get_result(job_id: str):
    # Return complete transcription result
    pass

@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    # Send real-time progress updates
    pass

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

**app/services/pipeline_service.py**:
```python
import sys
from pathlib import Path
import asyncio
from typing import Callable

# Import existing pipeline (DO NOT MODIFY original files)
pipeline_path = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline" / "src"
sys.path.insert(0, str(pipeline_path))

from pipeline import AudioPreprocessor, WhisperTranscriber, AudioTranscriptionPipeline

# Import improved alignment (CRITICAL for 100% accuracy)
improved_alignment_path = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline"
sys.path.insert(0, str(improved_alignment_path))

from improved_alignment import align_speakers_with_segments_improved, interpolate_unknown_speakers

class PipelineService:
    async def process_audio(
        self,
        audio_file_path: Path,
        job_id: str,
        progress_callback: Callable[[str, int], None]
    ):
        # Stage 1: Preprocessing (0-20%)
        progress_callback("preprocessing", 0)
        preprocessor = AudioPreprocessor()
        preprocessed = await asyncio.to_thread(preprocessor.preprocess, str(audio_file_path))
        progress_callback("preprocessing", 20)

        # Stage 2: Transcription (20-50%)
        progress_callback("transcription", 20)
        transcriber = WhisperTranscriber(api_key=os.getenv("OPENAI_API_KEY"))
        segments = await asyncio.to_thread(transcriber.transcribe, preprocessed)
        progress_callback("transcription", 50)

        # Stage 3: Diarization (50-90%)
        progress_callback("diarization", 50)
        # Use pyannote for speaker diarization
        # ... diarization code ...
        progress_callback("diarization", 90)

        # Stage 4: Improved Alignment (90-100%) - CRITICAL
        progress_callback("alignment", 90)
        aligned = align_speakers_with_segments_improved(
            segments=segments,
            turns=speaker_turns,
            overlap_threshold=0.3,  # Lower threshold for better accuracy
            use_nearest_fallback=True,
            debug=False
        )
        aligned = interpolate_unknown_speakers(aligned, debug=False)
        progress_callback("alignment", 100)

        return aligned
```

**app/models/schemas.py**:
```python
from pydantic import BaseModel
from typing import List, Optional, Literal

class TranscriptionJob(BaseModel):
    job_id: str
    status: Literal['queued', 'processing', 'completed', 'failed']
    progress_percentage: int
    current_stage: Optional[Literal['preprocessing', 'transcription', 'diarization', 'alignment']] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

class DiarizedSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str
    overlap_ratio: Optional[float] = None
    interpolated: Optional[bool] = False

class TranscriptionMetadata(BaseModel):
    duration: float
    language: str
    num_segments: int
    num_speaker_turns: int
    unknown_segments_percent: float  # MUST be 0.0
    alignment_algorithm: str  # MUST be "improved_v2"
    processing_time_seconds: float

class TranscriptionResult(BaseModel):
    job_id: str
    metadata: TranscriptionMetadata
    diarized_segments: List[DiarizedSegment]
```

4. Create .env file:
```bash
cat > .env << EOF
OPENAI_API_KEY=your_key_here
HF_TOKEN=your_token_here
BACKEND_PORT=8000
MAX_FILE_SIZE_MB=100
EOF
```

5. Implement complete endpoints with:
- File upload with size validation
- Background task processing
- In-memory job storage (dict)
- WebSocket progress updates
- Error handling

6. Write tests:

**tests/test_pipeline_integration.py**:
```python
import pytest
from pathlib import Path
from app.services.pipeline_service import PipelineService

@pytest.mark.asyncio
async def test_pipeline_achieves_100_percent_identification():
    service = PipelineService()

    # Use existing test audio
    test_audio = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline" / "tests" / "samples" / "test_audio.mp3"

    result = await service.process_audio(
        audio_file_path=test_audio,
        job_id="test-123",
        progress_callback=lambda s, p: print(f"{s}: {p}%")
    )

    # CRITICAL: Verify 0% unknown speakers
    assert result.metadata.unknown_segments_percent == 0.0
    assert result.metadata.alignment_algorithm == "improved_v2"
    assert len(result.diarized_segments) > 0
```

SUCCESS CRITERIA:
✅ FastAPI server starts without errors
✅ All endpoints return correct schema
✅ Pipeline integration uses improved_alignment.py
✅ Test achieves 0% unknown speakers
✅ WebSocket sends real-time progress updates
✅ Health check returns {"status": "healthy"}

CRITICAL REQUIREMENTS:
- MUST use align_speakers_with_segments_improved() with overlap_threshold=0.3
- MUST use interpolate_unknown_speakers()
- MUST achieve unknown_segments_percent = 0.0
- MUST return alignment_algorithm = "improved_v2"

START NOW. Create all files and run the tests.
```

---

## 🎯 PROMPT 3: DEPLOYMENT AGENT (Level 3)

```
You are the Deployment Agent. Your task is to containerize the frontend and backend for local and remote deployment.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web/
- Frontend: React + Vite (built by Frontend Agent)
- Backend: FastAPI (built by Backend Agent)
- Existing pipeline: ../audio-transcription-pipeline/ (must mount as volume)

YOUR DELIVERABLES:

1. Create deployment directory:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"
mkdir -p deployment
```

2. Create **docker-compose.yml** in ui-web/:
```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: ../deployment/Dockerfile.frontend
    ports:
      - "3000:5173"
    volumes:
      - ./frontend/src:/app/src:ro
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: ../deployment/Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app:ro
      - ../audio-transcription-pipeline/src:/app/pipeline_src:ro
      - ../audio-transcription-pipeline/improved_alignment.py:/app/improved_alignment.py:ro
      - backend-uploads:/app/uploads
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HF_TOKEN=${HF_TOKEN}
      - BACKEND_PORT=8000
      - MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB:-100}
      - PYTHONPATH=/app:/app/pipeline_src
    env_file:
      - .env

volumes:
  backend-uploads:
```

3. Create **deployment/Dockerfile.frontend**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

4. Create **deployment/Dockerfile.backend**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Start uvicorn with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

5. Create **.env.example**:
```bash
# Required API Keys
OPENAI_API_KEY=sk-proj-your_openai_key_here
HF_TOKEN=hf_your_huggingface_token_here

# Optional Configuration
BACKEND_PORT=8000
MAX_FILE_SIZE_MB=100
FILE_RETENTION_HOURS=24
RESULT_RETENTION_DAYS=7
```

6. Create **deployment/scripts/setup-local.sh**:
```bash
#!/bin/bash
set -e

echo "========================================="
echo "Audio Transcription UI - Local Setup"
echo "========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker Desktop."
    exit 1
fi
echo "✅ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not installed."
    exit 1
fi
echo "✅ Docker Compose found"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (from https://platform.openai.com/api-keys)"
    echo "   - HF_TOKEN (from https://huggingface.co/settings/tokens)"
    echo ""
    echo "After adding keys, run this script again."
    exit 1
fi

# Validate API keys
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ OPENAI_API_KEY not set in .env file"
    exit 1
fi

if ! grep -q "HF_TOKEN=hf_" .env; then
    echo "❌ HF_TOKEN not set in .env file"
    exit 1
fi
echo "✅ Environment variables configured"

echo ""
echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Health check
echo "Checking backend health..."
if curl -f http://localhost:8000/api/health &> /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    echo "Check logs: docker-compose logs backend"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo ""
```

Make executable:
```bash
chmod +x deployment/scripts/setup-local.sh
```

7. Create **deployment/railway.toml** (for Railway deployment):
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "deployment/Dockerfile.backend"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

8. Create **deployment/fly.toml** (for Fly.io deployment):
```toml
app = "transcription-backend"

[build]
  dockerfile = "deployment/Dockerfile.backend"

[env]
  PORT = "8000"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

9. Test local deployment:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"
./deployment/scripts/setup-local.sh
```

SUCCESS CRITERIA:
✅ docker-compose build completes without errors
✅ docker-compose up starts both services
✅ Backend health check returns 200 OK
✅ Frontend accessible at http://localhost:3000
✅ Backend accessible at http://localhost:8000/docs
✅ Existing pipeline files mounted correctly (not copied)
✅ Environment variables passed to containers
✅ setup-local.sh script works end-to-end

CONSTRAINTS:
- Use volume mounts for existing pipeline (DO NOT COPY)
- Frontend hot-reload must work (mount src/)
- Backend hot-reload must work (mount app/)
- Uploads stored in Docker volume (persistent)

START NOW. Create all files and test the local deployment.
```

---

## 🎯 PROMPT 4: TESTING AGENT (Level 3)

```
You are the Testing Agent. Your task is to create comprehensive tests for the entire system.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web/
- Backend: FastAPI (test with pytest)
- Frontend: React (test with Vitest)
- E2E: Full workflow (test with Playwright)
- Existing pipeline has test audio files you can use

YOUR DELIVERABLES:

1. Backend Tests - Create backend/tests/:

**tests/conftest.py**:
```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_audio_file():
    # Use existing test audio from pipeline
    audio_path = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline" / "tests" / "samples"
    test_files = list(audio_path.glob("*.mp3"))
    if test_files:
        return test_files[0]
    pytest.skip("No test audio files found")
```

**tests/test_api.py**:
```python
import pytest
from pathlib import Path

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_file(client, test_audio_file):
    with open(test_audio_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": (test_audio_file.name, f, "audio/mpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["filename"] == test_audio_file.name

def test_upload_invalid_file(client, tmp_path):
    # Create invalid text file
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("not an audio file")

    with open(invalid_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    assert response.status_code == 422

def test_start_transcription(client, test_audio_file):
    # Upload file first
    with open(test_audio_file, "rb") as f:
        upload_response = client.post(
            "/api/upload",
            files={"file": (test_audio_file.name, f, "audio/mpeg")}
        )
    file_id = upload_response.json()["file_id"]

    # Start transcription
    response = client.post("/api/transcribe", json={"file_id": file_id})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data

def test_get_job_status(client, test_audio_file):
    # Upload and start transcription
    with open(test_audio_file, "rb") as f:
        upload_response = client.post(
            "/api/upload",
            files={"file": (test_audio_file.name, f, "audio/mpeg")}
        )
    file_id = upload_response.json()["file_id"]

    transcribe_response = client.post("/api/transcribe", json={"file_id": file_id})
    job_id = transcribe_response.json()["job_id"]

    # Check status
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] in ["queued", "processing", "completed", "failed"]
```

**tests/test_pipeline_integration.py**:
```python
import pytest
from pathlib import Path
from app.services.pipeline_service import PipelineService

@pytest.mark.asyncio
async def test_pipeline_achieves_zero_unknown_speakers(test_audio_file):
    """CRITICAL TEST: Verify 100% speaker identification"""
    service = PipelineService()

    progress_updates = []
    def track_progress(stage: str, percentage: int):
        progress_updates.append((stage, percentage))

    result = await service.process_audio(
        audio_file_path=test_audio_file,
        job_id="test-100-percent",
        progress_callback=track_progress
    )

    # CRITICAL: Must achieve 0% unknown
    assert result.metadata.unknown_segments_percent == 0.0, \
        f"Expected 0% unknown speakers, got {result.metadata.unknown_segments_percent}%"

    # Verify improved algorithm was used
    assert result.metadata.alignment_algorithm == "improved_v2", \
        f"Expected improved_v2 algorithm, got {result.metadata.alignment_algorithm}"

    # Verify we have segments
    assert len(result.diarized_segments) > 0, "No segments returned"

    # Verify progress updates went through all stages
    stages = [update[0] for update in progress_updates]
    assert "preprocessing" in stages
    assert "transcription" in stages
    assert "diarization" in stages
    assert "alignment" in stages

    # Verify progress reached 100%
    final_progress = progress_updates[-1][1]
    assert final_progress == 100

@pytest.mark.asyncio
async def test_no_unknown_speakers_in_segments(test_audio_file):
    """Verify no segment has speaker='UNKNOWN'"""
    service = PipelineService()

    result = await service.process_audio(
        audio_file_path=test_audio_file,
        job_id="test-no-unknown",
        progress_callback=lambda s, p: None
    )

    unknown_segments = [seg for seg in result.diarized_segments if seg.speaker == "UNKNOWN"]
    assert len(unknown_segments) == 0, \
        f"Found {len(unknown_segments)} segments with UNKNOWN speaker"
```

2. Frontend Tests - Create frontend/src/__tests__/:

**Install Vitest**:
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**vitest.config.ts**:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/__tests__/setup.ts',
  },
});
```

**src/__tests__/setup.ts**:
```typescript
import '@testing-library/jest-dom';
```

**src/__tests__/api-client.test.ts**:
```typescript
import { describe, it, expect, vi } from 'vitest';
import { api } from '../lib/api-client';

describe('API Client', () => {
  it('should upload file successfully', async () => {
    // Mock successful upload
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ file_id: 'test-123', filename: 'test.mp3' }),
      })
    ) as any;

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' });
    const result = await api.uploadFile(file);

    expect(result.file_id).toBe('test-123');
    expect(result.filename).toBe('test.mp3');
  });
});
```

3. E2E Tests - Create tests-e2e/:

**Install Playwright**:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"
mkdir -p tests-e2e
cd tests-e2e
npm init -y
npm install -D @playwright/test
npx playwright install
```

**playwright.config.ts**:
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  timeout: 180000, // 3 minutes for full transcription
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'cd .. && docker-compose up',
    port: 3000,
    reuseExistingServer: true,
  },
});
```

**specs/critical-path.spec.ts**:
```typescript
import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Critical Path: 100% Speaker Identification', () => {
  test('should achieve 0% unknown speakers', async ({ page }) => {
    await page.goto('/');

    // Upload test audio from existing pipeline
    const audioPath = path.join(
      __dirname,
      '../../../audio-transcription-pipeline/tests/samples/test_audio.mp3'
    );

    await page.setInputFiles('input[type="file"]', audioPath);
    await page.click('button:has-text("Transcribe")');

    // Wait for completion (max 3 minutes)
    await expect(page.locator('text=/completed|100%/i')).toBeVisible({
      timeout: 180000
    });

    // CRITICAL: Verify 0% unknown speakers
    const unknownText = await page.locator('[data-testid="unknown-percentage"]').textContent();
    expect(unknownText).toContain('0%');

    // Verify improved_v2 algorithm
    await expect(page.locator('text=/improved_v2/i')).toBeVisible();
  });
});
```

4. Create test runner script:

**scripts/run-all-tests.sh**:
```bash
#!/bin/bash
set -e

echo "========================================="
echo "Running All Tests"
echo "========================================="
echo ""

# Backend tests
echo "📋 Backend Tests..."
cd backend
pytest -v --cov=app
cd ..

# Frontend tests
echo ""
echo "📋 Frontend Tests..."
cd frontend
npm test
cd ..

# E2E tests (requires services running)
echo ""
echo "📋 E2E Tests..."
cd tests-e2e
npx playwright test
cd ..

echo ""
echo "========================================="
echo "✅ All Tests Passed"
echo "========================================="
```

Make executable:
```bash
chmod +x scripts/run-all-tests.sh
```

SUCCESS CRITERIA:
✅ Backend pytest suite passes
✅ Frontend Vitest suite passes
✅ E2E Playwright tests pass
✅ CRITICAL test verifies 0% unknown speakers
✅ Integration test uses existing pipeline test audio
✅ All tests documented with clear assertions

RUN ALL TESTS:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"
./scripts/run-all-tests.sh
```

START NOW. Create all test files and run the test suite.
```

---

## 🎯 PROMPT 5: DOCUMENTATION AGENT (Level 3)

```
You are the Documentation Agent. Your task is to create complete, user-friendly documentation for the entire system.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web/
- System: React frontend + FastAPI backend + Docker deployment
- Key feature: 100% speaker identification (0% unknown)
- Audience: Developers and end-users

YOUR DELIVERABLES:

Create ui-web/docs/ with these files:

1. **README.md** (Project root: ui-web/README.md):
```markdown
# Audio Transcription Web UI

Web interface for audio transcription with **100% speaker identification accuracy**.

## ✨ Features

- 🎙️ Upload audio files (MP3, WAV, M4A, FLAC, OGG)
- 🔄 Real-time progress tracking via WebSocket
- 🎯 **100% speaker identification** (0% unknown segments)
- 🎨 Color-coded transcript (Therapist/Client)
- 📊 Processing metrics and quality stats
- 📥 Export to JSON and HTML

## 🚀 Quick Start

```bash
# 1. Clone and navigate
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"

# 2. Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and HF_TOKEN

# 3. Start services
./deployment/scripts/setup-local.sh

# 4. Open browser
open http://localhost:3000
```

## 📚 Documentation

- [User Guide](docs/user-guide.md) - How to use the application
- [API Reference](docs/api-reference.md) - Backend API documentation
- [Architecture](docs/architecture.md) - System design and components
- [Deployment Guide](docs/deployment-guide.md) - Deploy to production
- [Testing Guide](docs/testing-guide.md) - Run tests

## 🎯 Key Achievement

This system achieves **0% unknown speakers** using an improved alignment algorithm:
- 30% overlap threshold (vs 50% baseline)
- Nearest neighbor fallback for edge cases
- Speaker interpolation for brief gaps

See [improved_alignment.py](../audio-transcription-pipeline/improved_alignment.py) for implementation.

## 🛠️ Tech Stack

**Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
**Backend**: FastAPI + Python 3.11 + OpenAI Whisper + Pyannote
**Deployment**: Docker + Docker Compose
**Testing**: Pytest + Vitest + Playwright

## 📝 License

MIT
```

2. **docs/architecture.md** - Complete system architecture (see previous Level 2 prompt for content)

3. **docs/user-guide.md** - End-user documentation (see previous Level 2 prompt for content)

4. **docs/api-reference.md** - API documentation (see previous Level 2 prompt for content)

5. **docs/deployment-guide.md** - Deployment instructions (see previous Level 2 prompt for content)

6. **docs/local-setup.md** - Developer setup guide (see previous Level 2 prompt for content)

7. **docs/testing-guide.md** - Testing documentation (see previous Level 2 prompt for content)

8. **docs/CHANGELOG.md**:
```markdown
# Changelog

## [1.0.0] - 2024-12-21

### Added
- Initial release of Audio Transcription Web UI
- React + TypeScript frontend with drag-and-drop upload
- FastAPI backend wrapping existing transcription pipeline
- Docker containerization for local and remote deployment
- 100% speaker identification using improved alignment algorithm
- Real-time progress tracking via WebSocket
- Color-coded transcript viewer (Therapist/Client)
- Comprehensive test suite (unit, integration, E2E)
- Complete documentation

### Features
- Upload audio files up to 100 MB
- Support for MP3, WAV, M4A, FLAC, OGG formats
- Four-stage processing: preprocessing, transcription, diarization, alignment
- Export results as JSON or HTML
- Health check endpoint for monitoring

### Technical Achievements
- 0% unknown speakers (100% identification accuracy)
- improved_v2 alignment algorithm integration
- WebSocket real-time updates
- Docker Compose orchestration
```

9. Create **docs/troubleshooting.md**:
```markdown
# Troubleshooting Guide

## Common Issues

### Docker Build Fails

**Error**: `ERROR [internal] load build context`

**Solution**:
```bash
docker system prune -a
docker-compose build --no-cache
```

### Backend Can't Import Pipeline

**Error**: `ModuleNotFoundError: No module named 'pipeline'`

**Cause**: Volume mount to existing pipeline is incorrect.

**Solution**:
Verify in docker-compose.yml:
```yaml
volumes:
  - ../audio-transcription-pipeline/src:/app/pipeline_src:ro
```

Check path exists:
```bash
ls -la ../audio-transcription-pipeline/src
```

### "Unknown Speakers > 0%"

**Error**: Results show unknown_segments_percent > 0.0

**Cause**: Not using improved alignment algorithm.

**Solution**:
Verify backend is calling:
```python
align_speakers_with_segments_improved(
    segments=segments,
    turns=speaker_turns,
    overlap_threshold=0.3,  # MUST be 0.3
    use_nearest_fallback=True,  # MUST be True
    debug=False
)
```

### WebSocket Connection Fails

**Error**: Frontend shows "WebSocket disconnected"

**Solutions**:
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Verify VITE_WS_URL in .env.local: `ws://localhost:8000`
3. Check browser console for CORS errors

### Upload Fails with "413 Request Entity Too Large"

**Cause**: File exceeds 100 MB limit.

**Solutions**:
1. Compress audio file
2. Or increase MAX_FILE_SIZE_MB in .env

### First Run Very Slow

**Cause**: Downloading Pyannote models (~500 MB).

**Solution**: Wait 5-10 minutes on first run. Subsequent runs are fast (models cached).

## Getting Help

Check logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

For more help, see [User Guide](./user-guide.md).
```

10. Create **CONTRIBUTING.md**:
```markdown
# Contributing Guide

## Development Setup

1. Fork the repository
2. Clone your fork
3. Follow [Local Setup Guide](docs/local-setup.md)
4. Create a feature branch: `git checkout -b feature/my-feature`

## Code Standards

**Backend**:
- Follow PEP 8
- Type hints required
- Docstrings for all functions
- pytest for all new features

**Frontend**:
- TypeScript strict mode
- ESLint compliance
- Tests for all components

## Testing

Run full test suite before submitting PR:
```bash
./scripts/run-all-tests.sh
```

## Pull Request Process

1. Update CHANGELOG.md
2. Add tests for new features
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description

## Commit Messages

Format: `type(scope): description`

Examples:
- `feat(backend): add batch processing endpoint`
- `fix(frontend): correct WebSocket reconnection logic`
- `docs(api): update endpoint descriptions`

Types: feat, fix, docs, test, refactor, chore
```

SUCCESS CRITERIA:
✅ All 9 documentation files created
✅ README.md provides clear quick start
✅ User guide covers all features
✅ API reference documents all endpoints
✅ Architecture diagram included
✅ Troubleshooting covers common issues
✅ Deployment guide covers 3+ platforms
✅ All code examples are accurate

START NOW. Create all documentation files with complete, accurate content.
```

---

## 🎯 PROMPT 6: INTEGRATION & COORDINATION AGENT (Level 3)

```
You are the Integration & Coordination Agent. Your task is to validate that all 5 agents' deliverables work together correctly.

CONTEXT:
- Working directory: /Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web/
- Five agents are working in parallel: Frontend, Backend, Deployment, Testing, Documentation
- You will coordinate them and ensure the complete system works end-to-end
- CRITICAL SUCCESS METRIC: System must achieve 0% unknown speakers

YOUR DELIVERABLES:

1. Create **scripts/validate-integration.sh** (see Level 2 PROMPT 6 for complete script)

2. Create **INTEGRATION_STATUS.md** (see Level 2 PROMPT 6 for template)

3. Create **scripts/validate-types.ts** (TypeScript type validation - see Level 2 PROMPT 6)

4. Run integration validation:

```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"

# Step 1: Check all deliverables exist
echo "Checking Frontend deliverables..."
[ -d "frontend/src" ] || echo "❌ Frontend incomplete"
[ -f "frontend/package.json" ] || echo "❌ Frontend package.json missing"

echo "Checking Backend deliverables..."
[ -d "backend/app" ] || echo "❌ Backend incomplete"
[ -f "backend/requirements.txt" ] || echo "❌ Backend requirements.txt missing"

echo "Checking Deployment deliverables..."
[ -f "docker-compose.yml" ] || echo "❌ docker-compose.yml missing"

echo "Checking Testing deliverables..."
[ -d "backend/tests" ] || echo "❌ Backend tests missing"
[ -d "tests-e2e" ] || echo "❌ E2E tests missing"

echo "Checking Documentation deliverables..."
[ -f "docs/architecture.md" ] || echo "❌ Documentation incomplete"

# Step 2: Validate environment configuration
echo ""
echo "Checking environment configuration..."
[ -f ".env" ] || { echo "❌ .env missing"; exit 1; }
grep -q "OPENAI_API_KEY=sk-" .env || { echo "❌ OPENAI_API_KEY not set"; exit 1; }
grep -q "HF_TOKEN=hf_" .env || { echo "❌ HF_TOKEN not set"; exit 1; }

# Step 3: Build services
echo ""
echo "Building services..."
docker-compose build || { echo "❌ Build failed"; exit 1; }

# Step 4: Start services
echo ""
echo "Starting services..."
docker-compose up -d || { echo "❌ Start failed"; exit 1; }

sleep 15  # Wait for services to initialize

# Step 5: Health checks
echo ""
echo "Running health checks..."
curl -f http://localhost:8000/api/health || {
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
}

curl -f http://localhost:3000 || {
    echo "❌ Frontend not accessible"
    docker-compose logs frontend
    exit 1
}

# Step 6: Critical integration test - 100% speaker identification
echo ""
echo "Running CRITICAL TEST: 100% speaker identification..."

# Upload test audio
TEST_AUDIO="../audio-transcription-pipeline/tests/samples/test_audio.mp3"
if [ ! -f "$TEST_AUDIO" ]; then
    echo "❌ Test audio not found"
    exit 1
fi

UPLOAD_RESPONSE=$(curl -s -F "file=@$TEST_AUDIO" http://localhost:8000/api/upload)
FILE_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$FILE_ID" ]; then
    echo "❌ Upload failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi
echo "✅ File uploaded: $FILE_ID"

# Start transcription
TRANSCRIBE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/transcribe \
    -H "Content-Type: application/json" \
    -d "{\"file_id\":\"$FILE_ID\"}")
JOB_ID=$(echo "$TRANSCRIBE_RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo "❌ Transcription start failed"
    echo "$TRANSCRIBE_RESPONSE"
    exit 1
fi
echo "✅ Transcription started: $JOB_ID"

# Poll for completion
echo "Waiting for transcription to complete..."
MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/jobs/$JOB_ID)
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    PROGRESS=$(echo "$STATUS_RESPONSE" | grep -o '"progress_percentage":[0-9]*' | cut -d':' -f2)

    echo "Progress: $PROGRESS% (Status: $STATUS)"

    if [ "$STATUS" = "completed" ]; then
        echo "✅ Transcription completed"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Transcription failed"
        echo "$STATUS_RESPONSE"
        exit 1
    fi

    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Transcription timeout"
    exit 1
fi

# Verify results - CRITICAL: 0% unknown speakers
RESULT_RESPONSE=$(curl -s http://localhost:8000/api/results/$JOB_ID)

UNKNOWN_PCT=$(echo "$RESULT_RESPONSE" | grep -o '"unknown_segments_percent":[0-9.]*' | cut -d':' -f2)
ALGORITHM=$(echo "$RESULT_RESPONSE" | grep -o '"alignment_algorithm":"[^"]*"' | cut -d'"' -f4)
NUM_SEGMENTS=$(echo "$RESULT_RESPONSE" | grep -o '"num_segments":[0-9]*' | cut -d':' -f2)

echo ""
echo "========================================="
echo "CRITICAL VALIDATION RESULTS"
echo "========================================="
echo "Unknown speakers: $UNKNOWN_PCT%"
echo "Alignment algorithm: $ALGORITHM"
echo "Number of segments: $NUM_SEGMENTS"

# CRITICAL CHECKS
if [ "$UNKNOWN_PCT" != "0.0" ] && [ "$UNKNOWN_PCT" != "0" ]; then
    echo ""
    echo "❌ CRITICAL FAILURE: Unknown speakers = $UNKNOWN_PCT% (Expected: 0%)"
    exit 1
fi

if [ "$ALGORITHM" != "improved_v2" ]; then
    echo ""
    echo "❌ CRITICAL FAILURE: Wrong algorithm = $ALGORITHM (Expected: improved_v2)"
    exit 1
fi

if [ "$NUM_SEGMENTS" -lt 10 ]; then
    echo ""
    echo "❌ CRITICAL FAILURE: Too few segments = $NUM_SEGMENTS"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ ALL CRITICAL VALIDATIONS PASSED"
echo "========================================="
echo ""
echo "✅ 100% speaker identification achieved"
echo "✅ improved_v2 algorithm confirmed"
echo "✅ Transcription quality verified"
echo ""
echo "Services running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000/docs"
echo ""
```

Make executable:
```bash
chmod +x scripts/validate-integration.sh
```

5. Run validation:
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/ui-web"
./scripts/validate-integration.sh
```

6. Update **INTEGRATION_STATUS.md** with results:
- Mark each agent's deliverables as ✅ or ❌
- Document any integration issues found
- Record test results (especially critical 0% unknown test)
- Sign off when all validations pass

7. Create final **DEPLOYMENT_CHECKLIST.md**:
```markdown
# Production Deployment Checklist

## Pre-Deployment

- [ ] All tests passing (`./scripts/run-all-tests.sh`)
- [ ] Integration validation passed (`./scripts/validate-integration.sh`)
- [ ] 0% unknown speakers verified in integration test
- [ ] Documentation complete and accurate
- [ ] CHANGELOG.md updated
- [ ] Environment variables configured for production
- [ ] API keys rotated (not using dev keys)

## Deployment

- [ ] Backend deployed to production
- [ ] Frontend deployed to production
- [ ] Environment variables set in production
- [ ] Health check passing in production
- [ ] DNS configured (if using custom domain)
- [ ] SSL/TLS certificates configured
- [ ] CORS origins restricted (not `["*"]`)

## Post-Deployment

- [ ] Smoke test: Upload → Transcribe → View results
- [ ] Verify 0% unknown speakers in production
- [ ] Monitor logs for errors (first 24 hours)
- [ ] Verify WebSocket connections working
- [ ] Test from multiple browsers
- [ ] Performance monitoring configured

## Rollback Plan

If deployment fails:
1. Revert to previous version
2. Check logs: `docker-compose logs`
3. Verify API keys are correct
4. Test locally: `./scripts/validate-integration.sh`
5. Identify root cause before re-deploying

## Success Criteria

✅ All checklist items completed
✅ Production smoke test passed
✅ 0% unknown speakers in production
✅ No errors in logs (24 hours)
```

SUCCESS CRITERIA:
✅ validate-integration.sh runs without errors
✅ All 5 agents' deliverables present and functional
✅ Docker Compose builds and starts successfully
✅ Health checks pass for frontend and backend
✅ End-to-end test completes: upload → process → results
✅ **CRITICAL**: unknown_segments_percent = 0.0
✅ **CRITICAL**: alignment_algorithm = "improved_v2"
✅ INTEGRATION_STATUS.md completed with all sign-offs
✅ DEPLOYMENT_CHECKLIST.md created
✅ Type validation passes (Frontend types match Backend schemas)

START NOW. Run the integration validation and coordinate all agents.
```

---

## 📋 How to Use These Level 3 Prompts

1. **Open 6 separate Claude windows** (or tabs)

2. **Copy-paste each prompt** into a separate window:
   - Window 1: PROMPT 1 (Frontend Agent)
   - Window 2: PROMPT 2 (Backend Agent)
   - Window 3: PROMPT 3 (Deployment Agent)
   - Window 4: PROMPT 4 (Testing Agent)
   - Window 5: PROMPT 5 (Documentation Agent)
   - Window 6: PROMPT 6 (Integration Agent)

3. **Start agents 1-5 first** (let them run in parallel)

4. **Start agent 6 last** (after others have made progress) - this agent will coordinate and validate

5. **Monitor progress** - Each agent will report when they complete deliverables

6. **Integration agent validates** - Agent 6 will verify everything works together and achieve the critical 0% unknown speakers goal

---

**Total estimated completion time**: 15-30 minutes (with all 6 agents running in parallel)

**Critical success metric**: System achieves **0% unknown speakers** using improved_v2 alignment algorithm.
