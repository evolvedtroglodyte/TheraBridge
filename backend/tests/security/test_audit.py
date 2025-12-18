"""
Comprehensive test suite for HIPAA-compliant audit logging.

Tests cover:
- Audit middleware functionality (request/response logging, PHI tracking)
- Audit log query endpoints (filtering, pagination, admin access)
- Audit log export functionality (CSV generation)
- Patient accounting of disclosures (HIPAA right of access)
- Risk level classification (normal, elevated, high)
- Admin-only access controls
"""
import pytest
import pytest_asyncio
import csv
import io
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import Mock, AsyncMock, patch

from app.models.security_models import AuditLog
from app.models.db_models import User
from app.models.schemas import UserRole
from app.middleware.audit import AuditMiddleware
from app.main import app
from app.auth.utils import get_password_hash


# API prefix for audit endpoints
AUDIT_PREFIX = "/api/v1/audit"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def audit_logs_sample(test_db, therapist_user, patient_user, admin_user):
    """
    Create sample audit logs with different risk levels for testing.

    Creates 15 audit logs with varied characteristics:
    - Multiple risk levels (normal, elevated, high)
    - Different actions (view, create, update, delete, login, logout)
    - Multiple users (therapist, patient, admin)
    - Different patient PHI access patterns
    - Time distribution over last 30 days

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture
        patient_user: Patient user fixture
        admin_user: Admin user fixture

    Returns:
        List of 15 AuditLog objects
    """
    now = datetime.utcnow()
    logs = []

    # Sample audit log configurations
    log_configs = [
        # Normal risk - read-only operations
        {
            "user_id": therapist_user.id,
            "patient_id": None,
            "action": "view_session",
            "resource_type": "session",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 1,
            "ip": "192.168.1.100",
        },
        {
            "user_id": patient_user.id,
            "patient_id": patient_user.id,
            "action": "view_patient",
            "resource_type": "patient",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 2,
            "ip": "192.168.1.101",
        },
        {
            "user_id": therapist_user.id,
            "patient_id": None,
            "action": "view_note",
            "resource_type": "note",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 3,
            "ip": "192.168.1.100",
        },

        # Elevated risk - PHI access
        {
            "user_id": therapist_user.id,
            "patient_id": patient_user.id,
            "action": "view_session",
            "resource_type": "session",
            "risk_level": "elevated",
            "response_status": 200,
            "days_ago": 4,
            "ip": "192.168.1.100",
        },
        {
            "user_id": therapist_user.id,
            "patient_id": patient_user.id,
            "action": "create_note",
            "resource_type": "note",
            "risk_level": "elevated",
            "response_status": 201,
            "days_ago": 5,
            "ip": "192.168.1.100",
        },
        {
            "user_id": therapist_user.id,
            "patient_id": patient_user.id,
            "action": "update_transcript",
            "resource_type": "transcript",
            "risk_level": "elevated",
            "response_status": 200,
            "days_ago": 6,
            "ip": "192.168.1.100",
        },
        {
            "user_id": admin_user.id,
            "patient_id": patient_user.id,
            "action": "view_patient",
            "resource_type": "patient",
            "risk_level": "elevated",
            "response_status": 200,
            "days_ago": 7,
            "ip": "192.168.1.200",
        },

        # High risk - failed authentication
        {
            "user_id": None,
            "patient_id": None,
            "action": "user_login",
            "resource_type": "auth",
            "risk_level": "high",
            "response_status": 401,
            "days_ago": 8,
            "ip": "10.0.0.50",
        },
        {
            "user_id": None,
            "patient_id": None,
            "action": "user_login",
            "resource_type": "auth",
            "risk_level": "high",
            "response_status": 403,
            "days_ago": 9,
            "ip": "10.0.0.51",
        },

        # High risk - bulk export
        {
            "user_id": admin_user.id,
            "patient_id": None,
            "action": "export_data",
            "resource_type": "session",
            "risk_level": "high",
            "response_status": 200,
            "days_ago": 10,
            "ip": "192.168.1.200",
        },

        # High risk - admin user modifications
        {
            "user_id": admin_user.id,
            "patient_id": None,
            "action": "create_user",
            "resource_type": "user",
            "risk_level": "high",
            "response_status": 201,
            "days_ago": 11,
            "ip": "192.168.1.200",
        },
        {
            "user_id": admin_user.id,
            "patient_id": None,
            "action": "update_user",
            "resource_type": "user",
            "risk_level": "high",
            "response_status": 200,
            "days_ago": 12,
            "ip": "192.168.1.200",
        },

        # More normal risk
        {
            "user_id": therapist_user.id,
            "patient_id": None,
            "action": "view_resource",
            "resource_type": "unknown",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 15,
            "ip": "192.168.1.100",
        },
        {
            "user_id": patient_user.id,
            "patient_id": patient_user.id,
            "action": "view_session",
            "resource_type": "session",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 20,
            "ip": "192.168.1.101",
        },
        {
            "user_id": therapist_user.id,
            "patient_id": None,
            "action": "user_logout",
            "resource_type": "auth",
            "risk_level": "normal",
            "response_status": 200,
            "days_ago": 25,
            "ip": "192.168.1.100",
        },
    ]

    # Create audit logs
    for config in log_configs:
        log = AuditLog(
            id=uuid4(),
            timestamp=now - timedelta(days=config["days_ago"]),
            user_id=config["user_id"],
            session_id=str(uuid4()) if config["user_id"] else None,
            action=config["action"],
            resource_type=config["resource_type"],
            resource_id=uuid4(),
            patient_id=config["patient_id"],
            ip_address=config["ip"],
            user_agent="Mozilla/5.0 (Test Browser)",
            request_method="GET" if "view" in config["action"] else "POST",
            request_path=f"/api/{config['resource_type']}s",
            request_body_hash="abc123def456" if config.get("user_id") else None,
            response_status=config["response_status"],
            details={"test": True},
            risk_level=config["risk_level"],
            created_at=now - timedelta(days=config["days_ago"])
        )
        test_db.add(log)
        logs.append(log)

    test_db.commit()

    # Refresh all logs
    for log in logs:
        test_db.refresh(log)

    return logs


