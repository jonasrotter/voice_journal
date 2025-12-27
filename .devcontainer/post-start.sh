#!/bin/bash
# Post-start script for GitHub Codespaces
# Runs every time the container starts

set -e

echo "🔄 Starting Voice Journal services..."

# Navigate to workspace
cd /workspaces/voice_journal || cd /workspaces/$(ls /workspaces | head -1)

# Activate virtual environment
source venv/bin/activate 2>/dev/null || true

# Wait for services
echo "⏳ Waiting for services..."
sleep 2

# Check PostgreSQL
if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL not ready yet"
fi

# Check Azurite
if curl -s http://127.0.0.1:10000/ > /dev/null 2>&1; then
    echo "✅ Azurite is running"
else
    echo "⚠️  Azurite not ready yet"
fi

echo ""
echo "🚀 Ready to develop! Run './scripts/start-api.sh' to start the API server."
