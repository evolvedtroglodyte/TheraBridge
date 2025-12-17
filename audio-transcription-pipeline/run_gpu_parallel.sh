#!/bin/bash
#
# Parallel GPU Racing - Guaranteed Success Strategy
# Spins up 2-3 GPU instances simultaneously, uses first to complete
#
# Usage: ./run_gpu_parallel.sh <audio_file> [num_speakers] [num_racers]
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

AUDIO_FILE="$1"
NUM_SPEAKERS="${2:-2}"
NUM_RACERS="${3:-2}"

if [ -z "$AUDIO_FILE" ]; then
    echo -e "${RED}Usage: $0 <audio_file> [num_speakers] [num_racers]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 session.mp3                    # 2 speakers, 2 parallel instances"
    echo "  $0 session.mp3 3                  # 3 speakers, 2 parallel instances"
    echo "  $0 session.mp3 2 3                # 2 speakers, 3 parallel instances (more reliable)"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo -e "${RED}Error: Audio file not found: $AUDIO_FILE${NC}"
    exit 1
fi

# Check for VAST_API_KEY
if [ -z "$VAST_API_KEY" ]; then
    if [ -f .env ]; then
        echo -e "${YELLOW}Loading VAST_API_KEY from .env${NC}"
        export $(grep VAST_API_KEY .env | xargs)
    fi

    if [ -z "$VAST_API_KEY" ]; then
        echo -e "${RED}Error: VAST_API_KEY not set${NC}"
        echo ""
        echo "Set it via:"
        echo "  export VAST_API_KEY=your_api_key"
        echo "Or add to .env file:"
        echo "  echo 'VAST_API_KEY=your_key' >> .env"
        exit 1
    fi
fi

# Activate venv if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if vastai is installed
if ! command -v vastai &> /dev/null; then
    echo -e "${YELLOW}Installing vastai CLI...${NC}"
    pip install -q vastai
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Parallel GPU Racing - Guaranteed Success${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Audio file: $AUDIO_FILE"
echo "Speakers: $NUM_SPEAKERS"
echo "Parallel instances: $NUM_RACERS"
echo ""
echo -e "${YELLOW}Strategy: Spin up $NUM_RACERS GPUs, use fastest, destroy rest${NC}"
echo ""

# Run the parallel racer
python scripts/run_gpu_parallel.py "$AUDIO_FILE" \
    --num-speakers "$NUM_SPEAKERS" \
    --num-racers "$NUM_RACERS"

echo ""
echo -e "${GREEN}✓ Complete! Results saved to outputs/vast_results/${NC}"
