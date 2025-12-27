#!/bin/bash
# Start the Voice Journal API server
# Usage: ./scripts/start-api.sh [--azure]

set -e

cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate 2>/dev/null || {
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r api/requirements.txt
}

# Check for Azure mode
if [ "$1" == "--azure" ]; then
    echo "🔷 Starting in AZURE mode (connecting to Azure services via private endpoints)"
    export AI_PROCESSING_MODE=azure_openai
    
    # Check Azure login
    if ! az account show > /dev/null 2>&1; then
        echo "⚠️  Not logged into Azure. Please run: az login --use-device-code"
        exit 1
    fi
    echo "✅ Azure CLI authenticated"
else
    echo "🏠 Starting in LOCAL mode (using local PostgreSQL + Azurite)"
    export AI_PROCESSING_MODE=mock
fi

# Load environment
if [ -f api/.env ]; then
    export $(grep -v '^#' api/.env | xargs)
fi

echo ""
echo "🚀 Starting Voice Journal API..."
echo "   API Docs: http://localhost:8000/api/docs"
echo "   Health:   http://localhost:8000/api/health"
echo ""

# Start the server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
