#!/bin/bash
# Run Voice Journal tests
# Usage: ./scripts/run-tests.sh [test-path] [--coverage]

set -e

cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate 2>/dev/null || {
    echo "Virtual environment not found. Run post-create.sh first."
    exit 1
}

# Set test environment
export ENVIRONMENT=test
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/voicejournal
export AI_PROCESSING_MODE=mock
export JWT_SECRET_KEY=test-secret-key

# Parse arguments
TEST_PATH="${1:-tests/}"
COVERAGE=""

if [ "$1" == "--coverage" ] || [ "$2" == "--coverage" ]; then
    COVERAGE="--cov=api --cov-report=html --cov-report=term-missing"
    if [ "$1" == "--coverage" ]; then
        TEST_PATH="tests/"
    fi
fi

echo "🧪 Running Voice Journal tests..."
echo "   Test path: $TEST_PATH"
echo ""

# Run pytest
python -m pytest $TEST_PATH -v $COVERAGE

echo ""
echo "✅ Tests complete!"

if [ -n "$COVERAGE" ]; then
    echo "📊 Coverage report: htmlcov/index.html"
fi
