/**
 * Waveform Visualization Module
 * Uses WaveSurfer.js for audio waveform rendering with speaker diarization
 */

class WaveformVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.wavesurfer = null;
        this.regions = [];
        this.speakerColors = {
            'SPEAKER_00': '#3B82F6', // Blue
            'SPEAKER_01': '#10B981', // Green
            'SPEAKER_02': '#F59E0B', // Amber
            'SPEAKER_03': '#EF4444', // Red
            'SPEAKER_04': '#8B5CF6', // Purple
            'SPEAKER_05': '#EC4899', // Pink
            'SPEAKER_06': '#14B8A6', // Teal
            'SPEAKER_07': '#F97316', // Orange
        };
    }

    /**
     * Initialize WaveSurfer instance
     */
    async initialize() {
        // Check if WaveSurfer is loaded
        if (typeof WaveSurfer === 'undefined') {
            console.error('WaveSurfer.js is not loaded');
            return false;
        }

        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container ${this.containerId} not found`);
            return false;
        }

        // Create WaveSurfer instance
        this.wavesurfer = WaveSurfer.create({
            container: container,
            waveColor: '#94A3B8',
            progressColor: '#1E293B',
            cursorColor: '#0EA5E9',
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            height: 128,
            normalize: true,
            responsive: true,
            backend: 'WebAudio',
            interact: true,
            hideScrollbar: false,
            plugins: [
                WaveSurfer.regions.create({
                    regions: [],
                    dragSelection: false
                })
            ]
        });

        // Set up event listeners
        this.setupEventListeners();

        return true;
    }

    /**
     * Load audio file
     */
    async loadAudio(audioFile) {
        if (!this.wavesurfer) {
            console.error('WaveSurfer not initialized');
            return false;
        }

        try {
            // Load audio from File object or URL
            if (audioFile instanceof File) {
                const url = URL.createObjectURL(audioFile);
                await this.wavesurfer.load(url);
            } else {
                await this.wavesurfer.load(audioFile);
            }
            return true;
        } catch (error) {
            console.error('Error loading audio:', error);
            return false;
        }
    }

    /**
     * Add speaker diarization regions to waveform
     */
    addSpeakerRegions(segments) {
        if (!this.wavesurfer || !this.wavesurfer.regions) {
            console.error('WaveSurfer or regions plugin not initialized');
            return;
        }

        // Clear existing regions
        this.wavesurfer.regions.clear();
        this.regions = [];

        // Add region for each speaker segment
        segments.forEach((segment, index) => {
            const color = this.getSpeakerColor(segment.speaker);

            const region = this.wavesurfer.regions.add({
                start: segment.start,
                end: segment.end,
                color: this.hexToRgba(color, 0.2),
                drag: false,
                resize: false,
                data: {
                    speaker: segment.speaker,
                    text: segment.text,
                    index: index
                }
            });

            this.regions.push(region);
        });
    }

    /**
     * Get color for speaker
     */
    getSpeakerColor(speaker) {
        return this.speakerColors[speaker] || '#64748B'; // Default gray
    }

    /**
     * Convert hex color to rgba
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        if (!this.wavesurfer) return;

        // Update playback position
        this.wavesurfer.on('audioprocess', () => {
            this.updatePlaybackPosition();
        });

        // Handle region clicks
        this.wavesurfer.on('region-click', (region, e) => {
            e.stopPropagation();
            region.play();
            this.highlightSegment(region.data.index);
        });

        // Handle waveform ready
        this.wavesurfer.on('ready', () => {
            this.enableControls();
        });

        // Handle errors
        this.wavesurfer.on('error', (error) => {
            console.error('WaveSurfer error:', error);
            this.showError('Error loading audio file');
        });
    }

    /**
     * Update playback position indicator
     */
    updatePlaybackPosition() {
        const currentTime = this.wavesurfer.getCurrentTime();
        const duration = this.wavesurfer.getDuration();

        // Emit custom event for other components to listen
        document.dispatchEvent(new CustomEvent('waveform-position-update', {
            detail: { currentTime, duration }
        }));
    }

    /**
     * Highlight segment in transcript
     */
    highlightSegment(index) {
        document.dispatchEvent(new CustomEvent('segment-highlight', {
            detail: { index }
        }));
    }

    /**
     * Play/pause audio
     */
    playPause() {
        if (!this.wavesurfer) return;
        this.wavesurfer.playPause();
    }

    /**
     * Stop audio
     */
    stop() {
        if (!this.wavesurfer) return;
        this.wavesurfer.stop();
    }

    /**
     * Seek to position (0-1)
     */
    seekTo(progress) {
        if (!this.wavesurfer) return;
        this.wavesurfer.seekTo(progress);
    }

    /**
     * Zoom in/out
     */
    zoom(level) {
        if (!this.wavesurfer) return;
        this.wavesurfer.zoom(level);
    }

    /**
     * Enable playback controls
     */
    enableControls() {
        const playBtn = document.getElementById('playBtn');
        const stopBtn = document.getElementById('stopBtn');
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');

        if (playBtn) playBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;
        if (zoomInBtn) zoomInBtn.disabled = false;
        if (zoomOutBtn) zoomOutBtn.disabled = false;
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('waveformError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    /**
     * Get current playback state
     */
    isPlaying() {
        return this.wavesurfer ? this.wavesurfer.isPlaying() : false;
    }

    /**
     * Destroy instance
     */
    destroy() {
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
            this.wavesurfer = null;
        }
        this.regions = [];
    }
}

// Export for use in other modules
window.WaveformVisualizer = WaveformVisualizer;
