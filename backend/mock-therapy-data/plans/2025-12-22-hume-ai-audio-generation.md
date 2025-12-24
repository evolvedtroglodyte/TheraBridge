# Hume AI Audio Generation for Mockup Implementation Plan

## Overview

Generate realistic therapy session audio files from 12 JSON transcript files using Hume AI Octave TTS. These audio files are for **mockup/demo purposes only**, not part of the production application. The goal is to create 10.25 hours of high-quality, emotionally intelligent therapy dialogue with distinct therapist (male) and patient (androgynous) voices.

## Current State Analysis

**What exists:**
- ✅ 12 complete therapy session transcripts in JSON format (`mock-therapy-data/sessions/`)
- ✅ 11/12 sessions validated and ready (session_12 needs timestamp fix)
- ✅ Detailed session structure with `aligned_segments` arrays (150-220 segments per session)
- ✅ Speaker labels: SPEAKER_00 (therapist), SPEAKER_01 (patient)
- ✅ Total dialogue: ~537 validated segments across 11 sessions
- ✅ Documentation: INTEGRATION_GUIDE.md with voice specifications

**What's missing:**
- ❌ Hume AI API account and API key
- ❌ Python audio generation script
- ❌ Voice configuration (therapist male, patient androgynous)
- ❌ Audio file output directory structure
- ❌ MP3 files for all 12 sessions

**Critical Issue:**
- ⚠️ Session 12 (`session_12_thriving.json`) has timestamp mismatch: ends at 5300s but metadata says 3000s
- Must be fixed before audio generation to avoid duration errors

**Key Constraints:**
- Hume AI character limit: 5,000 characters per utterance
- Rate limit: 50 requests per minute
- Budget consideration: Free tier provides ~10,000 chars (~10 min audio), need paid plan for full generation
- Total audio to generate: 10.25 hours across 12 sessions

## Desired End State

**Deliverables:**
- 12 MP3 audio files with realistic therapy dialogue
- Distinct, natural-sounding voices for therapist and patient
- Emotional intelligence in delivery (sadness, hope, breakthroughs)
- Audio duration matches transcript metadata exactly
- Files stored in `mock-therapy-data/audio/` directory
- Quality suitable for demo/mockup presentation

**Verification Criteria:**
- All 12 session audio files exist
- File sizes appropriate (~8-15MB per 45-60 min session)
- Audio playback duration matches JSON `metadata.duration` (±5 seconds)
- Therapist voice distinctly different from patient voice
- No audio artifacts, glitches, or robotic delivery
- Emotional moments (breakthroughs, sadness) sound authentic

## What We're NOT Doing

- ❌ Integrating audio into production backend/database
- ❌ Uploading to Supabase Storage
- ❌ Creating audio player component in frontend
- ❌ Implementing real-time transcription
- ❌ Building audio generation into the application workflow
- ❌ Generating ground truth annotations or timestamps

**Clarification:** This is a one-time mockup generation task, not a software feature.

## Implementation Approach

**Strategy:** Segment-by-segment generation with batch processing

1. Fix session 12 timestamp issue (prerequisite)
2. Set up Hume AI account and get API key
3. Create custom voices or select pre-made voices
4. Build Python script to process JSON → Hume AI TTS → MP3
5. Generate audio in batches (3-4 sessions at a time) to manage rate limits
6. Validate audio quality after first session before batch generation
7. Combine segment audio files into full session MP3s

**Technology Stack:**
- Hume AI Octave TTS (v2) for speech synthesis
- Python 3.13 with hume-python-sdk
- ffmpeg for audio concatenation
- python-dotenv for API key management

---

## Phase 1: Prerequisites and Setup

### Overview
Fix critical data issue, set up Hume AI account, install dependencies, and configure voice settings.

### Changes Required:

#### 1.1 Fix Session 12 Timestamp Issue

**File**: `mock-therapy-data/sessions/session_12_thriving.json`

**Problem**: Last segment ends at 5300.0s (88 min) but metadata declares duration as 3000.0s (50 min)

**Solution Option A - Update Metadata (RECOMMENDED)**:
```json
{
  "metadata": {
    "duration": 5300.0  // Change from 3000.0 to match actual content
  }
}
```

**Solution Option B - Regenerate Session**:
- Re-run transcript generation with correct 50-minute constraint
- Ensure breakthrough content and clinical arc preserved

**Choose Option A** if clinical content is satisfactory and 88 minutes is acceptable.
**Choose Option B** if session must be exactly 50 minutes as originally planned.

#### 1.2 Create Hume AI Account and Get API Key

