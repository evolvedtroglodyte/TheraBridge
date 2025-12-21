=================================================================
PARALLEL DEBUGGING PROMPTS - RUN EACH IN SEPARATE CLAUDE WINDOW
=================================================================

Copy each prompt below into a separate Claude Code window and run in parallel.

-------------------------------------------------------------------
PROMPT 1: BACKEND API DATA INVESTIGATION
-------------------------------------------------------------------

# Backend API Data Investigation - Verify Step Messages Being Sent

## Objective
Verify that `ui/server_gpu.py` is setting and returning step messages correctly via the `/api/status/{job_id}` endpoint.

## File Location
`/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/server_gpu.py`

## Current Issue Symptom
Frontend progress bar shows only percentage (e.g., "45%") without the step message, suggesting:
- Backend not setting step messages
- Step field contains empty/null values
- JSON response missing the step field
- Wrong field name in API response

## Current Code State

**Lines 518-526 (Job Initialization):**
```python
# Initialize job
jobs[job_id] = {
    "status": "queued",
    "progress": 0,
    "step": "Initializing GPU pipeline",
    "created_at": datetime.now().isoformat(),
    "file_path": str(temp_path),
    "num_speakers": num_speakers,
    "gpu_type": gpu_status["type"]
}
```

**Lines 540-546 (Local GPU Pipeline Start):**
```python
async def run_local_gpu_pipeline(job_id: str, audio_path: Path, num_speakers: int = 2):
    """Run GPU pipeline locally"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Starting local GPU pipeline"
```

**Lines 601-607 (Vast.ai Pipeline Start):**
```python
async def run_vast_pipeline(job_id: str, audio_path: Path, num_speakers: int = 2):
    """Run GPU pipeline on Vast.ai instance"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = f"Connecting to Vast.ai instance {VAST_INSTANCE_ID}"
```

**Lines 898-903 (Transcription Step):**
```python
elif "GPU Transcription" in line_str or "Transcribing" in line_str:
    jobs[job_id]["progress"] = 80
    jobs[job_id]["step"] = "Transcribing with Whisper large-v3"
elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:
    jobs[job_id]["progress"] = 85
    jobs[job_id]["step"] = "Running pyannote speaker diarization"
```

**Lines 1004-1017 (Status Endpoint):**
```python
@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        step=job.get("step", ""),
        error=job.get("error")
    )
```

## Debugging Strategy
Add comprehensive print statements at all locations where `jobs[job_id]["step"]` is modified, and add logging in the status endpoint to verify what JSON is actually being returned to the frontend.

## Implementation Steps

### Step 1: Add Logging to Job Initialization (After Line 526)

Add a print statement right after job creation:

```python
# Use Edit tool
File: /Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/server_gpu.py

Find:
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "step": "Initializing GPU pipeline",
        "created_at": datetime.now().isoformat(),
        "file_path": str(temp_path),
        "num_speakers": num_speakers,
        "gpu_type": gpu_status["type"]
    }

    # Start processing in background

Replace with:
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "step": "Initializing GPU pipeline",
        "created_at": datetime.now().isoformat(),
        "file_path": str(temp_path),
        "num_speakers": num_speakers,
        "gpu_type": gpu_status["type"]
    }
    print(f"[BACKEND LOG] Job {job_id} initialized - step: '{jobs[job_id]['step']}'")

    # Start processing in background
```

### Step 2: Add Logging to Local GPU Pipeline Steps (After Line 546)

```python
Find:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Starting local GPU pipeline"

        output_file = RESULTS_DIR / f"{job_id}.json"

Replace with:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Starting local GPU pipeline"
        print(f"[BACKEND LOG] Job {job_id} - progress: {jobs[job_id]['progress']}%, step: '{jobs[job_id]['step']}'")

        output_file = RESULTS_DIR / f"{job_id}.json"
```

### Step 3: Add Logging to Vast.ai Pipeline Steps (After Line 607)

```python
Find:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = f"Connecting to Vast.ai instance {VAST_INSTANCE_ID}"

        # Get SSH connection details using vastai ssh-url

Replace with:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = f"Connecting to Vast.ai instance {VAST_INSTANCE_ID}"
        print(f"[BACKEND LOG] Job {job_id} - progress: {jobs[job_id]['progress']}%, step: '{jobs[job_id]['step']}'")

        # Get SSH connection details using vastai ssh-url
```

### Step 4: Add Logging to Upload Progress (After Line 664)

```python
Find:
        jobs[job_id]["progress"] = 30
        jobs[job_id]["step"] = "Transferring audio file to GPU instance"

        # Retry logic for SSH connection (handles rate limiting)

Replace with:
        jobs[job_id]["progress"] = 30
        jobs[job_id]["step"] = "Transferring audio file to GPU instance"
        print(f"[BACKEND LOG] Job {job_id} - progress: {jobs[job_id]['progress']}%, step: '{jobs[job_id]['step']}'")

        # Retry logic for SSH connection (handles rate limiting)
```

### Step 5: Add Logging to Transcription Step (After Line 900)

```python
Find:
            elif "GPU Transcription" in line_str or "Transcribing" in line_str:
                jobs[job_id]["progress"] = 80
                jobs[job_id]["step"] = "Transcribing with Whisper large-v3"
            elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:

Replace with:
            elif "GPU Transcription" in line_str or "Transcribing" in line_str:
                jobs[job_id]["progress"] = 80
                jobs[job_id]["step"] = "Transcribing with Whisper large-v3"
                print(f"[BACKEND LOG] Job {job_id} - progress: {jobs[job_id]['progress']}%, step: '{jobs[job_id]['step']}'")
            elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:
```

### Step 6: Add Logging to Diarization Step (After Line 903)

```python
Find:
            elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:
                jobs[job_id]["progress"] = 85
                jobs[job_id]["step"] = "Running pyannote speaker diarization"
            elif "Speaker Alignment" in line_str or "Aligning" in line_str:

Replace with:
            elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:
                jobs[job_id]["progress"] = 85
                jobs[job_id]["step"] = "Running pyannote speaker diarization"
                print(f"[BACKEND LOG] Job {job_id} - progress: {jobs[job_id]['progress']}%, step: '{jobs[job_id]['step']}'")
            elif "Speaker Alignment" in line_str or "Aligning" in line_str:
```

### Step 7: Add Logging to Status Endpoint Response (Lines 1010-1017)

