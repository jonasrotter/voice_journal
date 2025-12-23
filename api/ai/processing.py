"""AI processing functions for journal entries.

This module handles the AI processing pipeline for journal entries:
1. Transcription: Audio to text (Azure OpenAI Whisper, Azure Speech, or mock)
2. Summarization: Generate concise summary (Azure OpenAI GPT-4o or mock)
3. Emotion Analysis: Detect emotional tone (Azure OpenAI GPT-4o or mock)

The processing mode is controlled by the AI_PROCESSING_MODE environment variable:
- "azure_openai": Use Azure OpenAI for all processing (Whisper + GPT-4o)
- "azure_speech": Use Azure Speech for transcription, Azure OpenAI for analysis
- "mock": Use mock data (default for development)
"""
import os
import random
import logging
from uuid import UUID
from typing import Optional, Tuple

from api.config import settings
from api.entries.schemas import EntryStatus

logger = logging.getLogger(__name__)


# Mock transcriptions for fallback/development
MOCK_TRANSCRIPTIONS = [
    "Today was a challenging day at work. I had several meetings that ran over time, "
    "but I managed to complete the project proposal. I'm feeling a bit tired but accomplished.",
    
    "I've been thinking a lot about my goals lately. I want to focus more on personal growth "
    "and spend quality time with family. Small steps every day make a big difference.",
    
    "Had a wonderful morning walk in the park. The weather was perfect and I saw some beautiful birds. "
    "These quiet moments really help me stay centered and grateful.",
    
    "Feeling a bit anxious about the upcoming presentation. I've prepared well, "
    "but there's always that nervous energy. Taking deep breaths and staying positive.",
    
    "Reflected on the past week. There were ups and downs, but overall I'm grateful "
    "for the support of friends and the progress I've made on my personal projects."
]


def _transcribe_mock(audio_url: str) -> str:
    """Return mock transcription for development."""
    return random.choice(MOCK_TRANSCRIPTIONS)


def _summarize_mock(transcript: str) -> str:
    """Generate mock summary for development."""
    first_sentence = transcript.split('.')[0] + '.'
    prefixes = ["Today's reflection: ", "Key theme: ", "Main thought: "]
    return random.choice(prefixes) + first_sentence