**Steps:**
1. Visit https://platform.hume.ai/
2. Sign up for account
3. Navigate to API Keys section
4. Generate new API key
5. Note: Free tier provides ~10,000 chars (~10 min audio)
6. **Estimate costs:**
   - Total characters: ~537 segments × 200 chars avg = ~107,400 characters
   - Free tier insufficient - need paid plan
   - Estimated cost: ~$3-5 for Starter plan or pay-per-use

**Expected API Key Format**: `hume_api_xxx...`

#### 1.3 Install Python Dependencies

**File**: `mock-therapy-data/requirements.txt` (NEW)

```
hume==0.9.0
python-dotenv==1.0.0
pydub==0.25.1
```

**Installation:**
```bash
cd mock-therapy-data
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**System Dependencies:**
```bash
# Install ffmpeg (required for audio processing)
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt-get install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

#### 1.4 Create Environment Configuration

**File**: `mock-therapy-data/.env` (NEW)

```bash
# Hume AI API Configuration
HUME_API_KEY=your_api_key_here

# Voice Configuration (will be set after voice creation/selection)
THERAPIST_VOICE_ID=ITO  # Pre-made male voice OR custom voice ID
PATIENT_VOICE_ID=custom_voice_id  # Custom androgynous voice

# Output Configuration
OUTPUT_DIR=./audio
TEMP_DIR=./audio/temp

# Processing Configuration
MAX_REQUESTS_PER_MINUTE=45  # Stay under 50 limit
BATCH_SIZE=3  # Sessions per batch
```

**Security Note:** Add `.env` to `.gitignore` to avoid committing API keys

#### 1.5 Create Voice Profiles

**File**: `mock-therapy-data/scripts/create_voices.py` (NEW)

```python
import asyncio
import os
from hume import AsyncHumeClient
from dotenv import load_dotenv

load_dotenv()

async def create_patient_voice():
    """Create custom androgynous voice for Alex Chen (patient)"""
    client = AsyncHumeClient(api_key=os.getenv("HUME_API_KEY"))

    # Create custom voice with prompt
    voice_response = await client.voices.create(
        prompt="An androgynous voice, early 20s, slightly anxious but genuine. "
               "Warm and vulnerable with moments of hope and breakthrough. "
               "Gen-Z speaking patterns with natural hesitations and 'like' and 'um'. "
               "Non-binary identity, neither masculine nor feminine."
    )

    print(f"Patient Voice Created!")
    print(f"Voice ID: {voice_response.voice_id}")
    print(f"Add to .env: PATIENT_VOICE_ID={voice_response.voice_id}")

    return voice_response.voice_id

async def test_therapist_voice():
    """Test pre-made ITO voice for therapist"""
    client = AsyncHumeClient(api_key=os.getenv("HUME_API_KEY"))

    from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
    import base64

    utterance = PostedUtterance(
        text="That sounds like a lot to be dealing with all at once. "
             "When you say feeling really down, can you help me understand "
             "what that's been like for you?",
        description="Professional therapist, warm and validating, "
                    "actively listening with genuine empathy",
        voice=PostedUtteranceVoiceWithName(name='ITO', provider='HUME_AI'),
        speed=0.95,  # Slightly slower for therapeutic pacing
        trailing_silence=0.5
    )

    audio_chunks = []
    async for response in await client.tts.synthesize_json_streaming(
        utterances=[utterance],
        format="mp3",
        version="2"
    ):
        if response.generations:
            for gen in response.generations:
                audio_bytes = base64.b64decode(gen.audio)
                audio_chunks.append(audio_bytes)

    # Save test file
    with open("test_therapist_voice.mp3", "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    print("Therapist voice test saved: test_therapist_voice.mp3")
    print("Listen and confirm quality before proceeding.")

async def main():
    print("Creating Hume AI voices for therapy session mockup...\n")

    # Test therapist voice (pre-made ITO)
    print("1. Testing therapist voice (ITO)...")
    await test_therapist_voice()

    # Create custom patient voice
    print("\n2. Creating custom patient voice...")
    patient_voice_id = await create_patient_voice()

    print("\n✅ Voice setup complete!")
    print("\nNext steps:")
    print("1. Listen to test_therapist_voice.mp3 and confirm quality")
    print(f"2. Add PATIENT_VOICE_ID={patient_voice_id} to .env file")
    print("3. Run generate_audio.py to start audio generation")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python scripts/create_voices.py
```

### Success Criteria:

#### Automated Verification:
- [ ] Session 12 JSON metadata.duration matches actual segment end time
- [ ] `validate_sessions.py` shows all 12 sessions passing
- [ ] Python dependencies install successfully: `pip list | grep hume`
- [ ] ffmpeg installed and accessible: `ffmpeg -version`
- [ ] `.env` file exists with HUME_API_KEY populated
- [ ] Voice creation script runs without errors

