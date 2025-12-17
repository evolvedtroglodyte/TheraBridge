# Feature 1: Authentication - Ultra-Fine-Grained Agent Prompts

This document provides **maximum granularity** for Feature 1, breaking each track into micro-tasks that can be executed independently or sequentially by AI agents.

---

# TRACK 1.1: Database Models & Schemas

**Total Subtasks**: 8 micro-prompts
**Estimated Time**: 45-60 minutes
**Model**: Opus

---

## SUBTASK 1.1.1: Create User Model Base Structure

**Agent Prompt:**
```
You are creating the User database model for TherapyBridge authentication.

CONTEXT:
The User model represents therapists, patients, and admins in the system. It needs UUID-based primary keys, role-based access control, and timestamp tracking.

DEPENDENCIES:
- SQLAlchemy 2.0 installed
- PostgreSQL connection configured in database.py
- Base declarative model available

CREATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
1. Import required SQLAlchemy types:
   - from sqlalchemy import Column, String, Boolean, DateTime, Enum
   - from sqlalchemy.dialects.postgresql import UUID
   - from sqlalchemy.orm import relationship
   - import uuid
   - import enum
   - from datetime import datetime

2. Create UserRole enum class:
   class UserRole(str, enum.Enum):
       THERAPIST = "therapist"
       PATIENT = "patient"
       ADMIN = "admin"

3. Create User model class:
   class User(Base):
       __tablename__ = "users"

       # Primary key
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

       # DO NOT add other fields yet - those come in next subtask

VALIDATION:
- [ ] File created at backend/app/auth/models.py
- [ ] UserRole enum has 3 values (therapist, patient, admin)
- [ ] User class inherits from Base
- [ ] id field uses UUID with auto-generation
- [ ] No syntax errors when importing the file
```

---

## SUBTASK 1.1.2: Add User Authentication Fields

**Agent Prompt:**
```
You are adding authentication fields to the User model.

CONTEXT:
These fields handle email-based login with hashed passwords. We use bcrypt for password hashing (never store plain passwords).

DEPENDENCIES:
- SUBTASK 1.1.1 completed (User model base exists)

UPDATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
Add these fields to the User class (after the id field):

1. Email field (unique identifier for login):
   email = Column(String, unique=True, nullable=False, index=True)

2. Password field (stores bcrypt hash, not plain text):
   hashed_password = Column(String, nullable=False)

3. Full name field:
   full_name = Column(String, nullable=False)

IMPORTANT SECURITY NOTE:
- Never store passwords in plain text
- The hashed_password field stores bcrypt output (60 chars)
- Email must be unique and indexed for fast login lookups

VALIDATION:
- [ ] email field is unique and indexed
- [ ] hashed_password field exists (never named "password")
- [ ] full_name field exists
- [ ] All fields are NOT NULL
```

---

## SUBTASK 1.1.3: Add User Role and Status Fields

**Agent Prompt:**
```
You are adding role-based access control and account status fields to the User model.

CONTEXT:
The role field determines permissions (therapist can view all patients, patient can only view their own data). The is_active field allows soft account deactivation.

DEPENDENCIES:
- SUBTASK 1.1.2 completed (authentication fields exist)

UPDATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
Add these fields to the User class:

1. Role field (for RBAC):
   role = Column(Enum(UserRole), nullable=False)

2. Account status field:
   is_active = Column(Boolean, default=True, nullable=False)

BUSINESS LOGIC:
- role: Determines what endpoints user can access
  * THERAPIST: Can view all patients, create notes, access analytics
  * PATIENT: Can only view their own sessions and goals
  * ADMIN: Full system access

- is_active: Allows disabling accounts without deletion
  * True: Normal account (default)
  * False: Account disabled, cannot login

VALIDATION:
- [ ] role field uses UserRole enum
- [ ] is_active defaults to True
- [ ] Both fields are NOT NULL
```

---

## SUBTASK 1.1.4: Add User Timestamps

**Agent Prompt:**
```
You are adding created_at and updated_at timestamp tracking to the User model.

CONTEXT:
Timestamps are critical for audit trails, debugging, and analytics (e.g., "users created this month").

DEPENDENCIES:
- SUBTASK 1.1.3 completed (role and status fields exist)

UPDATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
Add these fields to the User class:

1. Creation timestamp:
   created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

2. Last updated timestamp:
   updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

IMPORTANT:
- Use datetime.utcnow (not datetime.now) to store UTC times
- created_at: Set once on insert, never changes
- updated_at: Auto-updates on every UPDATE query

VALIDATION:
- [ ] created_at uses datetime.utcnow as default
- [ ] updated_at uses datetime.utcnow for both default and onupdate
- [ ] Both fields use DateTime type (not String)
- [ ] Both fields are NOT NULL
```

---

## SUBTASK 1.1.5: Create Session Model for Refresh Tokens

**Agent Prompt:**
```
You are creating the Session model to store refresh tokens for JWT authentication.

CONTEXT:
We use two-token auth: short-lived access tokens (30 min) and long-lived refresh tokens (7 days). The Session model stores refresh tokens so users can get new access tokens without re-logging in.

DEPENDENCIES:
- SUBTASK 1.1.4 completed (User model complete)

UPDATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
Add this new model class below the User class:

class Session(Base):
    __tablename__ = "sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Refresh token (hashed for security)
    refresh_token = Column(String, nullable=False, unique=True)

    # Expiration tracking
    expires_at = Column(DateTime, nullable=False)

    # Revocation flag (for logout)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

SECURITY NOTES:
- refresh_token is hashed (not plain text) to prevent token theft from DB breaches
- ondelete="CASCADE": If user deleted, all their sessions deleted automatically
- is_revoked: Allows invalidating tokens without deleting the record (audit trail)

VALIDATION:
- [ ] Session table name is "sessions"
- [ ] user_id has CASCADE delete
- [ ] refresh_token is unique
- [ ] expires_at is DateTime (not String)
- [ ] is_revoked defaults to False
```

---

## SUBTASK 1.1.6: Add User-Session Relationship

**Agent Prompt:**
```
You are adding SQLAlchemy relationship between User and Session models.

CONTEXT:
This creates a bidirectional relationship: user.sessions gives all sessions for a user, session.user gives the user who owns the session.

DEPENDENCIES:
- SUBTASK 1.1.5 completed (Session model exists)

UPDATE THIS FILE:
backend/app/auth/models.py

IMPLEMENTATION:
Add this field to the User class (after the updated_at field):

# Relationship to sessions
sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

Add this field to the Session class (after created_at field):

# Relationship to user
user = relationship("User", back_populates="sessions")

WHAT THIS ENABLES:
- user.sessions: List of all active/revoked sessions for this user
- session.user: Get the User object from a session
- cascade="all, delete-orphan": If user deleted, all sessions auto-deleted

VALIDATION:
- [ ] User has sessions relationship
- [ ] Session has user relationship
- [ ] back_populates matches on both sides
- [ ] cascade includes "all, delete-orphan" on User side
- [ ] No circular import errors
```

---

## SUBTASK 1.1.7: Create Pydantic Schemas for User

**Agent Prompt:**
```
You are creating Pydantic schemas for User API input/output validation.

CONTEXT:
Pydantic schemas control what data can be sent to/from the API. Critical: UserResponse must NEVER include hashed_password (security risk).

DEPENDENCIES:
- SUBTASK 1.1.6 completed (User model with relationships exists)

CREATE THIS FILE:
backend/app/auth/schemas.py

IMPLEMENTATION:
1. Import dependencies:
   from pydantic import BaseModel, EmailStr, Field
   from typing import Optional
   from datetime import datetime
   from uuid import UUID
   from app.auth.models import UserRole

2. Create UserCreate schema (for signup):
   class UserCreate(BaseModel):
       email: EmailStr  # Auto-validates email format
       password: str = Field(..., min_length=8)
       full_name: str = Field(..., min_length=1)
       role: UserRole

3. Create UserLogin schema (for login):
   class UserLogin(BaseModel):
       email: EmailStr
       password: str

4. Create UserResponse schema (for API responses):
   class UserResponse(BaseModel):
       id: UUID
       email: str
       full_name: str
       role: UserRole
       is_active: bool
       created_at: datetime

       class Config:
           from_attributes = True  # Allows creating from SQLAlchemy models

CRITICAL SECURITY:
- UserResponse does NOT include hashed_password
- UserCreate validates password length (min 8 chars)
- EmailStr auto-validates email format

VALIDATION:
- [ ] UserCreate requires email, password, full_name, role
- [ ] Password minimum length is 8 characters
- [ ] UserLogin only requires email and password
- [ ] UserResponse does NOT include hashed_password
- [ ] UserResponse has Config with from_attributes=True
```

