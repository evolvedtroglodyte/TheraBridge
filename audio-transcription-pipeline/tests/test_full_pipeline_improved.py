#!/usr/bin/env python3
"""
Full audio transcription pipeline test WITH IMPROVED ALIGNMENT.

This version integrates the improved alignment algorithm that:
1. Uses a lower overlap threshold (30% instead of 50%)
2. Falls back to nearest-neighbor when overlap is insufficient
3. Optionally interpolates speakers for small gaps
4. Provides detailed metrics for debugging

This dramatically reduces "Unknown" speaker labels.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pydub import AudioSegment
import torch
import torchaudio
from openai import OpenAI
from pyannote.audio import Pipeline

# Load environment variables
load_dotenv()

# Constants
CHUNK_SIZE_MB = 24  # Stay under 25MB limit
SAMPLE_RATE = 16000  # 16kHz for Whisper
DEBUG_MODE = True

def debug_log(tag, message):
    """Print debug messages with timestamp"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{tag}] {message}")

# ============================================================================
# AUDIO PREPROCESSING
# ============================================================================
def preprocess_audio(input_path: str, output_path: str) -> str:
    """Convert input audio to mono MP3 for processing"""
    debug_log("PREPROCESS", f"Loading audio from {input_path}")

    audio = AudioSegment.from_file(input_path)
    original_duration = len(audio) / 1000.0

    debug_log("PREPROCESS", f"Original: {original_duration:.1f}s, {audio.channels} channels, {audio.frame_rate}Hz")

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(1)
        debug_log("PREPROCESS", "Converted to mono")

    # Export as MP3
    audio.export(output_path, format="mp3", bitrate="128k")
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)

    debug_log("PREPROCESS", f"Saved to {output_path} ({file_size_mb:.1f}MB)")
    return output_path

# ============================================================================
# WHISPER TRANSCRIPTION
# ============================================================================
def transcribe_with_whisper(audio_path: str, api_key: str) -> List[Dict]:
    """Transcribe audio using OpenAI Whisper API with chunking for large files"""
    client = OpenAI(api_key=api_key)

    # Check file size
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    debug_log("WHISPER", f"File size: {file_size_mb:.1f}MB")

    if file_size_mb <= CHUNK_SIZE_MB:
        # Single file transcription
        debug_log("WHISPER", "File under 24MB, transcribing in one piece")
        return transcribe_single_file(client, audio_path)
    else:
        # Need to chunk
        debug_log("WHISPER", f"File over {CHUNK_SIZE_MB}MB, splitting into chunks")
        return transcribe_chunked(client, audio_path)

def transcribe_single_file(client: OpenAI, audio_path: str) -> List[Dict]:
    """Transcribe a single audio file"""
    debug_log("WHISPER", "Starting transcription...")

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    segments = []
    for seg in response.segments:
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })

    debug_log("WHISPER", f"Got {len(segments)} segments")
    return segments

def transcribe_chunked(client: OpenAI, audio_path: str) -> List[Dict]:
    """Transcribe audio in chunks for files over 25MB"""
    audio = AudioSegment.from_file(audio_path)
    total_duration = len(audio)

    # Calculate chunk duration to stay under size limit
    chunk_duration_ms = int((CHUNK_SIZE_MB / (os.path.getsize(audio_path) / (1024 * 1024))) * total_duration)
    chunk_duration_ms = min(chunk_duration_ms, 10 * 60 * 1000)  # Max 10 min chunks

    debug_log("WHISPER", f"Chunk duration: {chunk_duration_ms/1000:.1f}s")

    all_segments = []
    chunk_num = 0
    offset_ms = 0

    while offset_ms < total_duration:
        chunk_num += 1
        chunk_end = min(offset_ms + chunk_duration_ms, total_duration)
        chunk = audio[offset_ms:chunk_end]

        # Save chunk
        chunk_path = f"temp_chunk_{chunk_num}.mp3"
        chunk.export(chunk_path, format="mp3")

        debug_log("WHISPER", f"Transcribing chunk {chunk_num} ({offset_ms/1000:.1f}s - {chunk_end/1000:.1f}s)")

        # Transcribe chunk
        chunk_segments = transcribe_single_file(client, chunk_path)

        # Adjust timestamps and add to results
        for seg in chunk_segments:
            seg["start"] += offset_ms / 1000
            seg["end"] += offset_ms / 1000
            all_segments.append(seg)

        # Cleanup chunk file
        os.remove(chunk_path)

        offset_ms = chunk_end

    debug_log("WHISPER", f"Total segments from all chunks: {len(all_segments)}")
    return all_segments

