"""
Comprehensive test suite for Security Headers Middleware.

Tests all 9 security headers added by SecurityHeadersMiddleware for HIPAA compliance
and defense-in-depth web security. Validates header presence, correctness, removal of
server fingerprints, and environment-aware configuration.

Test Coverage:
- All 9 security headers presence and correctness
- Server fingerprinting header removal
- HSTS configuration (enable/disable)
- CSP policy customization via environment
- Middleware integration on all responses
- Error response header inclusion
"""
import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from app.middleware.security_headers import SecurityHeadersMiddleware


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_app():
    """Create test FastAPI app with security headers middleware"""
    app = FastAPI()

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Test endpoints
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/test-404")
    async def test_404():
        return Response(status_code=404, content="Not found")

    @app.get("/test-500")
    async def test_500():
        # Simulate error
        raise Exception("Internal server error")

    @app.get("/test-with-server-header")
    async def test_server_header():
        # Try to set server header (should be removed by middleware)
        response = Response(content="test")
        response.headers["Server"] = "CustomServer/1.0"
        response.headers["X-Powered-By"] = "CustomFramework"
        return response

    return app


@pytest.fixture
def client(test_app):
    """Test client with security headers middleware"""
    return TestClient(test_app)


# ============================================================================
# Header Presence Tests
# ============================================================================

def test_security_headers_all_present(client):
    """All 9 security headers are present in response"""
    response = client.get("/test")

    # All 9 security headers should be present
    expected_headers = [
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Permissions-Policy",
        "X-Permitted-Cross-Domain-Policies",
        "X-Download-Options"
    ]

    for header in expected_headers:
        assert header in response.headers, f"Missing security header: {header}"


def test_hsts_header_correct(client):
    """HSTS header has correct policy: 1 year, includeSubDomains, preload"""
    response = client.get("/test")

    hsts = response.headers.get("Strict-Transport-Security")
    assert hsts is not None
    assert "max-age=31536000" in hsts  # 1 year in seconds
    assert "includeSubDomains" in hsts
    assert "preload" in hsts


def test_csp_header_correct(client):
    """CSP policy is restrictive and prevents XSS"""
    response = client.get("/test")

    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    # Should restrict to same-origin
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp  # Prevent embedding
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


def test_x_frame_options_deny(client):
    """X-Frame-Options set to DENY to prevent clickjacking"""
    response = client.get("/test")

    x_frame = response.headers.get("X-Frame-Options")
    assert x_frame == "DENY"


def test_x_content_type_options_nosniff(client):
    """X-Content-Type-Options set to nosniff"""
    response = client.get("/test")

    x_content_type = response.headers.get("X-Content-Type-Options")
    assert x_content_type == "nosniff"


def test_x_xss_protection_enabled(client):
    """X-XSS-Protection enabled with blocking mode"""
    response = client.get("/test")

    x_xss = response.headers.get("X-XSS-Protection")
    assert x_xss == "1; mode=block"


def test_referrer_policy_correct(client):
    """Referrer-Policy limits referrer information leakage"""
    response = client.get("/test")

    referrer = response.headers.get("Referrer-Policy")
    assert referrer == "strict-origin-when-cross-origin"


def test_permissions_policy_restrictive(client):
    """Permissions-Policy restricts browser features"""
    response = client.get("/test")

    permissions = response.headers.get("Permissions-Policy")
    assert permissions is not None
    # Should restrict dangerous features
    assert "geolocation=()" in permissions
    assert "microphone=()" in permissions
    assert "camera=()" in permissions
    assert "payment=()" in permissions


def test_x_permitted_cross_domain_policies_none(client):
    """X-Permitted-Cross-Domain-Policies set to none"""
    response = client.get("/test")

    x_permitted = response.headers.get("X-Permitted-Cross-Domain-Policies")
    assert x_permitted == "none"


def test_x_download_options_noopen(client):
    """X-Download-Options set to noopen (IE protection)"""
    response = client.get("/test")

    x_download = response.headers.get("X-Download-Options")
    assert x_download == "noopen"


# ============================================================================
# Header Removal Tests
# ============================================================================

def test_server_header_removed(client):
    """Server header is removed to prevent fingerprinting"""
    response = client.get("/test-with-server-header")

    # Server header should be removed by middleware
    assert "Server" not in response.headers


def test_x_powered_by_removed(client):
    """X-Powered-By header is removed to prevent fingerprinting"""
    response = client.get("/test-with-server-header")

    # X-Powered-By header should be removed by middleware
    assert "X-Powered-By" not in response.headers


# ============================================================================
# Configuration Tests
# ============================================================================

def test_hsts_disabled_in_dev():
    """HSTS can be disabled via environment variable"""
    app = FastAPI()

    # Add middleware with HSTS disabled
    with patch.dict(os.environ, {"SECURITY_HSTS_ENABLED": "false"}):
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)
        response = client.get("/test")

        # HSTS should not be present
        assert "Strict-Transport-Security" not in response.headers


