/**
 * Results Display Module
 * Handles rendering of transcription results, speaker statistics, and metrics
 */

class ResultsDisplay {
    constructor() {
        this.currentResults = null;
        this.speakerColors = {
            'SPEAKER_00': '#3B82F6',
            'SPEAKER_01': '#10B981',
            'SPEAKER_02': '#F59E0B',
            'SPEAKER_03': '#EF4444',
            'SPEAKER_04': '#8B5CF6',
            'SPEAKER_05': '#EC4899',
            'SPEAKER_06': '#14B8A6',
            'SPEAKER_07': '#F97316',
        };
        this.speakerLabels = {
            'SPEAKER_00': 'Therapist',
            'SPEAKER_01': 'Client'
        };
    }

    /**
     * Display results from pipeline output
     */
    displayResults(resultsData) {
        this.currentResults = resultsData;

        // Show results container, hide upload section
        this.toggleContainers(true);

        // Render each component
        this.renderTranscript(resultsData.aligned_transcript || []);
        this.renderSpeakerStats(resultsData.aligned_transcript || []);
        this.renderProcessingMetrics(resultsData.performance || {});

        // Scroll to results
        document.getElementById('resultsContainer')?.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Toggle between upload and results containers
     */
    toggleContainers(showResults) {
        const uploadContainer = document.getElementById('uploadContainer');
        const resultsContainer = document.getElementById('resultsContainer');

        if (uploadContainer) {
            uploadContainer.style.display = showResults ? 'none' : 'block';
        }
        if (resultsContainer) {
            resultsContainer.style.display = showResults ? 'block' : 'none';
        }
    }

    /**
     * Render speaker-labeled transcript
     */
    renderTranscript(segments) {
        const container = document.getElementById('transcriptDisplay');
        if (!container) return;

        container.innerHTML = '';

        if (!segments || segments.length === 0) {
            container.innerHTML = '<p class="no-data">No transcript data available</p>';
            return;
        }

        segments.forEach((segment, index) => {
            const segmentDiv = document.createElement('div');
            segmentDiv.className = 'transcript-segment';
            segmentDiv.dataset.index = index;
            segmentDiv.dataset.speaker = segment.speaker;

            const speakerColor = this.speakerColors[segment.speaker] || '#64748B';
            const speakerLabel = this.speakerLabels[segment.speaker] || segment.speaker;

            segmentDiv.innerHTML = `
                <div class="segment-header">
                    <span class="speaker-badge" style="background-color: ${speakerColor}">
                        ${speakerLabel}
                    </span>
                    <span class="timestamp">
                        ${this.formatTimestamp(segment.start)} - ${this.formatTimestamp(segment.end)}
                    </span>
                </div>
                <div class="segment-text">${this.escapeHtml(segment.text)}</div>
            `;

            // Make segment clickable to seek in waveform
            segmentDiv.addEventListener('click', () => {
                this.seekToSegment(segment.start);
                this.highlightSegment(index);
            });

            container.appendChild(segmentDiv);
        });
    }

    /**
     * Render speaker statistics
     */
    renderSpeakerStats(segments) {
        const container = document.getElementById('speakerStats');
        if (!container) return;

        container.innerHTML = '';

        if (!segments || segments.length === 0) {
            container.innerHTML = '<p class="no-data">No speaker data available</p>';
            return;
        }

        // Calculate statistics per speaker
        const stats = this.calculateSpeakerStats(segments);

        // Create stats table
        const table = document.createElement('table');
        table.className = 'stats-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Speaker</th>
                    <th>Turns</th>
                    <th>Duration</th>
                    <th>Words</th>
                    <th>Avg Turn</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(stats).map(([speaker, data]) => {
                    const color = this.speakerColors[speaker] || '#64748B';
                    const label = this.speakerLabels[speaker] || speaker;
                    return `
                        <tr>
                            <td>
                                <span class="speaker-badge" style="background-color: ${color}">
                                    ${label}
                                </span>
                            </td>
                            <td>${data.turns}</td>
                            <td>${this.formatDuration(data.duration)}</td>
                            <td>${data.words}</td>
                            <td>${this.formatDuration(data.avgTurn)}</td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        `;

        container.appendChild(table);

        // Add speaker distribution chart
        this.renderSpeakerChart(stats);
    }

    /**
     * Calculate speaker statistics
     */
    calculateSpeakerStats(segments) {
        const stats = {};

        segments.forEach(segment => {
            const speaker = segment.speaker;
            if (!stats[speaker]) {
                stats[speaker] = {
                    turns: 0,
                    duration: 0,
                    words: 0
                };
            }

            stats[speaker].turns++;
            stats[speaker].duration += (segment.end - segment.start);
            stats[speaker].words += segment.text.split(/\s+/).length;
        });

        // Calculate average turn duration
        Object.keys(stats).forEach(speaker => {
            stats[speaker].avgTurn = stats[speaker].duration / stats[speaker].turns;
        });

        return stats;
    }

    /**
     * Render speaker distribution chart
     */
    renderSpeakerChart(stats) {
        const container = document.getElementById('speakerChart');
        if (!container) return;

        container.innerHTML = '';

        const totalDuration = Object.values(stats).reduce((sum, s) => sum + s.duration, 0);

        const chartDiv = document.createElement('div');
        chartDiv.className = 'speaker-chart';

        Object.entries(stats).forEach(([speaker, data]) => {
            const percentage = (data.duration / totalDuration * 100).toFixed(1);
            const color = this.speakerColors[speaker] || '#64748B';
            const label = this.speakerLabels[speaker] || speaker;

            const barDiv = document.createElement('div');
            barDiv.className = 'chart-bar';
            barDiv.innerHTML = `
                <div class="chart-label">
                    <span class="speaker-badge" style="background-color: ${color}">${label}</span>
                    <span class="chart-percentage">${percentage}%</span>
                </div>
                <div class="chart-bar-container">
                    <div class="chart-bar-fill" style="width: ${percentage}%; background-color: ${color}"></div>
                </div>
            `;

            chartDiv.appendChild(barDiv);
        });

        container.appendChild(chartDiv);
    }

    /**
     * Render processing metrics
     */
    renderProcessingMetrics(performance) {
        const container = document.getElementById('processingMetrics');
        if (!container) return;

        container.innerHTML = '';

        if (!performance || Object.keys(performance).length === 0) {
            container.innerHTML = '<p class="no-data">No performance data available</p>';
            return;
        }

        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'metrics-grid';

        // Common metrics to display
        const metrics = [
            { key: 'total_time', label: 'Total Time', format: (v) => this.formatDuration(v) },
            { key: 'audio_duration', label: 'Audio Duration', format: (v) => this.formatDuration(v) },
            { key: 'transcription_time', label: 'Transcription', format: (v) => this.formatDuration(v) },
            { key: 'diarization_time', label: 'Diarization', format: (v) => this.formatDuration(v) },
            { key: 'alignment_time', label: 'Alignment', format: (v) => this.formatDuration(v) },
            { key: 'rtf', label: 'Real-time Factor', format: (v) => v.toFixed(2) + 'x' },
            { key: 'num_segments', label: 'Segments', format: (v) => v.toString() },
            { key: 'num_speakers', label: 'Speakers', format: (v) => v.toString() },
        ];

        metrics.forEach(({ key, label, format }) => {
            if (performance[key] !== undefined) {
                const metricDiv = document.createElement('div');
                metricDiv.className = 'metric-item';
                metricDiv.innerHTML = `
                    <div class="metric-label">${label}</div>
                    <div class="metric-value">${format(performance[key])}</div>
                `;
                metricsDiv.appendChild(metricDiv);
            }
        });

        container.appendChild(metricsDiv);
    }

    /**
     * Format timestamp to MM:SS
     */
    formatTimestamp(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Format duration to human-readable string
     */
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        } else if (seconds < 3600) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}m ${secs}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${mins}m`;
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Seek to segment in waveform
     */
    seekToSegment(startTime) {
        document.dispatchEvent(new CustomEvent('seek-to-time', {
            detail: { time: startTime }
        }));
    }

    /**
     * Highlight segment
     */
    highlightSegment(index) {
        // Remove previous highlights
        document.querySelectorAll('.transcript-segment.active').forEach(el => {
            el.classList.remove('active');
        });

        // Add highlight to current segment
        const segment = document.querySelector(`.transcript-segment[data-index="${index}"]`);
        if (segment) {
            segment.classList.add('active');
            segment.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Export transcript as text
     */
    exportTranscript() {
        if (!this.currentResults || !this.currentResults.aligned_transcript) {
            alert('No transcript to export');
            return;
        }

        let text = 'Audio Transcription\n';
        text += '===================\n\n';

        this.currentResults.aligned_transcript.forEach(segment => {
            const speaker = this.speakerLabels[segment.speaker] || segment.speaker;
            const timestamp = `[${this.formatTimestamp(segment.start)} - ${this.formatTimestamp(segment.end)}]`;
            text += `${speaker} ${timestamp}:\n${segment.text}\n\n`;
        });

        // Download as file
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'transcript.txt';
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Export results as JSON
     */
    exportJSON() {
        if (!this.currentResults) {
            alert('No results to export');
            return;
        }

        const blob = new Blob([JSON.stringify(this.currentResults, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'results.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Reset and return to upload view
     */
    reset() {
        this.currentResults = null;
        this.toggleContainers(false);

        // Clear all displays
        ['transcriptDisplay', 'speakerStats', 'processingMetrics', 'speakerChart'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '';
        });
    }
}

// Initialize event listeners for cross-component communication
document.addEventListener('segment-highlight', (e) => {
    const display = window.resultsDisplay;
    if (display) {
        display.highlightSegment(e.detail.index);
    }
});

document.addEventListener('seek-to-time', (e) => {
    const waveform = window.waveformVisualizer;
    if (waveform && waveform.wavesurfer) {
        const duration = waveform.wavesurfer.getDuration();
        const progress = e.detail.time / duration;
        waveform.seekTo(progress);
    }
});

// Export for global access
window.ResultsDisplay = ResultsDisplay;