---

## SUBTASK 1.1.8: Create Pydantic Schemas for Tokens

**Agent Prompt:**
```
You are creating Pydantic schemas for JWT token handling.

CONTEXT:
These schemas define the structure of token responses and refresh requests. TokenResponse is returned after login/signup, TokenRefresh is the input for refreshing expired access tokens.

DEPENDENCIES:
- SUBTASK 1.1.7 completed (User schemas exist)

UPDATE THIS FILE:
backend/app/auth/schemas.py

IMPLEMENTATION:
Add these schema classes to the file:

1. TokenResponse schema (returned after login/signup):
   class TokenResponse(BaseModel):
       access_token: str
       refresh_token: str
       token_type: str = "bearer"
       expires_in: int  # Seconds until access_token expires

2. TokenRefresh schema (input for /auth/refresh endpoint):
   class TokenRefresh(BaseModel):
       refresh_token: str

USAGE:
- TokenResponse: Sent to frontend after successful login
  * Frontend stores both tokens
  * access_token: Short-lived (30 min), sent with every API request
  * refresh_token: Long-lived (7 days), only sent to /auth/refresh

- TokenRefresh: Sent from frontend when access_token expires
  * Backend validates refresh_token from Session table
  * Issues new access_token

VALIDATION:
- [ ] TokenResponse has access_token, refresh_token, token_type, expires_in
- [ ] token_type defaults to "bearer"
- [ ] TokenRefresh only requires refresh_token field
- [ ] All fields have correct types (str, int)
```

---

## SUBTASK 1.1.9: Create Alembic Migration

**Agent Prompt:**
```
You are creating an Alembic database migration to create the users and sessions tables.

CONTEXT:
Alembic manages database schema changes (like git for your database). This migration will create both tables with all indexes and foreign keys.

DEPENDENCIES:
- SUBTASK 1.1.8 completed (all models and schemas exist)
- Alembic initialized in the project

CREATE THIS FILE:
backend/alembic/versions/001_create_auth_tables.py

IMPLEMENTATION:
Run this command to auto-generate the migration:

```bash
cd backend
alembic revision --autogenerate -m "create auth tables"
```

This creates a file like: `001_abc123_create_auth_tables.py`

Then manually verify the migration includes:

1. upgrade() function creates:
   - users table with all fields (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
   - Unique constraint on email
   - Index on email
   - sessions table with all fields (id, user_id, refresh_token, expires_at, is_revoked, created_at)
   - Foreign key: sessions.user_id -> users.id with CASCADE delete
   - Unique constraint on refresh_token

2. downgrade() function:
   - Drops both tables in reverse order (sessions first, then users)

VALIDATION:
- [ ] Migration file created in alembic/versions/
- [ ] upgrade() creates both users and sessions tables
- [ ] email field has unique constraint and index
- [ ] user_id foreign key has CASCADE delete
- [ ] refresh_token has unique constraint
- [ ] downgrade() drops both tables
- [ ] Can run: `alembic upgrade head` successfully
- [ ] Can verify tables exist in PostgreSQL
```

---

# TRACK 1.2: Authentication Utilities & Config

**Total Subtasks**: 6 micro-prompts
**Estimated Time**: 40-50 minutes
**Model**: Opus

---

## SUBTASK 1.2.1: Create Auth Configuration File

**Agent Prompt:**
```
You are creating the authentication configuration file with JWT settings.

CONTEXT:
This config file centralizes all auth-related settings (secret key, token expiration times). Using environment variables allows different settings for dev/staging/prod.

DEPENDENCIES:
- None (this is the foundation for auth utilities)

CREATE THIS FILE:
backend/app/auth/config.py

IMPLEMENTATION:
1. Import dependencies:
   from pydantic_settings import BaseSettings
   from typing import Optional
   import secrets

2. Create AuthConfig class:
   class AuthConfig(BaseSettings):
       # Secret key for JWT signing (should be 32+ random bytes)
       SECRET_KEY: str = secrets.token_urlsafe(32)

       # JWT algorithm
       ALGORITHM: str = "HS256"

       # Access token expiration (in minutes)
       ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

       # Refresh token expiration (in days)
       REFRESH_TOKEN_EXPIRE_DAYS: int = 7

       class Config:
           env_file = ".env"
           case_sensitive = True

3. Create singleton instance:
   auth_config = AuthConfig()

SECURITY NOTES:
- SECRET_KEY: Used to sign JWTs (like a password for tokens)
  * Default: Auto-generated random key (good for dev)
  * Production: MUST set via environment variable
  * If key changes, all existing tokens become invalid

- Access token: Short-lived (30 min)
  * Minimizes damage if token stolen
  * User needs to refresh frequently

- Refresh token: Long-lived (7 days)
  * Reduces login frequency
  * Stored in secure Session table

VALIDATION:
- [ ] AuthConfig class exists
- [ ] SECRET_KEY has secure default (secrets.token_urlsafe)
- [ ] ALGORITHM is "HS256"
- [ ] ACCESS_TOKEN_EXPIRE_MINUTES is 30
- [ ] REFRESH_TOKEN_EXPIRE_DAYS is 7
- [ ] auth_config singleton instance created
```

---

## SUBTASK 1.2.2: Create Password Hashing Functions

**Agent Prompt:**
```
You are implementing password hashing and verification using bcrypt.

CONTEXT:
Never store passwords in plain text. Bcrypt is a slow hashing algorithm designed to resist brute-force attacks. It automatically includes salts to prevent rainbow table attacks.

DEPENDENCIES:
- passlib[bcrypt] installed

CREATE THIS FILE:
backend/app/auth/utils.py

IMPLEMENTATION:
1. Import dependencies:
   from passlib.context import CryptContext
   from datetime import datetime, timedelta
   from typing import Optional, Dict
   import secrets

2. Create password context:
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

3. Create get_password_hash function:
   def get_password_hash(password: str) -> str:
       """
       Hash a plain text password using bcrypt.

       Args:
           password: Plain text password from user input

       Returns:
           Bcrypt hash (60 characters)
       """
       return pwd_context.hash(password)

4. Create verify_password function:
   def verify_password(plain_password: str, hashed_password: str) -> bool:
       """
       Verify a plain text password against a bcrypt hash.

       Args:
           plain_password: Password from login attempt
           hashed_password: Stored bcrypt hash from database

       Returns:
           True if password matches, False otherwise
       """
       return pwd_context.verify(plain_password, hashed_password)

SECURITY NOTES:
- Bcrypt automatically includes a random salt (prevents rainbow tables)
- Bcrypt is intentionally slow (prevents brute-force)
- Hash output is always 60 characters
- Same password hashed twice produces different hashes (because of random salt)

VALIDATION:
- [ ] pwd_context uses bcrypt scheme
- [ ] get_password_hash returns 60-character string
- [ ] verify_password returns True for correct password
- [ ] verify_password returns False for incorrect password
- [ ] Hashing same password twice produces different hashes
```

---

## SUBTASK 1.2.3: Create Access Token Generation Function

**Agent Prompt:**
```
You are implementing JWT access token generation.

CONTEXT:
Access tokens are short-lived JWTs that prove a user's identity. They're sent with every API request in the Authorization header.

DEPENDENCIES:
- SUBTASK 1.2.1 completed (auth_config exists)
- SUBTASK 1.2.2 completed (utils.py exists)
- python-jose[cryptography] installed

UPDATE THIS FILE:
backend/app/auth/utils.py

IMPLEMENTATION:
1. Add imports to the top of the file:
   from jose import jwt, JWTError
   from app.auth.config import auth_config
   from uuid import UUID

2. Create create_access_token function:
   def create_access_token(user_id: UUID, role: str) -> str:
       """
       Create a short-lived JWT access token.

       Args:
           user_id: User's UUID
           role: User's role (therapist/patient/admin)

       Returns:
           JWT token string
       """
       # Calculate expiration time
       expires_delta = timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES)
       expire = datetime.utcnow() + expires_delta

       # Create token payload
       payload = {
           "sub": str(user_id),  # "sub" is standard JWT claim for user ID
           "role": role,
           "exp": expire,  # "exp" is standard JWT claim for expiration
           "type": "access"
       }

       # Encode and sign token
       token = jwt.encode(
           payload,
           auth_config.SECRET_KEY,
           algorithm=auth_config.ALGORITHM
       )

       return token

JWT STRUCTURE:
- sub (subject): User's UUID (standard claim)
- role: Custom claim for role-based access control
- exp (expiration): UTC timestamp when token expires
- type: Custom claim to distinguish access vs refresh tokens

VALIDATION:
- [ ] Function accepts user_id (UUID) and role (str)
- [ ] Expiration calculated from auth_config.ACCESS_TOKEN_EXPIRE_MINUTES
- [ ] Payload includes sub, role, exp, type
- [ ] Token signed with SECRET_KEY and ALGORITHM
- [ ] Returns string (JWT token)
```

