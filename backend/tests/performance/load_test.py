"""
Load testing script for TherapyBridge Backend API.

Tests system performance under varying levels of concurrent load using locust.
Measures response times, throughput, error rates, and resource utilization.

Usage:
    # Install dependencies first:
    pip install locust psutil

    # Run with web UI (recommended for initial testing):
    locust -f tests/performance/load_test.py --host=http://localhost:8000

    # Run headless with specific load:
    locust -f tests/performance/load_test.py --host=http://localhost:8000 \
           --users 50 --spawn-rate 5 --run-time 5m --headless

    # Test specific scenario:
    locust -f tests/performance/load_test.py --host=http://localhost:8000 \
           --tags upload --users 10 --spawn-rate 2 --headless

Scenarios:
    - upload: Concurrent session uploads (tests file upload + processing)
    - rate_limit: Rate limit enforcement under load
    - extract: Concurrent note extraction requests
    - read: Read-heavy operations (list sessions, get session details)
    - health: Health check endpoint stress test
"""
import os
import time
import json
import random
from pathlib import Path
from io import BytesIO
from locust import HttpUser, task, between, events, tag
from locust.runners import MasterRunner, WorkerRunner
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPass123!")


class PerformanceMetrics:
    """Collect and track performance metrics during load tests."""

    def __init__(self):
        self.start_time = None
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = 0
        self.cpu_samples = []

    def start(self):
        """Start metrics collection."""
        self.start_time = time.time()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory

    def sample(self):
        """Sample current resource usage."""
        if self.start_time is None:
            return

        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)

        try:
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)
        except Exception as e:
            logger.warning(f"Failed to sample CPU: {e}")

    def report(self):
        """Generate performance report."""
        if self.start_time is None:
            return {}

        duration = time.time() - self.start_time
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0

        return {
            "duration_seconds": round(duration, 2),
            "memory_initial_mb": round(self.initial_memory, 2),
            "memory_peak_mb": round(self.peak_memory, 2),
            "memory_increase_mb": round(self.peak_memory - self.initial_memory, 2),
            "cpu_avg_percent": round(avg_cpu, 2),
            "cpu_samples": len(self.cpu_samples)
        }


