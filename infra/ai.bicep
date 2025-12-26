// ============================================================================
// Voice Journal Infrastructure - AI Module
// ============================================================================
// This module creates:
// - Azure OpenAI service
// - GPT-4o model deployment for chat/summarization
// - Whisper model deployment for transcription
// ============================================================================

// ============================================================================
// Parameters
// ============================================================================

@description('Azure region for resources')
param location string

@description('Resource naming prefix')
param resourcePrefix string

@description('Tags to apply to resources')
param tags object

@description('Name of the Key Vault for storing API keys')
param keyVaultName string

@description('GPT model deployment name')
param chatModelName string = 'gpt-4o'

@description('Whisper model deployment name')
param whisperModelName string = 'whisper'

@description('Principal ID of the Worker managed identity')
param workerIdentityPrincipalId string

@description('Principal ID of the API managed identity')
param apiIdentityPrincipalId string

@description('Enable private endpoint connectivity (disables public access)')
param enablePrivateEndpoints bool = false

// ============================================================================
// Variables
// ============================================================================

var openAiAccountName = 'oai-${resourcePrefix}'

// Role definition IDs
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// ============================================================================
// Azure OpenAI Account
// ============================================================================

@description('Azure OpenAI service account')
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiAccountName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
    networkAcls: {
      defaultAction: enablePrivateEndpoints ? 'Deny' : 'Allow'
    }
    disableLocalAuth: false
  }
}

// ============================================================================
// Model Deployments
// ============================================================================

@description('GPT-4o model deployment for chat completions and summarization')
resource chatModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: chatModelName
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

@description('Whisper model deployment for audio transcription')
resource whisperModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: whisperModelName
  sku: {
    name: 'Standard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'whisper'
      version: '001'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
  dependsOn: [
    chatModelDeployment // Deploy sequentially to avoid rate limits
  ]
}

// ============================================================================
// RBAC Role Assignments
// Note: Using existing check pattern to avoid conflicts with pre-existing assignments
// ============================================================================

@description('Worker identity has Cognitive Services OpenAI User access')
resource workerOpenAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiAccount.id, workerIdentityPrincipalId, cognitiveServicesOpenAIUserRoleId, 'worker')
  scope: openAiAccount
  properties: {
    principalId: workerIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

@description('API identity has Cognitive Services OpenAI User access')
resource apiOpenAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiAccount.id, apiIdentityPrincipalId, cognitiveServicesOpenAIUserRoleId, 'api')
  scope: openAiAccount
  properties: {
    principalId: apiIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Key Vault Secrets
// ============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

@description('Store OpenAI endpoint in Key Vault')
resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-endpoint'
  properties: {
    value: openAiAccount.properties.endpoint
  }
}

@description('Store OpenAI API key in Key Vault')
resource openAiApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openAiAccount.listKeys().key1
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Azure OpenAI endpoint URL')
output openAiEndpoint string = openAiAccount.properties.endpoint

@description('Azure OpenAI account name')
output openAiAccountName string = openAiAccount.name

@description('GPT-4o deployment name')
output chatDeploymentName string = chatModelDeployment.name

@description('Whisper deployment name')
output whisperDeploymentName string = whisperModelDeployment.name

@description('Azure OpenAI resource ID')
output openAiId string = openAiAccount.id
