/**
 * Timeline Module
 * Visualizes speaker segments and provides interactive navigation
 */

class Timeline {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // Configuration
        this.options = {
            height: options.height || 80,
            segmentHeight: options.segmentHeight || 50,
            backgroundColor: options.backgroundColor || '#1a1a1a',
            playheadColor: options.playheadColor || '#00ff00',
            hoverColor: options.hoverColor || '#ffffff',
            ...options
        };

        // Data
        this.segments = [];
        this.duration = 0;
        this.currentTime = 0;

        // Speaker colors (consistent with transcript)
        this.speakerColors = {
            'SPEAKER_00': '#3b82f6', // Blue
            'SPEAKER_01': '#ef4444', // Red
            'SPEAKER_02': '#10b981', // Green
            'SPEAKER_03': '#f59e0b', // Orange
            'SPEAKER_04': '#8b5cf6', // Purple
            'SPEAKER_05': '#ec4899', // Pink
            'Therapist': '#3b82f6',
            'Client': '#ef4444'
        };

        // Interaction state
        this.hoveredSegment = null;
        this.isDragging = false;

        // Callbacks
        this.onSeek = null;
        this.onSegmentClick = null;
        this.onSegmentHover = null;

        this.setupCanvas();
        this.setupEventListeners();
    }

    /**
     * Setup canvas sizing
     */
    setupCanvas() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();

        // Set canvas size to match container
        this.canvas.width = rect.width;
        this.canvas.height = this.options.height;

        // Handle high DPI displays
        const dpr = window.devicePixelRatio || 1;
        if (dpr > 1) {
            this.canvas.width = rect.width * dpr;
            this.canvas.height = this.options.height * dpr;
            this.canvas.style.width = rect.width + 'px';
            this.canvas.style.height = this.options.height + 'px';
            this.ctx.scale(dpr, dpr);
        }

        // Redraw on window resize
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.draw();
        });
    }

    /**
     * Setup mouse event listeners
     */
    setupEventListeners() {
        this.canvas.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });

        this.canvas.addEventListener('mousedown', (e) => {
            this.handleMouseDown(e);
        });

        this.canvas.addEventListener('mouseup', (e) => {
            this.handleMouseUp(e);
        });

        this.canvas.addEventListener('mouseleave', () => {
            this.hoveredSegment = null;
            this.isDragging = false;
            this.draw();
        });

        this.canvas.addEventListener('click', (e) => {
            this.handleClick(e);
        });
    }

    /**
     * Load speaker segments
     */
    loadSegments(segments, duration) {
        this.segments = segments;
        this.duration = duration;
        this.draw();
    }

    /**
     * Update current playback time
     */
    updateTime(time) {
        this.currentTime = time;
        this.draw();
    }

    /**
     * Draw the timeline
     */
    draw() {
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);

        // Clear canvas
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, width, height);

        if (this.duration === 0) {
            return;
        }

        // Draw speaker segments
        this.drawSegments(width, height);

        // Draw playhead
        this.drawPlayhead(width, height);

        // Draw time markers
        this.drawTimeMarkers(width, height);
    }

    /**
     * Draw speaker segments
     */
    drawSegments(width, height) {
        const segmentY = (height - this.options.segmentHeight) / 2;

        this.segments.forEach((segment, index) => {
            const startX = (segment.start / this.duration) * width;
            const segmentWidth = ((segment.end - segment.start) / this.duration) * width;

            // Get speaker color
            const speaker = segment.speaker || 'SPEAKER_00';
            const baseColor = this.speakerColors[speaker] || '#666666';

            // Highlight hovered segment
            const isHovered = this.hoveredSegment === index;
            this.ctx.fillStyle = isHovered ? this.lightenColor(baseColor, 20) : baseColor;

            // Draw segment rectangle
            this.ctx.fillRect(startX, segmentY, segmentWidth, this.options.segmentHeight);

            // Draw segment border
            this.ctx.strokeStyle = isHovered ? this.options.hoverColor : 'rgba(255, 255, 255, 0.2)';
            this.ctx.lineWidth = isHovered ? 2 : 1;
            this.ctx.strokeRect(startX, segmentY, segmentWidth, this.options.segmentHeight);
        });
    }

    /**
     * Draw playhead position indicator
     */
    drawPlayhead(width, height) {
        const x = (this.currentTime / this.duration) * width;

        // Draw playhead line
        this.ctx.strokeStyle = this.options.playheadColor;
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x, height);
        this.ctx.stroke();

        // Draw playhead triangle at top
        this.ctx.fillStyle = this.options.playheadColor;
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x - 6, 10);
        this.ctx.lineTo(x + 6, 10);
        this.ctx.closePath();
        this.ctx.fill();
    }

    /**
     * Draw time markers
     */
    drawTimeMarkers(width, height) {
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        this.ctx.font = '10px Arial';
        this.ctx.textAlign = 'center';

        // Determine marker interval
        const markers = 10;
        const interval = this.duration / markers;

        for (let i = 0; i <= markers; i++) {
            const time = i * interval;
            const x = (time / this.duration) * width;
            const timeStr = AudioPlayer.formatTime(time);

            // Draw marker tick
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            this.ctx.moveTo(x, height - 15);
            this.ctx.lineTo(x, height - 5);
            this.ctx.stroke();

            // Draw time label
            this.ctx.fillText(timeStr, x, height - 2);
        }
    }

    /**
     * Handle mouse move
     */
    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;

        // Find hovered segment
        const time = (x / rect.width) * this.duration;
        let foundSegment = null;

        this.segments.forEach((segment, index) => {
            if (time >= segment.start && time <= segment.end) {
                foundSegment = index;
            }
        });

        if (foundSegment !== this.hoveredSegment) {
            this.hoveredSegment = foundSegment;
            this.draw();

            // Show tooltip
            if (foundSegment !== null && this.onSegmentHover) {
                const segment = this.segments[foundSegment];
                this.onSegmentHover(segment, e);
            }
        }

        // Update cursor
        this.canvas.style.cursor = foundSegment !== null ? 'pointer' : 'default';

        // Handle dragging
        if (this.isDragging) {
            this.seekToPosition(x, rect.width);
        }
    }

    /**
     * Handle mouse down
     */
    handleMouseDown(e) {
        this.isDragging = true;
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        this.seekToPosition(x, rect.width);
    }

    /**
     * Handle mouse up
     */
    handleMouseUp(e) {
        this.isDragging = false;
    }

    /**
     * Handle click
     */
    handleClick(e) {
        if (this.hoveredSegment !== null && this.onSegmentClick) {
            const segment = this.segments[this.hoveredSegment];
            this.onSegmentClick(segment);
        }
    }

    /**
     * Seek to position
     */
    seekToPosition(x, width) {
        const time = (x / width) * this.duration;
        if (this.onSeek) {
            this.onSeek(time);
        }
    }

    /**
     * Get current segment at time
     */
    getCurrentSegment(time) {
        return this.segments.find(seg => time >= seg.start && time <= seg.end);
    }

    /**
     * Lighten color by percentage
     */
    lightenColor(color, percent) {
        const num = parseInt(color.replace("#",""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
            (G<255?G<1?0:G:255)*0x100 +
            (B<255?B<1?0:B:255))
            .toString(16).slice(1);
    }
}

// Export for use in other modules
window.Timeline = Timeline;
