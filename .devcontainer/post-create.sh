#!/bin/bash
# Post-create script for GitHub Codespaces
# Runs once after the container is created

set -e

echo "🚀 Setting up Voice Journal development environment..."

# Navigate to workspace
cd /workspaces/voice_journal || cd /workspaces/$(ls /workspaces | head -1)

# ============================================================================
# Python Environment Setup
# ============================================================================
echo "📦 Setting up Python virtual environment..."

python -m venv venv
source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r api/requirements.txt

# Install dev dependencies
pip install pytest pytest-cov pytest-asyncio httpx ruff

# ============================================================================
# Wait for PostgreSQL
# ============================================================================
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432 -U postgres; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# ============================================================================
# Database Initialization
# ============================================================================
echo "🗄️ Initializing database..."

# Create database if not exists (handled by docker-compose, but check anyway)
PGPASSWORD=postgres psql -h localhost -U postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = 'voicejournal'" | grep -q 1 || \
    PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE voicejournal"

# Run database migrations (tables created by SQLAlchemy on first run)
echo "Database ready for use"

# ============================================================================
# Azure Storage (Azurite) Setup
# ============================================================================
echo "📦 Setting up Azurite storage container..."

# Wait for Azurite to be ready
sleep 3

# Create the audio-files container in Azurite
az storage container create \
    --name audio-files \
    --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;" \
    2>/dev/null || echo "Container already exists or Azurite not ready yet"

# ============================================================================
# Environment Configuration
# ============================================================================
echo "⚙️ Setting up environment configuration..."

# Create .env file for local development if it doesn't exist
if [ ! -f api/.env ]; then
    cp api/.env.codespaces api/.env 2>/dev/null || cat > api/.env << 'EOF'
# Local Codespaces Development Configuration
ENVIRONMENT=codespaces

# Database (local PostgreSQL in docker-compose)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/voicejournal

# Storage (Azurite - local Azure Storage emulator)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
AZURE_STORAGE_CONTAINER_NAME=audio-files

# AI Processing (mock mode for local dev)
AI_PROCESSING_MODE=mock

# JWT Secret (development only)
JWT_SECRET_KEY=dev-secret-key-change-in-production

# CORS
ALLOWED_ORIGINS=["http://localhost:8000","http://localhost:3000","http://127.0.0.1:8000"]
EOF
    echo "Created api/.env with local development settings"
fi

# ============================================================================
# Git Configuration
# ============================================================================
echo "🔧 Configuring Git..."
git config --global --add safe.directory /workspaces/voice_journal

# ============================================================================
# VS Code Workspace
# ============================================================================
echo "📝 Setting up VS Code workspace..."

# Create VS Code settings if not exists
mkdir -p .vscode
if [ ! -f .vscode/launch.json ]; then
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": ["api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            "jinja": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        },
        {
            "name": "Pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
EOF
fi

echo ""
echo "✅ Voice Journal development environment is ready!"
echo ""
echo "📋 Quick Start Commands:"
echo "  - Start API:    ./scripts/start-api.sh"
echo "  - Run Tests:    ./scripts/run-tests.sh"
echo "  - Azure Login:  az login --use-device-code"
echo ""
echo "🌐 Ports:"
echo "  - API:        http://localhost:8000"
echo "  - API Docs:   http://localhost:8000/api/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Azurite:    localhost:10000 (Blob)"
echo ""
