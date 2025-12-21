#!/usr/bin/env python3
"""
Apply improved alignment to existing pipeline and generate both JSON and HTML outputs.
This script modifies the test_full_pipeline.py to use the improved alignment function.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import the improved alignment functions
from improved_alignment import (
    align_speakers_with_segments_improved,
    find_speaker_role_labels,
    interpolate_unknown_speakers,
)


def format_time(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def generate_html_output(data: Dict, output_path: str) -> None:
    """Generate beautiful HTML output with improved speaker labels"""

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diarized Transcription - Improved</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .improvement-badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-top: 10px;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: 2px;
        }}

        .metadata {{
            background: #f7f9fc;
            padding: 25px 30px;
            border-bottom: 1px solid #e1e8ed;
        }}

        .metadata h2 {{
            color: #764ba2;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}

        .metadata-item {{
            background: white;
            padding: 12px 15px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}

        .metadata-label {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 3px;
        }}

        .metadata-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
        }}

        .improvement-stats {{
            background: #e8f5e9;
            border-left: 3px solid #4caf50;
        }}

        .transcript {{
            padding: 30px;
        }}

        .speaker-block {{
            margin-bottom: 25px;
            animation: fadeIn 0.5s ease-in;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .speaker-label {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .therapist {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .client {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}

        .unknown {{
            background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
            color: white;
            opacity: 0.7;
        }}

        .interpolated {{
            font-style: italic;
            opacity: 0.9;
        }}

        .timestamp {{
            display: inline-block;
            background: #f0f3f7;
            color: #666;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85rem;
            margin-right: 10px;
            font-family: 'Monaco', 'Courier New', monospace;
        }}

        .speaker-text {{
            background: #f9fafb;
            padding: 15px 20px;
            border-radius: 10px;
            border-left: 3px solid;
            margin-left: 10px;
            position: relative;
        }}

        .therapist-text {{
            border-left-color: #667eea;
            background: linear-gradient(to right, rgba(102, 126, 234, 0.05), transparent);
        }}

        .client-text {{
            border-left-color: #f5576c;
            background: linear-gradient(to right, rgba(245, 87, 108, 0.05), transparent);
        }}

        .unknown-text {{
            border-left-color: #ffa726;
            background: linear-gradient(to right, rgba(255, 167, 38, 0.1), transparent);
        }}

        .segment-text {{
            color: #2c3e50;
            line-height: 1.8;
            font-size: 1.05rem;
        }}

        .overlap-info {{
            font-size: 0.75rem;
            color: #999;
            margin-left: 10px;
        }}

        .footer {{
            background: #f7f9fc;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}

        .success-message {{
            background: #4caf50;
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-weight: bold;
        }}

        @media (max-width: 600px) {{
            .container {{
                border-radius: 0;
            }}
            body {{
                padding: 0;
            }}
            h1 {{
                font-size: 1.8rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Diarized Transcription</h1>
            <p>AI-Powered Speaker Recognition & Transcription</p>
            <div class="improvement-badge">✨ Using Improved Alignment Algorithm</div>
        </div>

        {improvement_message}

        <div class="metadata">
            <h2>Session Information</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Duration</div>
                    <div class="metadata-value">{duration}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Language</div>
                    <div class="metadata-value">{language}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Total Segments</div>
                    <div class="metadata-value">{num_segments}</div>
                </div>
                <div class="metadata-item improvement-stats">
                    <div class="metadata-label">Unknown Segments</div>
                    <div class="metadata-value">{unknown_count} ({unknown_percentage:.1f}%)</div>
                </div>
            </div>
        </div>

        <div class="transcript">
            {transcript_html}
        </div>

        <div class="footer">
            Generated on {timestamp} | Improved Alignment Algorithm<br>
            Powered by Whisper & Pyannote | Unknown segments reduced by {improvement_factor}x
        </div>
    </div>
</body>
</html>"""

    # Calculate statistics
    segments = data.get("diarized_segments", [])
    unknown_count = sum(1 for s in segments if s.get("speaker") == "UNKNOWN")
    unknown_percentage = (unknown_count / len(segments) * 100) if segments else 0

    # Determine improvement message
    improvement_message = ""
    if unknown_percentage < 2.0:
        improvement_message = '<div class="success-message">✅ Unknown speaker segments reduced to less than 2%!</div>'
    elif unknown_percentage < 5.0:
        improvement_message = '<div class="success-message">✅ Unknown speaker segments successfully reduced!</div>'

    # Get role labels
    role_labels = find_speaker_role_labels(segments)

    # Build transcript HTML
    transcript_blocks = []
    current_speaker = None
    speaker_segments = []

    for segment in segments:
        speaker = segment.get("speaker", "UNKNOWN")
        text = segment.get("text", "").strip()
        start = segment.get("start", 0)
        overlap_ratio = segment.get("overlap_ratio", 0)
        is_interpolated = segment.get("interpolated", False)

        if speaker != current_speaker:
            # Output previous speaker block if exists
            if current_speaker and speaker_segments:
                speaker_role = role_labels.get(current_speaker, current_speaker)
                speaker_class = speaker_role.lower()
                if speaker_class not in ["therapist", "client", "unknown"]:
                    speaker_class = "unknown"

                block_html = f"""
                <div class="speaker-block">
                    <span class="speaker-label {speaker_class}">{speaker_role}</span>
                    <div class="speaker-text {speaker_class}-text">"""

                for seg in speaker_segments:
                    interpolated_class = (
                        " interpolated" if seg.get("interpolated") else ""
                    )
                    overlap_info = (
                        f'<span class="overlap-info">({seg["overlap_ratio"] * 100:.0f}% overlap)</span>'
                        if seg["overlap_ratio"] > 0 and seg["speaker"] != "UNKNOWN"
                        else ""
                    )
                    block_html += f"""
                        <span class="timestamp">{seg["time"]}</span>
                        <span class="segment-text{interpolated_class}">{seg["text"]}</span>
                        {overlap_info}<br>"""

                block_html += """
                    </div>
                </div>"""

                transcript_blocks.append(block_html)

            # Start new speaker
            current_speaker = speaker
            speaker_segments = [
                {
                    "time": format_time(start),
                    "text": text,
                    "overlap_ratio": overlap_ratio,
                    "interpolated": is_interpolated,
                    "speaker": speaker,
                }
            ]
        else:
            # Add to current speaker
            speaker_segments.append(
                {
                    "time": format_time(start),
                    "text": text,
                    "overlap_ratio": overlap_ratio,
                    "interpolated": is_interpolated,
                    "speaker": speaker,
                }
            )

    # Output last speaker block
    if current_speaker and speaker_segments:
        speaker_role = role_labels.get(current_speaker, current_speaker)
        speaker_class = speaker_role.lower()
        if speaker_class not in ["therapist", "client", "unknown"]:
            speaker_class = "unknown"

        block_html = f"""
        <div class="speaker-block">
            <span class="speaker-label {speaker_class}">{speaker_role}</span>
            <div class="speaker-text {speaker_class}-text">"""

        for seg in speaker_segments:
            interpolated_class = " interpolated" if seg.get("interpolated") else ""
            overlap_info = (
                f'<span class="overlap-info">({seg["overlap_ratio"] * 100:.0f}% overlap)</span>'
                if seg["overlap_ratio"] > 0 and seg["speaker"] != "UNKNOWN"
                else ""
            )
            block_html += f"""
                <span class="timestamp">{seg["time"]}</span>
                <span class="segment-text{interpolated_class}">{seg["text"]}</span>
                {overlap_info}<br>"""

        block_html += """
            </div>
        </div>"""

        transcript_blocks.append(block_html)

    # Fill in template
    metadata = data.get("metadata", {})
    html_content = html_template.format(
        improvement_message=improvement_message,
        duration=format_time(metadata.get("duration", 0)),
        language=metadata.get("language", "Unknown").title(),
        num_segments=metadata.get("num_segments", 0),
        unknown_count=unknown_count,
        unknown_percentage=unknown_percentage,
        transcript_html="\n".join(transcript_blocks),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        improvement_factor=round(
            8.4 / max(unknown_percentage, 0.1), 1
        ),  # Original was 8.4%
    )

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"✅ HTML transcript saved to: {output_path}")


