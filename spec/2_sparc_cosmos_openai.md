# Voice Journal Application 
## 1. Specification
### 1.1 Product Purpose
Enable users to privately capture voice journals and receive structured reflection (transcripts, summaries, emotional signals) with minimal friction and high trust, deployed via containerized workloads on Azure using declarative infrastructure.

### 1.2 Primary User Story
“As a user, I want to speak my thoughts freely, save them securely, and later understand patterns in what I said and how I felt.”

### 1.3 Core Capabilities
- In-browser voice recording
- Secure audio upload and storage
- Async transcription and AI reflection via Azure OpenAI
- CRUD for journal entries
- Per-user data isolation
- Fully containerized deployment
- Infrastructure defined via Bicep
- Strong API contracts enforced via Pydantic

### 1.4 Success Criteria
- AI processing does not block UI
- Containers scale independently
- Infrastructure reproducible from source control
- Full data deletion across Cosmos DB + Blob Storage

# 2. Pseudocode
(unchanged — see prior version)

# 3. Architecture
## 3.1 High-Level Architecture
[ Browser ]
   |
[ ui Container App ]
   |
[ api Container App ]
   |
[ Queue ]
   |
[ worker Container App ]
   |
+--> Azure OpenAI
+--> Cosmos DB
+--> Blob Storage

## 3.2 Repository Structure (Updated)
root/
├── ui/              # React frontend
├── api/             # FastAPI backend
├── infra/           # Azure Bicep IaC
│   ├── main.bicep
│   ├── containerapps.bicep
│   ├── data.bicep
│   ├── ai.bicep
│   ├── security.bicep
│   ├── queues.bicep
│   └── outputs.bicep
└── README.md

# 4. Refinement
## 4.1 Security & Privacy
- Managed identities for all container apps
- Secrets stored in Azure Key Vault
- No secrets in container images
- Cosmos DB partitioned by user_id
- Infrastructure enforces least privilege

## 4.2 Performance & Scaling
- Azure Container Apps autoscaling (KEDA)
- Worker containers scale on queue depth
- Cosmos DB autoscale throughput
- Blob Storage optimized for large audio files

## 4.3 Reliability & Maintainability
- Declarative infra via Bicep
- Idempotent deployments
- Clear separation of concerns across modules
- Supports dev / staging / prod via parameters

# 5. Completion
## 5.1 Definition of Done
- App deployable via az deployment group create
- All infra defined in /infra
- Containers running in Azure Container Apps
- Azure OpenAI, Cosmos DB, Blob Storage provisioned
- Unit, integration, and contract tests passing
- Observability enabled

## 5.2 Testing
(unchanged — unit, integration, contract tests)