#### Manual Verification:
- [ ] Hume AI account created and verified
- [ ] API key generated and tested (e.g., via curl or test script)
- [ ] Therapist test audio (`test_therapist_voice.mp3`) sounds natural and professional
- [ ] Voice quality acceptable for mockup demo
- [ ] Patient voice ID added to .env file
- [ ] Estimated costs reviewed and approved

**Implementation Note**: After voice testing passes, pause for human approval before proceeding to Phase 2.

---

## Phase 2: Audio Generation Script

### Overview
Build the main Python script to process JSON transcripts, call Hume AI TTS for each segment, and combine into full session MP3 files.

### Changes Required:

#### 2.1 Create Audio Generation Script

**File**: `mock-therapy-data/scripts/generate_audio.py` (NEW)

```python
import asyncio
import base64
import json
import os
import time
from pathlib import Path
from typing import List, Dict
from hume import AsyncHumeClient
from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
from dotenv import load_dotenv

load_dotenv()

# Configuration
HUME_API_KEY = os.getenv("HUME_API_KEY")
THERAPIST_VOICE = os.getenv("THERAPIST_VOICE_ID", "ITO")
PATIENT_VOICE = os.getenv("PATIENT_VOICE_ID")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./audio"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./audio/temp"))
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 45))

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

class RateLimiter:
    """Simple rate limiter to stay under API limits"""
    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self.requests = []

    async def wait_if_needed(self):
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]

        if len(self.requests) >= self.max_requests:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                print(f"  Rate limit: sleeping {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)
                self.requests = []

        self.requests.append(now)

async def generate_segment_audio(
    client: AsyncHumeClient,
    segment: Dict,
    session_id: str,
    rate_limiter: RateLimiter
) -> Path:
    """Generate audio for a single transcript segment"""

    # Select voice based on speaker
    voice_id = THERAPIST_VOICE if segment['speaker_id'] == 'SPEAKER_00' else PATIENT_VOICE

    # Determine speaking style from context
    description = get_speaking_description(segment)

    # Create utterance
    utterance = PostedUtterance(
        text=segment['text'],
        description=description,
        voice=PostedUtteranceVoiceWithName(
            name=voice_id,
            provider='HUME_AI'
        ),
        speed=0.95 if segment['speaker_id'] == 'SPEAKER_00' else 1.0,
        trailing_silence=0.3
    )

    # Wait for rate limiter
    await rate_limiter.wait_if_needed()

    # Generate audio
    audio_chunks = []
    async for response in await client.tts.synthesize_json_streaming(
        utterances=[utterance],
        format="mp3",
        version="2",
        instant_mode=True
    ):
        if response.generations:
            for gen in response.generations:
                audio_bytes = base64.b64decode(gen.audio)
                audio_chunks.append(audio_bytes)

    # Save segment audio
    segment_filename = f"{session_id}_seg_{segment['start']:.1f}-{segment['end']:.1f}.mp3"
    segment_path = TEMP_DIR / session_id / segment_filename
    segment_path.parent.mkdir(parents=True, exist_ok=True)

    with open(segment_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    return segment_path

def get_speaking_description(segment: Dict) -> str:
    """Generate acting instructions based on segment content"""
    text = segment['text'].lower()
    speaker = segment['speaker_id']

    if speaker == 'SPEAKER_00':  # Therapist
        if '?' in segment['text']:
            return "Warm therapist asking gentle questions, actively listening"
        elif any(word in text for word in ['safe', 'plan', 'crisis', 'hurt']):
            return "Professional and serious, concerned but calm"
        elif any(word in text for word in ['that makes sense', 'i hear you', 'that sounds']):
            return "Validating and empathetic, genuine warmth"
        else:
            return "Professional therapist, warm and supportive"

    else:  # Patient
        if any(word in text for word in ['i guess', 'i don\'t know', 'maybe', 'um']):
            return "Uncertain and tentative, slightly anxious"
        elif any(word in text for word in ['cry', 'tears', 'sad', 'down']):
            return "Emotional and vulnerable, holding back tears"
        elif any(word in text for word in ['breakthrough', 'oh my god', 'i just realized']):
            return "Moment of realization, slightly breathless with discovery"
        elif any(word in text for word in ['happy', 'better', 'hope', 'good']):
            return "Cautiously hopeful, gentle optimism"
        else:
            return "Young adult, genuine and vulnerable"

async def combine_segments_to_session(
    session_id: str,
    session_filename: str,
    segment_files: List[Path]
) -> Path:
    """Combine segment audio files into full session MP3"""
    from pydub import AudioSegment

    print(f"  Combining {len(segment_files)} segments...")

    # Load and concatenate segments
    combined = AudioSegment.empty()
    for segment_file in segment_files:
        audio = AudioSegment.from_mp3(segment_file)
        combined += audio

    # Export combined audio
    output_path = OUTPUT_DIR / session_filename
    combined.export(output_path, format="mp3", bitrate="64k")

    # Cleanup temp files
    for segment_file in segment_files:
        segment_file.unlink()

    # Remove temp directory
    (TEMP_DIR / session_id).rmdir()

    return output_path

async def generate_session_audio(session_file: Path) -> Path:
    """Generate complete audio for one therapy session"""
    client = AsyncHumeClient(api_key=HUME_API_KEY)
    rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE)

    # Load session data
    with open(session_file) as f:
        session = json.load(f)

    session_id = session['id']
    print(f"\n{'='*60}")
    print(f"Generating audio: {session_id}")
    print(f"  Duration: {session['metadata']['duration']/60:.1f} minutes")
    print(f"  Segments: {len(session['aligned_segments'])}")
    print(f"{'='*60}")

    # Generate audio for each segment
    segment_files = []
    for i, segment in enumerate(session['aligned_segments'], 1):
        speaker = "Therapist" if segment['speaker_id'] == 'SPEAKER_00' else "Patient"
        print(f"  [{i}/{len(session['aligned_segments'])}] {speaker}: {segment['text'][:60]}...")

        segment_path = await generate_segment_audio(
            client, segment, session_id, rate_limiter
        )
        segment_files.append(segment_path)

    # Combine segments
    output_path = await combine_segments_to_session(
        session_id,
        session['filename'],
        segment_files
    )

    # Verify audio duration
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(output_path)
    actual_duration = len(audio) / 1000  # Convert ms to seconds
    expected_duration = session['metadata']['duration']

    duration_diff = abs(actual_duration - expected_duration)
    if duration_diff > 30:  # Allow 30 second variance
        print(f"  ⚠️  WARNING: Duration mismatch!")
        print(f"     Expected: {expected_duration}s, Actual: {actual_duration}s")
    else:
        print(f"  ✅ Duration verified: {actual_duration:.1f}s (expected {expected_duration}s)")

    print(f"  ✅ Generated: {output_path}")
    print(f"     File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

    return output_path

async def generate_all_sessions(session_files: List[Path]):
    """Generate audio for all sessions"""
    print(f"\nStarting audio generation for {len(session_files)} sessions")
    print(f"Estimated time: {len(session_files) * 15} - {len(session_files) * 25} minutes")

    start_time = time.time()

    for session_file in session_files:
        try:
            await generate_session_audio(session_file)
        except Exception as e:
            print(f"\n❌ ERROR generating {session_file.name}: {e}")
            print("Continuing with next session...")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ All sessions complete!")
    print(f"   Total time: {elapsed/60:.1f} minutes")
    print(f"   Output directory: {OUTPUT_DIR.absolute()}")
    print(f"{'='*60}")

async def main():
    # Validate configuration
    if not HUME_API_KEY:
        print("❌ Error: HUME_API_KEY not set in .env file")
        return

    if not PATIENT_VOICE:
        print("❌ Error: PATIENT_VOICE_ID not set in .env file")
        print("   Run create_voices.py first to create custom patient voice")
        return

    # Find all session files
    sessions_dir = Path("sessions")
    session_files = sorted(sessions_dir.glob("session_*.json"))

    if not session_files:
        print(f"❌ Error: No session files found in {sessions_dir.absolute()}")
        return

    print(f"Found {len(session_files)} session files:")
    for f in session_files:
        print(f"  - {f.name}")

    # Confirm before proceeding
    print(f"\nConfiguration:")
    print(f"  API Key: {HUME_API_KEY[:20]}...")
    print(f"  Therapist Voice: {THERAPIST_VOICE}")
    print(f"  Patient Voice: {PATIENT_VOICE}")
    print(f"  Output: {OUTPUT_DIR.absolute()}")
    print(f"  Rate Limit: {MAX_REQUESTS_PER_MINUTE} req/min")

    response = input("\nProceed with generation? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    await generate_all_sessions(session_files)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2.2 Create Single Session Test Script

**File**: `mock-therapy-data/scripts/test_one_session.py` (NEW)

```python
"""Test audio generation with a single session before batch processing"""
import asyncio
from pathlib import Path
from generate_audio import generate_session_audio

