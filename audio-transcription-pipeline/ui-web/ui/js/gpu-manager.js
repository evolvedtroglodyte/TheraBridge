/**
 * GPU Manager - Handles Vast.ai GPU instance management
 */

class GPUManager {
    constructor() {
        this.statusCheckInterval = null;
        this.currentStatus = null;
    }

    /**
     * Initialize GPU manager and check status
     */
    async init() {
        await this.checkGPUStatus();
        this.startStatusMonitoring();
        this.setupUI();
    }

    /**
     * Check GPU status (local or Vast.ai)
     */
    async checkGPUStatus() {
        try {
            const response = await fetch('/api/gpu-status');
            const status = await response.json();
            this.currentStatus = status;
            this.updateGPUIndicator(status);
            return status;
        } catch (error) {
            console.error('GPU status check failed:', error);
            this.updateGPUIndicator({ available: false, message: 'Failed to check GPU status' });
            return null;
        }
    }

    /**
     * Update GPU status indicator in UI
     */
    updateGPUIndicator(status) {
        const indicator = document.getElementById('gpuIndicator');
        if (!indicator) return;

        const isAvailable = status.available;
        const type = status.type || 'none';
        const message = status.message || 'Unknown status';

        // Update indicator class
        indicator.className = `gpu-indicator ${isAvailable ? 'gpu-available' : 'gpu-unavailable'}`;

        // Update indicator content
        indicator.innerHTML = `
            <svg class="gpu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${isAvailable
                    ? '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>'
                    : '<circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>'
                }
            </svg>
            <span class="gpu-status-text">
                ${isAvailable
                    ? `GPU: ${type === 'local' ? 'Local' : 'Vast.ai'}`
                    : 'No GPU'
                }
            </span>
            <span class="gpu-status-detail">${message}</span>
        `;

        // Show/hide GPU boot button
        const bootBtn = document.getElementById('bootGPUBtn');
        if (bootBtn) {
            bootBtn.style.display = (!isAvailable && type === 'none') ? 'inline-flex' : 'none';
        }
    }

    /**
     * Setup UI elements
     */
    setupUI() {
        // Add GPU indicator to header
        const header = document.querySelector('.header .container');
        if (header && !document.getElementById('gpuIndicator')) {
            const gpuIndicator = document.createElement('div');
            gpuIndicator.id = 'gpuIndicator';
            gpuIndicator.className = 'gpu-indicator';
            header.appendChild(gpuIndicator);
        }

        // Add GPU boot button
        const uploadSection = document.querySelector('.upload-section');
        if (uploadSection && !document.getElementById('gpuBootSection')) {
            const bootSection = document.createElement('div');
            bootSection.id = 'gpuBootSection';
            bootSection.className = 'gpu-boot-section';
            bootSection.innerHTML = `
                <button id="bootGPUBtn" class="btn btn-gpu-boot" style="display: none;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                    Boot Vast.ai GPU Instance
                </button>
            `;
            uploadSection.insertBefore(bootSection, uploadSection.firstChild);

            // Add event listener
            document.getElementById('bootGPUBtn').addEventListener('click', () => this.showGPUBootModal());
        }
    }

    /**
     * Show GPU boot modal
     */
    async showGPUBootModal() {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'gpuBootModal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content gpu-boot-modal">
                <div class="modal-header">
                    <h2>Boot Vast.ai GPU Instance</h2>
                    <button class="modal-close" onclick="document.getElementById('gpuBootModal').remove()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">
                    <p class="modal-description">
                        Select a GPU instance to boot up. The instance will be automatically configured with all dependencies.
                    </p>

                    <div id="gpuOffersLoading" class="loading-spinner">
                        <div class="spinner"></div>
                        <p>Searching for available GPU instances...</p>
                    </div>

                    <div id="gpuOffersList" style="display: none;">
                        <!-- Offers will be populated here -->
                    </div>

                    <div id="gpuBootProgress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" id="bootProgressFill"></div>
                        </div>
                        <p id="bootProgressText">Setting up GPU instance...</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="document.getElementById('gpuBootModal').remove()">
                        Cancel
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Search for instances
        await this.searchGPUInstances();
    }

