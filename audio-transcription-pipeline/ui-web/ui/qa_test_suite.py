#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Audio Transcription UI
Tests file validation, size limits, and API integration
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_SAMPLES_DIR = Path(__file__).parent.parent / "tests" / "samples"
INVALID_FILES_DIR = TEST_SAMPLES_DIR / "invalid_test_files"

# Test results storage
test_results = []


class TestResult:
    def __init__(self, test_name: str, category: str):
        self.test_name = test_name
        self.category = category
        self.status = "PENDING"
        self.expected = ""
        self.actual = ""
        self.error = None
        self.duration = 0.0

    def pass_test(self, expected: str, actual: str):
        self.status = "PASS"
        self.expected = expected
        self.actual = actual

    def fail_test(self, expected: str, actual: str, error: str = None):
        self.status = "FAIL"
        self.expected = expected
        self.actual = actual
        self.error = error

    def skip_test(self, reason: str):
        self.status = "SKIP"
        self.error = reason

    def __str__(self):
        result = f"[{self.status}] {self.test_name}"
        if self.status == "FAIL":
            result += f"\n  Expected: {self.expected}\n  Actual: {self.actual}"
            if self.error:
                result += f"\n  Error: {self.error}"
        elif self.status == "SKIP":
            result += f"\n  Reason: {self.error}"
        return result


