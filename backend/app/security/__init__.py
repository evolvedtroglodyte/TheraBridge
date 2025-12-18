"""
Security module for HIPAA compliance.

Provides:
- Session management (SessionManager)
- Field-level encryption (FieldEncryption)
- Audit logging
- MFA configuration
- Access controls
- Emergency access (EmergencyAccessService)
- Consent management (ConsentService)
"""
from app.security.session_manager import SessionManager, get_session_manager
from app.security.encryption import (
    FieldEncryption,
    get_encryption_service,
    derive_key_from_passphrase,
    rotate_key,
    generate_new_master_key,
)
from app.security.emergency_access import EmergencyAccessService, get_emergency_access_service
from app.security.consent import ConsentService, get_consent_service, ConsentType

__all__ = [
    "SessionManager",
    "get_session_manager",
    "FieldEncryption",
    "get_encryption_service",
    "derive_key_from_passphrase",
    "rotate_key",
    "generate_new_master_key",
    "EmergencyAccessService",
    "get_emergency_access_service",
    "ConsentService",
    "get_consent_service",
    "ConsentType",
]
