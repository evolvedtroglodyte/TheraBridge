/**
 * UX Manager
 * Centralizes all UX enhancements and provides a unified interface
 */

class UXManager {
    constructor() {
        // Initialize all UX modules
        this.errorHandler = new ErrorHandler();
        this.toast = new ToastNotifications();
        this.loadingStates = new LoadingStates();
        this.confirmDialog = new ConfirmDialog();
        this.performanceMonitor = new PerformanceMonitor();

        // Track active operations
        this.activeOperations = new Map();
    }

    /**
     * Handle file selection with validation and warnings
     */
    async handleFileSelection(file) {
        this.performanceMonitor.startTimer('file-validation');

        try {
            // Validate file
            const validation = this.validateFile(file);
            if (!validation.valid) {
                this.toast.error(validation.error);
                return { valid: false, error: validation.error };
            }

            // Check for large files
            const fileSize = file.size;
            const fileSizeMB = fileSize / (1024 * 1024);

            if (fileSizeMB > 100) {
                // Get audio duration for estimation
                const duration = await this.getAudioDuration(file);
                const estimatedTime = this.loadingStates.estimateProcessingTime(duration);

                // Show confirmation dialog
                const confirmed = await this.confirmDialog.confirmLargeFileUpload(
                    fileSize,
                    estimatedTime
                );

                if (!confirmed) {
                    this.toast.info('Upload cancelled');
                    return { valid: false, cancelled: true };
                }

                // Show warning
                this.toast.warning(
                    `Processing large file (${fileSizeMB.toFixed(1)}MB). This may take ${estimatedTime}.`,
                    8000
                );
            }

            this.performanceMonitor.endTimer('file-validation');
            this.toast.success('File selected successfully');

            return { valid: true, file };

        } catch (error) {
            const errorInfo = this.errorHandler.handleError(error, { operation: 'validation' });
            this.toast.error(errorInfo.userMessage);
            this.performanceMonitor.endTimer('file-validation');
            return { valid: false, error: errorInfo };
        }
    }

    /**
     * Handle file upload with retry logic
     */
    async handleUpload(file, uploadFunction) {
        this.performanceMonitor.startTimer('upload');
        const startTime = Date.now();

        // Show progress toast
        const toastId = this.toast.progress('Starting upload...', { progress: true });

        const retryWrapper = async () => {
            try {
                const result = await uploadFunction(file);

                // Track upload performance
                const duration = Date.now() - startTime;
                this.performanceMonitor.trackUpload(file.size, duration);

                return result;
            } catch (error) {
                throw error;
            }
        };

        // Retry operation
        const result = await this.errorHandler.retryOperation(
            retryWrapper,
            'upload',
            3 // max retries
        );

        this.toast.remove(toastId);
        this.performanceMonitor.endTimer('upload');

        if (result.success) {
            this.toast.success('Upload complete! Processing started.');
            return result.result;
        } else {
            const errorDisplay = this.errorHandler.createErrorDisplay(
                result.error,
                () => this.handleUpload(file, uploadFunction)
            );

            this.toast.error(result.error.userMessage, 0);
            return null;
        }
    }

    /**
     * Handle processing status updates
     */
    updateProcessingStatus(statusData) {
        const { progress, step, estimatedTime } = statusData;

        // Update progress announcement for screen readers
        if ([25, 50, 75, 100].includes(progress)) {
            this.loadingStates.announce(`Processing ${progress}% complete`);
        }

        // Log performance
        this.performanceMonitor.recordMetric(`processing-progress-${step}`, progress, '%');
    }