---

## SUBTASK 1.2.4: Create Refresh Token Generation Function

**Agent Prompt:**
```
You are implementing refresh token generation.

CONTEXT:
Refresh tokens are long-lived tokens stored in the database. They're used to get new access tokens without re-logging in. Unlike access tokens, refresh tokens are validated against the Session table (can be revoked).

DEPENDENCIES:
- SUBTASK 1.2.3 completed (create_access_token exists)

UPDATE THIS FILE:
backend/app/auth/utils.py

IMPLEMENTATION:
Add this function to utils.py:

def create_refresh_token() -> str:
    """
    Create a secure random refresh token.

    Unlike access tokens (JWTs), refresh tokens are random strings
    stored in the database. This allows server-side revocation.

    Returns:
        URL-safe random string (43 characters)
    """
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token before storing in database.

    We store hashed tokens so if the database is compromised,
    attackers can't use the refresh tokens.

    Args:
        token: Plain refresh token

    Returns:
        Bcrypt hash of token
    """
    return get_password_hash(token)

DESIGN DECISION:
Why not use JWTs for refresh tokens?
- JWTs can't be revoked (they're stateless)
- Random tokens stored in DB can be deleted on logout
- Allows us to list all active sessions for a user
- Enables features like "logout all devices"

SECURITY:
- Token is 43 characters (256 bits of entropy)
- Hashed before storage (protects against DB breaches)
- Stored in Session table with expiration date

VALIDATION:
- [ ] create_refresh_token returns 43-character string
- [ ] Each call produces unique token (test 100 times)
- [ ] hash_refresh_token uses get_password_hash
- [ ] Hashed token is 60 characters (bcrypt output)
```

---

## SUBTASK 1.2.5: Create Token Verification Function

**Agent Prompt:**
```
You are implementing JWT token verification and decoding.

CONTEXT:
This function validates access tokens sent by the frontend. It checks signature, expiration, and extracts the user_id and role.

DEPENDENCIES:
- SUBTASK 1.2.4 completed (token generation functions exist)

UPDATE THIS FILE:
backend/app/auth/utils.py

IMPLEMENTATION:
1. Add import:
   from fastapi import HTTPException, status

2. Create decode_access_token function:
   def decode_access_token(token: str) -> Dict[str, any]:
       """
       Decode and verify a JWT access token.

       Args:
           token: JWT token from Authorization header

       Returns:
           Decoded payload dict with user_id and role

       Raises:
           HTTPException: If token invalid, expired, or wrong type
       """
       try:
           # Decode and verify signature
           payload = jwt.decode(
               token,
               auth_config.SECRET_KEY,
               algorithms=[auth_config.ALGORITHM]
           )

           # Verify token type
           if payload.get("type") != "access":
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid token type"
               )

           # Extract user_id and role
           user_id: str = payload.get("sub")
           role: str = payload.get("role")

           if user_id is None or role is None:
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid token payload"
               )

           return {
               "user_id": user_id,
               "role": role
           }

       except JWTError:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Could not validate credentials",
               headers={"WWW-Authenticate": "Bearer"},
           )

SECURITY CHECKS:
1. Signature verification (prevents tampering)
2. Expiration check (automatic in jwt.decode)
3. Token type check (prevents refresh token misuse)
4. Payload validation (ensures required claims exist)

VALIDATION:
- [ ] Valid token returns dict with user_id and role
- [ ] Expired token raises HTTPException with 401
- [ ] Invalid signature raises HTTPException
- [ ] Refresh token (type="refresh") raises error
- [ ] Token missing "sub" or "role" raises error
```

---

## SUBTASK 1.2.6: Update Environment Variables Example

**Agent Prompt:**
```
You are documenting required environment variables for authentication.

CONTEXT:
The .env.example file shows developers what environment variables they need to set. This is critical for deploying to production.

DEPENDENCIES:
- SUBTASK 1.2.5 completed (all auth utilities exist)

UPDATE THIS FILE:
backend/.env.example

IMPLEMENTATION:
Add these lines to .env.example (create file if it doesn't exist):

```env
# ============================================
# Authentication Configuration
# ============================================

# JWT Secret Key (CRITICAL: Change this in production!)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-here-change-in-production

# JWT Settings
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (required for auth)
DATABASE_URL=postgresql://user:password@localhost:5432/therapybridge
```

Also create a .env file for local development:
```env
SECRET_KEY=dev-secret-key-not-for-production-use-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/therapybridge_dev
```

IMPORTANT NOTES FOR DEVELOPERS:
- .env.example: Committed to git (shows what's needed)
- .env: NOT committed to git (contains secrets)
- Production: Use platform environment variables (Heroku, AWS, etc.)

VALIDATION:
- [ ] .env.example created with all auth variables
- [ ] Comments explain each variable
- [ ] Includes command to generate SECRET_KEY
- [ ] .env created for local development
- [ ] .env in .gitignore (never commit secrets!)
```

---

# TRACK 1.3: Authentication Router & Endpoints

**Total Subtasks**: 7 micro-prompts
**Estimated Time**: 50-60 minutes
**Model**: Opus

---

## SUBTASK 1.3.1: Create Database Dependency

**Agent Prompt:**
```
You are creating the database session dependency for FastAPI.

CONTEXT:
FastAPI dependencies are functions that run before endpoint handlers. The get_db dependency provides a database session to each request and ensures it's properly closed.

DEPENDENCIES:
- SQLAlchemy SessionLocal configured in database.py

CREATE THIS FILE:
backend/app/auth/dependencies.py

IMPLEMENTATION:
1. Import dependencies:
   from typing import Generator
   from sqlalchemy.orm import Session
   from app.database import SessionLocal

2. Create get_db dependency:
   def get_db() -> Generator[Session, None, None]:
       """
       Dependency that provides a database session.

       Yields:
           SQLAlchemy Session object

       Note:
           Session is automatically closed after request completes (finally block)
       """
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()

FASTAPI DEPENDENCY PATTERN:
- yield: Provides the db session to the endpoint
- try/finally: Ensures session closed even if endpoint errors
- Generator type hint: Required for yield dependencies

USAGE IN ENDPOINTS:
@router.post("/auth/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # db is now available here
    # Will be automatically closed after function returns

VALIDATION:
- [ ] Function returns Generator[Session, None, None]
- [ ] Uses yield to provide session
- [ ] finally block closes session
- [ ] Imports SessionLocal from app.database
```

---

## SUBTASK 1.3.2: Create Current User Dependency

**Agent Prompt:**
```
You are creating the get_current_user dependency to extract user from JWT token.

CONTEXT:
This dependency validates the JWT token from the Authorization header and loads the User from the database. It's used on protected endpoints.

DEPENDENCIES:
- SUBTASK 1.3.1 completed (get_db exists)
- SUBTASK 1.2.5 completed (decode_access_token exists)
- User model exists

UPDATE THIS FILE:
backend/app/auth/dependencies.py

IMPLEMENTATION:
1. Add imports:
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthCredentials
   from app.auth.utils import decode_access_token
   from app.auth.models import User
   from uuid import UUID

2. Create security scheme:
   security = HTTPBearer()

3. Create get_current_user dependency:
   def get_current_user(
       credentials: HTTPAuthCredentials = Depends(security),
       db: Session = Depends(get_db)
   ) -> User:
       """
       Extract and validate user from JWT access token.

       Args:
           credentials: HTTP Bearer token from Authorization header
           db: Database session

       Returns:
           User object from database

       Raises:
           HTTPException 401: If token invalid or user not found
           HTTPException 403: If user account is inactive
       """
       # Decode and verify token
       payload = decode_access_token(credentials.credentials)
       user_id = UUID(payload["user_id"])

       # Load user from database
       user = db.query(User).filter(User.id == user_id).first()

       if user is None:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="User not found"
           )

       if not user.is_active:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Account is inactive"
           )

       return user

USAGE IN ENDPOINTS:
@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    # current_user is now a User object from the database
    return UserResponse.from_orm(current_user)

VALIDATION:
- [ ] Function accepts credentials and db dependencies
- [ ] Decodes token using decode_access_token
- [ ] Queries User from database by id
- [ ] Returns 401 if user not found
- [ ] Returns 403 if user.is_active is False
- [ ] Returns User object
```

