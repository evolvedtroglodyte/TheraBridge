/**
 * Enhanced App Integration Example
 * This file demonstrates how to integrate the UX enhancements into app.js
 * Copy the relevant sections into your main app.js file
 */

// ========================================
// Initialize UX Manager (Add to init())
// ========================================
let uxManager;

function initUXEnhancements() {
    uxManager = new UXManager();
    console.log('UX Manager initialized');
}

// ========================================
// Enhanced File Selection (Replace handleFileSelect)
// ========================================
async function handleFileSelectEnhanced(file) {
    // Use UX Manager for validation and warnings
    const result = await uxManager.handleFileSelection(file);

    if (!result.valid) {
        return; // Error or cancellation already handled by UX Manager
    }

    // Continue with existing file selection logic
    state.selectedFile = file;
    displayFileInfo(file);
    elements.uploadBtn.disabled = false;
}

// ========================================
// Enhanced Upload (Replace uploadAndProcess)
// ========================================
async function uploadAndProcessEnhanced(file) {
    try {
        // Show button loading state
        uxManager.loadingStates.setButtonLoading('uploadBtn', true, 'Uploading...');

        // Wrap upload function for retry logic
        const uploadFunction = async (file) => {
            const formData = new FormData();
            formData.append('audio', file);

            const startTime = Date.now();

            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }

            const data = await response.json();

            // Track upload performance
            const duration = Date.now() - startTime;
            uxManager.performanceMonitor.trackUpload(file.size, duration);

            return data;
        };

        // Use UX Manager to handle upload with retry
        const uploadData = await uxManager.handleUpload(file, uploadFunction);

        if (!uploadData) {
            // Upload failed after retries
            uxManager.loadingStates.setButtonLoading('uploadBtn', false);
            elements.processingSection.style.display = 'none';
            elements.uploadSection.style.display = 'block';
            return;
        }

        currentJobId = uploadData.job_id;

        // Start polling
        pollProcessingStatusEnhanced();

    } catch (error) {
        const errorInfo = uxManager.errorHandler.handleError(error, { operation: 'upload' });
        uxManager.toast.error(errorInfo.userMessage);

        uxManager.loadingStates.setButtonLoading('uploadBtn', false);
        elements.processingSection.style.display = 'none';
        elements.uploadSection.style.display = 'block';
    }
}

// ========================================
// Enhanced Polling (Replace pollProcessingStatus)
// ========================================
async function pollProcessingStatusEnhanced() {
    if (!currentJobId || !state.isProcessing) {
        return;
    }

    try {
        // Track API call performance
        const apiCall = async () => {
            const response = await fetch(
                `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`
            );

            if (!response.ok) {
                throw new Error('Failed to get status');
            }

            return await response.json();
        };

        const result = await uxManager.trackAPICall('status', apiCall);

        if (!result.success) {
            throw result.error;
        }

        const statusData = result.result;

        // Update processing UI
        updateProcessingUIEnhanced(statusData);

        // Update UX Manager
        uxManager.updateProcessingStatus(statusData);

        if (statusData.status === 'completed') {
            clearInterval(statusPollInterval);
            await fetchAndDisplayResultsEnhanced();
        } else if (statusData.status === 'failed') {
            clearInterval(statusPollInterval);
            state.isProcessing = false;

            uxManager.handleProcessingFailure(
                new Error(statusData.error || 'Processing failed')
            );

            setTimeout(() => {
                elements.processingSection.style.display = 'none';
                elements.uploadSection.style.display = 'block';
            }, 3000);
        } else {
            statusPollInterval = setTimeout(pollProcessingStatusEnhanced, API_CONFIG.pollInterval);
        }

    } catch (error) {
        // Handle network errors with auto-retry
        const retryResult = await uxManager.handleNetworkError('polling', async () => {
            return await fetch(
                `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status}/${currentJobId}`
            ).then(r => r.json());
        });

        if (!retryResult.success) {
            clearInterval(statusPollInterval);
            state.isProcessing = false;

            setTimeout(() => {
                elements.processingSection.style.display = 'none';
                elements.uploadSection.style.display = 'block';
            }, 3000);
        } else {
            // Retry succeeded, continue polling
            statusPollInterval = setTimeout(pollProcessingStatusEnhanced, API_CONFIG.pollInterval);
        }
    }
}

