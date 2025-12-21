/**
 * Confirmation Dialog Module
 * Provides user confirmation for destructive or important actions
 */

class ConfirmDialog {
    constructor() {
        this.activeDialog = null;
    }

    /**
     * Show confirmation dialog
     * @param {Object} options - Dialog configuration
     * @returns {Promise} - Resolves to true if confirmed, false if cancelled
     */
    show(options = {}) {
        const {
            title = 'Confirm Action',
            message = 'Are you sure you want to proceed?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            type = 'warning', // 'warning', 'danger', 'info'
            icon = null
        } = options;

        return new Promise((resolve) => {
            // Remove any existing dialog
            this.close();

            // Create dialog
            const dialog = this.createDialog({
                title,
                message,
                confirmText,
                cancelText,
                type,
                icon
            });

            // Handle confirm
            const confirmBtn = dialog.querySelector('.confirm-btn');
            const cancelBtn = dialog.querySelector('.cancel-btn');
            const overlay = dialog.querySelector('.confirm-overlay');

            const handleConfirm = () => {
                this.close();
                resolve(true);
            };

            const handleCancel = () => {
                this.close();
                resolve(false);
            };

            confirmBtn.addEventListener('click', handleConfirm);
            cancelBtn.addEventListener('click', handleCancel);
            overlay.addEventListener('click', handleCancel);

            // Handle Escape key
            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    handleCancel();
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            document.addEventListener('keydown', handleEscape);

            // Add to DOM
            document.body.appendChild(dialog);
            this.activeDialog = dialog;

            // Focus on cancel button by default (safer)
            setTimeout(() => cancelBtn.focus(), 100);

            // Announce to screen readers
            this.announce(`${title}. ${message}`);
        });
    }

    /**
     * Create dialog element
     */
    createDialog(options) {
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-labelledby', 'confirm-dialog-title');
        dialog.setAttribute('aria-describedby', 'confirm-dialog-message');
        dialog.setAttribute('aria-modal', 'true');

        const iconSvg = options.icon || this.getIcon(options.type);

        dialog.innerHTML = `
            <div class="confirm-overlay"></div>
            <div class="confirm-content confirm-${options.type}">
                <div class="confirm-icon">${iconSvg}</div>
                <h3 id="confirm-dialog-title" class="confirm-title">${this.escapeHtml(options.title)}</h3>
                <p id="confirm-dialog-message" class="confirm-message">${this.escapeHtml(options.message)}</p>
                <div class="confirm-actions">
                    <button class="btn btn-secondary cancel-btn" aria-label="Cancel">
                        ${this.escapeHtml(options.cancelText)}
                    </button>
                    <button class="btn btn-${options.type === 'danger' ? 'error' : 'primary'} confirm-btn" aria-label="${options.confirmText}">
                        ${this.escapeHtml(options.confirmText)}
                    </button>
                </div>
            </div>
        `;

        return dialog;
    }

    /**
     * Close active dialog
     */
    close() {
        if (this.activeDialog) {
            this.activeDialog.remove();
            this.activeDialog = null;
        }
    }

    /**
     * Get icon for dialog type
     */
    getIcon(type) {
        const icons = {
            warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>`,
            danger: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>`,
            info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>`
        };

        return icons[type] || icons.warning;
    }

    /**
     * Preset: Confirm cancel processing
     */
    async confirmCancelProcessing() {
        return this.show({
            title: 'Cancel Processing?',
            message: 'Are you sure you want to cancel the current processing? This action cannot be undone.',
            confirmText: 'Yes, Cancel',
            cancelText: 'No, Continue',
            type: 'warning'
        });
    }

    /**
     * Preset: Confirm clear results
     */
    async confirmClearResults() {
        return this.show({
            title: 'Clear Results?',
            message: 'This will clear the current results and return to the upload screen.',
            confirmText: 'Clear Results',
            cancelText: 'Keep Results',
            type: 'info'
        });
    }

    /**
     * Preset: Confirm large file upload
     */
    async confirmLargeFileUpload(fileSize, estimatedTime) {
        const fileSizeMB = (fileSize / (1024 * 1024)).toFixed(1);
        return this.show({
            title: 'Large File Detected',
            message: `This file is ${fileSizeMB}MB and may take ${estimatedTime} to process. Do you want to continue?`,
            confirmText: 'Yes, Process',
            cancelText: 'Cancel',
            type: 'warning'
        });
    }

    /**
     * Announce to screen readers
     */
    announce(message) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('role', 'alert');
        announcement.setAttribute('aria-live', 'assertive');
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
window.ConfirmDialog = ConfirmDialog;
