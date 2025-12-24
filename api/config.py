"""Application configuration."""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Database - support both DATABASE_URL and individual components
        self.DATABASE_URL: str = self._build_database_url()
        
        # JWT
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        
        # Storage
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
        self.MAX_AUDIO_SIZE_MB: int = 50
        
        # Azure Storage Configuration
        self.AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "audio-files")
        
        # Azure OpenAI Configuration
        self.AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        self.AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.AZURE_OPENAI_CHAT_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
        self.AZURE_OPENAI_WHISPER_DEPLOYMENT: Optional[str] = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME")
        
        # Azure Speech Configuration (alternative to Whisper)
        self.AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
        self.AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "swedencentral")
        
        # AI Processing Mode: "azure_openai", "azure_speech", or "mock"
        self.AI_PROCESSING_MODE: str = os.getenv("AI_PROCESSING_MODE", "mock")
        
        # CORS
        self.ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    def is_azure_ai_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY)
    
    def is_azure_speech_configured(self) -> bool:
        """Check if Azure Speech is properly configured."""
        return bool(self.AZURE_SPEECH_KEY and self.AZURE_SPEECH_REGION)
    
    def is_azure_storage_configured(self) -> bool:
        """Check if Azure Storage is properly configured."""
        return bool(self.AZURE_STORAGE_ACCOUNT_NAME and self.AZURE_STORAGE_ACCOUNT_KEY)
    
    def _build_database_url(self) -> str:
        """Build DATABASE_URL from environment variables.
        
        Supports either:
        - DATABASE_URL directly
        - Individual POSTGRES_* components (for Azure Container Apps)
        """
        # Check for direct DATABASE_URL first
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # Build from individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DATABASE", "voice_journal")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        # For Azure PostgreSQL with managed identity, password may be empty
        # In that case, we need to get a token
        if not password and host != "localhost":
            # Azure PostgreSQL with managed identity - password will be set in database.py
            return f"postgresql://{user}@{host}:{port}/{database}?sslmode=require"
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# Singleton - will be initialized after dotenv is loaded
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global settings
    if settings is None:
        settings = Settings()
    return settings
