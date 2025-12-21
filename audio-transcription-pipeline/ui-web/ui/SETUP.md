# Setup & Testing Guide - Audio Transcription UI

## Quick Start

### 1. Run the UI (Local Development)

The UI is a static website that can be served locally:

```bash
# Navigate to UI directory
cd audio-transcription-pipeline/ui

# Option A: Python HTTP server (recommended)
python -m http.server 8080

# Option B: Python 2
python -m SimpleHTTPServer 8080

# Option C: Node.js (if you have it)
npx http-server -p 8080

# Option D: Direct file open (limited functionality)
open index.html
```

Then visit: **http://localhost:8080**

---

### 2. Run the Python Bridge Server

**IMPORTANT:** The server must be running for the UI to work.

```bash
# Navigate to pipeline directory
cd audio-transcription-pipeline

# Activate virtual environment
source venv/bin/activate

# Run the server (when Backend Dev #1 creates it)
python server.py
```

Server will start on: **http://localhost:5000**

---

### 3. Test the UI

1. **Upload a file**
   - Drag & drop an audio file (MP3, WAV, M4A, etc.)
   - Or click to browse

2. **Process the file**
   - Click "Process Audio"
   - Watch the progress bar and step indicators
   - Wait for processing to complete

3. **View results**
   - See waveform visualization
   - See speaker-labeled transcript
   - See performance metrics

4. **Export results**
   - Click "Export Transcript" for .txt file
   - Click "Export JSON" for raw data

---

## File Requirements

### Supported Audio Formats

- MP3 (`.mp3`)
- WAV (`.wav`)
- M4A (`.m4a`)
- AAC (`.aac`)
- OGG (`.ogg`)
- FLAC (`.flac`)
- WMA (`.wma`)
- AIFF (`.aiff`)

### File Size Limit

- Maximum: **200 MB**
- Recommended: Under 50 MB for best performance

### Audio Duration

- Minimum: 10 seconds
- Maximum: No hard limit (but longer files take more time)
- Recommended: 5-30 minutes

---

## Testing Scenarios

### Scenario 1: Happy Path

**Steps:**
1. Start Python server
2. Open UI in browser
3. Upload a 1-minute MP3 file
4. Click "Process Audio"
5. Wait for completion (~30-60 seconds)
6. View results

**Expected:**
- Progress bar updates smoothly
- Step indicators show current stage
- Results display with waveform and transcript
- No errors

---

### Scenario 2: Server Not Running

**Steps:**
1. Stop Python server
2. Open UI in browser
3. Try to upload a file

**Expected:**
- Error banner appears
- Message: "Cannot connect to server. Please ensure the server is running on http://localhost:5000"
- UI remains on upload screen

---

### Scenario 3: Invalid File Type

**Steps:**
1. Start Python server
2. Open UI in browser
3. Try to upload a .pdf or .txt file

**Expected:**
- Error banner appears immediately
- Message: "Invalid file type. Supported formats: .mp3, .wav, ..."
- Upload button remains disabled

---

### Scenario 4: File Too Large

**Steps:**
1. Start Python server
2. Open UI in browser
3. Try to upload a 250 MB audio file

**Expected:**
- Error banner appears immediately
- Message: "File too large. Maximum size: 200 MB"
- Upload button remains disabled

---

### Scenario 5: Cancel Processing

**Steps:**
1. Start Python server
2. Upload a file
3. Click "Process Audio"
4. Click "Cancel Processing" after 5 seconds

**Expected:**
- Processing stops
- Returns to upload screen
- Message: "Processing cancelled by user"

---

### Scenario 6: Network Interruption

**Steps:**
1. Start Python server
2. Upload a file
3. Click "Process Audio"
4. Stop server mid-processing

**Expected:**
- Error banner appears after next poll
- Message: "Lost connection to server. Please check if the server is still running."
- Returns to upload screen after 3 seconds

---

## Browser Testing

### Recommended Browsers

✅ **Chrome 90+** - Full support
✅ **Firefox 88+** - Full support
✅ **Safari 14+** - Full support
✅ **Edge 90+** - Full support

### Mobile Browsers

✅ **iOS Safari 14+** - Touch-optimized
✅ **Chrome Android 90+** - Touch-optimized

### Testing Checklist

- [ ] File upload works (drag & drop)
- [ ] File upload works (browse button)
- [ ] Progress updates in real-time
- [ ] Results display correctly
- [ ] Waveform plays audio
- [ ] Transcript is clickable
- [ ] Export buttons work
- [ ] Cancel button works
- [ ] Error messages appear
- [ ] Theme toggle works (dark/light)
- [ ] Responsive on mobile (< 768px)
- [ ] Keyboard shortcuts work

---

## Debugging

### Open Browser Console

