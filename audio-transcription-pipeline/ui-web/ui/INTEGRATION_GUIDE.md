# Wave 1 Integration Guide

## How to Connect All Components

This guide shows how to connect the three Wave 1 components (Upload UI, Waveform/Transcript, Player/Timeline) in the main `app.js` file.

## Component Responsibilities

### Frontend Dev #1: Upload UI
- File selection and drag-drop
- Upload progress tracking
- Processing status display
- Triggers result display when complete

### Frontend Dev #2: Waveform & Transcript
- Waveform visualization
- Transcript display with speaker labels
- Speaker statistics
- Export functionality

### Frontend Dev #3: Audio Player & Timeline
- Audio playback controls
- Speaker timeline visualization
- Keyboard shortcuts
- Synchronization with all components

## Integration in app.js

```javascript
// ========================================
// Global State
// ========================================
let playerIntegration = null;
let currentAudioUrl = null;
let currentResults = null;

// ========================================
// Initialize Components on Page Load
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Frontend Dev #1: Initialize upload handlers
    initializeUploadUI();

    // Frontend Dev #3: Initialize player integration
    playerIntegration = new PlayerIntegration();

    // Setup component connections
    setupComponentSync();
});

// ========================================
// Upload Flow (Frontend Dev #1)
// ========================================
function initializeUploadUI() {
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');

    uploadBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        // Show processing section
        showProcessingSection();

        // Upload and process
        try {
            const results = await uploadAndProcess(file);
            displayResults(results);
        } catch (error) {
            showError(error.message);
        }
    });
}

async function uploadAndProcess(file) {
    // Upload logic here
    // ... (Frontend Dev #1 implementation)

    // Mock response for demonstration
    return {
        audioUrl: '/path/to/audio.mp3',
        segments: [...],
        transcript: [...],
        duration: 120.5,
        speakers: {...}
    };
}

// ========================================
// Display Results (All Developers)
// ========================================
function displayResults(results) {
    currentResults = results;
    currentAudioUrl = results.audioUrl;

    // Hide upload/processing, show results
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';

    // Frontend Dev #2: Render waveform and transcript
    if (window.renderWaveform) {
        window.renderWaveform(results.audioUrl);
    }
    if (window.renderTranscript) {
        window.renderTranscript(results.transcript, results.segments);
    }
    if (window.renderSpeakerStats) {
        window.renderSpeakerStats(results.speakers);
    }

    // Frontend Dev #3: Load audio player and timeline
    playerIntegration.loadResults(results.audioUrl, results);

    // Setup synchronization
    syncAllComponents();
}

// ========================================
// Component Synchronization
// ========================================
function setupComponentSync() {
    // Connect player to waveform when available
    if (window.waveformInstance) {
        playerIntegration.setWaveform(window.waveformInstance);
    }

    // Setup transcript click-to-seek
    const transcriptEl = document.getElementById('transcriptDisplay');
    if (transcriptEl) {
        playerIntegration.setupTranscriptSync(transcriptEl);
    }
}

function syncAllComponents() {
    // This is called after results are loaded

    // Connect waveform to player
    if (window.waveformInstance) {
        playerIntegration.setWaveform(window.waveformInstance);

        // Bidirectional sync
        window.waveformInstance.onSeek = (time) => {
            playerIntegration.player.seekTo(time);
        };
    }

    // Connect transcript to player
    const transcriptEl = document.getElementById('transcriptDisplay');
    if (transcriptEl) {
        playerIntegration.setupTranscriptSync(transcriptEl);

        // Add click handlers to transcript segments
        transcriptEl.querySelectorAll('.transcript-segment').forEach(segment => {
            segment.addEventListener('click', () => {
                const time = parseFloat(segment.dataset.start);
                playerIntegration.player.seekTo(time);
            });
        });
    }

    // Sync timeline with waveform
    playerIntegration.timeline.onSeek = (time) => {
        playerIntegration.player.seekTo(time);
        if (window.waveformInstance && window.waveformInstance.seek) {
            window.waveformInstance.seek(time);
        }
    };
}

// ========================================
// Error Handling
// ========================================
function showError(message) {
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

// ========================================
// UI State Management
// ========================================
function showProcessingSection() {
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'block';
}

function showUploadSection() {
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'none';
}

// New upload button
document.getElementById('newUploadBtn')?.addEventListener('click', () => {
    // Reset state
    if (playerIntegration) {
        playerIntegration.player.pause();
        playerIntegration.player.seekTo(0);
    }

    // Show upload section
    showUploadSection();
});
```