// ========================================
// Enhanced Processing UI Update (Replace updateProcessingUI)
// ========================================
function updateProcessingUIEnhanced(statusData) {
    // Update progress bar
    const progress = statusData.progress || 0;
    updateProgress(progress);

    // Update progress bar ARIA
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.setAttribute('aria-valuenow', progress.toString());
    }

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
            stepElement.classList.remove('completed');
            stepElement.classList.add('active');
            statusElement.textContent = stepInfo.status;
        } else if (shouldMarkCompleted(stepName, currentStep)) {
            stepElement.classList.remove('active');
            stepElement.classList.add('completed');
            statusElement.textContent = 'Completed';
        } else {
            stepElement.classList.remove('active', 'completed');
            statusElement.textContent = 'Waiting...';
        }
    });
}

// ========================================
// Enhanced Results Display (Replace fetchAndDisplayResults)
// ========================================
async function fetchAndDisplayResultsEnhanced() {
    // Show skeleton loading state
    uxManager.loadingStates.showResultsSkeleton('resultsContainer');

    try {
        const response = await fetch(
            `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.results}/${currentJobId}`
        );

        if (!response.ok) {
            throw new Error('Failed to fetch results');
        }

        const resultsData = await response.json();

        // Clear skeleton
        uxManager.loadingStates.clearLoading('resultsContainer');

        // Handle processing completion with UX Manager
        await uxManager.handleProcessingComplete(resultsData);

        // Display results
        await completeProcessing(resultsData);

        // Show performance report in dev mode
        uxManager.showPerformanceReport();

    } catch (error) {
        const errorInfo = uxManager.errorHandler.handleError(error, { operation: 'results' });
        uxManager.toast.error(errorInfo.userMessage);

        setTimeout(() => {
            elements.processingSection.style.display = 'none';
            elements.uploadSection.style.display = 'block';
        }, 3000);
    }
}

// ========================================
// Enhanced Cancel Processing (Replace cancelProcessing)
// ========================================
async function cancelProcessingEnhanced() {
    // Show confirmation dialog
    const confirmed = await uxManager.handleCancelProcessing();

    if (!confirmed) {
        return; // User cancelled the cancellation
    }

    // Proceed with cancellation
    if (currentJobId) {
        try {
            await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.cancel}/${currentJobId}`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error cancelling job:', error);
        }
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
}

// ========================================
// Enhanced Error Display (Replace showError)
// ========================================
function showErrorEnhanced(message, retryCallback = null) {
    // Use toast notification instead of error banner
    if (retryCallback) {
        uxManager.toast.error(message, 0, {
            action: retryCallback,
            actionLabel: 'Retry',
            dismissOnAction: true
        });
    } else {
        uxManager.toast.error(message);
    }
}

// ========================================
// Add to Initialization
// ========================================
function initEnhanced() {
    initTheme();
    initUXEnhancements(); // Initialize UX Manager
    initEventListeners();

    console.log('Audio Diarization Pipeline UI initialized with UX enhancements');
}

// ========================================
// Enhanced Event Listeners
// ========================================
function initEventListenersEnhanced() {
    // ... existing event listeners ...

    // File input - use enhanced handler
    elements.fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            await handleFileSelectEnhanced(e.target.files[0]);
        }
    });

    // Drop zone - add keyboard support
    elements.dropZone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (!state.selectedFile) {
                elements.fileInput.click();
            }
        }
    });

    // Upload button - use enhanced handler
    elements.uploadBtn.addEventListener('click', () => {
        uploadAndProcessEnhanced(state.selectedFile);
    });

    // Cancel button - use enhanced handler
    elements.cancelBtn.addEventListener('click', cancelProcessingEnhanced);
}

// ========================================
// Export for integration
// ========================================
window.EnhancedApp = {
    initUXEnhancements,
    handleFileSelectEnhanced,
    uploadAndProcessEnhanced,
    pollProcessingStatusEnhanced,
    updateProcessingUIEnhanced,
    fetchAndDisplayResultsEnhanced,
    cancelProcessingEnhanced,
    showErrorEnhanced,
    initEnhanced,
    initEventListenersEnhanced
};
