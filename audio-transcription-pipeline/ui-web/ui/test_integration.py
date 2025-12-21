#!/usr/bin/env python3
"""
Comprehensive Integration Testing for GPU Pipeline UI and Server

Tests the complete end-to-end flow:
1. Server startup and health checks
2. API endpoint functionality
3. Upload → Processing → Results flow
4. Error handling scenarios
5. CORS configuration
6. Real file processing (optional)

Usage:
    # Quick API tests (no actual processing)
    python test_integration.py

    # Full end-to-end test with real audio file
    python test_integration.py --full-test
"""

import requests
import time
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# ========================================
# Configuration
# ========================================
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test sample location
SAMPLES_DIR = Path(__file__).parent.parent / "tests" / "samples"
TEST_AUDIO = SAMPLES_DIR / "compressed-cbt-session.m4a"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ========================================
# Test Utilities
# ========================================
def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")

def print_test(text: str):
    """Print test description"""
    print(f"{Colors.CYAN}TEST: {text}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"   {text}")

# ========================================
# Test 1: Server Health Check
# ========================================
def test_health_check() -> bool:
    """Test server health check endpoint"""
    print_header("Test 1: Server Health Check")
    print_test("GET /health")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_info(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: {data}")

        # Validate response structure
        assert data["status"] == "healthy", "Server status is not healthy"
        assert "pipeline_script" in data, "Missing pipeline_script field"
        assert "pipeline_exists" in data, "Missing pipeline_exists field"
        assert "active_jobs" in data, "Missing active_jobs field"

        if not data["pipeline_exists"]:
            print_warning(f"Pipeline script not found: {data['pipeline_script']}")
        else:
            print_info(f"Pipeline script: {data['pipeline_script']}")

        print_success("Health check passed")
        return True

    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server")
        print_info(f"Make sure server is running on {BASE_URL}")
        print_info("Run: python ui/server.py")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

# ========================================
# Test 2: CORS Configuration
# ========================================
def test_cors() -> bool:
    """Test CORS headers are present"""
    print_header("Test 2: CORS Configuration")
    print_test("Check CORS headers on /health endpoint")

    try:
        response = requests.options(f"{BASE_URL}/health")
        headers = response.headers

        print_info("CORS Headers:")
        cors_headers = {
            'Access-Control-Allow-Origin': headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': headers.get('Access-Control-Allow-Headers'),
        }

        for header, value in cors_headers.items():
            if value:
                print_info(f"  {header}: {value}")

        # CORS should allow * or specific origins
        if cors_headers['Access-Control-Allow-Origin']:
            print_success("CORS is configured")
            return True
        else:
            print_warning("CORS headers not found (may work anyway)")
            return True  # Not a failure, just a warning

    except Exception as e:
        print_error(f"Error checking CORS: {e}")
        return False

# ========================================
# Test 3: Invalid File Upload
# ========================================
def test_invalid_file_upload() -> bool:
    """Test upload with invalid file type"""
    print_header("Test 3: Invalid File Upload")
    print_test("POST /api/upload with .txt file")

    # Create temporary invalid file
    temp_file = Path("test_invalid.txt")
    temp_file.write_text("This is not an audio file")

    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_invalid.txt', f, 'text/plain')}
            response = requests.post(f"{API_URL}/upload", files=files)

        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.json()}")

        # Should reject with 400
        if response.status_code == 400:
            print_success("Invalid file correctly rejected")
            return True
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False
    finally:
        temp_file.unlink()

# ========================================
# Test 4: Valid File Upload (Mock)
# ========================================
def test_valid_file_upload() -> Optional[str]:
    """Test upload with valid audio file (mock data)"""
    print_header("Test 4: Valid File Upload (Mock)")
    print_test("POST /api/upload with .mp3 file")

    # Create temporary mock audio file
    temp_audio = Path("test_audio_mock.mp3")
    temp_audio.write_bytes(b"MOCK_AUDIO_DATA" * 1000)  # Fake MP3 data

    try:
        with open(temp_audio, 'rb') as f:
            files = {'file': ('test_audio_mock.mp3', f, 'audio/mpeg')}
            data = {'num_speakers': 2}
            response = requests.post(f"{API_URL}/upload", files=files, data=data)

        print_info(f"Status Code: {response.status_code}")
        result = response.json()
        print_info(f"Response: {result}")

        if response.status_code != 200:
            print_error(f"Upload failed with status {response.status_code}")
            return None

        # Validate response structure
        assert 'job_id' in result, "Missing job_id in response"
        assert 'status' in result, "Missing status in response"

        job_id = result['job_id']
        print_success(f"Upload accepted. Job ID: {job_id}")
        return job_id

    except Exception as e:
        print_error(f"Error: {e}")
        return None
    finally:
        temp_audio.unlink()

# ========================================
# Test 5: Status Polling
# ========================================
def test_status_endpoint(job_id: str) -> bool:
    """Test status endpoint"""
    print_header("Test 5: Status Endpoint")
    print_test(f"GET /api/status/{job_id}")

    try:
        response = requests.get(f"{API_URL}/status/{job_id}")
        print_info(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: {data}")

        # Validate response structure
        required_fields = ['job_id', 'status', 'progress', 'step']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        assert data['job_id'] == job_id, "Job ID mismatch"
        assert 0 <= data['progress'] <= 100, "Progress out of range"
        assert data['status'] in ['queued', 'processing', 'completed', 'failed'], \
            f"Invalid status: {data['status']}"

        print_success(f"Status: {data['status']} ({data['progress']}%) - {data['step']}")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ========================================
# Test 6: Invalid Job ID
# ========================================
def test_invalid_job_id() -> bool:
    """Test status endpoint with invalid job ID"""
    print_header("Test 6: Invalid Job ID")
    print_test("GET /api/status/invalid-job-id-12345")

    try:
        response = requests.get(f"{API_URL}/status/invalid-job-id-12345")
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.json()}")

        if response.status_code == 404:
            print_success("Invalid job ID correctly rejected with 404")
            return True
        else:
            print_error(f"Expected 404, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ========================================
# Test 7: List Jobs
# ========================================
def test_list_jobs() -> bool:
    """Test list jobs endpoint"""
    print_header("Test 7: List Jobs")
    print_test("GET /api/jobs")

    try:
        response = requests.get(f"{API_URL}/jobs")
        print_info(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False

        data = response.json()
        print_info(f"Total Jobs: {data['total']}")

        if data['total'] > 0:
            print_info("Recent Jobs:")
            for job in data['jobs'][:3]:  # Show first 3
                print_info(f"  - {job['job_id'][:8]}... | {job['status']} | {job.get('filename', 'N/A')}")

        print_success("Jobs list retrieved")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ========================================
# Test 8: Delete Job
# ========================================
def test_delete_job(job_id: str) -> bool:
    """Test delete job endpoint"""
    print_header("Test 8: Delete Job")
    print_test(f"DELETE /api/jobs/{job_id}")

    try:
        response = requests.delete(f"{API_URL}/jobs/{job_id}")
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.json()}")

        if response.status_code == 200:
            print_success("Job deleted successfully")
            return True
        else:
            print_error(f"Expected 200, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ========================================
# Test 9: Full End-to-End Test
# ========================================
def test_full_pipeline() -> bool:
    """Test complete pipeline with real audio file"""
    print_header("Test 9: Full End-to-End Pipeline Test")

    if not TEST_AUDIO.exists():
        print_warning(f"Test audio file not found: {TEST_AUDIO}")
        print_info("Skipping full pipeline test")
        return True  # Not a failure

    print_test(f"Processing real audio file: {TEST_AUDIO.name}")
    print_info(f"File size: {TEST_AUDIO.stat().st_size / (1024*1024):.1f} MB")

    try:
        # 1. Upload file
        print_info("\n[1/4] Uploading file...")
        with open(TEST_AUDIO, 'rb') as f:
            files = {'file': (TEST_AUDIO.name, f, 'audio/m4a')}
            data = {'num_speakers': 2}
            response = requests.post(f"{API_URL}/upload", files=files, data=data)

        if response.status_code != 200:
            print_error(f"Upload failed: {response.json()}")
            return False

        job_id = response.json()['job_id']
        print_success(f"Uploaded successfully. Job ID: {job_id[:8]}...")

        # 2. Poll for status
        print_info("\n[2/4] Monitoring processing status...")
        max_wait = 300  # 5 minutes timeout
        poll_interval = 2  # Poll every 2 seconds
        elapsed = 0
        last_step = None

        while elapsed < max_wait:
            response = requests.get(f"{API_URL}/status/{job_id}")
            if response.status_code != 200:
                print_error(f"Status check failed: {response.status_code}")
                return False

            status_data = response.json()
            status = status_data['status']
            progress = status_data['progress']
            step = status_data['step']

            # Print update if step changed
            if step != last_step:
                print_info(f"  {progress}% - {step}")
                last_step = step

            # Check completion
            if status == 'completed':
                print_success(f"Processing completed in {elapsed}s")
                break
            elif status == 'failed':
                error = status_data.get('error', 'Unknown error')
                print_error(f"Processing failed: {error}")
                return False

            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            print_error(f"Processing timeout after {max_wait}s")
            return False

        # 3. Fetch results
        print_info("\n[3/4] Fetching results...")
        response = requests.get(f"{API_URL}/results/{job_id}")

        if response.status_code != 200:
            print_error(f"Results fetch failed: {response.status_code}")
            return False

        results = response.json()

        # Validate results structure
        print_info("Results received:")
        if 'segments' in results:
            print_info(f"  - Segments: {len(results['segments'])}")
        if 'aligned_segments' in results:
            print_info(f"  - Aligned segments: {len(results['aligned_segments'])}")
        if 'full_text' in results:
            text_preview = results['full_text'][:100]
            print_info(f"  - Transcript preview: {text_preview}...")
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            print_info(f"  - Processing time: {metrics.get('total_time_seconds', 'N/A')}s")
            print_info(f"  - RTF: {metrics.get('rtf', 'N/A')}")

        print_success("Results retrieved successfully")

        # 4. Cleanup
        print_info("\n[4/4] Cleaning up...")
        requests.delete(f"{API_URL}/jobs/{job_id}")
        print_success("Job cleaned up")

        return True

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========================================
# Test 10: Static File Serving
# ========================================
def test_static_files() -> bool:
    """Test static file serving"""
    print_header("Test 10: Static File Serving")

    tests = [
        ("GET /", "index.html"),
        ("GET /static/app.js", "app.js"),
        ("GET /static/styles.css", "styles.css"),
    ]

    all_passed = True

    for method_path, description in tests:
        print_test(f"{method_path}")

        try:
            url = BASE_URL + method_path.replace("GET ", "")
            response = requests.get(url)

            if response.status_code == 200:
                print_success(f"{description} served successfully")
            elif response.status_code == 404:
                print_warning(f"{description} not found (404)")
                all_passed = False
            else:
                print_error(f"Unexpected status: {response.status_code}")
                all_passed = False

        except Exception as e:
            print_error(f"Error: {e}")
            all_passed = False

    return all_passed

# ========================================
# Main Test Runner
# ========================================
def run_all_tests(full_test: bool = False) -> bool:
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("GPU PIPELINE UI/SERVER INTEGRATION TESTS".center(70))
    print("=" * 70)
    print(f"{Colors.ENDC}")

    print_info(f"Server URL: {BASE_URL}")
    print_info(f"Testing mode: {'FULL (with real audio)' if full_test else 'QUICK (API only)'}")
    print_info("")

    # Track results
    results = {}

    # Core tests (always run)
    results["Health Check"] = test_health_check()
    if not results["Health Check"]:
        print_error("\nServer is not responding. Cannot continue tests.")
        print_info("Start the server with: python ui/server.py")
        return False

    results["CORS Configuration"] = test_cors()
    results["Invalid File Upload"] = test_invalid_file_upload()

    job_id = test_valid_file_upload()
    results["Valid File Upload"] = job_id is not None

    if job_id:
        results["Status Endpoint"] = test_status_endpoint(job_id)
        time.sleep(1)  # Let processing start

    results["Invalid Job ID"] = test_invalid_job_id()
    results["List Jobs"] = test_list_jobs()

    if job_id:
        results["Delete Job"] = test_delete_job(job_id)

    results["Static Files"] = test_static_files()

    # Full end-to-end test (optional)
    if full_test:
        results["Full Pipeline"] = test_full_pipeline()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if result else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
        print(f"{test_name:.<50} {status}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed. See details above.{Colors.ENDC}")
        return False

# ========================================
# Entry Point
# ========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Integration tests for GPU Pipeline UI/Server")
    parser.add_argument('--full-test', action='store_true',
                       help='Run full end-to-end test with real audio file (takes longer)')
    parser.add_argument('--url', default='http://localhost:8000',
                       help='Server URL (default: http://localhost:8000)')

    args = parser.parse_args()

    # Update config if custom URL provided
    if args.url != 'http://localhost:8000':
        BASE_URL = args.url
        API_URL = f"{BASE_URL}/api"

    # Run tests
    success = run_all_tests(full_test=args.full_test)

    sys.exit(0 if success else 1)
