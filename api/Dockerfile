# ============================================================================
# Voice Journal API - Dockerfile
# ============================================================================
# Multi-stage build for Python FastAPI backend
# Uses DefaultAzureCredential for Azure service authentication
# ============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to /app/.local
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# Production stage
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder to system python
COPY --from=builder /install /usr/local

# Copy application code into /app/api folder to match import structure
COPY . ./api/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application from the api folder
# Using 0.0.0.0 to accept connections from outside the container
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
