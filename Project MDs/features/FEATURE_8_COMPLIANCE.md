# Feature 8: HIPAA Compliance & Security

## Overview
Implement comprehensive security measures and compliance features to meet HIPAA requirements for protecting Protected Health Information (PHI) in the therapy documentation platform.

## Requirements

### HIPAA Technical Safeguards
1. **Access Controls** - Unique user identification, automatic logoff, encryption
2. **Audit Controls** - Hardware, software, and procedural mechanisms for recording access
3. **Integrity Controls** - Electronic measures to confirm PHI hasn't been altered
4. **Transmission Security** - Encryption of PHI in transit

### Security Features
1. **Authentication & Authorization**
   - Multi-factor authentication (MFA)
   - Role-based access control (RBAC)
   - Session management and timeout

2. **Data Protection**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Field-level encryption for sensitive data

3. **Audit Logging**
   - All PHI access logged
   - Login/logout events
   - Data modifications
   - Export activities

4. **Privacy Controls**
   - Minimum necessary access
   - Break-the-glass procedures
   - Consent management

## Database Schema

```sql
-- Audit log (comprehensive activity tracking)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    patient_id UUID REFERENCES users(id), -- if PHI accessed
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    request_body_hash VARCHAR(64), -- SHA-256 hash of request body
    response_status INTEGER,
    details JSONB,
    risk_level VARCHAR(20) DEFAULT 'normal', -- 'normal', 'elevated', 'high'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Partitioned by month for performance
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_logs_patient ON audit_logs(patient_id, timestamp);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Security events (authentication, authorization)
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    email VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(200),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_events_type ON security_events(event_type, created_at);
CREATE INDEX idx_security_events_user ON security_events(user_id, created_at);

-- MFA configuration
CREATE TABLE mfa_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    mfa_type VARCHAR(20) NOT NULL, -- 'totp', 'sms', 'email'
    secret_encrypted BYTEA, -- encrypted TOTP secret
    phone_number VARCHAR(20),
    backup_codes_hash VARCHAR(255)[], -- hashed backup codes
    is_enabled BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Session management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,
    is_active BOOLEAN DEFAULT true,
    last_activity_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    revoke_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id, is_active);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at) WHERE is_active = true;

-- Data access requests (HIPAA right of access)
CREATE TABLE access_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id),
    request_type VARCHAR(50) NOT NULL, -- 'access', 'amendment', 'restriction', 'accounting'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'denied', 'completed'
    requested_data TEXT,
    request_reason TEXT,
    response_notes TEXT,
    processed_by UUID REFERENCES users(id),
    processed_at TIMESTAMP,
    due_date DATE NOT NULL, -- 30 days from request
    created_at TIMESTAMP DEFAULT NOW()
);

-- Break-the-glass access
CREATE TABLE emergency_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES users(id),
    reason TEXT NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    expires_at TIMESTAMP,
    access_revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consent records
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL, -- 'treatment', 'hipaa_notice', 'telehealth', 'recording'
    version VARCHAR(20),
    consented BOOLEAN NOT NULL,
    consent_text TEXT,
    signature_data TEXT, -- base64 signature image
    ip_address VARCHAR(45),
    consented_at TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data encryption keys (for key rotation)
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_type VARCHAR(50) NOT NULL, -- 'data', 'field', 'backup'
    key_version INTEGER NOT NULL,
    key_encrypted BYTEA NOT NULL, -- encrypted with master key
    is_active BOOLEAN DEFAULT true,
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Authentication Security

#### POST /api/v1/auth/mfa/setup
Initialize MFA setup.

Request:
```json
{
    "mfa_type": "totp"
}
```

Response:
```json
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code_url": "otpauth://totp/TheraScribe:user@example.com?secret=...",
    "backup_codes": ["12345678", "23456789", ...]
}
```

#### POST /api/v1/auth/mfa/verify
Verify MFA code and enable.

Request:
```json
{
    "code": "123456"
}
```

#### POST /api/v1/auth/mfa/validate
Validate MFA during login.

#### GET /api/v1/auth/sessions
List active sessions.

Response:
```json
{
    "sessions": [
        {
            "id": "uuid",
            "ip_address": "192.168.1.1",
            "device": "Chrome on macOS",
            "location": "San Francisco, CA",
            "last_activity": "2024-03-10T14:00:00Z",
            "is_current": true
        }
    ]
}
```

#### DELETE /api/v1/auth/sessions/{session_id}
Revoke specific session.

#### POST /api/v1/auth/sessions/revoke-all
Revoke all sessions except current.

### Audit Logs

#### GET /api/v1/audit/logs
Get audit logs (admin only).

Query params:
- `user_id`: Filter by user
- `patient_id`: Filter by patient
- `action`: Filter by action type
- `start_date`: From date
- `end_date`: To date
- `risk_level`: Filter by risk level

Response:
```json
{
    "logs": [
        {
            "id": "uuid",
            "timestamp": "2024-03-10T14:00:00Z",
            "user": {"id": "uuid", "name": "Dr. Smith"},
            "action": "view_patient_record",
            "resource_type": "patient",
            "resource_id": "uuid",
            "patient_name": "John Doe",
            "ip_address": "192.168.1.1",
            "risk_level": "normal"
        }
    ],
    "total": 1250,
    "page": 1,
    "per_page": 50
}
```

#### GET /api/v1/audit/logs/export
Export audit logs for compliance reporting.

#### GET /api/v1/audit/patients/{patient_id}/accounting
Get accounting of disclosures for patient (HIPAA requirement).

### Access Requests

#### POST /api/v1/access-requests
Submit access request (patient-initiated).

Request:
```json
{
    "request_type": "access",
    "requested_data": "All session notes from 2024",
    "request_reason": "Personal records"
}
```

#### GET /api/v1/access-requests
List access requests (admin view).

#### PUT /api/v1/access-requests/{id}
Process access request.

### Emergency Access

#### POST /api/v1/emergency-access
Request break-the-glass access.

Request:
```json
{
    "patient_id": "uuid",
    "reason": "Patient emergency - need to contact emergency contact",
    "duration_minutes": 30
}
```

### Consent Management

#### POST /api/v1/consent
Record patient consent.

Request:
```json
{
    "patient_id": "uuid",
    "consent_type": "hipaa_notice",
    "consented": true,
    "signature_data": "base64..."
}
```

#### GET /api/v1/patients/{patient_id}/consents
Get patient's consent records.

## Security Implementation

### Encryption at Rest
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class FieldEncryption:
    """Encrypt sensitive fields before database storage."""

    def __init__(self, master_key: bytes):
        self.fernet = Fernet(master_key)

    def encrypt(self, plaintext: str) -> bytes:
        return self.fernet.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        return self.fernet.decrypt(ciphertext).decode()

# Encrypted fields: SSN, detailed diagnosis notes, contact info
```

