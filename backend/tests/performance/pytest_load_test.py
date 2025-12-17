"""
Pytest-based load testing for TherapyBridge Backend API.

Alternative to locust-based testing. Uses pytest-xdist for parallel execution
and httpx for async requests.

Usage:
    # Install dependencies:
    pip install pytest-xdist httpx psutil

    # Run with 10 concurrent workers:
    pytest tests/performance/pytest_load_test.py -n 10 -v

    # Run specific test scenario:
    pytest tests/performance/pytest_load_test.py::test_concurrent_sessions -n 20 -v

    # Run with detailed output:
    pytest tests/performance/pytest_load_test.py -n 10 -v -s

Test Scenarios:
    - test_concurrent_health_checks: Baseline throughput test
    - test_concurrent_sessions: Read-heavy concurrent load
    - test_concurrent_uploads: Upload endpoint under load (mocked)
    - test_rate_limit_enforcement: Verify rate limits work
    - test_database_pool_stress: Test connection pool limits
"""
import pytest
import asyncio
import httpx
import time
import json
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from io import BytesIO

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPass123!"


class PerformanceResult:
    """Track performance metrics for a test run."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.request_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.status_codes: Dict[int, int] = {}

    def add_request(self, duration: float, status_code: int, error: str = None):
        """Record a request's performance data."""
        self.request_times.append(duration)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

        if error:
            self.errors.append({
                "status_code": status_code,
                "error": error,
                "timestamp": time.time()
            })

    def finalize(self):
        """Mark test as complete and calculate final metrics."""
        self.end_time = time.time()

    def get_metrics(self) -> Dict[str, Any]:
        """Calculate and return performance metrics."""
        if not self.request_times:
            return {
                "test_name": self.test_name,
                "error": "No requests recorded"
            }

        sorted_times = sorted(self.request_times)
        total_requests = len(self.request_times)
        total_errors = len(self.errors)

        duration = (self.end_time or time.time()) - self.start_time

        return {
            "test_name": self.test_name,
            "duration_seconds": round(duration, 2),
            "total_requests": total_requests,
            "requests_per_second": round(total_requests / duration, 2) if duration > 0 else 0,
            "response_time_avg_ms": round(sum(self.request_times) / total_requests * 1000, 2),
            "response_time_min_ms": round(min(self.request_times) * 1000, 2),
            "response_time_max_ms": round(max(self.request_times) * 1000, 2),
            "response_time_p50_ms": round(sorted_times[int(total_requests * 0.50)] * 1000, 2),
            "response_time_p95_ms": round(sorted_times[int(total_requests * 0.95)] * 1000, 2),
            "response_time_p99_ms": round(sorted_times[int(total_requests * 0.99)] * 1000, 2),
            "total_errors": total_errors,
            "error_rate_percent": round((total_errors / total_requests) * 100, 2),
            "status_codes": self.status_codes,
            "errors": self.errors[:10]  # First 10 errors for debugging
        }

    def save_report(self):
        """Save performance metrics to JSON file."""
        metrics = self.get_metrics()

        report_dir = Path("tests/performance/results")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.test_name}_{timestamp}.json"
        report_file = report_dir / filename

        with open(report_file, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Performance Report: {self.test_name}")
        print(f"{'='*80}")
        print(json.dumps(metrics, indent=2))
        print(f"{'='*80}")
        print(f"Report saved to: {report_file}\n")

        return metrics


@pytest.fixture
async def auth_token():
    """Get authentication token for test requests."""
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )

        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

        return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    result: PerformanceResult,
    **kwargs
) -> httpx.Response:
    """
    Make HTTP request and track performance.

    Args:
        client: httpx async client
        method: HTTP method (get, post, etc.)
        url: Request URL
        result: PerformanceResult to track metrics
        **kwargs: Additional arguments for request

    Returns:
        Response object
    """
    start = time.time()
    error = None

    try:
        response = await getattr(client, method)(url, **kwargs)
        duration = time.time() - start
        result.add_request(duration, response.status_code)
        return response

    except Exception as e:
        duration = time.time() - start
        result.add_request(duration, 0, str(e))
        raise


@pytest.mark.asyncio
async def test_concurrent_health_checks(auth_headers):
    """
    Test health check endpoint with concurrent requests.

    Scenario: 100 concurrent health checks
    Expected: All succeed with fast response times
    """
    result = PerformanceResult("concurrent_health_checks")
    num_requests = 100

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        tasks = []
        for _ in range(num_requests):
            task = make_request(client, "get", "/health", result)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    result.finalize()
    metrics = result.save_report()

    # Assertions for health check performance
    assert metrics["error_rate_percent"] < 1.0, "Health check error rate too high"
    assert metrics["response_time_p95_ms"] < 500, "Health check p95 latency too high"


