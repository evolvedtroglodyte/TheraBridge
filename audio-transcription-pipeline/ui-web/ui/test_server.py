#!/usr/bin/env python3
"""
Test script for the FastAPI server

Tests all API endpoints without actually running the GPU pipeline
"""

import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")


def test_upload_invalid_file():
    """Test upload with invalid file type"""
    print_section("Testing Upload with Invalid File Type")

    # Create a dummy text file
    dummy_file = Path("test.txt")
    dummy_file.write_text("This is not an audio file")

    try:
        with open(dummy_file, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            response = requests.post(f"{API_URL}/upload", files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 400
        print("✅ Invalid file type correctly rejected")

    finally:
        dummy_file.unlink()


def test_upload_valid_file():
    """Test upload with valid audio file (mock)"""
    print_section("Testing Upload with Valid Audio File")

    # Create a dummy MP3 file (just for testing - won't actually process)
    dummy_audio = Path("test_audio.mp3")
    dummy_audio.write_bytes(b"FAKE_AUDIO_DATA" * 1000)

    try:
        with open(dummy_audio, 'rb') as f:
            files = {'file': ('test_audio.mp3', f, 'audio/mpeg')}
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                params={'num_speakers': 2}
            )

        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")

        assert response.status_code == 200
        assert 'job_id' in data
        print(f"✅ Upload accepted. Job ID: {data['job_id']}")

        return data['job_id']

    finally:
        dummy_audio.unlink()


def test_status(job_id):
    """Test status endpoint"""
    print_section(f"Testing Status for Job {job_id}")

    response = requests.get(f"{API_URL}/status/{job_id}")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")

    assert response.status_code == 200
    assert data['job_id'] == job_id
    assert 'status' in data
    assert 'progress' in data
    print(f"✅ Status retrieved: {data['status']} ({data['progress']}%)")

    return data['status']


def test_status_not_found():
    """Test status endpoint with invalid job ID"""
    print_section("Testing Status with Invalid Job ID")

    response = requests.get(f"{API_URL}/status/invalid-job-id")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 404
    print("✅ Invalid job ID correctly rejected")


def test_list_jobs():
    """Test list jobs endpoint"""
    print_section("Testing List Jobs")

    response = requests.get(f"{API_URL}/jobs")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Jobs: {data['total']}")
    print(f"Jobs: {data['jobs']}")

    assert response.status_code == 200
    print("✅ Jobs list retrieved")


def test_delete_job(job_id):
    """Test delete job endpoint"""
    print_section(f"Testing Delete Job {job_id}")

    response = requests.delete(f"{API_URL}/jobs/{job_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    print("✅ Job deleted successfully")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("GPU Pipeline Server API Tests")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  python server.py")
    print("\nPress Enter to continue...")
    input()

    try:
        # Test 1: Health check
        test_health_check()

        # Test 2: Invalid file upload
        test_upload_invalid_file()

        # Test 3: Valid file upload
        job_id = test_upload_valid_file()

        # Wait a moment for processing to start
        time.sleep(1)

        # Test 4: Check status
        test_status(job_id)

        # Test 5: List all jobs
        test_list_jobs()

        # Test 6: Invalid job status
        test_status_not_found()

        # Test 7: Delete job
        test_delete_job(job_id)

        # Final summary
        print_section("Test Summary")
        print("✅ All tests passed!")
        print("\nNote: These tests verify API endpoints only.")
        print("The pipeline execution will fail because we uploaded fake audio.")
        print("To test full pipeline integration, upload a real audio file via the UI.")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("Make sure the server is running: python server.py")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
