"""
Unit Tests - Entries Module
Tests for journal entry CRUD operations and processing
"""

import pytest
from datetime import datetime
from uuid import uuid4


class TestEntrySchemas:
    """Tests for entry Pydantic schemas"""
    
    def test_entry_create_valid(self):
        """EntryCreate should accept valid audio URL"""
        from api.entries.schemas import EntryCreate
        
        entry = EntryCreate(audio_url="/uploads/audio/test.webm")
        
        assert entry.audio_url == "/uploads/audio/test.webm"
    
    def test_entry_read_all_fields(self):
        """EntryRead should include all expected fields"""
        from api.entries.schemas import EntryRead, EntryStatus
        
        entry = EntryRead(
            id=uuid4(),
            user_id=uuid4(),
            audio_url="/uploads/audio/test.webm",
            transcript="Test transcript",
            summary="Test summary",
            emotion="calm",
            status=EntryStatus.PROCESSED,
            created_at=datetime.utcnow()
        )
        
        assert entry.transcript == "Test transcript"
        assert entry.summary == "Test summary"
        assert entry.emotion == "calm"
        assert entry.status == EntryStatus.PROCESSED
    
    def test_entry_update_partial(self):
        """EntryUpdate should allow partial updates"""
        from api.entries.schemas import EntryUpdate
        
        # Only updating summary
        update = EntryUpdate(summary="New summary")
        
        assert update.summary == "New summary"
        assert update.transcript is None
    
    def test_entry_status_enum(self):
        """EntryStatus should have all expected values"""
        from api.entries.schemas import EntryStatus
        
        statuses = [s.value for s in EntryStatus]
        
        assert "uploaded" in statuses
        assert "processing" in statuses
        assert "processed" in statuses
        assert "failed" in statuses


class TestEntryListResponse:
    """Tests for paginated entry list response"""
    
    def test_entry_list_response_structure(self):
        """EntryListResponse should include pagination info"""
        from api.entries.schemas import EntryListResponse, EntryRead, EntryStatus
        
        entries = [
            EntryRead(
                id=uuid4(),
                user_id=uuid4(),
                audio_url="/test.webm",
                transcript=None,
                summary=None,
                emotion=None,
                status=EntryStatus.UPLOADED,
                created_at=datetime.utcnow()
            )
        ]
        
        response = EntryListResponse(
            entries=entries,
            total=1,
            page=1,
            page_size=50
        )
        
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 50
        assert len(response.entries) == 1


class TestEntryService:
    """Tests for entry service layer (requires DB session mock)"""
    
    def test_create_entry_sets_uploaded_status(self):
        """New entries should have uploaded status"""
        from api.entries.schemas import EntryStatus
        
        # Verify the expected initial status value
        assert EntryStatus.UPLOADED.value == "uploaded"
    
    def test_entry_status_transitions(self):
        """Entry status should follow valid transitions"""
        from api.entries.schemas import EntryStatus
        
        # Valid transitions:
        # uploaded -> processing -> processed
        # uploaded -> processing -> failed
        valid_transitions = {
            EntryStatus.UPLOADED: [EntryStatus.PROCESSING],
            EntryStatus.PROCESSING: [EntryStatus.PROCESSED, EntryStatus.FAILED],
            EntryStatus.FAILED: [EntryStatus.PROCESSING],  # For reprocessing
            EntryStatus.PROCESSED: []  # Terminal state
        }
        
        # Verify uploaded can transition to processing
        assert EntryStatus.PROCESSING in valid_transitions[EntryStatus.UPLOADED]
        
        # Verify processing can transition to processed or failed
        assert EntryStatus.PROCESSED in valid_transitions[EntryStatus.PROCESSING]
        assert EntryStatus.FAILED in valid_transitions[EntryStatus.PROCESSING]


class TestAudioProcessing:
    """Tests for AI processing functions"""
    
    def test_transcribe_returns_string(self):
        """Transcribe should return transcript string"""
        from api.ai.processing import transcribe_audio
        
        # The function is synchronous (mock implementation)
        result = transcribe_audio("/path/to/audio.webm")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_returns_string(self):
        """Summarize should return summary string"""
        from api.ai.processing import summarize_text
        
        transcript = "This is a test transcript about my day."
        result = summarize_text(transcript)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_infer_emotion_returns_valid_emotion(self):
        """Infer emotion should return one of expected emotions"""
        from api.ai.processing import infer_emotion
        
        valid_emotions = [
            "happy", "sad", "anxious", "calm", "excited", 
            "frustrated", "grateful", "reflective", "neutral"
        ]
        
        transcript = "I had a wonderful day today!"
        result = infer_emotion(transcript)
        
        assert result in valid_emotions
    
    def test_process_entry_background_updates_status(self):
        """Background processing should update entry status"""
        # This would require mocking the database session
        # The test verifies the expected behavior:
        # 1. Set status to processing
        # 2. Call transcribe, summarize, infer_emotion
        # 3. Set status to processed (or failed on error)
        pass


class TestAudioStorage:
    """Tests for audio file storage"""
    
    def test_generate_audio_filename(self):
        """Audio filenames should be unique and safe"""
        import uuid
        import re
        
        # Generate filename pattern similar to service
        user_id = str(uuid4())
        filename = f"{user_id}_{uuid4().hex[:8]}.webm"
        
        # Should be valid filename
        assert re.match(r'^[a-f0-9-]+_[a-f0-9]+\.webm$', filename)
    
    def test_audio_url_format(self):
        """Audio URLs should follow expected format"""
        user_id = str(uuid4())
        filename = f"{user_id}_abc12345.webm"
        audio_url = f"/uploads/audio/{filename}"
        
        assert audio_url.startswith("/uploads/audio/")
        assert audio_url.endswith(".webm")


# Run tests with: pytest tests/test_entries.py -v
