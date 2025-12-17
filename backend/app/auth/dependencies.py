"""
FastAPI dependencies for authentication
"""
from typing import Generator
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import SessionLocal
from app.auth.utils import decode_access_token
from app.models.db_models import User


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


# Security scheme for JWT Bearer tokens
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
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
