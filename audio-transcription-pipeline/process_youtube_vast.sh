#!/bin/bash
# Download YouTube videos and process on Vast.ai GPU

set -e

echo "============================================================"
echo "YouTube → Vast.ai GPU Pipeline"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for required tools
if ! command -v python3 &> /dev/null; then
    echo "✗ python3 not found"
    exit 1
fi

# Display usage
show_usage() {
    echo "Usage:"
    echo "  ./process_youtube_vast.sh --url <youtube_url> [options]"
    echo "  ./process_youtube_vast.sh --search \"query\" [options]"
    echo ""
    echo "Options:"
    echo "  --url URL              YouTube video URL"
    echo "  --search QUERY         Search YouTube for videos"
    echo "  --max-results N        Maximum search results (default: 5)"
    echo "  --num-speakers N       Number of speakers (default: 2)"
    echo "  --download-only        Only download, don't transcribe"
    echo "  --help                 Show this help"
    echo ""
    echo "Examples:"
    echo "  # Download and transcribe single video"
    echo "  ./process_youtube_vast.sh --url \"https://www.youtube.com/watch?v=VLDDUL3HBIg\""
    echo ""
    echo "  # Search and process top 3 results"
    echo "  ./process_youtube_vast.sh --search \"CBT therapy session\" --max-results 3"
    echo ""
    echo "  # Download only"
    echo "  ./process_youtube_vast.sh --url \"https://www.youtube.com/watch?v=VLDDUL3HBIg\" --download-only"
    echo ""
    exit 0
}

# Parse arguments
URL=""
SEARCH=""
MAX_RESULTS=5
NUM_SPEAKERS=2
DOWNLOAD_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            URL="$2"
            shift 2
            ;;
        --search)
            SEARCH="$2"
            shift 2
            ;;
        --max-results)
            MAX_RESULTS="$2"
            shift 2
            ;;
        --num-speakers)
            NUM_SPEAKERS="$2"
            shift 2
            ;;
        --download-only)
            DOWNLOAD_ONLY=true
            shift
            ;;
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Validate input
if [ -z "$URL" ] && [ -z "$SEARCH" ]; then
    echo "Error: Must provide --url or --search"
    echo ""
    show_usage
fi

# Create temp directory for this session
SESSION_DIR="downloads/session_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SESSION_DIR"

echo "Step 1: Downloading from YouTube"
echo "============================================================"

# Download videos
if [ -n "$URL" ]; then
    # Single URL
    python3 -c "
import sys
sys.path.insert(0, 'src')
from youtube_downloader import YouTubeSessionDownloader

downloader = YouTubeSessionDownloader(download_dir='$SESSION_DIR')
result = downloader.download_session('$URL')

print('')
print('✓ Download complete!')
print(f\"  Audio: {result['audio_path']}\")
print(f\"  Duration: {result['metadata']['duration_minutes']:.1f} minutes\")

# Save audio path for processing
with open('$SESSION_DIR/audio_files.txt', 'w') as f:
    f.write(result['audio_path'])
"
elif [ -n "$SEARCH" ]; then
    # Search
    python3 -c "
import sys
sys.path.insert(0, 'src')
from youtube_downloader import YouTubeSessionDownloader

downloader = YouTubeSessionDownloader(download_dir='$SESSION_DIR')
results = downloader.search_and_download(
    query='$SEARCH',
    max_results=$MAX_RESULTS
)

print('')
print(f'✓ Downloaded {len(results)} videos')

# Save audio paths for processing
with open('$SESSION_DIR/audio_files.txt', 'w') as f:
    for r in results:
        f.write(r['audio_path'] + '\n')
"
fi

if [ ! -f "$SESSION_DIR/audio_files.txt" ]; then
    echo "✗ Download failed"
    exit 1
fi

# Count downloaded files
NUM_FILES=$(wc -l < "$SESSION_DIR/audio_files.txt" | tr -d ' ')
echo ""
echo "Downloaded $NUM_FILES file(s)"

if [ "$DOWNLOAD_ONLY" = true ]; then
    echo ""
    echo "============================================================"
    echo "✓ Download complete! (transcription skipped)"
    echo "============================================================"
    echo "Audio files saved to: $SESSION_DIR/audio/"
    echo ""
    echo "To transcribe later:"
    while IFS= read -r audio_file; do
        echo "  ./run_gpu_pipeline.sh \"$audio_file\" $NUM_SPEAKERS"
    done < "$SESSION_DIR/audio_files.txt"
    echo ""
    exit 0
fi

echo ""
echo "Step 2: Processing on Vast.ai GPU"
echo "============================================================"

# Process each file on Vast.ai
OUTPUT_DIR="outputs/youtube_sessions"
mkdir -p "$OUTPUT_DIR"

SUCCESS_COUNT=0
FAIL_COUNT=0

while IFS= read -r audio_file; do
    echo ""
    echo "Processing: $audio_file"
    echo "------------------------------------------------------------"

    # Run on Vast.ai
    if ./run_gpu_pipeline.sh "$audio_file" "$NUM_SPEAKERS"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "✓ Success"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "✗ Failed"
    fi

done < "$SESSION_DIR/audio_files.txt"

echo ""
echo "============================================================"
echo "✓ Processing Complete!"
echo "============================================================"
echo "Total files: $NUM_FILES"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo ""
echo "Downloads: $SESSION_DIR/"
echo "Results: outputs/vast_results/"
echo "============================================================"
echo ""
