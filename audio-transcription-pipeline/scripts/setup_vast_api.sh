#!/bin/bash
#
# Vast.ai API Key Setup Helper
# Guides you through getting your Vast.ai API key
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Vast.ai API Key Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if API key already exists in .env
if [ -f .env ] && grep -q "VAST_API_KEY=" .env; then
    EXISTING_KEY=$(grep "VAST_API_KEY=" .env | cut -d'=' -f2)
    if [ ! -z "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your_vast_api_key" ]; then
        echo -e "${GREEN}✓ VAST_API_KEY already configured in .env${NC}"
        echo ""
        echo "Current key (masked): ${EXISTING_KEY:0:8}..."
        echo ""
        read -p "Do you want to replace it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping existing API key."
            exit 0
        fi
    fi
fi

echo -e "${YELLOW}Step 1: Get your Vast.ai API key${NC}"
echo ""
echo "Choose your method:"
echo ""
echo -e "${GREEN}Option A: Web Interface (Easiest)${NC}"
echo "  1. Open your browser and go to:"
echo -e "     ${BLUE}https://cloud.vast.ai/cli/${NC}"
echo "  2. Log in to your Vast.ai account"
echo "  3. You'll see your API key displayed on the page"
echo "  4. Copy the API key (it looks like: a1b2c3d4e5f6...)"
echo ""
echo -e "${GREEN}Option B: Account Settings${NC}"
echo "  1. Go to: https://console.vast.ai/"
echo "  2. Click 'Account' → 'API Keys'"
echo "  3. Click 'Create New API Key'"
echo "  4. Give it a name (e.g., 'TherapyBridge Pipeline')"
echo "  5. Copy the key (IMPORTANT: It's only shown once!)"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Save your API key immediately!${NC}"
echo "   Vast.ai only shows it once for security reasons."
echo ""

read -p "Press Enter when you have your API key ready..."
echo ""

# Prompt for API key
echo -e "${YELLOW}Step 2: Enter your Vast.ai API key${NC}"
echo ""
read -s -p "Paste your VAST_API_KEY here: " VAST_API_KEY
echo ""
echo ""

# Validate it's not empty
if [ -z "$VAST_API_KEY" ]; then
    echo -e "${RED}✗ Error: API key cannot be empty${NC}"
    exit 1
fi

# Validate format (basic check)
if [ ${#VAST_API_KEY} -lt 20 ]; then
    echo -e "${RED}✗ Error: API key seems too short (should be 40+ characters)${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 3: Testing API key...${NC}"

# Test the API key
export VAST_API_KEY="$VAST_API_KEY"

# Activate venv if it exists
if [ -d venv ]; then
    source venv/bin/activate
fi

# Check if vastai is installed
if ! command -v vastai &> /dev/null; then
    echo "Installing vastai CLI..."
    pip install -q vastai
fi

# Test API key by listing instances
echo "Testing connection to Vast.ai..."
if vastai show instances &> /dev/null; then
    echo -e "${GREEN}✓ API key is valid!${NC}"
else
    echo -e "${RED}✗ API key validation failed${NC}"
    echo ""
    echo "Possible issues:"
    echo "  - API key is incorrect"
    echo "  - Network connection issue"
    echo "  - Vast.ai service is down"
    echo ""
    exit 1
fi

# Save to .env
echo ""
echo -e "${YELLOW}Step 4: Saving to .env file${NC}"

# Create or update .env
if [ -f .env ]; then
    # Remove existing VAST_API_KEY line
    sed -i.bak '/^VAST_API_KEY=/d' .env
    rm -f .env.bak
fi

echo "VAST_API_KEY=$VAST_API_KEY" >> .env

echo -e "${GREEN}✓ API key saved to .env${NC}"

# Check for other required keys
echo ""
echo -e "${YELLOW}Step 5: Checking other required keys${NC}"
echo ""

MISSING_KEYS=()

if ! grep -q "HF_TOKEN=" .env 2>/dev/null || grep -q "HF_TOKEN=your_hf_token" .env 2>/dev/null; then
    MISSING_KEYS+=("HF_TOKEN")
fi

if ! grep -q "OPENAI_API_KEY=" .env 2>/dev/null || grep -q "OPENAI_API_KEY=your_openai_key" .env 2>/dev/null; then
    MISSING_KEYS+=("OPENAI_API_KEY")
fi

if [ ${#MISSING_KEYS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All required API keys are configured!${NC}"
else
    echo -e "${YELLOW}⚠️  You still need to configure:${NC}"
    for key in "${MISSING_KEYS[@]}"; do
        case $key in
            HF_TOKEN)
                echo "  • HF_TOKEN - Get from: https://huggingface.co/settings/tokens"
                echo "    (Required for speaker diarization)"
                ;;
            OPENAI_API_KEY)
                echo "  • OPENAI_API_KEY - Get from: https://platform.openai.com/api-keys"
                echo "    (Optional - only needed for CPU/API fallback mode)"
                ;;
        esac
    done
    echo ""
    echo "Add them to .env manually or run:"
    echo "  echo 'HF_TOKEN=your_token_here' >> .env"
    echo "  echo 'OPENAI_API_KEY=your_key_here' >> .env"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "You can now run the GPU pipeline with:"
echo -e "  ${BLUE}./run_gpu_pipeline.sh \"your_audio.mp3\" 2${NC}"
echo ""
echo "Or test the connection:"
echo -e "  ${BLUE}vastai show instances${NC}"
echo ""
