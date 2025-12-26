// ============================================================================
// Voice Journal Infrastructure - Main Orchestration
// ============================================================================
// This is the main entry point for deploying the Voice Journal application
// infrastructure to Azure. It orchestrates all module deployments.
// ============================================================================

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
@minLength(3)
@maxLength(20)
param baseName string = 'voicejournal'

@description('Azure OpenAI model deployment name for GPT-4o')
param openAiChatModelName string = 'gpt-4o'

@description('Azure OpenAI model deployment name for Whisper')
param openAiWhisperModelName string = 'whisper'

@description('Container image for the API')
param apiContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container image for the UI')
param uiContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container image for the Worker')
param workerContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('PostgreSQL administrator password')
@secure()
param postgresAdminPassword string

@description('Enable private endpoint connectivity (disables public access to backend services)')
param enablePrivateEndpoints bool = false

@description('Tags to apply to all resources')
param tags object = {
  application: 'voice-journal'
  environment: environment
  managedBy: 'bicep'
}

// ============================================================================
// Variables
// ============================================================================

var resourcePrefix = '${baseName}-${environment}'
var resourcePrefixNoDash = replace(resourcePrefix, '-', '')

// ============================================================================
// Module: Network (VNet & Subnets) - Only when private endpoints enabled
// ============================================================================

module network 'network.bicep' = if (enablePrivateEndpoints) {
  name: 'network-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

// ============================================================================
// Module: Security (Key Vault & Managed Identities)
// Deploy first as other modules depend on these
// ============================================================================

module security 'security.bicep' = {
  name: 'security-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

// ============================================================================
// Module: Data (Cosmos DB & Blob Storage)
// ============================================================================

module data 'data.bicep' = {
  name: 'data-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    resourcePrefixNoDash: resourcePrefixNoDash
    tags: tags
    keyVaultName: security.outputs.keyVaultName
    apiIdentityPrincipalId: security.outputs.apiIdentityPrincipalId
    workerIdentityPrincipalId: security.outputs.workerIdentityPrincipalId
    postgresAdminPassword: postgresAdminPassword
    enablePrivateEndpoints: enablePrivateEndpoints
  }
}

// ============================================================================
// Module: AI (Azure OpenAI)
// ============================================================================

module ai 'ai.bicep' = {
  name: 'ai-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
    keyVaultName: security.outputs.keyVaultName
    chatModelName: openAiChatModelName
    whisperModelName: openAiWhisperModelName
    workerIdentityPrincipalId: security.outputs.workerIdentityPrincipalId
    apiIdentityPrincipalId: security.outputs.apiIdentityPrincipalId
    enablePrivateEndpoints: enablePrivateEndpoints
  }
}

// ============================================================================
// Module: Queues (Service Bus)
// ============================================================================

module queues 'queues.bicep' = {
  name: 'queues-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
    apiIdentityPrincipalId: security.outputs.apiIdentityPrincipalId
    workerIdentityPrincipalId: security.outputs.workerIdentityPrincipalId
  }
}

// ============================================================================
// Module: Container Apps
// ============================================================================

module containerApps 'containerapps.bicep' = {
  name: 'containerapps-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
    apiContainerImage: apiContainerImage
    uiContainerImage: uiContainerImage
    workerContainerImage: workerContainerImage
    apiIdentityId: security.outputs.apiIdentityId
    apiIdentityClientId: security.outputs.apiIdentityClientId
    uiIdentityId: security.outputs.uiIdentityId
    workerIdentityId: security.outputs.workerIdentityId
    workerIdentityClientId: security.outputs.workerIdentityClientId
    keyVaultName: security.outputs.keyVaultName
    postgresHost: data.outputs.postgresHost
    postgresDatabaseName: data.outputs.postgresDatabaseName
    postgresAdminLogin: data.outputs.postgresAdminLogin
    storageAccountName: data.outputs.storageAccountName
    storageBlobEndpoint: data.outputs.storageBlobEndpoint
    openAiEndpoint: ai.outputs.openAiEndpoint
    openAiChatDeploymentName: ai.outputs.chatDeploymentName
    openAiWhisperDeploymentName: ai.outputs.whisperDeploymentName
    serviceBusNamespace: queues.outputs.serviceBusNamespace
    serviceBusQueueName: queues.outputs.queueName
    enableVnetIntegration: enablePrivateEndpoints
    containerAppsSubnetId: enablePrivateEndpoints ? network.outputs.containerAppsSubnetId : ''
  }
  dependsOn: enablePrivateEndpoints ? [network] : []
}

// ============================================================================
// Module: Private Endpoints (only when enabled)
// ============================================================================

module privateEndpoints 'privateendpoints.bicep' = if (enablePrivateEndpoints) {
  name: 'privateendpoints-deployment'
  params: {
    location: location
    resourcePrefix: resourcePrefix
    tags: tags
    vnetId: network.outputs.vnetId
    vnetName: network.outputs.vnetName
    privateEndpointsSubnetId: network.outputs.privateEndpointsSubnetId
    storageAccountId: data.outputs.storageAccountId
    storageAccountName: data.outputs.storageAccountName
    postgresServerId: data.outputs.postgresServerId
    postgresServerName: data.outputs.postgresServerName
    openAiId: ai.outputs.openAiId
    openAiName: ai.outputs.openAiAccountName
  }
  dependsOn: [
    containerApps // Deploy after Container Apps to ensure DNS resolution works
  ]
}

// ============================================================================
// Module: Outputs
// ============================================================================

module outputs 'outputs.bicep' = {
  name: 'outputs-deployment'
  params: {
    keyVaultName: security.outputs.keyVaultName
    postgresHost: data.outputs.postgresHost
    postgresDatabaseName: data.outputs.postgresDatabaseName
    storageAccountName: data.outputs.storageAccountName
    storageBlobEndpoint: data.outputs.storageBlobEndpoint
    openAiEndpoint: ai.outputs.openAiEndpoint
    openAiChatDeploymentName: ai.outputs.chatDeploymentName
    openAiWhisperDeploymentName: ai.outputs.whisperDeploymentName
    serviceBusNamespace: queues.outputs.serviceBusNamespace
    serviceBusQueueName: queues.outputs.queueName
    apiAppUrl: containerApps.outputs.apiAppUrl
    uiAppUrl: containerApps.outputs.uiAppUrl
  }
}

// ============================================================================
// Top-level Outputs
// ============================================================================

@description('URL of the UI application')
output uiAppUrl string = containerApps.outputs.uiAppUrl

@description('URL of the API application')
output apiAppUrl string = containerApps.outputs.apiAppUrl

@description('Name of the Key Vault')
output keyVaultName string = security.outputs.keyVaultName

@description('PostgreSQL host')
output postgresHost string = data.outputs.postgresHost

@description('Azure OpenAI endpoint')
output openAiEndpoint string = ai.outputs.openAiEndpoint