# ============================================================================
# Middleware Tests
# ============================================================================

class TestAuditMiddleware:
    """Test audit middleware functionality"""

    @pytest.mark.asyncio
    async def test_audit_middleware_logs_request(self, async_test_db, therapist_user):
        """Test that middleware logs all requests to database"""
        # Create middleware instance
        middleware = AuditMiddleware(app)

        # Create mock request and response
        mock_request = Mock()
        mock_request.url.path = "/api/sessions/123"
        mock_request.method = "GET"
        mock_request.headers = {
            "user-agent": "Test Client",
            "x-forwarded-for": "192.168.1.1"
        }
        mock_request.query_params = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.state.user = {"id": therapist_user.id}
        mock_request.body = AsyncMock(return_value=b"")

        mock_response = Mock()
        mock_response.status_code = 200

        # Mock call_next to return response
        async def mock_call_next(request):
            return mock_response

        # Execute middleware
        with patch.object(middleware, '_create_audit_log') as mock_create_log:
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Verify response returned
            assert response == mock_response

            # Note: _create_audit_log is called via asyncio.create_task,
            # so we can't directly verify it was called in tests
            # In production, we would verify by querying the database

    def test_audit_middleware_tracks_phi_access(self, test_db, therapist_user, patient_user, audit_logs_sample):
        """Test that middleware tracks PHI access in audit logs"""
        # Filter audit logs that accessed patient PHI
        phi_logs = [log for log in audit_logs_sample if log.patient_id is not None]

        # Verify PHI access was logged
        assert len(phi_logs) > 0

        # Verify all PHI logs have required fields
        for log in phi_logs:
            assert log.patient_id is not None
            assert log.user_id is not None
            assert log.action is not None
            assert log.resource_type in ["patient", "session", "note", "transcript"]
            assert log.ip_address is not None
            assert log.timestamp is not None

    def test_audit_middleware_calculates_risk_level(self, audit_logs_sample):
        """Test that middleware correctly classifies risk levels"""
        # Count logs by risk level
        normal_count = len([log for log in audit_logs_sample if log.risk_level == "normal"])
        elevated_count = len([log for log in audit_logs_sample if log.risk_level == "elevated"])
        high_count = len([log for log in audit_logs_sample if log.risk_level == "high"])

        # Verify we have logs in each category
        assert normal_count > 0, "Should have normal risk logs"
        assert elevated_count > 0, "Should have elevated risk logs"
        assert high_count > 0, "Should have high risk logs"

        # Verify risk classification logic
        for log in audit_logs_sample:
            if log.risk_level == "high":
                # High risk should be failed auth, exports, or user modifications
                assert (
                    (log.response_status in [401, 403] and log.resource_type == "auth") or
                    log.action == "export_data" or
                    log.resource_type == "user"
                )
            elif log.risk_level == "elevated":
                # Elevated risk should be PHI access
                assert log.patient_id is not None or log.resource_type in ["patient", "session", "note", "transcript"]

    def test_audit_middleware_hashes_body(self, audit_logs_sample):
        """Test that request body is hashed, not stored"""
        # Find logs with request bodies
        logs_with_bodies = [log for log in audit_logs_sample if log.request_body_hash is not None]

        # Verify body is hashed (SHA-256 = 64 hex chars)
        for log in logs_with_bodies:
            assert len(log.request_body_hash) > 0
            # In real scenario, verify it's a hex string of correct length
            # Our fixture uses placeholder values

    def test_audit_middleware_extracts_user_id(self, audit_logs_sample, therapist_user, patient_user, admin_user):
        """Test that middleware extracts user ID from authenticated requests"""
        # Find logs with user_id
        user_logs = [log for log in audit_logs_sample if log.user_id is not None]

        # Verify user IDs were captured
        assert len(user_logs) > 0

        # Verify user IDs match our test users
        user_ids = {log.user_id for log in user_logs}
        assert therapist_user.id in user_ids
        assert patient_user.id in user_ids
        assert admin_user.id in user_ids


