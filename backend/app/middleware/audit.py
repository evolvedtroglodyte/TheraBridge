"""
HIPAA-compliant audit logging middleware

Automatically logs all PHI access and security events for compliance with:
- HIPAA 164.312(b) Audit Controls
- HIPAA 164.308(a)(1)(ii)(D) Information System Activity Review
- HIPAA 164.312(d) Person or Entity Authentication

Features:
- Comprehensive request/response tracking
- Risk level classification (normal, elevated, high)
- PHI access detection and logging
- Performance-optimized (non-blocking background logging)
- Excludes static files and health checks
- SHA-256 request body hashing (not storing raw PHI)
"""
import re
import hashlib
import asyncio
from typing import Optional, Callable
from uuid import UUID
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_models import AuditLog
from app.database import AsyncSessionLocal


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all PHI access and security events for HIPAA compliance.

    Captures:
    - User identification (from request.state.user)
    - Resource access (type, ID, patient ID)
    - Request metadata (IP, user agent, method, path)
    - Response status and outcome
    - Risk level classification

    Performance:
    - Logs asynchronously (doesn't block response)
    - Excludes static files, health checks, docs
    - Minimal overhead on request processing
    """

    # Paths to exclude from audit logging (static assets, health checks)
    EXCLUDED_PATHS = {
        "/health",
        "/healthz",
        "/favicon.ico",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Path prefixes to exclude
    EXCLUDED_PREFIXES = (
        "/static/",
        "/assets/",
        "/_next/",
    )

    # PHI-related resource types
    PHI_RESOURCES = {
        "patient",
        "session",
        "note",
        "transcript",
        "recording",
        "treatment_plan",
        "goal",
        "attachment",
    }

    # Auth-related paths
    AUTH_PATHS = {
        "/auth/login",
        "/auth/logout",
        "/auth/signup",
        "/auth/refresh",
        "/auth/password-reset",
    }

    def __init__(self, app):
        """
        Initialize audit middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit entry.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            HTTP response
        """
        # Skip audit logging for excluded paths
        if self._should_exclude(request):
            return await call_next(request)

        # Capture request body hash (before consuming the body)
        request_body_hash = await self._hash_request_body(request)

        # Process request
        response = await call_next(request)

        # Log audit entry asynchronously (don't block response)
        asyncio.create_task(
            self._create_audit_log(
                request=request,
                response=response,
                request_body_hash=request_body_hash
            )
        )

        return response

    def _should_exclude(self, request: Request) -> bool:
        """
        Determine if path should be excluded from audit logging.

        Args:
            request: HTTP request

        Returns:
            True if path should be excluded
        """
        path = request.url.path

        # Check exact matches
        if path in self.EXCLUDED_PATHS:
            return True

        # Check prefixes
        if path.startswith(self.EXCLUDED_PREFIXES):
            return True

        return False

    async def _hash_request_body(self, request: Request) -> Optional[str]:
        """
        Generate SHA-256 hash of request body for audit trail.
        Does NOT store the actual body (HIPAA compliance).

        Args:
            request: HTTP request

        Returns:
            SHA-256 hash of body, or None if no body
        """
        try:
            # Read body (this consumes the stream)
            body = await request.body()

            # Generate hash if body exists
            if body:
                return hashlib.sha256(body).hexdigest()

            return None
        except Exception:
            # If body already consumed or error reading, return None
            return None

    async def _create_audit_log(
        self,
        request: Request,
        response: Response,
        request_body_hash: Optional[str]
    ) -> None:
        """
        Create audit log entry in database.
        Runs asynchronously to avoid blocking response.

        Args:
            request: HTTP request
            response: HTTP response
            request_body_hash: SHA-256 hash of request body
        """
        try:
            # Create database session
            async with AsyncSessionLocal() as db:
                # Extract user information
                user_id = self._get_user_id(request)
                session_id = self._get_session_id(request)

                # Determine action and resource details
                action = self._determine_action(request)
                resource_type = self._extract_resource_type(request.url.path)
                resource_id = self._extract_resource_id(request.url.path)
                patient_id = self._extract_patient_id(request, resource_type)

                # Calculate risk level
                risk_level = self._calculate_risk_level(request, response)

                # Create audit log entry
                audit_log = AuditLog(
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    session_id=session_id,
                    action=action,
                    resource_type=resource_type or "unknown",
                    resource_id=resource_id,
                    patient_id=patient_id,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    request_method=request.method,
                    request_path=request.url.path,
                    request_body_hash=request_body_hash,
                    response_status=response.status_code,
                    risk_level=risk_level,
                    details={
                        "query_params": dict(request.query_params) if request.query_params else None,
                        "correlation_id": request.headers.get("x-request-id"),
                    }
                )

                db.add(audit_log)
                await db.commit()

        except Exception as e:
            # Log error but don't fail the request
            # In production, this should go to structured logging system
            print(f"Error creating audit log: {e}")

    def _get_user_id(self, request: Request) -> Optional[UUID]:
        """
        Extract user ID from request state.

        Args:
            request: HTTP request

        Returns:
            User UUID or None if not authenticated
        """
        try:
            # Check request.state.user (set by auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                # Handle both dict and object formats
                if isinstance(user, dict):
                    return user.get("id")
                elif hasattr(user, "id"):
                    return user.id

            # Check request.state.user_id (alternative location)
            if hasattr(request.state, "user_id"):
                return request.state.user_id

            return None
        except Exception:
            return None

    def _get_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request.

        Args:
            request: HTTP request

        Returns:
            Session ID string or None
        """
        try:
            # Check request state
            if hasattr(request.state, "session_id"):
                return str(request.state.session_id)

            # Check headers
            session_id = request.headers.get("x-session-id")
            if session_id:
                return session_id

            return None
        except Exception:
            return None

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.
        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: HTTP request

        Returns:
            IP address string or None
        """
        try:
            # Check X-Forwarded-For header (for proxied requests)
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                # Take first IP in chain (original client)
                return forwarded_for.split(",")[0].strip()

            # Fall back to direct connection
            if request.client:
                return request.client.host

            return None
        except Exception:
            return None

    def _determine_action(self, request: Request) -> str:
        """
        Determine action name from request method and path.

        Maps HTTP operations to human-readable actions:
        - GET /api/patients/{id} -> "view_patient"
        - POST /api/sessions -> "create_session"
        - PUT /api/notes/{id} -> "update_note"
        - DELETE /api/recordings/{id} -> "delete_recording"

        Args:
            request: HTTP request

        Returns:
            Action string (e.g., "view_patient", "create_session")
        """
        method = request.method.upper()
        path = request.url.path.lower()

        # Extract resource type from path
        resource_type = self._extract_resource_type(path)

        # Map method to action verb
        action_map = {
            "GET": "view",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }

        verb = action_map.get(method, "access")

        # Special cases for auth endpoints
        if "/login" in path:
            return "user_login"
        elif "/logout" in path:
            return "user_logout"
        elif "/signup" in path:
            return "user_signup"
        elif "/password-reset" in path:
            return "password_reset"
        elif "/refresh" in path:
            return "token_refresh"

        # Construct action name
        if resource_type:
            return f"{verb}_{resource_type}"

        return f"{verb}_resource"

    def _extract_resource_type(self, path: str) -> Optional[str]:
        """
        Extract resource type from URL path.

        Examples:
        - /api/patients/{id} -> "patient"
        - /api/sessions/{id}/notes -> "session"
        - /api/v1/therapy-sessions -> "session"

        Args:
            path: URL path

        Returns:
            Resource type string or None
        """
        # Normalize path
        path = path.lower().strip("/")

        # Resource type patterns (order matters - most specific first)
        patterns = [
            (r"/api/(?:v\d+/)?patients(?:/|$)", "patient"),
            (r"/api/(?:v\d+/)?sessions(?:/|$)", "session"),
            (r"/api/(?:v\d+/)?therapy-sessions(?:/|$)", "session"),
            (r"/api/(?:v\d+/)?notes(?:/|$)", "note"),
            (r"/api/(?:v\d+/)?transcripts(?:/|$)", "transcript"),
            (r"/api/(?:v\d+/)?recordings(?:/|$)", "recording"),
            (r"/api/(?:v\d+/)?treatment-plans(?:/|$)", "treatment_plan"),
            (r"/api/(?:v\d+/)?goals(?:/|$)", "goal"),
            (r"/api/(?:v\d+/)?attachments(?:/|$)", "attachment"),
            (r"/api/(?:v\d+/)?users(?:/|$)", "user"),
            (r"/auth/", "auth"),
        ]

        for pattern, resource_type in patterns:
            if re.search(pattern, path):
                return resource_type

        return None

    def _extract_resource_id(self, path: str) -> Optional[UUID]:
        """
        Extract UUID resource ID from URL path.

        Examples:
        - /api/patients/550e8400-e29b-41d4-a716-446655440000 -> UUID(...)
        - /api/sessions/123 -> None (not a UUID)

        Args:
            path: URL path

        Returns:
            UUID or None
        """
        # UUID pattern (8-4-4-4-12 format)
        uuid_pattern = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"

        match = re.search(uuid_pattern, path.lower())
        if match:
            try:
                return UUID(match.group(1))
            except ValueError:
                return None

        return None

    def _extract_patient_id(
        self,
        request: Request,
        resource_type: Optional[str]
    ) -> Optional[UUID]:
        """
        Extract patient ID if accessing PHI.

        Checks:
        1. Direct patient resource access (/api/patients/{id})
        2. Session/note resource (patient ID in path or query params)
        3. Request state (set by endpoint)

        Args:
            request: HTTP request
            resource_type: Type of resource being accessed

        Returns:
            Patient UUID or None
        """
        try:
            # If accessing patient resource directly
            if resource_type == "patient":
                return self._extract_resource_id(request.url.path)

            # Check query parameters
            patient_id_param = request.query_params.get("patient_id")
            if patient_id_param:
                try:
                    return UUID(patient_id_param)
                except ValueError:
                    pass

            # Check request state (set by endpoint)
            if hasattr(request.state, "patient_id"):
                return request.state.patient_id

            return None
        except Exception:
            return None

    def _calculate_risk_level(
        self,
        request: Request,
        response: Response
    ) -> str:
        """
        Classify request risk level based on operation and outcome.

        Risk Levels:
        - HIGH: Failed auth, emergency access, bulk exports, admin changes
        - ELEVATED: PHI access, user modifications, permission changes
        - NORMAL: Everything else

        Args:
            request: HTTP request
            response: HTTP response

        Returns:
            Risk level string: "high", "elevated", or "normal"
        """
        path = request.url.path.lower()
        method = request.method.upper()
        status = response.status_code

        # HIGH RISK: Failed authentication attempts
        if path in self.AUTH_PATHS and status in (401, 403):
            return "high"

        # HIGH RISK: Emergency access
        if "emergency" in path:
            return "high"

        # HIGH RISK: Bulk data exports
        if "/export" in path or "bulk" in path:
            return "high"

        # HIGH RISK: Administrative changes (user creation, role changes)
        if method in ("POST", "PUT", "PATCH", "DELETE") and "/users" in path:
            return "high"

        # ELEVATED RISK: PHI access (any interaction with PHI resources)
        resource_type = self._extract_resource_type(path)
        if resource_type in self.PHI_RESOURCES:
            return "elevated"

        # ELEVATED RISK: Permission/consent changes
        if "/permissions" in path or "/consent" in path:
            return "elevated"

        # ELEVATED RISK: Password changes
        if "/password" in path:
            return "elevated"

        # NORMAL: Everything else
        return "normal"


__all__ = ["AuditMiddleware"]