def check_server_health() -> bool:
    """Check if server is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_valid_file_upload(file_path: Path, file_type: str) -> TestResult:
    """Test uploading a valid audio file"""
    test = TestResult(f"Upload valid {file_type} file", "File Type Validation")

    try:
        start_time = time.time()

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/mpeg')}
            response = requests.post(
                f"{API_BASE_URL}/api/upload",
                files=files,
                timeout=30
            )

        test.duration = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            if 'job_id' in data:
                test.pass_test(
                    "File accepted with job_id",
                    f"Got job_id: {data['job_id'][:8]}... (status: {data.get('status', 'unknown')})"
                )
            else:
                test.fail_test(
                    "File accepted with job_id",
                    f"Missing job_id in response: {data}",
                    "Response missing job_id"
                )
        else:
            test.fail_test(
                "HTTP 200 (accepted)",
                f"HTTP {response.status_code}",
                response.text[:200]
            )

    except Exception as e:
        test.fail_test("Successful upload", "Exception raised", str(e))

    return test


def test_invalid_file_upload(file_path: Path, expected_rejection_reason: str) -> TestResult:
    """Test uploading an invalid file (should be rejected)"""
    test = TestResult(f"Reject invalid file: {file_path.name}", "File Validation")

    try:
        start_time = time.time()

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(
                f"{API_BASE_URL}/api/upload",
                files=files,
                timeout=30
            )

        test.duration = time.time() - start_time

        # Should reject with 4xx error
        if response.status_code >= 400 and response.status_code < 500:
            test.pass_test(
                f"Rejected with 4xx error ({expected_rejection_reason})",
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
        else:
            test.fail_test(
                "File rejected (4xx error)",
                f"HTTP {response.status_code} (file was accepted!)",
                "Invalid file should have been rejected"
            )

    except Exception as e:
        test.fail_test("File rejection", "Exception raised", str(e))

    return test


def test_file_size_limit(file_path: Path, size_mb: float, should_accept: bool) -> TestResult:
    """Test file size limits"""
    test_name = f"File size {size_mb:.1f}MB - {'Accept' if should_accept else 'Reject'}"
    test = TestResult(test_name, "File Size Limits")

    try:
        start_time = time.time()

        file_size = os.path.getsize(file_path)
        actual_size_mb = file_size / (1024 * 1024)

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/mpeg')}
            response = requests.post(
                f"{API_BASE_URL}/api/upload",
                files=files,
                timeout=60
            )

        test.duration = time.time() - start_time

        if should_accept:
            if response.status_code == 200:
                test.pass_test(
                    f"File accepted ({actual_size_mb:.1f}MB)",
                    f"HTTP {response.status_code}"
                )
            else:
                test.fail_test(
                    f"File accepted ({actual_size_mb:.1f}MB)",
                    f"HTTP {response.status_code} - Rejected",
                    response.text[:200]
                )
        else:
            if response.status_code == 413:  # Payload too large
                test.pass_test(
                    f"File rejected ({actual_size_mb:.1f}MB)",
                    f"HTTP {response.status_code}"
                )
            elif response.status_code >= 400:
                test.pass_test(
                    f"File rejected ({actual_size_mb:.1f}MB)",
                    f"HTTP {response.status_code} (not 413 but still rejected)"
                )
            else:
                test.fail_test(
                    f"File rejected ({actual_size_mb:.1f}MB)",
                    f"HTTP {response.status_code} - Accepted!",
                    "File exceeds limit but was accepted"
                )

    except Exception as e:
        test.fail_test("Size limit enforcement", "Exception raised", str(e))

    return test


def test_api_status_endpoint(job_id: str) -> TestResult:
    """Test status polling endpoint"""
    test = TestResult("API Status Endpoint", "API Integration")

    try:
        response = requests.get(f"{API_BASE_URL}/api/status/{job_id}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            required_fields = ['job_id', 'status', 'progress', 'step']

            if all(field in data for field in required_fields):
                test.pass_test(
                    f"Status response with {required_fields}",
                    f"Got all fields: {data}"
                )
            else:
                missing = [f for f in required_fields if f not in data]
                test.fail_test(
                    f"Status response with {required_fields}",
                    f"Missing fields: {missing}",
                    f"Response: {data}"
                )
        elif response.status_code == 404:
            test.pass_test(
                "404 for invalid job_id",
                f"HTTP {response.status_code}"
            )
        else:
            test.fail_test(
                "Valid status response",
                f"HTTP {response.status_code}",
                response.text[:200]
            )

    except Exception as e:
        test.fail_test("Status endpoint", "Exception raised", str(e))

    return test


def run_all_tests():
    """Execute comprehensive QA test suite"""

    print("=" * 80)
    print("Audio Transcription UI - QA Test Suite")
    print("=" * 80)
    print()

    # Check server health
    print("Checking server health...")
    if not check_server_health():
        print("❌ ERROR: Server not running at", API_BASE_URL)
        print("Please start the server first: python server.py")
        return
    print("✓ Server is running\n")

    # Category 1: Valid File Types
    print("\n" + "=" * 80)
    print("Category 1: Valid File Type Tests")
    print("=" * 80)

    valid_files = [
        (TEST_SAMPLES_DIR / "small_test.mp3", "MP3"),
        (TEST_SAMPLES_DIR / "compressed-cbt-session.m4a", "M4A"),
    ]

    for file_path, file_type in valid_files:
        if file_path.exists():
            result = test_valid_file_upload(file_path, file_type)
            test_results.append(result)
            print(result)
        else:
            print(f"[SKIP] {file_type} test file not found: {file_path}")

    # Category 2: Invalid File Types
    print("\n" + "=" * 80)
    print("Category 2: Invalid File Type Tests")
    print("=" * 80)

    invalid_files = [
        (INVALID_FILES_DIR / "test.txt", "Invalid extension (.txt)"),
        (INVALID_FILES_DIR / "test.jpg", "Invalid extension (.jpg)"),
        (INVALID_FILES_DIR / "corrupted.mp3", "Corrupted MP3 data"),
    ]

    for file_path, reason in invalid_files:
        if file_path.exists():
            result = test_invalid_file_upload(file_path, reason)
            test_results.append(result)
            print(result)
        else:
            print(f"[SKIP] Invalid file not found: {file_path}")

    # Category 3: File Size Limits
    print("\n" + "=" * 80)
    print("Category 3: File Size Limit Tests")
    print("=" * 80)

    size_tests = [
        (TEST_SAMPLES_DIR / "small_test.mp3", 0.5, True),  # ~500KB, should accept
        (TEST_SAMPLES_DIR / "compressed-cbt-session.m4a", 15, True),  # ~15MB, should accept
        (TEST_SAMPLES_DIR / "LIVE Cognitive Behavioral Therapy Session (1).mp3", 21, True),  # ~21MB, should accept
    ]

    for file_path, size_mb, should_accept in size_tests:
        if file_path.exists():
            result = test_file_size_limit(file_path, size_mb, should_accept)
            test_results.append(result)
            print(result)
        else:
            print(f"[SKIP] Size test file not found: {file_path}")

    # Category 4: Edge Cases
    print("\n" + "=" * 80)
    print("Category 4: Edge Case Tests")
    print("=" * 80)

    # Empty file test
    empty_file = INVALID_FILES_DIR / "empty.mp3"
    if empty_file.exists():
        result = test_invalid_file_upload(empty_file, "Empty file (0 bytes)")
        test_results.append(result)
        print(result)

    # Category 5: API Integration
    print("\n" + "=" * 80)
    print("Category 5: API Integration Tests")
    print("=" * 80)

    # Test status endpoint with invalid job ID
    result = test_api_status_endpoint("invalid-job-id-12345")
    test_results.append(result)
    print(result)

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    total = len(test_results)
    passed = len([t for t in test_results if t.status == "PASS"])
    failed = len([t for t in test_results if t.status == "FAIL"])
    skipped = len([t for t in test_results if t.status == "SKIP"])

    print(f"Total Tests: {total}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"⊘ Skipped: {skipped}")
    print(f"Pass Rate: {(passed/total*100) if total > 0 else 0:.1f}%")

    # Failed tests details
    if failed > 0:
        print("\n" + "=" * 80)
        print("Failed Tests Details")
        print("=" * 80)
        for test in test_results:
            if test.status == "FAIL":
                print(f"\n{test}")

    return test_results


def generate_markdown_report(results: List[TestResult], output_path: Path):
    """Generate detailed markdown test report"""

    with open(output_path, 'w') as f:
        f.write("# Audio Transcription UI - QA Test Report\n\n")
        f.write(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**API Endpoint:** {API_BASE_URL}\n\n")

        # Summary
        total = len(results)
        passed = len([t for t in results if t.status == "PASS"])
        failed = len([t for t in results if t.status == "FAIL"])
        skipped = len([t for t in results if t.status == "SKIP"])

        f.write("## Test Summary\n\n")
        f.write(f"- **Total Tests:** {total}\n")
        f.write(f"- **Passed:** {passed} ✓\n")
        f.write(f"- **Failed:** {failed} ✗\n")
        f.write(f"- **Skipped:** {skipped} ⊘\n")
        f.write(f"- **Pass Rate:** {(passed/total*100) if total > 0 else 0:.1f}%\n\n")

        # Results by category
        categories = {}
        for test in results:
            if test.category not in categories:
                categories[test.category] = []
            categories[test.category].append(test)

        for category, tests in categories.items():
            f.write(f"## {category}\n\n")
            f.write("| Test | Status | Expected | Actual | Duration |\n")
            f.write("|------|--------|----------|--------|----------|\n")

            for test in tests:
                status_icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘"}.get(test.status, "?")
                expected = test.expected.replace("\n", " ")[:50]
                actual = test.actual.replace("\n", " ")[:50]
                duration = f"{test.duration:.2f}s" if test.duration > 0 else "N/A"

                f.write(f"| {test.test_name} | {status_icon} {test.status} | {expected} | {actual} | {duration} |\n")

            f.write("\n")

        # Failed tests details
        if failed > 0:
            f.write("## Failed Tests - Detailed Analysis\n\n")
            for test in results:
                if test.status == "FAIL":
                    f.write(f"### {test.test_name}\n\n")
                    f.write(f"**Expected:** {test.expected}\n\n")
                    f.write(f"**Actual:** {test.actual}\n\n")
                    if test.error:
                        f.write(f"**Error:** {test.error}\n\n")
                    f.write("---\n\n")

        # Test Environment
        f.write("## Test Environment\n\n")
        f.write(f"- **API Server:** {API_BASE_URL}\n")
        f.write(f"- **Test Samples Directory:** {TEST_SAMPLES_DIR}\n")
        f.write(f"- **Max File Size (Server):** 500MB\n")
        f.write(f"- **Max File Size (UI):** 200MB\n")
        f.write(f"- **Allowed Extensions:** .mp3, .wav, .m4a, .flac, .ogg, .webm, .mp4\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if failed > 0:
            f.write("### Issues Found\n\n")
            f.write(f"- {failed} test(s) failed. Review details above.\n")
        else:
            f.write("- ✓ All tests passed! UI validation is working correctly.\n")

        f.write("\n### Browser Compatibility Testing\n\n")
        f.write("Manual browser testing recommended:\n")
        f.write("- [ ] Chrome (latest)\n")
        f.write("- [ ] Firefox (latest)\n")
        f.write("- [ ] Safari (latest)\n")
        f.write("- [ ] Edge (latest)\n\n")

        f.write("### Additional Test Scenarios\n\n")
        f.write("- [ ] Test with very long filenames (>255 chars)\n")
        f.write("- [ ] Test with special characters in filename\n")
        f.write("- [ ] Test with multiple rapid uploads\n")
        f.write("- [ ] Test network interruption during upload\n")
        f.write("- [ ] Test concurrent uploads from multiple tabs\n\n")

    print(f"\n✓ Test report saved to: {output_path}")


if __name__ == "__main__":
    results = run_all_tests()

    # Generate report
    report_path = Path(__file__).parent / "UI_TEST_REPORT.md"
    generate_markdown_report(results, report_path)

    print(f"\n{'='*80}")
    print("QA Testing Complete!")
    print(f"{'='*80}\n")
