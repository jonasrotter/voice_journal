"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=128, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="New password")


class UserRead(UserBase):
    """Schema for reading user data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="User unique identifier")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserInDB(UserRead):
    """Schema for user data stored in database."""
    password_hash: str
