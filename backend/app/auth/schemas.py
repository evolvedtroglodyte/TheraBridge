"""
Pydantic schemas for User API input/output validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.auth.models import UserRole
from app.auth.utils import validate_password_strength


class UserCreate(BaseModel):
    """Schema for user registration - supports both full_name and first_name/last_name formats"""
    email: EmailStr  # Auto-validates email format
    password: str = Field(
        ...,
        min_length=12,
        description="Password must be at least 12 characters with uppercase, lowercase, number, and special character"
    )
    # Support both input formats - all optional, validated in model_validator
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: UserRole

    @model_validator(mode='before')
    @classmethod
    def validate_names(cls, data):
        """
        Accept either full_name OR first_name+last_name.
        If full_name provided, split into first_name and last_name.
        Ensures both first_name and last_name are populated regardless of input format.
        """
        # Convert to dict if needed
        if not isinstance(data, dict):
            data = dict(data)

        has_full_name = data.get('full_name')
        has_first_name = data.get('first_name')
        has_last_name = data.get('last_name')

        # Case 1: full_name provided (frontend format)
        if has_full_name and not (has_first_name or has_last_name):
            full_name = data['full_name'].strip()
            if not full_name:
                raise ValueError("full_name cannot be empty")

            # Split on first space
            parts = full_name.split(None, 1)  # Split on whitespace, max 2 parts
            if len(parts) == 2:
                data['first_name'] = parts[0]
                data['last_name'] = parts[1]
            else:
                # Single name - use as first_name, use same as last_name
                data['first_name'] = parts[0]
                data['last_name'] = parts[0]  # Use same name for both fields

        # Case 2: first_name and last_name provided (backend format)
        elif has_first_name and has_last_name:
            # Validate first_name is not empty
            if not data['first_name'].strip():
                raise ValueError("first_name cannot be empty")
            # last_name can be empty, but if provided must not be whitespace-only
            if data['last_name'] and not data['last_name'].strip():
                raise ValueError("last_name cannot be whitespace only")
            # Compute full_name for property
            data['full_name'] = f"{data['first_name']} {data['last_name']}".strip()

        # Case 3: Neither format provided
        else:
            raise ValueError("Either 'full_name' or both 'first_name' and 'last_name' must be provided")

        return data

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
    def full_name_property(self) -> str:
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