async def main():
    # Use shortest session for quick test
    test_session = Path("sessions/session_02_emotional_regulation.json")

    if not test_session.exists():
        print(f"Error: {test_session} not found")
        return

    print("Testing audio generation with one session...")
    print("This will help verify voice quality before batch processing.\n")

    output_path = await generate_session_audio(test_session)

    print("\n" + "="*60)
    print("✅ Test complete!")
    print(f"   Listen to: {output_path}")
    print("\nQuality checklist:")
    print("  [ ] Therapist voice sounds professional and warm")
    print("  [ ] Patient voice sounds androgynous and natural")
    print("  [ ] Voices are clearly distinguishable")
    print("  [ ] Emotional moments sound authentic")
    print("  [ ] No robotic or glitchy audio")
    print("  [ ] Pacing feels natural")
    print("\nIf quality is acceptable, run: python scripts/generate_audio.py")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
```

### Success Criteria:

#### Automated Verification:
- [ ] Scripts run without Python syntax errors: `python -m py_compile scripts/generate_audio.py`
- [ ] All imports resolve successfully
- [ ] Environment variables load correctly
- [ ] Session JSON files parse without errors
- [ ] Output directories created successfully

#### Manual Verification:
- [ ] Test single session generation: `python scripts/test_one_session.py`
- [ ] Output MP3 file plays correctly
- [ ] Therapist voice quality acceptable (warm, professional)
- [ ] Patient voice quality acceptable (androgynous, natural)
- [ ] Voices clearly distinguishable
- [ ] Emotional delivery authentic (not robotic)
- [ ] Audio duration matches transcript metadata (±30 seconds)
- [ ] No audio glitches or artifacts

**Implementation Note**: After test session passes quality review, proceed to Phase 3 batch generation.

---

## Phase 3: Batch Audio Generation

### Overview
Generate audio for all 12 therapy sessions using the validated script and voice configuration.

### Changes Required:

#### 3.1 Run Batch Generation

**Command:**
```bash
cd mock-therapy-data
source venv/bin/activate
python scripts/generate_audio.py
```

**Expected Behavior:**
- Prompts for confirmation before starting
- Processes sessions sequentially (to manage rate limits)
- Shows progress for each segment
- Handles rate limiting automatically (sleeps when approaching 50 req/min)
- Validates duration after each session
- Continues on error (logs error and moves to next session)

**Expected Output:**
```
Found 12 session files:
  - session_01_crisis_intake.json
  - session_02_emotional_regulation.json
  ...
  - session_12_thriving.json

