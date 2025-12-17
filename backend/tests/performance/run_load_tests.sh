#!/bin/bash
# Load testing runner script for TherapyBridge Backend
#
# Usage:
#   ./run_load_tests.sh [test_type] [options]
#
# Test types:
#   quick     - Quick baseline test (5 users, 1 minute)
#   moderate  - Moderate load test (20 users, 5 minutes)
#   heavy     - Heavy load test (50 users, 10 minutes)
#   stress    - Stress test (100 users, 15 minutes)
#   pytest    - Run pytest-based load tests
#   all       - Run all pytest scenarios
#
# Examples:
#   ./run_load_tests.sh quick
#   ./run_load_tests.sh pytest
#   ./run_load_tests.sh heavy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_BASE_URL:-http://localhost:8000}"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${TEST_DIR}/results"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Check if backend is running
check_backend() {
    echo -e "${BLUE}Checking if backend is running...${NC}"

    if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Backend is not running at ${API_URL}${NC}"
        echo -e "${YELLOW}Start the backend with: uvicorn app.main:app --reload${NC}"
        exit 1
    fi

    echo -e "${GREEN}Backend is running ✓${NC}"
}

# Check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"

    local missing=0

    if ! python -c "import locust" 2>/dev/null; then
        echo -e "${RED}locust not installed${NC}"
        missing=1
    fi

    if ! python -c "import pytest" 2>/dev/null; then
        echo -e "${RED}pytest not installed${NC}"
        missing=1
    fi

    if ! python -c "import psutil" 2>/dev/null; then
        echo -e "${RED}psutil not installed${NC}"
        missing=1
    fi

    if [ $missing -eq 1 ]; then
        echo -e "${YELLOW}Install missing dependencies with:${NC}"
        echo "pip install locust pytest-xdist httpx psutil pytest-asyncio"
        exit 1
    fi

    echo -e "${GREEN}All dependencies installed ✓${NC}"
}

# Run locust test
run_locust() {
    local users=$1
    local spawn_rate=$2
    local duration=$3
    local test_name=$4

    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Running Locust Load Test: ${test_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Users: ${users}"
    echo -e "Spawn rate: ${spawn_rate}/sec"
    echo -e "Duration: ${duration}"
    echo -e "Target: ${API_URL}\n"

    locust -f "${TEST_DIR}/load_test.py" \
        --host="${API_URL}" \
        --users "${users}" \
        --spawn-rate "${spawn_rate}" \
        --run-time "${duration}" \
        --headless \
        --html "${RESULTS_DIR}/locust_${test_name}_$(date +%Y%m%d_%H%M%S).html" \
        --csv "${RESULTS_DIR}/locust_${test_name}_$(date +%Y%m%d_%H%M%S)"

    echo -e "\n${GREEN}Test completed ✓${NC}"
}

# Run pytest tests
run_pytest() {
    local workers=${1:-10}
    local test_name=${2:-}

    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Running Pytest Load Tests${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Workers: ${workers}"
    echo -e "Target: ${API_URL}\n"

    if [ -n "${test_name}" ]; then
        pytest "${TEST_DIR}/pytest_load_test.py::${test_name}" -n "${workers}" -v -s
    else
        pytest "${TEST_DIR}/pytest_load_test.py" -n "${workers}" -v -s
    fi

    echo -e "\n${GREEN}Tests completed ✓${NC}"
}

# Print usage
usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 [test_type] [options]"
    echo ""
    echo -e "${BLUE}Test types:${NC}"
    echo "  quick     - Quick baseline test (5 users, 1 minute)"
    echo "  moderate  - Moderate load test (20 users, 5 minutes)"
    echo "  heavy     - Heavy load test (50 users, 10 minutes)"
    echo "  stress    - Stress test (100 users, 15 minutes)"
    echo "  pytest    - Run pytest-based load tests"
    echo "  all       - Run all pytest scenarios"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 quick"
    echo "  $0 pytest"
    echo "  $0 heavy"
}

# Main execution
main() {
    local test_type="${1:-quick}"

    # Show header
    echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  TherapyBridge Load Testing Suite     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

    # Pre-flight checks
    check_backend
    check_dependencies

    # Run selected test
    case "${test_type}" in
        quick)
            run_locust 5 1 "1m" "quick"
            ;;
        moderate)
            run_locust 20 2 "5m" "moderate"
            ;;
        heavy)
            run_locust 50 5 "10m" "heavy"
            ;;
        stress)
            run_locust 100 10 "15m" "stress"
            ;;
        pytest)
            run_pytest 10
            ;;
        all)
            echo -e "${BLUE}Running all pytest scenarios...${NC}\n"
            run_pytest 10 "test_concurrent_health_checks"
            run_pytest 20 "test_concurrent_sessions"
            run_pytest 10 "test_concurrent_uploads"
            run_pytest 1 "test_rate_limit_enforcement"
            run_pytest 50 "test_database_pool_stress"
            run_pytest 10 "test_sustained_load"
            run_pytest 1 "test_memory_leak_detection"
            ;;
        help|-h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown test type: ${test_type}${NC}\n"
            usage
            exit 1
            ;;
    esac

    # Show results location
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Results saved to:${NC}"
    echo -e "${RESULTS_DIR}"
    echo -e "${GREEN}========================================${NC}\n"
}

# Run main function
main "$@"