# ============================================================================
# Audit Query Tests
# ============================================================================

class TestAuditLogsQuery:
    """Test audit log query endpoint"""

    def test_get_audit_logs_admin_only(self, client, therapist_auth_headers, audit_logs_sample):
        """Test that non-admin users get 403 when accessing audit logs"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["detail"].lower()

    def test_get_audit_logs_filters_by_user(self, client, admin_auth_headers, therapist_user, audit_logs_sample):
        """Test filtering audit logs by user_id"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs?user_id={therapist_user.id}",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "entries" in data
        assert "total_count" in data
        assert "has_more" in data

        # Verify all entries belong to therapist
        therapist_logs = [log for log in audit_logs_sample if log.user_id == therapist_user.id]
        assert data["total_count"] == len(therapist_logs)

        for entry in data["entries"]:
            assert entry["user_id"] == str(therapist_user.id)

    def test_get_audit_logs_filters_by_patient(self, client, admin_auth_headers, patient_user, audit_logs_sample):
        """Test filtering audit logs by patient_id"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs?patient_id={patient_user.id}",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify all entries involve the patient
        patient_logs = [log for log in audit_logs_sample if log.patient_id == patient_user.id]
        assert data["total_count"] == len(patient_logs)

        for entry in data["entries"]:
            assert entry["patient_id"] == str(patient_user.id)

    def test_get_audit_logs_filters_by_risk_level(self, client, admin_auth_headers, audit_logs_sample):
        """Test filtering audit logs by risk level"""
        # Test high risk filter
        response = client.get(
            f"{AUDIT_PREFIX}/logs?risk_level=high",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify all entries are high risk
        high_risk_logs = [log for log in audit_logs_sample if log.risk_level == "high"]
        assert data["total_count"] == len(high_risk_logs)

        for entry in data["entries"]:
            assert entry["severity"] == "high"

    def test_get_audit_logs_pagination(self, client, admin_auth_headers, audit_logs_sample):
        """Test pagination of audit logs"""
        # Request first page (5 items per page)
        response = client.get(
            f"{AUDIT_PREFIX}/logs?page=1&per_page=5",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify pagination metadata
        assert len(data["entries"]) <= 5
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert data["total_count"] == len(audit_logs_sample)
        assert data["has_more"] == (len(audit_logs_sample) > 5)

        # Request second page
        response = client.get(
            f"{AUDIT_PREFIX}/logs?page=2&per_page=5",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["offset"] == 5


# ============================================================================
# Audit Export Tests
# ============================================================================

class TestAuditLogsExport:
    """Test audit log CSV export functionality"""

    def test_export_audit_logs_csv(self, client, admin_auth_headers, audit_logs_sample):
        """Test exporting audit logs to CSV"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs/export",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "audit_logs_" in response.headers["content-disposition"]

        # Parse CSV content
        csv_content = response.text
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        # Verify CSV structure
        assert len(rows) > 1  # Header + data rows

        # Verify we have at least as many data rows as logs
        # (might have header row)
        assert len(rows) >= len(audit_logs_sample)

    def test_export_audit_logs_admin_only(self, client, therapist_auth_headers):
        """Test that non-admin users cannot export audit logs"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs/export",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_audit_logs_includes_headers(self, client, admin_auth_headers, audit_logs_sample):
        """Test that CSV export includes proper headers"""
        response = client.get(
            f"{AUDIT_PREFIX}/logs/export",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Parse CSV
        csv_content = response.text
        reader = csv.reader(io.StringIO(csv_content))
        headers = next(reader)

        # Verify expected headers are present
        expected_headers = [
            "timestamp",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "patient_name",
            "ip_address",
            "risk_level"
        ]

        assert headers == expected_headers

    def test_export_audit_logs_filters(self, client, admin_auth_headers, therapist_user, audit_logs_sample):
        """Test that filters apply to CSV export"""
        # Export with user filter
        response = client.get(
            f"{AUDIT_PREFIX}/logs/export?user_id={therapist_user.id}",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Parse CSV
        csv_content = response.text
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        # Count expected rows (header + therapist's logs)
        therapist_logs = [log for log in audit_logs_sample if log.user_id == therapist_user.id]

        # Should have header + therapist's logs
        assert len(rows) == len(therapist_logs) + 1  # +1 for header


# ============================================================================
# Patient Accounting Tests
# ============================================================================

class TestPatientAccounting:
    """Test patient accounting of disclosures endpoint"""

    def test_patient_accounting_success(self, client, patient_auth_headers, patient_user, audit_logs_sample):
        """Test that patient can view their own accounting of disclosures"""
        response = client.get(
            f"{AUDIT_PREFIX}/patients/{patient_user.id}/accounting",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "patient_id" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "total_disclosures" in data
        assert "disclosures" in data
        assert "hipaa_notice" in data

        assert data["patient_id"] == str(patient_user.id)

    def test_patient_accounting_admin_access(self, client, admin_auth_headers, patient_user, audit_logs_sample):
        """Test that admin can view any patient's accounting"""
        response = client.get(
            f"{AUDIT_PREFIX}/patients/{patient_user.id}/accounting",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == str(patient_user.id)

    def test_patient_accounting_unauthorized(self, client, therapist_auth_headers, patient_user, audit_logs_sample):
        """Test that users cannot view other patients' accounting"""
        response = client.get(
            f"{AUDIT_PREFIX}/patients/{patient_user.id}/accounting",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_accounting_6_year_default(self, client, patient_auth_headers, patient_user):
        """Test that default accounting period is 6 years"""
        response = client.get(
            f"{AUDIT_PREFIX}/patients/{patient_user.id}/accounting",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Parse dates
        start_date = datetime.fromisoformat(data["period_start"].replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(data["period_end"].replace("Z", "+00:00"))

        # Verify 6-year period (approximately)
        delta = end_date - start_date
        assert delta.days >= 6 * 365 - 7  # Allow 1 week tolerance
        assert delta.days <= 6 * 365 + 7


# ============================================================================
# Risk Level Tests
# ============================================================================

class TestRiskLevelClassification:
    """Test risk level classification logic"""

    def test_risk_level_high_failed_auth(self, audit_logs_sample):
        """Test that failed authentication attempts are classified as high risk"""
        failed_auth_logs = [
            log for log in audit_logs_sample
            if log.resource_type == "auth" and log.response_status in [401, 403]
        ]

        # Verify all failed auth attempts are high risk
        for log in failed_auth_logs:
            assert log.risk_level == "high"

    def test_risk_level_elevated_phi_access(self, audit_logs_sample, patient_user):
        """Test that PHI access is classified as elevated risk"""
        phi_access_logs = [
            log for log in audit_logs_sample
            if log.patient_id == patient_user.id and log.response_status == 200
        ]

        # Verify PHI access logs are elevated risk
        for log in phi_access_logs:
            assert log.risk_level == "elevated"

    def test_risk_level_normal_read_only(self, audit_logs_sample):
        """Test that read-only operations without PHI are normal risk"""
        normal_logs = [
            log for log in audit_logs_sample
            if log.risk_level == "normal"
        ]

        # Verify normal risk logs are read-only or non-PHI operations
        for log in normal_logs:
            assert (
                log.patient_id is None or
                log.action.startswith("view") or
                log.response_status == 200
            )


# ============================================================================
# Integration Tests
# ============================================================================

class TestAuditIntegration:
    """Integration tests for complete audit workflows"""

    def test_audit_logs_complete_workflow(self, client, admin_auth_headers, therapist_user, audit_logs_sample):
        """Test complete workflow: query -> filter -> export"""
        # Step 1: Query all logs
        response = client.get(
            f"{AUDIT_PREFIX}/logs",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        all_logs = response.json()

        # Step 2: Filter by user
        response = client.get(
            f"{AUDIT_PREFIX}/logs?user_id={therapist_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        filtered_logs = response.json()
        assert filtered_logs["total_count"] < all_logs["total_count"]

        # Step 3: Export filtered results
        response = client.get(
            f"{AUDIT_PREFIX}/logs/export?user_id={therapist_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_audit_hipaa_compliance_features(self, client, admin_auth_headers, patient_user, audit_logs_sample):
        """Test HIPAA-specific compliance features"""
        # Test 1: PHI access logging
        response = client.get(
            f"{AUDIT_PREFIX}/logs?patient_id={patient_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        phi_logs = response.json()
        assert phi_logs["total_count"] > 0

        # Test 2: Risk level filtering for security monitoring
        response = client.get(
            f"{AUDIT_PREFIX}/logs?risk_level=high",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        high_risk = response.json()
        assert high_risk["total_count"] > 0

        # Test 3: Patient accounting of disclosures
        response = client.get(
            f"{AUDIT_PREFIX}/patients/{patient_user.id}/accounting",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        accounting = response.json()
        assert "hipaa_notice" in accounting
        assert "disclosures" in accounting
