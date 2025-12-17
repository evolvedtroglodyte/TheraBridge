"""
Authentication endpoints for user login, signup, and token management.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_db, get_current_user
from app.auth.models import AuthSession
from app.models.db_models import User
from app.auth.schemas import UserLogin, TokenResponse, TokenRefresh, UserResponse
from app.auth.utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token
)
from app.auth.config import auth_config


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
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


@router.post("/refresh", response_model=TokenResponse)
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

    # Generate new access token
    access_token = create_access_token(user.id, user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=token_data.refresh_token,  # Return same refresh token
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
