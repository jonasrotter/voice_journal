"""Journal Entry router."""
import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from api.db import get_db
from api.auth.dependencies import get_current_user
from api.users.models import User
from api.entries.schemas import (
    EntryRead,
    EntryUpdate,
    EntryCreateResponse,
    EntryListResponse,
    EntryStatus
)
from api.entries import service
from api.ai.processing import process_entry_background
from api.storage.blob_service import get_storage_service
from api.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=EntryCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(..., description="Audio file to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EntryCreateResponse:
    """Upload audio and create a new journal entry."""
    # Validate file size
    content = await audio.read()
    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds maximum size of {settings.MAX_AUDIO_SIZE_MB}MB"
        )
    
    # Validate content type (allow MIME types with codecs, e.g., audio/webm;codecs=opus)
    allowed_types = ["audio/wav", "audio/webm", "audio/mp3", "audio/mpeg", "audio/ogg"]
    if audio.content_type:
        # Extract base MIME type (before semicolon)
        base_content_type = audio.content_type.split(';')[0].strip().lower()
        if base_content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported audio format. Allowed: {', '.join(allowed_types)}"
            )
    
    # Store audio file (with username for Azure Blob naming)
    audio_url = service.store_audio_file(content, audio.filename or "audio.wav", current_user.email)
    
    # Create entry in database
    entry = service.create_entry(db, current_user.id, audio_url)
    
    # Queue background processing
    background_tasks.add_task(process_entry_background, entry.id, db)
    
    return EntryCreateResponse(
        id=entry.id,
        status=entry.status,
        audio_url=entry.audio_url,
        created_at=entry.created_at
    )


@router.get("", response_model=EntryListResponse)
def list_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Entries per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EntryListResponse:
    """List all journal entries for the current user."""
    entries, total = service.get_user_entries(db, current_user.id, page, page_size)
    
    return EntryListResponse(
        entries=[EntryRead.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{entry_id}", response_model=EntryRead)
def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EntryRead:
    """Get a specific journal entry."""
    entry = service.get_entry_by_id_for_user(db, entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    return EntryRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=EntryRead)
def update_entry(
    entry_id: UUID,
    entry_data: EntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EntryRead:
    """Update a journal entry's transcript or summary."""
    entry = service.get_entry_by_id_for_user(db, entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    updated_entry = service.update_entry(db, entry, entry_data)
    return EntryRead.model_validate(updated_entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Permanently delete a journal entry and its associated audio."""
    entry = service.get_entry_by_id_for_user(db, entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    service.delete_entry(db, entry)


@router.post("/{entry_id}/reprocess", response_model=EntryRead)
def reprocess_entry(
    entry_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EntryRead:
    """Reprocess an entry's AI analysis."""
    entry = service.get_entry_by_id_for_user(db, entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Reset status and queue for reprocessing
    entry = service.update_entry_status(db, entry, EntryStatus.PROCESSING)
    background_tasks.add_task(process_entry_background, entry.id, db)
    
    return EntryRead.model_validate(entry)


@router.get("/{entry_id}/audio")
def stream_audio(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Stream audio file for an entry.
    
    This endpoint acts as a proxy to Azure Blob Storage, allowing the frontend
    to access audio files without needing direct blob storage credentials.
    Works with DefaultAzureCredential (Azure CLI locally, Managed Identity in Azure).
    """
    entry = service.get_entry_by_id_for_user(db, entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    if not entry.audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio file associated with this entry"
        )
    
    try:
        storage_service = get_storage_service()
        audio_data = storage_service.download_audio(entry.audio_url)
        
        # Determine content type from URL extension
        ext = os.path.splitext(entry.audio_url)[1].lower()
        content_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac"
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=audio{ext}",
                "Accept-Ranges": "bytes"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audio: {str(e)}"
        )
