"""Authentication Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: str | None = Field(None, description="User ID from token")


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