def test_hsts_enabled_by_default():
    """HSTS is enabled by default"""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    client = TestClient(app)
    response = client.get("/test")

    # HSTS should be present
    assert "Strict-Transport-Security" in response.headers


def test_csp_from_environment():
    """CSP policy can be overridden via environment variable"""
    custom_csp = "default-src 'none'; script-src 'self' https://cdn.example.com"

    app = FastAPI()

    with patch.dict(os.environ, {"CSP_POLICY": custom_csp}):
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy")
        assert csp == custom_csp


def test_csp_default_without_environment():
    """Default CSP policy used when no environment override"""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    client = TestClient(app)
    response = client.get("/test")

    csp = response.headers.get("Content-Security-Policy")
    # Should have default restrictive policy
    assert "default-src 'self'" in csp


# ============================================================================
# Middleware Integration Tests
# ============================================================================

def test_security_headers_on_all_responses(client):
    """Security headers added to all endpoint responses"""
    # Test multiple endpoints
    endpoints = ["/test", "/test-404"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should have CSP header (one of the key security headers)
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers


def test_security_headers_on_errors(client):
    """Security headers present even on error responses"""
    # Test 404 error
    response = client.get("/test-404")
    assert response.status_code == 404
    assert "Content-Security-Policy" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers


def test_security_headers_on_500_errors(client):
    """Security headers present on 500 server errors"""
    # Test 500 error
    response = client.get("/test-500")
    assert response.status_code == 500

    # Security headers should still be present
    assert "Content-Security-Policy" in response.headers
    assert "X-Frame-Options" in response.headers


def test_multiple_requests_consistent_headers(client):
    """Security headers are consistent across multiple requests"""
    # Make 3 requests
    responses = [client.get("/test") for _ in range(3)]

    # All responses should have same security headers
    first_csp = responses[0].headers.get("Content-Security-Policy")

    for response in responses[1:]:
        assert response.headers.get("Content-Security-Policy") == first_csp


def test_security_headers_idempotent(client):
    """Multiple middleware calls don't duplicate headers"""
    response = client.get("/test")

    # Check that headers are not duplicated
    # If headers were duplicated, the header value might contain commas or multiple values
    csp = response.headers.get("Content-Security-Policy")
    assert csp.count("default-src 'self'") == 1


# ============================================================================
# HSTS Environment Detection Tests
# ============================================================================

def test_hsts_auto_enabled_in_production():
    """HSTS automatically enabled in production environment"""
    app = FastAPI()

    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        # Don't explicitly set SECURITY_HSTS_ENABLED
        from app.middleware.security_headers import create_security_headers_middleware

        middleware = create_security_headers_middleware()
        app.add_middleware(middleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)
        response = client.get("/test")

        # HSTS should be present in production
        assert "Strict-Transport-Security" in response.headers


def test_hsts_auto_disabled_in_development():
    """HSTS automatically disabled in development environment"""
    app = FastAPI()

    with patch.dict(os.environ, {"ENVIRONMENT": "development", "SECURITY_HSTS_ENABLED": ""}, clear=True):
        from app.middleware.security_headers import create_security_headers_middleware

        middleware = create_security_headers_middleware()
        app.add_middleware(middleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)
        response = client.get("/test")

        # HSTS should not be present in development
        assert "Strict-Transport-Security" not in response.headers


# ============================================================================
# Header Value Validation Tests
# ============================================================================

def test_all_security_headers_non_empty(client):
    """All security headers have non-empty values"""
    response = client.get("/test")

    security_headers = [
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Permissions-Policy",
        "X-Permitted-Cross-Domain-Policies",
        "X-Download-Options"
    ]

    for header in security_headers:
        value = response.headers.get(header)
        if header == "Strict-Transport-Security":
            # HSTS might be disabled in tests
            if value:
                assert len(value) > 0
        else:
            assert value is not None
            assert len(value) > 0


def test_hsts_max_age_one_year(client):
    """HSTS max-age is set to 1 year (31536000 seconds)"""
    response = client.get("/test")

    hsts = response.headers.get("Strict-Transport-Security")
    if hsts:  # Only test if HSTS is enabled
        # Extract max-age value
        assert "max-age=31536000" in hsts


def test_csp_prevents_inline_scripts_by_default(client):
    """Default CSP policy prevents inline scripts (no 'unsafe-inline' for scripts)"""
    response = client.get("/test")

    csp = response.headers.get("Content-Security-Policy")
    # script-src should not allow 'unsafe-inline'
    # (Some frameworks might add it for styles, but not scripts)
    assert "script-src 'self'" in csp
    # Ensure we're not allowing unsafe-inline for scripts
    assert "script-src 'self' 'unsafe-inline'" not in csp
