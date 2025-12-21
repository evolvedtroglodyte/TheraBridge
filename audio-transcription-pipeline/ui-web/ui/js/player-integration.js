/**
 * Player Integration Module
 * Connects audio player, timeline, waveform, and transcript for synchronized playback
 */

class PlayerIntegration {
    constructor() {
        this.player = null;
        this.timeline = null;
        this.waveform = null; // Will be set by Frontend Dev #2

        this.audioUrl = null;
        this.segments = [];
        this.transcript = [];

        this.initializeComponents();
        this.setupUIHandlers();
    }

    /**
     * Initialize player and timeline components
     */
    initializeComponents() {
        // Initialize audio player
        this.player = new AudioPlayer();

        // Initialize timeline
        this.timeline = new Timeline('timelineCanvas', {
            height: 80,
            segmentHeight: 50,
            backgroundColor: getComputedStyle(document.body).getPropertyValue('--bg-secondary').trim() || '#2d2d2d',
            playheadColor: '#00ff00'
        });

        // Setup player callbacks
        this.setupPlayerCallbacks();

        // Setup timeline callbacks
        this.setupTimelineCallbacks();
    }

    /**
     * Setup audio player event callbacks
     */
    setupPlayerCallbacks() {
        // Update timeline and UI on time update
        this.player.onTimeUpdate = (time) => {
            this.timeline.updateTime(time);
            this.updateTimeDisplay(time);
            this.highlightCurrentSegment(time);

            // Sync with waveform if available
            if (this.waveform && this.waveform.updatePlayhead) {
                this.waveform.updatePlayhead(time);
            }
        };

        // Update play/pause button icons
        this.player.onPlay = () => {
            this.updatePlayPauseButton(true);
        };

        this.player.onPause = () => {
            this.updatePlayPauseButton(false);
        };

        // Handle audio end
        this.player.onEnded = () => {
            this.updatePlayPauseButton(false);
            this.player.seekTo(0);
        };

        // Initialize UI when audio loads
        this.player.onLoadedMetadata = (duration) => {
            this.updateDurationDisplay(duration);
            this.timeline.loadSegments(this.segments, duration);
        };
    }

    /**
     * Setup timeline event callbacks
     */
    setupTimelineCallbacks() {
        // Seek audio when timeline is clicked
        this.timeline.onSeek = (time) => {
            this.player.seekTo(time);
        };

        // Seek to segment when clicked
        this.timeline.onSegmentClick = (segment) => {
            this.player.seekTo(segment.start);
        };

        // Show tooltip on segment hover
        this.timeline.onSegmentHover = (segment, event) => {
            this.showSegmentTooltip(segment, event);
        };
    }

