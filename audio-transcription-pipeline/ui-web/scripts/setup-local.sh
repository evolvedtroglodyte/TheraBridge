#!/bin/bash
set -e

echo "🚀 Setting up Audio Transcription UI for local development..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to ui-web root (parent of scripts/)
UI_WEB_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Working directory: $UI_WEB_ROOT"

# Check if .env files exist
echo -e "\n${BLUE}Checking environment configuration...${NC}"

if [ ! -f "$UI_WEB_ROOT/backend/.env" ]; then
    echo "Creating backend/.env from .env.example..."
    cp "$UI_WEB_ROOT/backend/.env.example" "$UI_WEB_ROOT/backend/.env"
    echo "⚠️  Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - HUGGINGFACE_TOKEN"
fi

if [ ! -f "$UI_WEB_ROOT/frontend/.env.local" ]; then
    echo "Creating frontend/.env.local..."
    cat > "$UI_WEB_ROOT/frontend/.env.local" << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
fi

# Install backend dependencies
echo -e "\n${BLUE}Installing backend dependencies...${NC}"
cd "$UI_WEB_ROOT/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
echo -e "\n${BLUE}Installing frontend dependencies...${NC}"
cd "$UI_WEB_ROOT/frontend"
npm install

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\nTo run the application:"
echo -e "  ${BLUE}Terminal 1 (Backend):${NC}"
echo -e "    cd backend"
echo -e "    source venv/bin/activate"
echo -e "    python -m app.main"
echo -e "\n  ${BLUE}Terminal 2 (Frontend):${NC}"
echo -e "    cd frontend"
echo -e "    npm run dev"
echo -e "\nThen open http://localhost:5173 in your browser"
