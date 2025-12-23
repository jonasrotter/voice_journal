"""Application configuration."""
import os
from typing import Optional

class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/voice_journal"
    )
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_AUDIO_SIZE_MB: int = 50
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_WHISPER_DEPLOYMENT: Optional[str] = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME")
    
    # Azure Speech Configuration (alternative to Whisper)
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "swedencentral")
    
    # AI Processing Mode: "azure_openai", "azure_speech", or "mock"
    AI_PROCESSING_MODE: str = os.getenv("AI_PROCESSING_MODE", "mock")
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    def is_azure_ai_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY)
    
    def is_azure_speech_configured(self) -> bool:
        """Check if Azure Speech is properly configured."""
        return bool(self.AZURE_SPEECH_KEY and self.AZURE_SPEECH_REGION)

settings = Settings()