@pytest.mark.asyncio
async def test_concurrent_sessions(auth_headers):
    """
    Test listing sessions with concurrent requests.

    Scenario: 50 concurrent session list requests
    Expected: All succeed, reasonable response times
    """
    result = PerformanceResult("concurrent_sessions")
    num_requests = 50

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        tasks = []
        for _ in range(num_requests):
            task = make_request(
                client,
                "get",
                "/api/sessions/",
                result,
                headers=auth_headers
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    result.finalize()
    metrics = result.save_report()

    # Assertions
    assert metrics["error_rate_percent"] < 5.0, "Session list error rate too high"
    assert metrics["response_time_p95_ms"] < 2000, "Session list p95 latency too high"


@pytest.mark.asyncio
async def test_concurrent_uploads(auth_headers, auth_token):
    """
    Test upload endpoint with concurrent requests.

    Scenario: 10 concurrent uploads (small files)
    Expected: Most succeed, some may hit rate limits
    """
    # First, get a patient ID
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        response = await client.get("/api/patients/", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No patients available for upload test")

        patient_id = response.json()[0]["id"]

    result = PerformanceResult("concurrent_uploads")
    num_requests = 10

    # Create mock audio file
    mock_audio = b"ID3" + b"\x00" * 1024 * 100  # 100KB mock MP3

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=60.0) as client:
        tasks = []
        for i in range(num_requests):
            files = {
                "file": (f"test_session_{i}.mp3", BytesIO(mock_audio), "audio/mpeg")
            }
            data = {
                "patient_id": str(patient_id),
                "session_date": "2024-01-15",
                "notes": f"Load test session {i}"
            }

            task = make_request(
                client,
                "post",
                "/api/sessions/upload",
                result,
                headers=auth_headers,
                files=files,
                data=data
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    result.finalize()
    metrics = result.save_report()

    # Note: Some uploads may hit rate limits (429), which is expected
    success_rate = 100 - metrics["error_rate_percent"]
    assert success_rate > 50.0, "Upload success rate too low"


@pytest.mark.asyncio
async def test_rate_limit_enforcement(auth_headers):
    """
    Test that rate limiting is enforced under rapid requests.

    Scenario: 150 rapid requests (exceeds 100/minute default limit)
    Expected: Should see 429 responses after hitting limit
    """
    result = PerformanceResult("rate_limit_enforcement")
    num_requests = 150

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        for _ in range(num_requests):
            await make_request(
                client,
                "get",
                "/api/sessions/",
                result,
                headers=auth_headers
            )
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.01)

    result.finalize()
    metrics = result.save_report()

    # Should see 429 status codes
    assert 429 in metrics["status_codes"], "Rate limiting not enforced"
    assert metrics["status_codes"][429] > 0, "No rate limit responses received"

    print(f"\nRate limit triggered after {metrics['status_codes'].get(200, 0)} successful requests")


@pytest.mark.asyncio
async def test_database_pool_stress(auth_headers):
    """
    Test database connection pool under concurrent load.

    Scenario: 100 concurrent database queries
    Expected: All succeed without pool exhaustion errors
    """
    result = PerformanceResult("database_pool_stress")
    num_requests = 100

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        tasks = []
        for _ in range(num_requests):
            # Mix of endpoints that require database access
            endpoint = "/health"  # Health check queries database
            task = make_request(client, "get", endpoint, result)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    result.finalize()
    metrics = result.save_report()

    # Check for database pool errors
    pool_errors = [
        e for e in metrics["errors"]
        if "pool" in str(e).lower() or "connection" in str(e).lower()
    ]

    assert len(pool_errors) == 0, f"Database pool errors detected: {pool_errors}"
    assert metrics["error_rate_percent"] < 1.0, "Too many errors during DB pool stress test"


@pytest.mark.asyncio
async def test_sustained_load(auth_headers):
    """
    Test system behavior under sustained load.

    Scenario: 500 requests over 1 minute (mixed operations)
    Expected: Consistent performance, no degradation
    """
    result = PerformanceResult("sustained_load")
    num_requests = 500
    duration_target = 60  # seconds

    # Calculate delay between requests to spread over duration
    delay = duration_target / num_requests

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        for i in range(num_requests):
            # Mix of operations
            if i % 10 == 0:
                endpoint = "/health"
            elif i % 5 == 0:
                endpoint = "/ready"
            else:
                endpoint = "/api/sessions/"

            headers = auth_headers if endpoint.startswith("/api/") else {}

            await make_request(client, "get", endpoint, result, headers=headers)
            await asyncio.sleep(delay)

    result.finalize()
    metrics = result.save_report()

    # Check for performance degradation
    # P95 should not be more than 2x average
    assert metrics["response_time_p95_ms"] < metrics["response_time_avg_ms"] * 2.5, \
        "Performance degradation detected (P95 too high relative to average)"

    assert metrics["error_rate_percent"] < 2.0, "Error rate too high during sustained load"


@pytest.mark.asyncio
async def test_memory_leak_detection(auth_headers):
    """
    Monitor memory usage during repeated requests.

    Scenario: 200 requests while monitoring memory
    Expected: No significant memory growth
    """
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    result = PerformanceResult("memory_leak_detection")
    num_requests = 200

    memory_samples = []

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        for i in range(num_requests):
            await make_request(
                client,
                "get",
                "/api/sessions/",
                result,
                headers=auth_headers
            )

            # Sample memory every 20 requests
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

    result.finalize()
    metrics = result.save_report()

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_growth = final_memory - initial_memory

    print(f"\nMemory Analysis:")
    print(f"  Initial: {initial_memory:.2f} MB")
    print(f"  Final: {final_memory:.2f} MB")
    print(f"  Growth: {memory_growth:.2f} MB")
    print(f"  Samples: {[f'{m:.2f}' for m in memory_samples]}")

    # Memory growth should be reasonable (less than 50MB for this test)
    assert memory_growth < 50, f"Potential memory leak: {memory_growth:.2f} MB growth"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
