"""Journal Entry service layer."""
import os
import uuid
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.entries.models import JournalEntry
from api.entries.schemas import EntryUpdate, EntryStatus
from api.config import settings


def get_entry_by_id(db: Session, entry_id: UUID) -> Optional[JournalEntry]:
    """Get entry by ID."""
    return db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()


def get_entry_by_id_for_user(db: Session, entry_id: UUID, user_id: UUID) -> Optional[JournalEntry]:
    """Get entry by ID ensuring it belongs to the user."""
    return db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.user_id == user_id
    ).first()


def get_user_entries(
    db: Session,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[JournalEntry], int]:
    """Get paginated entries for a user, ordered by created_at DESC."""
    query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)
    
    total = query.count()
    
    entries = (
        query
        .order_by(desc(JournalEntry.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return entries, total


def create_entry(db: Session, user_id: UUID, audio_url: str) -> JournalEntry:
    """Create a new journal entry."""
    entry = JournalEntry(
        user_id=user_id,
        audio_url=audio_url,
        status=EntryStatus.UPLOADED
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry: JournalEntry, entry_data: EntryUpdate) -> JournalEntry:
    """Update an existing entry."""
    update_data = entry_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry


def update_entry_status(db: Session, entry: JournalEntry, status: EntryStatus) -> JournalEntry:
    """Update entry processing status."""
    entry.status = status
    db.commit()
    db.refresh(entry)
    return entry


def update_entry_ai_results(
    db: Session,
    entry: JournalEntry,
    transcript: str,
    summary: str,
    emotion: str
) -> JournalEntry:
    """Update entry with AI processing results."""
    entry.transcript = transcript
    entry.summary = summary
    entry.emotion = emotion
    entry.status = EntryStatus.PROCESSED
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry: JournalEntry) -> None:
    """Permanently delete an entry and its associated audio file."""
    # Delete audio file
    if entry.audio_url:
        audio_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(entry.audio_url))
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    db.delete(entry)
    db.commit()


def store_audio_file(audio_data: bytes, filename: str) -> str:
    """Store audio file and return URL."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(filename)[1] or ".wav"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(audio_data)
    
    return f"/uploads/{unique_filename}"
