# Voice Journal API

FastAPI backend for voice journaling with Azure OpenAI transcription, summarization, and emotion analysis.

## Quick Start

```bash
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt

# Configure
cp .env.example .env          # Edit with your values

# Run
uvicorn api.main:app --reload --port 8000
```

**API Docs**: http://localhost:8000/api/docs

## Architecture

```
api/
├── ai/                    # AI processing
│   ├── azure_services.py  # Azure OpenAI (Whisper + GPT-4o)
│   └── processing.py      # Background processing pipeline
├── auth/                  # JWT authentication
├── db/                    # SQLAlchemy models & session
├── entries/               # Journal entry CRUD
├── storage/               # Azure Blob Storage service
│   └── blob_service.py    # Audio file management
├── users/                 # User management
├── config.py              # Environment configuration
├── main.py                # FastAPI application
├── Dockerfile             # Container image
└── requirements.txt       # Python dependencies
```

## Configuration

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | JWT signing key | Required |
| `UPLOAD_DIR` | Local audio directory | `./uploads` |
| `AI_PROCESSING_MODE` | `mock` or `azure_openai` | `mock` |

### Database (Alternative to DATABASE_URL)

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DATABASE` | Database name | `voice_journal` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | - |

### Azure OpenAI

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint URL | - |
| `AZURE_OPENAI_API_KEY` | API key (optional with MI) | - |
| `AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME` | Whisper deployment | - |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | GPT deployment | `gpt-4o` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-12-01-preview` |

### Azure Blob Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage account | - |
| `AZURE_STORAGE_ACCOUNT_KEY` | Access key (optional with MI) | - |
| `AZURE_STORAGE_CONTAINER_NAME` | Container name | `audio-files` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login → JWT token |
| GET | `/api/v1/users/me` | Get profile |
| PATCH | `/api/v1/users/me` | Update profile |
| DELETE | `/api/v1/users/me` | Delete account |
| POST | `/api/v1/entries` | Upload audio |
| GET | `/api/v1/entries` | List entries |
| GET | `/api/v1/entries/{id}` | Get entry |
| DELETE | `/api/v1/entries/{id}` | Delete entry |
| POST | `/api/v1/entries/{id}/reprocess` | Retry AI processing |
| GET | `/api/health` | Health check |

## Docker

```bash
# Build
docker build -t voice-journal-api .

# Run
docker run -p 8000:8000 --env-file .env voice-journal-api
```

## Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/ --cov=api --cov-report=html # With coverage
```

## AI Processing Modes

| Mode | Transcription | Analysis | Use Case |
|------|---------------|----------|----------|
| `mock` | Placeholder | Placeholder | Local development |
| `azure_openai` | Whisper | GPT-4o | Production |

## Authentication

- **Local**: API key or Azure CLI credentials
- **Azure**: Managed Identity (DefaultAzureCredential)

Both Azure OpenAI and Blob Storage support passwordless auth via Managed Identity.
