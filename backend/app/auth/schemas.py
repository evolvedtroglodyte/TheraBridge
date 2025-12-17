"""
Pydantic schemas for User API input/output validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.auth.models import UserRole
from app.auth.utils import validate_password_strength


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr  # Auto-validates email format
    password: str = Field(
        ...,
        min_length=12,
        description="Password must be at least 12 characters with uppercase, lowercase, number, and special character"
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements"""
        try:
            validate_password_strength(v)
        except ValueError as e:
            raise ValueError(str(e))
        return v

    @property
    def full_name(self) -> str:
        """Computed full_name for backwards compatibility"""
        return f"{self.first_name} {self.last_name}".strip()


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for API responses - NEVER includes hashed_password"""
    id: UUID
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy models


class TokenResponse(BaseModel):
    """Schema for token response after login/signup"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access_token expires


class TokenRefresh(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
