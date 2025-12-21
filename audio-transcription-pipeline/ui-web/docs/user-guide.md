# User Guide

Complete guide for using the Audio Transcription Web UI.

## Table of Contents

- [Getting Started](#getting-started)
- [Uploading Audio Files](#uploading-audio-files)
- [Understanding Processing Stages](#understanding-processing-stages)
- [Viewing Transcripts](#viewing-transcripts)
- [Using the Audio Player](#using-the-audio-player)
- [Searching and Filtering](#searching-and-filtering)
- [Exporting Results](#exporting-results)
- [Managing Transcriptions](#managing-transcriptions)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing the Application

Open your web browser and navigate to your deployment URL:

- **Local Development**: `http://localhost:5173`
- **Production**: `https://your-app-name.railway.app` (or your custom domain)

### Supported Browsers

The application works best with modern browsers:

| Browser | Minimum Version | Notes |
|---------|----------------|-------|
| **Chrome** | 90+ | Recommended |
| **Firefox** | 88+ | Recommended |
| **Safari** | 14+ | Good support |
| **Edge** | 90+ | Good support |
| **Mobile Safari** | 14+ | Mobile support |
| **Mobile Chrome** | 90+ | Mobile support |

> **Note**: Audio waveform visualization requires WebAudio API support (available in all modern browsers).

### First Time Setup

No account creation or login required! Simply:

1. Navigate to the application URL
2. Upload your first audio file
3. Wait for processing to complete
4. View your transcript

## Uploading Audio Files

### Supported File Formats

The application accepts the following audio formats:

| Format | Extension | Quality | Notes |
|--------|-----------|---------|-------|
| **MP3** | `.mp3` | Good | Most common format |
| **WAV** | `.wav` | Excellent | Uncompressed, larger files |
| **M4A** | `.m4a` | Good | Apple/iTunes format |
| **OGG** | `.ogg` | Good | Open-source format |
| **FLAC** | `.flac` | Excellent | Lossless compression |
| **AAC** | `.aac` | Good | Advanced audio codec |

### File Size Limits

- **Maximum file size**: 100MB (default)
- **Recommended**: Keep files under 50MB for faster processing
- **Very large files**: Consider splitting into smaller segments

> **Tip**: A 100MB audio file is approximately:
> - **MP3** (128 kbps): ~100 minutes
> - **WAV** (16-bit, 44.1kHz): ~10 minutes
> - **FLAC**: ~30-60 minutes (depending on compression)

### Upload Methods

#### Method 1: Drag and Drop (Recommended)

1. Click or drag your audio file into the upload area
2. The file name and size will be displayed
3. Click **"Upload & Transcribe"**

![Upload Area Placeholder]

**Visual Feedback**:
- Drag zone highlights when file is dragged over
- File info displays immediately after selection
- Progress bar appears during upload

#### Method 2: File Browser

1. Click **"Choose File"** in the upload area
2. Browse your computer for the audio file
3. Select the file and click "Open"
4. Click **"Upload & Transcribe"**

### What Happens After Upload

Once you upload a file:

1. **Upload Progress**: Shows percentage uploaded (usually <5 seconds)
2. **Processing Starts**: File is queued for transcription
3. **Real-Time Updates**: Progress bar shows current processing stage
4. **Completion**: Transcript appears automatically when done

**Processing Time**:
- **1 minute audio**: ~30-60 seconds
- **10 minute audio**: ~5-10 minutes
- **30 minute audio**: ~15-30 minutes

> **Note**: Processing time depends on server load, audio quality, and number of speakers.

## Understanding Processing Stages

Your audio file goes through four stages during processing:

### 1. Preprocessing (0-10%)

**What's happening**:
- Audio format conversion to WAV
- Audio normalization (volume adjustment)
- Resampling to optimal format

**Duration**: 5-10 seconds

**Progress Indicator**: Blue progress bar at 0-10%

### 2. Transcription (10-50%)

**What's happening**:
- Audio uploaded to OpenAI Whisper API
- Speech-to-text conversion
- Timestamp generation
- Language detection

**Duration**: 50-70% of total processing time

**Progress Indicator**: Blue progress bar at 10-50%

> **Note**: This stage requires internet connection to OpenAI servers.

### 3. Speaker Diarization (50-90%)

**What's happening**:
- Identifying different speakers
- Assigning speaker labels (SPEAKER_00, SPEAKER_01, etc.)
- Detecting speaker change points
- Analyzing voice characteristics

**Duration**: 30-40% of total processing time

**Progress Indicator**: Blue progress bar at 50-90%

> **Accuracy**: The system can distinguish between 2-10 speakers with high accuracy.

### 4. Post-Processing (90-100%)

**What's happening**:
- Merging transcription with speaker labels
- Calculating speaker statistics
- Generating final output
- Saving results

**Duration**: 5-10 seconds

**Progress Indicator**: Blue progress bar at 90-100%

### Processing Complete

When processing is complete:
- ✅ Success notification appears
- ✅ Transcript viewer automatically opens
- ✅ Audio player loads with waveform
- ✅ Speaker timeline displays

## Viewing Transcripts

### Transcript Layout

The transcript view is divided into three main sections:

```
┌─────────────────────────────────────────────────────────┐
│  Audio Player + Waveform                                │
│  [====================================]                  │
│  [Play] 1:23 / 5:45                                     │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Speaker Timeline (Visual)                              │
│  [SPEAKER_00][SPEAKER_01][SPEAKER_00][SPEAKER_01]...    │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Transcript Segments                                    │
│                                                         │
│  [0:00] SPEAKER_00: Hello, welcome to...               │
│  [0:15] SPEAKER_01: Thank you for having me...         │
│  [0:32] SPEAKER_00: Let's get started with...          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Transcript Segments

Each segment shows:

- **[Timestamp]**: When the speaker started talking
- **Speaker Label**: SPEAKER_00, SPEAKER_01, etc.
- **Transcribed Text**: What the speaker said

**Example**:
```
[0:00] SPEAKER_00: Hello, welcome to our conversation.
[0:05] SPEAKER_01: Thank you for having me.
[0:10] SPEAKER_00: Let's get started with the first topic.
```

### Speaker Labels

Speakers are automatically labeled:

| Label | Color | Meaning |
|-------|-------|---------|
| **SPEAKER_00** | Blue | First speaker detected |
| **SPEAKER_01** | Green | Second speaker detected |
| **SPEAKER_02** | Purple | Third speaker detected |
| **SPEAKER_03** | Orange | Fourth speaker detected |

> **Note**: Speaker labels are assigned based on voice characteristics, not chronological order. SPEAKER_00 is not necessarily the first person to speak.

### Speaker Statistics

At the top of the transcript, you'll see speaker statistics:

```
SPEAKER_00: 15 segments, 5:23 speaking time (60%)
SPEAKER_01: 12 segments, 3:45 speaking time (40%)
```

**Includes**:
- Number of speaking segments
- Total speaking time
- Percentage of total conversation

## Using the Audio Player

### Waveform Visualization

The audio player displays a visual waveform of your audio:

- **Height**: Represents volume (louder = taller)
- **Color**: Different speakers may have different colors (optional)
- **Cursor**: Shows current playback position

### Player Controls

| Control | Action | Keyboard Shortcut |
|---------|--------|-------------------|
| **Play/Pause** | Start/stop playback | Space |
| **Seek** | Click anywhere on waveform | - |
| **Volume** | Adjust playback volume | Up/Down arrows |
| **Speed** | Change playback speed (0.5x - 2x) | - |

### Playback Features

#### 1. Click to Jump

Click anywhere on the waveform to jump to that position:
- Click at 1:30 → Audio jumps to 1:30
- Useful for reviewing specific sections

#### 2. Playback Speed

Adjust playback speed from the speed selector:
- **0.5x**: Slow (easier to understand)
- **1.0x**: Normal (default)
- **1.5x**: Fast (save time)
- **2.0x**: Very fast (skim through)

#### 3. Synchronized Transcript

As audio plays:
- Current segment highlights in the transcript
- Transcript auto-scrolls to keep current segment visible
- Waveform cursor moves in real-time

#### 4. Click Segment to Jump

Click any transcript segment to jump to that point in the audio:
1. Click on **[2:30] SPEAKER_01: ...**
2. Audio jumps to 2:30
3. Playback starts from that point

## Searching and Filtering

### Search by Text

Use the search box to find specific words or phrases:

1. Type your search term (e.g., "project deadline")
2. Matching segments highlight in yellow
3. Use **Next/Previous** buttons to navigate results
4. Search is case-insensitive

**Example Search Queries**:
- `budget` - Find all mentions of "budget"
- `Q1 revenue` - Find discussions about Q1 revenue
- `action items` - Locate action items

### Filter by Speaker

Filter the transcript to show only specific speakers:

1. Click the speaker filter dropdown
2. Select one or more speakers
3. Transcript shows only selected speakers
4. Audio player remains unchanged (all speakers audible)

**Use Cases**:
- Review only what SPEAKER_00 said
- Compare what two specific speakers discussed
- Export transcript for specific speaker

### Combined Search + Filter

Combine search and filter for powerful queries:

**Example**:
- **Filter**: SPEAKER_01
- **Search**: "deadline"
- **Result**: Only segments where SPEAKER_01 mentioned "deadline"

### Clear Filters

Click **"Clear Filters"** to remove all search and speaker filters.

## Exporting Results

### Export Formats

Export your transcript in multiple formats:

#### 1. JSON (Detailed)

**Use case**: Technical integration, data analysis

**Includes**:
- Full transcription with timestamps
- Speaker information and statistics
- Processing metadata
- Quality metrics

**Example**:
```json
{
  "id": "550e8400-...",
  "filename": "meeting.mp3",
  "speakers": [...],
  "segments": [
    {
      "start": 0.0,
      "end": 5.5,
      "text": "Hello, welcome...",
      "speaker_id": "0"
    }
  ],
  "metadata": {...}
}
```

**Download**: Click **"Export → JSON"**

#### 2. TXT (Plain Text)

**Use case**: Reading, sharing, editing

**Format**:
```
Transcription: meeting.mp3
Date: 2025-12-21

SPEAKER_00 [0:00]: Hello, welcome to our conversation.
SPEAKER_01 [0:15]: Thank you for having me.
SPEAKER_00 [0:32]: Let's get started with the first topic.
```

**Download**: Click **"Export → TXT"**

#### 3. SRT (Subtitles)

**Use case**: Video subtitles, media players

**Format**:
```
1
00:00:00,000 --> 00:00:05,500
SPEAKER_00: Hello, welcome to our conversation.

2
00:00:06,000 --> 00:00:10,200
SPEAKER_01: Thank you for having me.
```

**Compatible with**:
- Video editing software (Premiere, Final Cut)
- Media players (VLC, QuickTime)
- YouTube, Vimeo subtitle uploads

**Download**: Click **"Export → SRT"**

### Export Options

#### Export Full Transcript

Default: Exports entire transcript with all speakers.

#### Export Filtered Transcript

If you have filters applied:
1. Apply speaker filter or search
2. Click **"Export"**
3. Only visible segments are exported

**Example**:
- Filter: SPEAKER_01
- Export TXT → Only SPEAKER_01's words exported

### Downloading Exports

1. Click your desired format (JSON/TXT/SRT)
2. Browser downloads file automatically
3. Filename: `{original-filename}-transcript.{format}`

**Example**: `meeting.mp3` → `meeting-transcript.txt`

## Managing Transcriptions

### View All Transcriptions

Click **"My Transcriptions"** (or similar) to see all your past transcriptions:

- **List View**: Shows filename, date, duration
- **Quick Actions**: View, download, delete
- **Sort**: By date (newest first)

### Delete Transcriptions

To free up storage or remove unwanted transcriptions:

1. Go to transcription detail view
2. Click **"Delete"** button (trash icon)
3. Confirm deletion
4. Transcription and files are permanently removed

> **Warning**: Deletion is permanent. Download transcripts before deleting.

### Re-Open Previous Transcriptions

To view a previous transcription:

1. Click **"My Transcriptions"**
2. Click on the transcription you want to view
3. Transcript viewer opens with full audio and text

**Persistence**:
- Transcriptions stored on server (for now)
- Available until manually deleted
- No expiration (currently)

> **Note**: Future versions may auto-delete after 30 days. Download important transcripts.

## Best Practices

### Audio Quality Tips

For best transcription accuracy:

✅ **Do**:
- Use a good microphone (USB mic or headset)
- Record in a quiet environment
- Keep volume consistent (not too loud/quiet)
- Use lossless formats (WAV, FLAC) when possible
- Record each speaker on separate channels (if possible)

❌ **Don't**:
- Record with heavy background noise (music, traffic)
- Let speakers talk over each other
- Use very low bitrate MP3s (<64 kbps)
- Record too far from microphone

### Improving Speaker Diarization

For better speaker separation:

✅ **Do**:
- Ensure speakers have distinct voices
- Avoid overlapping speech
- Use clear audio (no distortion)
- Keep consistent microphone distance

❌ **Don't**:
- Have multiple people with similar voices
- Allow long periods of overlapping speech
- Use speakerphone with echo

### File Management

To stay organized:

✅ **Do**:
- Use descriptive filenames (e.g., `team-meeting-2025-12-21.mp3`)
- Export transcripts immediately after processing
- Delete old transcriptions you no longer need
- Keep original audio files as backup

❌ **Don't**:
- Use generic names (e.g., `recording001.mp3`)
- Rely only on server storage (export important ones)
- Upload extremely large files (split them first)

### Processing Large Files

For files longer than 1 hour:

**Option 1: Split the File**
```bash
# Using FFmpeg to split audio
ffmpeg -i long-meeting.mp3 -ss 00:00:00 -t 01:00:00 part1.mp3
ffmpeg -i long-meeting.mp3 -ss 01:00:00 -t 01:00:00 part2.mp3
```

**Option 2: Upload Overnight**
- Start processing before leaving for the day
- Results ready next morning

**Option 3: Use GPU Pipeline**
- Contact your admin to enable GPU processing (5-10x faster)

### Transcript Review

After receiving your transcript:

1. **Listen while reading**: Catch any errors
2. **Check speaker labels**: Verify they're consistent
3. **Note timestamps**: Mark important sections
4. **Export immediately**: Don't rely on server storage

## Troubleshooting

### Upload Issues

#### "File type not supported"

**Cause**: Unsupported file format

**Solution**: Convert to MP3, WAV, M4A, OGG, FLAC, or AAC
```bash
# Convert using FFmpeg
ffmpeg -i input.webm -acodec libmp3lame output.mp3
```

#### "File too large"

**Cause**: File exceeds 100MB limit

**Solution**:
1. Compress the audio (reduce bitrate)
2. Split into smaller files
3. Contact admin to increase limit

```bash
# Compress using FFmpeg
ffmpeg -i input.wav -b:a 128k output.mp3
```

#### Upload stalls at 99%

**Cause**: Network timeout or server issue

**Solution**:
1. Wait 30 seconds
2. Refresh page and try again
3. Check internet connection
4. Try smaller file first

### Processing Issues

#### Processing takes forever

**Expected Duration**:
- 1 min audio = 30-60 sec processing
- 10 min audio = 5-10 min processing
- 60 min audio = 30-60 min processing

**If slower than expected**:
1. Check server load (other jobs in queue)
2. Check internet speed (slow upload to Whisper API)
3. Wait patiently - diarization is CPU-intensive

#### Processing failed

**Common Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "OpenAI API error" | API issue or quota | Check OpenAI status, verify API key |
| "Timeout" | File too large or slow processing | Retry with smaller file |
| "Invalid audio" | Corrupted file | Re-export audio from source |

**General Solution**: Retry upload. If persists, contact support.

#### No speakers detected

**Cause**:
- Single speaker (or silence)
- Very poor audio quality

**Solution**:
- Verify audio has speech
- Check volume levels (increase if too quiet)
- Try different audio file

#### Wrong number of speakers

**Scenario**: Transcript shows 3 speakers, but only 2 people spoke

**Cause**: Background noise, music, or similar voices

**Solution**:
- Re-record with cleaner audio
- Accept slight inaccuracy (manually correct if needed)

### Playback Issues

#### Audio won't play

**Cause**: Browser compatibility or codec issue

**Solution**:
1. Try different browser (Chrome recommended)
2. Update browser to latest version
3. Check browser console for errors (F12)

#### Waveform not visible

**Cause**: Browser doesn't support WebAudio API

**Solution**:
1. Update browser
2. Try Chrome or Firefox
3. Waveform is optional - transcript still works

#### Audio and transcript out of sync

**Cause**: Timing calculation error

**Solution**:
1. Refresh page
2. Re-seek to current position
3. If persists, report bug

### Export Issues

#### Export downloads empty file

**Cause**: Processing not complete or browser issue

**Solution**:
1. Wait for processing to complete (100%)
2. Try different browser
3. Disable browser extensions (ad blockers)

#### SRT format doesn't work in video editor

**Cause**: Character encoding or format issue

**Solution**:
1. Open SRT file in text editor
2. Save as UTF-8 encoding
3. Verify timestamps are correct format

### Display Issues

#### Transcript not showing

**Cause**: JavaScript error or loading issue

**Solution**:
1. Refresh page (Ctrl+R / Cmd+R)
2. Clear browser cache
3. Check browser console (F12) for errors

#### Segments cut off or overlapping

**Cause**: Layout issue or zoom level

**Solution**:
1. Reset browser zoom (Ctrl+0 / Cmd+0)
2. Try different screen size
3. Refresh page

### Need More Help?

If your issue isn't covered here:

1. **Check backend logs**: Admin can view server logs for errors
2. **Try sample file**: Verify system works with a known-good file
3. **Contact support**: Provide:
   - Error message (exact text)
   - File name and size
   - Browser and version
   - Steps to reproduce

## Tips & Tricks

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Space** | Play/Pause audio |
| **Ctrl+F** / **Cmd+F** | Focus search box |
| **Escape** | Clear search/filters |
| **Arrow Keys** | Adjust volume (when player focused) |

### Advanced Search

Use quotes for exact phrases:
- `"project deadline"` - Only matches exact phrase
- `deadline` - Matches any segment containing "deadline"

### Quick Navigation

Click timestamp in segment to jump to that point:
- **[2:30]** SPEAKER_01: ... ← Click [2:30] to jump

### Batch Export

To export multiple transcriptions:
1. Open each transcript
2. Export to desired format
3. Files download to your Downloads folder

### Mobile Usage

The app works on mobile, with limitations:
- ✅ Upload files
- ✅ View progress
- ✅ Read transcripts
- ⚠️ Audio player may have limited features
- ⚠️ Waveform may not render (depends on device)

**Recommendation**: Use desktop for best experience.

## Conclusion

You now know how to:
- ✅ Upload audio files for transcription
- ✅ Monitor processing progress
- ✅ View and navigate transcripts
- ✅ Use the audio player with synchronized transcript
- ✅ Search and filter segments
- ✅ Export in multiple formats
- ✅ Troubleshoot common issues

**Next Steps**:
- Try uploading your first audio file
- Explore the export formats
- Experiment with search and filters
- Share transcripts with your team

---

**Need technical help?** See the [API Reference](api-reference.md) for integration options.

**Want to deploy your own?** See the [Deployment Guide](deployment-guide.md).