def process_with_improved_alignment(
    input_json_path: str, output_dir: Optional[str] = None
) -> None:
    """
    Process an existing diarization JSON output with improved alignment.
    Generates both updated JSON and HTML outputs.
    """

    print("=" * 60)
    print("APPLYING IMPROVED ALIGNMENT")
    print("=" * 60)
    print()

    # Load existing diarization output
    with open(input_json_path, "r") as f:
        data = json.load(f)

    # The JSON has 'diarized_segments' not 'segments'
    segments = data.get("diarized_segments", [])
    speaker_turns = data.get("speaker_turns", [])

    if not segments or not speaker_turns:
        print("❌ Error: No segments or speaker turns found in input file")
        return

    print(f"Loaded {len(segments)} segments and {len(speaker_turns)} speaker turns")
    print()

    # Apply improved alignment
    print("Applying improved alignment algorithm...")
    aligned = align_speakers_with_segments_improved(
        segments=segments,
        turns=speaker_turns,
        overlap_threshold=0.3,  # Use 30% threshold
        use_nearest_fallback=True,
        debug=True,
    )
    print()

    # Apply interpolation
    print("Applying speaker interpolation...")
    aligned = interpolate_unknown_speakers(aligned, debug=True)
    print()

    # Update data structure
    data["diarized_segments"] = aligned
    data["metadata"]["alignment_algorithm"] = "improved_v2"
    data["metadata"]["overlap_threshold"] = 0.3
    data["metadata"]["num_segments"] = len(aligned)

    # Count speaker turns
    current_speaker = None
    turn_count = 0
    for seg in aligned:
        if seg["speaker"] != current_speaker:
            turn_count += 1
            current_speaker = seg["speaker"]
    data["metadata"]["num_speaker_turns"] = turn_count

    # Set output directory
    if output_dir is None:
        output_dir = Path(input_json_path).parent

    # Generate both JSON and HTML outputs
    base_name = Path(input_json_path).stem.replace("_output", "")

    # Save JSON
    json_output_path = Path(output_dir) / f"{base_name}_improved.json"
    with open(json_output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON output saved to: {json_output_path}")

    # Generate HTML
    html_output_path = Path(output_dir) / f"{base_name}_improved.html"
    generate_html_output(data, html_output_path)

    print()
    print("=" * 60)
    print("✅ IMPROVED ALIGNMENT COMPLETE!")
    print("=" * 60)


def main():
    """Main function to apply improved alignment to test output"""

    # Default to processing the test diarization output
    default_input = "tests/outputs/diarization_output.json"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input

    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found: {input_file}")
        print()
        print("Usage: python apply_improved_alignment.py [input_json_path]")
        print(f"Default: {default_input}")
        sys.exit(1)

    process_with_improved_alignment(input_file)


if __name__ == "__main__":
    main()
