#!/bin/bash
# Download and transcribe YouTube CBT therapy sessions

set -e

echo "============================================================"
echo "YouTube CBT Session Downloader & Transcriber"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Check for required environment variables
if [ -z "$VAST_API_KEY" ] && [ ! -f .env ]; then
    echo "⚠ VAST_API_KEY not found"
    echo "Set it in .env file or export VAST_API_KEY=your_key"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Display usage
show_usage() {
    echo "Usage:"
    echo "  ./download_youtube_sessions.sh --url <youtube_url>"
    echo "  ./download_youtube_sessions.sh --search \"CBT therapy session\""
    echo "  ./download_youtube_sessions.sh --urls-file urls.txt"
    echo ""
    echo "Options:"
    echo "  --url URL              Single YouTube video or playlist URL"
    echo "  --search QUERY         Search YouTube for videos"
    echo "  --urls-file FILE       File with one URL per line"
    echo "  --max-results N        Maximum search results (default: 10)"
    echo "  --num-speakers N       Number of speakers (default: 2)"
    echo "  --batch-size N         Videos per GPU instance (default: 5)"
    echo "  --local                Process locally (requires GPU)"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Download single video"
    echo "  ./download_youtube_sessions.sh --url https://www.youtube.com/watch?v=VIDEO_ID"
    echo ""
    echo "  # Search and process 20 videos"
    echo "  ./download_youtube_sessions.sh --search \"cognitive behavioral therapy session\" --max-results 20"
    echo ""
    echo "  # Process playlist"
    echo "  ./download_youtube_sessions.sh --url https://www.youtube.com/playlist?list=PLAYLIST_ID"
    echo ""
    echo "  # Batch process URLs from file using Vast.ai"
    echo "  ./download_youtube_sessions.sh --urls-file cbt_videos.txt --batch-size 10"
    echo ""
    exit 0
}

# Parse arguments
LOCAL_MODE=false
URL=""
SEARCH=""
URLS_FILE=""
MAX_RESULTS=10
NUM_SPEAKERS=2
BATCH_SIZE=5

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
        --urls-file)
            URLS_FILE="$2"
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
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --local)
            LOCAL_MODE=true
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
if [ -z "$URL" ] && [ -z "$SEARCH" ] && [ -z "$URLS_FILE" ]; then
    echo "Error: Must provide --url, --search, or --urls-file"
    echo ""
    show_usage
fi

# Choose processing mode
if [ "$LOCAL_MODE" = true ]; then
    echo "Mode: Local GPU processing"
    echo "============================================================"
    echo ""

    # Check for GPU
    if ! python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
        echo "✗ GPU not available. Use Vast.ai mode (remove --local flag)"
        exit 1
    fi

    # Build command
    CMD="python src/youtube_to_transcript.py"

    if [ -n "$URL" ]; then
        CMD="$CMD --url \"$URL\""
    elif [ -n "$SEARCH" ]; then
        CMD="$CMD --search \"$SEARCH\" --max-results $MAX_RESULTS"
    fi

    CMD="$CMD --num-speakers $NUM_SPEAKERS"

    # Execute
    eval $CMD

else
    echo "Mode: Vast.ai GPU instances"
    echo "============================================================"
    echo ""

    if [ -n "$URL" ] || [ -n "$SEARCH" ]; then
        # Single video or search - use youtube_to_transcript with Vast.ai upload
        echo "⚠ For optimal Vast.ai performance, use --urls-file with multiple videos"
        echo ""

        CMD="python src/youtube_to_transcript.py"

        if [ -n "$URL" ]; then
            CMD="$CMD --url \"$URL\""
        elif [ -n "$SEARCH" ]; then
            CMD="$CMD --search \"$SEARCH\" --max-results $MAX_RESULTS"
        fi

        CMD="$CMD --num-speakers $NUM_SPEAKERS"
        eval $CMD

    elif [ -n "$URLS_FILE" ]; then
        # Batch processing with Vast.ai
        if [ ! -f "$URLS_FILE" ]; then
            echo "✗ File not found: $URLS_FILE"
            exit 1
        fi

        python scripts/batch_youtube_vast.py \
            --urls-file "$URLS_FILE" \
            --num-speakers $NUM_SPEAKERS \
            --batch-size $BATCH_SIZE
    fi
fi

echo ""
echo "============================================================"
echo "✓ Processing complete!"
echo "============================================================"
echo "Results saved to: outputs/youtube_sessions/"
echo ""
