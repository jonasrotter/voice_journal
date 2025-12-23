// ============================================================================
// Voice Journal Infrastructure - Parameters File
// ============================================================================
// This file contains the parameters for deploying the Voice Journal
// infrastructure. Modify these values for your environment.
// ============================================================================
// Usage:
//   az deployment group create \
//     --resource-group <your-resource-group> \
//     --template-file main.bicep \
//     --parameters main.bicepparam
// ============================================================================

using 'main.bicep'

// ============================================================================
// Environment Configuration
// ============================================================================

// Environment: dev, staging, or prod
param environment = 'dev'

// Base name used for all resources (3-20 chars, alphanumeric and dashes)
param baseName = 'voicejournal'

// ============================================================================
// Azure OpenAI Model Deployments
// ============================================================================

// GPT-4o deployment name for chat completions and summarization
param openAiChatModelName = 'gpt-4o'

// Whisper deployment name for audio transcription
param openAiWhisperModelName = 'whisper'

// ============================================================================
// Container Images
// ============================================================================
// Replace these with your actual container images after building and pushing
// to a container registry (e.g., Azure Container Registry)

// API container image (FastAPI backend)
param apiContainerImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// UI container image (React frontend)
param uiContainerImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// Worker container image (background processor)
param workerContainerImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ============================================================================
// PostgreSQL Configuration
// ============================================================================
// IMPORTANT: Change this password before deployment!
// In production, use Azure Key Vault or a secure parameter source.

param postgresAdminPassword = 'ChangeMe123!' // TODO: Use secure parameter in production

// ============================================================================
// Resource Tags
// ============================================================================

param tags = {
  application: 'voice-journal'
  environment: 'dev'
  managedBy: 'bicep'
  costCenter: 'development'
  owner: 'voice-journal-team'
}
