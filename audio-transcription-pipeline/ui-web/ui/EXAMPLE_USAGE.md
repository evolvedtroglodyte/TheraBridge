# Results Display - Example Usage

## Quick Start Example

This demonstrates how to use the Results Display component with sample data.

### 1. Open the UI in Browser

```bash
# From the ui/ directory
open index.html
# or
python -m http.server 8080
# then navigate to http://localhost:8080
```

### 2. Load Demo Data via Console

Open browser developer console (F12) and run:

```javascript
// Load demo results data
const demoData = loadDemoResults();

// Create a demo audio file (you can also use a real File object from file input)
const audioUrl = 'path/to/your/audio.mp3';

// Display results
displayPipelineResults(demoData, audioUrl);
```

### 3. Sample Integration Code

Here's how to integrate with your backend API:

```javascript
// Example: Process audio and display results
async function handleAudioProcessing() {
    const fileInput = document.getElementById('fileInput');
    const audioFile = fileInput.files[0];

    if (!audioFile) {
        alert('Please select an audio file');
        return;
    }

    try {
        // Show processing UI
        showProcessingScreen();

        // Upload to backend
        const formData = new FormData();
        formData.append('audio', audioFile);

        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Processing failed');
        }

        const results = await response.json();

        // Display results
        await displayPipelineResults(results, audioFile);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}
```

## Visual Output Example

When you display results, users will see:

### 1. Results Header
```
┌─────────────────────────────────────────────────────────┐
│ Diarization Results                                     │
│                [Export Transcript] [Export JSON] [New]  │
└─────────────────────────────────────────────────────────┘
```

### 2. Audio Waveform
```
┌─────────────────────────────────────────────────────────┐
│ Audio Waveform                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │▁▂▃▅▇█████▇▅▃▂▁▁▂▃▅▇██████▇▅▃▂▁▁▂▃▅▇████▇▅▃▂▁│ │
│ │  ▓▓▓░░░  ▓▓▓░░░░░  ▓▓▓░░░      (regions)   │ │
│ │  Blue    Green     Blue                      │ │
│ └─────────────────────────────────────────────────────┘ │
│ [Play] [Stop] [Zoom In] [Zoom Out]    00:23 / 01:45   │
└─────────────────────────────────────────────────────────┘
```