    /**
     * Setup UI button handlers
     */
    setupUIHandlers() {
        // Play/Pause button
        const playPauseBtn = document.getElementById('playPauseBtn');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                this.player.togglePlayPause();
            });
        }

        // Mute button
        const muteBtn = document.getElementById('muteBtn');
        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                this.player.toggleMute();
                this.updateMuteButton(this.player.audio.volume === 0);
            });
        }

        // Volume slider
        const volumeSlider = document.getElementById('volumeSlider');
        if (volumeSlider) {
            volumeSlider.addEventListener('input', (e) => {
                const volume = e.target.value / 100;
                this.player.setVolume(volume);
                this.updateMuteButton(volume === 0);
            });
        }

        // Speed select
        const speedSelect = document.getElementById('speedSelect');
        if (speedSelect) {
            speedSelect.addEventListener('change', (e) => {
                const rate = parseFloat(e.target.value);
                this.player.setPlaybackRate(rate);
            });
        }

        // Shortcuts button
        const shortcutsBtn = document.getElementById('shortcutsBtn');
        const shortcutsModal = document.getElementById('shortcutsModal');
        const closeShortcutsBtn = document.getElementById('closeShortcutsBtn');
        const shortcutsOverlay = document.getElementById('shortcutsModalOverlay');

        if (shortcutsBtn && shortcutsModal) {
            shortcutsBtn.addEventListener('click', () => {
                shortcutsModal.classList.remove('hidden');
            });
        }

        if (closeShortcutsBtn && shortcutsModal) {
            closeShortcutsBtn.addEventListener('click', () => {
                shortcutsModal.classList.add('hidden');
            });
        }

        if (shortcutsOverlay && shortcutsModal) {
            shortcutsOverlay.addEventListener('click', () => {
                shortcutsModal.classList.add('hidden');
            });
        }
    }

    /**
     * Load audio and diarization results
     */
    loadResults(audioUrl, diarizationResults) {
        this.audioUrl = audioUrl;
        this.segments = diarizationResults.segments || [];
        this.transcript = diarizationResults.transcript || [];

        // Load audio
        this.player.loadAudio(audioUrl).then(() => {
            console.log('Audio loaded successfully');
        }).catch(err => {
            console.error('Failed to load audio:', err);
            this.showError('Failed to load audio file');
        });
    }

    /**
     * Update time display
     */
    updateTimeDisplay(time) {
        const currentTimeEl = document.getElementById('currentTime');
        if (currentTimeEl) {
            currentTimeEl.textContent = AudioPlayer.formatTime(time);
        }
    }

    /**
     * Update duration display
     */
    updateDurationDisplay(duration) {
        const totalDurationEl = document.getElementById('totalDuration');
        if (totalDurationEl) {
            totalDurationEl.textContent = AudioPlayer.formatTime(duration);
        }
    }

    /**
     * Update play/pause button icon
     */
    updatePlayPauseButton(isPlaying) {
        const playIcon = document.getElementById('playIcon');
        const pauseIcon = document.getElementById('pauseIcon');

        if (playIcon && pauseIcon) {
            if (isPlaying) {
                playIcon.classList.add('hidden');
                pauseIcon.classList.remove('hidden');
            } else {
                playIcon.classList.remove('hidden');
                pauseIcon.classList.add('hidden');
            }
        }
    }

    /**
     * Update mute button icon
     */
    updateMuteButton(isMuted) {
        const volumeIcon = document.getElementById('volumeIcon');
        const muteIcon = document.getElementById('muteIcon');

        if (volumeIcon && muteIcon) {
            if (isMuted) {
                volumeIcon.classList.add('hidden');
                muteIcon.classList.remove('hidden');
            } else {
                volumeIcon.classList.remove('hidden');
                muteIcon.classList.add('hidden');
            }
        }
    }

    /**
     * Highlight current segment in transcript
     */
    highlightCurrentSegment(time) {
        const currentSegment = this.timeline.getCurrentSegment(time);

        if (currentSegment) {
            // Remove previous highlights
            document.querySelectorAll('.transcript-segment').forEach(el => {
                el.classList.remove('active');
            });

            // Highlight current segment
            const segmentEl = document.querySelector(
                `.transcript-segment[data-start="${currentSegment.start}"]`
            );

            if (segmentEl) {
                segmentEl.classList.add('active');

                // Auto-scroll to current segment
                segmentEl.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }
        }
    }

    /**
     * Show segment tooltip on hover
     */
    showSegmentTooltip(segment, event) {
        const tooltip = document.getElementById('segmentTooltip');

        if (tooltip) {
            const speaker = segment.speaker || 'Unknown';
            const text = segment.text || '';
            const duration = segment.end - segment.start;

            tooltip.innerHTML = `
                <strong>${speaker}</strong><br>
                ${AudioPlayer.formatTime(segment.start)} - ${AudioPlayer.formatTime(segment.end)}<br>
                Duration: ${AudioPlayer.formatTime(duration)}<br>
                ${text ? `<em>${text.substring(0, 100)}${text.length > 100 ? '...' : ''}</em>` : ''}
            `;

            tooltip.style.left = `${event.clientX + 10}px`;
            tooltip.style.top = `${event.clientY + 10}px`;
            tooltip.classList.remove('hidden');
        }
    }

    /**
     * Hide segment tooltip
     */
    hideSegmentTooltip() {
        const tooltip = document.getElementById('segmentTooltip');
        if (tooltip) {
            tooltip.classList.add('hidden');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorBanner = document.getElementById('errorBanner');
        const errorMessage = document.getElementById('errorMessage');

        if (errorBanner && errorMessage) {
            errorMessage.textContent = message;
            errorBanner.style.display = 'block';

            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorBanner.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * Public method to sync with waveform component
     */
    setWaveform(waveform) {
        this.waveform = waveform;

        // Setup bidirectional sync
        if (waveform && waveform.onSeek) {
            waveform.onSeek = (time) => {
                this.player.seekTo(time);
            };
        }
    }

    /**
     * Public method for transcript clicks
     */
    setupTranscriptSync(transcriptContainer) {
        if (!transcriptContainer) return;

        transcriptContainer.addEventListener('click', (e) => {
            const segment = e.target.closest('.transcript-segment');
            if (segment && segment.dataset.start) {
                const time = parseFloat(segment.dataset.start);
                this.player.seekTo(time);
            }
        });
    }
}

// Export for use in main app
window.PlayerIntegration = PlayerIntegration;