## Expected Data Format

### Diarization Results Object
```javascript
{
    audioUrl: '/path/to/audio.mp3',  // Audio file URL
    duration: 120.5,                  // Total duration in seconds

    segments: [                       // Speaker segments
        {
            start: 0.0,               // Start time in seconds
            end: 5.5,                 // End time in seconds
            speaker: 'SPEAKER_00',    // Speaker ID
            text: 'Hello world'       // Transcript text
        },
        // ... more segments
    ],

    transcript: [                     // Full transcript
        {
            timestamp: '00:00',
            speaker: 'SPEAKER_00',
            text: 'Hello world'
        },
        // ... more entries
    ],

    speakers: {                       // Speaker statistics
        'SPEAKER_00': {
            totalTime: 45.2,
            segments: 12,
            percentage: 37.7
        },
        // ... more speakers
    }
}
```

## Component Communication

### Player → Timeline
```javascript
player.onTimeUpdate = (time) => {
    timeline.updateTime(time);
};
```

### Timeline → Player
```javascript
timeline.onSeek = (time) => {
    player.seekTo(time);
};
```

### Player → Waveform
```javascript
player.onTimeUpdate = (time) => {
    waveform.updatePlayhead(time);
};
```

### Waveform → Player
```javascript
waveform.onSeek = (time) => {
    player.seekTo(time);
};
```

### Player → Transcript
```javascript
player.onTimeUpdate = (time) => {
    const segment = timeline.getCurrentSegment(time);
    highlightTranscriptSegment(segment);
    autoScrollToSegment(segment);
};
```

### Transcript → Player
```javascript
transcriptSegment.addEventListener('click', () => {
    const time = parseFloat(segment.dataset.start);
    player.seekTo(time);
});
```

## HTML Data Attributes for Transcript

Each transcript segment should have these data attributes for click-to-seek:

```html
<div class="transcript-segment" data-start="15.5" data-end="18.2">
    <span class="speaker">SPEAKER_00</span>
    <span class="timestamp">00:15</span>
    <span class="text">This is the transcript text.</span>
</div>
```

## Testing the Integration

1. **Upload Flow:**
   - Select file → Upload → Processing → Results display

2. **Player Controls:**
   - Play/pause works
   - Volume slider adjusts audio
   - Speed selector changes rate

3. **Timeline Interaction:**
   - Click timeline → Audio seeks
   - Playhead moves with audio
   - Hover shows segment tooltip

4. **Waveform Sync:**
   - Waveform playhead matches audio
   - Click waveform → Audio seeks

5. **Transcript Sync:**
   - Current segment highlights
   - Auto-scrolls during playback
   - Click segment → Audio seeks

6. **Keyboard Shortcuts:**
   - Space plays/pauses
   - Arrow keys skip
   - Number keys jump to percentage

## Troubleshooting

### Audio won't play
- Check audio URL is valid
- Check CORS headers if cross-origin
- Check browser console for errors
- Verify audio format is supported (MP3, WAV, M4A)

### Timeline not rendering
- Check canvas element exists
- Verify segments data format
- Check browser console for Canvas errors
- Ensure parent container has width

### Sync issues
- Verify all callbacks are set
- Check data-start attributes on transcript
- Ensure components are initialized in order
- Check for JavaScript errors in console

### Keyboard shortcuts not working
- Check for input focus (shortcuts disabled in inputs)
- Verify event listeners are attached
- Check browser console for errors

## Performance Tips

1. **Canvas Rendering:**
   - Timeline redraws only on time update or user interaction
   - Uses requestAnimationFrame for smooth playhead

2. **Event Throttling:**
   - Time updates are throttled to 60fps max
   - Resize events are debounced

3. **DOM Updates:**
   - Transcript highlighting uses class toggling (minimal reflow)
   - Auto-scroll uses smooth behavior with block: 'nearest'

## Browser Compatibility

- **Recommended:** Chrome 90+, Firefox 88+, Safari 14+
- **Minimum:** Any browser with HTML5 Audio + Canvas support
- **Mobile:** Touch-optimized controls, responsive layout
- **Accessibility:** Keyboard navigation, ARIA labels, semantic HTML
