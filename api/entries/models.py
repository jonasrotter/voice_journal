"""Journal Entry SQLAlchemy models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.db.database import Base


class JournalEntry(Base):
    """Journal entry database model."""
    
    __tablename__ = "journal_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    audio_url = Column(String(500), nullable=False)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    emotion = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="entries")
    
    def __repr__(self) -> str:
        return f"<JournalEntry(id={self.id}, status={self.status})>"


class Subscription(Base):
    """Subscription database model."""
    
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default="free")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self) -> str:
        return f"<Subscription(user_id={self.user_id}, plan={self.plan})>"
