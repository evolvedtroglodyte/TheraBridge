#!/usr/bin/env python3
"""
Main processing script that applies improved alignment and generates all output formats.
This ensures HTML output is ALWAYS generated when processing transcriptions.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add tests directory to path for imports
sys.path.insert(0, 'tests')

def process_transcription(input_json: str = None, auto_generate_html: bool = True) -> dict:
    """
    Process transcription data with improved alignment and generate all outputs.

    Args:
        input_json: Path to input JSON file (auto-detect if None)
        auto_generate_html: Always generate HTML outputs (default: True)

    Returns:
        Dictionary with paths to all generated outputs
    """

    # Determine input file
    if input_json and os.path.exists(input_json):
        json_path = input_json
    else:
        # Check for existing outputs in priority order
        possible_paths = [
            "tests/outputs/diarization_output.json",
            "tests/outputs/transcription_output.json"
        ]

        json_path = None
        for path in possible_paths:
            if os.path.exists(path):
                json_path = path
                print(f"Found existing output: {json_path}")
                break

        if not json_path:
            print("❌ No transcription output found to process")
            print("   Please run the transcription pipeline first")
            return None

    print("="*60)
    print("PROCESSING TRANSCRIPTION WITH IMPROVED ALIGNMENT")
    print("="*60)
    print()

    # Load the data
    print(f"Loading data from: {json_path}")
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Apply improved alignment
    from improved_alignment import align_speakers_with_segments_improved

    # Extract segments and speaker turns
    segments = []
    for seg in data.get('diarized_segments', []):
        segments.append({
            'text': seg.get('text', ''),
            'start': seg.get('start', 0),
            'end': seg.get('end', 0)
        })

    speaker_turns = data.get('speaker_turns', [])

    print(f"Processing {len(segments)} segments with {len(speaker_turns)} speaker turns")

    # Apply improved alignment with better parameters
    aligned_segments = align_speakers_with_segments_improved(
        segments,
        speaker_turns,
        overlap_threshold=0.3,  # Lower threshold
        use_nearest_fallback=True,  # Use fallback
        debug=False  # Quiet mode
    )

    # Update the data with improved alignment
    improved_data = {
        **data,
        'diarized_segments': aligned_segments,
        'alignment_config': {
            'method': 'improved',
            'overlap_threshold': 0.3,
            'use_nearest_fallback': True,
            'timestamp': datetime.now().isoformat()
        }
    }

    # Save improved JSON
    output_dir = "tests/outputs"
    os.makedirs(output_dir, exist_ok=True)

    improved_json_path = os.path.join(output_dir, "diarization_output_improved.json")
    with open(improved_json_path, 'w') as f:
        json.dump(improved_data, f, indent=2)

    print(f"✅ Saved improved alignment to: {improved_json_path}")

    outputs = {'json': improved_json_path}

    # ALWAYS generate HTML outputs
    if auto_generate_html:
        print()
        print("Generating HTML outputs (automatic)...")
        print("-"*40)

        try:
            from test_formatted_output_professional import (
                generate_html_output,
                generate_speaker_only_html,
                generate_speaker_only_json
            )

            # Generate standard HTML with all timestamps
            html_path = os.path.join(output_dir, "transcription_professional.html")
            generate_html_output(improved_data, html_path)
            outputs['html_standard'] = html_path

            # Generate speaker-only HTML (cleaner version)
            speaker_html_path = os.path.join(output_dir, "transcription_speaker_only.html")
            generate_speaker_only_html(improved_data, speaker_html_path)
            outputs['html_speaker_only'] = speaker_html_path

            # Generate speaker-only JSON
            speaker_json_path = os.path.join(output_dir, "speaker_only_output.json")
            speaker_data = generate_speaker_only_json(improved_data, speaker_json_path)
            outputs['json_speaker_only'] = speaker_json_path

            # Calculate statistics
            original_segments = len(data.get('diarized_segments', []))
            consolidated_blocks = len(speaker_data.get('speaker_blocks', []))
            reduction = (1 - consolidated_blocks / original_segments) * 100 if original_segments > 0 else 0

            print()
            print("📊 Output Statistics:")
            print(f"   Original segments: {original_segments}")
            print(f"   Consolidated speaker blocks: {consolidated_blocks}")
            print(f"   Reduction: {reduction:.1f}%")

        except ImportError as e:
            print(f"⚠️  Warning: Could not import HTML generation module: {e}")
            print("   Skipping HTML generation")
        except Exception as e:
            print(f"⚠️  Error generating HTML: {e}")
            print("   Continuing without HTML output")

    # Print summary
    print()
    print("="*60)
    print("✅ PROCESSING COMPLETE")
    print("="*60)
    print()
    print("Generated outputs:")
    for output_type, path in outputs.items():
        print(f"  • {output_type}: {path}")

    if 'html_standard' in outputs:
        print()
        print("📌 Professional HTML Color Scheme:")
        print("  • Therapist: Teal (#1abc9c)")
        print("  • Client: Orange (#e67e22)")
        print("  • Unknown: Gray (#95a5a6)")
        print()
        print("Open the HTML files in your browser to view the formatted transcription.")

    return outputs


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Process transcription with improved alignment and generate all outputs'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to input JSON file (auto-detect if not specified)'
    )
    parser.add_argument(
        '--no-html',
        action='store_true',
        help='Skip HTML generation (not recommended)'
    )

    args = parser.parse_args()

    # Process with HTML generation enabled by default
    outputs = process_transcription(
        input_json=args.input,
        auto_generate_html=not args.no_html
    )

    if not outputs:
        sys.exit(1)

    # Try to open in browser (macOS)
    if 'html_standard' in outputs and sys.platform == 'darwin':
        import subprocess
        try:
            subprocess.run(['open', outputs['html_standard']], check=False)
            print("\n✅ Opened HTML in browser")
        except:
            pass


if __name__ == "__main__":
    main()