---

## SUBTASK 1.3.3: Create Role-Based Access Control Dependency

**Agent Prompt:**
```
You are creating a role-checking dependency for authorization.

CONTEXT:
This dependency restricts endpoints to specific roles (e.g., only therapists can view analytics). It's a higher-order function that returns a dependency.

DEPENDENCIES:
- SUBTASK 1.3.2 completed (get_current_user exists)

UPDATE THIS FILE:
backend/app/auth/dependencies.py

IMPLEMENTATION:
Add this function to dependencies.py:

def require_role(allowed_roles: list[str]):
    """
    Create a dependency that requires specific user roles.

    Args:
        allowed_roles: List of role names (e.g., ["therapist", "admin"])

    Returns:
        Dependency function that checks user role

    Usage:
        @router.get("/analytics")
        def get_analytics(user: User = Depends(require_role(["therapist"]))):
            # Only therapists can access this endpoint
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker

ADVANCED PATTERN:
- require_role is a factory function (returns a dependency)
- The returned role_checker function is the actual dependency
- This allows parameterized dependencies

EXAMPLE USAGE:
# Only therapists
@router.get("/patients")
def list_patients(user: User = Depends(require_role(["therapist"]))):
    ...

# Therapists or admins
@router.get("/reports")
def get_reports(user: User = Depends(require_role(["therapist", "admin"]))):
    ...

VALIDATION:
- [ ] Function accepts allowed_roles list
- [ ] Returns a dependency function
- [ ] Inner function uses get_current_user
- [ ] Raises 403 if role not in allowed_roles
- [ ] Returns User object if authorized
```

---

## SUBTASK 1.3.4: Create Signup Endpoint

**Agent Prompt:**
```
You are creating the /auth/signup endpoint for user registration.

CONTEXT:
This endpoint creates a new user account, hashes the password, and returns JWT tokens so the user is automatically logged in.

DEPENDENCIES:
- SUBTASK 1.3.3 completed (all dependencies exist)
- All models, schemas, and utilities exist

CREATE THIS FILE:
backend/app/auth/router.py

IMPLEMENTATION:
1. Import dependencies:
   from fastapi import APIRouter, Depends, HTTPException, status
   from sqlalchemy.orm import Session
   from app.auth.schemas import UserCreate, UserResponse, TokenResponse
   from app.auth.models import User, Session as SessionModel
   from app.auth.dependencies import get_db
   from app.auth.utils import (
       get_password_hash,
       create_access_token,
       create_refresh_token,
       hash_refresh_token
   )
   from app.auth.config import auth_config
   from datetime import datetime, timedelta

2. Create router:
   router = APIRouter()

3. Create signup endpoint:
   @router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
   def signup(user_data: UserCreate, db: Session = Depends(get_db)):
       """
       Register a new user account.

       Args:
           user_data: Email, password, full_name, role
           db: Database session

       Returns:
           Access token, refresh token, and expiration info

       Raises:
           HTTPException 400: If email already registered
       """
       # Check if email already exists
       existing_user = db.query(User).filter(User.email == user_data.email).first()
       if existing_user:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="Email already registered"
           )

       # Create new user
       new_user = User(
           email=user_data.email,
           hashed_password=get_password_hash(user_data.password),
           full_name=user_data.full_name,
           role=user_data.role
       )
       db.add(new_user)
       db.commit()
       db.refresh(new_user)

       # Generate tokens
       access_token = create_access_token(new_user.id, new_user.role.value)
       refresh_token = create_refresh_token()

       # Store refresh token in database
       session = SessionModel(
           user_id=new_user.id,
           refresh_token=hash_refresh_token(refresh_token),
           expires_at=datetime.utcnow() + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
       )
       db.add(session)
       db.commit()

       return TokenResponse(
           access_token=access_token,
           refresh_token=refresh_token,
           expires_in=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
       )

VALIDATION:
- [ ] Endpoint path is /auth/signup
- [ ] Returns 201 status code on success
- [ ] Checks for duplicate email
- [ ] Hashes password before storing
- [ ] Creates both User and Session records
- [ ] Returns TokenResponse with both tokens
```

---

## SUBTASK 1.3.5: Create Login Endpoint

**Agent Prompt:**
```
You are creating the /auth/login endpoint for user authentication.

CONTEXT:
This endpoint verifies email/password, creates a new session, and returns JWT tokens.

DEPENDENCIES:
- SUBTASK 1.3.4 completed (signup endpoint exists, router.py exists)

UPDATE THIS FILE:
backend/app/auth/router.py

IMPLEMENTATION:
1. Add import:
   from app.auth.schemas import UserLogin
   from app.auth.utils import verify_password

2. Add login endpoint:
   @router.post("/auth/login", response_model=TokenResponse)
   def login(credentials: UserLogin, db: Session = Depends(get_db)):
       """
       Authenticate user and create new session.

       Args:
           credentials: Email and password
           db: Database session

       Returns:
           Access token, refresh token, and expiration info

       Raises:
           HTTPException 401: If email/password incorrect or account inactive
       """
       # Find user by email
       user = db.query(User).filter(User.email == credentials.email).first()

       if not user:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Incorrect email or password"
           )

       # Verify password
       if not verify_password(credentials.password, user.hashed_password):
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Incorrect email or password"
           )

       # Check if account active
       if not user.is_active:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Account is inactive"
           )

       # Generate tokens
       access_token = create_access_token(user.id, user.role.value)
       refresh_token = create_refresh_token()

       # Store refresh token in database
       session = SessionModel(
           user_id=user.id,
           refresh_token=hash_refresh_token(refresh_token),
           expires_at=datetime.utcnow() + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
       )
       db.add(session)
       db.commit()

       return TokenResponse(
           access_token=access_token,
           refresh_token=refresh_token,
           expires_in=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
       )

SECURITY NOTE:
Always return same error for "user not found" and "wrong password"
to prevent email enumeration attacks.

VALIDATION:
- [ ] Finds user by email
- [ ] Verifies password with verify_password
- [ ] Checks is_active status
- [ ] Creates new Session record
- [ ] Returns TokenResponse
- [ ] Returns same error message for missing user and wrong password
```

---

## SUBTASK 1.3.6: Create Token Refresh and Logout Endpoints

**Agent Prompt:**
```
You are creating /auth/refresh (get new access token) and /auth/logout (revoke session) endpoints.

CONTEXT:
- /auth/refresh: Validates refresh token and issues new access token (without re-entering password)
- /auth/logout: Revokes the session (prevents future token refreshes)

DEPENDENCIES:
- SUBTASK 1.3.5 completed (login endpoint exists)

UPDATE THIS FILE:
backend/app/auth/router.py

IMPLEMENTATION:
1. Add imports:
   from app.auth.schemas import TokenRefresh
   from app.auth.dependencies import get_current_user

2. Add refresh endpoint:
   @router.post("/auth/refresh", response_model=TokenResponse)
   def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
       """
       Get new access token using refresh token.

       Args:
           token_data: Refresh token
           db: Database session

       Returns:
           New access token (same refresh token)

       Raises:
           HTTPException 401: If refresh token invalid/expired/revoked
       """
       # Find session with this refresh token
       session = db.query(SessionModel).filter(
           SessionModel.refresh_token == hash_refresh_token(token_data.refresh_token)
       ).first()

       if not session:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid refresh token"
           )

       # Check if revoked
       if session.is_revoked:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Token has been revoked"
           )

       # Check if expired
       if datetime.utcnow() > session.expires_at:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Refresh token expired"
           )

       # Get user
       user = db.query(User).filter(User.id == session.user_id).first()

       # Generate new access token
       access_token = create_access_token(user.id, user.role.value)

       return TokenResponse(
           access_token=access_token,
           refresh_token=token_data.refresh_token,  # Return same refresh token
           expires_in=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
       )

3. Add logout endpoint:
   @router.post("/auth/logout")
   def logout(
       token_data: TokenRefresh,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """
       Revoke refresh token (logout).

       Args:
           token_data: Refresh token to revoke
           current_user: Authenticated user
           db: Database session

       Returns:
           Success message
       """
       # Find and revoke session
       session = db.query(SessionModel).filter(
           SessionModel.user_id == current_user.id,
           SessionModel.refresh_token == hash_refresh_token(token_data.refresh_token)
       ).first()

       if session:
           session.is_revoked = True
           db.commit()

       return {"message": "Successfully logged out"}

VALIDATION:
- [ ] /auth/refresh validates refresh token from Session table
- [ ] Returns 401 if token revoked or expired
- [ ] Issues new access_token
- [ ] Returns same refresh_token (doesn't create new one)
- [ ] /auth/logout requires authentication
- [ ] Sets is_revoked to True
- [ ] Returns success message even if session not found (idempotent)
```

