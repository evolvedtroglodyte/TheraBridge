#!/usr/bin/env python3
"""
Full Pipeline Test: Preprocessing + Whisper + Pyannote Diarization
===================================================================
Tests all three stages with the one-minute audio sample.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug logging helper
def debug_log(stage: str, message: str):
    """Print debug message with stage prefix"""
    print(f"[DEBUG:{stage}] {message}")


# ============================================================================
# STAGE 1: Audio Preprocessing
# ============================================================================
class AudioPreprocessor:
    """
    Prepares audio for Whisper transcription.

    What it does:
    - Loads any audio format (mp3, wav, m4a, etc.) using ffmpeg
    - Trims silence from start/end to focus on actual speech
    - Normalizes volume so quiet recordings become clearer
    - Converts to 16kHz mono MP3 - Whisper's optimal format
    - Keeps file under 25MB (Whisper API limit)
    """

    def __init__(self, output_format: str = "wav"):
        # Use WAV for better compatibility with pyannote/torchaudio
        # MP3 can be used for Whisper but WAV is more reliable for diarization
        self.target_format = output_format
        self.target_sample_rate = 16000
        self.target_bitrate = "64k"  # Only used for MP3
        self.max_file_size_mb = 25

    def preprocess(self, audio_path: str, output_path: str = None) -> str:
        from pydub import AudioSegment, effects
        from pydub.silence import detect_leading_silence

        debug_log("PREPROCESS", f"Loading audio file: {audio_path}")
        audio = AudioSegment.from_file(audio_path)

        original_duration = len(audio) / 1000
        original_channels = audio.channels
        original_rate = audio.frame_rate
        debug_log("PREPROCESS", f"Original: {original_duration:.1f}s, {original_channels}ch, {original_rate}Hz")

        # Step 1: Trim leading/trailing silence
        debug_log("PREPROCESS", "Trimming silence...")
        start_trim = detect_leading_silence(audio, silence_threshold=-40)
        end_trim = detect_leading_silence(audio.reverse(), silence_threshold=-40)
        duration = len(audio)
        audio = audio[start_trim:duration - end_trim]
        trimmed = (start_trim + end_trim) / 1000
        debug_log("PREPROCESS", f"Trimmed {trimmed:.2f}s of silence")

        # Step 2: Normalize volume
        debug_log("PREPROCESS", "Normalizing volume...")
        original_dbfs = audio.dBFS
        audio = effects.normalize(audio, headroom=0.1)
        debug_log("PREPROCESS", f"Volume: {original_dbfs:.1f}dB -> {audio.dBFS:.1f}dB")

        # Step 3: Convert to mono 16kHz
        debug_log("PREPROCESS", "Converting to mono 16kHz...")
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(self.target_sample_rate)

        # Step 4: Export
        if output_path is None:
            output_path = audio_path.rsplit('.', 1)[0] + f'_processed.{self.target_format}'

        if self.target_format == "mp3":
            audio.export(output_path, format=self.target_format, bitrate=self.target_bitrate)
        else:
            audio.export(output_path, format=self.target_format)
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        debug_log("PREPROCESS", f"Exported: {output_path} ({file_size_mb:.2f}MB)")

        return output_path


# ============================================================================
# STAGE 2: Whisper Transcription
# ============================================================================
class WhisperTranscriber:
    """
    Sends audio to OpenAI Whisper API for speech-to-text.

    What it does:
    - Uploads the preprocessed audio to OpenAI
    - Whisper AI model converts speech to text
    - Returns timestamps for each sentence/segment
    - We use "verbose_json" to get start/end times for diarization alignment
    """

    def __init__(self):
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_path: str) -> Dict:
        debug_log("WHISPER", f"Uploading to Whisper API: {audio_path}")
        debug_log("WHISPER", f"File size: {os.path.getsize(audio_path) / (1024*1024):.2f}MB")

        start_time = time.time()

        with open(audio_path, "rb") as f:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        elapsed = time.time() - start_time
        debug_log("WHISPER", f"API response received in {elapsed:.2f}s")

        # Extract segments
        segments = [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            for seg in response.segments
        ]

        debug_log("WHISPER", f"Got {len(segments)} segments, duration: {response.duration}s")

        return {
            "segments": segments,
            "full_text": response.text,
            "language": response.language,
            "duration": response.duration
        }


# ============================================================================
# STAGE 3: Pyannote Speaker Diarization
# ============================================================================
class SpeakerDiarizer:
    """
    Identifies WHO is speaking WHEN using Pyannote AI model.

    What it does:
    - Loads pretrained speaker diarization model (pyannote/speaker-diarization-3.1)
    - Analyzes audio to detect voice characteristics
    - Creates "speaker turns" - time ranges for each speaker
    - We tell it there are 2 speakers (therapy: therapist + client)

    The model uses neural networks trained on thousands of hours of conversation
    to distinguish different voices based on pitch, tone, speaking patterns, etc.
    """

    def __init__(self, num_speakers: int = 2):
        import torch
        from pyannote.audio import Pipeline
        from pyannote.audio.core.task import Specifications, Problem, Resolution
        import sys
        from pathlib import Path

        # Add src to path to import compatibility layer
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from pyannote_compat import log_version_info

        # Add safe globals for PyTorch 2.6+ compatibility
        import torch.serialization
        torch.serialization.add_safe_globals([
            torch.torch_version.TorchVersion,
            Specifications,
            Problem,
            Resolution
        ])

        self.num_speakers = num_speakers

        # Use MPS (Apple Silicon GPU) for faster processing
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        debug_log("DIARIZE", f"Using device: {self.device}")

        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN not set - needed for pyannote model")

        # Log pyannote version information
        log_version_info(lambda msg: debug_log("DIARIZE", msg))

        debug_log("DIARIZE", "Loading pyannote speaker-diarization-3.1 model...")
        start = time.time()

        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )
        self.pipeline.to(self.device)

        debug_log("DIARIZE", f"Model loaded in {time.time() - start:.2f}s")

    def diarize(self, audio_path: str) -> List[Dict]:
        """
        Run speaker diarization on audio file.

        Returns list of speaker turns: [{"speaker": "SPEAKER_00", "start": 0.5, "end": 3.2}, ...]
        """
        import torchaudio

        debug_log("DIARIZE", f"Processing audio: {audio_path}")
        start = time.time()

        # Load audio with torchaudio (workaround for torchcodec issues)
        debug_log("DIARIZE", "Loading audio with torchaudio...")
        waveform, sample_rate = torchaudio.load(audio_path)
        debug_log("DIARIZE", f"Loaded: shape={waveform.shape}, sample_rate={sample_rate}")

        # Pyannote expects mono audio - if stereo, convert to mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
            debug_log("DIARIZE", "Converted to mono")

        # Create input dict that pyannote expects
        audio_input = {"waveform": waveform, "sample_rate": sample_rate}

        # Run the diarization pipeline
        debug_log("DIARIZE", "Running diarization model...")
        diarization = self.pipeline(audio_input, num_speakers=self.num_speakers)

        # Use compatibility layer to extract Annotation object
        # Handles both pyannote 3.x (Annotation directly) and 4.x (DiarizeOutput wrapper)
        from pyannote_compat import extract_annotation
        annotation = extract_annotation(diarization)
        debug_log("DIARIZE", f"Extracted Annotation from {type(diarization).__name__}")

        # Convert to list of speaker turns
        turns = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            turns.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end
            })

        debug_log("DIARIZE", f"Found {len(turns)} speaker turns in {time.time() - start:.2f}s")

        # Count turns per speaker
        speaker_counts = {}
        for t in turns:
            speaker_counts[t["speaker"]] = speaker_counts.get(t["speaker"], 0) + 1
        debug_log("DIARIZE", f"Speaker distribution: {speaker_counts}")

        return turns


# ============================================================================
# ALIGNMENT: Combining Whisper + Diarization
# ============================================================================
def align_speakers_with_segments(segments: List[Dict], turns: List[Dict]) -> List[Dict]:
    """
    Matches each Whisper text segment with the speaker who said it.

    How it works:
    - For each Whisper segment (with start/end times)
    - Find which speaker turn overlaps the most with that time range
    - Assign that speaker to the segment

    Example:
    - Segment: "Hello, how are you?" (0.5s - 2.0s)
    - Speaker turns: SPEAKER_00 (0.0s - 1.8s), SPEAKER_01 (2.0s - 5.0s)
    - Overlap: SPEAKER_00 has 1.3s overlap, SPEAKER_01 has 0s
    - Result: Assign SPEAKER_00 to this segment
    """
    debug_log("ALIGN", f"Aligning {len(segments)} segments with {len(turns)} speaker turns")

    aligned = []
    for seg in segments:
        seg_start, seg_end = seg["start"], seg["end"]
        seg_duration = seg_end - seg_start

        # Find speaker with maximum overlap
        best_speaker = "UNKNOWN"
        best_overlap = 0

        for turn in turns:
            # Calculate overlap: max(0, min(end1, end2) - max(start1, start2))
            overlap_start = max(seg_start, turn["start"])
            overlap_end = min(seg_end, turn["end"])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        # Only assign speaker if overlap covers at least 50% of segment
        # Otherwise mark as UNKNOWN (insufficient speaker coverage)
        if seg_duration > 0 and (best_overlap / seg_duration) < 0.5:
            best_speaker = "UNKNOWN"

        aligned.append({
            "start": seg_start,
            "end": seg_end,
            "text": seg["text"],
            "speaker": best_speaker
        })

    # Stats
    speaker_text_count = {}
    for seg in aligned:
        speaker_text_count[seg["speaker"]] = speaker_text_count.get(seg["speaker"], 0) + 1
    debug_log("ALIGN", f"Segments per speaker: {speaker_text_count}")

    return aligned


# ============================================================================
# CHUNKED TRANSCRIPTION: Handle files > 25MB
# ============================================================================
def split_audio_for_whisper(audio_path: str, max_chunk_minutes: int = 10) -> List[str]:
    """
    Split audio into chunks if file exceeds Whisper's 25MB limit.
    Returns list of chunk file paths (or single original path if no split needed).
    """
    from pydub import AudioSegment

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    # If under limit, no chunking needed
    if file_size_mb <= 24:  # 24MB to leave margin
        debug_log("CHUNK", f"File {file_size_mb:.1f}MB under limit, no chunking needed")
        return [audio_path]

    debug_log("CHUNK", f"File {file_size_mb:.1f}MB exceeds limit, splitting...")

    audio = AudioSegment.from_file(audio_path)
    chunk_length_ms = max_chunk_minutes * 60 * 1000  # 10 min in ms

    chunks = []
    chunk_dir = Path(audio_path).parent

    for i, start_ms in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start_ms:start_ms + chunk_length_ms]
        chunk_path = str(chunk_dir / f"chunk_{i:03d}.mp3")
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        chunks.append(chunk_path)
        debug_log("CHUNK", f"Created chunk {i}: {start_ms/1000:.1f}s - {(start_ms + len(chunk))/1000:.1f}s")

    debug_log("CHUNK", f"Split into {len(chunks)} chunks")
    return chunks


def transcribe_with_chunks(transcriber: WhisperTranscriber, audio_path: str) -> Dict:
    """
    Transcribe audio, using chunking if file exceeds Whisper limit.
    Merges results and adjusts timestamps.
    """
    chunks = split_audio_for_whisper(audio_path)

    if len(chunks) == 1:
        # No chunking needed
        return transcriber.transcribe(chunks[0])

    # Process each chunk
    all_segments = []
    full_text_parts = []
    time_offset = 0.0
    detected_language = None

    for i, chunk_path in enumerate(chunks):
        debug_log("WHISPER", f"Transcribing chunk {i+1}/{len(chunks)}")
        result = transcriber.transcribe(chunk_path)

        # Adjust timestamps by offset
        for seg in result["segments"]:
            all_segments.append({
                "start": seg["start"] + time_offset,
                "end": seg["end"] + time_offset,
                "text": seg["text"]
            })

        full_text_parts.append(result["full_text"])
        detected_language = result["language"]
        time_offset += result["duration"]

        # Cleanup chunk file (don't delete original)
        if chunk_path != audio_path:
            os.remove(chunk_path)
            debug_log("CHUNK", f"Cleaned up chunk {i}")

    debug_log("WHISPER", f"Merged {len(all_segments)} segments, total duration: {time_offset:.1f}s")

    return {
        "segments": all_segments,
        "full_text": " ".join(full_text_parts),
        "language": detected_language,
        "duration": time_offset
    }


# ============================================================================
# MAIN TEST
# ============================================================================
def main():
    import sys

    print("=" * 60)
    print("FULL PIPELINE TEST: Preprocess + Whisper + Diarization")
    print("=" * 60)

    # Input file - use command line arg or default
    script_dir = Path(__file__).parent
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
    else:
        # Try to find any available sample audio file
        candidates = [
            "compressed-cbt-session.m4a",
            "LIVE Cognitive Behavioral Therapy Session (1).mp3",
            "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
        ]
        audio_file = None
        for candidate in candidates:
            test_path = script_dir / "samples" / candidate
            if test_path.exists():
                audio_file = test_path
                break

    if audio_file is None or not audio_file.exists():
        print(f"ERROR: No sample audio files found in tests/samples/")
        print(f"")
        print(f"Please add sample audio files to run this test.")
        print(f"See tests/README.md for setup instructions.")
        print(f"")
        print(f"Quick setup:")
        print(f"1. Download a therapy session from YouTube:")
        print(f"   yt-dlp -x --audio-format mp3 'https://youtube.com/watch?v=...'")
        print(f"2. Move file to: {script_dir / 'samples'}/")
        print(f"3. Or provide audio file path as argument: python {__file__} /path/to/audio.mp3")
        return

    print(f"\nInput: {audio_file}")
    print(f"Size: {os.path.getsize(audio_file) / (1024*1024):.2f}MB")

    total_start = time.time()

    # ------------------------------------------
    # STAGE 1: Preprocessing
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 1: AUDIO PREPROCESSING")
    print("=" * 60)
    print("""
    What happens here:
    - Load the audio file (any format)
    - Trim silence from start/end
    - Normalize volume levels
    - Convert to 16kHz mono MP3 (works for both Whisper and diarization)
    """)

    # Single MP3 output - works for both Whisper and diarization
    preprocessor = AudioPreprocessor(output_format="mp3")
    processed_audio = preprocessor.preprocess(str(audio_file), str(script_dir / "processed/temp_processed.mp3"))

    # ------------------------------------------
    # STAGE 2: Whisper Transcription
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 2: WHISPER TRANSCRIPTION")
    print("=" * 60)
    print("""
    What happens here:
    - Upload audio to OpenAI's Whisper API
    - AI converts speech to text
    - Returns text with timestamps per segment
    """)

    transcriber = WhisperTranscriber()
    transcription = transcribe_with_chunks(transcriber, processed_audio)

    print("\n--- Whisper Raw Output ---")
    print(f"Duration: {transcription['duration']}s")
    print(f"Language: {transcription['language']}")
    print(f"Segments: {len(transcription['segments'])}")
    print("\nFull text preview (first 500 chars):")
    print(transcription['full_text'][:500] + "..." if len(transcription['full_text']) > 500 else transcription['full_text'])

    # ------------------------------------------
    # STAGE 3: Speaker Diarization
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 3: SPEAKER DIARIZATION (Pyannote)")
    print("=" * 60)
    print("""
    What happens here:
    - Load pyannote AI model (trained on conversations)
    - Analyze voice characteristics throughout audio
    - Detect speaker changes based on pitch, tone, rhythm
    - Output: "who speaks when" (speaker turns)
    """)

    diarizer = SpeakerDiarizer(num_speakers=2)
    speaker_turns = diarizer.diarize(processed_audio)  # MP3 works with torchaudio

    print("\n--- Speaker Turns (first 10) ---")
    for i, turn in enumerate(speaker_turns[:10]):
        print(f"  {turn['speaker']}: {turn['start']:.2f}s - {turn['end']:.2f}s")
    if len(speaker_turns) > 10:
        print(f"  ... and {len(speaker_turns) - 10} more turns")

    # ------------------------------------------
    # ALIGNMENT: Combine results
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("ALIGNMENT: Matching Speakers to Text")
    print("=" * 60)
    print("""
    What happens here:
    - Take each text segment (with timestamp)
    - Find which speaker was talking at that time
    - Assign speaker label to the text
    - Uses "temporal overlap" - finds speaker with most time overlap
    """)

    aligned_segments = align_speakers_with_segments(transcription['segments'], speaker_turns)

    # ------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------
    print("\n" + "=" * 60)
    print("FINAL OUTPUT: Diarized Transcription")
    print("=" * 60)

    total_time = time.time() - total_start
    print(f"\nTotal processing time: {total_time:.2f}s")

    print("\n--- DIARIZED TRANSCRIPT ---\n")

    current_speaker = None
    for seg in aligned_segments:
        if seg["speaker"] != current_speaker:
            current_speaker = seg["speaker"]
            print(f"\n[{current_speaker}]")
        print(f"  ({seg['start']:.1f}s - {seg['end']:.1f}s): {seg['text']}")

    # Save results
    output = {
        "metadata": {
            "source_file": str(audio_file),
            "duration": transcription['duration'],
            "language": transcription['language'],
            "processing_time_seconds": total_time,
            "num_segments": len(aligned_segments),
            "num_speaker_turns": len(speaker_turns)
        },
        "speaker_turns": speaker_turns,
        "diarized_segments": aligned_segments,
        "full_text": transcription['full_text']
    }

    output_file = script_dir / "outputs/diarization_output.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    # Cleanup temp file
    temp_file = script_dir / "processed/temp_processed.mp3"
    if temp_file.exists():
        temp_file.unlink()
    print("Cleaned up temp file")


if __name__ == "__main__":
    main()
