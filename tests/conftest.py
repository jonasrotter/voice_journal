"""
Tests Configuration
pytest fixtures and configuration
"""

import pytest
import os
import sys
import tempfile

# Set environment before any API imports
os.environ["DATABASE_URL"] = "sqlite:///./test_db.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["TESTING"] = "true"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.testclient import TestClient


# Create test engine with file-based SQLite (more reliable for tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def client():
    """Create a FastAPI test client with database override"""
    # Import after env vars are set
    from api.main import app
    from api.db.database import get_db, Base, engine
    from api.users.models import User
    from api.entries.models import JournalEntry, Subscription
    
    # Drop and recreate tables using the app's engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as c:
        yield c
    
    # Clean up after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a new database session for each test"""
    from api.db.database import Base, engine
    from api.users.models import User
    from api.entries.models import JournalEntry, Subscription
    
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def temp_upload_dir():
    """Create temporary upload directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_dir = os.path.join(tmpdir, "audio")
        os.makedirs(audio_dir)
        yield tmpdir


def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_sessionfinish(session, exitstatus):
    """Clean up test database file after all tests"""
    import os
    if os.path.exists("./test_db.db"):
        try:
            os.remove("./test_db.db")
        except:
            pass