### Audit Logging Middleware
```python
from fastapi import Request
import hashlib

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        # Capture request details
        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest() if body else None

        response = await call_next(request)

        # Log after response
        await create_audit_log(
            user_id=request.state.user_id,
            action=self.determine_action(request),
            resource_type=self.extract_resource_type(request.url.path),
            resource_id=self.extract_resource_id(request.url.path),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_method=request.method,
            request_path=request.url.path,
            request_body_hash=body_hash,
            response_status=response.status_code
        )

        return response
```

### MFA Implementation
```python
import pyotp

class TOTPService:
    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def get_provisioning_uri(self, secret: str, email: str) -> str:
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="TheraScribe")

    def verify_code(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30 second window
```

### Session Security
```python
from datetime import datetime, timedelta

class SessionManager:
    SESSION_TIMEOUT_MINUTES = 30
    MAX_SESSIONS_PER_USER = 5

    async def create_session(self, user_id: str, request: Request) -> str:
        # Revoke oldest sessions if limit exceeded
        await self.enforce_session_limit(user_id)

        session = UserSession(
            user_id=user_id,
            session_token_hash=self.hash_token(secrets.token_urlsafe(32)),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.now() + timedelta(hours=8),
        )
        await save_session(session)
        return session.token

    async def validate_session(self, token: str) -> Optional[UserSession]:
        session = await get_session_by_token_hash(self.hash_token(token))
        if not session or not session.is_active:
            return None
        if datetime.now() > session.expires_at:
            await self.revoke_session(session.id, "expired")
            return None
        if self.is_session_idle(session):
            await self.revoke_session(session.id, "idle_timeout")
            return None

        # Update last activity
        session.last_activity_at = datetime.now()
        await save_session(session)
        return session
```

## HIPAA Compliance Checklist

### Administrative Safeguards
- [ ] Security officer designated
- [ ] Risk assessment documented
- [ ] Workforce training program
- [ ] Access authorization procedures
- [ ] Incident response plan
- [ ] Business associate agreements

### Physical Safeguards
- [ ] Facility access controls
- [ ] Workstation security
- [ ] Device and media controls

### Technical Safeguards
- [ ] Unique user identification (implemented)
- [ ] Emergency access procedure (implemented)
- [ ] Automatic logoff (implemented)
- [ ] Encryption (implemented)
- [ ] Audit controls (implemented)
- [ ] Integrity controls (implemented)
- [ ] Authentication (implemented)
- [ ] Transmission security (implemented)

### Organizational Requirements
- [ ] Business associate contracts
- [ ] Privacy policies and procedures
- [ ] Documentation retention (6 years)

## Security Headers
```python
# Security headers for all responses
security_headers = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

## Testing Checklist
- [ ] MFA setup and verification flow
- [ ] Session creation and validation
- [ ] Session timeout and revocation
- [ ] Audit log creation for all PHI access
- [ ] Field-level encryption/decryption
- [ ] Access request workflow
- [ ] Emergency access with approval
- [ ] Consent recording
- [ ] Failed login attempt tracking
- [ ] Rate limiting on auth endpoints
- [ ] Security headers present

## Files to Create/Modify
- `app/security/__init__.py`
- `app/security/encryption.py`
- `app/security/mfa.py`
- `app/security/session_manager.py`
- `app/middleware/audit.py`
- `app/middleware/security_headers.py`
- `app/routers/security.py`
- `app/routers/audit.py`
- `app/routers/consent.py`
- `app/models/security.py`
- `app/schemas/security.py`
- `alembic/versions/xxx_add_security_tables.py`

## Dependencies
```
cryptography==42.0.0
pyotp==2.9.0
argon2-cffi==23.1.0
python-jose[cryptography]==3.3.0
```
