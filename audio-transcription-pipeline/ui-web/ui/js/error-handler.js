/**
 * Error Handler Module
 * Provides comprehensive error handling with specific messages and retry logic
 */

class ErrorHandler {
    constructor() {
        this.retryAttempts = new Map(); // Track retry attempts per operation
        this.maxRetries = 3;
        this.retryDelay = 1000; // Initial delay in ms (exponential backoff)
    }

    /**
     * Handle different error types with specific messages
     */
    handleError(error, context = {}) {
        console.error(`[${context.operation || 'Unknown'}] Error:`, error);
        console.error('Error stack:', error.stack);

        const errorInfo = this.categorizeError(error, context);

        // Log structured error data
        this.logError({
            timestamp: new Date().toISOString(),
            operation: context.operation,
            errorType: errorInfo.type,
            message: errorInfo.message,
            userMessage: errorInfo.userMessage,
            retryable: errorInfo.retryable,
            details: error.message,
            stack: error.stack
        });

        return errorInfo;
    }

    /**
     * Categorize error and return appropriate user message
     */
    categorizeError(error, context) {
        // Network/Connection errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return {
                type: 'CONNECTION_ERROR',
                message: 'Cannot connect to server',
                userMessage: 'Cannot connect to server. Please ensure the backend server is running.',
                retryable: true,
                showRetry: true,
                icon: 'network'
            };
        }

        // Server not running
        if (error.message && error.message.includes('ECONNREFUSED')) {
            return {
                type: 'SERVER_NOT_RUNNING',
                message: 'Server not running',
                userMessage: 'Cannot connect to server. Please start the backend server on localhost:8000.',
                retryable: true,
                showRetry: true,
                icon: 'server'
            };
        }

        // Upload failures
        if (context.operation === 'upload' || error.message?.includes('upload')) {
            return {
                type: 'UPLOAD_ERROR',
                message: 'Upload failed',
                userMessage: `Upload failed: ${error.message || 'Unknown error'}. Please try again.`,
                retryable: true,
                showRetry: true,
                icon: 'upload'
            };
        }

        // Processing failures
        if (context.operation === 'processing' || error.message?.includes('processing')) {
            return {
                type: 'PROCESSING_ERROR',
                message: 'Processing failed',
                userMessage: `Processing error: ${error.message || 'Unknown error'}. The file may be corrupted or unsupported.`,
                retryable: false,
                showRetry: false,
                icon: 'warning'
            };
        }

        // Results not found
        if (context.operation === 'results' || error.message?.includes('results')) {
            return {
                type: 'RESULTS_ERROR',
                message: 'Results not available',
                userMessage: 'Results not available. Processing may have failed or been cancelled.',
                retryable: false,
                showRetry: false,
                icon: 'warning'
            };
        }

        // File validation errors
        if (context.operation === 'validation' || error.message?.includes('invalid')) {
            return {
                type: 'VALIDATION_ERROR',
                message: 'Invalid file',
                userMessage: error.message || 'Invalid file. Please check the file format and size.',
                retryable: false,
                showRetry: false,
                icon: 'warning'
            };
        }

        // Audio loading errors
        if (error.message?.includes('audio') || error.message?.includes('media')) {
            return {
                type: 'AUDIO_ERROR',
                message: 'Audio loading failed',
                userMessage: 'Failed to load audio file. The file may be corrupted or in an unsupported format.',
                retryable: false,
                showRetry: false,
                icon: 'audio'
            };
        }

        // Timeout errors
        if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
            return {
                type: 'TIMEOUT_ERROR',
                message: 'Operation timed out',
                userMessage: 'Operation timed out. The server may be overloaded. Please try again.',
                retryable: true,
                showRetry: true,
                icon: 'clock'
            };
        }

        // Default/Unknown errors
        return {
            type: 'UNKNOWN_ERROR',
            message: 'An error occurred',
            userMessage: `An unexpected error occurred: ${error.message || 'Please try again'}`,
            retryable: true,
            showRetry: true,
            icon: 'warning'
        };
    }

    /**
     * Retry operation with exponential backoff
     */
    async retryOperation(operation, operationName, maxRetries = this.maxRetries) {
        const attemptKey = operationName || 'default';
        let attempts = this.retryAttempts.get(attemptKey) || 0;

        while (attempts < maxRetries) {
            try {
                const result = await operation();
                // Success - reset retry counter
                this.retryAttempts.delete(attemptKey);
                return { success: true, result };
            } catch (error) {
                attempts++;
                this.retryAttempts.set(attemptKey, attempts);

                const errorInfo = this.handleError(error, { operation: operationName });

                if (!errorInfo.retryable || attempts >= maxRetries) {
                    // Not retryable or max retries reached
                    return {
                        success: false,
                        error: errorInfo,
                        attempts
                    };
                }

                // Calculate exponential backoff delay
                const delay = this.retryDelay * Math.pow(2, attempts - 1);

                console.log(`Retry ${attempts}/${maxRetries} for ${operationName} after ${delay}ms...`);

                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }

        // Should not reach here, but just in case
        return {
            success: false,
            error: { message: 'Max retries exceeded' },
            attempts
        };
    }

    /**
     * Reset retry counter for an operation
     */
    resetRetries(operationName) {
        this.retryAttempts.delete(operationName);
    }

    /**
     * Log error to console (and potentially to external service)
     */
    logError(errorData) {
        // Log to console
        console.group(`🚨 Error Log - ${errorData.timestamp}`);
        console.log('Operation:', errorData.operation);
        console.log('Error Type:', errorData.errorType);
        console.log('Message:', errorData.message);
        console.log('User Message:', errorData.userMessage);
        console.log('Retryable:', errorData.retryable);
        console.log('Details:', errorData.details);
        console.groupEnd();

        // In production, you could send to an error tracking service
        // Example: Sentry.captureException(errorData);
    }

    /**
     * Create user-friendly error message with action buttons
     */
    createErrorDisplay(errorInfo, onRetry = null) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-display';
        errorDiv.setAttribute('role', 'alert');
        errorDiv.setAttribute('aria-live', 'assertive');

        const icon = this.getErrorIcon(errorInfo.icon);

        errorDiv.innerHTML = `
            <div class="error-display-content">
                <div class="error-icon">${icon}</div>
                <div class="error-text">
                    <h4 class="error-title">${errorInfo.message}</h4>
                    <p class="error-description">${errorInfo.userMessage}</p>
                </div>
            </div>
            ${errorInfo.showRetry && onRetry ? `
                <div class="error-actions">
                    <button class="btn btn-primary btn-retry" aria-label="Retry operation">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                        </svg>
                        Retry
                    </button>
                </div>
            ` : ''}
        `;

        if (errorInfo.showRetry && onRetry) {
            const retryBtn = errorDiv.querySelector('.btn-retry');
            retryBtn.addEventListener('click', onRetry);
        }

        return errorDiv;
    }

    /**
     * Get error icon SVG
     */
    getErrorIcon(iconType) {
        const icons = {
            network: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>`,
            server: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                <line x1="6" y1="6" x2="6.01" y2="6"/>
                <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>`,
            upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>`,
            warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>`,
            audio: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <line x1="23" y1="9" x2="17" y2="15"/>
                <line x1="17" y1="9" x2="23" y2="15"/>
            </svg>`,
            clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
            </svg>`
        };

        return icons[iconType] || icons.warning;
    }
}

// Export for global access
window.ErrorHandler = ErrorHandler;