```python
Find:
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        step=job.get("step", ""),
        error=job.get("error")
    )

Replace with:
    job = jobs[job_id]
    response = JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        step=job.get("step", ""),
        error=job.get("error")
    )
    print(f"[BACKEND LOG] Returning status for {job_id}: progress={response.progress}%, step='{response.step}', status={response.status}")
    return response
```

## Testing Procedure

1. **Start the server:**
   ```bash
   cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline"
   python3 ui/server_gpu.py
   ```

2. **Open browser and upload a file:**
   - Navigate to http://localhost:8000
   - Select and upload an audio file

3. **Watch the terminal output:**
   - Look for `[BACKEND LOG]` entries
   - Observe what step messages are being set
   - Observe what the status endpoint returns

## Expected Output If Working

```
[BACKEND LOG] Job abc-123-def initialized - step: 'Initializing GPU pipeline'
[BACKEND LOG] Job abc-123-def - progress: 10%, step: 'Connecting to Vast.ai instance 12345'
[BACKEND LOG] Returning status for abc-123-def: progress=10%, step='Connecting to Vast.ai instance 12345', status=processing
[BACKEND LOG] Job abc-123-def - progress: 30%, step: 'Transferring audio file to GPU instance'
[BACKEND LOG] Returning status for abc-123-def: progress=30%, step='Transferring audio file to GPU instance', status=processing
[BACKEND LOG] Job abc-123-def - progress: 80%, step: 'Transcribing with Whisper large-v3'
[BACKEND LOG] Returning status for abc-123-def: progress=80%, step='Transcribing with Whisper large-v3', status=processing
[BACKEND LOG] Job abc-123-def - progress: 85%, step: 'Running pyannote speaker diarization'
[BACKEND LOG] Returning status for abc-123-def: progress=85%, step='Running pyannote speaker diarization', status=processing
```

## Expected Output If Broken

**Scenario 1: Step messages never set**
```
[BACKEND LOG] Job abc-123-def initialized - step: ''
[BACKEND LOG] Returning status for abc-123-def: progress=10%, step='', status=processing
```

**Scenario 2: Step messages set but endpoint returns empty**
```
[BACKEND LOG] Job abc-123-def - progress: 80%, step: 'Transcribing with Whisper large-v3'
[BACKEND LOG] Returning status for abc-123-def: progress=80%, step='', status=processing
```

**Scenario 3: No status endpoint calls (polling not working)**
```
[BACKEND LOG] Job abc-123-def initialized - step: 'Initializing GPU pipeline'
[BACKEND LOG] Job abc-123-def - progress: 10%, step: 'Connecting to Vast.ai instance 12345'
# ... but NO "Returning status" logs
```

## What This Tells Us

- **If you see step messages in both assignment AND endpoint logs:** Backend is working correctly. Issue is in frontend receiving/processing the data.

- **If you see step messages in assignments but empty in endpoint logs:** Issue with `job.get("step", "")` or JobStatus model serialization.

- **If you see empty step messages in assignments:** Issue with step assignment logic, possibly wrong code path being executed.

- **If you see NO endpoint logs:** Frontend polling is not working or calling wrong endpoint.

-------------------------------------------------------------------
PROMPT 2: FRONTEND NETWORK LAYER ANALYSIS
-------------------------------------------------------------------

# Frontend Network Layer Analysis - Verify API Response Reception

## Objective
Verify that `ui/app.js` `pollProcessingStatus()` function correctly receives step messages from the backend API response.

## File Location
`/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/app.js`

## Current Issue Symptom
UI not updating despite implemented fixes, suggesting:
- `statusData.step` is undefined or null
- API response is missing the `step` field
- Polling function not being called
- JSON parsing issues

## Current Code State

**Lines 288-338 (pollProcessingStatus function):**
```javascript
async function pollProcessingStatus() {
    if (!currentJobId || !state.isProcessing) {
        return;
    }

    try {
        const statusResponse = await fetch(
            `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`
        );

        if (!statusResponse.ok) {
            throw new Error('Failed to get status');
        }

        const statusData = await statusResponse.json();

        // Update UI with current status
        updateProcessingUI(statusData);

        // Check if processing is complete
        if (statusData.status === 'completed') {
            clearInterval(statusPollInterval);
            await fetchAndDisplayResults();
        } else if (statusData.status === 'failed') {
            clearInterval(statusPollInterval);
            state.isProcessing = false;
            showError('Processing failed: ' + (statusData.error || 'Unknown error'));

            // Reset to upload view
            setTimeout(() => {
                elements.processingSection.style.display = 'none';
                elements.uploadSection.style.display = 'block';
            }, 3000);
        } else {
            // Continue polling
            statusPollInterval = setTimeout(pollProcessingStatus, API_CONFIG.pollInterval);
        }

    } catch (error) {
        console.error('Status polling error:', error);
        clearInterval(statusPollInterval);
        state.isProcessing = false;
        showError('Lost connection to server. Please check if the server is still running.');

        // Reset to upload view
        setTimeout(() => {
            elements.processingSection.style.display = 'none';
            elements.uploadSection.style.display = 'block';
        }, 3000);
    }
}
```

## Debugging Strategy
Add comprehensive console logging immediately after receiving and parsing the API response to verify that `statusData.step` is present and contains the expected backend messages.

## Implementation Steps

### Step 1: Add Network Response Logging (After Line 302)

Use the Edit tool to add logging right after JSON parsing:

```javascript
Find:
        const statusData = await statusResponse.json();

        // Update UI with current status
        updateProcessingUI(statusData);

Replace with:
        const statusData = await statusResponse.json();

        // [DEBUG] Log complete API response
        const timestamp = new Date().toISOString();
        console.log(`[NETWORK ${timestamp}] Status API Response:`, JSON.stringify(statusData, null, 2));
        console.log(`[NETWORK ${timestamp}] job_id: ${currentJobId}`);
        console.log(`[NETWORK ${timestamp}] statusData.status: ${statusData.status}`);
        console.log(`[NETWORK ${timestamp}] statusData.progress: ${statusData.progress}`);
        console.log(`[NETWORK ${timestamp}] statusData.step: "${statusData.step}"`);
        console.log(`[NETWORK ${timestamp}] statusData.step type: ${typeof statusData.step}`);
        console.log(`[NETWORK ${timestamp}] statusData.step is null/undefined: ${statusData.step == null}`);

        // Update UI with current status
        updateProcessingUI(statusData);
```

