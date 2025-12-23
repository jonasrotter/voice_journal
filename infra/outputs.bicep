// ============================================================================
// Voice Journal Infrastructure - Outputs Module
// ============================================================================
// This module consolidates all outputs from the deployment for easy reference.
// Use these outputs to configure your application and CI/CD pipelines.
// ============================================================================

// ============================================================================
// Parameters (passed from main.bicep)
// ============================================================================

@description('Name of the Key Vault')
param keyVaultName string

@description('PostgreSQL host')
param postgresHost string

@description('PostgreSQL database name')
param postgresDatabaseName string

@description('Storage account name')
param storageAccountName string

@description('Storage blob endpoint')
param storageBlobEndpoint string

@description('Azure OpenAI endpoint')
param openAiEndpoint string

@description('Azure OpenAI chat deployment name')
param openAiChatDeploymentName string

@description('Azure OpenAI Whisper deployment name')
param openAiWhisperDeploymentName string

@description('Service Bus namespace name')
param serviceBusNamespace string

@description('Service Bus queue name')
param serviceBusQueueName string

@description('API application URL')
param apiAppUrl string

@description('UI application URL')
param uiAppUrl string

// ============================================================================
// Output Variables (for documentation/reference)
// ============================================================================

var deploymentSummary = {
  applications: {
    uiUrl: uiAppUrl
    apiUrl: apiAppUrl
  }
  dataServices: {
    postgres: {
      host: postgresHost
      databaseName: postgresDatabaseName
    }
    storage: {
      accountName: storageAccountName
      blobEndpoint: storageBlobEndpoint
    }
  }
  aiServices: {
    openAi: {
      endpoint: openAiEndpoint
      chatDeployment: openAiChatDeploymentName
      whisperDeployment: openAiWhisperDeploymentName
    }
  }
  messaging: {
    serviceBus: {
      namespace: serviceBusNamespace
      queueName: serviceBusQueueName
    }
  }
  security: {
    keyVaultName: keyVaultName
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Complete deployment summary')
output deploymentSummary object = deploymentSummary

@description('UI application URL')
output uiUrl string = uiAppUrl

@description('API application URL')
output apiUrl string = apiAppUrl

@description('Key Vault name for secrets management')
output keyVault string = keyVaultName

@description('PostgreSQL host for data access')
output postgresHostOutput string = postgresHost

@description('Azure OpenAI endpoint for AI services')
output openAiServiceEndpoint string = openAiEndpoint

@description('Service Bus namespace for messaging')
output serviceBus string = '${serviceBusNamespace}.servicebus.windows.net'