# ============================================================================
# SPEAKER DIARIZATION
# ============================================================================
def perform_diarization(audio_path: str, hf_token: str) -> List[Dict]:
    """Identify who is speaking when using pyannote"""
    debug_log("DIARIZATION", "Loading diarization model...")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )

    # Load audio as waveform
    debug_log("DIARIZATION", "Loading audio waveform...")
    waveform, sample_rate = torchaudio.load(audio_path)

    audio_dict = {
        "waveform": waveform,
        "sample_rate": sample_rate
    }

    debug_log("DIARIZATION", "Running diarization (this may take a while)...")
    start_time = time.time()

    diarization = pipeline(audio_dict)

    elapsed = time.time() - start_time
    debug_log("DIARIZATION", f"Diarization complete in {elapsed:.1f}s")

    # Convert to list of speaker turns
    turns = []
    for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
        turns.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end
        })

    debug_log("DIARIZATION", f"Found {len(turns)} speaker turns")

    # Show speaker summary
    speaker_times = {}
    for turn in turns:
        duration = turn["end"] - turn["start"]
        speaker_times[turn["speaker"]] = speaker_times.get(turn["speaker"], 0) + duration

    for speaker, total_time in speaker_times.items():
        debug_log("DIARIZATION", f"  {speaker}: {total_time:.1f}s total")

    return turns

