"""Azure AI services integration for journal entry processing.

This module provides:
- Speech-to-text transcription using Azure OpenAI Whisper or Azure Speech Services
- Text summarization using Azure OpenAI GPT-4o
- Emotion/sentiment analysis using Azure OpenAI GPT-4o
"""
import os
import json
import logging
from typing import Optional, Tuple

from api.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Azure OpenAI service for transcription, summarization, and emotion analysis."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Azure OpenAI client lazily."""
        if not settings.AZURE_OPENAI_ENDPOINT:
            logger.warning("Azure OpenAI endpoint not configured. AI features will use mock data.")
            return
        
        try:
            # Always use DefaultAzureCredential as primary auth method
            # This supports both local dev (Azure CLI) and production (managed identity)
            self._init_with_default_credential()
            if self._client:
                return
                
            # Fallback to API key if DefaultAzureCredential fails and key is available
            if settings.AZURE_OPENAI_API_KEY:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION
                )
                logger.info("Azure OpenAI client initialized with API key (fallback)")
                
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
    
    def _init_with_default_credential(self):
        """Initialize client with DefaultAzureCredential (Entra ID / managed identity)."""
        try:
            from openai import AzureOpenAI
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, 
                "https://cognitiveservices.azure.com/.default"
            )
            
            self._client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            logger.info("Azure OpenAI client initialized with DefaultAzureCredential")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI with DefaultAzureCredential: {e}")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Check if the Azure OpenAI service is available."""
        return self._client is not None
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using Azure OpenAI Whisper.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.is_available:
            logger.warning("Azure OpenAI not available for transcription")
            return None
        
        if not settings.AZURE_OPENAI_WHISPER_DEPLOYMENT:
            logger.warning("Whisper deployment not configured")
            return None
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                result = self._client.audio.transcriptions.create(
                    file=audio_file,
                    model=settings.AZURE_OPENAI_WHISPER_DEPLOYMENT
                )
            
            transcript = result.text
            logger.info(f"Successfully transcribed audio: {len(transcript)} characters")
            return transcript
            
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def summarize_text(self, transcript: str) -> Optional[str]:
        """
        Generate a concise summary of the journal entry.
        
        Args:
            transcript: The transcribed text to summarize
            
        Returns:
            Summary text or None if summarization fails
        """
        if not self.is_available:
            logger.warning("Azure OpenAI not available for summarization")
            return None
        
        try:
            system_prompt = """You are a helpful assistant that summarizes voice journal entries.
Create a brief, empathetic summary (2-3 sentences) that captures:
- The main topic or theme
- Key thoughts or reflections
- Overall tone of the entry

Keep the summary personal and warm, as if speaking to the journal author."""

            response = self._client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please summarize this journal entry:\n\n{transcript}"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
    
    def analyze_emotion(self, transcript: str) -> Optional[str]:
        """
        Analyze the emotional tone of the journal entry.
        
        Args:
            transcript: The transcribed text to analyze
            
        Returns:
            Primary emotion label or None if analysis fails
        """
        if not self.is_available:
            logger.warning("Azure OpenAI not available for emotion analysis")
            return None
        
        try:
            system_prompt = """You are an empathetic assistant that identifies emotional tones in journal entries.
Analyze the text and identify the PRIMARY emotion from this list:
- grateful
- anxious
- hopeful
- reflective
- accomplished
- peaceful
- tired
- happy
- sad
- frustrated
- neutral

Respond with ONLY the single emotion word, nothing else."""

            response = self._client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"What is the primary emotion in this journal entry?\n\n{transcript}"}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            emotion = response.choices[0].message.content.strip().lower()
            
            # Validate emotion is in our expected list
            valid_emotions = [
                "grateful", "anxious", "hopeful", "reflective", "accomplished",
                "peaceful", "tired", "happy", "sad", "frustrated", "neutral"
            ]
            
            if emotion not in valid_emotions:
                emotion = "neutral"
            
            logger.info(f"Detected emotion: {emotion}")
            return emotion
            
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return None
    
    def process_journal_entry(self, transcript: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a journal entry to generate summary and emotion in a single call.
        
        Args:
            transcript: The transcribed text to process
            
        Returns:
            Tuple of (summary, emotion) or (None, None) if processing fails
        """
        if not self.is_available:
            logger.warning("Azure OpenAI not available for journal processing")
            return None, None
        
        try:
            system_prompt = """You are an empathetic assistant that processes voice journal entries.
Given a journal entry transcript, provide:
1. A brief summary (2-3 sentences) capturing the main theme and key thoughts
2. The primary emotion from: grateful, anxious, hopeful, reflective, accomplished, peaceful, tired, happy, sad, frustrated, neutral

Respond in this exact JSON format:
{
  "summary": "Your summary here...",
  "emotion": "emotion_word"
}"""

            response = self._client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Process this journal entry:\n\n{transcript}"}
                ],
                max_tokens=300,
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            summary = result.get("summary", "")
            emotion = result.get("emotion", "neutral").lower()
            
            # Validate emotion
            valid_emotions = [
                "grateful", "anxious", "hopeful", "reflective", "accomplished",
                "peaceful", "tired", "happy", "sad", "frustrated", "neutral"
            ]
            if emotion not in valid_emotions:
                emotion = "neutral"
            
            logger.info(f"Processed journal entry: summary={len(summary)} chars, emotion={emotion}")
            return summary, emotion
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Journal processing failed: {e}")
            return None, None


class AzureSpeechService:
    """Azure Speech service for speech-to-text transcription."""
    
    def __init__(self):
        """Initialize Azure Speech client."""
        self._speech_config = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Azure Speech SDK configuration."""
        if not settings.is_azure_speech_configured():
            logger.warning("Azure Speech not configured.")
            return
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            self._speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            # Set recognition language
            self._speech_config.speech_recognition_language = "en-US"
            
            logger.info("Azure Speech client initialized successfully")
        except ImportError:
            logger.error("azure-cognitiveservices-speech package not installed. Run: pip install azure-cognitiveservices-speech")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech client: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if the Azure Speech service is available."""
        return self._speech_config is not None
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using Azure Speech Services.
        
        Args:
            audio_file_path: Path to the audio file (WAV format preferred)
            
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.is_available:
            logger.warning("Azure Speech not available for transcription")
            return None
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self._speech_config,
                audio_config=audio_config
            )
            
            # Use continuous recognition for longer audio files
            all_results = []
            done = False
            
            def handle_final_result(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    all_results.append(evt.result.text)
            
            def handle_canceled(evt):
                nonlocal done
                done = True
            
            def handle_session_stopped(evt):
                nonlocal done
                done = True
            
            speech_recognizer.recognized.connect(handle_final_result)
            speech_recognizer.canceled.connect(handle_canceled)
            speech_recognizer.session_stopped.connect(handle_session_stopped)
            
            speech_recognizer.start_continuous_recognition()
            
            # Wait for recognition to complete (max 5 minutes)
            import time
            timeout = 300
            start_time = time.time()
            while not done and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            speech_recognizer.stop_continuous_recognition()
            
            transcript = " ".join(all_results)
            logger.info(f"Successfully transcribed audio: {len(transcript)} characters")
            return transcript if transcript else None
            
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None


# Singleton instances
_azure_openai_service: Optional[AzureOpenAIService] = None
_azure_speech_service: Optional[AzureSpeechService] = None


def get_azure_openai_service() -> AzureOpenAIService:
    """Get or create the Azure OpenAI service singleton."""
    global _azure_openai_service
    if _azure_openai_service is None:
        _azure_openai_service = AzureOpenAIService()
    return _azure_openai_service


def get_azure_speech_service() -> AzureSpeechService:
    """Get or create the Azure Speech service singleton."""
    global _azure_speech_service
    if _azure_speech_service is None:
        _azure_speech_service = AzureSpeechService()
    return _azure_speech_service
