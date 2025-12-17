"""
Pydantic schemas for User API input/output validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.auth.models import UserRole


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr  # Auto-validates email format
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    role: UserRole


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for API responses - NEVER includes hashed_password"""
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
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