# ============================================================================
# IMPROVED ALIGNMENT: Combining Whisper + Diarization
# ============================================================================
def align_speakers_with_segments_improved(
    segments: List[Dict],
    turns: List[Dict],
    overlap_threshold: float = 0.3,
    use_nearest_fallback: bool = True,
    interpolate_gaps: bool = True,
    max_gap_for_interpolation: float = 2.0
) -> Tuple[List[Dict], Dict]:
    """
    Improved alignment algorithm with multiple strategies to reduce Unknown speakers.

    Returns:
        Tuple of (aligned_segments, metrics_dict)
    """
    debug_log("ALIGN", f"Aligning {len(segments)} segments with {len(turns)} speaker turns")
    debug_log("ALIGN", f"Config: threshold={overlap_threshold}, nearest={use_nearest_fallback}, interpolate={interpolate_gaps}")

    aligned = []
    metrics = {
        'total_segments': len(segments),
        'unknown_segments': 0,
        'low_overlap_segments': 0,
        'nearest_neighbor_assigns': 0,
        'interpolated_assigns': 0,
        'unknown_duration': 0.0,
        'total_duration': 0.0
    }

    for seg in segments:
        seg_start, seg_end = seg.get('start', 0), seg.get('end', 0)
        seg_duration = seg_end - seg_start
        metrics['total_duration'] += seg_duration

        # Step 1: Find best overlapping speaker
        best_speaker = "UNKNOWN"
        best_overlap = 0
        best_overlap_pct = 0

        for turn in turns:
            turn_start, turn_end = turn['start'], turn['end']

            # Calculate overlap
            overlap_start = max(seg_start, turn_start)
            overlap_end = min(seg_end, turn_end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_overlap_pct = (overlap / seg_duration) if seg_duration > 0 else 0
                best_speaker = turn['speaker']

        # Step 2: Check if overlap meets threshold
        if best_overlap_pct < overlap_threshold:
            metrics['low_overlap_segments'] += 1

            # Step 3: Try nearest neighbor fallback
            if use_nearest_fallback and seg_duration > 0:
                nearest_speaker, nearest_distance = find_nearest_speaker(seg_start, seg_end, turns)

                if nearest_speaker and nearest_distance < seg_duration:
                    best_speaker = nearest_speaker
                    metrics['nearest_neighbor_assigns'] += 1

            # Step 4: Try interpolation for gaps
            if interpolate_gaps and best_speaker == "UNKNOWN":
                interpolated_speaker = try_interpolation(seg_start, seg_end, turns, max_gap_for_interpolation)

                if interpolated_speaker:
                    best_speaker = interpolated_speaker
                    metrics['interpolated_assigns'] += 1

        # Track Unknown segments
        if best_speaker == "UNKNOWN":
            metrics['unknown_segments'] += 1
            metrics['unknown_duration'] += seg_duration

        # Add aligned segment
        aligned.append({
            "start": seg_start,
            "end": seg_end,
            "text": seg["text"],
            "speaker": best_speaker,
            "overlap_percentage": best_overlap_pct * 100
        })

    # Calculate final metrics
    metrics['unknown_percentage'] = (
        metrics['unknown_segments'] / metrics['total_segments'] * 100
        if metrics['total_segments'] > 0 else 0
    )

    # Stats
    speaker_text_count = {}
    for seg in aligned:
        speaker_text_count[seg["speaker"]] = speaker_text_count.get(seg["speaker"], 0) + 1
    debug_log("ALIGN", f"Segments per speaker: {speaker_text_count}")
    debug_log("ALIGN", f"Unknown segments: {metrics['unknown_segments']} ({metrics['unknown_percentage']:.1f}%)")
    debug_log("ALIGN", f"Nearest neighbor assigns: {metrics['nearest_neighbor_assigns']}")
    debug_log("ALIGN", f"Interpolated assigns: {metrics['interpolated_assigns']}")

    return aligned, metrics

def find_nearest_speaker(seg_start: float, seg_end: float, turns: List[Dict]) -> Tuple[Optional[str], float]:
    """Find the nearest speaker turn to a segment"""
    min_distance = float('inf')
    nearest_speaker = None

    for turn in turns:
        if seg_end < turn['start']:
            distance = turn['start'] - seg_end
        elif seg_start > turn['end']:
            distance = seg_start - turn['end']
        else:
            distance = 0

        if distance < min_distance:
            min_distance = distance
            nearest_speaker = turn['speaker']

    return nearest_speaker, min_distance

def try_interpolation(seg_start: float, seg_end: float, turns: List[Dict], max_gap: float) -> Optional[str]:
    """Try to interpolate speaker for segments in small gaps"""
    turn_before = None
    turn_after = None

    for turn in turns:
        if turn['end'] <= seg_start:
            if not turn_before or turn['end'] > turn_before['end']:
                turn_before = turn
        elif turn['start'] >= seg_end:
            if not turn_after or turn['start'] < turn_after['start']:
                turn_after = turn

    if turn_before and turn_after:
        if turn_before['speaker'] == turn_after['speaker']:
            gap = turn_after['start'] - turn_before['end']
            if gap <= max_gap:
                return turn_before['speaker']

    return None

# ============================================================================
# MAIN PIPELINE
# ============================================================================
def main():
    # Input/output paths - use relative paths from test file location
    script_dir = Path(__file__).parent
    input_audio = script_dir / "samples" / "LIVE Cognitive Behavioral Therapy Session (1).mp3"
    processed_audio = script_dir / "outputs" / "processed_audio.mp3"
    output_json = script_dir / "outputs" / "diarization_output_improved.json"

    # Check input exists
    if not input_audio.exists():
        print(f"❌ Input file not found: {input_audio}")
        print(f"   Expected location: {input_audio.absolute()}")
        print(f"   Please ensure the sample audio file exists at the expected location.")
        sys.exit(1)

    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    hf_token = os.getenv("HF_TOKEN")

    if not openai_key or not hf_token:
        print("❌ Missing API keys in .env file")
        print("   Required: OPENAI_API_KEY, HF_TOKEN")
        sys.exit(1)

    print("="*60)
    print("FULL AUDIO TRANSCRIPTION PIPELINE - IMPROVED VERSION")
    print("="*60)
    print()

    try:
        # Step 1: Preprocess audio
        print("📌 Step 1: Preprocessing audio...")
        processed_audio.parent.mkdir(parents=True, exist_ok=True)
        processed = preprocess_audio(str(input_audio), str(processed_audio))
        print()

        # Step 2: Transcribe with Whisper
        print("📌 Step 2: Transcribing with Whisper...")
        segments = transcribe_with_whisper(processed, openai_key)
        print(f"✅ Got {len(segments)} text segments")
        print()

        # Step 3: Speaker diarization
        print("📌 Step 3: Identifying speakers...")
        speaker_turns = perform_diarization(processed, hf_token)
        print(f"✅ Got {len(speaker_turns)} speaker turns")
        print()

        # Step 4: Align speakers with text (IMPROVED)
        print("📌 Step 4: Aligning speakers with text (IMPROVED)...")
        aligned_segments, alignment_metrics = align_speakers_with_segments_improved(
            segments,
            speaker_turns,
            overlap_threshold=0.3,  # Lower threshold
            use_nearest_fallback=True,  # Use nearest neighbor
            interpolate_gaps=True  # Interpolate small gaps
        )
        print(f"✅ Aligned {len(aligned_segments)} segments")
        print()

        # Print alignment metrics
        print("ALIGNMENT METRICS:")
        print("-" * 40)
        print(f"Total segments: {alignment_metrics['total_segments']}")
        print(f"Unknown segments: {alignment_metrics['unknown_segments']} ({alignment_metrics['unknown_percentage']:.1f}%)")
        print(f"Low overlap segments: {alignment_metrics['low_overlap_segments']}")
        print(f"Nearest neighbor assigns: {alignment_metrics['nearest_neighbor_assigns']}")
        print(f"Interpolated assigns: {alignment_metrics['interpolated_assigns']}")
        print()

        # Step 5: Generate full transcript
        print("📌 Step 5: Generating full transcript...")
        full_text = " ".join([seg["text"] for seg in aligned_segments])
        print(f"✅ Total transcript length: {len(full_text)} characters")
        print()

        # Step 6: Save output
        print("📌 Step 6: Saving results...")

        # Calculate metadata
        audio = AudioSegment.from_file(processed)
        duration_seconds = len(audio) / 1000.0

        output_data = {
            "metadata": {
                "input_file": str(input_audio),
                "processed_file": str(processed_audio),
                "duration": duration_seconds,
                "duration_formatted": str(timedelta(seconds=int(duration_seconds))),
                "total_segments": len(aligned_segments),
                "total_speaker_turns": len(speaker_turns),
                "alignment_config": {
                    "overlap_threshold": 0.3,
                    "use_nearest_fallback": True,
                    "interpolate_gaps": True,
                    "max_gap_for_interpolation": 2.0
                },
                "alignment_metrics": alignment_metrics,
                "timestamp": datetime.now().isoformat()
            },
            "speaker_turns": speaker_turns,
            "diarized_segments": aligned_segments,
            "full_text": full_text
        }

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_json), "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Results saved to: {output_json}")
        print()

        # Step 7: Show sample output
        print("📌 Sample output (first 5 segments):")
        print("-" * 60)
        for seg in aligned_segments[:5]:
            speaker = seg["speaker"]
            text = seg["text"]
            start = seg["start"]
            end = seg["end"]
            overlap = seg.get("overlap_percentage", 0)
            print(f"[{start:.1f}s - {end:.1f}s] {speaker} (overlap: {overlap:.1f}%)")
            print(f"  \"{text}\"")
            print()

        print("="*60)
        print("✅ PIPELINE COMPLETE - IMPROVED VERSION")
        print("="*60)
        print()
        print(f"Output saved to: {output_json}")
        print()
        print("Improvement summary:")
        print(f"- Reduced Unknown segments to {alignment_metrics['unknown_percentage']:.1f}%")
        print(f"- Used nearest-neighbor fallback: {alignment_metrics['nearest_neighbor_assigns']} times")
        print(f"- Used interpolation: {alignment_metrics['interpolated_assigns']} times")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()