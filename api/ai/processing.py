"""AI processing functions for journal entries."""
import os
import random
from uuid import UUID
from typing import Optional

from api.config import settings
from api.entries.schemas import EntryStatus


# Mock transcription - in production, replace with actual speech-to-text API
def transcribe_audio(audio_url: str) -> str:
    """
    Transcribe audio file to text.
    
    In production, this would call a speech-to-text service like:
    - OpenAI Whisper
    - Google Speech-to-Text
    - Azure Speech Services
    
    For MVP, returns mock transcription.
    """
    # Mock implementation - returns sample transcriptions
    sample_transcriptions = [
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
    
    return random.choice(sample_transcriptions)


def summarize_text(transcript: str) -> str:
    """
    Generate a summary of the transcribed text.
    
    In production, this would use an LLM like:
    - OpenAI GPT
    - Anthropic Claude
    - Local LLM
    
    For MVP, returns a mock summary.
    """
    # Simple mock summary - extracts first sentence and adds context
    first_sentence = transcript.split('.')[0] + '.'
    
    summaries = [
        f"Today's reflection: {first_sentence}",
        f"Key theme: {first_sentence}",
        f"Main thought: {first_sentence}",
    ]
    
    return random.choice(summaries)


def infer_emotion(transcript: str) -> str:
    """
    Analyze emotional tone of the transcript.
    
    In production, this would use sentiment analysis:
    - Custom trained model
    - OpenAI API with prompt engineering
    - Dedicated emotion detection service
    
    For MVP, returns mock emotion based on keywords.
    """
    transcript_lower = transcript.lower()
    
    # Simple keyword-based emotion detection
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
            return
        
        # Update status to processing
        entry.status = EntryStatus.PROCESSING
        db.commit()
        
        # Get audio file path
        audio_path = os.path.join(
            settings.UPLOAD_DIR,
            os.path.basename(entry.audio_url)
        )
        
        # Process with AI
        transcript = transcribe_audio(audio_path)
        summary = summarize_text(transcript)
        emotion = infer_emotion(transcript)
        
        # Update entry with results
        entry.transcript = transcript
        entry.summary = summary
        entry.emotion = emotion
        entry.status = EntryStatus.PROCESSED
        db.commit()
        
    except Exception as e:
        # On failure, mark as failed but keep entry
        try:
            entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
            if entry:
                entry.status = EntryStatus.FAILED
                db.commit()
        except Exception:
            pass
        
        # Log error (in production, use proper logging)
        print(f"Error processing entry {entry_id}: {str(e)}")
        
    finally:
        db.close()
