# Voice Journal Development Container
# Based on Python 3.12 with Node.js 20

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Install PostgreSQL client tools
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        postgresql-client \
        libpq-dev \
        ffmpeg \
        curl \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip \
    && pip install \
        ruff \
        pytest \
        pytest-cov \
        pytest-asyncio \
        httpx

# Set up workspace
WORKDIR /workspaces

# Default command
CMD ["sleep", "infinity"]
