#!/bin/bash

# =============================================================================
# Test Coverage Runner Script for TherapyBridge Backend
# =============================================================================
# This script runs the test suite with comprehensive coverage reporting.
# It provides multiple output formats and enforces coverage thresholds.
#
# Usage:
#   ./scripts/run_tests_with_coverage.sh [options]
#
# Options:
#   --no-threshold    Skip coverage threshold check
#   --quick           Run tests without HTML report (faster)
#   --unit-only       Run only unit tests (marked with @pytest.mark.unit)
#   --integration     Run only integration tests
#   --clean           Clean previous coverage reports before running
#   --help            Show this help message
#
# Examples:
#   ./scripts/run_tests_with_coverage.sh                # Full run
#   ./scripts/run_tests_with_coverage.sh --quick        # Skip HTML report
#   ./scripts/run_tests_with_coverage.sh --unit-only    # Only unit tests
#   ./scripts/run_tests_with_coverage.sh --clean        # Clean first
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Parse command line arguments
NO_THRESHOLD=false
QUICK=false
UNIT_ONLY=false
INTEGRATION_ONLY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-threshold)
      NO_THRESHOLD=true
      shift
      ;;
    --quick)
      QUICK=true
      shift
      ;;
    --unit-only)
      UNIT_ONLY=true
      shift
      ;;
    --integration)
      INTEGRATION_ONLY=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --no-threshold    Skip coverage threshold check"
      echo "  --quick           Run tests without HTML report (faster)"
      echo "  --unit-only       Run only unit tests"
      echo "  --integration     Run only integration tests"
      echo "  --clean           Clean previous coverage reports before running"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Change to backend directory
cd "$BACKEND_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TherapyBridge Backend - Coverage Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clean previous coverage data if requested
if [ "$CLEAN" = true ]; then
  echo -e "${YELLOW}Cleaning previous coverage reports...${NC}"
  rm -rf htmlcov/ .coverage coverage.xml coverage.json 2>/dev/null || true
  echo -e "${GREEN}✓ Cleaned${NC}"
  echo ""
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
  echo -e "${YELLOW}Attempting to activate venv...${NC}"
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
  else
    echo -e "${RED}Error: venv/bin/activate not found${NC}"
    echo -e "${YELLOW}Please create a virtual environment first:${NC}"
    echo -e "  python -m venv venv"
    echo -e "  source venv/bin/activate"
    echo -e "  pip install -r requirements.txt"
    exit 1
  fi
  echo ""
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
  echo -e "${RED}Error: pytest not found${NC}"
  echo -e "${YELLOW}Installing test dependencies...${NC}"
  pip install pytest pytest-asyncio pytest-cov httpx
  echo ""
fi

# Build pytest command
PYTEST_CMD="pytest"

# Add test selection
if [ "$UNIT_ONLY" = true ]; then
  echo -e "${BLUE}Running unit tests only...${NC}"
  PYTEST_CMD="$PYTEST_CMD -m unit"
elif [ "$INTEGRATION_ONLY" = true ]; then
  echo -e "${BLUE}Running integration tests only...${NC}"
  PYTEST_CMD="$PYTEST_CMD -m integration"
else
  echo -e "${BLUE}Running all tests...${NC}"
fi

# Override coverage report options if quick mode
if [ "$QUICK" = true ]; then
  echo -e "${YELLOW}Quick mode: Skipping HTML report${NC}"
  PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing --cov-report=xml --no-cov-on-fail"
fi

# Override threshold if requested
if [ "$NO_THRESHOLD" = true ]; then
  echo -e "${YELLOW}Skipping coverage threshold check${NC}"
  # Add flag to skip threshold (will need to override pytest.ini setting)
  export PYTEST_ADDOPTS="--override-ini=addopts="
fi

echo ""
echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
echo ""

# Run tests with coverage
if $PYTEST_CMD; then
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}✓ Tests passed!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""

  # Show coverage report locations
  if [ "$QUICK" = false ]; then
    if [ -d "htmlcov" ]; then
      echo -e "${BLUE}Coverage Reports Generated:${NC}"
      echo -e "  📊 HTML Report:  htmlcov/index.html"
      echo -e "  📄 XML Report:   coverage.xml"
      echo -e "  📋 JSON Report:  coverage.json"
      echo ""
      echo -e "${YELLOW}To view the HTML report, run:${NC}"
      echo -e "  open htmlcov/index.html"
      echo ""
    fi
  fi

  exit 0
else
  EXIT_CODE=$?
  echo ""
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}✗ Tests failed!${NC}"
  echo -e "${RED}========================================${NC}"
  echo ""

  if [ $EXIT_CODE -eq 2 ]; then
    echo -e "${YELLOW}Coverage threshold not met (minimum: 80%)${NC}"
    echo -e "${YELLOW}Run with --no-threshold to skip this check${NC}"
  fi

  exit $EXIT_CODE
fi
