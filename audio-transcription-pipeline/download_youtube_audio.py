#!/usr/bin/env python3
"""
Simple YouTube audio downloader for testing
Downloads audio without requiring GPU or transcription
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from youtube_downloader import YouTubeSessionDownloader


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download YouTube audio (no transcription)')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output-dir', default='downloads', help='Output directory')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("YouTube Audio Downloader")
    print("="*60)
    print(f"URL: {args.url}")
    print("="*60 + "\n")

    # Download
    downloader = YouTubeSessionDownloader(download_dir=args.output_dir)
    result = downloader.download_session(args.url)

    # Display results
    print("\n" + "="*60)
    print("✓ DOWNLOAD COMPLETE")
    print("="*60)
    print(f"Session ID: {result['session_id']}")
    print(f"Title: {result['metadata']['title']}")
    print(f"Channel: {result['metadata']['channel']}")
    print(f"Duration: {result['metadata']['duration_minutes']:.1f} minutes")
    print(f"\nAudio file: {result['audio_path']}")
    print(f"Metadata: {result['metadata_path']}")
    print("="*60 + "\n")

    print("To transcribe this file on Vast.ai:")
    print(f"  ./run_gpu_pipeline.sh \"{result['audio_path']}\" 2")
    print("")


if __name__ == "__main__":
    main()
