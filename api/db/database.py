"""Database connection and session management."""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables FIRST before importing settings
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from api.config import get_settings

settings = get_settings()


def _get_postgres_connection_string() -> str:
    """Build PostgreSQL connection string, using managed identity if available."""
    database_url = settings.DATABASE_URL
    
    # Check if we're using Azure PostgreSQL (non-localhost)
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    azure_client_id = os.getenv("AZURE_CLIENT_ID")
    
    logger.info(f"Database connection setup - Host: {postgres_host}, Client ID: {azure_client_id is not None}")
    
    if postgres_host != "localhost" and azure_client_id:
        # Azure PostgreSQL with managed identity - get access token
        logger.info("Attempting managed identity authentication to Azure PostgreSQL...")
        try:
            from azure.identity import ManagedIdentityCredential
            
            credential = ManagedIdentityCredential(client_id=azure_client_id)
            logger.info(f"Created ManagedIdentityCredential with client_id: {azure_client_id}")
            
            # Get token for Azure PostgreSQL
            token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
            logger.info("Successfully obtained access token for PostgreSQL")
            
            # For managed identity auth, username is the managed identity name
            # This should match the role created in PostgreSQL via pgaadauth_create_principal_with_oid
            user = os.getenv("POSTGRES_MI_USERNAME", "id-voicejournal-dev-api")
            database = os.getenv("POSTGRES_DATABASE", "voicejournal")
            port = os.getenv("POSTGRES_PORT", "5432")
            
            # URL encode the token (contains special chars)
            import urllib.parse
            encoded_token = urllib.parse.quote(token.token, safe='')
            
            connection_url = f"postgresql://{user}:{encoded_token}@{postgres_host}:{port}/{database}?sslmode=require"
            logger.info(f"Built connection URL (token hidden): postgresql://{user}:***@{postgres_host}:{port}/{database}?sslmode=require")
            
            return connection_url
        except Exception as e:
            logger.error(f"Failed to get managed identity token: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # Don't fall back silently - fail fast to show the error
    
    logger.info(f"Using default DATABASE_URL: {database_url[:50]}...")
    return database_url


# Get the actual connection string
actual_database_url = _get_postgres_connection_string()

# SQLite doesn't support pool_size/max_overflow, so conditionally set options
if actual_database_url.startswith("sqlite"):
    engine = create_engine(
        actual_database_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        actual_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
