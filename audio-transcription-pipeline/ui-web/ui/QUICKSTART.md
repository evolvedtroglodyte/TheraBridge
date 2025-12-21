# Results Display Component - Quick Start

## 🚀 Get Started in 3 Steps

### 1. Open the UI

```bash
# Option A: Direct file open
open index.html

# Option B: Local server (recommended)
python -m http.server 8080
# Then visit: http://localhost:8080
```

### 2. Test with Demo Data

Open browser console (F12) and run:

```javascript
// Load demo data
const demoData = loadDemoResults();

// You'll need an audio file - use the file input or provide a URL
const audioFile = document.getElementById('fileInput').files[0];

// Display results
displayPipelineResults(demoData, audioFile);
```

### 3. Integrate with Your Pipeline

```javascript
// Your API call
const response = await fetch('/api/process', {
    method: 'POST',
    body: formData  // FormData with audio file
});

const results = await response.json();

// Display results
displayPipelineResults(results, audioFile);
```

---

## 📊 Expected Data Format

```json
{
  "aligned_transcript": [
    {
      "speaker": "SPEAKER_00",
      "text": "Hello, how are you?",
      "start": 0.5,
      "end": 3.2
    }
  ],
  "performance": {
    "total_time": 45.2,
    "audio_duration": 43.0,
    "transcription_time": 12.3,
    "diarization_time": 18.5,
    "num_segments": 7,
    "num_speakers": 2
  }
}
```

**Important**:
- Times in **seconds** (not milliseconds)
- Speaker IDs: `SPEAKER_00`, `SPEAKER_01`, etc.

---

## 🎨 What You Get

### Waveform Visualization
- Interactive audio waveform with speaker regions
- Color-coded by speaker (Blue = Therapist, Green = Client)
- Click regions to play that segment
- Zoom controls for detailed view

### Speaker-Labeled Transcript
- Professional card layout
- Color-coded speaker badges
- Timestamps (MM:SS)
- Click to seek audio

### Speaker Statistics
- Speaking time per speaker
- Turn count and word count
- Visual distribution chart

### Processing Metrics
- Pipeline performance data
- Real-time factor
- Stage-by-stage timing

### Export Functions
- Download transcript as .txt
- Download full data as .json

---

## 📱 Responsive Design

- **Desktop**: 2-column layout (transcript + stats)
- **Tablet**: Stacked single column
- **Mobile**: Compact, touch-friendly

---

## 🎯 Key Features

✅ WaveSurfer.js waveform visualization
✅ Speaker color coding (8 distinct colors)
✅ Click-to-seek interaction
✅ Zoom controls (0-500x)
✅ Export to text/JSON
✅ Print-friendly styles
✅ Fully responsive
✅ Vanilla JavaScript (no framework)

---

## 🔧 API Reference

### Display Results
```javascript
await displayPipelineResults(resultsData, audioFile);
```

### Reset to Upload
```javascript
resetToUpload();
```

### Export Functions
```javascript
resultsDisplay.exportTranscript();  // Download .txt
resultsDisplay.exportJSON();        // Download .json
```

### Waveform Controls
```javascript
waveformVisualizer.playPause();
waveformVisualizer.stop();
waveformVisualizer.zoom(100);  // 0-500
```

---

## 📚 Documentation

- **RESULTS_COMPONENT.md** - Complete API reference
- **EXAMPLE_USAGE.md** - Detailed examples and integration
- **VISUAL_DESIGN.md** - Design specifications
- **WAVE1_FRONTEND_DEV2_REPORT.md** - Implementation report

---

## 🐛 Troubleshooting

### Waveform not loading?
- Check WaveSurfer.js CDN is accessible
- Verify audio file format (MP3, WAV, M4A, etc.)
- Check browser console for errors

### Regions not showing?
- Verify speaker IDs: `SPEAKER_00`, `SPEAKER_01`
- Check timestamps are in seconds
- Ensure `aligned_transcript` array exists

### Export not working?
- Check browser allows downloads
- Verify results data is loaded
- Try from console: `resultsDisplay.exportTranscript()`

---

## ✨ Demo Mode

Built-in demo data for testing:

```javascript
const demoData = loadDemoResults();
console.log(demoData);

// Returns sample data with:
// - 7 transcript segments
// - 2 speakers (Therapist/Client)
// - Performance metrics
```

---

## 🎨 Speaker Colors

| Speaker | Color | Label |
|---------|-------|-------|
| SPEAKER_00 | 🔵 Blue | Therapist |
| SPEAKER_01 | 🟢 Green | Client |
| SPEAKER_02 | 🟡 Amber | Speaker 2 |
| SPEAKER_03 | 🔴 Red | Speaker 3 |

---

## 🚀 Next Steps

1. **Test** - Use demo data to verify everything works
2. **Integrate** - Connect to your backend API
3. **Customize** - Adjust speaker labels in `results.js`
4. **Deploy** - Ready for production use

---

**Need help?** Check the full documentation in `RESULTS_COMPONENT.md`

**Built with**: WaveSurfer.js v7, Vanilla JavaScript, CSS Grid
**Browser Support**: Chrome, Firefox, Safari, Edge (latest)
