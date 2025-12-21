// ========================================
// State Management
// ========================================
const state = {
    selectedFile: null,
    isProcessing: false,
    currentStep: 0,
    processingProgress: 0
};

// ========================================
// DOM Elements
// ========================================
const elements = {
    // Theme toggle
    themeToggle: document.getElementById('themeToggle'),

    // Upload elements
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    dropZoneContent: document.getElementById('dropZoneContent'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    fileDuration: document.getElementById('fileDuration'),
    removeFileBtn: document.getElementById('removeFileBtn'),
    uploadBtn: document.getElementById('uploadBtn'),

    // Processing elements
    uploadSection: document.getElementById('uploadSection'),
    processingSection: document.getElementById('processingSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    cancelBtn: document.getElementById('cancelBtn'),
    steps: {
        step1: document.getElementById('step1'),
        step2: document.getElementById('step2'),
        step3: document.getElementById('step3'),
        step4: document.getElementById('step4')
    },

    // Results elements
    resultsSection: document.getElementById('resultsSection'),
    newUploadBtn: document.getElementById('newUploadBtn'),

    // Error banner
    errorBanner: document.getElementById('errorBanner'),
    errorMessage: document.getElementById('errorMessage'),
    closeErrorBtn: document.getElementById('closeErrorBtn')
};

// ========================================
// GPU Status Check
// ========================================
async function checkGPUStatus() {
    const statusElement = document.getElementById('gpuStatus');
    const statusIcon = document.getElementById('gpuStatusIcon');
    const statusText = document.getElementById('gpuStatusText');

    try {
        const response = await fetch(`${API_CONFIG.baseUrl}/api/gpu-status`);
        const status = await response.json();

        if (status.available) {
            statusElement.className = 'gpu-status available';
            statusIcon.textContent = '✅';
            if (status.type === 'local') {
                statusText.textContent = `GPU Ready: ${status.gpu_name || 'Local GPU'}`;
            } else if (status.type === 'vast') {
                statusText.textContent = `Vast.ai Ready: Instance ${status.vast_instance}`;
            } else {
                statusText.textContent = 'GPU Available';
            }
            // Enable upload button if file is selected
            if (state.selectedFile) {
                elements.uploadBtn.disabled = false;
            }
        } else {
            statusElement.className = 'gpu-status unavailable';
            statusIcon.textContent = '❌';
            statusText.textContent = 'No GPU Available';
            // Disable upload button
            elements.uploadBtn.disabled = true;

            // Show detailed error in console
            console.error('GPU Status:', status.message);
        }
    } catch (error) {
        statusElement.className = 'gpu-status unavailable';
        statusIcon.textContent = '⚠️';
        statusText.textContent = 'Cannot connect to server';
        elements.uploadBtn.disabled = true;
        console.error('Failed to check GPU status:', error);
    }
}

// Check GPU status on page load and periodically
setInterval(checkGPUStatus, 30000); // Check every 30 seconds

// ========================================
// Theme Management
// ========================================
function initTheme() {
    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// ========================================
// File Validation
// ========================================
const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.aiff'];
const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB

function validateFile(file) {
    if (!file) {
        return { valid: false, error: 'No file selected' };
    }

    // Check file extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
        return {
            valid: false,
            error: `Invalid file type. Supported formats: ${ALLOWED_EXTENSIONS.join(', ')}`
        };
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        return {
            valid: false,
            error: `File too large. Maximum size: ${formatFileSize(MAX_FILE_SIZE)}`
        };
    }

    return { valid: true };
}

// ========================================
// File Handling
// ========================================
function handleFileSelect(file) {
    const validation = validateFile(file);

    if (!validation.valid) {
        showError(validation.error);
        return;
    }

    state.selectedFile = file;
    displayFileInfo(file);

    // Check GPU status before enabling upload button
    checkGPUStatus();
}

function displayFileInfo(file) {
    // Hide drop zone content, show file info
    elements.dropZoneContent.style.display = 'none';
    elements.fileInfo.style.display = 'flex';

    // Update file info
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);

    // Calculate audio duration
    getAudioDuration(file).then(duration => {
        if (duration) {
            elements.fileDuration.textContent = formatDuration(duration);
        } else {
            elements.fileDuration.textContent = 'Duration unknown';
        }
    });
}

function removeFile() {
    state.selectedFile = null;

    // Show drop zone content, hide file info
    elements.dropZoneContent.style.display = 'flex';
    elements.fileInfo.style.display = 'none';

    // Reset file input
    elements.fileInput.value = '';

    // Disable upload button
    elements.uploadBtn.disabled = true;
}

// ========================================
// Drag & Drop Handling
// ========================================
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

// ========================================
// API Configuration
// ========================================
const API_CONFIG = {
    baseUrl: 'http://localhost:8000',  // Python bridge server (FastAPI)
    endpoints: {
        upload: '/api/upload',
        status: '/api/status',
        results: '/api/results',
        cancel: '/api/cancel'
    },
    pollInterval: 1000  // Poll status every 1 second
};

// ========================================
// API Integration
// ========================================
let currentJobId = null;
let statusPollInterval = null;

async function uploadAndProcess(file) {
    try {
        // 1. Upload file to server
        const formData = new FormData();
        formData.append('file', file);

        const uploadResponse = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`, {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.error || 'Upload failed');
        }

        const uploadData = await uploadResponse.json();
        currentJobId = uploadData.job_id;

        console.log('Upload successful. Job ID:', currentJobId);

        // 2. Start polling for status updates
        console.log(`[NETWORK] Starting status polling for job: ${currentJobId}`);
        console.log(`[NETWORK] Poll interval: ${API_CONFIG.pollInterval}ms`);
        console.log(`[NETWORK] Status endpoint: ${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`);
        pollProcessingStatus();

    } catch (error) {
        console.error('Upload error:', error);
        state.isProcessing = false;

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('Cannot connect to server. Please ensure the server is running on ' + API_CONFIG.baseUrl);
        } else {
            showError('Upload failed: ' + error.message);
        }

        // Reset to upload view
        elements.processingSection.style.display = 'none';
        elements.uploadSection.style.display = 'block';
    }
}

async function pollProcessingStatus() {
    if (!currentJobId || !state.isProcessing) {
        return;
    }

    try {
        const statusResponse = await fetch(
            `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`
        );

        if (!statusResponse.ok) {
            console.error(`[NETWORK ERROR] Status fetch failed: ${statusResponse.status} ${statusResponse.statusText}`);
            console.error(`[NETWORK ERROR] URL: ${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`);
            throw new Error('Failed to get status');
        }

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
            console.log(`[NETWORK] Continuing to poll (status: ${statusData.status}, progress: ${statusData.progress}%)`);
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

async function fetchAndDisplayResults() {
    try {
        const resultsResponse = await fetch(
            `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.results}/${currentJobId}`
        );

        if (!resultsResponse.ok) {
            throw new Error('Failed to fetch results');
        }

        const resultsData = await resultsResponse.json();

        console.log('Results fetched successfully:', resultsData);

        // Complete processing and show results
        completeProcessing(resultsData);

    } catch (error) {
        console.error('Error fetching results:', error);
        state.isProcessing = false;
        showError('Failed to retrieve results: ' + error.message);

        // Reset to upload view
        setTimeout(() => {
            elements.processingSection.style.display = 'none';
            elements.uploadSection.style.display = 'block';
        }, 3000);
    }
}

async function cancelProcessing() {
    if (!currentJobId) {
        state.isProcessing = false;
        elements.processingSection.style.display = 'none';
        elements.uploadSection.style.display = 'block';
        return;
    }

    try {
        // Attempt to cancel the job on the server
        await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.cancel}/${currentJobId}`, {
            method: 'POST'
        });

        console.log('Job cancelled:', currentJobId);
    } catch (error) {
        console.error('Error cancelling job:', error);
        // Continue with client-side cleanup even if server cancellation fails
    }

    // Clear polling interval
    if (statusPollInterval) {
        clearTimeout(statusPollInterval);
        statusPollInterval = null;
    }

    // Reset state
    state.isProcessing = false;
    currentJobId = null;

    // Hide processing section, show upload section
    elements.processingSection.style.display = 'none';
    elements.uploadSection.style.display = 'block';

    showError('Processing cancelled by user');
}

// ========================================
// Processing Flow
// ========================================
function startProcessing() {
    if (!state.selectedFile) {
        showError('Please select a file first');
        return;
    }

    state.isProcessing = true;
    state.currentStep = 0;
    state.processingProgress = 0;

    // Hide upload section, show processing section
    elements.uploadSection.style.display = 'none';
    elements.processingSection.style.display = 'block';
    elements.processingSection.classList.add('fade-in');

    // Reset all steps
    Object.values(elements.steps).forEach(step => {
        step.classList.remove('active', 'completed');
        const status = step.querySelector('.step-status');
        status.textContent = 'Waiting...';
    });

    // Start upload and processing
    uploadAndProcess(state.selectedFile);
}

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

async function completeProcessing(resultsData) {
    state.isProcessing = false;

    // Hide processing section, show results section
    elements.processingSection.style.display = 'none';
    elements.resultsSection.style.display = 'block';
    elements.resultsSection.classList.add('fade-in');

    // Display results using the results-integration module
    try {
        if (typeof displayPipelineResults === 'function') {
            await displayPipelineResults(resultsData, state.selectedFile);
            console.log('Results displayed successfully');
        } else {
            console.warn('displayPipelineResults function not found. Make sure results-integration.js is loaded.');
        }
    } catch (error) {
        console.error('Error displaying results:', error);
        showError('Failed to display results: ' + error.message);
    }
}

function resetToUpload() {
    // Hide results section, show upload section
    elements.resultsSection.style.display = 'none';
    elements.uploadSection.style.display = 'block';

    // Reset file selection
    removeFile();
}

// ========================================
// Error Handling
// ========================================
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorBanner.style.display = 'block';
    elements.errorBanner.classList.add('fade-in');

    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

function hideError() {
    elements.errorBanner.style.display = 'none';
}

// ========================================
// Utility Functions
// ========================================
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function getAudioDuration(file) {
    return new Promise((resolve) => {
        try {
            const audio = new Audio();
            const url = URL.createObjectURL(file);

            audio.addEventListener('loadedmetadata', () => {
                URL.revokeObjectURL(url);
                resolve(audio.duration);
            });

            audio.addEventListener('error', () => {
                URL.revokeObjectURL(url);
                resolve(null);
            });

            audio.src = url;
        } catch (error) {
            resolve(null);
        }
    });
}

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

// ========================================
// Event Listeners
// ========================================
function initEventListeners() {
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);

    // File input
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Browse button
    elements.browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.fileInput.click();
    });

    // Drop zone click
    elements.dropZone.addEventListener('click', () => {
        if (!state.selectedFile) {
            elements.fileInput.click();
        }
    });

    // Drag & drop
    elements.dropZone.addEventListener('dragover', handleDragOver);
    elements.dropZone.addEventListener('dragleave', handleDragLeave);
    elements.dropZone.addEventListener('drop', handleDrop);

    // Remove file button
    elements.removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeFile();
    });

    // Upload button
    elements.uploadBtn.addEventListener('click', startProcessing);

    // Cancel processing button
    elements.cancelBtn.addEventListener('click', cancelProcessing);

    // New upload button
    elements.newUploadBtn.addEventListener('click', resetToUpload);

    // Close error button
    elements.closeErrorBtn.addEventListener('click', hideError);

    // Prevent default drag/drop on document
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => e.preventDefault());
}

// ========================================
// Initialization
// ========================================
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

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
