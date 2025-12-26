-- Grant permissions to managed identity for Azure PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE voicejournal TO "id-voicejournal-dev-api";
GRANT ALL PRIVILEGES ON SCHEMA public TO "id-voicejournal-dev-api";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "id-voicejournal-dev-api";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "id-voicejournal-dev-api";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "id-voicejournal-dev-api";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO "id-voicejournal-dev-api";
