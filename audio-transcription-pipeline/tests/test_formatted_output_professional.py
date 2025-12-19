#!/usr/bin/env python3
"""
Professional formatted output generation for diarized transcriptions.
Uses a clean, professional color scheme without gradients.

Color scheme:
- Therapist (SPEAKER_00): Professional teal/turquoise
- Client (SPEAKER_01): Warm orange/amber
- Unknown: Neutral gray
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Terminal color codes for terminal output
BOLD = '\033[1m'
TEAL = '\033[36m'      # Professional teal for Therapist
ORANGE = '\033[33m'    # Warm amber for Client
GRAY = '\033[90m'      # Gray for unknown
RESET = '\033[0m'

def generate_html_output(data: Dict, output_path: str) -> None:
    """
    Generate a professional HTML file from diarized transcription data.
    Uses a clean, modern design with solid colors (no gradients).
    """

    # Extract metadata with proper field names and fallbacks
    metadata = data.get('metadata', {})

    # Handle both field name variants and provide sensible defaults
    duration = metadata.get('duration_formatted')
    if not duration and metadata.get('duration'):
        # Convert seconds to formatted string if needed
        duration_seconds = metadata.get('duration', 0)
        duration = str(timedelta(seconds=int(duration_seconds)))
    elif not duration:
        duration = 'Unknown'

    # Use actual field names from the JSON
    num_segments = metadata.get('total_segments', metadata.get('num_segments', 0))
    num_speaker_turns = metadata.get('total_speaker_turns', metadata.get('num_speaker_turns', 0))

    # Handle language field variations
    language = metadata.get('language', 'english')
    language = language.capitalize() if language else 'English'

    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    # HTML template with professional styling
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcription - {title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #f8f9fa;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
        }}

        .header {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            border-bottom: 4px solid #1abc9c;
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .metadata {{
            padding: 30px;
            background: #fafbfc;
            border-bottom: 1px solid #e1e4e8;
        }}

        .metadata h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .metadata-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e1e4e8;
        }}

        .metadata-label {{
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .metadata-value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
        }}

        .transcript {{
            padding: 30px;
        }}

        .speaker-block {{
            margin-bottom: 25px;
            animation: fadeIn 0.3s ease-in;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .speaker-label {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        /* Professional color scheme - no gradients */
        .speaker-00 {{
            background: #1abc9c;  /* Teal/turquoise */
            color: white;
        }}

        .speaker-01 {{
            background: #e67e22;  /* Orange/amber */
            color: white;
        }}

        .speaker-unknown {{
            background: #95a5a6;  /* Gray */
            color: white;
        }}

        .speaker-text {{
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid;
            background: #fafbfc;
            position: relative;
            transition: all 0.2s ease;
        }}

        .speaker-text:hover {{
            background: #f3f4f6;
            transform: translateX(2px);
        }}

        .speaker-00-text {{
            border-left-color: #1abc9c;
            background: #f0fdf9;
        }}

        .speaker-01-text {{
            border-left-color: #e67e22;
            background: #fef5e7;
        }}

        .speaker-unknown-text {{
            border-left-color: #95a5a6;
            background: #f8f9fa;
        }}

        .timestamp {{
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 8px;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
        }}

        .footer {{
            background: #fafbfc;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
            border-top: 1px solid #e1e4e8;
        }}

        /* Professional typography */
        h1, h2, h3 {{
            line-height: 1.2;
        }}

        p {{
            line-height: 1.8;
        }}

        @media (max-width: 600px) {{
            .container {{
                border-radius: 0;
            }}
            body {{
                padding: 0;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
            .metadata-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Transcription Analysis</h1>
            <p>AI-Powered Speaker Recognition & Transcription</p>
        </div>

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
                    <div class="metadata-label">Segments</div>
                    <div class="metadata-value">{num_segments}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Speaker Turns</div>
                    <div class="metadata-value">{num_speaker_turns}</div>
                </div>
            </div>
        </div>

        <div class="transcript">
            {transcript_html}
        </div>

        <div class="footer">
            Generated on {timestamp} | Powered by Whisper & Pyannote
        </div>
    </div>
</body>
</html>"""

    # Build transcript HTML
    transcript_blocks = []
    segments = data.get('diarized_segments', [])

    current_speaker = None
    speaker_segments = []

    for segment in segments:
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()
        start = segment.get('start', 0)

        if speaker != current_speaker:
            # Output previous speaker block if exists
            if current_speaker and speaker_segments:
                speaker_class = current_speaker.lower().replace('_', '-')
                speaker_display = current_speaker.replace('SPEAKER_00', 'Therapist').replace('SPEAKER_01', 'Client').replace('UNKNOWN', 'Unknown')

                block_html = f'''
                <div class="speaker-block">
                    <span class="speaker-label {speaker_class}">{speaker_display}</span>
                '''

                for seg_text, seg_start in speaker_segments:
                    timestamp = format_timestamp(seg_start)
                    block_html += f'''
                    <div class="speaker-text {speaker_class}-text">
                        <div class="timestamp">[{timestamp}]</div>
                        <p>{seg_text}</p>
                    </div>
                    '''

                block_html += '</div>'
                transcript_blocks.append(block_html)

            # Reset for new speaker
            current_speaker = speaker
            speaker_segments = []

        speaker_segments.append((text, start))

    # Don't forget the last speaker block
    if current_speaker and speaker_segments:
        speaker_class = current_speaker.lower().replace('_', '-')
        speaker_display = current_speaker.replace('SPEAKER_00', 'Therapist').replace('SPEAKER_01', 'Client').replace('UNKNOWN', 'Unknown')

        block_html = f'''
        <div class="speaker-block">
            <span class="speaker-label {speaker_class}">{speaker_display}</span>
        '''

        for seg_text, seg_start in speaker_segments:
            timestamp = format_timestamp(seg_start)
            block_html += f'''
            <div class="speaker-text {speaker_class}-text">
                <div class="timestamp">[{timestamp}]</div>
                <p>{seg_text}</p>
            </div>
            '''

        block_html += '</div>'
        transcript_blocks.append(block_html)

    # Fill in template
    html_content = html_template.format(
        title=Path(metadata.get('input_file', 'Unknown')).stem,
        duration=duration,
        language=language,
        num_segments=num_segments,
        num_speaker_turns=num_speaker_turns,
        transcript_html='\n'.join(transcript_blocks),
        timestamp=timestamp
    )

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML output saved to: {output_path}")

