-- Initialize Voice Journal database for local development
-- This script runs automatically when the PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE voicejournal TO postgres;

-- Note: SQLAlchemy will create tables automatically on first run
-- This file is for any additional setup needed
