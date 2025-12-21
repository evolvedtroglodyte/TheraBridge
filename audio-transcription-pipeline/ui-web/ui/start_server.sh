#!/bin/bash
# Quick start script for GPU Pipeline Web Server

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================================"
echo "GPU Transcription Pipeline Server - Quick Start"
echo "============================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION"
echo ""

# Check if venv exists (optional but recommended)
if [ ! -d "../venv" ]; then
    echo -e "${YELLOW}Warning: No virtual environment found${NC}"
    echo "Recommended: Create a venv first:"
    echo "  cd .."
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if requirements are installed
echo "Checking server dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}FastAPI not found. Installing dependencies...${NC}"
    pip install -r requirements-server.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo "✓ Dependencies found"
fi
echo ""

# Check environment variables
echo "Checking environment variables..."
if [ -f "../.env" ]; then
    echo "✓ .env file found"

    # Check for required tokens
    if grep -q "OPENAI_API_KEY=" ../.env && grep -q "HF_TOKEN=" ../.env; then
        echo "✓ API keys configured"
    else
        echo -e "${YELLOW}Warning: API keys may not be configured${NC}"
        echo "Make sure .env contains:"
        echo "  OPENAI_API_KEY=your_key"
        echo "  HF_TOKEN=your_token"
    fi
else
    echo -e "${YELLOW}Warning: No .env file found${NC}"
    echo "Create ../.env with:"
    echo "  OPENAI_API_KEY=your_key"
    echo "  HF_TOKEN=your_token"
fi
echo ""

# Check if pipeline exists
PIPELINE_PATH="../src/pipeline_gpu.py"
if [ -f "$PIPELINE_PATH" ]; then
    echo "✓ GPU pipeline found"
else
    echo -e "${RED}Error: Pipeline not found at $PIPELINE_PATH${NC}"
    exit 1
fi
echo ""

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use${NC}"
    echo "Kill the process or use a different port"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "============================================================"
echo -e "${GREEN}Starting Server...${NC}"
echo "============================================================"
echo ""
echo "Server will be available at:"
echo "  - UI:       http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health:   http://localhost:8000/health"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start server
python3 server.py