def consolidate_segments_by_speaker(segments: List[Dict]) -> List[Dict]:
    """
    Consolidate consecutive segments from the same speaker into single blocks.
    Returns list of speaker blocks with combined text.
    """
    if not segments:
        return []

    consolidated = []
    current_block = {
        'speaker': segments[0].get('speaker', 'UNKNOWN'),
        'start': segments[0].get('start', 0),
        'end': segments[0].get('end', 0),
        'text': segments[0].get('text', '').strip(),
        'segment_count': 1
    }

    for segment in segments[1:]:
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()

        if speaker == current_block['speaker']:
            # Same speaker - extend the current block
            current_block['text'] += ' ' + text
            current_block['end'] = segment.get('end', current_block['end'])
            current_block['segment_count'] += 1
        else:
            # Different speaker - save current block and start new one
            consolidated.append(current_block)
            current_block = {
                'speaker': speaker,
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': text,
                'segment_count': 1
            }

    # Don't forget the last block
    if current_block:
        consolidated.append(current_block)

    return consolidated

def generate_speaker_only_json(data: Dict, output_path: str) -> Dict:
    """
    Generate JSON with timestamps only at speaker changes.
    Creates a cleaner, more readable format.
    """
    segments = data.get('diarized_segments', [])
    consolidated = consolidate_segments_by_speaker(segments)

    # Build new structure
    speaker_only_data = {
        'metadata': {
            **data.get('metadata', {}),
            'format': 'speaker_changes_only',
            'total_speaker_blocks': len(consolidated),
            'original_segments': len(segments)
        },
        'speaker_blocks': consolidated,
        'full_text': data.get('full_text', '')
    }

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(speaker_only_data, f, indent=2)

    print(f"✅ Speaker-only JSON saved to: {output_path}")
    return speaker_only_data

