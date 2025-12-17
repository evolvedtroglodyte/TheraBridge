# Feature 1: Authentication & Authorization

## Overview
Implement secure JWT-based authentication with role-based access control (RBAC) for therapists and patients.

## Requirements

### User Roles
- **Therapist**: Full access to patient data, sessions, notes
- **Patient**: Limited access to own sessions and notes only
- **Admin**: System-wide management (future)

### Authentication Flow
1. User registers with email/password
2. Email verification (optional for MVP)
3. Login returns JWT access + refresh tokens
4. Access token used for API requests
5. Refresh token for obtaining new access tokens

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'patient',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Therapist-Patient relationships
CREATE TABLE therapist_patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapist_id UUID REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(therapist_id, patient_id)
);
```

## API Endpoints

### POST /api/v1/auth/register
```json
{
    "email": "therapist@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Smith",
    "role": "therapist"
}
```

### POST /api/v1/auth/login
```json
{
    "email": "therapist@example.com",
    "password": "SecurePass123!"
}
```

Response:
```json
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### POST /api/v1/auth/refresh
```json
{
    "refresh_token": "eyJ..."
}
```

### POST /api/v1/auth/logout
Invalidates the refresh token.

### GET /api/v1/auth/me
Returns current user profile.

## Implementation Details

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### JWT Configuration
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
```

### Security Measures
- Passwords hashed with bcrypt (cost factor 12)
- Rate limiting on login endpoints (5 attempts/minute)
- Refresh token rotation on use
- Secure cookie options for web clients

## Dependencies
```
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

## Testing Checklist
- [ ] User registration with valid data
- [ ] User registration with duplicate email (should fail)
- [ ] Login with correct credentials
- [ ] Login with incorrect password (should fail)
- [ ] Access protected endpoint with valid token
- [ ] Access protected endpoint with expired token (should fail)
- [ ] Token refresh flow
- [ ] Logout invalidates refresh token
- [ ] Role-based access control enforcement

## Files to Create/Modify
- `app/auth/__init__.py`
- `app/auth/router.py`
- `app/auth/schemas.py`
- `app/auth/utils.py`
- `app/auth/dependencies.py`
- `app/models/user.py`
- `alembic/versions/xxx_add_auth_tables.py`
