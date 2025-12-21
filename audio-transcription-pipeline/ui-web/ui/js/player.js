/**
 * Audio Player Module
 * Handles HTML5 audio playback, controls, and synchronization
 */

class AudioPlayer {
    constructor() {
        this.audio = null;
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        this.playbackRate = 1.0;
        this.volume = 1.0;

        // Callbacks for sync with other components
        this.onTimeUpdate = null;
        this.onPlay = null;
        this.onPause = null;
        this.onEnded = null;
        this.onLoadedMetadata = null;

        this.initializeKeyboardShortcuts();
    }

    /**
     * Load audio file
     */
    loadAudio(audioUrl) {
        if (this.audio) {
            this.audio.pause();
            this.audio = null;
        }

        this.audio = new Audio(audioUrl);
        this.setupEventListeners();

        return new Promise((resolve, reject) => {
            this.audio.addEventListener('loadedmetadata', () => {
                this.duration = this.audio.duration;
                if (this.onLoadedMetadata) {
                    this.onLoadedMetadata(this.duration);
                }
                resolve(this.duration);
            });

            this.audio.addEventListener('error', (e) => {
                reject(new Error(`Failed to load audio: ${e.message}`));
            });
        });
    }

    /**
     * Setup audio event listeners
     */
    setupEventListeners() {
        this.audio.addEventListener('timeupdate', () => {
            this.currentTime = this.audio.currentTime;
            if (this.onTimeUpdate) {
                this.onTimeUpdate(this.currentTime);
            }
        });

        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            if (this.onPlay) {
                this.onPlay();
            }
        });

        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            if (this.onPause) {
                this.onPause();
            }
        });

        this.audio.addEventListener('ended', () => {
            this.isPlaying = false;
            if (this.onEnded) {
                this.onEnded();
            }
        });
    }

    /**
     * Play audio
     */
    play() {
        if (this.audio && !this.isPlaying) {
            this.audio.play().catch(e => {
                console.error('Play failed:', e);
            });
        }
    }

    /**
     * Pause audio
     */
    pause() {
        if (this.audio && this.isPlaying) {
            this.audio.pause();
        }
    }

    /**
     * Toggle play/pause
     */
    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    /**
     * Seek to specific time (in seconds)
     */
    seekTo(time) {
        if (this.audio) {
            time = Math.max(0, Math.min(time, this.duration));
            this.audio.currentTime = time;
            this.currentTime = time;
        }
    }

    /**
     * Skip forward by seconds
     */
    skipForward(seconds = 5) {
        this.seekTo(this.currentTime + seconds);
    }

    /**
     * Skip backward by seconds
     */
    skipBackward(seconds = 5) {
        this.seekTo(this.currentTime - seconds);
    }

    /**
     * Set playback speed
     */
    setPlaybackRate(rate) {
        if (this.audio) {
            this.playbackRate = rate;
            this.audio.playbackRate = rate;
        }
    }

    /**
     * Set volume (0.0 to 1.0)
     */
    setVolume(volume) {
        if (this.audio) {
            this.volume = Math.max(0, Math.min(1, volume));
            this.audio.volume = this.volume;
        }
    }

    /**
     * Get current time
     */
    getCurrentTime() {
        return this.currentTime;
    }

    /**
     * Get duration
     */
    getDuration() {
        return this.duration;
    }

    /**
     * Get playback state
     */
    getPlaybackState() {
        return {
            isPlaying: this.isPlaying,
            currentTime: this.currentTime,
            duration: this.duration,
            playbackRate: this.playbackRate,
            volume: this.volume
        };
    }

    /**
     * Initialize keyboard shortcuts
     */
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            switch(e.key) {
                case ' ':
                case 'k':
                    e.preventDefault();
                    this.togglePlayPause();
                    break;

                case 'ArrowLeft':
                    e.preventDefault();
                    this.skipBackward(5);
                    break;

                case 'ArrowRight':
                    e.preventDefault();
                    this.skipForward(5);
                    break;

                case 'j':
                    e.preventDefault();
                    this.skipBackward(10);
                    break;

                case 'l':
                    e.preventDefault();
                    this.skipForward(10);
                    break;

                case 'm':
                    e.preventDefault();
                    this.toggleMute();
                    break;

                case '0':
                    e.preventDefault();
                    this.seekTo(0);
                    break;

                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                case '6':
                case '7':
                case '8':
                case '9':
                    e.preventDefault();
                    const percent = parseInt(e.key) / 10;
                    this.seekTo(this.duration * percent);
                    break;
            }
        });
    }

    /**
     * Toggle mute
     */
    toggleMute() {
        if (this.audio) {
            if (this.audio.volume > 0) {
                this.previousVolume = this.audio.volume;
                this.setVolume(0);
            } else {
                this.setVolume(this.previousVolume || 1.0);
            }
        }
    }

    /**
     * Format time as MM:SS or HH:MM:SS
     */
    static formatTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds)) {
            return '0:00';
        }

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Export for use in other modules
window.AudioPlayer = AudioPlayer;
