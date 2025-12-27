#!/bin/bash
# Start the UI development server
# Usage: ./scripts/start-ui.sh [--port PORT]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
UI_DIR="$PROJECT_ROOT/ui"

# Default port
PORT=3000

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--port PORT]"
            echo ""
            echo "Options:"
            echo "  --port PORT    Port to run the UI server on (default: 3000)"
            echo ""
            echo "Note: The UI is served by the FastAPI backend at port 8000."
            echo "      This script starts a separate dev server for UI-only development."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$UI_DIR"

echo "=========================================="
echo "  Voice Journal UI Development Server"
echo "=========================================="
echo ""
echo "Starting UI server on port $PORT..."
echo "API should be running at http://localhost:8000"
echo ""

# Check if npx is available (for live-server or similar)
if command -v npx &> /dev/null; then
    echo "Using npx to serve static files..."
    npx serve -l $PORT -s .
elif command -v python3 &> /dev/null; then
    echo "Using Python HTTP server..."
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    echo "Using Python HTTP server..."
    python -m http.server $PORT
else
    echo "Error: No suitable server found. Install Node.js or Python."
    exit 1
fi