---

## SUBTASK 1.3.7: Create Get Current User Endpoint and Register Router

**Agent Prompt:**
```
You are creating /auth/me endpoint (get current user info) and registering the auth router in main.py.

CONTEXT:
- /auth/me: Protected endpoint that returns current user's info (useful for frontend to check auth status)
- Router registration: Makes all auth endpoints available in the app

DEPENDENCIES:
- SUBTASK 1.3.6 completed (all auth endpoints exist)

UPDATE THIS FILE:
backend/app/auth/router.py

IMPLEMENTATION:
1. Add get me endpoint:
   @router.get("/auth/me", response_model=UserResponse)
   def get_me(current_user: User = Depends(get_current_user)):
       """
       Get current authenticated user's information.

       Args:
           current_user: User from JWT token

       Returns:
           User information (without password)
       """
       return UserResponse.from_orm(current_user)

2. UPDATE THIS FILE: backend/app/main.py

Add these lines to include the auth router:

   from app.auth.router import router as auth_router

   app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])

WHAT THIS ENABLES:
Frontend can call GET /api/v1/auth/me with access token to:
- Check if user is still authenticated
- Get current user's role (redirect therapist vs patient)
- Display user's name in UI

ROUTER CONFIGURATION:
- prefix="/api/v1": All routes become /api/v1/auth/*
- tags=["authentication"]: Groups endpoints in OpenAPI docs

VALIDATION:
- [ ] /auth/me endpoint exists
- [ ] Uses get_current_user dependency
- [ ] Returns UserResponse (not User model)
- [ ] Router registered in main.py with /api/v1 prefix
- [ ] Can access http://localhost:8000/docs and see auth endpoints
- [ ] All 5 endpoints visible: signup, login, refresh, logout, me
```

---

# TRACK 1.4: Frontend Auth Components

**Total Subtasks**: 8 micro-prompts
**Estimated Time**: 50-60 minutes
**Model**: Opus

---

## SUBTASK 1.4.1: Create Token Storage Utility

**Agent Prompt:**
```
You are creating localStorage utilities for JWT token management.

CONTEXT:
Tokens must persist across page refreshes. localStorage is the standard browser API for client-side storage (unlike sessionStorage which clears on tab close).

DEPENDENCIES:
- None (pure TypeScript utility)

CREATE THIS FILE:
frontend/lib/token-storage.ts

IMPLEMENTATION:
const ACCESS_TOKEN_KEY = 'therapybridge_access_token';
const REFRESH_TOKEN_KEY = 'therapybridge_refresh_token';

export const tokenStorage = {
  /**
   * Save both access and refresh tokens to localStorage.
   */
  saveTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  /**
   * Get access token from localStorage.
   * Returns null if not found.
   */
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Get refresh token from localStorage.
   * Returns null if not found.
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Remove both tokens from localStorage (logout).
   */
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user has tokens (quick auth check).
   * Note: Does NOT validate if tokens are valid/expired.
   */
  hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  }
};

SECURITY NOTES:
- localStorage persists until explicitly cleared
- Vulnerable to XSS attacks (sanitize all user input!)
- Alternative: httpOnly cookies (more secure, but harder to implement)

VALIDATION:
- [ ] Can save tokens with saveTokens()
- [ ] Can retrieve tokens with getAccessToken/getRefreshToken
- [ ] clearTokens removes both tokens
- [ ] hasTokens returns true only if both exist
- [ ] Tokens persist after page refresh
```

---

## SUBTASK 1.4.2: Create API Client with Auth Interceptor

**Agent Prompt:**
```
You are creating an API client that automatically adds auth tokens to requests and handles token refresh on 401 errors.

CONTEXT:
Every API request needs the access token in the Authorization header. If the backend returns 401 (token expired), we automatically refresh the token and retry the request.

DEPENDENCIES:
- SUBTASK 1.4.1 completed (tokenStorage exists)

CREATE THIS FILE:
frontend/lib/api-client.ts

IMPLEMENTATION:
import { tokenStorage } from './token-storage';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  /**
   * Make authenticated API request.
   * Automatically adds Authorization header and handles token refresh.
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const accessToken = tokenStorage.getAccessToken();

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

      // Handle 401 (token expired)
      if (response.status === 401) {
        return await this.handleTokenRefresh(endpoint, options);
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Handle token refresh when 401 received.
   */
  private async handleTokenRefresh<T>(
    endpoint: string,
    options: RequestInit
  ): Promise<T> {
    const refreshToken = tokenStorage.getRefreshToken();

    if (!refreshToken) {
      tokenStorage.clearTokens();
      window.location.href = '/auth/login';
      throw new Error('No refresh token available');
    }

    // Refresh the access token
    const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!refreshResponse.ok) {
      // Refresh token also expired, force re-login
      tokenStorage.clearTokens();
      window.location.href = '/auth/login';
      throw new Error('Session expired');
    }

    const { access_token, refresh_token } = await refreshResponse.json();
    tokenStorage.saveTokens(access_token, refresh_token);

    // Retry original request with new token
    return this.request<T>(endpoint, options);
  }

  // Convenience methods
  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();

VALIDATION:
- [ ] GET request includes Authorization header
- [ ] 401 error triggers token refresh
- [ ] After refresh, original request retried
- [ ] If refresh fails, redirects to login
- [ ] Can call apiClient.get(), post(), patch(), delete()
```

---

## SUBTASK 1.4.3: Create Auth Context and Provider

**Agent Prompt:**
```
You are creating React Context for global authentication state.

CONTEXT:
Auth context provides user state and auth methods (login, logout, etc.) to all components. This avoids prop drilling and centralizes auth logic.

DEPENDENCIES:
- SUBTASK 1.4.2 completed (apiClient exists)
- tokenStorage exists

CREATE THIS FILE:
frontend/lib/auth-context.tsx

IMPLEMENTATION:
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from './api-client';
import { tokenStorage } from './token-storage';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'therapist' | 'patient' | 'admin';
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    if (!tokenStorage.hasTokens()) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await apiClient.get<User>('/auth/me');
      setUser(userData);
    } catch (error) {
      tokenStorage.clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/auth/login', { email, password });

    tokenStorage.saveTokens(response.access_token, response.refresh_token);
    await checkAuth();
  };

  const signup = async (email: string, password: string, fullName: string, role: string) => {
    const response = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/auth/signup', {
      email,
      password,
      full_name: fullName,
      role,
    });

    tokenStorage.saveTokens(response.access_token, response.refresh_token);
    await checkAuth();
  };

  const logout = async () => {
    const refreshToken = tokenStorage.getRefreshToken();

    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch (error) {
        // Ignore errors (already logged out on server)
      }
    }

    tokenStorage.clearTokens();
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

VALIDATION:
- [ ] AuthProvider wraps children
- [ ] Calls checkAuth on mount
- [ ] login saves tokens and fetches user
- [ ] signup creates account and auto-logs in
- [ ] logout revokes token and clears state
- [ ] useAuth hook throws error if outside provider
```

---

## SUBTASK 1.4.4: Create Login Page

