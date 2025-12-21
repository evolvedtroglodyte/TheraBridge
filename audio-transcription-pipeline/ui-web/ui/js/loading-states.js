/**
 * Loading States Module
 * Provides skeleton screens, shimmer effects, and loading indicators
 */

class LoadingStates {
    constructor() {
        this.activeLoaders = new Map();
    }

    /**
     * Show skeleton screen for results
     */
    showResultsSkeleton(container) {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        const skeleton = `
            <div class="skeleton-results" role="status" aria-label="Loading results">
                <div class="skeleton-header">
                    <div class="skeleton-title shimmer"></div>
                    <div class="skeleton-actions">
                        <div class="skeleton-button shimmer"></div>
                        <div class="skeleton-button shimmer"></div>
                    </div>
                </div>

                <div class="skeleton-player">
                    <div class="skeleton-waveform shimmer"></div>
                    <div class="skeleton-controls">
                        <div class="skeleton-button-circle shimmer"></div>
                        <div class="skeleton-time shimmer"></div>
                        <div class="skeleton-slider shimmer"></div>
                    </div>
                </div>

                <div class="skeleton-transcript">
                    ${this.createSkeletonSegments(5)}
                </div>

                <div class="skeleton-stats">
                    <div class="skeleton-stat-card shimmer"></div>
                    <div class="skeleton-stat-card shimmer"></div>
                    <div class="skeleton-stat-card shimmer"></div>
                </div>

                <span class="sr-only">Loading transcription results...</span>
            </div>
        `;

        container.innerHTML = skeleton;
    }

    /**
     * Create skeleton transcript segments
     */
    createSkeletonSegments(count = 5) {
        let segments = '';
        for (let i = 0; i < count; i++) {
            const width = 60 + Math.random() * 30; // Random width between 60-90%
            segments += `
                <div class="skeleton-segment">
                    <div class="skeleton-segment-header">
                        <div class="skeleton-badge shimmer"></div>
                        <div class="skeleton-timestamp shimmer"></div>
                    </div>
                    <div class="skeleton-text shimmer" style="width: ${width}%"></div>
                    <div class="skeleton-text shimmer" style="width: ${width - 10}%"></div>
                </div>
            `;
        }
        return segments;
    }

    /**
     * Show processing animation with estimated time
     */
    showProcessingLoader(container, options = {}) {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        const {
            title = 'Processing Audio',
            message = 'This may take 2-5 minutes...',
            showEstimate = true,
            estimatedTime = null
        } = options;

        const loader = document.createElement('div');
        loader.className = 'processing-loader';
        loader.setAttribute('role', 'status');
        loader.setAttribute('aria-live', 'polite');
        loader.setAttribute('aria-atomic', 'true');

        loader.innerHTML = `
            <div class="processing-animation">
                <div class="processing-spinner">
                    <svg viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" class="spinner-track"/>
                        <circle cx="50" cy="50" r="45" class="spinner-progress"/>
                    </svg>
                    <div class="processing-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                        </svg>
                    </div>
                </div>
                <h3 class="processing-title">${this.escapeHtml(title)}</h3>
                <p class="processing-message">${this.escapeHtml(message)}</p>
                ${showEstimate && estimatedTime ? `
                    <div class="processing-estimate">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                        <span>Estimated: ${this.escapeHtml(estimatedTime)}</span>
                    </div>
                ` : ''}
                <span class="sr-only">${this.escapeHtml(title)}. ${this.escapeHtml(message)}</span>
            </div>
        `;

        container.appendChild(loader);
        return loader;
    }

    /**
     * Show inline loading spinner
     */
    showInlineLoader(container, text = 'Loading...') {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        const loader = document.createElement('div');
        loader.className = 'inline-loader';
        loader.setAttribute('role', 'status');

        loader.innerHTML = `
            <div class="inline-spinner"></div>
            <span class="inline-loader-text">${this.escapeHtml(text)}</span>
            <span class="sr-only">${this.escapeHtml(text)}</span>
        `;

        container.appendChild(loader);
        return loader;
    }

