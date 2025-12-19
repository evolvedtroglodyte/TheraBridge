#!/usr/bin/env python3
"""
Test YouTube download and transcription pipeline
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.youtube_downloader import YouTubeSessionDownloader
from src.youtube_to_transcript import YouTubeTranscriptPipeline


def test_download_only():
    """Test downloading a YouTube video without transcription"""
    print("\n" + "="*60)
    print("TEST 1: Download YouTube Video Only")
    print("="*60)

    # Use a short educational CBT video
    test_url = "https://www.youtube.com/watch?v=VLDDUL3HBIg"

    downloader = YouTubeSessionDownloader(download_dir="tests/downloads")

    try:
        result = downloader.download_session(test_url)

        print("\n✓ Download test passed!")
        print(f"  Session ID: {result['session_id']}")
        print(f"  Audio file: {result['audio_path']}")
        print(f"  Duration: {result['metadata']['duration_minutes']:.1f} minutes")

        # Verify file exists
        assert Path(result['audio_path']).exists(), "Audio file not found"
        assert Path(result['metadata_path']).exists(), "Metadata file not found"

        return True

    except Exception as e:
        print(f"\n✗ Download test failed: {e}")
        return False


def test_local_transcription():
    """Test full pipeline with local GPU"""
    print("\n" + "="*60)
    print("TEST 2: Full Pipeline (Download + Transcription)")
    print("="*60)

    # Check for GPU
    try:
        import torch
        if not torch.cuda.is_available():
            print("⚠ Skipping - No GPU available")
            print("  Use Vast.ai for GPU processing")
            return True
    except ImportError:
        print("⚠ Skipping - PyTorch not installed")
        return True

    # Use a short video
    test_url = "https://www.youtube.com/watch?v=VLDDUL3HBIg"

    # Use paths relative to script location
    script_dir = Path(__file__).parent
    download_dir = script_dir / "downloads"
    output_dir = script_dir / "outputs" / "youtube"

    pipeline = YouTubeTranscriptPipeline(
        download_dir=str(download_dir),
        output_dir=str(output_dir),
        whisper_model="base"  # Use smaller model for testing
    )

    try:
        result = pipeline.process_url(
            url=test_url,
            num_speakers=2,
            enable_diarization=True
        )

        print("\n✓ Transcription test passed!")
        print(f"  Output JSON: {result['output_json']}")
        print(f"  Output TXT: {result['output_txt']}")

        # Verify files exist
        assert Path(result['output_json']).exists(), "JSON output not found"
        assert Path(result['output_txt']).exists(), "TXT output not found"

        return True

    except Exception as e:
        print(f"\n✗ Transcription test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    """Test YouTube search functionality"""
    print("\n" + "="*60)
    print("TEST 3: YouTube Search")
    print("="*60)

    downloader = YouTubeSessionDownloader(download_dir="tests/downloads")

    try:
        # Search but don't download (dry run)
        from yt_dlp import YoutubeDL

        search_url = "ytsearch3:CBT therapy session"
        ydl_opts = {'quiet': True, 'extract_flat': True}

        with YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(search_url, download=False)

            if 'entries' in results and len(results['entries']) > 0:
                print(f"\n✓ Search test passed!")
                print(f"  Found {len(results['entries'])} results")
                for i, entry in enumerate(results['entries'][:3], 1):
                    print(f"  {i}. {entry['title']}")
                return True
            else:
                print("\n✗ Search test failed - no results")
                return False

    except Exception as e:
        print(f"\n✗ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("YOUTUBE PIPELINE TESTS")
    print("="*60)

    tests = [
        ("Download Only", test_download_only),
        ("Search Functionality", test_search),
        ("Full Pipeline", test_local_transcription),
    ]

    results = []
    for name, test_func in tests:
        print(f"\nRunning: {name}")
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"Test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} passed")
    print("="*60 + "\n")

    return total_passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
