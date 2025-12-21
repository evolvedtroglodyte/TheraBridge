/**
 * API Integration Example
 *
 * This file shows how to integrate the real backend API into app.js
 * Replace the mock/simulation functions with these real API calls
 */

// ========================================
// Configuration
// ========================================
const API_BASE_URL = 'http://localhost:8000/api';

// ========================================
// Real API Integration Functions
// ========================================

/**
 * Upload audio file and start processing
 *
 * Replace: The file selection and processFile() function
 */
async function uploadAndProcess(file, numSpeakers = 2) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Upload file
        const response = await fetch(`${API_BASE_URL}/upload?num_speakers=${numSpeakers}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        return result.job_id;

    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

/**
 * Poll for job status
 *
 * Replace: The simulateProcessing() function
 */
async function pollJobStatus(jobId, onProgress) {
    const pollInterval = 1000; // Poll every second
    const maxAttempts = 3600; // Max 1 hour
    let attempts = 0;

    return new Promise((resolve, reject) => {
        const poll = async () => {
            if (attempts++ >= maxAttempts) {
                reject(new Error('Processing timeout'));
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/status/${jobId}`);

                if (!response.ok) {
                    throw new Error('Failed to get status');
                }

                const status = await response.json();

                // Update UI with progress
                if (onProgress) {
                    onProgress(status);
                }

                // Check if complete
                if (status.status === 'completed') {
                    resolve(jobId);
                    return;
                }

                // Check if failed
                if (status.status === 'failed') {
                    reject(new Error(status.error || 'Processing failed'));
                    return;
                }

                // Continue polling
                setTimeout(poll, pollInterval);

            } catch (error) {
                reject(error);
            }
        };

        poll();
    });
}

/**
 * Get final results
 *
 * Replace: The mock results in completeProcessing()
 */
async function getResults(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/results/${jobId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get results');
        }

        const results = await response.json();
        return results;

    } catch (error) {
        console.error('Get results error:', error);
        throw error;
    }
}

// ========================================
// Complete Integration Example
// ========================================

/**
 * Example: How to integrate into the existing processFile() function
 */
async function processFileWithRealAPI(file) {
    try {
        // 1. Show processing UI
        state.isProcessing = true;
        elements.uploadSection.style.display = 'none';
        elements.processingSection.style.display = 'block';
        updateProgress(0);

        // 2. Upload file
        elements.steps.step1.querySelector('.step-status').textContent = 'Uploading...';
        const jobId = await uploadAndProcess(file, 2);
        elements.steps.step1.classList.add('completed');
        updateProgress(25);

        // 3. Poll for completion
        await pollJobStatus(jobId, (status) => {
            // Update UI based on status
            updateProgress(status.progress);

            // Update step status based on current step
            if (status.step.includes('Preprocessing')) {
                elements.steps.step2.classList.add('active');
                elements.steps.step2.querySelector('.step-status').textContent = status.step;
            } else if (status.step.includes('Transcribing')) {
                elements.steps.step2.classList.remove('active');
                elements.steps.step2.classList.add('completed');
                elements.steps.step3.classList.add('active');
                elements.steps.step3.querySelector('.step-status').textContent = status.step;
            } else if (status.step.includes('speakers')) {
                elements.steps.step3.classList.remove('active');
                elements.steps.step3.classList.add('completed');
                elements.steps.step4.classList.add('active');
                elements.steps.step4.querySelector('.step-status').textContent = status.step;
            }
        });

        // 4. Get results
        const results = await getResults(jobId);

        // 5. Display results
        displayResults(results);

        // 6. Show results section
        elements.processingSection.style.display = 'none';
        elements.resultsSection.style.display = 'block';

    } catch (error) {
        showError(error.message);
        state.isProcessing = false;
        elements.processingSection.style.display = 'none';
        elements.uploadSection.style.display = 'block';
    }
}

/**
 * Display results in the UI
 */
function displayResults(results) {
    // Update summary stats
    document.getElementById('totalSegments').textContent = results.segments.length;
    document.getElementById('totalSpeakers').textContent =
        new Set(results.aligned_segments.map(s => s.speaker)).size;
    document.getElementById('audioDuration').textContent =
        formatTime(results.duration);

    // Update transcript
    const transcriptContainer = document.getElementById('transcript');
    transcriptContainer.innerHTML = '';

    results.aligned_segments.forEach(segment => {
        const segmentEl = document.createElement('div');
        segmentEl.className = 'segment';
        segmentEl.innerHTML = `
            <div class="segment-header">
                <span class="speaker">${segment.speaker}</span>
                <span class="timestamp">${formatTime(segment.start)} - ${formatTime(segment.end)}</span>
            </div>
            <div class="segment-text">${segment.text}</div>
        `;
        transcriptContainer.appendChild(segmentEl);
    });

    // Update speaker timeline (if you have this feature)
    if (typeof updateSpeakerTimeline === 'function') {
        updateSpeakerTimeline(results.speaker_turns, results.duration);
    }
}

/**
 * Format time in seconds to MM:SS
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ========================================
// Integration Instructions
// ========================================

/**
 * TO INTEGRATE WITH EXISTING app.js:
 *
 * 1. Add API_BASE_URL constant at the top of app.js
 *
 * 2. Replace the processFile() function with processFileWithRealAPI()
 *
 * 3. Remove the simulateProcessing() function (no longer needed)
 *
 * 4. Add the helper functions:
 *    - uploadAndProcess()
 *    - pollJobStatus()
 *    - getResults()
 *    - displayResults()
 *    - formatTime()
 *
 * 5. Update event listeners to use the new function:
 *    - In startProcessing(), call processFileWithRealAPI(state.selectedFile)
 *
 * 6. Test with server running:
 *    - Start server: python server.py
 *    - Open browser: http://localhost:8000
 *    - Upload audio file and verify processing works
 */

// ========================================
// Testing the API (Browser Console)
// ========================================

/**
 * Test upload from browser console:
 *
 * const input = document.getElementById('fileInput');
 * const file = input.files[0];
 *
 * // Upload
 * const formData = new FormData();
 * formData.append('file', file);
 * const response = await fetch('http://localhost:8000/api/upload?num_speakers=2', {
 *   method: 'POST',
 *   body: formData
 * });
 * const result = await response.json();
 * console.log('Job ID:', result.job_id);
 *
 * // Check status
 * const statusResponse = await fetch(`http://localhost:8000/api/status/${result.job_id}`);
 * const status = await statusResponse.json();
 * console.log('Status:', status);
 *
 * // Get results (when complete)
 * const resultsResponse = await fetch(`http://localhost:8000/api/results/${result.job_id}`);
 * const results = await resultsResponse.json();
 * console.log('Results:', results);
 */