### Step 2: Add Polling Start Confirmation (After Line 270)

Add logging when polling begins:

```javascript
Find:
        // 2. Start polling for status updates
        pollProcessingStatus();

    } catch (error) {

Replace with:
        // 2. Start polling for status updates
        console.log(`[NETWORK] Starting status polling for job: ${currentJobId}`);
        console.log(`[NETWORK] Poll interval: ${API_CONFIG.pollInterval}ms`);
        console.log(`[NETWORK] Status endpoint: ${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`);
        pollProcessingStatus();

    } catch (error) {
```

### Step 3: Add Fetch Error Detailed Logging (After Line 298)

```javascript
Find:
        if (!statusResponse.ok) {
            throw new Error('Failed to get status');
        }

Replace with:
        if (!statusResponse.ok) {
            console.error(`[NETWORK ERROR] Status fetch failed: ${statusResponse.status} ${statusResponse.statusText}`);
            console.error(`[NETWORK ERROR] URL: ${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`);
            throw new Error('Failed to get status');
        }
```

### Step 4: Add Polling Continuation Logging (After Line 323)

```javascript
Find:
        } else {
            // Continue polling
            statusPollInterval = setTimeout(pollProcessingStatus, API_CONFIG.pollInterval);
        }

Replace with:
        } else {
            // Continue polling
            console.log(`[NETWORK] Continuing to poll (status: ${statusData.status}, progress: ${statusData.progress}%)`);
            statusPollInterval = setTimeout(pollProcessingStatus, API_CONFIG.pollInterval);
        }
```

## Testing Procedure

1. **Start the backend server:**
   ```bash
   cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline"
   python3 ui/server_gpu.py
   ```

2. **Open browser with DevTools:**
   - Navigate to http://localhost:8000
   - Press F12 to open DevTools
   - Click on the **Console** tab
   - Clear the console (click trash icon)

3. **Upload an audio file:**
   - Select a file and click upload
   - Watch the Console tab for `[NETWORK]` logs

4. **Observe the output:**
   - Look for the polling start message
   - Look for status API responses every 1 second
   - Check if `statusData.step` is present and has values

## Expected Output If Working

```javascript
[NETWORK] Starting status polling for job: abc-123-def-456
[NETWORK] Poll interval: 1000ms
[NETWORK] Status endpoint: http://localhost:8000/api/status/abc-123-def-456

[NETWORK 2025-12-21T10:30:15.123Z] Status API Response: {
  "job_id": "abc-123-def-456",
  "status": "processing",
  "progress": 10,
  "step": "Connecting to Vast.ai instance 12345",
  "error": null
}
[NETWORK 2025-12-21T10:30:15.123Z] job_id: abc-123-def-456
[NETWORK 2025-12-21T10:30:15.123Z] statusData.status: processing
[NETWORK 2025-12-21T10:30:15.123Z] statusData.progress: 10
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step: "Connecting to Vast.ai instance 12345"
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step type: string
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step is null/undefined: false
[NETWORK] Continuing to poll (status: processing, progress: 10%)

[NETWORK 2025-12-21T10:30:16.234Z] Status API Response: {
  "job_id": "abc-123-def-456",
  "status": "processing",
  "progress": 80,
  "step": "Transcribing with Whisper large-v3",
  "error": null
}
[NETWORK 2025-12-21T10:30:16.234Z] statusData.step: "Transcribing with Whisper large-v3"
...
```

## Expected Output If Broken

**Scenario 1: Missing step field**
```javascript
[NETWORK 2025-12-21T10:30:15.123Z] Status API Response: {
  "job_id": "abc-123-def-456",
  "status": "processing",
  "progress": 10,
  "error": null
}
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step: "undefined"
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step type: undefined
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step is null/undefined: true
```

**Scenario 2: Empty step field**
```javascript
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step: ""
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step type: string
[NETWORK 2025-12-21T10:30:15.123Z] statusData.step is null/undefined: false
```

**Scenario 3: Polling not happening**
```javascript
[NETWORK] Starting status polling for job: abc-123-def-456
# ... then no more NETWORK logs (polling stopped or never started)
```

**Scenario 4: Network error**
```javascript
[NETWORK ERROR] Status fetch failed: 404 Not Found
[NETWORK ERROR] URL: http://localhost:8000/api/status/abc-123-def-456
Status polling error: Error: Failed to get status
```

## What This Tells Us

- **If you see `statusData.step` with correct messages:** Network layer is working. Issue is in the JavaScript functions that process this data (check Prompt 3).

- **If `statusData.step` is undefined:** Backend is not including `step` in the JSON response, or using a different field name (check Prompt 1).

- **If `statusData.step` is empty string (""):** Backend is setting step but with empty values (check Prompt 1).

- **If no polling logs appear:** Polling is not starting - check if `currentJobId` is being set correctly, or if `uploadAndProcess()` is failing before polling starts.

- **If you see 404 errors:** Wrong endpoint URL, or backend not running.

-------------------------------------------------------------------
PROMPT 3: JAVASCRIPT FUNCTION FLOW TRACING
-------------------------------------------------------------------

# JavaScript Function Flow Tracing - Trace Execution Through All Functions

## Objective
Trace the complete execution flow through `detectCurrentStepFromMessage()`, `updateStepStatus()`, `updateProcessingUI()`, and `updateProgress()` to identify exactly where the logic fails or returns early.

## File Location
`/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/app.js`

## Current Issue Symptom
Functions are implemented with correct logic but UI not updating, suggesting:
- Functions not being called at all
- Wrong parameters being passed
- Logic errors in conditionals (early returns, wrong comparisons)
- DOM manipulation happening but being overwritten

## Current Code State

**Lines 340-371 (detectCurrentStepFromMessage):**
```javascript
function detectCurrentStepFromMessage(message) {
    if (!message) return null;

    const msgLower = message.toLowerCase();

    // Step 1: Upload/Initialization (keywords: upload, initializing, connecting, transferring)
    if (msgLower.includes('upload') || msgLower.includes('initializ') ||
        msgLower.includes('connect') || msgLower.includes('transfer')) {
        return 'step1';
    }

    // Step 2: Transcription (keywords: transcrib, preprocessing, whisper)
    if (msgLower.includes('transcrib') || msgLower.includes('preprocess') ||
        msgLower.includes('whisper')) {
        return 'step2';
    }

    // Step 3: Diarization (keywords: diariz, speaker, pyannote)
    if (msgLower.includes('diariz') || msgLower.includes('speaker') ||
        msgLower.includes('pyannote')) {
        return 'step3';
    }

    // Step 4: Finalization (keywords: align, finaliz, download, preparing, complete)
    if (msgLower.includes('align') || msgLower.includes('finaliz') ||
        msgLower.includes('download') || msgLower.includes('preparing') ||
        msgLower.includes('complete')) {
        return 'step4';
    }

    return null;
}
```

**Lines 373-389 (updateStepStatus):**
```javascript
function updateStepStatus(stepElement, state, message = null) {
    const statusElement = stepElement.querySelector('.step-status');

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        stepElement.classList.add('active');
        // Display actual backend message if provided, otherwise use generic status
        statusElement.textContent = message || 'Processing...';
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
    } else {
        // waiting state
        statusElement.textContent = 'Waiting...';
    }
}
```

**Lines 391-423 (updateProcessingUI):**
```javascript
function updateProcessingUI(statusData) {
    // Update progress bar with step message
    const progress = statusData.progress || 0;
    updateProgress(progress, statusData.step);

    // Detect current step from backend message
    const currentStepId = detectCurrentStepFromMessage(statusData.step);

    if (!currentStepId) {
        // No step detected, keep all waiting
        return;
    }

    // Map step IDs to step numbers
    const stepOrder = ['step1', 'step2', 'step3', 'step4'];
    const currentStepIndex = stepOrder.indexOf(currentStepId);

    // Update each step indicator
    stepOrder.forEach((stepId, index) => {
        const stepElement = elements.steps[stepId];

        if (index < currentStepIndex) {
            // Previous steps - mark as completed
            updateStepStatus(stepElement, 'completed');
        } else if (index === currentStepIndex) {
            // Current step - mark as active with backend message
            updateStepStatus(stepElement, 'active', statusData.step);
        } else {
            // Future steps - waiting
            updateStepStatus(stepElement, 'waiting');
        }
    });
}
```

**Lines 481-491 (updateProgress):**
```javascript
function updateProgress(percent, stepMessage = null) {
    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        elements.progressText.innerHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
    } else {
        elements.progressText.textContent = `${percent}%`;
    }
}
```

## Debugging Strategy
Add comprehensive console logging at function entry/exit points, before all conditionals, and at all state changes to create a complete execution trace.

## Implementation Steps

### Step 1: Instrument detectCurrentStepFromMessage (Lines 340-371)

```javascript
Find:
function detectCurrentStepFromMessage(message) {
    if (!message) return null;

    const msgLower = message.toLowerCase();

    // Step 1: Upload/Initialization (keywords: upload, initializing, connecting, transferring)
    if (msgLower.includes('upload') || msgLower.includes('initializ') ||
        msgLower.includes('connect') || msgLower.includes('transfer')) {
        return 'step1';
    }

    // Step 2: Transcription (keywords: transcrib, preprocessing, whisper)
    if (msgLower.includes('transcrib') || msgLower.includes('preprocess') ||
        msgLower.includes('whisper')) {
        return 'step2';
    }

    // Step 3: Diarization (keywords: diariz, speaker, pyannote)
    if (msgLower.includes('diariz') || msgLower.includes('speaker') ||
        msgLower.includes('pyannote')) {
        return 'step3';
    }

    // Step 4: Finalization (keywords: align, finaliz, download, preparing, complete)
    if (msgLower.includes('align') || msgLower.includes('finaliz') ||
        msgLower.includes('download') || msgLower.includes('preparing') ||
        msgLower.includes('complete')) {
        return 'step4';
    }

    return null;
}

Replace with:
function detectCurrentStepFromMessage(message) {
    console.log(`[TRACE] detectCurrentStepFromMessage() called with message: "${message}"`);
    console.log(`[TRACE] message type: ${typeof message}, is null/undefined: ${message == null}`);

    if (!message) {
        console.log(`[TRACE] detectCurrentStepFromMessage() returning null (no message)`);
        return null;
    }

    const msgLower = message.toLowerCase();
    console.log(`[TRACE] msgLower: "${msgLower}"`);

    // Step 1: Upload/Initialization (keywords: upload, initializing, connecting, transferring)
    if (msgLower.includes('upload') || msgLower.includes('initializ') ||
        msgLower.includes('connect') || msgLower.includes('transfer')) {
        console.log(`[TRACE] detectCurrentStepFromMessage() matched Step 1 - returning 'step1'`);
        return 'step1';
    }

    // Step 2: Transcription (keywords: transcrib, preprocessing, whisper)
    if (msgLower.includes('transcrib') || msgLower.includes('preprocess') ||
        msgLower.includes('whisper')) {
        console.log(`[TRACE] detectCurrentStepFromMessage() matched Step 2 - returning 'step2'`);
        return 'step2';
    }

    // Step 3: Diarization (keywords: diariz, speaker, pyannote)
    if (msgLower.includes('diariz') || msgLower.includes('speaker') ||
        msgLower.includes('pyannote')) {
        console.log(`[TRACE] detectCurrentStepFromMessage() matched Step 3 - returning 'step3'`);
        return 'step3';
    }

    // Step 4: Finalization (keywords: align, finaliz, download, preparing, complete)
    if (msgLower.includes('align') || msgLower.includes('finaliz') ||
        msgLower.includes('download') || msgLower.includes('preparing') ||
        msgLower.includes('complete')) {
        console.log(`[TRACE] detectCurrentStepFromMessage() matched Step 4 - returning 'step4'`);
        return 'step4';
    }

    console.log(`[TRACE] detectCurrentStepFromMessage() returning null (no keyword matches)`);
    return null;
}
```

### Step 2: Instrument updateStepStatus (Lines 373-389)

```javascript
Find:
function updateStepStatus(stepElement, state, message = null) {
    const statusElement = stepElement.querySelector('.step-status');

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        stepElement.classList.add('active');
        // Display actual backend message if provided, otherwise use generic status
        statusElement.textContent = message || 'Processing...';
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
    } else {
        // waiting state
        statusElement.textContent = 'Waiting...';
    }
}

Replace with:
function updateStepStatus(stepElement, state, message = null) {
    console.log(`[TRACE] updateStepStatus() called:`, {
        stepElementId: stepElement.id,
        state: state,
        message: message,
        messageType: typeof message
    });

    const statusElement = stepElement.querySelector('.step-status');
    console.log(`[TRACE] statusElement found: ${statusElement != null}, current text: "${statusElement?.textContent}"`);

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        console.log(`[TRACE] Setting ${stepElement.id} to ACTIVE with message: "${message}"`);
        stepElement.classList.add('active');
        // Display actual backend message if provided, otherwise use generic status
        statusElement.textContent = message || 'Processing...';
        console.log(`[TRACE] After update - statusElement.textContent: "${statusElement.textContent}"`);
    } else if (state === 'completed') {
        console.log(`[TRACE] Setting ${stepElement.id} to COMPLETED`);
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
    } else {
        console.log(`[TRACE] Setting ${stepElement.id} to WAITING`);
        // waiting state
        statusElement.textContent = 'Waiting...';
    }
}
```

### Step 3: Instrument updateProcessingUI (Lines 391-423)

```javascript
Find:
function updateProcessingUI(statusData) {
    // Update progress bar with step message
    const progress = statusData.progress || 0;
    updateProgress(progress, statusData.step);

    // Detect current step from backend message
    const currentStepId = detectCurrentStepFromMessage(statusData.step);

    if (!currentStepId) {
        // No step detected, keep all waiting
        return;
    }

    // Map step IDs to step numbers
    const stepOrder = ['step1', 'step2', 'step3', 'step4'];
    const currentStepIndex = stepOrder.indexOf(currentStepId);

    // Update each step indicator
    stepOrder.forEach((stepId, index) => {
        const stepElement = elements.steps[stepId];

        if (index < currentStepIndex) {
            // Previous steps - mark as completed
            updateStepStatus(stepElement, 'completed');
        } else if (index === currentStepIndex) {
            // Current step - mark as active with backend message
            updateStepStatus(stepElement, 'active', statusData.step);
        } else {
            // Future steps - waiting
            updateStepStatus(stepElement, 'waiting');
        }
    });
}

Replace with:
function updateProcessingUI(statusData) {
    console.log(`[TRACE] ========================================`);
    console.log(`[TRACE] updateProcessingUI() called with:`, {
        status: statusData.status,
        progress: statusData.progress,
        step: statusData.step,
        stepType: typeof statusData.step
    });

    // Update progress bar with step message
    const progress = statusData.progress || 0;
    console.log(`[TRACE] Calling updateProgress(${progress}, "${statusData.step}")`);
    updateProgress(progress, statusData.step);

    // Detect current step from backend message
    console.log(`[TRACE] Calling detectCurrentStepFromMessage("${statusData.step}")`);
    const currentStepId = detectCurrentStepFromMessage(statusData.step);
    console.log(`[TRACE] detectCurrentStepFromMessage returned: ${currentStepId}`);

    if (!currentStepId) {
        // No step detected, keep all waiting
        console.log(`[TRACE] ⚠️ No step detected! Exiting updateProcessingUI early.`);
        console.log(`[TRACE] This means the backend message didn't match any keywords.`);
        return;
    }

    // Map step IDs to step numbers
    const stepOrder = ['step1', 'step2', 'step3', 'step4'];
    const currentStepIndex = stepOrder.indexOf(currentStepId);
    console.log(`[TRACE] currentStepIndex = ${currentStepIndex}`);

    // Update each step indicator
    console.log(`[TRACE] Looping through steps...`);
    stepOrder.forEach((stepId, index) => {
        const stepElement = elements.steps[stepId];
        console.log(`[TRACE] Processing ${stepId} (index ${index})`);

        if (index < currentStepIndex) {
            // Previous steps - mark as completed
            console.log(`[TRACE] ${stepId}: index(${index}) < currentStepIndex(${currentStepIndex}) → completed`);
            updateStepStatus(stepElement, 'completed');
        } else if (index === currentStepIndex) {
            // Current step - mark as active with backend message
            console.log(`[TRACE] ${stepId}: index(${index}) === currentStepIndex(${currentStepIndex}) → active`);
            updateStepStatus(stepElement, 'active', statusData.step);
        } else {
            // Future steps - waiting
            console.log(`[TRACE] ${stepId}: index(${index}) > currentStepIndex(${currentStepIndex}) → waiting`);
            updateStepStatus(stepElement, 'waiting');
        }
    });
    console.log(`[TRACE] ========================================`);
}
```

### Step 4: Instrument updateProgress (Lines 481-491)

```javascript
Find:
function updateProgress(percent, stepMessage = null) {
    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        elements.progressText.innerHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
    } else {
        elements.progressText.textContent = `${percent}%`;
    }
}

