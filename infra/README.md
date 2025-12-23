# Voice Journal Infrastructure

Azure Bicep infrastructure-as-code for the Voice Journal application.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Azure Resource Group                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Container Apps Environment                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │  UI App     │  │  API App    │  │ Worker App  │                  │    │
│  │  │  (React)    │──│  (FastAPI)  │──│ (Python)    │                  │    │
│  │  │  Port 3000  │  │  Port 8000  │  │ No Ingress  │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                    │                          │
│                              ▼                    ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Azure Service Bus                            │    │
│  │                     Queue: audio-processing                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Key Vault  │  │ PostgreSQL   │  │ Blob Storage │  │ Azure OpenAI │    │
│  │   (Secrets)  │  │  (Database)  │  │ (Audio Files)│  │  (GPT/Whisper)│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Managed Identities                              │    │
│  │  • API Identity    • UI Identity    • Worker Identity                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `main.bicep` | Main orchestration file - deploys all modules |
| `main.bicepparam` | Parameters file for deployment configuration |
| `security.bicep` | Key Vault and Managed Identities |
| `data.bicep` | PostgreSQL Flexible Server and Blob Storage |
| `ai.bicep` | Azure OpenAI service and model deployments |
| `queues.bicep` | Service Bus namespace and queues |
| `containerapps.bicep` | Container Apps Environment and apps |
| `outputs.bicep` | Consolidated deployment outputs |
| `deploy.ps1` | PowerShell deployment script (Windows) |
| `deploy.sh` | Bash deployment script (Linux/macOS) |

## Prerequisites

1. **Azure CLI** installed and configured (`az version` ≥ 2.50)
2. **Azure subscription** with required permissions
3. **Bicep CLI** (installed automatically via `az bicep install`)
4. **jq** (required for bash script - `brew install jq` on macOS, `apt-get install jq` on Ubuntu)

## Quick Start with Deployment Scripts

The easiest way to deploy is using the included scripts:

### PowerShell (Windows)

```powershell
cd infra

# Deploy development environment
.\deploy.ps1

# Deploy to production in West Europe
.\deploy.ps1 -Environment prod -Location westeurope

# Preview changes without deploying (what-if)
.\deploy.ps1 -WhatIf

# Custom resource group and base name
.\deploy.ps1 -ResourceGroupName "my-rg" -BaseName "myjournal" -Environment staging
```

### Bash (Linux/macOS)

```bash
cd infra

# Make script executable
chmod +x deploy.sh

# Deploy development environment
./deploy.sh

# Deploy to production in West Europe
./deploy.sh -e prod -l westeurope

# Preview changes without deploying
./deploy.sh -w

# Custom resource group and base name
./deploy.sh -g "my-rg" -n "myjournal" -e staging
```

### Script Parameters

| Parameter | PowerShell | Bash | Default | Description |
|-----------|------------|------|---------|-------------|
| Environment | `-Environment` | `-e, --environment` | `dev` | Target environment (dev/staging/prod) |
| Location | `-Location` | `-l, --location` | `swedencentral` | Azure region |
| Base Name | `-BaseName` | `-n, --name` | `voicejournal` | Base name for resources |
| Resource Group | `-ResourceGroupName` | `-g, --resource-group` | `rg-{name}-{env}` | Resource group name |
| Subscription | `-SubscriptionId` | `-s, --subscription` | Current | Azure subscription ID |
| What-If | `-WhatIf` | `-w, --what-if` | `false` | Preview mode |
| Skip Login | `-SkipLogin` | N/A | `false` | Skip Azure login prompt |

## Manual Deployment

If you prefer to deploy manually:

### 1. Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create Resource Group

```bash
az group create \
  --name rg-voicejournal-dev \
  --location swedencentral
```

### 3. Deploy Infrastructure

```bash
cd infra

# Deploy with default parameters
az deployment group create \
  --resource-group rg-voicejournal-dev \
  --template-file main.bicep \
  --parameters main.bicepparam

# Or deploy with custom parameters
az deployment group create \
  --resource-group rg-voicejournal-dev \
  --template-file main.bicep \
  --parameters environment=prod baseName=voicejournal
```

### 4. Get Deployment Outputs

```bash
az deployment group show \
  --resource-group rg-voicejournal-dev \
  --name main \
  --query properties.outputs
```

## Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| `kv-voicejournal-{env}` | Key Vault | Secrets management |
| `id-voicejournal-{env}-api` | Managed Identity | API authentication |
| `id-voicejournal-{env}-ui` | Managed Identity | UI authentication |
| `id-voicejournal-{env}-worker` | Managed Identity | Worker authentication |
| `psql-voicejournal-{env}` | PostgreSQL Flexible Server | Journal entries storage |
| `stvoicejournal{env}` | Storage Account | Audio files storage |
| `oai-voicejournal-{env}` | Azure OpenAI | AI processing |
| `sb-voicejournal-{env}` | Service Bus | Message queue |
| `cae-voicejournal-{env}` | Container Apps Env | Container hosting |
| `ca-voicejournal-{env}-api` | Container App | API service |
| `ca-voicejournal-{env}-ui` | Container App | UI service |
| `ca-voicejournal-{env}-worker` | Container App | Background worker |

## Environment Configuration

### Development
```bash
az deployment group create \
  --resource-group rg-voicejournal-dev \
  --template-file main.bicep \
  --parameters environment=dev
```

### Staging
```bash
az deployment group create \
  --resource-group rg-voicejournal-staging \
  --template-file main.bicep \
  --parameters environment=staging
```

### Production
```bash
az deployment group create \
  --resource-group rg-voicejournal-prod \
  --template-file main.bicep \
  --parameters environment=prod
```

## Security Features

- **Managed Identities**: No secrets in container images
- **Key Vault**: Centralized secrets management
- **RBAC**: Least-privilege access control
- **PostgreSQL SSL**: Encrypted connections required
- **Private Networking**: Can be enabled for production

## Scaling

### API & UI
- HTTP-based autoscaling (concurrent requests)
- Min: 1, Max: 10 replicas

### Worker
- Queue-based autoscaling (KEDA)
- Min: 0, Max: 10 replicas
- Scales based on queue message count

## Cost Optimization

- **Burstable PostgreSQL**: Cost-effective for dev/test workloads
- **Consumption tier**: Container Apps
- **Worker scales to zero**: When no messages in queue
- **Standard tier**: Service Bus (cost-effective)

## Cleanup

```bash
az group delete --name rg-voicejournal-dev --yes --no-wait
```

## Troubleshooting

### View Container App Logs
```bash
az containerapp logs show \
  --name ca-voicejournal-dev-api \
  --resource-group rg-voicejournal-dev \
  --follow
```

### Check Deployment Status
```bash
az deployment group list \
  --resource-group rg-voicejournal-dev \
  --output table
```

### Validate Bicep Files
```bash
az bicep build --file main.bicep
```
