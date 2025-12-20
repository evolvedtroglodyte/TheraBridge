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
    elements.uploadBtn.disabled = false;
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

function updateProcessingUI(statusData) {
    // Update progress bar
    const progress = statusData.progress || 0;
    updateProgress(progress);

    // Map API step to UI step
    const stepMapping = {
        'uploading': { element: elements.steps.step1, status: 'Uploading...' },
        'transcribing': { element: elements.steps.step2, status: 'Transcribing...' },
        'diarizing': { element: elements.steps.step3, status: 'Analyzing speakers...' },
        'aligning': { element: elements.steps.step4, status: 'Finalizing...' }
    };

    const currentStep = statusData.step || 'uploading';

    // Update step indicators
    Object.entries(stepMapping).forEach(([stepName, stepInfo]) => {
        const stepElement = stepInfo.element;
        const statusElement = stepElement.querySelector('.step-status');

        if (stepName === currentStep) {
            // Current step - mark as active
            stepElement.classList.remove('completed');
            stepElement.classList.add('active');
            statusElement.textContent = stepInfo.status;
        } else if (shouldMarkCompleted(stepName, currentStep)) {
            // Previous steps - mark as completed
            stepElement.classList.remove('active');
            stepElement.classList.add('completed');
            statusElement.textContent = 'Completed';
        } else {
            // Future steps - waiting
            stepElement.classList.remove('active', 'completed');
            statusElement.textContent = 'Waiting...';
        }
    });
}

function shouldMarkCompleted(stepName, currentStep) {
    const stepOrder = ['uploading', 'transcribing', 'diarizing', 'aligning'];
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepName);
    return stepIndex < currentIndex;
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

function updateProgress(percent) {
    state.processingProgress = percent;
    elements.progressFill.style.width = `${percent}%`;
    elements.progressText.textContent = `${percent}%`;
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

    console.log('Audio Diarization Pipeline UI initialized');
    console.log('Supported formats:', ALLOWED_EXTENSIONS.join(', '));
    console.log('Max file size:', formatFileSize(MAX_FILE_SIZE));
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