Replace with:
function updateProgress(percent, stepMessage = null) {
    console.log(`[TRACE] updateProgress() called: percent=${percent}, stepMessage="${stepMessage}"`);
    console.log(`[TRACE] stepMessage type: ${typeof stepMessage}, is null/undefined: ${stepMessage == null}`);

    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        console.log(`[TRACE] stepMessage exists, setting innerHTML with message`);
        const newHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
        console.log(`[TRACE] New innerHTML: "${newHTML}"`);
        elements.progressText.innerHTML = newHTML;
        console.log(`[TRACE] After update - progressText.innerHTML: "${elements.progressText.innerHTML}"`);
    } else {
        console.log(`[TRACE] No stepMessage, setting textContent to percentage only`);
        elements.progressText.textContent = `${percent}%`;
    }
}
```

## Testing Procedure

1. **Start backend server:**
   ```bash
   cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline"
   python3 ui/server_gpu.py
   ```

2. **Open browser with DevTools:**
   - Navigate to http://localhost:8000
   - Press F12 → Console tab
   - Clear console

3. **Upload audio file and observe trace:**
   - Upload a file
   - Watch the `[TRACE]` logs in real-time
   - Look for the complete execution path

4. **Analyze the trace:**
   - Verify functions are called in correct order
   - Check parameter values
   - Look for early returns or unexpected values

## Expected Output If Working

```javascript
[TRACE] ========================================
[TRACE] updateProcessingUI() called with: {status: "processing", progress: 80, step: "Transcribing with Whisper large-v3", stepType: "string"}
[TRACE] Calling updateProgress(80, "Transcribing with Whisper large-v3")
[TRACE] updateProgress() called: percent=80, stepMessage="Transcribing with Whisper large-v3"
[TRACE] stepMessage type: string, is null/undefined: false
[TRACE] stepMessage exists, setting innerHTML with message
[TRACE] New innerHTML: "80%<br><small style="font-size: 0.85em; opacity: 0.9;">Transcribing with Whisper large-v3</small>"
[TRACE] After update - progressText.innerHTML: "80%<br><small style="font-size: 0.85em; opacity: 0.9;">Transcribing with Whisper large-v3</small>"
[TRACE] Calling detectCurrentStepFromMessage("Transcribing with Whisper large-v3")
[TRACE] detectCurrentStepFromMessage() called with message: "Transcribing with Whisper large-v3"
[TRACE] message type: string, is null/undefined: false
[TRACE] msgLower: "transcribing with whisper large-v3"
[TRACE] detectCurrentStepFromMessage() matched Step 2 - returning 'step2'
[TRACE] detectCurrentStepFromMessage returned: step2
[TRACE] currentStepIndex = 1
[TRACE] Looping through steps...
[TRACE] Processing step1 (index 0)
[TRACE] step1: index(0) < currentStepIndex(1) → completed
[TRACE] updateStepStatus() called: {stepElementId: "step1", state: "completed", message: null}
[TRACE] statusElement found: true, current text: "Waiting..."
[TRACE] Setting step1 to COMPLETED
[TRACE] Processing step2 (index 1)
[TRACE] step2: index(1) === currentStepIndex(1) → active
[TRACE] updateStepStatus() called: {stepElementId: "step2", state: "active", message: "Transcribing with Whisper large-v3"}
[TRACE] statusElement found: true, current text: "Waiting..."
[TRACE] Setting step2 to ACTIVE with message: "Transcribing with Whisper large-v3"
[TRACE] After update - statusElement.textContent: "Transcribing with Whisper large-v3"
[TRACE] Processing step3 (index 2)
[TRACE] step3: index(2) > currentStepIndex(1) → waiting
[TRACE] Processing step4 (index 3)
[TRACE] step4: index(3) > currentStepIndex(1) → waiting
[TRACE] ========================================
```

## Expected Output If Broken

**Scenario 1: Early return due to no step match**
```javascript
[TRACE] updateProcessingUI() called with: {status: "processing", progress: 80, step: "Some unmatched message"}
[TRACE] detectCurrentStepFromMessage() called with message: "Some unmatched message"
[TRACE] msgLower: "some unmatched message"
[TRACE] detectCurrentStepFromMessage() returning null (no keyword matches)
[TRACE] detectCurrentStepFromMessage returned: null
[TRACE] ⚠️ No step detected! Exiting updateProcessingUI early.
```

**Scenario 2: stepMessage is null/undefined**
```javascript
[TRACE] updateProgress() called: percent=80, stepMessage="undefined"
[TRACE] stepMessage type: undefined, is null/undefined: true
[TRACE] No stepMessage, setting textContent to percentage only
```

**Scenario 3: Function not called at all**
```javascript
# No [TRACE] logs appear → updateProcessingUI never called
```

**Scenario 4: querySelector returns null**
```javascript
[TRACE] updateStepStatus() called: {stepElementId: "step2", state: "active", message: "..."}
[TRACE] statusElement found: false, current text: "undefined"
# DOM element doesn't exist!
```

## What This Tells Us

- **If trace shows complete execution with correct values:** Functions are working, issue is DOM-related (check Prompt 4).

- **If early return at detectCurrentStepFromMessage:** Backend messages don't match keyword patterns - need to adjust keywords or check backend messages.

- **If stepMessage is null/undefined in updateProgress:** Issue is in how updateProcessingUI passes the parameter (line 394).

- **If querySelector returns null:** DOM elements don't exist or have wrong IDs.

- **If no trace logs appear:** updateProcessingUI is not being called - check network polling (Prompt 2).

-------------------------------------------------------------------
PROMPT 4: DOM MANIPULATION VERIFICATION
-------------------------------------------------------------------

# DOM Manipulation Verification - Verify Elements Are Actually Updated

## Objective
Verify that DOM elements (`#progressText` and `.step-status` elements) are actually being updated in the browser, and that CSS or HTML structure issues aren't hiding the changes.