### 3. Processing Metrics
```
┌─────────────────────────────────────────────────────────┐
│ Processing Metrics                                      │
│ ┌────────────┬──────────────┬──────────────┬─────────┐ │
│ │ Total Time │ Audio Length │ Transcription│   RTF   │ │
│ │   45.2s    │    43.0s     │    12.3s     │  1.05x  │ │
│ └────────────┴──────────────┴──────────────┴─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4. Transcript Display (Left Column)
```
┌──────────────────────────────────────────────────────────┐
│ Speaker-Labeled Transcript                               │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ┌──────────────────────────────────────────────────┐ │ │
│ │ │ [Therapist] 00:00 - 00:03                        │ │ │
│ │ │ Hello, how are you feeling today?                │ │ │
│ │ └──────────────────────────────────────────────────┘ │ │
│ │                                                      │ │ │
│ │ ┌──────────────────────────────────────────────────┐ │ │
│ │ │ [Client] 00:03 - 00:08                           │ │ │
│ │ │ I've been feeling a bit anxious lately. There's  │ │ │
│ │ │ a lot going on at work.                          │ │ │
│ │ └──────────────────────────────────────────────────┘ │ │
│ │                                                      │ │ │
│ │ ┌──────────────────────────────────────────────────┐ │ │
│ │ │ [Therapist] 00:09 - 00:13                        │ │ │
│ │ │ I understand. Can you tell me more about what's  │ │ │
│ │ │ been happening at work?                          │ │ │
│ │ └──────────────────────────────────────────────────┘ │ │
│ │                                                      │ │ │
│ │ (scrollable...)                                      │ │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 5. Speaker Statistics (Right Column)
```
┌──────────────────────────────────────────────────────────┐
│ Speaker Statistics                                       │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Speaker   │ Turns │ Duration │ Words │ Avg Turn     │ │
│ │───────────┼───────┼──────────┼───────┼──────────────│ │
│ │ Therapist │   4   │  18.2s   │  120  │   4.5s       │ │
│ │ Client    │   3   │  24.8s   │  156  │   8.3s       │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Speaking Time Distribution:                              │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [Therapist] ████████████░░░░░░░░░░░░░░░░░░ 42.3%    │ │
│ │ [Client]    ████████████████████░░░░░░░░░ 57.7%    │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Color Scheme

Speakers are color-coded consistently across all views:

| Speaker Badge | Waveform Region | Chart Bar |
|--------------|----------------|-----------|
| 🔵 Therapist (Blue) | Blue overlay | Blue bar |
| 🟢 Client (Green) | Green overlay | Green bar |
| 🟠 Speaker 2 (Amber) | Amber overlay | Amber bar |
| 🔴 Speaker 3 (Red) | Red overlay | Red bar |

## Interactive Features

### Click Transcript Segment
- Highlights segment
- Seeks to that timestamp in waveform
- Auto-scrolls to keep visible

### Click Waveform Region
- Plays that segment
- Highlights corresponding transcript

### Zoom Controls
- Zoom in: Shows more waveform detail
- Zoom out: Shows full overview

### Export Functions
- **Export Transcript**: Downloads clean text version
- **Export JSON**: Downloads full data for further processing

## Sample Data Structure

```json
{
  "aligned_transcript": [
    {
      "speaker": "SPEAKER_00",
      "text": "Hello, how are you feeling today?",
      "start": 0.5,
      "end": 3.2
    },
    {
      "speaker": "SPEAKER_01",
      "text": "I've been feeling a bit anxious lately.",
      "start": 3.8,
      "end": 8.5
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

## Real Pipeline Integration

To connect with your actual pipeline:

```javascript
// In app.js or your main JavaScript file

async function processPipelineOutput(audioFile) {
    try {
        // 1. Upload audio
        const formData = new FormData();
        formData.append('audio', audioFile);

        // 2. Call pipeline API
        const response = await fetch('http://localhost:8000/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // 3. Display results
        await displayPipelineResults(data, audioFile);

        console.log('Results displayed successfully');

    } catch (error) {
        console.error('Pipeline error:', error);
        showError('Failed to process audio: ' + error.message);
    }
}

// Hook into upload button
document.getElementById('uploadBtn').addEventListener('click', () => {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file) {
        processPipelineOutput(file);
    }
});
```

## Testing Checklist

- [x] Waveform loads and renders
- [x] Speaker regions display with correct colors
- [x] Clicking regions plays audio
- [x] Transcript displays with speaker labels
- [x] Clicking transcript seeks waveform
- [x] Speaker statistics calculate correctly
- [x] Processing metrics display
- [x] Export transcript downloads .txt file
- [x] Export JSON downloads .json file
- [x] Play/pause controls work
- [x] Zoom controls work
- [x] Responsive layout on mobile
- [x] Print-friendly styles apply

## Troubleshooting

### Issue: Waveform not loading
**Solution**: Check browser console. Ensure WaveSurfer.js CDN is accessible.

### Issue: Regions not showing
**Solution**: Verify `aligned_transcript` has valid `start`/`end` times in seconds.

### Issue: Colors wrong
**Solution**: Check speaker IDs match format (`SPEAKER_00`, `SPEAKER_01`, etc.)

### Issue: Audio not playing
**Solution**: Verify audio file format is browser-compatible (MP3, WAV recommended).

## Next Steps

1. **Backend Integration**: Connect to pipeline API endpoint
2. **Real-time Updates**: Add WebSocket support for live processing status
3. **Advanced Features**: Add search, filtering, speaker renaming
4. **Accessibility**: Add ARIA labels and keyboard navigation
5. **Testing**: Add unit tests for component logic

---

For complete documentation, see `RESULTS_COMPONENT.md`
