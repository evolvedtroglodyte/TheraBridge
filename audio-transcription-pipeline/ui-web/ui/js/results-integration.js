/**
 * Results Integration Module
 * Connects waveform visualizer and results display with the main app
 */

// Initialize global instances
let waveformVisualizer = null;
let resultsDisplay = null;
let exportManager = null;
let currentAudioFile = null;
let currentResultsData = null;
let currentZoomLevel = 0;

/**
 * Initialize results components
 */
function initializeResultsComponents() {
    // Initialize waveform visualizer
    waveformVisualizer = new WaveformVisualizer('waveformContainer');
    window.waveformVisualizer = waveformVisualizer; // Make globally accessible

    // Initialize results display
    resultsDisplay = new ResultsDisplay();
    window.resultsDisplay = resultsDisplay; // Make globally accessible

    // Initialize export manager
    exportManager = new ExportManager();
    window.exportManager = exportManager; // Make globally accessible

    // Set up event listeners
    setupResultsEventListeners();
    setupExportListeners();
    setupExportKeyboardShortcuts();

    console.log('Results components initialized');
}

/**
 * Set up event listeners for results view
 */
function setupResultsEventListeners() {
    // Play/Pause button
    const playBtn = document.getElementById('playBtn');
    if (playBtn) {
        playBtn.addEventListener('click', () => {
            waveformVisualizer.playPause();
            updatePlayButton();
        });
    }

    // Stop button
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            waveformVisualizer.stop();
            updatePlayButton();
        });
    }

    // Zoom in button
    const zoomInBtn = document.getElementById('zoomInBtn');
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            currentZoomLevel = Math.min(currentZoomLevel + 50, 500);
            waveformVisualizer.zoom(currentZoomLevel);
        });
    }

    // Zoom out button
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            currentZoomLevel = Math.max(currentZoomLevel - 50, 0);
            waveformVisualizer.zoom(currentZoomLevel);
        });
    }

    // New upload button
    const newUploadBtn = document.getElementById('newUploadBtn');
    if (newUploadBtn) {
        newUploadBtn.addEventListener('click', () => {
            resetToUpload();
        });
    }

    // Listen for waveform position updates
    document.addEventListener('waveform-position-update', (e) => {
        updatePlaybackTime(e.detail.currentTime, e.detail.duration);
    });

    // Listen for waveform ready event
    if (waveformVisualizer && waveformVisualizer.wavesurfer) {
        waveformVisualizer.wavesurfer.on('play', updatePlayButton);
        waveformVisualizer.wavesurfer.on('pause', updatePlayButton);
    }
}

/**
 * Set up export menu and button listeners
 */
function setupExportListeners() {
    const exportMenuBtn = document.getElementById('exportMenuBtn');
    const exportMenu = document.getElementById('exportMenu');
    const exportDropdown = document.querySelector('.export-dropdown');

    // Toggle dropdown menu
    if (exportMenuBtn && exportMenu) {
        exportMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportMenu.classList.toggle('hidden');
            exportDropdown?.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!exportDropdown?.contains(e.target)) {
                exportMenu.classList.add('hidden');
                exportDropdown?.classList.remove('active');
            }
        });
    }

    // Export format button listeners
    const exportButtons = document.querySelectorAll('.dropdown-item[data-export]');
    exportButtons.forEach(button => {
        button.addEventListener('click', () => {
            const format = button.dataset.export;
            handleExport(format);
            exportMenu?.classList.add('hidden');
            exportDropdown?.classList.remove('active');
        });
    });
}

/**
 * Set up keyboard shortcuts for export
 */
function setupExportKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Only trigger when results are visible
        const resultsVisible = document.getElementById('resultsContainer')?.style.display !== 'none';
        if (!resultsVisible) return;

        // Check for Ctrl/Cmd key combinations
        if (e.ctrlKey || e.metaKey) {
            switch(e.key.toLowerCase()) {
                case 's':
                    e.preventDefault();
                    handleExport('pdf');
                    break;
                case 't':
                    e.preventDefault();
                    handleExport('txt');
                    break;
                case 'c':
                    e.preventDefault();
                    handleExport('csv');
                    break;
                case 'j':
                    e.preventDefault();
                    handleExport('json');
                    break;
            }
        }
    });
}

/**
 * Handle export based on format
 */
function handleExport(format) {
    if (!currentResultsData || !exportManager) {
        console.error('No results data or export manager available');
        alert('No results to export');
        return;
    }

    const audioFilename = currentAudioFile?.name || 'audio.mp3';

    switch(format) {
        case 'pdf':
            exportManager.exportToPDF(currentResultsData, audioFilename);
            break;
        case 'txt':
            exportManager.exportToTXT(currentResultsData, audioFilename);
            break;
        case 'csv':
            exportManager.exportToCSV(currentResultsData, audioFilename);
            break;
        case 'json':
            exportManager.exportToJSON(currentResultsData, audioFilename);
            break;
        default:
            console.error('Unknown export format:', format);
    }
}

