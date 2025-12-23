"""
Tests for Azure AI services integration.

These tests verify the AI processing pipeline works correctly with:
- Mock mode (default)
- Azure OpenAI mode
- Azure Speech mode (transcription only)
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


# Set test environment before importing modules
os.environ["AI_PROCESSING_MODE"] = "mock"
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_OPENAI_API_KEY"] = ""

# Check if openai is available
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class TestMockProcessing:
    """Tests for mock AI processing mode."""
    
    def test_transcribe_audio_mock(self):
        """Test that mock transcription returns a valid string."""
        from api.ai.processing import transcribe_audio
        
        result = transcribe_audio("/fake/path/audio.wav")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_text_mock(self):
        """Test that mock summarization returns a valid summary."""
        from api.ai.processing import summarize_text
        
        transcript = "Today was a great day. I learned many new things."
        result = summarize_text(transcript)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_infer_emotion_mock(self):
        """Test that mock emotion detection returns valid emotions."""
        from api.ai.processing import infer_emotion
        
        # Test various emotions
        test_cases = [
            ("I am so grateful for this day", "grateful"),
            ("I feel really anxious about tomorrow", "anxious"),
            ("I am so hopeful about the future", "hopeful"),
            ("I've been thinking about my life", "reflective"),
            ("I accomplished so much today", "accomplished"),
            ("It was a calm and peaceful day", "peaceful"),
            ("I am so tired after work", "tired"),
            ("I am happy with my progress", "happy"),
            ("Just a regular day with nothing special", "neutral"),
        ]
        
        for transcript, expected_emotion in test_cases:
            result = infer_emotion(transcript)
            assert isinstance(result, str)
            assert result == expected_emotion, f"Expected {expected_emotion} for '{transcript}', got {result}"
    
    def test_process_transcript_mock(self):
        """Test that process_transcript returns both summary and emotion."""
        from api.ai.processing import process_transcript
        
        transcript = "I feel grateful for all the support I received today."
        summary, emotion = process_transcript(transcript)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert isinstance(emotion, str)
        assert emotion == "grateful"


class TestAzureOpenAIService:
    """Tests for Azure OpenAI service."""
    
    def test_service_not_available_without_config(self):
        """Test service reports unavailable when not configured."""
        with patch('api.config.settings') as mock_settings:
            mock_settings.is_azure_ai_configured.return_value = False
            mock_settings.AZURE_OPENAI_ENDPOINT = None
            mock_settings.AZURE_OPENAI_API_KEY = None
            
            # Force reimport to get fresh instance
            from api.ai import azure_services
            import importlib
            importlib.reload(azure_services)
            
            service = azure_services.AzureOpenAIService()
            assert service.is_available is False
    
    @patch('api.ai.azure_services.settings')
    def test_transcribe_returns_none_when_unavailable(self, mock_settings):
        """Test transcription returns None when service unavailable."""
        mock_settings.is_azure_ai_configured.return_value = False
        
        from api.ai.azure_services import AzureOpenAIService
        service = AzureOpenAIService()
        
        result = service.transcribe_audio("/fake/path.wav")
        assert result is None
    
    @patch('api.ai.azure_services.settings')
    def test_summarize_returns_none_when_unavailable(self, mock_settings):
        """Test summarization returns None when service unavailable."""
        mock_settings.is_azure_ai_configured.return_value = False
        
        from api.ai.azure_services import AzureOpenAIService
        service = AzureOpenAIService()
        
        result = service.summarize_text("Some transcript")
        assert result is None
    
    @patch('api.ai.azure_services.settings')
    def test_analyze_emotion_returns_none_when_unavailable(self, mock_settings):
        """Test emotion analysis returns None when service unavailable."""
        mock_settings.is_azure_ai_configured.return_value = False
        
        from api.ai.azure_services import AzureOpenAIService
        service = AzureOpenAIService()
        
        result = service.analyze_emotion("Some transcript")
        assert result is None


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
class TestAzureOpenAIIntegration:
    """Integration tests for Azure OpenAI (requires openai package)."""
    
    @pytest.fixture
    def azure_service(self):
        """Create Azure OpenAI service with mocked client."""
        with patch('api.ai.azure_services.settings') as mock_settings:
            mock_settings.is_azure_ai_configured.return_value = True
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com"
            mock_settings.AZURE_OPENAI_API_KEY = "test-key"
            mock_settings.AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
            mock_settings.AZURE_OPENAI_CHAT_DEPLOYMENT = "gpt-4o"
            mock_settings.AZURE_OPENAI_WHISPER_DEPLOYMENT = "whisper"
            
            with patch('openai.AzureOpenAI') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                
                from api.ai.azure_services import AzureOpenAIService
                service = AzureOpenAIService()
                service._client = mock_instance
                
                yield service, mock_instance
    
    def test_transcribe_audio_success(self, azure_service):
        """Test successful audio transcription."""
        service, mock_client = azure_service
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "This is the transcribed text."
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', MagicMock()):
            result = service.transcribe_audio("/fake/audio.wav")
        
        assert result == "This is the transcribed text."
    
    def test_summarize_text_success(self, azure_service):
        """Test successful text summarization."""
        service, mock_client = azure_service
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a summary."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = service.summarize_text("Some long transcript text.")
        
        assert result == "This is a summary."
    
    def test_analyze_emotion_success(self, azure_service):
        """Test successful emotion analysis."""
        service, mock_client = azure_service
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "grateful"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = service.analyze_emotion("I am so thankful for today.")
        
        assert result == "grateful"
    
    def test_analyze_emotion_invalid_normalized(self, azure_service):
        """Test that invalid emotions are normalized to neutral."""
        service, mock_client = azure_service
        
        # Mock response with invalid emotion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "INVALID_EMOTION"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = service.analyze_emotion("Some text.")
        
        assert result == "neutral"
    
    def test_process_journal_entry_success(self, azure_service):
        """Test successful combined processing."""
        service, mock_client = azure_service
        
        # Mock JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"summary": "A great day", "emotion": "happy"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        summary, emotion = service.process_journal_entry("Today was wonderful!")
        
        assert summary == "A great day"
        assert emotion == "happy"


class TestProcessingModeSwitching:
    """Tests for switching between processing modes."""
    
    def test_mock_mode_always_returns_result(self):
        """Test that mock mode always returns valid results."""
        # Ensure we're in mock mode
        with patch.object(__import__('api.config', fromlist=['settings']).settings, 
                         'AI_PROCESSING_MODE', 'mock'):
            from api.ai.processing import transcribe_audio, summarize_text, infer_emotion
            
            transcript = transcribe_audio("/fake/path.wav")
            assert isinstance(transcript, str)
            assert len(transcript) > 0
            
            summary = summarize_text(transcript)
            assert isinstance(summary, str)
            
            emotion = infer_emotion(transcript)
            assert isinstance(emotion, str)
    
    def test_mock_functions_work_independently(self):
        """Test mock helper functions work correctly."""
        from api.ai.processing import _transcribe_mock, _summarize_mock, _infer_emotion_mock
        
        transcript = _transcribe_mock("/any/path")
        assert isinstance(transcript, str)
        assert len(transcript) > 10
        
        summary = _summarize_mock(transcript)
        assert isinstance(summary, str)
        
        emotion = _infer_emotion_mock(transcript)
        assert isinstance(emotion, str)

