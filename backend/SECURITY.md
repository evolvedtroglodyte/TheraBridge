# Feature 8: HIPAA Compliance & Security

## Overview

TherapyBridge implements comprehensive HIPAA-compliant security measures to protect Protected Health Information (PHI) in accordance with the Health Insurance Portability and Accountability Act (HIPAA) requirements.

**Implementation Date:** 2025-12-18
**Compliance Standard:** HIPAA Security Rule (45 CFR Part 164.300-318)
**Feature Version:** 8.0

---

## Security Features Implemented

### 1. Multi-Factor Authentication (MFA)

**TOTP-based two-factor authentication** using industry-standard authenticator apps.

**Endpoints:**
- `POST /api/v1/mfa/setup` - Initialize MFA with QR code
- `POST /api/v1/mfa/verify` - Verify TOTP code and enable MFA
- `POST /api/v1/mfa/validate` - Validate MFA during login

**Setup Instructions:**

1. **User enables MFA:**
   ```bash
   curl -X POST https://api.therapybridge.com/api/v1/mfa/setup \
     -H "Authorization: Bearer <access_token>"
   ```

2. **Scan QR code** with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)

3. **Verify with 6-digit code:**
   ```bash
   curl -X POST https://api.therapybridge.com/api/v1/mfa/verify \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"code": "123456"}'
   ```

4. **Save backup codes** - Displayed once during setup, store securely

**Security Features:**
- TOTP secrets encrypted with AES-256 before database storage
- Backup codes hashed with SHA-256
- Rate limiting: 10 attempts/minute
- 30-second time window (±30 seconds for clock drift)

---

### 2. Audit Logging

**Comprehensive activity logging** for HIPAA compliance and security monitoring.

**What's Logged:**
- All PHI access (view, create, update, delete)
- Authentication events (login, logout, MFA)
- Administrative actions
- Failed access attempts
- Data exports

**Endpoints:**
- `GET /api/v1/audit/logs` - Query audit logs (admin only)
- `GET /api/v1/audit/logs/export` - Export logs as CSV
- `GET /api/v1/audit/patients/{id}/accounting` - HIPAA accounting of disclosures

**Log Fields:**
- Timestamp (UTC)
- User ID and email
- Action performed
- Resource type and ID
- Patient ID (if PHI accessed)
- IP address
- User agent
- Request method and path
- Request body hash (SHA-256, not raw body)
- Response status
- Risk level (normal, elevated, high)

**Retention:** 7 years (2555 days) per HIPAA requirements

**Risk Levels:**
- **HIGH:** Failed auth attempts, emergency access, bulk exports
- **ELEVATED:** PHI access, permission changes, password resets
- **NORMAL:** All other operations

---

### 3. Encryption at Rest

**Field-level encryption** for sensitive PHI data using AES-256.

**Encrypted Fields:**
- TOTP secrets (MFA configuration)
- Sensitive patient data (as configured)
- Backup codes

**Implementation:**
```python
from app.security.encryption import get_encryption_service

# Encrypt before storage
encrypted = encryption_service.encrypt("sensitive data")

# Decrypt when retrieved
plaintext = encryption_service.decrypt(encrypted)
```

**Key Management:**
- Master key stored in `ENCRYPTION_MASTER_KEY` environment variable
- Key rotation supported without data loss
- PBKDF2-HMAC-SHA256 for key derivation

**Configuration:**
```bash
# Generate new master key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
ENCRYPTION_MASTER_KEY=<generated_key>
```

---

### 4. Session Management

**Secure session handling** with timeout enforcement and device tracking.

**Endpoints:**
- `GET /api/v1/auth/sessions` - List active sessions
- `DELETE /api/v1/auth/sessions/{id}` - Revoke specific session
- `POST /api/v1/auth/sessions/revoke-all` - Sign out everywhere

**Security Features:**
- **Idle timeout:** 30 minutes of inactivity
- **Absolute expiration:** 8 hours from creation
- **Session limit:** Maximum 5 concurrent sessions per user
- **Token hashing:** Tokens hashed (SHA-256) before storage
- **Device fingerprinting:** Tracks device type, OS, browser, IP
- **Activity tracking:** Updates last activity timestamp on each request

**Session Lifecycle:**
1. User logs in → Session created with secure random token
2. Token included in Authorization header for each request
3. Session validated on every request (active, not expired, not idle)
4. Activity timestamp updated
5. Automatic revocation after idle timeout or expiration

