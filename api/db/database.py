"""Database connection and session management."""
import os
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables FIRST before importing settings
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator, Optional

from api.config import get_settings

settings = get_settings()

# Global token cache for Azure PostgreSQL
_token_cache = {
    "token": None,
    "expires_at": 0,
    "credential": None
}

# Token refresh interval (15 minutes before expiry, tokens last ~1 hour)
TOKEN_REFRESH_INTERVAL = 900  # 15 minutes in seconds


def _get_azure_credential():
    """Get or create the Azure credential for managed identity."""
    azure_client_id = os.getenv("AZURE_CLIENT_ID")
    
    if _token_cache["credential"] is None and azure_client_id:
        from azure.identity import ManagedIdentityCredential
        _token_cache["credential"] = ManagedIdentityCredential(client_id=azure_client_id)
        logger.info(f"Created ManagedIdentityCredential with client_id: {azure_client_id}")
    
    return _token_cache["credential"]


def _get_fresh_token() -> Optional[str]:
    """Get a fresh access token for Azure PostgreSQL, using cache when possible."""
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    azure_client_id = os.getenv("AZURE_CLIENT_ID")
    
    if postgres_host == "localhost" or not azure_client_id:
        return None
    
    current_time = time.time()
    
    # Check if cached token is still valid (with buffer)
    if _token_cache["token"] and current_time < _token_cache["expires_at"] - TOKEN_REFRESH_INTERVAL:
        logger.debug("Using cached Azure PostgreSQL token")
        return _token_cache["token"]
    
    # Refresh the token
    logger.info("Refreshing Azure PostgreSQL access token...")
    try:
        credential = _get_azure_credential()
        if credential:
            token_response = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
            _token_cache["token"] = token_response.token
            _token_cache["expires_at"] = token_response.expires_on
            logger.info(f"Successfully refreshed access token, expires at: {token_response.expires_on}")
            return token_response.token
    except Exception as e:
        logger.error(f"Failed to refresh managed identity token: {type(e).__name__}: {e}")
        raise
    
    return None


def _is_azure_postgres() -> bool:
    """Check if we're using Azure PostgreSQL with managed identity."""
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    azure_client_id = os.getenv("AZURE_CLIENT_ID")
    return postgres_host != "localhost" and azure_client_id is not None


def _get_base_connection_url() -> str:
    """Get the base connection URL (without token for Azure, or full URL for local)."""
    if _is_azure_postgres():
        postgres_host = os.getenv("POSTGRES_HOST")
        user = os.getenv("POSTGRES_MI_USERNAME", "id-voicejournal-dev-api")
        database = os.getenv("POSTGRES_DATABASE", "voicejournal")
        port = os.getenv("POSTGRES_PORT", "5432")
        
        # Return URL without password - password will be set in do_connect event
        connection_url = f"postgresql://{user}:@{postgres_host}:{port}/{database}?sslmode=require"
        logger.info(f"Using Azure PostgreSQL with managed identity: {user}@{postgres_host}:{port}/{database}")
        return connection_url
    
    database_url = settings.DATABASE_URL
    logger.info(f"Using default DATABASE_URL: {database_url[:50]}...")
    return database_url


# Get the base connection string
base_database_url = _get_base_connection_url()

# SQLite doesn't support pool_size/max_overflow, so conditionally set options
if base_database_url.startswith("sqlite"):
    engine = create_engine(
        base_database_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        base_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )


# Register event listener to refresh token on each connection (Azure PostgreSQL only)
if _is_azure_postgres():
    @event.listens_for(engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):
        """
        SQLAlchemy event handler that refreshes the Azure AD token on each connection.
        This ensures tokens are always fresh and never expire during long-running operations.
        """
        logger.debug("do_connect event: refreshing token for new connection")
        token = _get_fresh_token()
        if token:
            cparams["password"] = token
            logger.debug("Token set for new database connection")

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
