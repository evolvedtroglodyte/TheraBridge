"""
Security Headers Middleware for HIPAA Compliance.

Adds comprehensive security headers to all HTTP responses to prevent common
web attacks and protect Protected Health Information (PHI).

Features:
- HSTS (HTTP Strict Transport Security) with preload
- Content Security Policy (CSP) to prevent XSS attacks
- X-Frame-Options to prevent clickjacking
- X-Content-Type-Options to prevent MIME sniffing
- XSS Protection header
- Referrer Policy for privacy
- Permissions Policy to restrict browser features
- Removes server identification headers
- Environment-aware configuration

Security Headers Added:
1. Strict-Transport-Security: Forces HTTPS for 1 year + preload
2. Content-Security-Policy: Restricts resource loading to prevent XSS
3. X-Content-Type-Options: Prevents MIME type sniffing attacks
4. X-Frame-Options: Prevents clickjacking by blocking iframe embedding
5. X-XSS-Protection: Enables browser XSS protection
6. Referrer-Policy: Controls referrer information leakage
7. Permissions-Policy: Restricts access to browser features (geolocation, camera, etc.)
8. X-Permitted-Cross-Domain-Policies: Prevents Flash/PDF policy file access

HIPAA Compliance:
- Protects PHI from XSS, CSRF, and clickjacking attacks
- Enforces HTTPS for all traffic (encryption in transit)
- Restricts third-party resource loading
- Minimizes information leakage via referrer headers
"""

import logging
import os
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    This middleware implements defense-in-depth security by adding multiple
    layers of protection against common web attacks.

    Configuration:
    - CSP_POLICY: Override Content-Security-Policy via environment variable
    - SECURITY_HSTS_ENABLED: Disable HSTS in development (default: true)
    - SECURITY_HEADERS_ENABLED: Disable all security headers (default: true)

    Usage:
        from app.middleware.security_headers import SecurityHeadersMiddleware

        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        csp_policy: str = None,
        log_headers: bool = False
    ):
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application instance
            enable_hsts: Enable HSTS header (disable in development if needed)
            csp_policy: Custom Content-Security-Policy (overrides default)
            log_headers: Log when security headers are applied (for debugging)
        """
        super().__init__(app)

        # Environment-aware configuration
        self.enable_hsts = os.getenv("SECURITY_HSTS_ENABLED", str(enable_hsts)).lower() == "true"
        self.log_headers = os.getenv("SECURITY_LOG_HEADERS", str(log_headers)).lower() == "true"

        # Default CSP policy (restrictive, allows only same-origin)
        default_csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # unsafe-inline needed for some CSS-in-JS
            "img-src 'self' data:; "  # data: URIs for inline images
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "  # Prevent embedding in frames
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Allow CSP override from environment or constructor
        self.csp_policy = os.getenv("CSP_POLICY", csp_policy or default_csp)

        # Headers to remove (server fingerprinting)
        self.headers_to_remove = [
            "Server",
            "X-Powered-By",
            "X-AspNet-Version",
            "X-AspNetMvc-Version"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            HTTP response with security headers added
        """
        # Skip WebSocket connections
        if request.headers.get("upgrade") == "websocket":
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Check if this is a documentation endpoint
        is_docs_endpoint = request.url.path in ["/docs", "/redoc", "/openapi.json"]

        # Add security headers (with conditional CSP for docs)
        self._add_security_headers(response, is_docs_endpoint)

        # Remove server identification headers
        self._remove_fingerprint_headers(response)

        # Optional logging
        if self.log_headers:
            logger.debug(
                "Security headers applied",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "hsts_enabled": self.enable_hsts,
                    "docs_endpoint": is_docs_endpoint
                }
            )

        return response

    def _add_security_headers(self, response: Response, is_docs_endpoint: bool = False) -> None:
        """
        Add all security headers to the response.

        Args:
            response: HTTP response object to modify
            is_docs_endpoint: Whether this is a documentation endpoint (relaxed CSP)
        """
        # 1. HSTS - Force HTTPS for 1 year with subdomains and preload
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 2. Content-Security-Policy - Prevent XSS and data injection attacks
        # Use relaxed CSP for documentation endpoints to allow Swagger UI CDN resources
        if is_docs_endpoint:
            docs_csp = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "  # Allow Swagger UI scripts
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "  # Allow Swagger UI styles
                "img-src 'self' data: https://fastapi.tiangolo.com; "  # Allow favicon
                "font-src 'self' https://cdn.jsdelivr.net; "  # Allow Swagger UI fonts
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            response.headers["Content-Security-Policy"] = docs_csp
        else:
            response.headers["Content-Security-Policy"] = self.csp_policy

        # 3. X-Content-Type-Options - Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 4. X-Frame-Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 5. X-XSS-Protection - Enable browser XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer-Policy - Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy - Restrict browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # 8. X-Permitted-Cross-Domain-Policies - Prevent Flash/PDF policy file access
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. X-Download-Options - Prevent IE from executing downloads in site context
        response.headers["X-Download-Options"] = "noopen"

    def _remove_fingerprint_headers(self, response: Response) -> None:
        """
        Remove headers that could be used for server fingerprinting.

        Args:
            response: HTTP response object to modify
        """
        for header in self.headers_to_remove:
            if header in response.headers:
                del response.headers[header]


# ============================================
# Utility Functions
# ============================================

def create_security_headers_middleware(
    enable_hsts: bool = None,
    csp_policy: str = None,
    log_headers: bool = False
) -> type:
    """
    Factory function to create SecurityHeadersMiddleware with custom config.

    This is useful when you want to pass environment-specific settings
    during middleware registration.

    Args:
        enable_hsts: Enable HSTS header (None = auto-detect from environment)
        csp_policy: Custom CSP policy (None = use default)
        log_headers: Log when headers are applied

    Returns:
        Configured SecurityHeadersMiddleware class

    Usage:
        from app.middleware.security_headers import create_security_headers_middleware
        from app.config import settings

        # Auto-disable HSTS in development
        enable_hsts = settings.is_production or settings.is_staging

        app.add_middleware(
            create_security_headers_middleware(
                enable_hsts=enable_hsts,
                log_headers=settings.DEBUG
            )
        )
    """
    # Auto-detect HSTS based on environment if not specified
    if enable_hsts is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
        enable_hsts = environment in ["production", "staging"]

    # Create middleware class with configuration
    class ConfiguredSecurityHeadersMiddleware(SecurityHeadersMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                enable_hsts=enable_hsts,
                csp_policy=csp_policy,
                log_headers=log_headers
            )

    return ConfiguredSecurityHeadersMiddleware


__all__ = [
    'SecurityHeadersMiddleware',
    'create_security_headers_middleware'
]