---

### 5. Emergency Access (Break-the-Glass)

**Time-limited emergency access** to patient records with audit trail.

**Endpoint:**
- `POST /api/v1/emergency-access` - Request emergency access
- `GET /api/v1/emergency-access/active` - List active grants
- `DELETE /api/v1/emergency-access/{id}` - Revoke access

**Use Cases:**
- Patient crisis requiring immediate record access
- Medical emergencies
- Safety concerns

**Requirements:**
- Only therapists/admins can request
- Detailed justification required (50+ characters)
- Auto-approved in MVP (production requires supervisor approval)
- Time-limited (default: 24 hours, max: 168 hours)
- Comprehensive audit logging (high-risk events)

**Workflow:**
1. Therapist requests emergency access with justification
2. Access granted immediately (MVP) or after supervisor approval (production)
3. Access logged in audit trail
4. Access expires automatically after duration
5. Can be revoked manually before expiration

---

### 6. Consent Management

**Patient consent tracking** for treatment, HIPAA notices, and data sharing.

**Endpoints:**
- `POST /api/v1/consent` - Record consent
- `GET /api/v1/consent/patients/{id}/consents` - List consents
- `GET /api/v1/consent/patients/{id}/consent/status` - Check all consent types

**Consent Types:**
1. `treatment` - Consent to treatment
2. `hipaa_notice` - HIPAA notice acknowledgment
3. `telehealth` - Telehealth services consent
4. `recording` - Session recording consent
5. `data_sharing` - Data sharing with third parties
6. `research` - Research participation consent

**Features:**
- Digital signature capture (base64 image)
- IP address tracking
- Version control for consent forms
- Expiration dates
- Revocation support

---

### 7. Access Request Management

**Patient right of access** per HIPAA requirements.

**Endpoints:**
- `POST /api/v1/access-requests` - Submit access request (patient)
- `GET /api/v1/access-requests` - List requests (admin/therapist)
- `PUT /api/v1/access-requests/{id}` - Process request (admin/therapist)

**Request Types:**
1. **access** - Request copy of records
2. **amendment** - Request correction of inaccurate information
3. **restriction** - Request restriction on disclosure
4. **accounting** - Request accounting of disclosures

**HIPAA Compliance:**
- **30-day SLA:** Requests must be processed within 30 days
- **Due date tracking:** Automatic calculation of due dates
- **Priority handling:** Overdue requests highlighted
- **Audit trail:** All requests and responses logged

---

### 8. Security Headers

**HTTP security headers** protect against common web vulnerabilities.

**Headers Applied:**
1. **Strict-Transport-Security:** Forces HTTPS for 1 year
2. **Content-Security-Policy:** Prevents XSS and data injection
3. **X-Content-Type-Options:** Prevents MIME sniffing
4. **X-Frame-Options:** Prevents clickjacking (DENY)
5. **X-XSS-Protection:** Browser XSS filter enabled
6. **Referrer-Policy:** Controls referrer leakage
7. **Permissions-Policy:** Restricts browser features
8. **X-Permitted-Cross-Domain-Policies:** Blocks Flash/PDF policies
9. **X-Download-Options:** Prevents IE download execution

**Configuration:**
```bash
# Disable HSTS in development
SECURITY_HSTS_ENABLED=false

# Custom CSP policy
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'"
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Master encryption key (REQUIRED in production)
ENCRYPTION_MASTER_KEY=<base64-encoded-fernet-key>

# MFA issuer name (optional, default: "TherapyBridge")
MFA_ISSUER=TherapyBridge

# Security headers (optional, defaults shown)
SECURITY_HSTS_ENABLED=true
CSP_POLICY=  # Leave empty for default restrictive policy

# Audit log retention (optional, default: 2555 days = 7 years)
AUDIT_LOG_RETENTION_DAYS=2555
```

### Generating Encryption Key

```bash
# Generate new Fernet key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Output example:
# gAAAAABh1234567890abcdefghijklmnopqrstuvwxyz==
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Set `ENCRYPTION_MASTER_KEY` in production environment
- [ ] Configure `MFA_ISSUER` with company name
- [ ] Review CSP policy for frontend compatibility
- [ ] Test HSTS in staging (irreversible once deployed)
- [ ] Backup database before running migrations

### Database Migration

```bash
# Review migration
alembic upgrade head --sql