# Global metrics instance
metrics = PerformanceMetrics()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize metrics collection when test starts."""
    metrics.start()
    logger.info("Performance metrics collection started")

    # Log database connection pool config
    logger.info(f"Testing against: {environment.host}")
    logger.info("Make sure database connection pool is configured appropriately")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Report performance metrics when test stops."""
    report = metrics.report()
    logger.info("=" * 80)
    logger.info("PERFORMANCE METRICS REPORT")
    logger.info("=" * 80)
    logger.info(json.dumps(report, indent=2))
    logger.info("=" * 80)

    # Save report to file
    report_dir = Path("tests/performance/results")
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"metrics_{timestamp}.json"

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Metrics saved to: {report_file}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Sample metrics on each request."""
    metrics.sample()


class TherapyBridgeUser(HttpUser):
    """
    Simulated user for load testing TherapyBridge API.

    Models realistic user behavior with think time between requests.
    """

    # Wait 1-3 seconds between tasks (simulates user think time)
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.patient_id = None
        self.session_ids = []

    def on_start(self):
        """
        Called when a simulated user starts.
        Authenticates and gets initial data.
        """
        self.login()
        self.get_patient_list()

    def login(self):
        """Authenticate and obtain access token."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            },
            name="/api/v1/auth/login"
        )

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            logger.info(f"User logged in: {TEST_USER_EMAIL}")
        else:
            logger.error(f"Login failed: {response.status_code} - {response.text}")

    def get_auth_headers(self):
        """Get authorization headers for authenticated requests."""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    def get_patient_list(self):
        """Get list of patients and cache a patient ID."""
        response = self.client.get(
            "/api/patients/",
            headers=self.get_auth_headers(),
            name="/api/patients/ (setup)"
        )

        if response.status_code == 200:
            patients = response.json()
            if patients:
                self.patient_id = patients[0]["id"]
                logger.info(f"Using patient ID: {self.patient_id}")

    @task(3)
    @tag("read", "health")
    def health_check(self):
        """Test health check endpoint (lightweight)."""
        self.client.get("/health", name="/health")

    @task(2)
    @tag("read")
    def readiness_check(self):
        """Test readiness probe endpoint."""
        self.client.get("/ready", name="/ready")

    @task(5)
    @tag("read")
    def list_sessions(self):
        """List all sessions (common read operation)."""
        response = self.client.get(
            "/api/sessions/",
            headers=self.get_auth_headers(),
            name="/api/sessions/"
        )

        if response.status_code == 200:
            sessions = response.json()
            # Cache some session IDs for detail views
            if sessions and len(self.session_ids) < 10:
                for session in sessions[:5]:
                    if session["id"] not in self.session_ids:
                        self.session_ids.append(session["id"])

    @task(3)
    @tag("read")
    def get_session_detail(self):
        """Get specific session details."""
        if not self.session_ids:
            return

        session_id = random.choice(self.session_ids)
        self.client.get(
            f"/api/sessions/{session_id}",
            headers=self.get_auth_headers(),
            name="/api/sessions/{id}"
        )

    @task(2)
    @tag("read")
    def list_patients(self):
        """List all patients."""
        self.client.get(
            "/api/patients/",
            headers=self.get_auth_headers(),
            name="/api/patients/"
        )

    @task(1)
    @tag("read")
    def get_patient_sessions(self):
        """Get sessions for a specific patient."""
        if not self.patient_id:
            return

        self.client.get(
            f"/api/patients/{self.patient_id}/sessions",
            headers=self.get_auth_headers(),
            name="/api/patients/{id}/sessions"
        )

    @task(1)
    @tag("upload", "write")
    def upload_session(self):
        """
        Test session upload endpoint.

        Simulates uploading a small audio file (mock data).
        This is the most resource-intensive operation.
        """
        if not self.patient_id:
            logger.warning("No patient ID available for upload test")
            return

        # Create mock audio file (small MP3-like data)
        # In real testing, you'd use actual audio files
        mock_audio = b"ID3" + b"\x00" * 1024 * 100  # 100KB mock MP3

        files = {
            "file": ("test_session.mp3", BytesIO(mock_audio), "audio/mpeg")
        }
        data = {
            "patient_id": str(self.patient_id),
            "session_date": "2024-01-15",
            "notes": "Load test session"
        }

        response = self.client.post(
            "/api/sessions/upload",
            headers=self.get_auth_headers(),
            files=files,
            data=data,
            name="/api/sessions/upload"
        )

        if response.status_code in (200, 202):
            session_data = response.json()
            session_id = session_data.get("id")
            if session_id and session_id not in self.session_ids:
                self.session_ids.append(session_id)

    @task(1)
    @tag("extract", "write")
    def trigger_extraction(self):
        """
        Trigger note extraction for a session.

        Tests the AI extraction endpoint under load.
        """
        if not self.session_ids:
            return

        session_id = random.choice(self.session_ids)
        self.client.post(
            f"/api/sessions/{session_id}/extract-notes",
            headers=self.get_auth_headers(),
            name="/api/sessions/{id}/extract-notes"
        )


class RateLimitTestUser(HttpUser):
    """
    Specialized user for testing rate limit enforcement.

    Makes rapid requests to trigger rate limiting.
    """

    # No wait time - hammer the API
    wait_time = between(0, 0.1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.rate_limited_count = 0

    def on_start(self):
        """Authenticate before testing."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )

        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")

    def get_auth_headers(self):
        """Get authorization headers."""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    @task
    @tag("rate_limit")
    def rapid_fire_requests(self):
        """
        Make rapid requests to test rate limiting.

        Expected behavior:
        - Initial requests succeed (200)
        - After limit, receive 429 Too Many Requests
        """
        response = self.client.get(
            "/api/sessions/",
            headers=self.get_auth_headers(),
            name="/api/sessions/ (rate-limit-test)"
        )

        if response.status_code == 429:
            self.rate_limited_count += 1
            if self.rate_limited_count % 10 == 0:
                logger.info(f"Rate limited {self.rate_limited_count} times")


class DatabaseConnectionPoolUser(HttpUser):
    """
    Test database connection pool behavior under load.

    Makes concurrent database-heavy requests to test pool exhaustion.
    """

    wait_time = between(0, 0.5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None

    def on_start(self):
        """Authenticate."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )

        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")

    def get_auth_headers(self):
        """Get authorization headers."""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    @task
    @tag("db_pool")
    def db_heavy_operation(self):
        """
        Make database-heavy requests.

        List sessions requires database query and should hold
        a connection for the duration of the request.
        """
        self.client.get(
            "/api/sessions/",
            headers=self.get_auth_headers(),
            name="/api/sessions/ (db-pool-test)"
        )

    @task
    @tag("db_pool")
    def health_with_db_check(self):
        """
        Health endpoint checks database connectivity.
        """
        self.client.get(
            "/health",
            name="/health (db-pool-test)"
        )


# Convenience: If run directly, provide usage instructions
if __name__ == "__main__":
    print(__doc__)
    print("\nTo run this test, use the locust command:")
    print("  locust -f tests/performance/load_test.py --host=http://localhost:8000")
    print("\nFor more options, run: locust --help")
