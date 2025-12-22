"""Journal Entry Pydantic schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class EntryStatus(str, Enum):
    """Journal entry processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class EntryBase(BaseModel):
    """Base entry schema."""
    pass


class EntryCreate(EntryBase):
    """Schema for creating a new entry (internal use)."""
    audio_url: str = Field(..., description="URL to stored audio file")


class EntryUpdate(BaseModel):
    """Schema for updating an entry."""
    transcript: Optional[str] = Field(None, description="Updated transcript")
    summary: Optional[str] = Field(None, description="Updated summary")


class EntryRead(BaseModel):
    """Schema for reading entry data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Entry unique identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    audio_url: str = Field(..., description="URL to audio file")
    transcript: Optional[str] = Field(None, description="Transcribed text")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    emotion: Optional[str] = Field(None, description="Detected emotional tone")
    status: EntryStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")


class EntryCreateResponse(BaseModel):
    """Response schema for entry creation."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Entry unique identifier")
    status: EntryStatus = Field(..., description="Processing status")
    audio_url: str = Field(..., description="URL to stored audio file")
    created_at: datetime = Field(..., description="Creation timestamp")


class EntryListResponse(BaseModel):
    """Response schema for entry listing."""
    entries: List[EntryRead] = Field(..., description="List of entries")
    total: int = Field(..., description="Total number of entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of entries per page")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., description="Error message")
