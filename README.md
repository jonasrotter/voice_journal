# Voice Journal

Privacy-first voice journaling with AI transcription, summarization, and emotion detection. Deploys to Azure Container Apps.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Container Apps Environment                       │
│   ┌─────────────┐      ┌─────────────┐                                  │
│   │  UI (Nginx) │─────▶│ API (FastAPI)│                                 │
│   └─────────────┘      └──────┬──────┘                                  │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Key Vault│ │PostgreSQL│ │  Blob   │ │ OpenAI  │ │Managed  │
   │(Secrets)│ │(Database)│ │(Storage)│ │(Whisper)│ │Identity │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Project Structure

```
voice_journal/
├── api/          # FastAPI backend (see api/README.md)
├── ui/           # Vanilla JS frontend (see ui/README.md)
├── infra/        # Azure Bicep IaC (see infra/README.md)
└── tests/        # Pytest test suite
```

## Quick Start

### 1. Start PostgreSQL
```bash
docker run -d --name postgres -e POSTGRES_PASSWORD=localdev123 -e POSTGRES_DB=voice_journal -p 5432:5432 postgres:14
```

### 2. Start API
```bash
python -m venv venv && .\venv\Scripts\Activate.ps1  # Windows
pip install -r api/requirements.txt
cd api && uvicorn main:app --reload --port 8000
```

### 3. Start UI
```bash
cd ui && python -m http.server 3000
```

**App**: http://localhost:3000 | **API Docs**: http://localhost:8000/api/docs

## Azure Deployment

```powershell
cd infra
.\deploy.ps1                              # Deploy infrastructure
.\deploy-containers.ps1 -Environment dev  # Deploy containers
```

See [infra/README.md](infra/README.md) for details.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login → JWT |
| GET | `/api/v1/users/me` | Get profile |
| POST | `/api/v1/entries` | Upload audio |
| GET | `/api/v1/entries` | List entries |
| GET | `/api/v1/entries/{id}` | Get entry |
| DELETE | `/api/v1/entries/{id}` | Delete entry |
| POST | `/api/v1/entries/{id}/reprocess` | Retry AI |
| GET | `/api/health` | Health check |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla JS, Web Audio API, Nginx |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| AI | Azure OpenAI (Whisper, GPT-4o) |
| Storage | Azure PostgreSQL, Blob Storage |
| Infrastructure | Container Apps, Key Vault, Managed Identity, Bicep |

## Testing

```bash
pytest tests/ -v                          # Run tests
pytest tests/ --cov=api --cov-report=html # With coverage
```

## License

MIT - See [LICENSE](LICENSE)