# Apply migration
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt" | grep -E '(audit_logs|security_events|mfa_config|user_sessions|access_requests|emergency_access|consent_records|encryption_keys)'
```

### Post-Deployment Verification

```bash
# 1. Test security headers
curl -I https://api.therapybridge.com/health

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# Content-Security-Policy: default-src 'self'...
# X-Frame-Options: DENY

# 2. Test MFA setup
curl -X POST https://api.therapybridge.com/api/v1/mfa/setup \
  -H "Authorization: Bearer <token>"

# Expected: 200 with QR code and backup codes

# 3. Test audit logging
curl https://api.therapybridge.com/api/v1/audit/logs \
  -H "Authorization: Bearer <admin_token>"

# Expected: 200 with audit log entries

# 4. Test session management
curl https://api.therapybridge.com/api/v1/auth/sessions \
  -H "Authorization: Bearer <token>"

# Expected: 200 with list of active sessions
```

---

## HIPAA Compliance Checklist

### Technical Safeguards (§164.312)

#### Access Control (§164.312(a))
- [x] Unique user identification (JWT tokens)
- [x] Emergency access procedure (break-the-glass)
- [x] Automatic logoff (30-minute idle timeout)
- [x] Encryption and decryption (AES-256 field-level)

#### Audit Controls (§164.312(b))
- [x] Comprehensive audit logging
- [x] PHI access tracking
- [x] 7-year retention
- [x] Risk level classification

#### Integrity (§164.312(c))
- [x] Authenticated encryption (tampering detection)
- [x] Request body hashing for audit trail

#### Person/Entity Authentication (§164.312(d))
- [x] Multi-factor authentication
- [x] Session management
- [x] Password complexity requirements

#### Transmission Security (§164.312(e))
- [x] TLS 1.3 encryption in transit
- [x] HSTS enforcement
- [x] Certificate pinning recommended

### Administrative Safeguards (§164.308)

#### Security Management Process (§164.308(a)(1))
- [x] Risk assessment (completed during implementation)
- [x] Risk management (mitigations implemented)
- [x] Sanction policy (access controls, audit logging)
- [x] Information system activity review (audit logs)

#### Assigned Security Responsibility (§164.308(a)(2))
- [ ] Security officer designated (organization responsibility)

#### Workforce Security (§164.308(a)(3))
- [x] Authorization procedures (role-based access control)
- [x] Workforce clearance (authentication required)
- [x] Termination procedures (session revocation)

#### Information Access Management (§164.308(a)(4))
- [x] Access authorization (require_role dependencies)
- [x] Access establishment (user signup/approval)
- [x] Access modification (session management)

#### Security Awareness Training (§164.308(a)(5))
- [ ] Training program (organization responsibility)
- [ ] Periodic security updates (organization responsibility)

#### Contingency Plan (§164.308(a)(7))
- [ ] Data backup plan (organization responsibility)
- [ ] Disaster recovery plan (organization responsibility)
- [ ] Emergency mode operation plan (emergency access implemented)

### Physical Safeguards (§164.310)

- [ ] Facility access controls (organization responsibility)
- [ ] Workstation use policies (organization responsibility)
- [ ] Device and media controls (organization responsibility)

### Organizational Requirements (§164.314)

- [ ] Business associate agreements (organization responsibility)
- [ ] Privacy policies and procedures (organization responsibility)
- [ ] Documentation retention (audit logs: 7 years ✓)

### Patient Rights (§164.524, §164.526, §164.528)

- [x] Right of access (access request management)
- [x] Right to amend (access request types)
- [x] Accounting of disclosures (audit log patient accounting)

---

## Security Incident Response

### Suspected Breach Procedure

1. **Detect:** Monitor audit logs for suspicious activity
   ```bash
   # Query high-risk events
   GET /api/v1/audit/logs?risk_level=high
   ```

2. **Contain:** Revoke compromised sessions immediately
   ```bash
   POST /api/v1/auth/sessions/revoke-all
   ```

3. **Investigate:** Review audit trail
   ```bash
   # Export full audit log
   GET /api/v1/audit/logs/export?start_date=<incident_date>
   ```

4. **Report:** Follow organizational HIPAA breach notification procedures

5. **Remediate:** Update credentials, rotate encryption keys if needed

### Common Security Events

| Event | Risk Level | Action |
|-------|-----------|--------|
| Multiple failed login attempts | HIGH | Investigate IP, consider blocking |
| Unusual PHI access patterns | ELEVATED | Review with user, verify legitimacy |
| Emergency access requests | HIGH | Verify justification, monitor usage |
| Bulk data exports | HIGH | Verify authorization, audit content |
| MFA disabled | ELEVATED | Verify user request, re-enable if unauthorized |

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor high-risk audit events
- Review failed authentication attempts

**Weekly:**
- Review emergency access grants (ensure expired/revoked)
- Check session management (orphaned sessions)

**Monthly:**
- Review access requests (ensure 30-day SLA met)
- Audit MFA adoption rates
- Review consent status compliance

**Annually:**
- Key rotation (encryption keys, JWT secrets)
- Security assessment
- HIPAA compliance audit
- Update consent forms (version increment)

### Audit Log Queries

```bash
# Failed login attempts (last 24 hours)
GET /api/v1/audit/logs?action=user_login&response_status=401&start_date=<24h_ago>

