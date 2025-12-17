#!/usr/bin/env python3
"""
YouTube to Transcript Pipeline
Downloads CBT sessions from YouTube and processes them with GPU-accelerated transcription
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from youtube_downloader import YouTubeSessionDownloader
from pipeline_gpu import GPUTranscriptionPipeline


class YouTubeTranscriptPipeline:
    """
    Complete pipeline: YouTube download → GPU transcription → Speaker diarization
    """

    def __init__(self,
                 download_dir: str = "downloads",
                 output_dir: str = "outputs/youtube_sessions",
                 whisper_model: str = "large-v3"):
        """
        Initialize combined pipeline

        Args:
            download_dir: Directory for downloaded audio
            output_dir: Directory for transcription results
            whisper_model: Whisper model to use (large-v3, medium, small)
        """
        self.downloader = YouTubeSessionDownloader(download_dir=download_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize GPU pipeline if available
        self.gpu_available = self._check_gpu()
        if self.gpu_available:
            print("✓ GPU detected - using GPU pipeline")
            self.pipeline = GPUTranscriptionPipeline(whisper_model=whisper_model)
        else:
            print("⚠ No GPU detected - GPU pipeline required for diarization")
            print("  Install CUDA and PyTorch with GPU support, or use Vast.ai")
            self.pipeline = None

    def _check_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def process_url(self,
                   url: str,
                   num_speakers: int = 2,
                   enable_diarization: bool = True) -> Dict:
        """
        Download YouTube video and transcribe

        Args:
            url: YouTube video URL
            num_speakers: Number of speakers (2 for therapist + client)
            enable_diarization: Whether to run speaker diarization

        Returns:
            Dict with download info, transcription, and output paths
        """
        if not self.pipeline:
            raise RuntimeError("GPU pipeline not available. GPU required for transcription.")

        # Step 1: Download from YouTube
        print("\n" + "="*60)
        print("STEP 1: DOWNLOADING FROM YOUTUBE")
        print("="*60)
        download_result = self.downloader.download_session(url)

        # Step 2: Transcribe with GPU
        print("\n" + "="*60)
        print("STEP 2: GPU TRANSCRIPTION & DIARIZATION")
        print("="*60)
        transcription_result = self.pipeline.process(
            audio_path=download_result['audio_path'],
            num_speakers=num_speakers,
            enable_diarization=enable_diarization
        )

        # Step 3: Combine and save results
        print("\n" + "="*60)
        print("STEP 3: SAVING RESULTS")
        print("="*60)
        combined_result = self._combine_results(download_result, transcription_result)

        session_id = download_result['session_id']
        output_path = self.output_dir / f"{session_id}_transcript.json"

        with open(output_path, 'w') as f:
            json.dump(combined_result, f, indent=2)

        # Save human-readable transcript
        readable_path = self.output_dir / f"{session_id}_transcript.txt"
        self._save_readable_transcript(combined_result, readable_path)

        print(f"✓ Transcription saved: {output_path}")
        print(f"✓ Readable transcript: {readable_path}")
        print("="*60 + "\n")

        return {
            'session_id': session_id,
            'output_json': str(output_path),
            'output_txt': str(readable_path),
            'result': combined_result
        }

    def process_playlist(self,
                        playlist_url: str,
                        num_speakers: int = 2,
                        max_videos: Optional[int] = None,
                        enable_diarization: bool = True) -> List[Dict]:
        """
        Download and transcribe entire playlist

        Args:
            playlist_url: YouTube playlist URL
            num_speakers: Number of speakers per video
            max_videos: Maximum videos to process
            enable_diarization: Whether to run speaker diarization

        Returns:
            List of results for each video
        """
        if not self.pipeline:
            raise RuntimeError("GPU pipeline not available. GPU required for transcription.")

        # Download all videos
        download_results = self.downloader.download_playlist(playlist_url, max_videos=max_videos)

        # Process each video
        results = []
        for i, download_result in enumerate(download_results, 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING VIDEO {i}/{len(download_results)}")
            print(f"{'='*60}")

            try:
                # Transcribe
                transcription_result = self.pipeline.process(
                    audio_path=download_result['audio_path'],
                    num_speakers=num_speakers,
                    enable_diarization=enable_diarization
                )

                # Save combined result
                combined_result = self._combine_results(download_result, transcription_result)
                session_id = download_result['session_id']
                output_path = self.output_dir / f"{session_id}_transcript.json"

                with open(output_path, 'w') as f:
                    json.dump(combined_result, f, indent=2)

                # Save readable transcript
                readable_path = self.output_dir / f"{session_id}_transcript.txt"
                self._save_readable_transcript(combined_result, readable_path)

                results.append({
                    'session_id': session_id,
                    'output_json': str(output_path),
                    'output_txt': str(readable_path),
                    'success': True
                })

                print(f"✓ Video {i} complete: {session_id}")

            except Exception as e:
                print(f"✗ Failed to process video {i}: {e}")
                results.append({
                    'session_id': download_result['session_id'],
                    'success': False,
                    'error': str(e)
                })

        print(f"\n{'='*60}")
        print(f"PLAYLIST PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {sum(1 for r in results if r['success'])}/{len(results)}")
        print(f"{'='*60}\n")

        return results

    def search_and_process(self,
                          query: str,
                          max_results: int = 10,
                          num_speakers: int = 2,
                          enable_diarization: bool = True) -> List[Dict]:
        """
        Search YouTube and process all results

        Args:
            query: Search query (e.g., "CBT therapy session")
            max_results: Maximum videos to download
            num_speakers: Number of speakers
            enable_diarization: Whether to run speaker diarization

        Returns:
            List of results for each video
        """
        if not self.pipeline:
            raise RuntimeError("GPU pipeline not available. GPU required for transcription.")

        # Search and download
        download_results = self.downloader.search_and_download(
            query=query,
            max_results=max_results
        )

        # Process each video
        results = []
        for i, download_result in enumerate(download_results, 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING SEARCH RESULT {i}/{len(download_results)}")
            print(f"{'='*60}")

            try:
                transcription_result = self.pipeline.process(
                    audio_path=download_result['audio_path'],
                    num_speakers=num_speakers,
                    enable_diarization=enable_diarization
                )

                combined_result = self._combine_results(download_result, transcription_result)
                session_id = download_result['session_id']
                output_path = self.output_dir / f"{session_id}_transcript.json"

                with open(output_path, 'w') as f:
                    json.dump(combined_result, f, indent=2)

                readable_path = self.output_dir / f"{session_id}_transcript.txt"
                self._save_readable_transcript(combined_result, readable_path)

                results.append({
                    'session_id': session_id,
                    'output_json': str(output_path),
                    'output_txt': str(readable_path),
                    'success': True
                })

                print(f"✓ Result {i} complete: {session_id}")

            except Exception as e:
                print(f"✗ Failed to process result {i}: {e}")
                results.append({
                    'session_id': download_result['session_id'],
                    'success': False,
                    'error': str(e)
                })

        print(f"\n{'='*60}")
        print(f"SEARCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {sum(1 for r in results if r['success'])}/{len(results)}")
        print(f"{'='*60}\n")

        return results

    def _combine_results(self, download_result: Dict, transcription_result: Dict) -> Dict:
        """Combine download metadata with transcription results"""
        return {
            'youtube_metadata': download_result['metadata'],
            'audio_path': download_result['audio_path'],
            'transcription': {
                'full_text': transcription_result['full_text'],
                'language': transcription_result['language'],
                'duration': transcription_result['duration'],
                'segments': transcription_result['segments'],
                'aligned_segments': transcription_result.get('aligned_segments', []),
                'speaker_turns': transcription_result.get('speaker_turns', []),
            },
            'performance_metrics': transcription_result.get('performance_metrics', {}),
            'provider': transcription_result.get('provider', 'unknown'),
            'processed_at': datetime.now().isoformat(),
        }

    def _save_readable_transcript(self, result: Dict, output_path: Path):
        """Save human-readable transcript"""
        with open(output_path, 'w') as f:
            # Header
            metadata = result['youtube_metadata']
            f.write("="*60 + "\n")
            f.write(f"THERAPY SESSION TRANSCRIPT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Title: {metadata['title']}\n")
            f.write(f"Source: {metadata['url']}\n")
            f.write(f"Channel: {metadata['channel']}\n")
            f.write(f"Duration: {metadata['duration_minutes']:.1f} minutes\n")
            f.write(f"Processed: {result['processed_at']}\n")
            f.write("\n" + "="*60 + "\n\n")

            # Transcript with speakers
            aligned_segments = result['transcription'].get('aligned_segments', [])
            if aligned_segments:
                # Group by speaker for readability
                current_speaker = None
                for segment in aligned_segments:
                    speaker = segment.get('speaker', 'UNKNOWN')
                    text = segment['text']
                    timestamp = f"[{segment['start']:.1f}s]"

                    # Add speaker label when it changes
                    if speaker != current_speaker:
                        f.write(f"\n{speaker}:\n")
                        current_speaker = speaker

                    f.write(f"{timestamp} {text}\n")
            else:
                # Fallback to plain segments
                for segment in result['transcription']['segments']:
                    timestamp = f"[{segment['start']:.1f}s]"
                    f.write(f"{timestamp} {segment['text']}\n")

            # Footer
            f.write("\n" + "="*60 + "\n")
            metrics = result.get('performance_metrics', {})
            if 'total_duration' in metrics:
                f.write(f"Processing time: {metrics['total_duration']:.1f}s\n")
            f.write("="*60 + "\n")


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Download YouTube CBT sessions and transcribe with GPU acceleration'
    )
    parser.add_argument('--url', help='YouTube video or playlist URL')
    parser.add_argument('--search', help='Search query for YouTube videos')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum search results')
    parser.add_argument('--num-speakers', type=int, default=2, help='Number of speakers')
    parser.add_argument('--no-diarization', action='store_true', help='Disable speaker diarization')
    parser.add_argument('--output-dir', default='outputs/youtube_sessions', help='Output directory')
    parser.add_argument('--download-dir', default='downloads', help='Download directory')
    parser.add_argument('--model', default='large-v3', help='Whisper model (large-v3, medium, small)')

    args = parser.parse_args()

    if not args.url and not args.search:
        print("Error: Must provide either --url or --search")
        parser.print_help()
        sys.exit(1)

    # Initialize pipeline
    pipeline = YouTubeTranscriptPipeline(
        download_dir=args.download_dir,
        output_dir=args.output_dir,
        whisper_model=args.model
    )

    # Process based on input type
    if args.url:
        if 'playlist' in args.url or 'list=' in args.url:
            results = pipeline.process_playlist(
                args.url,
                num_speakers=args.num_speakers,
                enable_diarization=not args.no_diarization
            )
        else:
            result = pipeline.process_url(
                args.url,
                num_speakers=args.num_speakers,
                enable_diarization=not args.no_diarization
            )
            results = [result]
    elif args.search:
        results = pipeline.search_and_process(
            args.search,
            max_results=args.max_results,
            num_speakers=args.num_speakers,
            enable_diarization=not args.no_diarization
        )

    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    successful = sum(1 for r in results if r.get('success', True))
    print(f"Total processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Output directory: {args.output_dir}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