- **Chrome/Edge:** Press `F12` or `Ctrl+Shift+J` (Mac: `Cmd+Option+J`)
- **Firefox:** Press `F12` or `Ctrl+Shift+K` (Mac: `Cmd+Option+K`)
- **Safari:** Enable Developer menu first, then `Cmd+Option+C`

### Check Console Logs

Look for:
```
Audio Diarization Pipeline UI initialized
Supported formats: .mp3, .wav, .m4a, ...
Max file size: 200 MB

// On upload:
Upload successful. Job ID: abc-123

// On completion:
Results fetched successfully: {...}
Results displayed successfully
```

### Check Network Tab

1. Open DevTools
2. Go to Network tab
3. Upload a file
4. Watch requests:
   - `POST /api/upload` - Should return 200
   - `GET /api/status/{job_id}` - Should poll every 1s
   - `GET /api/results/{job_id}` - Should return 200 when complete

### Common Issues

**Issue:** "Cannot connect to server"
- **Fix:** Start the Python server: `python server.py`

**Issue:** Waveform not showing
- **Fix:** Check WaveSurfer.js CDN is accessible
- **Fix:** Try a different audio file format

**Issue:** Progress stuck at 0%
- **Fix:** Check server logs for errors
- **Fix:** Verify server is processing the file

**Issue:** Results not displaying
- **Fix:** Check browser console for JavaScript errors
- **Fix:** Verify response format matches specification

---

## Configuration

### Change Server URL

Edit `app.js` line 182:

```javascript
const API_CONFIG = {
    baseUrl: 'http://your-server:5000',  // Change this
    // ...
};
```

### Change Max File Size

Edit `app.js` line 74:

```javascript
const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB (change this)
```

### Change Polling Interval

Edit `app.js` line 189:

```javascript
const API_CONFIG = {
    // ...
    pollInterval: 2000  // 2 seconds instead of 1
};
```

---

## Project Structure

```
ui/
├── index.html              # Main HTML page
├── app.js                  # Main application logic + API integration
├── styles.css              # Global styles
├── results-styles.css      # Results section styles
│
├── js/
│   ├── results-integration.js  # Results display integration
│   ├── results.js              # Results display component
│   ├── waveform.js             # Waveform visualization
│   ├── player.js               # Audio player controls
│   ├── player-integration.js   # Player synchronization
│   └── timeline.js             # Timeline visualization
│
├── API_INTEGRATION.md      # API specification (this wave)
├── SETUP.md                # This file
├── QUICKSTART.md           # Quick reference
├── EXAMPLE_USAGE.md        # Detailed usage examples
└── *.md                    # Other documentation
```

---

## Example: Running Locally

### Terminal 1: Python Server

```bash
cd ~/path/to/audio-transcription-pipeline
source venv/bin/activate
python server.py

# Output:
# * Running on http://0.0.0.0:5000
# * Debug mode: on
```

### Terminal 2: UI Server

```bash
cd ~/path/to/audio-transcription-pipeline/ui
python -m http.server 8080

# Output:
# Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

### Browser

Visit: **http://localhost:8080**

---

## Production Deployment

### Static Hosting

The UI can be deployed to any static hosting service:

- **Netlify:** Drag & drop the `ui/` folder
- **Vercel:** Deploy from Git repository
- **GitHub Pages:** Push to gh-pages branch
- **AWS S3 + CloudFront:** Upload to S3 bucket
- **Firebase Hosting:** `firebase deploy`

### Server Configuration

Update `API_CONFIG.baseUrl` in `app.js` to point to production server:

```javascript
const API_CONFIG = {
    baseUrl: 'https://api.yourcompany.com',  // Production server
    // ...
};
```

### CORS Configuration

Ensure production server has CORS enabled:

```python
# Flask
from flask_cors import CORS
CORS(app, origins=['https://yourdomain.com'])

# Or manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://yourdomain.com')
    return response
```

---

## Getting Help

### Documentation

- **API_INTEGRATION.md** - Complete API specification
- **RESULTS_COMPONENT.md** - Results display API
- **INTEGRATION_GUIDE.md** - Component integration
- **QUICKSTART.md** - Quick reference

### Contact

- **Frontend Dev #1:** Upload UI (Wave 1)
- **Frontend Dev #2:** Waveform & Transcript (Wave 1)
- **Frontend Dev #3:** Player & Timeline (Wave 1)
- **Backend Dev #2:** API Integration (Wave 2) - *This work*

---

## Next Steps

1. ✅ **UI is ready** - All frontend work complete
2. ⏳ **Waiting for server** - Backend Dev #1 needs to create `server.py`
3. ⏳ **End-to-end testing** - Test full pipeline with real audio
4. ⏳ **Production deployment** - Deploy UI and server

---

**Status:** ✅ **UI READY FOR TESTING**
**Waiting on:** Backend Dev #1 to create `server.py`
**Last Updated:** December 20, 2025
