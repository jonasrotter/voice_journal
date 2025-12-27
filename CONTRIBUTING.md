# Contributing to Voice Journal

This guide explains how to set up your development environment for the Voice Journal project.

## 🚀 Quick Start with GitHub Codespaces (Recommended)

The fastest way to start developing is using GitHub Codespaces, which provides a fully configured development environment in the cloud.

### Option 1: Local Development Mode (Default)

1. **Open in Codespaces**
   - Click the green "Code" button on the repository
   - Select "Codespaces" tab
   - Click "Create codespace on main"

2. **Wait for setup** (~2-3 minutes)
   - The container builds automatically
   - Python dependencies are installed
   - Local PostgreSQL and Azurite start automatically

3. **Start the API**
   ```bash
   ./scripts/start-api.sh
   ```

4. **Start the UI** (optional - API already serves UI at port 8000)
   ```bash
   ./scripts/start-ui.sh
   ```

5. **Open the app**
   - Click the "Ports" tab in VS Code
   - Click the globe icon next to port 8000
   - Or visit: `http://localhost:8000`

### Option 2: Azure VNet Integration Mode

For testing against real Azure services via private endpoints:

1. **Prerequisites**
   - GitHub Enterprise organization with VNet integration enabled
   - Azure subscription with deployed infrastructure
   - Service principal with access to Azure resources

2. **Configure GitHub Secrets**
   In your repository settings, add these Codespaces secrets:
   - `AZURE_TENANT_ID` - Your Azure AD tenant ID
   - `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
   - `AZURE_CLIENT_ID` - Service principal client ID
   - `AZURE_CLIENT_SECRET` - Service principal secret

3. **Configure VNet Integration**
   In GitHub organization settings → Codespaces → Network:
   - Add your Azure subscription
   - Select the VNet: `vnet-voicejournal-dev`
   - Select the subnet: `snet-codespaces`

4. **Connect to Azure**
   ```bash
   ./scripts/connect-azure.sh
   ./scripts/start-api.sh --azure
   ```

---

## 🖥️ Local Development (Without Codespaces)

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Azure CLI (for Azure mode)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jonasrotter/voice_journal.git
   cd voice_journal
   ```

2. **Start local services**
   ```bash
   docker-compose -f .devcontainer/docker-compose.yml up -d db azurite
   ```

3. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
   pip install -r api/requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp api/.env.codespaces api/.env
   # Edit api/.env as needed
   ```

5. **Start the API**
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 📁 Project Structure

```
voice_journal/
├── .devcontainer/       # GitHub Codespaces configuration
│   ├── devcontainer.json
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── post-create.sh
├── api/                 # FastAPI backend
│   ├── ai/              # Azure OpenAI integration
│   ├── auth/            # JWT authentication
│   ├── db/              # Database models & connection
│   ├── entries/         # Journal entries CRUD
│   ├── storage/         # Azure Blob Storage
│   ├── users/           # User management
│   └── websocket/       # Real-time updates
├── infra/               # Azure Bicep infrastructure
├── scripts/             # Development scripts
├── tests/               # Pytest test suite
└── ui/                  # Frontend (vanilla JS)
```

---

## 🧪 Running Tests

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test file
./scripts/run-tests.sh tests/test_auth.py

# Run with coverage
./scripts/run-tests.sh --coverage
```

---

## 🔧 Development Modes

| Mode | Database | Storage | AI | Use Case |
|------|----------|---------|----|----|
| **Local** | Docker PostgreSQL | Azurite | Mock | Daily development |
| **Azure** | Azure PostgreSQL | Azure Blob | Azure OpenAI | Integration testing |

### Switching Modes

```bash
# Local mode (default)
./scripts/start-api.sh

# Azure mode (requires VNet integration or public access)
./scripts/connect-azure.sh
./scripts/start-api.sh --azure
```

---

## 🏗️ Infrastructure

The Azure infrastructure is defined in Bicep templates in the `infra/` directory.

### Deploy Infrastructure

```bash
cd infra
az deployment group create \
  --resource-group rg-voicejournal-dev \
  --template-file main.bicep \
  --parameters main.bicepparam
```

### Key Resources

- **PostgreSQL Flexible Server** - Journal data storage
- **Azure Blob Storage** - Audio file storage
- **Azure OpenAI** - Transcription (Whisper) & summarization (GPT-4o)
- **Container Apps** - API, UI, and Worker containers
- **Key Vault** - Secrets management
- **VNet** - Private networking with private endpoints

---

## 🔐 Security

- All Azure services use **private endpoints** (no public access)
- Authentication via **JWT tokens**
- Secrets stored in **Azure Key Vault**
- **Managed identities** for service-to-service auth

---

## 📝 Code Style

- Python: Ruff formatter and linter
- JavaScript: ESLint + Prettier
- Bicep: Standard formatting

Run linting:
```bash
ruff check api/
ruff format api/
```

---

## 🐛 Debugging

### VS Code Launch Configurations

- **FastAPI** - Debug the API server
- **Pytest** - Debug tests
- **Python: Current File** - Debug any Python file

### Common Issues

1. **Database connection failed**
   - Check if PostgreSQL is running: `docker ps`
   - Verify DATABASE_URL in `.env`

2. **Storage access denied**
   - For local: Ensure Azurite is running
   - For Azure: Check managed identity permissions

3. **WebSocket not connecting**
   - Ensure `websockets` package is installed
   - Check JWT token is valid

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [GitHub Codespaces Documentation](https://docs.github.com/codespaces)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