/**
 * Display results from pipeline output
 * @param {Object} resultsData - Pipeline output JSON
 * @param {File} audioFile - Original audio file
 */
async function displayPipelineResults(resultsData, audioFile) {
    try {
        // Store audio file and results data reference
        currentAudioFile = audioFile;
        currentResultsData = resultsData;

        // Initialize waveform
        await waveformVisualizer.initialize();
        await waveformVisualizer.loadAudio(audioFile);

        // Add speaker regions to waveform
        if (resultsData.aligned_transcript) {
            waveformVisualizer.addSpeakerRegions(resultsData.aligned_transcript);
        }

        // Display results
        resultsDisplay.displayResults(resultsData);

        console.log('Results displayed successfully');
    } catch (error) {
        console.error('Error displaying results:', error);
        showError('Failed to display results: ' + error.message);
    }
}

/**
 * Update play/pause button text
 */
function updatePlayButton() {
    const playBtn = document.getElementById('playBtn');
    if (!playBtn || !waveformVisualizer) return;

    if (waveformVisualizer.isPlaying()) {
        playBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="6" y="4" width="4" height="16"/>
                <rect x="14" y="4" width="4" height="16"/>
            </svg>
            Pause
        `;
    } else {
        playBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Play
        `;
    }
}

/**
 * Update playback time display
 */
function updatePlaybackTime(currentTime, duration) {
    const playbackTimeEl = document.getElementById('playbackTime');
    if (!playbackTimeEl) return;

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    playbackTimeEl.textContent = `${formatTime(currentTime)} / ${formatTime(duration)}`;
}

/**
 * Reset to upload view
 */
function resetToUpload() {
    // Destroy waveform
    if (waveformVisualizer) {
        waveformVisualizer.destroy();
    }

    // Reset results display
    if (resultsDisplay) {
        resultsDisplay.reset();
    }

    // Clear current file and data
    currentAudioFile = null;
    currentResultsData = null;
    currentZoomLevel = 0;

    // Show upload section, hide results
    const uploadSection = document.getElementById('uploadSection');
    const resultsContainer = document.getElementById('resultsContainer');

    if (uploadSection) uploadSection.style.display = 'block';
    if (resultsContainer) resultsContainer.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    const errorBanner = document.getElementById('errorBanner');
    const errorMessage = document.getElementById('errorMessage');

    if (errorBanner && errorMessage) {
        errorMessage.textContent = message;
        errorBanner.style.display = 'flex';
    }
}

/**
 * Demo function: Load sample results for testing
 */
function loadDemoResults() {
    const demoData = {
        aligned_transcript: [
            {
                speaker: 'SPEAKER_00',
                text: 'Hello, how are you feeling today?',
                start: 0.5,
                end: 3.2
            },
            {
                speaker: 'SPEAKER_01',
                text: "I've been feeling a bit anxious lately. There's a lot going on at work.",
                start: 3.8,
                end: 8.5
            },
            {
                speaker: 'SPEAKER_00',
                text: "I understand. Can you tell me more about what's been happening at work?",
                start: 9.0,
                end: 13.4
            },
            {
                speaker: 'SPEAKER_01',
                text: "Well, we have a big project deadline coming up, and I'm worried I won't be able to finish everything on time.",
                start: 14.0,
                end: 20.5
            },
            {
                speaker: 'SPEAKER_00',
                text: "That sounds stressful. Have you tried breaking down the project into smaller, manageable tasks?",
                start: 21.0,
                end: 27.3
            },
            {
                speaker: 'SPEAKER_01',
                text: "I have, but even the smaller tasks feel overwhelming. I think I might be taking on too much.",
                start: 28.0,
                end: 34.8
            },
            {
                speaker: 'SPEAKER_00',
                text: "It's important to recognize your limits. Let's talk about some strategies for managing your workload and reducing anxiety.",
                start: 35.5,
                end: 42.9
            }
        ],
        performance: {
            total_time: 45.2,
            audio_duration: 43.0,
            transcription_time: 12.3,
            diarization_time: 18.5,
            alignment_time: 2.1,
            rtf: 1.05,
            num_segments: 7,
            num_speakers: 2
        }
    };

    // Note: In production, you would load the actual audio file
    // For demo, you can use a sample audio URL or File object
    console.log('Demo data ready. Call displayPipelineResults(demoData, audioFile) when audio is loaded.');

    return demoData;
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeResultsComponents);
} else {
    initializeResultsComponents();
}

// Export functions for use in main app
window.displayPipelineResults = displayPipelineResults;
window.loadDemoResults = loadDemoResults;
window.resetToUpload = resetToUpload;
