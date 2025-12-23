# Voice Journal API

A FastAPI backend for voice journaling with AI-powered transcription, summarization, and emotion analysis.

## Features

- **Voice Recording**: Upload audio files for transcription
- **AI Transcription**: Convert speech to text using Azure OpenAI Whisper or Azure Speech Services
- **AI Analysis**: Generate summaries and detect emotions using Azure OpenAI GPT-4o
- **Secure Storage**: JWT authentication and per-user data isolation
- **RESTful API**: Full CRUD operations for journal entries

## Requirements

- Python 3.10+
- PostgreSQL (or SQLite for development)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `UPLOAD_DIR` | Directory for audio files | Yes |
| `AI_PROCESSING_MODE` | `mock`, `azure_openai`, or `azure_speech` | Yes |

### Azure AI Configuration (for `azure_openai` mode)

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | API key |
| `AZURE_OPENAI_API_VERSION` | API version (default: 2024-12-01-preview) |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | GPT-4o deployment name |
| `AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME` | Whisper deployment name |

### Azure Speech Configuration (for `azure_speech` mode)

| Variable | Description |
|----------|-------------|
| `AZURE_SPEECH_KEY` | Azure Speech service key |
| `AZURE_SPEECH_REGION` | Azure region (e.g., swedencentral) |

## AI Processing Modes

The API supports three processing modes:

1. **mock** (default): Uses mock data for development. No Azure credentials required.
2. **azure_openai**: Uses Azure OpenAI for all processing:
   - Whisper for transcription
   - GPT-4o for summarization and emotion analysis
3. **azure_speech**: Hybrid mode:
   - Azure Speech Services for transcription
   - Azure OpenAI GPT-4o for analysis

## Running

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update current user
- `DELETE /api/v1/users/me` - Delete account (GDPR)

### Entries
- `POST /api/v1/entries` - Upload audio and create entry
- `GET /api/v1/entries` - List all entries (paginated)
- `GET /api/v1/entries/{id}` - Get specific entry
- `PATCH /api/v1/entries/{id}` - Update entry
- `DELETE /api/v1/entries/{id}` - Delete entry
- `POST /api/v1/entries/{id}/reprocess` - Rerun AI analysis

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ai_services.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

## Architecture

```
api/
├── ai/                 # AI processing modules
│   ├── azure_services.py  # Azure OpenAI & Speech integration
│   └── processing.py      # Background processing pipeline
├── auth/               # Authentication (JWT, password hashing)
├── db/                 # Database models and session
├── entries/            # Journal entry CRUD
├── users/              # User management
├── config.py           # Configuration settings
└── main.py             # FastAPI application
```