def generate_speaker_only_html(data: Dict, output_path: str) -> None:
    """
    Generate HTML with timestamps only at speaker changes.
    Uses consolidated speaker blocks for cleaner output.
    """
    # First consolidate the segments
    segments = data.get('diarized_segments', [])
    speaker_blocks = consolidate_segments_by_speaker(segments)

    # Extract metadata with proper field names and fallbacks
    metadata = data.get('metadata', {})

    # Handle both field name variants and provide sensible defaults
    duration = metadata.get('duration_formatted')
    if not duration and metadata.get('duration'):
        # Convert seconds to formatted string if needed
        duration_seconds = metadata.get('duration', 0)
        duration = str(timedelta(seconds=int(duration_seconds)))
    elif not duration:
        duration = 'Unknown'

    # Use actual field names from the JSON
    num_segments = metadata.get('total_segments', metadata.get('num_segments', 0))
    num_speaker_turns = metadata.get('total_speaker_turns', metadata.get('num_speaker_turns', 0))

    # Handle language field variations
    language = metadata.get('language', 'english')
    language = language.capitalize() if language else 'English'

    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    # HTML template with professional styling (reusing existing template)
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcription (Speaker Changes Only) - {title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #f8f9fa;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
        }}

        .header {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            border-bottom: 4px solid #1abc9c;
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .format-badge {{
            display: inline-block;
            background: #e67e22;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            margin-top: 10px;
            font-weight: 600;
        }}

        .metadata {{
            padding: 30px;
            background: #fafbfc;
            border-bottom: 1px solid #e1e4e8;
        }}

        .metadata h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .metadata-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e1e4e8;
        }}

        .metadata-label {{
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .metadata-value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
        }}

        .transcript {{
            padding: 30px;
        }}

        .speaker-block {{
            margin-bottom: 25px;
            animation: fadeIn 0.3s ease-in;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .speaker-label {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        /* Professional color scheme - no gradients */
        .speaker-00 {{
            background: #1abc9c;  /* Teal/turquoise */
            color: white;
        }}

        .speaker-01 {{
            background: #e67e22;  /* Orange/amber */
            color: white;
        }}

        .speaker-unknown {{
            background: #95a5a6;  /* Gray */
            color: white;
        }}

        .speaker-text {{
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid;
            background: #fafbfc;
            position: relative;
            transition: all 0.2s ease;
        }}

        .speaker-text:hover {{
            background: #f3f4f6;
            transform: translateX(2px);
        }}

        .speaker-00-text {{
            border-left-color: #1abc9c;
            background: #f0fdf9;
        }}

        .speaker-01-text {{
            border-left-color: #e67e22;
            background: #fef5e7;
        }}

        .speaker-unknown-text {{
            border-left-color: #95a5a6;
            background: #f8f9fa;
        }}

        .timestamp {{
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 8px;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
        }}

        .segment-info {{
            font-size: 0.7rem;
            color: #95a5a6;
            font-style: italic;
        }}

        .footer {{
            background: #fafbfc;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
            border-top: 1px solid #e1e4e8;
        }}

        /* Professional typography */
        h1, h2, h3 {{
            line-height: 1.2;
        }}

        p {{
            line-height: 1.8;
        }}

        @media (max-width: 600px) {{
            .container {{
                border-radius: 0;
            }}
            body {{
                padding: 0;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
            .metadata-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Transcription Analysis</h1>
            <p>AI-Powered Speaker Recognition & Transcription</p>
            <span class="format-badge">Speaker Changes Only</span>
        </div>

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
                    <div class="metadata-label">Speaker Blocks</div>
                    <div class="metadata-value">{num_blocks}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Original Segments</div>
                    <div class="metadata-value">{num_segments}</div>
                </div>
            </div>
        </div>

        <div class="transcript">
            {transcript_html}
        </div>

        <div class="footer">
            Generated on {timestamp} | Powered by Whisper & Pyannote | Speaker Changes Format
        </div>
    </div>
</body>
</html>"""

    # Build transcript HTML with consolidated blocks
    transcript_blocks = []

    for block in speaker_blocks:
        speaker = block['speaker']
        text = block['text']
        start = block['start']
        segment_count = block.get('segment_count', 1)

        speaker_class = speaker.lower().replace('_', '-')
        speaker_display = (speaker.replace('SPEAKER_00', 'Therapist')
                                 .replace('SPEAKER_01', 'Client')
                                 .replace('UNKNOWN', 'Unknown'))

        timestamp_str = format_timestamp(start)

        block_html = f'''
        <div class="speaker-block">
            <span class="speaker-label {speaker_class}">{speaker_display}</span>
            <div class="speaker-text {speaker_class}-text">
                <div class="timestamp">[{timestamp_str}] <span class="segment-info">({segment_count} segments consolidated)</span></div>
                <p>{text}</p>
            </div>
        </div>
        '''
        transcript_blocks.append(block_html)

    # Fill in template
    html_content = html_template.format(
        title=Path(metadata.get('input_file', metadata.get('source_file', 'Unknown'))).stem,
        duration=duration,
        language=language,
        num_blocks=len(speaker_blocks),
        num_segments=num_segments,
        transcript_html='\n'.join(transcript_blocks),
        timestamp=timestamp
    )

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Speaker-only HTML saved to: {output_path}")

def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def print_terminal_output(data: Dict) -> None:
    """Print formatted output to terminal"""
    segments = data.get('diarized_segments', [])

    print("\n" + "="*60)
    print("TRANSCRIPTION OUTPUT (Professional Colors)")
    print("="*60)

    for segment in segments[:50]:  # Show first 50 segments in terminal
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()
        start = segment.get('start', 0)
        end = segment.get('end', 0)

        # Choose color based on speaker
        if 'SPEAKER_00' in speaker:
            speaker_color = TEAL
            speaker_display = "Therapist"
        elif 'SPEAKER_01' in speaker:
            speaker_color = ORANGE
            speaker_display = "Client"
        else:
            speaker_color = GRAY
            speaker_display = "Unknown"

        # Format timestamp
        timestamp = format_timestamp(start)

        print(f"\n{BOLD}{speaker_color}[{timestamp}] {speaker_display}{RESET}")
        print(f"  {text}")

    if len(segments) > 50:
        print(f"\n... and {len(segments) - 50} more segments")

    print("\n" + "="*60)

def validate_json_data(json_path: str) -> Dict:
    """Validate and load JSON data with proper error handling"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Ensure required fields exist
        if 'metadata' not in data:
            print("⚠️  Warning: No metadata found in JSON, using defaults")
            data['metadata'] = {}

        if 'diarized_segments' not in data:
            print("❌ Error: No diarized_segments found in JSON")
            return None

        return data
    except FileNotFoundError:
        print(f"❌ File not found: {json_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None

def parse_args():
    """Parse command-line arguments"""
    # Default output dir relative to script location
    script_dir = Path(__file__).parent
    default_output_dir = script_dir / "outputs"

    parser = argparse.ArgumentParser(
        description='Generate formatted outputs from diarization results'
    )
    parser.add_argument(
        '--format',
        choices=['all', 'standard', 'speaker-only'],
        default='all',
        help='Output format to generate (default: all)'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to input JSON file (auto-detect if not specified)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(default_output_dir),
        help='Directory for output files (default: tests/outputs)'
    )
    return parser.parse_args()

def main():
    """Main function to test formatted output generation"""

    # Parse command-line arguments
    args = parse_args()

    # Determine input file
    script_dir = Path(__file__).parent
    if args.input:
        json_path = Path(args.input)
        if not json_path.exists():
            print(f"❌ Specified input file not found: {json_path}")
            print(f"   Expected location: {json_path.absolute()}")
            sys.exit(1)
    else:
        # Check for input files in priority order
        json_paths = [
            script_dir / "outputs" / "diarization_output_improved.json",
            script_dir / "outputs" / "diarization_output.json"
        ]

        json_path = None
        for path in json_paths:
            if path.exists():
                json_path = path
                break

        if not json_path:
            print("❌ No diarization output found")
            print("   Checked locations:")
            for path in json_paths:
                print(f"     - {path.absolute()}")
            print("   Please run the transcription pipeline first:")
            print("   python tests/test_full_pipeline_improved.py")
            sys.exit(1)

    print(f"Loading diarization data from: {json_path}")

    # Validate and load data
    data = validate_json_data(str(json_path))
    if not data:
        sys.exit(1)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate outputs based on format selection
    print("\nGenerating formatted outputs...")

    outputs_generated = []

    # 1. Terminal output (always shown for context)
    if args.format in ['all', 'standard']:
        print_terminal_output(data)

    # 2. Standard HTML output (all timestamps)
    if args.format in ['all', 'standard']:
        html_path = output_dir / "transcription_professional.html"
        generate_html_output(data, str(html_path))
        outputs_generated.append(('Standard HTML', str(html_path)))

    # 3. Speaker-only outputs
    if args.format in ['all', 'speaker-only']:
        # Speaker-only JSON output
        speaker_json_path = output_dir / "speaker_only_output.json"
        speaker_data = generate_speaker_only_json(data, str(speaker_json_path))
        outputs_generated.append(('Speaker-only JSON', str(speaker_json_path)))

        # Speaker-only HTML output
        speaker_html_path = output_dir / "transcription_speaker_only.html"
        generate_speaker_only_html(data, str(speaker_html_path))
        outputs_generated.append(('Speaker-only HTML', str(speaker_html_path)))

        # Generate statistics for speaker-only format
        if args.format == 'all' or args.format == 'speaker-only':
            print("\n📊 Output Statistics:")
            print(f"   Original segments: {len(data.get('diarized_segments', []))}")
            print(f"   Consolidated blocks: {len(speaker_data.get('speaker_blocks', []))}")

            orig_count = len(data.get('diarized_segments', []))
            cons_count = len(speaker_data.get('speaker_blocks', []))
            if orig_count > 0:
                reduction = (1 - cons_count / orig_count) * 100
                print(f"   Reduction: {reduction:.1f}%")

    # Final summary
    print("\n✅ All outputs generated successfully!")
    for output_type, output_path in outputs_generated:
        print(f"   {output_type}: {output_path}")

    if args.format in ['all', 'standard', 'speaker-only'] and len(outputs_generated) > 1:
        print("\nOpen the HTML files in your browser to compare the formats.")

if __name__ == "__main__":
    main()