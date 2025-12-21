# Results Display Component Documentation

## Overview

The Results Display Component provides a comprehensive visualization interface for audio transcription pipeline results, featuring:

- **Waveform Visualization**: Interactive audio waveform with speaker diarization regions
- **Speaker-Labeled Transcript**: Clickable transcript with color-coded speakers
- **Speaker Statistics**: Detailed analytics on speaker participation
- **Processing Metrics**: Performance data from the pipeline
- **Export Functionality**: Export transcript as text or full results as JSON

## Architecture

### Components

1. **waveform.js** (`WaveformVisualizer` class)
   - Waveform rendering using WaveSurfer.js
   - Speaker region visualization
   - Audio playback controls
   - Zoom functionality
   - Click-to-seek interaction

2. **results.js** (`ResultsDisplay` class)
   - Transcript rendering with speaker labels
   - Speaker statistics calculation
   - Processing metrics display
   - Export functionality
   - Cross-component event communication

3. **results-integration.js**
   - Integration layer between components
   - Event handler setup
   - Demo data loader
   - Global initialization

4. **results-styles.css**
   - Complete styling for all components
   - Responsive design
   - Print-friendly styles
   - Dark/light theme support (inherits from main styles)

## Usage

### Basic Integration

```javascript
// Initialize on page load (automatically done in results-integration.js)
// Components are initialized when DOM loads

// Display results from pipeline
const resultsData = {
    aligned_transcript: [
        {
            speaker: 'SPEAKER_00',
            text: 'Hello, how are you?',
            start: 0.5,
            end: 3.2
        },
        // ... more segments
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

const audioFile = /* File object from input */;

// Display results
await displayPipelineResults(resultsData, audioFile);
```

### Data Format

The component expects pipeline output in this format:

```json
{
  "aligned_transcript": [
    {
      "speaker": "SPEAKER_00",
      "text": "Transcript text here",
      "start": 0.5,
      "end": 3.2
    }
  ],
  "performance": {
    "total_time": 45.2,
    "audio_duration": 43.0,
    "transcription_time": 12.3,
    "diarization_time": 18.5,
    "alignment_time": 2.1,
    "rtf": 1.05,
    "num_segments": 7,
    "num_speakers": 2
  }
}
```

### API Reference

#### WaveformVisualizer

```javascript
const visualizer = new WaveformVisualizer('containerId');

// Initialize WaveSurfer
await visualizer.initialize();

// Load audio file
await visualizer.loadAudio(audioFile);

// Add speaker regions
visualizer.addSpeakerRegions(segments);

// Playback control
visualizer.playPause();
visualizer.stop();
visualizer.seekTo(0.5); // 0-1 progress

// Zoom control
visualizer.zoom(50); // Zoom level 0-500

// Cleanup
visualizer.destroy();
```

#### ResultsDisplay

```javascript
const display = new ResultsDisplay();

// Display full results
display.displayResults(resultsData);

// Export functions
display.exportTranscript(); // Download as .txt
display.exportJSON();       // Download as .json

// Reset view
display.reset();

// Utility functions
display.highlightSegment(index);
display.seekToSegment(startTime);
```

## Features

### 1. Waveform Visualization

- **Library**: WaveSurfer.js v7 (loaded via CDN)
- **Features**:
  - Interactive waveform rendering
  - Speaker regions with color coding
  - Click regions to play that segment
  - Playback position indicator
  - Zoom in/out controls
  - Responsive canvas sizing

### 2. Speaker-Labeled Transcript

- Color-coded speaker badges (consistent across all views)
- Clickable segments to seek in audio
- Timestamp display (MM:SS format)
- Active segment highlighting
- Auto-scroll to active segment
- Professional layout with hover effects

### 3. Speaker Statistics

- **Metrics per speaker**:
  - Number of speaking turns
  - Total speaking duration
  - Word count
  - Average turn duration

- **Visual chart**:
  - Speaking time distribution
  - Percentage breakdown
  - Color-coded bars

### 4. Processing Metrics

Grid display of pipeline performance:
- Total processing time
- Audio duration
- Individual stage times (transcription, diarization, alignment)
- Real-time factor (RTF)
- Number of segments and speakers

### 5. Export Functionality

**Export Transcript** (`.txt`):
```
Audio Transcription
===================

Therapist [00:00 - 00:03]:
Hello, how are you feeling today?

Client [00:03 - 00:08]:
I've been feeling a bit anxious lately...
```

**Export JSON** (`.json`):
Full pipeline results with all metadata

### 6. Keyboard Shortcuts

Managed by results-integration.js:
- **Space**: Play/Pause
- **Arrow Left/Right**: Seek ±5 seconds
- **+/-**: Zoom in/out

## Speaker Color Mapping

Consistent color scheme across all components:

