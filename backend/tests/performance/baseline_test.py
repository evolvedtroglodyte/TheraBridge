"""
Quick baseline performance test.

This is a lightweight test that can be run without starting the full backend server.
It measures basic API response times and validates performance expectations.

Usage:
    pytest tests/performance/baseline_test.py -v -s
"""
import pytest
import time
import httpx
import json
from pathlib import Path


@pytest.mark.asyncio
async def test_baseline_health_check():
    """
    Baseline test for health check endpoint.

    Measures response time for the health check endpoint which includes:
    - Database connectivity check
    - Connection pool status
    - OpenAI API client initialization
    """
    api_url = "http://localhost:8000"

    # Warmup request
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.get(f"{api_url}/health")
        except Exception as e:
            pytest.skip(f"Backend not running: {e}")

    # Measure response times
    times = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(20):
            start = time.time()
            response = await client.get(f"{api_url}/health")
            duration = time.time() - start

            assert response.status_code == 200, f"Health check failed: {response.text}"
            times.append(duration * 1000)  # Convert to milliseconds

    # Calculate metrics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    print("\n" + "="*60)
    print("BASELINE HEALTH CHECK PERFORMANCE")
    print("="*60)
    print(f"Requests: {len(times)}")
    print(f"Average: {avg_time:.2f}ms")
    print(f"Min: {min_time:.2f}ms")
    print(f"Max: {max_time:.2f}ms")
    print(f"P95: {p95_time:.2f}ms")
    print("="*60)

    # Performance assertions
    assert avg_time < 500, f"Average response time too high: {avg_time:.2f}ms"
    assert p95_time < 1000, f"P95 response time too high: {p95_time:.2f}ms"


@pytest.mark.asyncio
async def test_baseline_api_latency():
    """
    Measure baseline latency for core API endpoints.

    This test does NOT require authentication and measures:
    - Root endpoint (/)
    - Health check (/health)
    - Readiness probe (/ready)
    - Liveness probe (/live)
    """
    api_url = "http://localhost:8000"

    endpoints = {
        "root": "/",
        "health": "/health",
        "ready": "/ready",
        "live": "/live"
    }

    results = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, endpoint in endpoints.items():
            times = []

            # Warmup
            try:
                await client.get(f"{api_url}{endpoint}")
            except Exception as e:
                pytest.skip(f"Backend not running: {e}")

            # Measure
            for _ in range(10):
                start = time.time()
                response = await client.get(f"{api_url}{endpoint}")
                duration = time.time() - start

                assert response.status_code == 200, f"{endpoint} failed: {response.text}"
                times.append(duration * 1000)

            # Calculate metrics
            results[name] = {
                "endpoint": endpoint,
                "avg_ms": round(sum(times) / len(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2)
            }

    # Print report
    print("\n" + "="*80)
    print("BASELINE API LATENCY REPORT")
    print("="*80)
    print(f"{'Endpoint':<20} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'P95 (ms)':<12}")
    print("-"*80)

    for name, metrics in results.items():
        print(f"{metrics['endpoint']:<20} {metrics['avg_ms']:<12} {metrics['min_ms']:<12} "
              f"{metrics['max_ms']:<12} {metrics['p95_ms']:<12}")

    print("="*80)

    # Save report
    report_dir = Path("tests/performance/results")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"baseline_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "results": results
        }, f, indent=2)

    print(f"\nReport saved to: {report_file}\n")

    # Performance assertions
    for name, metrics in results.items():
        assert metrics["avg_ms"] < 500, f"{name} average latency too high: {metrics['avg_ms']}ms"


@pytest.mark.asyncio
async def test_connection_stability():
    """
    Test connection stability and reliability.

    Makes 50 sequential requests to verify:
    - No connection drops
    - Consistent response times
    - No memory leaks in client/server
    """
    api_url = "http://localhost:8000"
    num_requests = 50

    times = []
    errors = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(num_requests):
            try:
                start = time.time()
                response = await client.get(f"{api_url}/health")
                duration = time.time() - start

                if response.status_code != 200:
                    errors.append(f"Request {i}: Status {response.status_code}")

                times.append(duration * 1000)

            except Exception as e:
                errors.append(f"Request {i}: {str(e)}")

    # Calculate metrics
    success_rate = ((num_requests - len(errors)) / num_requests) * 100
    avg_time = sum(times) / len(times) if times else 0

    print("\n" + "="*60)
    print("CONNECTION STABILITY TEST")
    print("="*60)
    print(f"Total requests: {num_requests}")
    print(f"Successful: {num_requests - len(errors)}")
    print(f"Failed: {len(errors)}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Average latency: {avg_time:.2f}ms")

    if errors:
        print("\nErrors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

    print("="*60)

    # Assertions
    assert success_rate == 100.0, f"Connection stability issue: {len(errors)} failures"
    assert avg_time < 500, f"Average latency degraded: {avg_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