def _infer_emotion_mock(transcript: str) -> str:
    """Infer emotion using simple keyword matching for development."""
    transcript_lower = transcript.lower()
    
    emotion_keywords = {
        "grateful": ["grateful", "thankful", "appreciate", "blessed", "wonderful"],
        "anxious": ["anxious", "worried", "nervous", "stress", "overwhelm"],
        "hopeful": ["hope", "excited", "looking forward", "positive", "optimistic"],
        "reflective": ["thinking", "reflect", "consider", "ponder", "realize"],
        "accomplished": ["accomplished", "achieved", "completed", "proud", "success"],
        "peaceful": ["calm", "peaceful", "serene", "quiet", "centered"],
        "tired": ["tired", "exhausted", "drained", "fatigue", "sleepy"],
        "happy": ["happy", "joy", "delighted", "pleased", "content"]
    }
    
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in transcript_lower:
                return emotion
    
    return "neutral"


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text.
    
    Uses the appropriate service based on AI_PROCESSING_MODE:
    - azure_openai: Azure OpenAI Whisper
    - azure_speech: Azure Speech Services
    - mock: Returns mock transcription
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Transcribed text
    """
    mode = settings.AI_PROCESSING_MODE.lower()
    
    if mode == "azure_openai":
        from api.ai.azure_services import get_azure_openai_service
        service = get_azure_openai_service()
        
        if service.is_available:
            transcript = service.transcribe_audio(audio_path)
            if transcript:
                return transcript
            logger.warning("Azure OpenAI transcription failed, falling back to mock")
        else:
            logger.warning("Azure OpenAI not available, falling back to mock")
    
    elif mode == "azure_speech":
        from api.ai.azure_services import get_azure_speech_service
        service = get_azure_speech_service()
        
        if service.is_available:
            transcript = service.transcribe_audio(audio_path)
            if transcript:
                return transcript
            logger.warning("Azure Speech transcription failed, falling back to mock")
        else:
            logger.warning("Azure Speech not available, falling back to mock")
    
    # Fallback to mock
    return _transcribe_mock(audio_path)


def summarize_text(transcript: str) -> str:
    """
    Generate a summary of the transcribed text.
    
    Uses Azure OpenAI GPT-4o if configured, otherwise mock summary.
    
    Args:
        transcript: The transcribed text to summarize
        
    Returns:
        Summary text
    """
    mode = settings.AI_PROCESSING_MODE.lower()
    
    if mode in ["azure_openai", "azure_speech"]:
        from api.ai.azure_services import get_azure_openai_service
        service = get_azure_openai_service()
        
        if service.is_available:
            summary = service.summarize_text(transcript)
            if summary:
                return summary
            logger.warning("Azure OpenAI summarization failed, falling back to mock")
        else:
            logger.warning("Azure OpenAI not available for summarization, falling back to mock")
    
    return _summarize_mock(transcript)


def infer_emotion(transcript: str) -> str:
    """
    Analyze emotional tone of the transcript.
    
    Uses Azure OpenAI GPT-4o if configured, otherwise keyword-based mock.
    
    Args:
        transcript: The transcribed text to analyze
        
    Returns:
        Primary emotion label
    """
    mode = settings.AI_PROCESSING_MODE.lower()
    
    if mode in ["azure_openai", "azure_speech"]:
        from api.ai.azure_services import get_azure_openai_service
        service = get_azure_openai_service()
        
        if service.is_available:
            emotion = service.analyze_emotion(transcript)
            if emotion:
                return emotion
            logger.warning("Azure OpenAI emotion analysis failed, falling back to mock")
        else:
            logger.warning("Azure OpenAI not available for emotion analysis, falling back to mock")
    
    return _infer_emotion_mock(transcript)


def process_transcript(transcript: str) -> Tuple[str, str]:
    """
    Process transcript to generate summary and emotion in one call.
    
    This is more efficient than calling summarize_text and infer_emotion separately
    when using Azure OpenAI.
    
    Args:
        transcript: The transcribed text to process
        
    Returns:
        Tuple of (summary, emotion)
    """
    mode = settings.AI_PROCESSING_MODE.lower()
    
    if mode in ["azure_openai", "azure_speech"]:
        from api.ai.azure_services import get_azure_openai_service
        service = get_azure_openai_service()
        
        if service.is_available:
            summary, emotion = service.process_journal_entry(transcript)
            if summary and emotion:
                return summary, emotion
            logger.warning("Azure OpenAI processing failed, falling back to mock")
        else:
            logger.warning("Azure OpenAI not available, falling back to mock")
    
    # Fallback to mock
    return _summarize_mock(transcript), _infer_emotion_mock(transcript)


def process_entry_background(entry_id: UUID, db_session) -> None:
    """
    Background task to process a journal entry with AI.
    
    This function:
    1. Retrieves the entry from the database
    2. Transcribes the audio
    3. Generates a summary
    4. Infers emotional tone
    5. Updates the entry with results
    
    On failure, sets status to 'failed' but preserves the entry.
    
    Args:
        entry_id: UUID of the entry to process
        db_session: Database session (not used, creates new session)
    """
    from api.entries.models import JournalEntry
    from api.entries.schemas import EntryStatus
    from api.db.database import SessionLocal
    
    # Create new session for background task
    db = SessionLocal()
    
    try:
        # Get entry
        entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        
        if not entry:
            logger.error(f"Entry not found: {entry_id}")
            return
        
        # Update status to processing
        entry.status = EntryStatus.PROCESSING
        db.commit()
        
        # Get audio file path
        audio_path = os.path.join(
            settings.UPLOAD_DIR,
            os.path.basename(entry.audio_url)
        )
        
        logger.info(f"Processing entry {entry_id} with mode: {settings.AI_PROCESSING_MODE}")
        
        # Transcribe audio
        transcript = transcribe_audio(audio_path)
        
        # Process transcript for summary and emotion (more efficient single call)
        summary, emotion = process_transcript(transcript)
        
        # Update entry with results
        entry.transcript = transcript
        entry.summary = summary
        entry.emotion = emotion
        entry.status = EntryStatus.PROCESSED
        db.commit()
        
        logger.info(f"Successfully processed entry {entry_id}: emotion={emotion}")
        
    except Exception as e:
        # On failure, mark as failed but keep entry
        logger.error(f"Error processing entry {entry_id}: {str(e)}")
        try:
            entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
            if entry:
                entry.status = EntryStatus.FAILED
                db.commit()
        except Exception as commit_error:
            logger.error(f"Failed to update entry status: {commit_error}")
        
    finally:
        db.close()

