# Audio Player & Timeline Components - Frontend Dev #3

## Overview
This document describes the audio playback and timeline visualization components created for the Audio Transcription UI (Wave 1, Instance I3).

## Files Created

### JavaScript Modules

#### 1. `/ui/js/player.js` - Audio Player Module
**Purpose:** HTML5 audio playback engine with full control capabilities

**Features:**
- HTML5 Audio API wrapper
- Play/pause/seek functionality
- Volume control (0.0 to 1.0)
- Playback speed control (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x)
- Comprehensive keyboard shortcuts
- Event callbacks for synchronization
- Time formatting utilities

**Keyboard Shortcuts:**
- `Space` or `K` - Play/Pause
- `←` - Skip back 5 seconds
- `→` - Skip forward 5 seconds
- `J` - Skip back 10 seconds
- `L` - Skip forward 10 seconds
- `M` - Toggle mute
- `0-9` - Jump to 0%-90% of audio

**Public API:**
```javascript
const player = new AudioPlayer();
await player.loadAudio(audioUrl);
player.play();
player.pause();
player.seekTo(time);
player.setVolume(0.8);
player.setPlaybackRate(1.5);
```

#### 2. `/ui/js/timeline.js` - Timeline Visualization Module
**Purpose:** Interactive speaker segment timeline with canvas rendering

**Features:**
- Canvas-based timeline rendering
- Color-coded speaker segments
- Interactive playhead indicator
- Click-to-seek functionality
- Segment hover tooltips
- Time markers
- High-DPI display support
- Responsive canvas sizing

