#!/usr/bin/env python3
"""
YouTube CBT Session Downloader
Downloads therapy session videos from YouTube and extracts audio for transcription
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yt_dlp


class YouTubeSessionDownloader:
    """
    Downloads CBT/therapy sessions from YouTube
    Extracts metadata and prepares audio for transcription pipeline
    """

    def __init__(self, download_dir: str = "downloads"):
        """
        Initialize YouTube downloader

        Args:
            download_dir: Directory to store downloaded audio files
        """
        self.download_dir = Path(download_dir)
        self.audio_dir = self.download_dir / "audio"
        self.metadata_dir = self.download_dir / "metadata"

        # Create directories
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def download_session(self,
                        url: str,
                        session_id: Optional[str] = None) -> Dict:
        """
        Download single YouTube video and extract audio

        Args:
            url: YouTube video URL or ID
            session_id: Optional custom ID for the session

        Returns:
            Dict with audio_path, metadata_path, and video info
        """
        print(f"\n{'='*60}")
        print(f"Downloading YouTube Session")
        print(f"{'='*60}")
        print(f"URL: {url}")

        # Normalize URL
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        # Generate session ID if not provided
        if not session_id:
            session_id = f"yt_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        audio_path = self.audio_dir / f"{session_id}.mp3"
        metadata_path = self.metadata_dir / f"{session_id}.json"

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.audio_dir / f"{session_id}.%(ext)s"),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }

        # Download and extract audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading video: {video_id}")
            info = ydl.extract_info(url, download=True)

            # Save metadata
            metadata = self._extract_metadata(info, video_id, session_id)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"\n✓ Download complete!")
            print(f"  Audio: {audio_path}")
            print(f"  Metadata: {metadata_path}")
            print(f"  Duration: {metadata['duration_minutes']:.1f} minutes")
            print(f"  Title: {metadata['title']}")
            print(f"{'='*60}\n")

        return {
            'session_id': session_id,
            'video_id': video_id,
            'audio_path': str(audio_path),
            'metadata_path': str(metadata_path),
            'metadata': metadata
        }

    def download_playlist(self,
                         playlist_url: str,
                         max_videos: Optional[int] = None) -> List[Dict]:
        """
        Download all videos from a YouTube playlist

        Args:
            playlist_url: YouTube playlist URL
            max_videos: Maximum number of videos to download

        Returns:
            List of dicts with download results
        """
        print(f"\n{'='*60}")
        print(f"Downloading YouTube Playlist")
        print(f"{'='*60}")
        print(f"URL: {playlist_url}")

        # Extract playlist info
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)

            if 'entries' not in playlist_info:
                raise ValueError("Not a valid playlist URL")

            entries = playlist_info['entries']
            if max_videos:
                entries = entries[:max_videos]

            print(f"Found {len(entries)} videos")
            print(f"{'='*60}\n")

        # Download each video
        results = []
        for i, entry in enumerate(entries, 1):
            try:
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                print(f"\n[{i}/{len(entries)}] Processing: {entry['title']}")

                result = self.download_session(video_url)
                results.append(result)

            except Exception as e:
                print(f"✗ Failed to download {entry['id']}: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"Playlist Download Complete")
        print(f"{'='*60}")
        print(f"Successfully downloaded: {len(results)}/{len(entries)} videos")
        print(f"{'='*60}\n")

        return results

    def search_and_download(self,
                          query: str,
                          max_results: int = 10,
                          min_duration: int = 300,  # 5 minutes
                          max_duration: int = 7200) -> List[Dict]:  # 2 hours
        """
        Search YouTube for CBT sessions and download results

        Args:
            query: Search query (e.g., "CBT therapy session")
            max_results: Maximum number of results to download
            min_duration: Minimum video duration in seconds
            max_duration: Maximum video duration in seconds

        Returns:
            List of dicts with download results
        """
        print(f"\n{'='*60}")
        print(f"Searching YouTube")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Max Results: {max_results}")
        print(f"Duration: {min_duration//60}-{max_duration//60} minutes")

        # Search options
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }

        search_url = f"ytsearch{max_results}:{query}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(search_url, download=False)

            if 'entries' not in search_results:
                print("No results found")
                return []

            entries = search_results['entries']
            print(f"Found {len(entries)} videos")
            print(f"{'='*60}\n")

        # Filter by duration and download
        results = []
        for i, entry in enumerate(entries, 1):
            try:
                # Get full video info to check duration
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"

                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    duration = info.get('duration', 0)

                    # Filter by duration
                    if duration < min_duration or duration > max_duration:
                        print(f"[{i}/{len(entries)}] Skipping (duration {duration//60}m): {entry['title']}")
                        continue

                print(f"\n[{i}/{len(entries)}] Downloading ({duration//60}m): {entry['title']}")
                result = self.download_session(video_url)
                results.append(result)

            except Exception as e:
                print(f"✗ Failed to download {entry['id']}: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"Search Download Complete")
        print(f"{'='*60}")
        print(f"Successfully downloaded: {len(results)}/{len(entries)} videos")
        print(f"{'='*60}\n")

        return results

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _extract_metadata(self, info: Dict, video_id: str, session_id: str) -> Dict:
        """Extract relevant metadata from video info"""
        return {
            'session_id': session_id,
            'video_id': video_id,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'title': info.get('title', 'Unknown'),
            'description': info.get('description', ''),
            'uploader': info.get('uploader', 'Unknown'),
            'upload_date': info.get('upload_date', ''),
            'duration': info.get('duration', 0),
            'duration_minutes': info.get('duration', 0) / 60,
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'channel': info.get('channel', 'Unknown'),
            'channel_url': info.get('channel_url', ''),
            'tags': info.get('tags', []),
            'categories': info.get('categories', []),
            'downloaded_at': datetime.now().isoformat(),
        }


def main():
    """Example usage"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Download CBT therapy sessions from YouTube')
    parser.add_argument('--url', help='YouTube video or playlist URL')
    parser.add_argument('--search', help='Search query for YouTube videos')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum results for search')
    parser.add_argument('--output-dir', default='downloads', help='Output directory')

    args = parser.parse_args()

    if not args.url and not args.search:
        print("Error: Must provide either --url or --search")
        parser.print_help()
        sys.exit(1)

    downloader = YouTubeSessionDownloader(download_dir=args.output_dir)

    if args.url:
        if 'playlist' in args.url or 'list=' in args.url:
            results = downloader.download_playlist(args.url)
        else:
            results = [downloader.download_session(args.url)]
    elif args.search:
        results = downloader.search_and_download(args.search, max_results=args.max_results)

    print(f"\nDownloaded {len(results)} sessions")
    print(f"Audio files saved to: {downloader.audio_dir}")
    print(f"Metadata saved to: {downloader.metadata_dir}")


if __name__ == "__main__":
    main()