    /**
     * Handle processing completion
     */
    async handleProcessingComplete(resultsData) {
        this.performanceMonitor.startTimer('results-rendering');

        try {
            // Track processing performance
            if (resultsData.performance) {
                const audioDuration = resultsData.performance.audio_duration || 0;
                const totalTime = resultsData.performance.total_time || 0;

                this.performanceMonitor.trackProcessing(
                    audioDuration,
                    totalTime,
                    {
                        transcription: resultsData.performance.transcription_time,
                        diarization: resultsData.performance.diarization_time,
                        alignment: resultsData.performance.alignment_time
                    }
                );
            }

            this.performanceMonitor.endTimer('results-rendering');
            this.toast.success('Processing complete! Results are ready.', 5000);

            // Announce completion
            this.loadingStates.announce('Processing complete. Results are ready.');

        } catch (error) {
            const errorInfo = this.errorHandler.handleError(error, { operation: 'results' });
            this.toast.error(errorInfo.userMessage);
            this.performanceMonitor.endTimer('results-rendering');
        }
    }

    /**
     * Handle processing failure
     */
    handleProcessingFailure(error) {
        const errorInfo = this.errorHandler.handleError(error, { operation: 'processing' });

        this.toast.error(errorInfo.userMessage, 0);

        // Show detailed error with retry if applicable
        if (errorInfo.retryable) {
            this.loadingStates.announce('Processing failed. Please try again.');
        } else {
            this.loadingStates.announce('Processing failed. Please check your file and try again.');
        }
    }

    /**
     * Handle cancel processing
     */
    async handleCancelProcessing() {
        const confirmed = await this.confirmDialog.confirmCancelProcessing();

        if (confirmed) {
            this.toast.info('Processing cancelled');
            this.loadingStates.announce('Processing has been cancelled');
            return true;
        }

        return false;
    }

    /**
     * Handle network errors with auto-retry
     */
    async handleNetworkError(operation, retryFunction) {
        const errorInfo = this.errorHandler.handleError(
            new Error('Network connection failed'),
            { operation }
        );

        // Auto-retry for network errors
        const result = await this.errorHandler.retryOperation(
            retryFunction,
            operation,
            3
        );

        if (!result.success) {
            this.toast.error(errorInfo.userMessage, 0, {
                action: retryFunction,
                actionLabel: 'Retry',
                dismissOnAction: true
            });
        }

        return result;
    }

    /**
     * Validate file
     */
    validateFile(file) {
        const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.aiff'];
        const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB

        if (!file) {
            return { valid: false, error: 'No file selected' };
        }

        // Check file extension
        const fileName = file.name.toLowerCase();
        const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));

        if (!hasValidExtension) {
            return {
                valid: false,
                error: `Invalid file type. Supported formats: MP3, WAV, M4A, AAC, OGG, FLAC, WMA, AIFF`
            };
        }

        // Check file size
        if (file.size > MAX_FILE_SIZE) {
            const maxSizeMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
            return {
                valid: false,
                error: `File too large. Maximum size: ${maxSizeMB}MB`
            };
        }

        return { valid: true };
    }

    /**
     * Get audio duration
     */
    getAudioDuration(file) {
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
                    resolve(0);
                });

                audio.src = url;
            } catch (error) {
                resolve(0);
            }
        });
    }

    /**
     * Track API call
     */
    async trackAPICall(endpoint, apiFunction) {
        const startTime = performance.now();

        try {
            const result = await apiFunction();
            const duration = performance.now() - startTime;

            this.performanceMonitor.trackAPICall(endpoint, duration, true);

            return { success: true, result };
        } catch (error) {
            const duration = performance.now() - startTime;

            this.performanceMonitor.trackAPICall(endpoint, duration, false);

            return { success: false, error };
        }
    }

    /**
     * Generate and display performance report
     */
    showPerformanceReport() {
        if (this.performanceMonitor.devMode) {
            this.performanceMonitor.generateReport();
            this.toast.info('Performance report logged to console', 3000);
        }
    }

    /**
     * Cleanup and reset
     */
    cleanup() {
        this.toast.removeAll();
        this.confirmDialog.close();
        this.activeOperations.clear();
    }
}

// Export for global access
window.UXManager = UXManager;