Configuration:
  API Key: hume_api_xxx...
  Therapist Voice: ITO
  Patient Voice: custom_voice_abc123
  Output: /path/to/mock-therapy-data/audio
  Rate Limit: 45 req/min

Proceed with generation? (yes/no): yes

============================================================
Generating audio: session_01_alex_chen
  Duration: 60.0 minutes
  Segments: 213
============================================================
  [1/213] Therapist: Hi Alex, welcome. I'm Dr. Rodriguez...
  [2/213] Patient: Yeah, that makes sense. Um, I'm really nervous...
  ...
  [213/213] Patient: Thank you. I'll see you next week.
  Combining 213 segments...
  ✅ Duration verified: 3601.2s (expected 3600s)
  ✅ Generated: audio/session_01_2025-01-10.mp3
     File size: 14.2 MB

...

============================================================
✅ All sessions complete!
   Total time: 127.3 minutes
   Output directory: /path/to/mock-therapy-data/audio
============================================================
```

**Estimated Time:**
- Per segment: ~5-8 seconds (API call + processing)
- Per session: 10-20 minutes (depending on segment count)
- Total: ~2-4 hours for all 12 sessions

#### 3.2 Create Validation Script

**File**: `mock-therapy-data/scripts/validate_audio.py` (NEW)

```python
"""Validate generated audio files"""
from pathlib import Path
from pydub import AudioSegment
import json

def validate_audio_files():
    audio_dir = Path("audio")
    sessions_dir = Path("sessions")

    print("Validating generated audio files...\n")

    issues = []

    for session_file in sorted(sessions_dir.glob("session_*.json")):
        with open(session_file) as f:
            session = json.load(f)

        audio_path = audio_dir / session['filename']

        # Check file exists
        if not audio_path.exists():
            issues.append(f"❌ Missing: {session['filename']}")
            continue

        # Check file size
        file_size_mb = audio_path.stat().st_size / 1024 / 1024
        if file_size_mb < 5:
            issues.append(f"⚠️  Suspiciously small: {session['filename']} ({file_size_mb:.1f} MB)")

        # Check duration
        audio = AudioSegment.from_mp3(audio_path)
        actual_duration = len(audio) / 1000
        expected_duration = session['metadata']['duration']

        duration_diff = abs(actual_duration - expected_duration)
        if duration_diff > 30:
            issues.append(
                f"⚠️  Duration mismatch: {session['filename']} "
                f"(expected {expected_duration}s, got {actual_duration:.1f}s, diff: {duration_diff:.1f}s)"
            )

        print(f"✅ {session['filename']}: {actual_duration:.1f}s, {file_size_mb:.1f} MB")

    print("\n" + "="*60)
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ All audio files validated successfully!")
    print("="*60)

