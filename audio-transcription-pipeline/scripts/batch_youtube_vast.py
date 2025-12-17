#!/usr/bin/env python3
"""
Batch YouTube Processing with Vast.ai
Downloads YouTube videos and processes them on GPU instances
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.youtube_downloader import YouTubeSessionDownloader


class BatchYouTubeProcessor:
    """
    Batch process YouTube videos with Vast.ai GPU instances
    """

    def __init__(self,
                 download_dir: str = "downloads",
                 output_dir: str = "outputs/youtube_sessions",
                 vast_api_key: Optional[str] = None):
        """
        Initialize batch processor

        Args:
            download_dir: Directory for downloaded audio
            output_dir: Directory for transcription results
            vast_api_key: Vast.ai API key (optional, reads from env)
        """
        self.download_dir = Path(download_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Get Vast API key
        self.vast_api_key = vast_api_key or os.getenv("VAST_API_KEY")
        if not self.vast_api_key:
            raise ValueError("VAST_API_KEY not found in environment")

        self.downloader = YouTubeSessionDownloader(download_dir=str(download_dir))

    def process_url_list(self,
                        urls: List[str],
                        num_speakers: int = 2,
                        batch_size: int = 5) -> List[Dict]:
        """
        Process list of YouTube URLs in batches

        Args:
            urls: List of YouTube URLs
            num_speakers: Number of speakers
            batch_size: Number of videos to process per GPU instance

        Returns:
            List of processing results
        """
        print(f"\n{'='*60}")
        print(f"BATCH YOUTUBE PROCESSING")
        print(f"{'='*60}")
        print(f"Total videos: {len(urls)}")
        print(f"Batch size: {batch_size}")
        print(f"{'='*60}\n")

        # Step 1: Download all videos locally
        print("STEP 1: DOWNLOADING ALL VIDEOS")
        print("="*60)
        download_results = []
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n[{i}/{len(urls)}] Downloading: {url}")
                result = self.downloader.download_session(url)
                download_results.append(result)
            except Exception as e:
                print(f"✗ Failed to download {url}: {e}")
                continue

        print(f"\n✓ Downloaded {len(download_results)}/{len(urls)} videos")
        print("="*60 + "\n")

        # Step 2: Process in batches on Vast.ai
        print("STEP 2: PROCESSING ON VAST.AI GPU")
        print("="*60)
        all_results = []

        for i in range(0, len(download_results), batch_size):
            batch = download_results[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(download_results) + batch_size - 1) // batch_size

            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} videos)")

            try:
                batch_results = self._process_batch_on_vast(batch, num_speakers)
                all_results.extend(batch_results)
            except Exception as e:
                print(f"✗ Failed to process batch {batch_num}: {e}")
                # Mark all in batch as failed
                for item in batch:
                    all_results.append({
                        'session_id': item['session_id'],
                        'success': False,
                        'error': str(e)
                    })

        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        successful = sum(1 for r in all_results if r.get('success', False))
        print(f"Total: {len(all_results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(all_results) - successful}")
        print(f"{'='*60}\n")

        return all_results

    def process_search_query(self,
                           query: str,
                           max_results: int = 20,
                           num_speakers: int = 2,
                           batch_size: int = 5) -> List[Dict]:
        """
        Search YouTube and process results in batches

        Args:
            query: Search query
            max_results: Maximum videos to download
            num_speakers: Number of speakers
            batch_size: Videos per GPU instance

        Returns:
            List of processing results
        """
        print(f"\n{'='*60}")
        print(f"YOUTUBE SEARCH & BATCH PROCESSING")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Max results: {max_results}")
        print(f"{'='*60}\n")

        # Download from search
        download_results = self.downloader.search_and_download(
            query=query,
            max_results=max_results
        )

        if not download_results:
            print("No videos downloaded")
            return []

        # Process in batches
        all_results = []
        for i in range(0, len(download_results), batch_size):
            batch = download_results[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(download_results) + batch_size - 1) // batch_size

            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} videos)")

            try:
                batch_results = self._process_batch_on_vast(batch, num_speakers)
                all_results.extend(batch_results)
            except Exception as e:
                print(f"✗ Failed to process batch {batch_num}: {e}")
                for item in batch:
                    all_results.append({
                        'session_id': item['session_id'],
                        'success': False,
                        'error': str(e)
                    })

        return all_results

    def _process_batch_on_vast(self, batch: List[Dict], num_speakers: int) -> List[Dict]:
        """
        Process batch of videos on a single Vast.ai instance

        Args:
            batch: List of download results
            num_speakers: Number of speakers

        Returns:
            List of processing results
        """
        print(f"\nStarting Vast.ai instance for {len(batch)} videos...")

        # Create batch manifest
        manifest = {
            'videos': [
                {
                    'session_id': item['session_id'],
                    'audio_path': item['audio_path'],
                    'metadata_path': item['metadata_path']
                }
                for item in batch
            ],
            'num_speakers': num_speakers
        }

        manifest_path = self.download_dir / "batch_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        # Use existing run_gpu_vast.py script
        script_path = Path(__file__).parent / "run_gpu_vast_batch.py"

        try:
            # Run batch processing script
            cmd = [
                "python",
                str(script_path),
                str(manifest_path),
                "--output-dir", str(self.output_dir)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Vast.ai processing failed: {result.stderr}")

            # Parse results
            results_file = self.output_dir / "batch_results.json"
            if results_file.exists():
                with open(results_file) as f:
                    return json.load(f)
            else:
                raise RuntimeError("Results file not found")

        except Exception as e:
            print(f"Error processing batch: {e}")
            raise


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Batch process YouTube videos with Vast.ai GPU'
    )
    parser.add_argument('--urls', nargs='+', help='List of YouTube URLs')
    parser.add_argument('--urls-file', help='File with one URL per line')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--max-results', type=int, default=20, help='Max search results')
    parser.add_argument('--num-speakers', type=int, default=2, help='Number of speakers')
    parser.add_argument('--batch-size', type=int, default=5, help='Videos per GPU instance')
    parser.add_argument('--output-dir', default='outputs/youtube_sessions', help='Output directory')
    parser.add_argument('--download-dir', default='downloads', help='Download directory')

    args = parser.parse_args()

    # Get URLs
    urls = []
    if args.urls:
        urls = args.urls
    elif args.urls_file:
        with open(args.urls_file) as f:
            urls = [line.strip() for line in f if line.strip()]
    elif not args.search:
        print("Error: Must provide --urls, --urls-file, or --search")
        parser.print_help()
        sys.exit(1)

    # Initialize processor
    processor = BatchYouTubeProcessor(
        download_dir=args.download_dir,
        output_dir=args.output_dir
    )

    # Process
    if urls:
        results = processor.process_url_list(
            urls=urls,
            num_speakers=args.num_speakers,
            batch_size=args.batch_size
        )
    else:
        results = processor.process_search_query(
            query=args.search,
            max_results=args.max_results,
            num_speakers=args.num_speakers,
            batch_size=args.batch_size
        )

    # Save summary
    summary_path = Path(args.output_dir) / "batch_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
