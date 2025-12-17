"""
Authentication endpoints for user login, signup, and token management.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import get_db, get_current_user
from app.auth.models import AuthSession
from app.models.db_models import User
from app.auth.schemas import UserLogin, UserCreate, TokenResponse, TokenRefresh, UserResponse
from app.auth.utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_refresh_token
)
from app.auth.config import auth_config
from app.middleware.rate_limit import limiter


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and create new session.

    Rate limit: 5 requests per minute per IP address (prevents brute force attacks)

    Args:
        request: FastAPI request object (required for rate limiting)
        credentials: Email and password
        db: Database session

    Returns:
        Access token, refresh token, and expiration info

    Raises:
        HTTPException 401: If email/password incorrect or account inactive
        HTTPException 429: If rate limit exceeded
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
    session = AuthSession(
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


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
def signup(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user account and return authentication tokens.

    Rate limit: 3 requests per hour per IP address (prevents account spam)

    Args:
        request: FastAPI request object (required for rate limiting)
        user_data: Email, password, full name, and role
        db: Database session

    Returns:
        Access token, refresh token, and expiration info

    Raises:
        HTTPException 409: If email already registered
        HTTPException 429: If rate limit exceeded
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user with first_name/last_name and computed full_name
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        full_name=user_data.full_name,  # Computed from first_name + last_name
        role=user_data.role,
        is_active=True,
        is_verified=False  # Requires email verification (future feature)
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Generate tokens
    access_token = create_access_token(new_user.id, new_user.role.value)
    refresh_token = create_refresh_token()

    # Store refresh token in database
    auth_session = AuthSession(
        user_id=new_user.id,
        refresh_token=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(auth_session)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh_token(request: Request, token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Get new access token using refresh token (with rotation).

    Token rotation is a security best practice: the old refresh token is revoked
    and a new one is issued, preventing replay attacks if a token is compromised.

    Rate limit: 10 requests per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        token_data: Refresh token
        db: Database session

    Returns:
        New access token AND new refresh token (rotation)

    Raises:
        HTTPException 401: If refresh token invalid/expired/revoked
        HTTPException 429: If rate limit exceeded
    """
    # Find session with this refresh token
    session = db.query(AuthSession).filter(
        AuthSession.refresh_token == hash_refresh_token(token_data.refresh_token)
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

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # REVOKE OLD TOKEN (rotation security)
    session.is_revoked = True
    db.commit()

    # Generate NEW tokens
    new_access_token = create_access_token(user.id, user.role.value)
    new_refresh_token = create_refresh_token()

    # Create NEW session with new refresh token
    new_session = AuthSession(
        user_id=user.id,
        refresh_token=hash_refresh_token(new_refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,  # Return NEW refresh token
        expires_in=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
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
    session = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.id,
        AuthSession.refresh_token == hash_refresh_token(token_data.refresh_token)
    ).first()

    if session:
        session.is_revoked = True
        db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.

    Args:
        current_user: User from JWT token

    Returns:
        User information (without password)
    """
    return UserResponse.from_orm(current_user)
