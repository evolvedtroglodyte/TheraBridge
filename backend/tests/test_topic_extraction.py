"""
Test script for topic extraction on mock therapy sessions

This script:
1. Loads session transcripts from mock-therapy-data directory
2. Runs topic extraction using TopicExtractor
3. Outputs extracted metadata for each session
4. Saves results to a JSON file for verification

Usage:
    python tests/test_topic_extraction.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.topic_extractor import TopicExtractor


def load_session_transcript(session_file: Path):
    """Load transcript from a mock session JSON file"""
    with open(session_file, 'r') as f:
        data = json.load(f)
    return data


def process_session(session_file: Path, extractor: TopicExtractor):
    """Process a single session and extract topics"""
    print(f"\n{'=' * 80}")
    print(f"Processing: {session_file.name}")
    print('=' * 80)

    # Load session data
    session_data = load_session_transcript(session_file)
    session_id = session_data.get('id', session_file.stem)

    # Get transcript segments
    segments = session_data.get('segments', [])

    if not segments:
        print(f"⚠️  No segments found in {session_file.name}")
        return None

    print(f"📄 Session ID: {session_id}")
    print(f"📊 Total segments: {len(segments)}")

    # Extract metadata
    try:
        metadata = extractor.extract_metadata(
            session_id=session_id,
            segments=segments
        )

        # Display results
        print(f"\n✨ Extraction Results:")
        print(f"   Confidence: {metadata.confidence:.2f}")
        print(f"\n📌 Topics ({len(metadata.topics)}):")
        for i, topic in enumerate(metadata.topics, 1):
            print(f"   {i}. {topic}")

        print(f"\n✅ Action Items ({len(metadata.action_items)}):")
        for i, item in enumerate(metadata.action_items, 1):
            print(f"   {i}. {item}")

        print(f"\n🛠️  Technique:")
        print(f"   {metadata.technique}")

        print(f"\n📝 Summary:")
        print(f"   {metadata.summary}")

        # Validate summary length
        summary_length = len(metadata.summary)
        length_status = "✅" if summary_length <= 150 else "❌"
        print(f"    Summary length: {length_status} {summary_length}/150 chars")

        if summary_length > 150:
            print(f"    ⚠️  WARNING: Summary exceeds limit!")

        # Convert to dict for JSON serialization
        return {
            'session_id': metadata.session_id,
            'session_file': session_file.name,
            'topics': metadata.topics,
            'action_items': metadata.action_items,
            'technique': metadata.technique,
            'summary': metadata.summary,
            'confidence': metadata.confidence,
            'extracted_at': metadata.extracted_at.isoformat(),
            'raw_meta_summary': metadata.raw_meta_summary
        }

    except Exception as e:
        print(f"\n❌ Error extracting topics: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test runner"""
    print("\n" + "=" * 80)
    print("TOPIC EXTRACTION TEST - Mock Therapy Sessions")
    print("=" * 80)

    # Find mock-therapy-data directory
    current_dir = Path(__file__).parent.parent.parent
    mock_data_dir = current_dir / "mock-therapy-data" / "sessions"

    if not mock_data_dir.exists():
        print(f"\n❌ Error: Mock data directory not found at {mock_data_dir}")
        return

    print(f"\n📁 Mock data directory: {mock_data_dir}")

    # Get all session files
    session_files = sorted(mock_data_dir.glob("session_*.json"))

    if not session_files:
        print(f"\n❌ Error: No session files found in {mock_data_dir}")
        return

    print(f"📊 Found {len(session_files)} session files")

    # Initialize extractor
    print("\n🤖 Initializing TopicExtractor...")
    try:
        extractor = TopicExtractor()
        print("✓ TopicExtractor initialized successfully")
    except Exception as e:
        print(f"\n❌ Error initializing TopicExtractor: {e}")
        print("\nMake sure OPENAI_API_KEY is set in backend/.env")
        return

    # Process each session
    results = []
    for session_file in session_files:
        result = process_session(session_file, extractor)
        if result:
            results.append(result)

    # Save results
    output_file = current_dir / "mock-therapy-data" / "topic_extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'test_run_at': datetime.now().isoformat(),
            'total_sessions': len(session_files),
            'successful_extractions': len(results),
            'results': results
        }, f, indent=2)

    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print('=' * 80)
    print(f"Total sessions processed: {len(session_files)}")
    print(f"Successful extractions: {len(results)}")
    print(f"Failed extractions: {len(session_files) - len(results)}")
    print(f"\n💾 Results saved to: {output_file}")
    print("\n✨ Test complete!")


if __name__ == "__main__":
    main()
