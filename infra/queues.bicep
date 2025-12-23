// ============================================================================
// Voice Journal Infrastructure - Queues Module
// ============================================================================
// This module creates:
// - Azure Service Bus namespace
// - Queue for async audio processing jobs
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

@description('Principal ID of the API managed identity')
param apiIdentityPrincipalId string

@description('Principal ID of the Worker managed identity')
param workerIdentityPrincipalId string

// ============================================================================
// Variables
// ============================================================================

var serviceBusNamespaceName = 'sb-${resourcePrefix}'
var audioProcessingQueueName = 'audio-processing'

// Role definition IDs
var serviceBusDataSenderRoleId = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
var serviceBusDataReceiverRoleId = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'

// ============================================================================
// Service Bus Namespace
// ============================================================================

@description('Azure Service Bus namespace for message queuing')
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusNamespaceName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    zoneRedundant: false
  }
}

// ============================================================================
// Audio Processing Queue
// ============================================================================

@description('Queue for audio processing jobs')
resource audioProcessingQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: audioProcessingQueueName
  properties: {
    lockDuration: 'PT5M' // 5 minute lock for processing
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: false
    requiresSession: false
    defaultMessageTimeToLive: 'P1D' // 1 day TTL
    deadLetteringOnMessageExpiration: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    maxDeliveryCount: 5 // Retry up to 5 times
    enablePartitioning: false
    enableExpress: false
    enableBatchedOperations: true
  }
}

// ============================================================================
// RBAC Role Assignments
// ============================================================================

@description('API identity can send messages to Service Bus')
resource apiServiceBusSenderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, apiIdentityPrincipalId, serviceBusDataSenderRoleId)
  scope: serviceBusNamespace
  properties: {
    principalId: apiIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataSenderRoleId)
    principalType: 'ServicePrincipal'
  }
}

@description('Worker identity can receive messages from Service Bus')
resource workerServiceBusReceiverRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, workerIdentityPrincipalId, serviceBusDataReceiverRoleId)
  scope: serviceBusNamespace
  properties: {
    principalId: workerIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataReceiverRoleId)
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Service Bus namespace name')
output serviceBusNamespace string = serviceBusNamespace.name

@description('Service Bus namespace FQDN')
output serviceBusNamespaceFqdn string = '${serviceBusNamespace.name}.servicebus.windows.net'

@description('Audio processing queue name')
output queueName string = audioProcessingQueue.name

@description('Service Bus namespace endpoint')
output serviceBusEndpoint string = serviceBusNamespace.properties.serviceBusEndpoint
