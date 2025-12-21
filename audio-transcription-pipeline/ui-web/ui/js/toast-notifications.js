/**
 * Toast Notification System
 * Provides user feedback for actions with customizable toast messages
 */

class ToastNotifications {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.maxToasts = 5;
        this.defaultDuration = 4000; // 4 seconds
        this.init();
    }

    /**
     * Initialize toast container
     */
    init() {
        // Create toast container
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        this.container.setAttribute('role', 'region');
        this.container.setAttribute('aria-label', 'Notifications');
        this.container.setAttribute('aria-live', 'polite');
        document.body.appendChild(this.container);
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in ms (0 = no auto-dismiss)
     * @param {object} options - Additional options
     */
    show(message, type = 'info', duration = this.defaultDuration, options = {}) {
        // Remove oldest toast if at max capacity
        if (this.toasts.length >= this.maxToasts) {
            this.remove(this.toasts[0].id);
        }

        const toastId = `toast-${Date.now()}-${Math.random()}`;
        const toast = this.createToast(toastId, message, type, options);

        this.container.appendChild(toast);
        this.toasts.push({ id: toastId, element: toast });

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => this.remove(toastId), duration);
        }

        // Announce to screen readers
        this.announce(message);

        return toastId;
    }

    /**
     * Create toast element
     */
    createToast(id, message, type, options) {
        const toast = document.createElement('div');
        toast.id = id;
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-atomic', 'true');

        const icon = this.getIcon(type);
        const hasAction = options.action && options.actionLabel;

        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">${icon}</div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
                ${hasAction ? `
                    <button class="toast-action" aria-label="${options.actionLabel}">
                        ${options.actionLabel}
                    </button>
                ` : ''}
                <button class="toast-close" aria-label="Close notification">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            ${options.progress ? '<div class="toast-progress"><div class="toast-progress-bar"></div></div>' : ''}
        `;

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.remove(id));

        // Action button handler
        if (hasAction) {
            const actionBtn = toast.querySelector('.toast-action');
            actionBtn.addEventListener('click', () => {
                options.action();
                if (options.dismissOnAction !== false) {
                    this.remove(id);
                }
            });
        }

        return toast;
    }

    /**
     * Remove a toast
     */
    remove(toastId) {
        const toastData = this.toasts.find(t => t.id === toastId);
        if (!toastData) return;

        const toast = toastData.element;

        // Fade out animation
        toast.classList.remove('show');
        toast.classList.add('hide');

        // Remove after animation
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts = this.toasts.filter(t => t.id !== toastId);
        }, 300);
    }

    /**
     * Remove all toasts
     */
    removeAll() {
        this.toasts.forEach(toast => this.remove(toast.id));
    }

    /**
     * Success toast
     */
    success(message, duration, options = {}) {
        return this.show(message, 'success', duration, options);
    }

    /**
     * Error toast
     */
    error(message, duration = 6000, options = {}) {
        return this.show(message, 'error', duration, options);
    }

    /**
     * Warning toast
     */
    warning(message, duration = 5000, options = {}) {
        return this.show(message, 'warning', duration, options);
    }

    /**
     * Info toast
     */
    info(message, duration, options = {}) {
        return this.show(message, 'info', duration, options);
    }

    /**
     * Progress toast (for long operations)
     */
    progress(message, options = {}) {
        return this.show(message, 'info', 0, { ...options, progress: true });
    }

    /**
     * Update toast message
     */
    update(toastId, message, type = null) {
        const toastData = this.toasts.find(t => t.id === toastId);
        if (!toastData) return;

        const messageEl = toastData.element.querySelector('.toast-message');
        if (messageEl) {
            messageEl.textContent = message;
        }

        if (type) {
            toastData.element.className = `toast toast-${type} show`;
        }
    }

    /**
     * Get icon for toast type
     */
    getIcon(type) {
        const icons = {
            success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>`,
            error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>`,
            warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>`,
            info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>`
        };

        return icons[type] || icons.info;
    }

    /**
     * Announce message to screen readers
     */
    announce(message) {
        // Screen readers will announce due to aria-live="polite" on container
        // This method can be extended for additional accessibility features
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global access
window.ToastNotifications = ToastNotifications;