if __name__ == "__main__":
    validate_audio_files()
```

**Run validation:**
```bash
python scripts/validate_audio.py
```

### Success Criteria:

#### Automated Verification:
- [ ] All 12 MP3 files exist in `audio/` directory: `ls audio/*.mp3 | wc -l` returns 12
- [ ] No temp files remain: `ls audio/temp/` is empty or directory doesn't exist
- [ ] Audio validation script passes: `python scripts/validate_audio.py`
- [ ] All file sizes > 5MB (indicates full session, not stub)
- [ ] All durations within ±30 seconds of expected

#### Manual Verification:
- [ ] Listen to 3 sample sessions (beginning, middle, end) for quality
- [ ] Verify therapist/patient voices are distinct and consistent across sessions
- [ ] Check emotional delivery in breakthrough moments (e.g., Session 3 ADHD realization)
- [ ] Confirm no audio gaps, glitches, or artifacts
- [ ] Verify total file size reasonable (~100-150MB for all 12 sessions)

**Implementation Note**: If any sessions fail validation, regenerate individually using modified test script targeting specific session.

---

## Phase 4: Documentation and Cleanup

### Overview
Document the generated audio files, update integration guide, and clean up temporary files.

### Changes Required:

#### 4.1 Update Integration Guide

**File**: `mock-therapy-data/INTEGRATION_GUIDE.md`

**Update Section "Audio Generation Next Steps" (lines 419-472):**

```markdown
## Audio Files (COMPLETED)

**Generation Date:** December 22, 2025
**TTS Service:** Hume AI Octave v2
**Total Audio:** 10.25 hours across 12 sessions

**Voice Configuration:**
- **Dr. Sarah Mitchell (SPEAKER_00):** Hume AI ITO voice (male, professional)
- **Alex Chen (SPEAKER_01):** Custom androgynous voice (warm, vulnerable)

**Audio Files:**
All audio files are located in `mock-therapy-data/audio/`:

```
audio/
├── session_01_2025-01-10.mp3  (60 min, ~14 MB)
├── session_02_2025-01-17.mp3  (45 min, ~10 MB)
├── session_03_2025-01-31.mp3  (50 min, ~12 MB)
├── session_04_2025-02-14.mp3  (45 min, ~10 MB)
├── session_05_2025-02-28.mp3  (55 min, ~13 MB)
├── session_06_2025-03-14.mp3  (50 min, ~12 MB)
├── session_07_2025-04-04.mp3  (50 min, ~12 MB)
├── session_08_2025-04-18.mp3  (45 min, ~10 MB)
├── session_09_2025-05-02.mp3  (60 min, ~14 MB)
├── session_10_2025-05-09.mp3  (55 min, ~13 MB)
├── session_11_2025-05-16.mp3  (50 min, ~12 MB)
└── session_12_2025-05-30.mp3  (88 min, ~21 MB)
```

**Quality Verification:**
- ✅ All durations match transcript metadata (±30 seconds)
- ✅ Voices distinguishable and natural
- ✅ Emotional delivery authentic
- ✅ No audio artifacts or glitches

**Usage:**
These audio files are for **mockup/demo purposes only**. To use in frontend:

```typescript
// Example: Play audio in session detail view
const audioUrl = `/mock-therapy-data/audio/session_01_2025-01-10.mp3`;
const audio = new Audio(audioUrl);
audio.play();
```
```

#### 4.2 Create Audio Generation README

**File**: `mock-therapy-data/audio/README.md` (NEW)

```markdown
# Therapy Session Audio Files

**Generated:** December 22, 2025
**Service:** Hume AI Octave TTS v2
**Total Duration:** 10.25 hours

## Voice Profiles

**Therapist (Dr. Sarah Mitchell):**
- Voice: Hume AI ITO (male, pre-made voice)
- Characteristics: Professional, warm, validating
- Speed: 0.95x (slightly slower for therapeutic pacing)

**Patient (Alex Chen):**
- Voice: Custom androgynous voice
- Characteristics: Early 20s, vulnerable, genuine
- Personality: Gen-Z speaking patterns, natural hesitations

## Files

| Session | Date | Duration | Size | Description |
|---------|------|----------|------|-------------|
| 01 | Jan 10 | 60 min | ~14 MB | Crisis intake, safety planning |
| 02 | Jan 17 | 45 min | ~10 MB | Emotional regulation (DBT) |
| 03 | Jan 31 | 50 min | ~12 MB | ADHD discovery breakthrough |
| 04 | Feb 14 | 45 min | ~10 MB | Medication start |
| 05 | Feb 28 | 55 min | ~13 MB | Family conflict |
| 06 | Mar 14 | 50 min | ~12 MB | Spring break hope |
| 07 | Apr 4 | 50 min | ~12 MB | Dating anxiety |
| 08 | Apr 18 | 45 min | ~10 MB | Relationship boundaries |
| 09 | May 2 | 60 min | ~14 MB | Coming out preparation |
| 10 | May 9 | 55 min | ~13 MB | Coming out aftermath |
| 11 | May 16 | 50 min | ~12 MB | Rebuilding resilience |
| 12 | May 30 | 88 min | ~21 MB | Thriving and termination |

**Total:** 153 MB

## Quality Notes

- All audio verified for duration accuracy
- Emotional delivery matches transcript context
- No robotic or artificial-sounding segments
- Voices remain consistent across all sessions

## Regeneration

To regenerate audio (if needed):

```bash
cd ../
source venv/bin/activate
python scripts/generate_audio.py
```

See `../plans/2025-12-22-hume-ai-audio-generation.md` for details.
```

#### 4.3 Add .gitignore Entry

**File**: `mock-therapy-data/.gitignore` (NEW or UPDATE)

```
# Virtual environment
venv/
__pycache__/

# Environment configuration
.env

# Audio files (too large for git)
audio/*.mp3
audio/temp/

# Test files
test_*.mp3
```

#### 4.4 Create Cost Report

**File**: `mock-therapy-data/COST_REPORT.md` (NEW)

```markdown
# Hume AI Audio Generation Cost Report

**Date:** December 22, 2025
**Service:** Hume AI Octave TTS

## Character Count

**Total Segments:** ~537 (11 sessions, Session 12 pending fix)
**Average Characters per Segment:** ~200
**Total Characters:** ~107,400

**Session 12 (if 88 min):** +additional characters (TBD)

## Pricing

**Plan Used:** [Starter/Creator/Pro - fill in actual]
**Rate:** $X per 1,000 characters

**Estimated Cost:**
- Base characters: 107,400 × ($X / 1,000) = $Y
- Session 12: [TBD]
- **Total: $Z**

**Actual Cost:** $[fill in from Hume AI dashboard]

## Comparison

**Hume AI vs. Alternatives:**
- Hume AI: $Z for 10.25 hours
- ElevenLabs: ~$Z×2 (50% more expensive)
- Google TTS: Cheaper but lower quality
- AWS Polly: Comparable pricing, less emotional intelligence

**Value:** Hume AI provided superior emotional delivery for therapy context.

## API Usage

- Total API calls: ~537 segments
- Rate limiting: 45 req/min configured
- Actual generation time: ~[X] hours
- Errors encountered: [None/List any]

## Recommendations

For future audio generation:
- Hume AI excellent for emotionally nuanced content
- Consider batch processing 3-4 sessions at a time to manage costs
- Test voice quality with 1 session before batch generation
- Custom voice creation worth the effort for character authenticity
```

### Success Criteria:

#### Automated Verification:
- [ ] All files validated: `python scripts/validate_audio.py` passes
- [ ] Git ignores audio files: `git status` doesn't show audio/*.mp3
- [ ] Temp directory empty: `ls audio/temp/` shows nothing or doesn't exist

#### Manual Verification:
- [ ] INTEGRATION_GUIDE.md updated with audio file locations
- [ ] audio/README.md created with complete file listing
- [ ] COST_REPORT.md created with actual costs from Hume AI dashboard
- [ ] All documentation accurate and complete
- [ ] Audio files organized and ready for demo

**Implementation Note**: This phase is complete when all documentation is updated and audio files are ready for use.

---

## Testing Strategy

### Quality Testing

**Test 1: Voice Distinctiveness**
- Listen to Session 1, segments with back-and-forth dialogue
- Verify therapist (male) and patient (androgynous) voices clearly different
- Check for consistent voice characteristics throughout session

**Test 2: Emotional Authenticity**
- Session 3 (~1935s): ADHD breakthrough - should sound like genuine realization
- Session 10 (coming out aftermath): Should convey distress and emotional weight
- Session 12 (thriving): Should sound hopeful and confident

**Test 3: Natural Pacing**
- Verify no unnatural pauses or rushing
- Check trailing silence between speaker turns feels natural
- Confirm therapist speaks ~5% slower (0.95x speed)

**Test 4: Technical Quality**
- No robotic artifacts or glitches
- No audio dropouts or volume inconsistencies
- Clean transitions between segments

### Duration Testing

**Automated:**
```python
# Run validate_audio.py
python scripts/validate_audio.py
```

**Manual:**
- Open 3 random session MP3 files
- Verify duration matches file properties
- Compare to JSON metadata.duration field

### Integration Testing

**Frontend Integration (Optional):**
```html
<!-- Test audio playback in browser -->
<audio controls>
  <source src="mock-therapy-data/audio/session_01_2025-01-10.mp3" type="audio/mpeg">
</audio>
```

- Verify audio loads and plays
- Check file path resolution
- Confirm browser compatibility

---

## Performance Considerations

**API Rate Limiting:**
- Hume AI limit: 50 requests per minute
- Script configured: 45 requests per minute (safety buffer)
- Automatic sleep when approaching limit
- Per-session generation time: 10-20 minutes

**File Size Optimization:**
- MP3 bitrate: 64kbps (balance quality/size)
- Expected file size: ~200KB per minute of audio
- 45-minute session: ~9-10MB
- 60-minute session: ~12-14MB
- Total: ~100-150MB for 12 sessions

**Processing Time:**
- Single segment: 5-8 seconds (API latency + processing)
- 200-segment session: ~15-20 minutes
- 12 sessions total: ~2-4 hours
- Rate limiting adds overhead

**Cost Optimization:**
- Test 1 session before batch to avoid wasting credits on poor quality
- Use custom voices to maximize authenticity (worth the setup time)
- Batch process in groups of 3-4 to monitor quality mid-process

---

## Migration Notes

**Not Applicable** - This is one-time audio generation for mockup purposes, not a database migration or code deployment.

**Future Considerations:**
If audio generation becomes a production feature:
1. Store voice IDs in database
2. Implement job queue for async processing
3. Add progress tracking
4. Implement retry logic for failed segments
5. Consider audio file CDN storage

---

## Troubleshooting

### Issue: "HUME_API_KEY not set"
**Solution:**
```bash
# Verify .env file exists and has key
cat .env | grep HUME_API_KEY

# If missing, add:
echo "HUME_API_KEY=your_key_here" >> .env
```

### Issue: "PATIENT_VOICE_ID not set"
**Solution:**
```bash
# Run voice creation script first
python scripts/create_voices.py

# Add returned voice ID to .env
echo "PATIENT_VOICE_ID=voice_id_here" >> .env
```

### Issue: Rate limit errors (429 Too Many Requests)
**Solution:**
- Reduce MAX_REQUESTS_PER_MINUTE in .env (try 30 or 35)
- Add manual delays between sessions
- Check Hume AI dashboard for current rate limits

### Issue: Audio duration mismatch
**Solution:**
- Check Session 12 metadata.duration field (should be 5300.0, not 3000.0)
- Verify ffmpeg installed correctly: `ffmpeg -version`
- Manually inspect segment timestamps in JSON for gaps

### Issue: Voice sounds robotic
**Solution:**
- Review `description` parameter in generate_segment_audio()
- Simplify acting instructions (Hume AI recommends <100 chars)
- Test with different voice speed settings (0.9-1.1 range)
- Consider creating new custom voice with better prompt

### Issue: File size too large
**Solution:**
- Reduce MP3 bitrate in combine_segments_to_session():
  ```python
  combined.export(output_path, format="mp3", bitrate="48k")  # Down from 64k
  ```
- Note: Lower bitrate may reduce quality

### Issue: Script crashes mid-generation
**Solution:**
- Check which session failed (last printed session ID)
- Manually generate that session: `python scripts/test_one_session.py`
- Modify script to resume from last successful session
- Check Hume AI API status: https://status.hume.ai/

---

## References

- **Hume AI Documentation:** https://dev.hume.ai/docs/text-to-speech-tts/overview
- **Python SDK:** https://github.com/HumeAI/hume-python-sdk
- **Session Transcripts:** `mock-therapy-data/sessions/`
- **Integration Guide:** `mock-therapy-data/INTEGRATION_GUIDE.md`
- **Research Document:** `thoughts/shared/research/2025-12-22-audio-generation-pipeline-next-steps.md`

---

## Execution Summary

**Total Phases:** 4
**Estimated Time:** 4-6 hours (including API account setup and generation time)
**Dependencies:** Session 12 timestamp fix must be complete before starting

**Critical Path:**
1. Fix Session 12 → 15 minutes
2. Set up Hume AI account and create voices → 30 minutes
3. Test 1 session generation and quality review → 30 minutes
4. Batch generate 11 remaining sessions → 2-4 hours
5. Validation and documentation → 30 minutes

**Deliverables Upon Completion:**
- ✅ 12 high-quality therapy session MP3 files
- ✅ Distinct, natural voices for therapist and patient
- ✅ Emotionally intelligent delivery matching clinical context
- ✅ Audio files ready for mockup demo
- ✅ Complete documentation and cost report
- ✅ Validation scripts for quality assurance

**Success Metrics:**
- All 12 audio files generated
- Duration accuracy within ±30 seconds
- Voice quality acceptable for demo presentation
- Emotional delivery authentic and engaging
- Total cost under estimated budget