**Agent Prompt:**
```
You are creating the login page UI.

CONTEXT:
This page has email/password form, calls authContext.login(), and redirects based on user role.

DEPENDENCIES:
- SUBTASK 1.4.3 completed (AuthContext exists)
- shadcn/ui Button and Input components installed

CREATE THIS FILE:
frontend/app/auth/login/page.tsx

IMPLEMENTATION:
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login, user } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);

      // Redirect based on role (user is updated after login)
      if (user?.role === 'therapist') {
        router.push('/therapist');
      } else if (user?.role === 'patient') {
        router.push('/patient');
      } else {
        router.push('/');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Login to TherapyBridge</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded text-sm">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link href="/auth/signup" className="text-blue-600 hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}

VALIDATION:
- [ ] Form validates email format (type="email")
- [ ] Password field is masked (type="password")
- [ ] Error message displays on failed login
- [ ] Loading state disables button
- [ ] Redirects to /therapist or /patient based on role
- [ ] Link to signup page works
```

---

## SUBTASK 1.4.5: Create Signup Page

**Agent Prompt:**
```
You are creating the signup/registration page UI.

CONTEXT:
This page has form for email, password, full name, and role selector. Calls authContext.signup() and auto-logs user in.

DEPENDENCIES:
- SUBTASK 1.4.4 completed (login page exists as reference)

CREATE THIS FILE:
frontend/app/auth/signup/page.tsx

IMPLEMENTATION:
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'therapist' | 'patient'>('patient');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { signup, user } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await signup(email, password, fullName, role);

      // Redirect based on role
      if (role === 'therapist') {
        router.push('/therapist');
      } else {
        router.push('/patient');
      }
    } catch (err: any) {
      setError(err.message || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Create Account</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium mb-1">
              Full Name
            </label>
            <Input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password (min 8 characters)
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder="••••••••"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium mb-1">
              I am a...
            </label>
            <Select value={role} onValueChange={(val) => setRole(val as 'therapist' | 'patient')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="patient">Patient</SelectItem>
                <SelectItem value="therapist">Therapist</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded text-sm">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Creating account...' : 'Sign Up'}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-blue-600 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

VALIDATION:
- [ ] All fields required
- [ ] Password min length validated (8 chars)
- [ ] Role selector with therapist/patient options
- [ ] Auto-redirects after signup
- [ ] Link to login page works
```

---

## SUBTASK 1.4.6: Create Protected Route Wrapper

**Agent Prompt:**
```
You are creating a ProtectedRoute component that redirects unauthenticated users to login.

CONTEXT:
This wrapper component checks if user is authenticated. If not, redirects to /auth/login. If authenticated but wrong role, shows error.

DEPENDENCIES:
- SUBTASK 1.4.3 completed (AuthContext exists)

CREATE THIS FILE:
frontend/components/auth/ProtectedRoute.tsx

IMPLEMENTATION:
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ('therapist' | 'patient' | 'admin')[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login');
    }

    if (!isLoading && user && allowedRoles && !allowedRoles.includes(user.role)) {
      router.push('/unauthorized');
    }
  }, [isLoading, isAuthenticated, user, allowedRoles, router]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  // Show nothing while redirecting
  if (!isAuthenticated) {
    return null;
  }

  // Check role authorization
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">
          You don't have permission to access this page.
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

USAGE EXAMPLE:
// Protect therapist dashboard
export default function TherapistDashboard() {
  return (
    <ProtectedRoute allowedRoles={['therapist']}>
      <div>Therapist Dashboard Content</div>
    </ProtectedRoute>
  );
}

VALIDATION:
- [ ] Redirects to /auth/login if not authenticated
- [ ] Shows loading spinner while checking auth
- [ ] Allows access if user authenticated
- [ ] Blocks access if user role not in allowedRoles
- [ ] allowedRoles is optional (if omitted, any authenticated user allowed)
```

---

## SUBTASK 1.4.7: Wrap App with AuthProvider

**Agent Prompt:**
```
You are wrapping the entire app with AuthProvider to enable auth context globally.

CONTEXT:
The AuthProvider must wrap all pages so useAuth() works anywhere in the app. In Next.js 13+ App Router, this goes in the root layout.

DEPENDENCIES:
- SUBTASK 1.4.6 completed (all auth components exist)

UPDATE THIS FILE:
frontend/app/layout.tsx

IMPLEMENTATION:
Find the root layout component and wrap children with AuthProvider:

import { AuthProvider } from '@/lib/auth-context';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

WHY THIS WORKS:
- AuthProvider at root means all pages/components can useAuth()
- Client component ('use client') works in server component (layout)
- Auth state persists across page navigations

VALIDATION:
- [ ] AuthProvider imported from @/lib/auth-context
- [ ] Wraps {children} in layout
- [ ] No errors when starting dev server
- [ ] Can call useAuth() from any page
```

---

## SUBTASK 1.4.8: Create Environment Variables File

**Agent Prompt:**
```
You are creating .env.local for frontend API configuration.

CONTEXT:
Next.js reads environment variables from .env.local. The NEXT_PUBLIC_ prefix makes variables available in the browser.

DEPENDENCIES:
- None (configuration file)

CREATE THIS FILE:
frontend/.env.local.example

IMPLEMENTATION:
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Also create the actual .env.local file:

frontend/.env.local
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

IMPORTANT NOTES:
- .env.local.example: Committed to git (template)
- .env.local: NOT committed to git (actual config)
- NEXT_PUBLIC_ prefix: Makes variable available in browser
- Without prefix: Only available in server components

Add to .gitignore (if not already there):
```
.env.local
.env*.local
```

PRODUCTION CONFIGURATION:
When deploying, set NEXT_PUBLIC_API_URL to production backend URL:
```env
NEXT_PUBLIC_API_URL=https://api.therapybridge.com/api/v1
```

VALIDATION:
- [ ] .env.local.example created
- [ ] .env.local created with same content
- [ ] .env.local in .gitignore
- [ ] Variable accessible via process.env.NEXT_PUBLIC_API_URL
- [ ] Can restart dev server and API calls work
```

---

# INTEGRATION TESTING

**After all 4 tracks complete, run this integration test:**

## INTEGRATION TEST PROMPT

**Agent Prompt:**
```
You are running end-to-end integration tests for Feature 1 (Authentication).

CONTEXT:
All 4 tracks are complete. Now we verify the entire auth flow works from frontend to database.

PREREQUISITES:
- PostgreSQL running
- Backend server running: `cd backend && uvicorn app.main:app --reload`
- Frontend server running: `cd frontend && npm run dev`

TEST SCENARIOS:

1. DATABASE VERIFICATION
   [ ] Connect to PostgreSQL
   [ ] Verify tables exist: users, sessions
   [ ] Verify indexes: users.email
   [ ] Verify foreign key: sessions.user_id -> users.id

2. BACKEND API TESTS (use curl or Postman)

   A. Signup:
   [ ] POST http://localhost:8000/api/v1/auth/signup
       Body: {"email": "test@example.com", "password": "password123", "full_name": "Test User", "role": "therapist"}
       Expected: 201 status, returns access_token and refresh_token

   [ ] Verify user created in database
   [ ] Verify session created in database
   [ ] Verify password is hashed (not plain text)

   B. Login:
   [ ] POST http://localhost:8000/api/v1/auth/login
       Body: {"email": "test@example.com", "password": "password123"}
       Expected: 200 status, returns tokens

   [ ] Try wrong password -> 401 error
   [ ] Try non-existent email -> 401 error

   C. Get Current User:
   [ ] GET http://localhost:8000/api/v1/auth/me
       Header: Authorization: Bearer {access_token}
       Expected: 200 status, returns user info without password

   [ ] Try without token -> 401 error
   [ ] Try with invalid token -> 401 error

   D. Token Refresh:
   [ ] POST http://localhost:8000/api/v1/auth/refresh
       Body: {"refresh_token": "{refresh_token}"}
       Expected: 200 status, returns new access_token

   [ ] Try with invalid refresh_token -> 401 error

   E. Logout:
   [ ] POST http://localhost:8000/api/v1/auth/logout
       Header: Authorization: Bearer {access_token}
       Body: {"refresh_token": "{refresh_token}"}
       Expected: 200 status

   [ ] Verify session.is_revoked = true in database
   [ ] Try to refresh with revoked token -> 401 error

3. FRONTEND TESTS (manual testing in browser)

   A. Signup Flow:
   [ ] Visit http://localhost:3000/auth/signup
   [ ] Fill form: email, password (min 8 chars), full name, role
   [ ] Click "Sign Up"
   [ ] Verify redirected to /therapist or /patient based on role
   [ ] Verify tokens in localStorage (dev tools -> Application -> Local Storage)

   B. Logout:
   [ ] Click logout button (implement a simple one if not exists)
   [ ] Verify redirected to login page
   [ ] Verify tokens removed from localStorage

   C. Login Flow:
   [ ] Visit http://localhost:3000/auth/login
   [ ] Enter email and password
   [ ] Click "Login"
   [ ] Verify redirected based on role

   D. Protected Route:
   [ ] Logout
   [ ] Try to visit /therapist directly
   [ ] Verify redirected to /auth/login

   E. Token Refresh (requires waiting 30 min or manually expiring token):
   [ ] Login
   [ ] Wait for access token to expire (or manually change expiration to 1 min)
   [ ] Make API request
   [ ] Verify new access token retrieved automatically
   [ ] Verify request succeeds

4. SECURITY CHECKS:
   [ ] Passwords stored as bcrypt hashes (check database)
   [ ] UserResponse never includes hashed_password
   [ ] Refresh tokens stored as hashes (check database)
   [ ] Cannot access /auth/me without valid token
   [ ] Cannot refresh with revoked token
   [ ] Role-based access control works (therapist can't access patient-only routes)

5. ERROR HANDLING:
   [ ] Duplicate email signup -> "Email already registered"
   [ ] Wrong password -> "Incorrect email or password"
   [ ] Inactive account -> "Account is inactive"
   [ ] Expired token -> Auto-refresh or redirect to login

VALIDATION CRITERIA:
✅ All database tables and relationships correct
✅ All 5 API endpoints functional
✅ Signup + auto-login works
✅ Login redirects based on role
✅ Protected routes require authentication
✅ Token refresh happens automatically
✅ Logout revokes tokens
✅ Security checks pass

If all checks pass, Feature 1 (Authentication) is COMPLETE! 🎉

NEXT STEPS:
- Move to Feature 6 (Goal Tracking) - easiest next feature
- Or start Feature 2 (Analytics) if you want the complex features done first
```