## File Locations
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/index.html`
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/ui/app.js`

## Current Issue Symptom
Functions may execute correctly but DOM not reflecting changes due to:
- Incorrect element selectors (IDs don't match)
- CSS hiding updated content
- `innerHTML` being overwritten by subsequent code
- Elements not existing when JavaScript runs
- Wrong parent/child element structure

## Current Code State

**index.html Lines 141-146 (Progress Bar):**
```html
<div class="progress-container">
    <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Processing progress">
        <div class="progress-fill" id="progressFill"></div>
    </div>
    <p class="progress-text" id="progressText" aria-live="polite">0%</p>
</div>
```

**index.html Lines 148-193 (Step Boxes - showing step1 and step2 structure):**
```html
<div class="processing-steps">
    <div class="step" id="step1">
        <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        </div>
        <div class="step-content">
            <p class="step-title">Uploading file</p>
            <p class="step-status">Pending...</p>
        </div>
    </div>
    <div class="step" id="step2">
        <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        </div>
        <div class="step-content">
            <p class="step-title">Transcribing audio</p>
            <p class="step-status">Waiting...</p>
        </div>
    </div>
    <!-- step3 and step4 have identical structure -->
</div>
```

**app.js Lines 481-491 (updateProgress):**
```javascript
function updateProgress(percent, stepMessage = null) {
    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        elements.progressText.innerHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
    } else {
        elements.progressText.textContent = `${percent}%`;
    }
}
```

**app.js Lines 373-389 (updateStepStatus):**
```javascript
function updateStepStatus(stepElement, state, message = null) {
    const statusElement = stepElement.querySelector('.step-status');

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        stepElement.classList.add('active');
        statusElement.textContent = message || 'Processing...';
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
    } else {
        statusElement.textContent = 'Waiting...';
    }
}
```

**app.js Lines 14-41 (Elements initialization):**
```javascript
const elements = {
    // ... other elements
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    steps: {
        step1: document.getElementById('step1'),
        step2: document.getElementById('step2'),
        step3: document.getElementById('step3'),
        step4: document.getElementById('step4')
    },
    // ...
};
```

## Debugging Strategy
Create a DOM verification function to query and log element states, add before/after logging in DOM manipulation functions, and provide manual DevTools inspection steps to visually confirm changes.

## Implementation Steps

### Step 1: Create DOM Verification Function (Add after line 578)

Add this new function to check DOM state on demand:

```javascript
// Add after the getAudioDuration function (around line 578)

// ========================================
// DOM Verification (Debugging)
// ========================================
function verifyDOMState() {
    console.log('[DOM VERIFY] ========================================');
    console.log('[DOM VERIFY] Checking DOM element existence and state...');

    // Check progressText element
    const progressText = document.getElementById('progressText');
    console.log('[DOM VERIFY] progressText element:', {
        exists: progressText !== null,
        id: progressText?.id,
        textContent: progressText?.textContent,
        innerHTML: progressText?.innerHTML,
        display: progressText ? window.getComputedStyle(progressText).display : 'N/A',
        visibility: progressText ? window.getComputedStyle(progressText).visibility : 'N/A'
    });

    // Check progressFill element
    const progressFill = document.getElementById('progressFill');
    console.log('[DOM VERIFY] progressFill element:', {
        exists: progressFill !== null,
        width: progressFill?.style.width,
        computedWidth: progressFill ? window.getComputedStyle(progressFill).width : 'N/A'
    });

    // Check step elements
    ['step1', 'step2', 'step3', 'step4'].forEach(stepId => {
        const stepElement = document.getElementById(stepId);
        const statusElement = stepElement?.querySelector('.step-status');

        console.log(`[DOM VERIFY] ${stepId}:`, {
            exists: stepElement !== null,
            classList: stepElement ? Array.from(stepElement.classList) : [],
            statusExists: statusElement !== null,
            statusText: statusElement?.textContent,
            display: stepElement ? window.getComputedStyle(stepElement).display : 'N/A'
        });
    });

    console.log('[DOM VERIFY] ========================================');
}

// Make it globally accessible for console testing
window.verifyDOMState = verifyDOMState;
```

### Step 2: Add Before/After Logging in updateProgress (Lines 481-491)

```javascript
Find:
function updateProgress(percent, stepMessage = null) {
    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        elements.progressText.innerHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
    } else {
        elements.progressText.textContent = `${percent}%`;
    }
}

Replace with:
function updateProgress(percent, stepMessage = null) {
    console.log('[DOM] updateProgress() - BEFORE:', {
        progressTextExists: elements.progressText !== null,
        currentInnerHTML: elements.progressText?.innerHTML,
        currentTextContent: elements.progressText?.textContent,
        progressFillWidth: elements.progressFill?.style.width
    });

    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;

    // Display percentage and optional step message
    if (stepMessage) {
        console.log(`[DOM] Setting progressText.innerHTML with message`);
        elements.progressText.innerHTML = `${percent}%<br><small style="font-size: 0.85em; opacity: 0.9;">${stepMessage}</small>`;
    } else {
        console.log(`[DOM] Setting progressText.textContent (no message)`);
        elements.progressText.textContent = `${percent}%`;
    }

    console.log('[DOM] updateProgress() - AFTER:', {
        newInnerHTML: elements.progressText.innerHTML,
        newTextContent: elements.progressText.textContent,
        progressFillWidth: elements.progressFill.style.width
    });
}
```

### Step 3: Add Before/After Logging in updateStepStatus (Lines 373-389)

```javascript
Find:
function updateStepStatus(stepElement, state, message = null) {
    const statusElement = stepElement.querySelector('.step-status');

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        stepElement.classList.add('active');
        // Display actual backend message if provided, otherwise use generic status
        statusElement.textContent = message || 'Processing...';
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
    } else {
        // waiting state
        statusElement.textContent = 'Waiting...';
    }
}

Replace with:
function updateStepStatus(stepElement, state, message = null) {
    const statusElement = stepElement.querySelector('.step-status');

    console.log(`[DOM] updateStepStatus(${stepElement?.id}) - BEFORE:`, {
        stepElementExists: stepElement !== null,
        statusElementExists: statusElement !== null,
        currentClasses: stepElement ? Array.from(stepElement.classList) : [],
        currentStatusText: statusElement?.textContent,
        targetState: state,
        message: message
    });

    stepElement.classList.remove('active', 'completed');

    if (state === 'active') {
        stepElement.classList.add('active');
        // Display actual backend message if provided, otherwise use generic status
        statusElement.textContent = message || 'Processing...';
        console.log(`[DOM] Set ${stepElement.id} to ACTIVE, status text: "${statusElement.textContent}"`);
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        statusElement.textContent = 'Completed';
        console.log(`[DOM] Set ${stepElement.id} to COMPLETED`);
    } else {
        // waiting state
        statusElement.textContent = 'Waiting...';
        console.log(`[DOM] Set ${stepElement.id} to WAITING`);
    }

    console.log(`[DOM] updateStepStatus(${stepElement.id}) - AFTER:`, {
        newClasses: Array.from(stepElement.classList),
        newStatusText: statusElement.textContent,
        computedDisplay: window.getComputedStyle(stepElement).display,
        computedVisibility: window.getComputedStyle(stepElement).visibility
    });
}
```

### Step 4: Add Element Existence Check on Init (Around Line 639)

Add verification when DOM is ready:

```javascript
Find:
function init() {
    initTheme();
    initEventListeners();
    checkGPUStatus(); // Check GPU status on load

    console.log('Audio Diarization Pipeline UI initialized');
    console.log('Supported formats:', ALLOWED_EXTENSIONS.join(', '));
    console.log('Max file size:', formatFileSize(MAX_FILE_SIZE));
}

Replace with:
function init() {
    initTheme();
    initEventListeners();
    checkGPUStatus(); // Check GPU status on load

    console.log('Audio Diarization Pipeline UI initialized');
    console.log('Supported formats:', ALLOWED_EXTENSIONS.join(', '));
    console.log('Max file size:', formatFileSize(MAX_FILE_SIZE));

    // Verify critical DOM elements exist
    console.log('[DOM INIT] Verifying critical elements...');
    console.log('[DOM INIT] progressText exists:', elements.progressText !== null);
    console.log('[DOM INIT] progressFill exists:', elements.progressFill !== null);
    console.log('[DOM INIT] step1 exists:', elements.steps.step1 !== null);
    console.log('[DOM INIT] step2 exists:', elements.steps.step2 !== null);
    console.log('[DOM INIT] step3 exists:', elements.steps.step3 !== null);
    console.log('[DOM INIT] step4 exists:', elements.steps.step4 !== null);

    if (!elements.progressText || !elements.progressFill ||
        !elements.steps.step1 || !elements.steps.step2 ||
        !elements.steps.step3 || !elements.steps.step4) {
        console.error('[DOM INIT] ⚠️ Some critical elements are missing!');
    } else {
        console.log('[DOM INIT] ✓ All critical elements found');
    }
}
```

## Testing Procedure

### Automated Testing (Console)

1. **Start backend server:**
   ```bash
   cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline"
   python3 ui/server_gpu.py
   ```

2. **Open browser with DevTools:**
   - Navigate to http://localhost:8000
   - Press F12 → Console tab
   - Check for `[DOM INIT]` logs confirming elements exist

3. **Run verification function:**
   ```javascript
   verifyDOMState()
   ```
   - Check that all elements exist
   - Note current state before upload

4. **Upload audio file:**
   - Upload a file
   - Watch `[DOM]` logs showing before/after states
   - Run `verifyDOMState()` again during processing

5. **Check logs for:**
   - Elements existing (not null)
   - innerHTML/textContent actually changing
   - Classes being added/removed
   - CSS display/visibility values

### Manual Testing (Elements Inspector)

1. **Open Elements tab in DevTools**

2. **Find #progressText:**
   - Press Ctrl+F (Cmd+F on Mac) in Elements tab
   - Search for "progressText"
   - Right-click → "Break on" → "subtree modifications"

3. **Upload file and watch:**
   - Elements tab should auto-highlight when changes occur
   - Watch `innerHTML` attribute in real-time
   - Verify `<small>` tag appears with step message

4. **Find step elements:**
   - Search for "step1", "step2", etc.
   - Watch `class` attribute for "active" and "completed"
   - Watch `.step-status` text content

5. **Check CSS:**
   - Select element in Elements tab
   - Look at Styles panel on right
   - Check for `display: none` or `visibility: hidden`
   - Check if `opacity: 0` or `height: 0` is hiding content

## Expected Output If Working

**Console on init:**
```javascript
[DOM INIT] Verifying critical elements...
[DOM INIT] progressText exists: true
[DOM INIT] progressFill exists: true
[DOM INIT] step1 exists: true
[DOM INIT] step2 exists: true
[DOM INIT] step3 exists: true
[DOM INIT] step4 exists: true
[DOM INIT] ✓ All critical elements found
```

**verifyDOMState() before upload:**
```javascript
[DOM VERIFY] ========================================
[DOM VERIFY] progressText element: {exists: true, id: "progressText", textContent: "0%", innerHTML: "0%", display: "block", visibility: "visible"}
[DOM VERIFY] step1: {exists: true, classList: ["step"], statusExists: true, statusText: "Pending...", display: "flex"}
[DOM VERIFY] step2: {exists: true, classList: ["step"], statusExists: true, statusText: "Waiting...", display: "flex"}
...
```

**During processing (console logs):**
```javascript
[DOM] updateProgress() - BEFORE: {progressTextExists: true, currentInnerHTML: "0%", currentTextContent: "0%", progressFillWidth: "0%"}
[DOM] Setting progressText.innerHTML with message
[DOM] updateProgress() - AFTER: {newInnerHTML: "80%<br><small style="...">Transcribing with Whisper large-v3</small>", newTextContent: "80%↵Transcribing with Whisper large-v3", progressFillWidth: "80%"}

[DOM] updateStepStatus(step2) - BEFORE: {stepElementExists: true, statusElementExists: true, currentClasses: ["step"], currentStatusText: "Waiting...", targetState: "active", message: "Transcribing..."}
[DOM] Set step2 to ACTIVE, status text: "Transcribing with Whisper large-v3"
[DOM] updateStepStatus(step2) - AFTER: {newClasses: ["step", "active"], newStatusText: "Transcribing with Whisper large-v3", computedDisplay: "flex", computedVisibility: "visible"}
```

**Elements tab:**
- `#progressText` innerHTML changes visibly
- `.step` elements gain "active"/"completed" classes
- `.step-status` text changes from "Waiting..." to actual messages

## Expected Output If Broken

**Scenario 1: Elements don't exist**
```javascript
[DOM INIT] progressText exists: false
[DOM INIT] ⚠️ Some critical elements are missing!

[DOM] updateProgress() - BEFORE: {progressTextExists: false, currentInnerHTML: undefined, ...}
# TypeError: Cannot set property 'innerHTML' of null
```

**Scenario 2: Elements exist but updates don't persist**
```javascript
[DOM] updateProgress() - AFTER: {newInnerHTML: "80%<br><small>...</small>", ...}
# But verifyDOMState() shows:
[DOM VERIFY] progressText innerHTML: "0%"  # ← Still the old value!
```

**Scenario 3: querySelector returns null**
```javascript
[DOM] updateStepStatus(step2) - BEFORE: {stepElementExists: true, statusElementExists: false, ...}
# TypeError: Cannot set property 'textContent' of null
```

**Scenario 4: CSS hiding content**
```javascript
[DOM] updateStepStatus(step2) - AFTER: {newClasses: ["step", "active"], computedDisplay: "none", ...}
# Element updated but CSS has display:none
```

## What This Tells Us

- **If elements don't exist on init:** HTML structure issue or IDs don't match JavaScript selectors.

- **If elements exist but updates don't persist:** Another script or function is overwriting changes, or elements are being replaced/recreated.

- **If querySelector returns null:** `.step-status` selector doesn't match HTML structure (check for typos or different class names).

- **If CSS is hiding content:** Check CSS files for rules that set `display: none`, `visibility: hidden`, `opacity: 0`, or `height: 0` on `.step.active` or similar selectors.

- **If innerHTML shows correct value but visually wrong:** CSS issue with `<small>` tag, font-size, or line-height.

=================================================================
END OF PROMPTS
=================================================================

**USAGE INSTRUCTIONS:**

1. Open 4 separate Claude Code windows
2. Copy PROMPT 1 into window 1, PROMPT 2 into window 2, etc.
3. Run all 4 prompts simultaneously
4. Compare results to identify where the issue occurs
5. The combination of all 4 outputs will provide complete diagnostic coverage
