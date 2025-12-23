# Audio Transcription Pipeline - Web UI

> **📌 Repository Rules:** This subproject follows the global repository rules defined in [`/.claude/CLAUDE.md`](../../.claude/CLAUDE.md). Please review the root CLAUDE.md for critical workflows including git-first policies, change logging requirements, and repository organization standards.

## Project Overview

Web interface for the audio transcription pipeline. Displays speaker-diarized transcripts with synchronized audio playback, granular highlighting, and interactive timeline navigation.

**Tech Stack:**
- Frontend: Vite + React 19 + TypeScript
- Audio: WaveSurfer.js
- Backend: FastAPI (Python)
- Styling: Tailwind CSS

## Quick Start

### Frontend Development
```bash
cd frontend
npm install
npm run dev      # Development server (http://localhost:5173)
npm run build    # Production build
```

### Backend Server
```bash
cd backend
source venv/bin/activate  # or activate venv on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload  # Server at http://localhost:8000
```

## Architecture

### Key Components

**ResultsView.tsx** - Main orchestrator component
- Detects and corrects timestamp offsets between audio and transcript
- Manages playback state and segment synchronization
- Passes corrected data to child components

**AudioPlayer.tsx** - Integrated audio player with timeline
- WaveSurfer.js waveform visualization
- Speaker timeline bars behind waveform
- Hover tooltips showing segment details
- Speaker legend with statistics
- Playback controls and segment navigation

**TranscriptViewer.tsx** - Scrollable transcript display
- Auto-scroll following audio playback (with manual override)
- Granular phrase-level highlighting
- Speaker labels and timestamps
- Click to seek audio

### Critical Pattern: Timestamp Offset Correction

**Problem:** Backend may return segment timestamps that don't start at 0, causing misalignment with audio file.

**Solution:** ResultsView automatically detects and corrects offsets:

```typescript
// Detect offset when result loads
useEffect(() => {
  if (result?.segments?.[0]?.start > 10) {
    const offset = result.segments[0].start;
    console.warn(`Detected timestamp offset: ${offset.toFixed(2)}s`);
    setTimestampOffset(offset);
  }
}, [result]);

// Apply correction to all segments
const correctedSegments = result?.segments.map(seg => ({
  ...seg,
  start: Math.max(0, seg.start - timestampOffset),
  end: Math.max(0, seg.end - timestampOffset),
})) || [];
```

**Why this matters:** Without correction, audio at 12:44 could show transcript at 15:22 (~2.5 min ahead).

### Segment Types

**Combined Segments** (`segments`):
- Full speaker turns (e.g., 10-30 seconds)
- Used for timeline bars, speaker statistics
- Displayed in transcript as collapsible sections

**Aligned Segments** (`aligned_segments`):
- Granular phrase-level timestamps (e.g., 1-3 seconds)
- Used for precise highlighting during playback
- Nested within combined segments

## File Structure

```
ui-web/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── results/
│   │   │   │   ├── ResultsView.tsx        # Main orchestrator
│   │   │   │   ├── AudioPlayer.tsx        # Audio + timeline
│   │   │   │   └── TranscriptViewer.tsx   # Transcript display
│   │   │   └── ui/                        # shadcn/ui components
│   │   ├── App.tsx                        # Routes
│   │   └── main.tsx                       # Entry point
│   ├── package.json
│   └── vite.config.ts
│
└── backend/
    ├── app/
    │   ├── main.py                        # FastAPI app
    │   ├── routers/                       # API endpoints
    │   └── models/                        # Data models
    ├── requirements.txt
    └── venv/
```

## Key Features (v1.1.0)

### Implemented
- ✅ Automatic timestamp offset detection and correction
- ✅ Integrated audio player with speaker timeline (merged component)
- ✅ Auto-scroll following playback (with manual override)
- ✅ Granular phrase-level highlighting
- ✅ Hover tooltip on timeline segments
- ✅ Speaker legend with statistics
- ✅ Double-click word navigation
- ✅ Toggle controls for auto-scroll and granular highlighting
- ✅ Segment navigation buttons (prev/next)

### Known Issues
- Page refresh returns to uploader (needs session persistence)
- Hover opacity on playing segments may need testing

## Development Notes

### WaveSurfer.js Integration
- Initialized in AudioPlayer with `useRef` hook
- Timeline height: 120px for better visibility
- Speaker bars positioned behind waveform using absolute positioning
- Hover interactions managed with `onMouseEnter`/`onMouseLeave`

### Auto-scroll Pattern
```typescript
// Only scroll on segment changes, not every time update
const lastAutoScrollSegment = useRef<number | null>(null);

useEffect(() => {
  if (!autoScrollEnabled) return;

  if (lastAutoScrollSegment.current !== currentSegmentIndex) {
    lastAutoScrollSegment.current = currentSegmentIndex;
    // Scroll to segment
  }
}, [currentSegmentIndex, autoScrollEnabled]);
```

This prevents auto-scroll from overriding manual scrolling.

### Backend Dependencies
- Python 3.13 compatible
- `pyaudioop-lts` removed (incompatible with 3.13)
- FastAPI, pydantic-settings, uvicorn required

## Testing

### Manual Test Checklist
1. Load audio file - verify timestamp alignment (audio time should match transcript time)
2. Play audio - verify granular highlighting follows playback
3. Enable auto-scroll - verify transcript scrolls to current segment
4. Disable auto-scroll - verify manual scrolling works
5. Hover timeline bars - verify tooltip shows segment details
6. Click timeline bars - verify audio seeks to segment
7. Double-click transcript word - verify audio jumps to that word
8. Use prev/next buttons - verify segment navigation works
9. Verify tooltips auto-fade after 3 seconds

## Recent Changes

### 2025-12-22 - Critical Timestamp Offset Fix
**Problem:** Audio at 12:44 showing transcript at 15:22 (~2.5 min ahead)
**Solution:** Implemented automatic offset detection in ResultsView - detects when first segment starts >10s after 0, applies correction to all segments

### 2025-12-22 - Merged Timeline into Audio Player
**Change:** Combined SpeakerTimeline into AudioPlayer component
**Result:** Single unified "Audio Playback & Speaker Timeline" card with:
- 120px tall timeline with speaker bars behind waveform
- Hover tooltip showing speaker, timestamps, text preview
- Speaker legend at bottom with colored dots and statistics

### 2025-12-22 - Multiple UI Fixes
- Fixed auto-scroll preventing manual scroll (only scroll on segment change)
- Fixed granular highlighting logic (proper overlap detection)
- Fixed double-click word navigation (find actual granular segment)
- Fixed tooltip auto-fade (removed onHide from dependencies)
- Fixed TypeScript build errors

## Git Workflow

Recent commits:
```
93ff7f6 Fix critical 2.5 minute timestamp offset issue
9b0faca Fix multiple UI issues from user testing
9f25ac3 Fix TypeScript errors and refine auto-scroll pause detection
```

When making changes:
1. Test locally with `npm run dev`
2. Build to verify: `npm run build`
3. Commit with descriptive message
4. Push to GitHub

## Troubleshooting

### Backend "Address already in use"
```bash
# Check what's using port 8000
lsof -i:8000

# Kill process if needed
lsof -ti:8000 | xargs kill -9
```

### Frontend build errors
```bash
# Clear cache and rebuild
rm -rf node_modules .next
npm install
npm run build
```

### Timestamp misalignment persists
- Check browser console for offset detection warnings
- Verify `correctedSegments` are being passed to AudioPlayer
- Confirm backend data has `segments` and `aligned_segments` arrays