**Speaker Colors:**
- SPEAKER_00 / Therapist: Blue (#3b82f6)
- SPEAKER_01 / Client: Red (#ef4444)
- SPEAKER_02: Green (#10b981)
- SPEAKER_03: Orange (#f59e0b)
- SPEAKER_04: Purple (#8b5cf6)
- SPEAKER_05: Pink (#ec4899)

**Public API:**
```javascript
const timeline = new Timeline('timelineCanvas', options);
timeline.loadSegments(segments, duration);
timeline.updateTime(currentTime);
timeline.onSeek = (time) => { /* handle seek */ };
timeline.onSegmentClick = (segment) => { /* handle click */ };
```

#### 3. `/ui/js/player-integration.js` - Integration Module
**Purpose:** Synchronizes player, timeline, waveform, and transcript

**Features:**
- Bidirectional sync between all components
- Automatic UI updates
- Current segment highlighting
- Auto-scroll transcript to playback position
- Error handling
- Segment tooltip display

**Integration:**
```javascript
const integration = new PlayerIntegration();
integration.loadResults(audioUrl, diarizationResults);
integration.setWaveform(waveformInstance); // Optional
integration.setupTranscriptSync(transcriptContainer); // Optional
```

## HTML Structure

### Audio Controls Section
Located in `index.html` at the results section:

```html
<div class="player-controls-section">
    <div class="audio-controls">
        <!-- Play/Pause Button -->
        <button id="playPauseBtn">...</button>

        <!-- Time Display -->
        <div class="time-display">
            <span id="currentTime">0:00</span>
            <span>/</span>
            <span id="totalDuration">0:00</span>
        </div>

        <!-- Volume Control -->
        <div class="volume-control">
            <button id="muteBtn">...</button>
            <input type="range" id="volumeSlider">
        </div>

        <!-- Playback Speed -->
        <div class="speed-control">
            <select id="speedSelect">...</select>
        </div>

        <!-- Shortcuts Button -->
        <button id="shortcutsBtn">...</button>
    </div>
</div>
```

### Timeline Section
```html
<div class="timeline-section">
    <h3>Speaker Timeline</h3>
    <div class="timeline-container">
        <canvas id="timelineCanvas"></canvas>
    </div>
    <div id="segmentTooltip" class="segment-tooltip hidden"></div>
</div>
```

### Keyboard Shortcuts Modal
```html
<div id="shortcutsModal" class="modal hidden">
    <!-- Modal content with keyboard shortcuts grid -->
</div>
```

## CSS Styling

### Player Controls (`styles.css`)
- Flexbox layout with responsive wrapping
- Professional dark/light theme support
- Custom styled volume slider
- Hover effects and transitions
- Mobile-responsive design

### Timeline Visualization
- Full-width canvas container
- Smooth animations
- Hover tooltips with segment info
- Responsive padding and spacing

### Keyboard Shortcuts Modal
- Centered overlay modal
- Grid layout for shortcuts
- Styled `<kbd>` elements
- Fade-in animations
- Click-outside-to-close

## Synchronization Architecture

### Data Flow
```
Audio Playback → Player Module
                    ↓
              Time Updates
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Timeline    Waveform   Transcript
    (Instance I3) (Instance I2) (Instance I2)
```

### Event Chain
1. **Audio plays** → `player.onTimeUpdate(time)`
2. **Timeline updates** → `timeline.updateTime(time)`
3. **Current segment detected** → Highlight in transcript
4. **Waveform syncs** → Playhead position updates
5. **User clicks timeline** → `timeline.onSeek(time)` → `player.seekTo(time)`

## Integration with Other Components

### Frontend Dev #1 (Upload UI)
- No direct integration needed
- Player appears only after upload completes

### Frontend Dev #2 (Waveform & Transcript)
**Waveform Sync:**
```javascript
// In results-integration.js or app.js
playerIntegration.setWaveform(waveformInstance);
```

**Transcript Sync:**
```javascript
// Setup click handlers for transcript segments
playerIntegration.setupTranscriptSync(transcriptContainer);

// Add data attributes to transcript segments
<div class="transcript-segment" data-start="15.5" data-end="18.2">
    ...
</div>
```

## Usage Example

```javascript
// Initialize the integration (happens automatically when scripts load)
const playerIntegration = new PlayerIntegration();

// Load results after processing completes
const audioUrl = '/path/to/audio.mp3';
const diarizationResults = {
    segments: [
        {
            start: 0.0,
            end: 5.5,
            speaker: 'SPEAKER_00',
            text: 'Hello, how are you today?'
        },
        {
            start: 5.5,
            end: 10.2,
            speaker: 'SPEAKER_01',
            text: 'I am doing well, thank you.'
        }
    ],
    transcript: [...],
    duration: 120.5
};

playerIntegration.loadResults(audioUrl, diarizationResults);

// Optional: Connect to waveform component
if (window.waveformInstance) {
    playerIntegration.setWaveform(window.waveformInstance);
}

// Optional: Setup transcript click-to-seek
const transcriptEl = document.getElementById('transcriptContent');
if (transcriptEl) {
    playerIntegration.setupTranscriptSync(transcriptEl);
}
```

## Testing Checklist

- [ ] Audio loads and plays correctly
- [ ] Play/pause button toggles properly
- [ ] Timeline displays speaker segments
- [ ] Clicking timeline seeks to position
- [ ] Volume control adjusts audio
- [ ] Speed control changes playback rate
- [ ] Keyboard shortcuts work (all 7 types)
- [ ] Time display updates during playback
- [ ] Playhead indicator moves smoothly
- [ ] Segment tooltips show on hover
- [ ] Shortcuts modal opens/closes
- [ ] Responsive on mobile devices
- [ ] Dark/light theme compatibility
- [ ] High-DPI displays render correctly
- [ ] Sync with waveform (if available)
- [ ] Sync with transcript (if available)

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (webkit prefixes included)
- Mobile browsers: ✅ Touch-friendly controls

## Performance Notes

- Canvas rendering is optimized for 60fps
- Uses requestAnimationFrame for smooth playhead updates
- High-DPI scaling handled automatically
- Debounced resize events prevent layout thrashing
- Minimal DOM manipulation during playback

## Future Enhancements (Post-Wave 1)

- [ ] Waveform-style mini timeline above main timeline
- [ ] Segment editing (drag to adjust boundaries)
- [ ] Speaker label editing
- [ ] Bookmarks/markers
- [ ] Loop region selection
- [ ] Multi-track timeline for overlapping speech
- [ ] Export timeline as image
- [ ] A/B comparison mode

## Dependencies

- None (vanilla JavaScript)
- Uses HTML5 Audio API
- Canvas 2D rendering context
- CSS variables for theming

## Browser APIs Used

- `HTMLAudioElement`
- `HTMLCanvasElement` + 2D context
- `KeyboardEvent` for shortcuts
- `MouseEvent` for timeline interaction
- `devicePixelRatio` for high-DPI support

## Notes for Integration

1. **Load Order:** Player.js and Timeline.js must load before PlayerIntegration.js
2. **Canvas Sizing:** Timeline canvas auto-sizes to container width
3. **Theme Support:** Uses CSS variables, updates automatically on theme change
4. **Event Delegation:** Click handlers use delegation for transcript sync
5. **Error Handling:** Shows error banner if audio fails to load

## Contact

Frontend Dev #3 (Instance I3)
Wave 1 - Audio Transcription UI
Component: Audio Player & Timeline Visualization