---

# START NOW: 15-Window Maximum Parallelization

## ⏱️ TIMELINE: Complete Feature 1 in 70 Minutes

**Current Time:** _____________ (write this down!)
**Target Completion:** _____________ (+70 minutes)

---

## 🪟 WINDOW SETUP (Do this first - 3 minutes)

### Open 15 Claude Code Browser Tabs

**Quick method:**
1. Open Claude Code: https://claude.ai
2. Press Cmd+T (Mac) or Ctrl+T (Windows) 14 more times
3. Label each tab (right-click tab → rename or use tab numbers)

**Tab Labels:**
```
Tab 1:  1.1.1-UserBase
Tab 2:  1.1.2-AuthFields
Tab 3:  1.1.3-RoleFields
Tab 4:  1.1.4-Timestamps
Tab 5:  1.1.5-Session
Tab 6:  1.2.1-Config
Tab 7:  1.2.2-Password
Tab 8:  1.2.3-AccessToken
Tab 9:  1.2.4-RefreshToken
Tab 10: 1.2.6-EnvBackend
Tab 11: 1.4.1-TokenStore
Tab 12: 1.4.8-EnvFrontend
Tab 13: BUFFER
Tab 14: BUFFER
Tab 15: BUFFER
```

---

## 📋 PHASE 1: FOUNDATION (12 tasks, 12 minutes)

### Step 1: Copy ALL 12 Prompts (5 minutes)

Open this file in a separate window:
`prompts/FEATURE_1_ULTRA_FINE_GRAINED.md`

For each tab 1-12, copy the corresponding subtask:

#### **TAB 1 - Copy this entire prompt:**
Search for "## SUBTASK 1.1.1: Create User Model Base Structure" in FEATURE_1_ULTRA_FINE_GRAINED.md
Copy from "You are creating..." through all VALIDATION checkboxes
Paste into Tab 1
**DO NOT PRESS ENTER YET**

#### **TAB 2 - Copy this entire prompt:**
Search for "## SUBTASK 1.1.2: Add User Authentication Fields"
Copy entire prompt → Paste into Tab 2
**DO NOT PRESS ENTER YET**

#### **TAB 3 - Copy this entire prompt:**
Search for "## SUBTASK 1.1.3: Add User Role and Status Fields"
Copy entire prompt → Paste into Tab 3
**DO NOT PRESS ENTER YET**

#### **TAB 4 - Copy this entire prompt:**
Search for "## SUBTASK 1.1.4: Add User Timestamps"
Copy entire prompt → Paste into Tab 4
**DO NOT PRESS ENTER YET**

#### **TAB 5 - Copy this entire prompt:**
Search for "## SUBTASK 1.1.5: Create Session Model for Refresh Tokens"
Copy entire prompt → Paste into Tab 5
**DO NOT PRESS ENTER YET**

#### **TAB 6 - Copy this entire prompt:**
Search for "## SUBTASK 1.2.1: Create Auth Configuration File"
Copy entire prompt → Paste into Tab 6
**DO NOT PRESS ENTER YET**

#### **TAB 7 - Copy this entire prompt:**
Search for "## SUBTASK 1.2.2: Create Password Hashing Functions"
Copy entire prompt → Paste into Tab 7
**DO NOT PRESS ENTER YET**

#### **TAB 8 - Copy this entire prompt:**
Search for "## SUBTASK 1.2.3: Create Access Token Generation Function"
Copy entire prompt → Paste into Tab 8
**DO NOT PRESS ENTER YET**

#### **TAB 9 - Copy this entire prompt:**
Search for "## SUBTASK 1.2.4: Create Refresh Token Generation Function"
Copy entire prompt → Paste into Tab 9
**DO NOT PRESS ENTER YET**

#### **TAB 10 - Copy this entire prompt:**
Search for "## SUBTASK 1.2.6: Update Environment Variables Example"
Copy entire prompt → Paste into Tab 10
**DO NOT PRESS ENTER YET**

#### **TAB 11 - Copy this entire prompt:**
Search for "## SUBTASK 1.4.1: Create Token Storage Utility"
Copy entire prompt → Paste into Tab 11
**DO NOT PRESS ENTER YET**

#### **TAB 12 - Copy this entire prompt:**
Search for "## SUBTASK 1.4.8: Create Environment Variables File"
Copy entire prompt → Paste into Tab 12
**DO NOT PRESS ENTER YET**

---

### Step 2: SYNCHRONIZED START (30 seconds)

**IMPORTANT:** You need to press Enter on all 12 tabs within 30 seconds of each other.

**Method A: Quick succession**
1. Click Tab 1 → Press Enter
2. Immediately click Tab 2 → Press Enter
3. Continue through Tab 12
4. Should take ~20-30 seconds total

**Method B: Keyboard shortcuts (faster)**
1. Cmd+1 (or Ctrl+1) → Enter
2. Cmd+2 → Enter
3. Cmd+3 → Enter
... continue through Cmd+9, then click tabs 10-12

**YOU SHOULD SEE:**
Each tab showing "I'm implementing..." and a progress indicator

**START TIME:** _____________ (write this down!)

---

### Step 3: MONITOR PROGRESS (10 minutes)

Watch for completions. They'll come in waves:

**Expected completion order:**
```
~3 min:  Tab 10 ✅ (1.2.6 - simple env file)
~3 min:  Tab 12 ✅ (1.4.8 - simple env file)
~5 min:  Tab 1 ✅ (1.1.1 - User base)
~5 min:  Tab 2 ✅ (1.1.2 - Auth fields)
~5 min:  Tab 3 ✅ (1.1.3 - Role fields)
~5 min:  Tab 4 ✅ (1.1.4 - Timestamps)
~7 min:  Tab 6 ✅ (1.2.1 - Config)
~8 min:  Tab 7 ✅ (1.2.2 - Password)
~8 min:  Tab 5 ✅ (1.1.5 - Session)
~8 min:  Tab 9 ✅ (1.2.4 - Refresh token)
~10 min: Tab 8 ✅ (1.2.3 - Access token)
~10 min: Tab 11 ✅ (1.4.1 - Token storage)
```

**What to do while waiting:**
- Open `prompts/EXECUTION_DASHBOARD_TEMPLATE.md`
- Copy it to a new file: `MY_EXECUTION_DASHBOARD.md`
- Update the status column as each tab completes
- Mark start/end times

---

### Step 4: QUICK VALIDATION (2 minutes)

Once all 12 tabs show completion, verify files exist:

