# Voice Journal

A privacy-first voice journaling application with AI-powered transcription, summarization, and emotion detection. Deployable to Azure Container Apps with full infrastructure-as-code support.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Azure Resource Group                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Container Apps Environment                        │    │
│  │  ┌─────────────┐  ┌─────────────┐                                   │    │
│  │  │  UI App     │  │  API App    │                                   │    │
│  │  │  (Nginx)    │──│  (FastAPI)  │                                   │    │
│  │  │  Port 80    │  │  Port 8000  │                                   │    │
│  │  └─────────────┘  └─────────────┘                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Key Vault  │  │ PostgreSQL   │  │ Blob Storage │  │ Azure OpenAI │    │
│  │   (Secrets)  │  │  (Database)  │  │ (Audio Files)│  │(GPT/Whisper) │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Managed Identities                              │    │
│  │              (Passwordless authentication to Azure services)         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
voice_journal/
├── api/                    # FastAPI Backend
│   ├── ai/                # AI processing (Azure OpenAI integration)
│   ├── auth/              # Authentication (JWT, password hashing)
│   ├── db/                # Database (SQLAlchemy, PostgreSQL)
│   ├── entries/           # Journal entries CRUD
│   ├── storage/           # Azure Blob Storage integration
│   ├── users/             # User management
│   ├── config.py          # Application configuration
│   ├── Dockerfile         # API container image
│   └── main.py            # FastAPI application
├── ui/                     # Vanilla JavaScript Frontend
│   ├── api/               # API client
│   ├── auth/              # Login/register components
│   ├── components/        # Shared components (toast, header)
│   ├── entries/           # Entry list and card components
│   ├── recording/         # Web Audio API recording
│   ├── settings/          # User settings
│   ├── Dockerfile         # UI container image (Nginx)
│   ├── nginx.conf         # Nginx configuration with API proxy
│   ├── index.html         # HTML entry point
│   ├── main.js            # Application entry point
│   ├── router.js          # Client-side routing
│   └── styles.css         # Global styles
├── infra/                  # Azure Infrastructure (Bicep)
│   ├── main.bicep         # Main orchestration
│   ├── containerapps.bicep # Container Apps
│   ├── data.bicep         # PostgreSQL & Blob Storage
│   ├── ai.bicep           # Azure OpenAI
│   ├── security.bicep     # Key Vault & Managed Identities
│   ├── deploy.ps1         # PowerShell deployment script
│   └── deploy.sh          # Bash deployment script
├── tests/                  # Test suite
│   ├── test_auth.py       # Auth unit tests
│   ├── test_entries.py    # Entries unit tests
│   ├── test_integration.py # API integration tests
│   └── conftest.py        # Test configuration
└── .github/
    └── agents/            # GitHub Copilot agent configurations
```

## Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Database | Azure PostgreSQL |
| AI Services | Azure OpenAI |
| File Storage | Azure Blob Storage |

### Frontend
| Component | Technology |
|-----------|------------|
| UI | Vanilla JavaScript |
| Server | Nginx (containerized) |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Container Platform | Azure Container Apps |
| Database | Azure PostgreSQL |
| AI | Azure OpenAI |
| Storage | Azure Blob Storage |
| Secrets | Azure Key Vault |
| Auth | Managed Identities |
| IaC | Azure Bicep |

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (local or Docker)
- Node.js 18+ (optional, for live reload)

### Option 1: Docker Compose (Recommended)

The easiest way to run the full stack locally:

```bash
# Start PostgreSQL
docker run -d --name postgres-voicejournal \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=localdev123 \
  -e POSTGRES_DB=voice_journal \
  -p 5432:5432 \
  postgres:14

# Clone and setup
git clone <repository-url>
cd voice_journal
```

### Option 2: Manual Setup

#### 1. Database Setup

```bash
# Using Docker
docker run -d --name postgres-voicejournal \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=localdev123 \
  -e POSTGRES_DB=voice_journal \
  -p 5432:5432 \
  postgres:14

# Or install PostgreSQL locally and create database
createdb voice_journal
```

#### 2. Backend Setup

```bash
# Navigate to project root
cd voice_journal

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt

# Start the API server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

#### 3. Frontend Setup

In a new terminal:

```bash
cd voice_journal/ui

# Option A: Python's built-in server
python -m http.server 3000

# Option B: Node.js live-server (with hot reload)
npx live-server --port=3000
```

The UI will be available at `http://localhost:3000`

#### 4. Test the Application

```bash
# Activate virtual environment
cd voice_journal
.\venv\Scripts\Activate.ps1  # Windows

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

## Azure Deployment

### Prerequisites

1. Azure CLI installed (`az version` ≥ 2.50)
2. Azure subscription with Contributor access
3. Docker installed (for building container images)

### Deploy Infrastructure

```powershell
cd infra

# Deploy development environment
.\deploy.ps1

# Deploy to production
.\deploy.ps1 -Environment prod -Location westeurope

# Preview changes (what-if)
.\deploy.ps1 -WhatIf
```

### Deploy Containers

After infrastructure is deployed:

```powershell
# Build and push container images, then update Container Apps
.\deploy-containers.ps1 -Environment dev
```

See [infra/README.md](infra/README.md) for detailed deployment instructions.

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PATCH | `/api/v1/users/me` | Update current user |

### Journal Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/entries` | Upload audio entry (multipart/form-data) |
| GET | `/api/v1/entries` | List entries (paginated) |
| GET | `/api/v1/entries/{id}` | Get single entry |
| DELETE | `/api/v1/entries/{id}` | Delete entry |
| POST | `/api/v1/entries/{id}/reprocess` | Reprocess failed entry |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

## Features

- ✅ User registration and authentication
- ✅ JWT-based session management
- ✅ Audio recording with Web Audio API
- ✅ Audio upload to Azure Blob Storage
- ✅ AI transcription with Azure OpenAI Whisper
- ✅ AI summarization with GPT-4o
- ✅ Emotion detection with GPT-4o
- ✅ Entry listing with pagination
- ✅ Audio playback
- ✅ Entry deletion
- ✅ Reprocess failed entries
- ✅ Privacy settings (AI opt-out)
- ✅ Responsive design
- ✅ Docker containerization
- ✅ Azure Container Apps deployment
- ✅ Infrastructure as Code (Bicep)
- ✅ Managed Identity authentication


## Contributing

See [.github/agents/](/.github/agents/) for AI coding agent configurations.

## License

MIT License - See [LICENSE](LICENSE) file for details.