    /**
     * Search for available GPU instances
     */
    async searchGPUInstances() {
        try {
            const response = await fetch('/api/vast/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gpu_ram_min: 16, max_price: 0.5 })
            });

            const data = await response.json();
            const offers = data.offers || [];

            // Hide loading spinner
            document.getElementById('gpuOffersLoading').style.display = 'none';

            // Show offers list
            const offersList = document.getElementById('gpuOffersList');
            offersList.style.display = 'block';

            if (offers.length === 0) {
                offersList.innerHTML = `
                    <div class="no-offers">
                        <p>No GPU instances available at the moment.</p>
                        <p>Try adjusting your search criteria or check back later.</p>
                    </div>
                `;
                return;
            }

            // Render offers
            offersList.innerHTML = `
                <div class="gpu-offers-grid">
                    ${offers.map(offer => this.renderGPUOffer(offer)).join('')}
                </div>
            `;

            // Add click listeners
            offersList.querySelectorAll('.gpu-offer-card').forEach(card => {
                card.addEventListener('click', () => {
                    const offerId = card.dataset.offerId;
                    this.bootGPUInstance(offerId);
                });
            });

        } catch (error) {
            console.error('Failed to search GPU instances:', error);
            document.getElementById('gpuOffersLoading').innerHTML = `
                <div class="error-message">
                    <p>Failed to search for GPU instances.</p>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Render GPU offer card
     */
    renderGPUOffer(offer) {
        const gpuName = offer.gpu_name || 'Unknown GPU';
        const gpuRam = offer.gpu_ram || 0;
        const price = offer.dph_total || 0;
        const reliability = offer.reliability2 || 0;
        const diskSpace = offer.disk_space || 0;
        const bandwidth = offer.inet_down || 0;

        return `
            <div class="gpu-offer-card" data-offer-id="${offer.id}">
                <div class="offer-header">
                    <h3>${gpuName}</h3>
                    <span class="offer-price">$${price.toFixed(3)}/hr</span>
                </div>
                <div class="offer-specs">
                    <div class="spec-item">
                        <span class="spec-label">VRAM:</span>
                        <span class="spec-value">${gpuRam} GB</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Disk:</span>
                        <span class="spec-value">${diskSpace} GB</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Network:</span>
                        <span class="spec-value">${bandwidth} Mbps</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Reliability:</span>
                        <span class="spec-value">${(reliability * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div class="offer-actions">
                    <button class="btn btn-primary btn-sm">
                        Select & Boot
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Boot GPU instance
     */
    async bootGPUInstance(offerId) {
        try {
            // Hide offers list
            document.getElementById('gpuOffersList').style.display = 'none';

            // Show progress
            const progressDiv = document.getElementById('gpuBootProgress');
            progressDiv.style.display = 'block';

            // Update progress
            this.updateBootProgress(10, 'Creating instance...');

            const response = await fetch('/api/vast/boot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ offer_id: parseInt(offerId) })
            });

            const data = await response.json();

            if (data.success) {
                this.updateBootProgress(50, 'Instance created. Installing dependencies...');

                // Poll for setup completion
                await this.waitForInstanceSetup(data.instance_id);

                this.updateBootProgress(100, 'GPU instance ready!');

                // Close modal after 2 seconds
                setTimeout(() => {
                    document.getElementById('gpuBootModal').remove();
                    // Refresh GPU status
                    this.checkGPUStatus();
                }, 2000);

            } else {
                throw new Error(data.message || 'Failed to boot instance');
            }

        } catch (error) {
            console.error('Failed to boot GPU instance:', error);
            document.getElementById('bootProgressText').innerHTML = `
                <span class="error-text">Failed to boot instance: ${error.message}</span>
            `;
        }
    }

    /**
     * Wait for instance setup to complete
     */
    async waitForInstanceSetup(instanceId) {
        let attempts = 0;
        const maxAttempts = 60; // 5 minutes max

        while (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds

            // Check GPU status
            const status = await this.checkGPUStatus();

            if (status && status.available && status.type === 'vast') {
                return; // Setup complete
            }

            attempts++;
            const progress = 50 + (attempts / maxAttempts) * 40; // 50-90%
            this.updateBootProgress(progress, `Installing dependencies... (${attempts * 5}s)`);
        }

        throw new Error('Setup timeout - instance may still be configuring');
    }

    /**
     * Update boot progress bar
     */
    updateBootProgress(percent, text) {
        const fillBar = document.getElementById('bootProgressFill');
        const textElement = document.getElementById('bootProgressText');

        if (fillBar) fillBar.style.width = `${percent}%`;
        if (textElement) textElement.textContent = text;
    }

    /**
     * Start periodic GPU status monitoring
     */
    startStatusMonitoring() {
        // Check every 30 seconds
        this.statusCheckInterval = setInterval(() => {
            this.checkGPUStatus();
        }, 30000);
    }

    /**
     * Stop status monitoring
     */
    stopStatusMonitoring() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }
}

// Initialize GPU manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.gpuManager = new GPUManager();
        window.gpuManager.init();
    });
} else {
    window.gpuManager = new GPUManager();
    window.gpuManager.init();
}