    /**
     * Show button loading state
     */
    setButtonLoading(button, isLoading = true, loadingText = 'Loading...') {
        if (typeof button === 'string') {
            button = document.getElementById(button);
        }
        if (!button) return;

        if (isLoading) {
            // Store original content
            button.dataset.originalContent = button.innerHTML;
            button.dataset.originalDisabled = button.disabled;

            button.disabled = true;
            button.classList.add('btn-loading');
            button.innerHTML = `
                <div class="btn-spinner"></div>
                <span>${this.escapeHtml(loadingText)}</span>
            `;
            button.setAttribute('aria-busy', 'true');
        } else {
            // Restore original content
            if (button.dataset.originalContent) {
                button.innerHTML = button.dataset.originalContent;
            }
            button.disabled = button.dataset.originalDisabled === 'true';
            button.classList.remove('btn-loading');
            button.removeAttribute('aria-busy');
        }
    }

    /**
     * Show progress bar
     */
    showProgressBar(container, progress = 0, options = {}) {
        const {
            label = '',
            showPercentage = true,
            indeterminate = false
        } = options;

        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        const existingBar = container.querySelector('.progress-bar-container');
        if (existingBar) {
            this.updateProgressBar(existingBar, progress);
            return existingBar;
        }

        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar-container';
        progressBar.setAttribute('role', 'progressbar');
        progressBar.setAttribute('aria-valuemin', '0');
        progressBar.setAttribute('aria-valuemax', '100');
        progressBar.setAttribute('aria-valuenow', progress.toString());

        progressBar.innerHTML = `
            ${label ? `<div class="progress-label">${this.escapeHtml(label)}</div>` : ''}
            <div class="progress-bar ${indeterminate ? 'indeterminate' : ''}">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            ${showPercentage ? `<div class="progress-percentage">${progress}%</div>` : ''}
        `;

        container.appendChild(progressBar);
        return progressBar;
    }

    /**
     * Update progress bar
     */
    updateProgressBar(progressBar, progress) {
        const fill = progressBar.querySelector('.progress-fill');
        const percentage = progressBar.querySelector('.progress-percentage');

        if (fill) {
            fill.style.width = `${progress}%`;
        }
        if (percentage) {
            percentage.textContent = `${progress}%`;
        }

        progressBar.setAttribute('aria-valuenow', progress.toString());

        // Announce progress to screen readers at 25%, 50%, 75%, 100%
        if ([25, 50, 75, 100].includes(progress)) {
            this.announce(`${progress}% complete`);
        }
    }

    /**
     * Show file size warning
     */
    showFileSizeWarning(fileSize, estimatedTime) {
        const warning = document.createElement('div');
        warning.className = 'file-size-warning';
        warning.setAttribute('role', 'alert');

        const fileSizeMB = (fileSize / (1024 * 1024)).toFixed(1);

        warning.innerHTML = `
            <div class="warning-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
            </div>
            <div class="warning-content">
                <h4>Large File Detected</h4>
                <p>This file is ${fileSizeMB}MB. Processing may take ${estimatedTime}.</p>
            </div>
        `;

        return warning;
    }

    /**
     * Calculate estimated processing time based on file duration
     */
    estimateProcessingTime(audioDuration) {
        // Rough estimate: 1 minute of audio = 30-60 seconds of processing
        const estimatedSeconds = audioDuration * 0.75; // 45 seconds per minute average

        if (estimatedSeconds < 60) {
            return 'about 1 minute';
        } else if (estimatedSeconds < 300) {
            const minutes = Math.ceil(estimatedSeconds / 60);
            return `${minutes}-${minutes + 1} minutes`;
        } else if (estimatedSeconds < 600) {
            return '5-10 minutes';
        } else {
            return '10+ minutes';
        }
    }

    /**
     * Remove all loading states from container
     */
    clearLoading(container) {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        const loaders = container.querySelectorAll('.skeleton-results, .processing-loader, .inline-loader');
        loaders.forEach(loader => loader.remove());
    }

    /**
     * Announce to screen readers
     */
    announce(message) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = message;

        document.body.appendChild(announcement);

        // Remove after announcement
        setTimeout(() => announcement.remove(), 1000);
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global access
window.LoadingStates = LoadingStates;
