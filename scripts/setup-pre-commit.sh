#!/bin/bash
# Setup script for pre-commit hooks and security scanning
# Run from repository root: ./scripts/setup-pre-commit.sh

set -e  # Exit on error

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================"
echo "Pre-commit Hooks Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Install Python 3.13+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if in git repository
echo "Checking git repository..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git repository detected${NC}"
echo ""

# Install pre-commit using pipx (recommended) or pip
echo "Installing pre-commit..."
if command -v pipx &> /dev/null; then
    echo "Using pipx (recommended)..."
    pipx install pre-commit || pipx upgrade pre-commit
elif command -v brew &> /dev/null; then
    echo "Using Homebrew (recommended for macOS)..."
    brew install pre-commit || brew upgrade pre-commit
else
    echo "Using pip3 --user (fallback)..."
    python3 -m pip install --user pre-commit --upgrade
fi

if ! command -v pre-commit &> /dev/null; then
    echo -e "${RED}Error: pre-commit installation failed${NC}"
    echo "Try manually: pip3 install --user pre-commit"
    exit 1
fi

echo -e "${GREEN}✓ pre-commit installed${NC}"
echo ""

# Install detect-secrets
echo "Installing detect-secrets..."
if command -v pipx &> /dev/null; then
    pipx install detect-secrets || pipx upgrade detect-secrets
else
    python3 -m pip install --user detect-secrets --upgrade
fi

if ! command -v detect-secrets &> /dev/null && ! python3 -m detect_secrets --version &> /dev/null; then
    echo -e "${YELLOW}Warning: detect-secrets installation may have failed${NC}"
    echo "Try manually: pip3 install --user detect-secrets"
else
    echo -e "${GREEN}✓ detect-secrets installed${NC}"
fi
echo ""

# Install pre-commit hooks into .git/hooks
echo "Installing pre-commit hooks into .git/hooks..."
pre-commit install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${RED}Error: Failed to install pre-commit hooks${NC}"
    exit 1
fi
echo ""

# Check if .pre-commit-config.yaml exists
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${YELLOW}Warning: .pre-commit-config.yaml not found${NC}"
    echo "See .github/SECURITY.md for configuration template"
else
    echo -e "${GREEN}✓ .pre-commit-config.yaml found${NC}"
fi
echo ""

# Update secrets baseline if detect-secrets is available
if command -v detect-secrets &> /dev/null || python3 -m detect_secrets --version &> /dev/null 2>&1; then
    echo "Updating secrets baseline..."

    if command -v detect-secrets &> /dev/null; then
        detect-secrets scan --baseline .secrets.baseline
    else
        python3 -m detect_secrets scan --baseline .secrets.baseline
    fi

    echo -e "${GREEN}✓ Secrets baseline updated${NC}"
else
    echo -e "${YELLOW}Skipping secrets baseline update (detect-secrets not available)${NC}"
fi
echo ""

# Run pre-commit on all files (optional, can be slow)
read -p "Run pre-commit checks on all files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running pre-commit on all files..."
    pre-commit run --all-files

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All pre-commit checks passed${NC}"
    else
        echo -e "${YELLOW}Some checks failed - review output above${NC}"
    fi
else
    echo "Skipping full repository scan"
fi
echo ""

# Summary
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Pre-commit hooks will now run automatically on 'git commit'"
echo "2. To manually run hooks: pre-commit run --all-files"
echo "3. To bypass hooks (emergency only): git commit --no-verify"
echo "4. See .github/SECURITY.md for full documentation"
echo ""
echo "Installed hooks:"
echo "  - detect-secrets: Scans for hardcoded credentials"
echo "  - check-added-large-files: Prevents large file commits"
echo "  - detect-private-key: Detects SSH/TLS private keys"
echo "  - no-commit-to-branch: Blocks direct commits to main/master"
echo "  - black: Python code formatting"
echo "  - prettier: Frontend code formatting"
echo ""
echo -e "${GREEN}Happy secure coding!${NC}"
