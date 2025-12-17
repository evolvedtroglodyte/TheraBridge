"""
Authentication models - User is imported from db_models, AuthSession defined here
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

# Import User and UserRole from existing models to avoid duplication
from app.models.db_models import User
from app.models.schemas import UserRole

# Re-export for convenience
__all__ = ["User", "UserRole", "AuthSession"]


class AuthSession(Base):
    """AuthSession model for storing refresh tokens (renamed to avoid conflict with therapy Session)"""
    __tablename__ = "auth_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Refresh token (hashed for security)
    refresh_token = Column(String, nullable=False, unique=True)

    # Expiration tracking
    expires_at = Column(DateTime, nullable=False)

    # Revocation flag (for logout)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship("User", back_populates="auth_sessions")
