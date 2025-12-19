#!/usr/bin/env python3
"""
Test script that generates beautifully formatted diarized transcription output.
Creates both HTML and Markdown versions for easy viewing.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def load_diarization_output(json_path):
    """Load the diarization JSON output"""
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_markdown(data, output_path):
    """Generate a clean Markdown formatted transcript"""
    md_lines = []

    # Header
    md_lines.append("# Diarized Transcription")
    md_lines.append("")

    # Metadata
    metadata = data.get('metadata', {})
    md_lines.append("## Session Information")
    md_lines.append(f"- **Source:** {metadata.get('source_file', 'Unknown')}")
    md_lines.append(f"- **Duration:** {format_time(metadata.get('duration', 0))} ({metadata.get('duration', 0):.1f} seconds)")
    md_lines.append(f"- **Language:** {metadata.get('language', 'Unknown')}")
    md_lines.append(f"- **Total Segments:** {metadata.get('num_segments', 0)}")
    md_lines.append(f"- **Speaker Turns:** {metadata.get('num_speaker_turns', 0)}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Transcript
    md_lines.append("## Transcript")
    md_lines.append("")

    segments = data.get('diarized_segments', [])

    if not segments:
        md_lines.append("*No segments found*")
    else:
        current_speaker = None
        speaker_text = []

        for segment in segments:
            speaker = segment.get('speaker', 'UNKNOWN')
            text = segment.get('text', '').strip()
            start = segment.get('start', 0)

            # If speaker changes, output the accumulated text
            if speaker != current_speaker:
                if current_speaker and speaker_text:
                    # Output the previous speaker's text
                    md_lines.append(f"### {current_speaker.replace('SPEAKER_', 'Speaker ')}")
                    md_lines.append("")
                    md_lines.append(" ".join(speaker_text))
                    md_lines.append("")

                # Start new speaker
                current_speaker = speaker
                speaker_text = [f"*[{format_time(start)}]*", text]
            else:
                # Continue with same speaker
                speaker_text.append(text)

        # Output the last speaker's text
        if current_speaker and speaker_text:
            md_lines.append(f"### {current_speaker.replace('SPEAKER_', 'Speaker ')}")
            md_lines.append("")
            md_lines.append(" ".join(speaker_text))
            md_lines.append("")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(md_lines))

    print(f"✅ Markdown transcript saved to: {output_path}")

def generate_html(data, output_path):
    """Generate a beautifully styled HTML transcript"""

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diarized Transcription</title>
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

        .speaker-00 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .speaker-01 {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}

        .speaker-unknown {{
            background: linear-gradient(135deg, #a8a8a8 0%, #686868 100%);
            color: white;
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

        .speaker-00-text {{
            border-left-color: #667eea;
            background: linear-gradient(to right, rgba(102, 126, 234, 0.05), transparent);
        }}

        .speaker-01-text {{
            border-left-color: #f5576c;
            background: linear-gradient(to right, rgba(245, 87, 108, 0.05), transparent);
        }}

        .speaker-unknown-text {{
            border-left-color: #a8a8a8;
            background: linear-gradient(to right, rgba(168, 168, 168, 0.05), transparent);
        }}

        .segment-text {{
            color: #2c3e50;
            line-height: 1.8;
            font-size: 1.05rem;
        }}

        .footer {{
            background: #f7f9fc;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
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
                    <div class="speaker-text {speaker_class}-text">'''

                for seg in speaker_segments:
                    block_html += f'''
                        <span class="timestamp">{seg['time']}</span>
                        <span class="segment-text">{seg['text']}</span><br>'''

                block_html += '''
                    </div>
                </div>'''

                transcript_blocks.append(block_html)

            # Start new speaker
            current_speaker = speaker
            speaker_segments = [{'time': format_time(start), 'text': text}]
        else:
            # Add to current speaker
            speaker_segments.append({'time': format_time(start), 'text': text})

    # Output last speaker block
    if current_speaker and speaker_segments:
        speaker_class = current_speaker.lower().replace('_', '-')
        speaker_display = current_speaker.replace('SPEAKER_00', 'Therapist').replace('SPEAKER_01', 'Client').replace('UNKNOWN', 'Unknown')

        block_html = f'''
        <div class="speaker-block">
            <span class="speaker-label {speaker_class}">{speaker_display}</span>
            <div class="speaker-text {speaker_class}-text">'''

        for seg in speaker_segments:
            block_html += f'''
                <span class="timestamp">{seg['time']}</span>
                <span class="segment-text">{seg['text']}</span><br>'''

        block_html += '''
            </div>
        </div>'''

        transcript_blocks.append(block_html)

    # Fill in template
    metadata = data.get('metadata', {})
    html_content = html_template.format(
        duration=format_time(metadata.get('duration', 0)),
        language=metadata.get('language', 'Unknown').title(),
        num_segments=metadata.get('num_segments', 0),
        num_speaker_turns=metadata.get('num_speaker_turns', 0),
        transcript_html='\n'.join(transcript_blocks),
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # Write to file
    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"✅ HTML transcript saved to: {output_path}")

def generate_terminal_output(data):
    """Generate a colored terminal output for immediate viewing"""
    # ANSI color codes
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    print(f"\n{BOLD}{PURPLE}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}         DIARIZED TRANSCRIPTION OUTPUT{RESET}")
    print(f"{BOLD}{PURPLE}{'='*60}{RESET}\n")

    # Metadata
    metadata = data.get('metadata', {})
    print(f"{BOLD}📊 Session Information:{RESET}")
    print(f"  • Duration: {GREEN}{format_time(metadata.get('duration', 0))}{RESET}")
    print(f"  • Language: {GREEN}{metadata.get('language', 'Unknown').title()}{RESET}")
    print(f"  • Segments: {GREEN}{metadata.get('num_segments', 0)}{RESET}")
    print(f"  • Speaker Turns: {GREEN}{metadata.get('num_speaker_turns', 0)}{RESET}")
    print(f"\n{PURPLE}{'─'*60}{RESET}\n")

    # Transcript
    print(f"{BOLD}📝 Transcript:{RESET}\n")

    segments = data.get('diarized_segments', [])
    current_speaker = None

    for segment in segments[:50]:  # Show first 50 segments in terminal
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()
        start = segment.get('start', 0)

        if speaker != current_speaker:
            current_speaker = speaker

            if speaker == 'SPEAKER_00':
                speaker_color = CYAN
                speaker_display = "THERAPIST"
            elif speaker == 'SPEAKER_01':
                speaker_color = YELLOW
                speaker_display = "CLIENT"
            else:
                speaker_color = GRAY
                speaker_display = "UNKNOWN"

            print(f"\n{BOLD}{speaker_color}[{speaker_display}]{RESET}")

        print(f"  {GRAY}{format_time(start):>6}{RESET}  {text}")

    if len(segments) > 50:
        print(f"\n{GRAY}... and {len(segments) - 50} more segments{RESET}")

    print(f"\n{PURPLE}{'='*60}{RESET}\n")

def main():
    # Default path relative to script location
    script_dir = Path(__file__).parent
    default_input = script_dir / "outputs" / "diarization_output.json"

    parser = argparse.ArgumentParser(description='Generate formatted output from diarization JSON')
    parser.add_argument('--input', '-i',
                       default=str(default_input),
                       help='Input JSON file path')
    parser.add_argument('--format', '-f',
                       choices=['html', 'markdown', 'terminal', 'all'],
                       default='all',
                       help='Output format(s) to generate')

    args = parser.parse_args()

    # Check if input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        print(f"   Expected location: {input_path.absolute()}")
        print(f"   Please ensure the diarization output file exists or provide a path with --input")
        sys.exit(1)

    # Load the data
    print(f"📖 Loading diarization output from: {input_path}")
    data = load_diarization_output(str(input_path))

    # Generate outputs based on format choice
    output_dir = input_path.parent
    base_name = input_path.stem

    if args.format in ['markdown', 'all']:
        md_path = output_dir / f"{base_name}_formatted.md"
        generate_markdown(data, md_path)

    if args.format in ['html', 'all']:
        html_path = output_dir / f"{base_name}_formatted.html"
        generate_html(data, html_path)

    if args.format in ['terminal', 'all']:
        generate_terminal_output(data)

    print(f"\n✨ Formatting complete!")

if __name__ == "__main__":
    main()