# PHI access by specific user
GET /api/v1/audit/logs?user_id=<uuid>&patient_id=<uuid>

# High-risk events
GET /api/v1/audit/logs?risk_level=high&start_date=<date>

# Patient disclosure accounting
GET /api/v1/audit/patients/<uuid>/accounting?start_date=<6_years_ago>
```

---

## Testing

### Security Test Suite

Run comprehensive security tests:

```bash
# All security tests
pytest tests/security/ -v

# Specific areas
pytest tests/security/test_mfa.py -v                 # MFA tests (19 tests)
pytest tests/security/test_sessions.py -v            # Session tests (25 tests)
pytest tests/security/test_audit.py -v               # Audit tests (23 tests)
pytest tests/security/test_encryption.py -v          # Encryption tests (40 tests)
pytest tests/security/test_emergency.py -v           # Emergency access (30 tests)
pytest tests/security/test_consent.py -v             # Consent tests (16 tests)
pytest tests/middleware/test_security_headers.py -v  # Headers tests (27 tests)

# E2E security flows
pytest tests/e2e/test_security_flow.py -v
```

### Manual Security Testing

```bash
# 1. Test MFA enrollment
curl -X POST https://localhost:8000/api/v1/mfa/setup \
  -H "Authorization: Bearer <token>"

# 2. Test audit logging
curl https://localhost:8000/api/v1/patients/<uuid> \
  -H "Authorization: Bearer <token>"

# Verify audit log created
curl https://localhost:8000/api/v1/audit/logs \
  -H "Authorization: Bearer <admin_token>"

# 3. Test session timeout
# Wait 30 minutes, then:
curl https://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
# Expected: 401 Unauthorized

# 4. Test security headers
curl -I https://localhost:8000/health
# Verify all 9 headers present
```

---

## Troubleshooting

### Common Issues

**Issue:** MFA setup fails with 500 error
**Cause:** Missing `ENCRYPTION_MASTER_KEY`
**Solution:** Set environment variable and restart server

**Issue:** Audit logs not created
**Cause:** AuditMiddleware not registered or registered in wrong order
**Solution:** Verify middleware order in main.py (SecurityHeaders → Audit → CORS)

**Issue:** Sessions expire too quickly
**Cause:** Idle timeout configuration
**Solution:** Adjust SESSION_TIMEOUT_MINUTES in SessionManager (default: 30 min)

**Issue:** HSTS breaks local development
**Cause:** HSTS header cached by browser for 1 year
**Solution:** Set `SECURITY_HSTS_ENABLED=false` in development .env

**Issue:** Emergency access requests fail
**Cause:** User role not therapist/admin
**Solution:** Verify user role in database, update if needed

---

## Support

For security concerns or questions:

- **Security Issues:** Report to security@therapybridge.com
- **HIPAA Compliance:** Contact compliance@therapybridge.com
- **Technical Support:** support@therapybridge.com

**Emergency Contact:** 1-800-XXX-XXXX (24/7 security hotline)

---

## Changelog

### Version 8.0 (2025-12-18)
- Initial HIPAA compliance implementation
- Multi-factor authentication (TOTP)
- Comprehensive audit logging
- Field-level encryption (AES-256)
- Session management with timeout
- Emergency access (break-the-glass)
- Consent management
- Access request workflow
- Security headers middleware
- 180+ comprehensive tests

---

**Document Version:** 1.0
**Last Updated:** 2025-12-18
**Next Review:** 2026-01-18