| Speaker | Color | Hex Code | Use Case |
|---------|-------|----------|----------|
| SPEAKER_00 | Blue | #3B82F6 | Therapist (primary) |
| SPEAKER_01 | Green | #10B981 | Client (secondary) |
| SPEAKER_02 | Amber | #F59E0B | Additional speaker |
| SPEAKER_03 | Red | #EF4444 | Additional speaker |
| SPEAKER_04 | Purple | #8B5CF6 | Additional speaker |
| SPEAKER_05 | Pink | #EC4899 | Additional speaker |
| SPEAKER_06 | Teal | #14B8A6 | Additional speaker |
| SPEAKER_07 | Orange | #F97316 | Additional speaker |

Default (unknown): Gray (#64748B)

## Custom Speaker Labels

Override default speaker labels in `results.js`:

```javascript
this.speakerLabels = {
    'SPEAKER_00': 'Therapist',
    'SPEAKER_01': 'Client',
    'SPEAKER_02': 'Observer'
};
```

## Cross-Component Events

The components communicate via custom DOM events:

```javascript
// Waveform → Transcript
document.dispatchEvent(new CustomEvent('segment-highlight', {
    detail: { index: 0 }
}));

// Transcript → Waveform
document.dispatchEvent(new CustomEvent('seek-to-time', {
    detail: { time: 10.5 }
}));

// Waveform → Timeline
document.dispatchEvent(new CustomEvent('waveform-position-update', {
    detail: { currentTime: 10.5, duration: 120 }
}));
```

## Responsive Design

Breakpoints:
- **Desktop** (>1024px): 2-column grid (transcript + stats)
- **Tablet** (768px-1024px): 1-column stack
- **Mobile** (<768px): Compact layout, smaller fonts

## Print Styles

Optimized for printing transcripts:
- Hides controls and interactive elements
- Shows only transcript and speaker stats
- Black and white speaker badges
- Page break prevention for segments
- 1-inch margins

## Testing

### Demo Mode

Load sample results for testing:

```javascript
// In browser console
const demoData = loadDemoResults();
console.log(demoData);

// Then call with actual audio file:
// displayPipelineResults(demoData, audioFile);
```

### Sample HTML

The component is already integrated into `index.html`. To test:

1. Open `index.html` in browser
2. Process an audio file (or wait for backend integration)
3. Results display automatically when processing completes

## Dependencies

- **WaveSurfer.js v7**: Loaded via CDN
  ```html
  <script src="https://unpkg.com/wavesurfer.js@7"></script>
  ```

- **No other external dependencies**: Pure vanilla JavaScript

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (WaveSurfer.js uses WebAudio API)
- Mobile browsers: Responsive design tested on iOS Safari and Chrome Android

## Performance Considerations

- **Large files**: Waveform rendering may be slow for very long audio (>2 hours)
- **Many segments**: Transcript rendering is optimized with virtual scrolling in mind
- **Memory**: Audio file is kept in memory for playback - may impact performance on low-memory devices

## Future Enhancements

Potential improvements for future iterations:
- [ ] Virtual scrolling for very long transcripts (1000+ segments)
- [ ] Speaker name editing (rename SPEAKER_00 to custom name)
- [ ] Search/filter transcript
- [ ] Highlight keywords
- [ ] Speaker voice comparison (audio fingerprinting)
- [ ] Multi-language support
- [ ] Real-time processing progress (streaming results)

## Troubleshooting

### Waveform not loading
- Check browser console for errors
- Verify WaveSurfer.js CDN is accessible
- Ensure audio file format is supported (MP3, WAV, M4A, etc.)

### Regions not displaying
- Verify `aligned_transcript` data has `start` and `end` times
- Check that times are in seconds (not milliseconds)
- Ensure speaker IDs match expected format (`SPEAKER_00`, etc.)

### Export not working
- Check browser allows downloads
- Verify results data is loaded (`resultsDisplay.currentResults`)
- Try exporting from browser console: `resultsDisplay.exportTranscript()`

## File Structure

```
ui/
├── index.html                  # Main HTML (results section integrated)
├── styles.css                  # Main styles
├── results-styles.css          # Results-specific styles
├── js/
│   ├── waveform.js            # Waveform visualizer
│   ├── results.js             # Results display
│   ├── results-integration.js # Integration layer
│   ├── player.js              # Audio player (Frontend Dev #1)
│   └── timeline.js            # Timeline canvas (Frontend Dev #1)
└── RESULTS_COMPONENT.md       # This documentation
```

## Integration with Backend

When connecting to the backend API:

```javascript
// Example API integration
async function processAndDisplayResults(audioFile) {
    try {
        // Upload and process
        const formData = new FormData();
        formData.append('audio', audioFile);

        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        const results = await response.json();

        // Display results
        await displayPipelineResults(results, audioFile);

    } catch (error) {
        console.error('Processing failed:', error);
        showError('Failed to process audio');
    }
}
```

## Credits

- **WaveSurfer.js**: https://wavesurfer-js.org/
- **Design**: Tailwind CSS inspired utility classes
- **Icons**: Inline SVG (Feather Icons style)

---

**Last Updated**: December 2025
**Version**: 1.0.0
**Author**: Frontend Dev #2 (Wave 1 - Results Display)