```bash
# Run this command:
cd /Users/vishnuanapalli/Desktop/Rohin\ \&\ Vish\ Global\ Domination/peerbridge\ proj/therabridge-backend

# Check backend files
ls -lh backend/app/auth/models.py
ls -lh backend/app/auth/config.py
ls -lh backend/app/auth/utils.py
ls -lh backend/.env.example

# Check frontend files
ls -lh frontend/lib/token-storage.ts
ls -lh frontend/.env.local
```

**ALL files should exist.** If any are missing, use buffer tabs (13-15) to re-run that subtask.

**PHASE 1 COMPLETE TIME:** _____________ (should be ~12-15 min from start)

✅ **Checkpoint:** Mark Phase 1 complete in your dashboard!

---

## 📋 PHASE 2: INTEGRATION (8 tasks, 15 minutes)

Phase 2 has dependencies, so we do it in 3 sub-phases:

### SUB-PHASE 2A: Parallel Windows (3 tasks, 12 minutes)

**TAB 1 - New prompt:**
Search for "## SUBTASK 1.1.6: Add User-Session Relationship"
Copy entire prompt → Paste into Tab 1 → Press Enter

**TAB 4 - New prompt:**
Search for "## SUBTASK 1.2.5: Create Token Verification Function"
Copy entire prompt → Paste into Tab 4 → Press Enter

**TAB 6 - New prompt:**
Search for "## SUBTASK 1.4.2: Create API Client with Auth Interceptor"
Copy entire prompt → Paste into Tab 6 → Press Enter

**WAIT ~12 minutes for all 3 to complete**

---

### SUB-PHASE 2B: Parallel Windows (3 tasks, 15 minutes)

**TAB 2 - New prompt:**
Search for "## SUBTASK 1.1.7: Create Pydantic Schemas for User"
Copy entire prompt → Paste into Tab 2 → Press Enter

**TAB 5 - New prompt:**
Search for "## SUBTASK 1.3.1: Create Database Dependency"
Copy entire prompt → Paste into Tab 5 → Press Enter

**TAB 7 - New prompt:**
Search for "## SUBTASK 1.4.3: Create Auth Context and Provider"
Copy entire prompt → Paste into Tab 7 → Press Enter

**WAIT ~15 minutes for all 3 to complete**

---

### SUB-PHASE 2C: Parallel Windows (2 tasks, 10 minutes)

**TAB 3 - New prompt:**
Search for "## SUBTASK 1.1.8: Create Pydantic Schemas for Tokens"
Copy entire prompt → Paste into Tab 3 → Press Enter

**TAB 8 - New prompt:**
Search for "## SUBTASK 1.1.9: Create Alembic Migration"
Copy entire prompt → Paste into Tab 8 → Press Enter

**WAIT ~10 minutes for both to complete**

**PHASE 2 COMPLETE TIME:** _____________ (should be ~40 min from start)

✅ **Checkpoint:** Mark Phase 2 complete in your dashboard!

---

## 📋 PHASE 3: API & UI (7 tasks, 15 minutes)

### SUB-PHASE 3A: Parallel Windows (6 tasks, 15 minutes)

**TAB 1 - New prompt:**
Search for "## SUBTASK 1.3.2: Create Current User Dependency"
Copy entire prompt → Paste into Tab 1 → Press Enter

**TAB 3 - New prompt:**
Search for "## SUBTASK 1.3.4: Create Signup Endpoint"
Copy entire prompt → Paste into Tab 3 → Press Enter

**TAB 4 - New prompt:**
Search for "## SUBTASK 1.3.5: Create Login Endpoint"
Copy entire prompt → Paste into Tab 4 → Press Enter

**TAB 5 - New prompt:**
Search for "## SUBTASK 1.4.4: Create Login Page"
Copy entire prompt → Paste into Tab 5 → Press Enter

**TAB 6 - New prompt:**
Search for "## SUBTASK 1.4.5: Create Signup Page"
Copy entire prompt → Paste into Tab 6 → Press Enter

**TAB 7 - New prompt:**
Search for "## SUBTASK 1.4.6: Create Protected Route Wrapper"
Copy entire prompt → Paste into Tab 7 → Press Enter

**Press Enter on all 6 tabs within 30 seconds**

**WAIT ~15 minutes for all 6 to complete**

---

### SUB-PHASE 3B: Sequential (1 task, 10 minutes)

**TAB 2 - New prompt:**
Search for "## SUBTASK 1.3.3: Create Role-Based Access Control Dependency"
Copy entire prompt → Paste into Tab 2 → Press Enter

**WAIT ~10 minutes**

**PHASE 3 COMPLETE TIME:** _____________ (should be ~55 min from start)

✅ **Checkpoint:** Mark Phase 3 complete in your dashboard!

---

## 📋 PHASE 4: FINAL INTEGRATION (3 tasks, 10 minutes)

These must run sequentially:

**TAB 1 - New prompt:**
Search for "## SUBTASK 1.3.6: Create Token Refresh and Logout Endpoints"
Copy entire prompt → Paste into Tab 1 → Press Enter
**WAIT for completion (~10 min)**

**TAB 2 - New prompt:**
Search for "## SUBTASK 1.3.7: Create Get Current User Endpoint and Register Router"
Copy entire prompt → Paste into Tab 2 → Press Enter
**WAIT for completion (~8 min)**

**TAB 3 - New prompt:**
Search for "## SUBTASK 1.4.7: Wrap App with AuthProvider"
Copy entire prompt → Paste into Tab 3 → Press Enter
**WAIT for completion (~5 min)**

**PHASE 4 COMPLETE TIME:** _____________ (should be ~65 min from start)

✅ **Checkpoint:** Mark Phase 4 complete in your dashboard!

---

## 📋 PHASE 5: INTEGRATION TESTING (1 task, 20 minutes)

**TAB 1 - Integration Test:**
Search for "## INTEGRATION TEST PROMPT" in FEATURE_1_ULTRA_FINE_GRAINED.md
Copy entire prompt → Paste into Tab 1 → Press Enter

This will run all the E2E tests. Follow along and check off each validation item.

**PHASE 5 COMPLETE TIME:** _____________ (should be ~85 min from start)

✅ **Checkpoint:** All tests pass? FEATURE 1 COMPLETE! 🎉

---

## 🎉 COMPLETION CHECKLIST

- [ ] All 29 subtasks completed
- [ ] All files exist and have content
- [ ] Can start backend: `cd backend && uvicorn app.main:app --reload`
- [ ] Can start frontend: `cd frontend && npm run dev`
- [ ] Can signup at http://localhost:3000/auth/signup
- [ ] Can login at http://localhost:3000/auth/login
- [ ] Protected routes redirect to login when not authenticated
- [ ] Tokens stored in localStorage
- [ ] All integration tests pass

**TOTAL TIME:** _____________
**TARGET:** 70 minutes
**ACTUAL:** _____________ minutes

---

## 🚨 EMERGENCY: If Something Goes Wrong

### Error in Phase 1
- Use buffer tabs (13-15) to re-run failed task
- Don't wait - other tabs can continue
- Fix and move on

### Dependency Error
- Check if prerequisite subtask actually completed
- Look at the DEPENDENCIES section of the failing prompt
- Re-run the prerequisite first

### Can't Monitor 12 Windows
- Reduce to 6 windows
- Do Phase 1 in 2 batches of 6 tasks each
- Will take ~20 min instead of 12 min (still fast!)

### Too Overwhelming
- PAUSE all windows
- Take a 5-minute break
- Resume with 3 windows instead
- Complete sequentially (still better than starting from scratch)

---

## 💡 PRO TIPS

1. **Use two monitors:** Left for Claude Code tabs, right for documentation
2. **Audio cues:** Turn on tab sound notifications to hear when tabs complete
3. **Batch validation:** Don't validate after each task, wait for phase completion
4. **Trust the process:** The prompts are designed to work independently
5. **Take breaks:** After each phase, stand up and stretch for 2 minutes

---

## 🎯 READY TO START?

1. ✅ 15 Claude Code tabs open and labeled
2. ✅ FEATURE_1_ULTRA_FINE_GRAINED.md open in separate window
3. ✅ Execution dashboard ready for tracking
4. ✅ Coffee/water nearby
5. ✅ Timer ready to track progress

**WHEN READY, START PHASE 1 STEP 1!**

Write your start time here: _____________

**LET'S BUILD! 🚀**
