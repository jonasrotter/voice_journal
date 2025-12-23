// ============================================================================
// Voice Journal Infrastructure - Data Module
// ============================================================================
// This module creates:
// - Azure Cosmos DB (NoSQL API) for journal entries
// - Azure Blob Storage for audio files
// ============================================================================

// ============================================================================
// Parameters
// ============================================================================

@description('Azure region for resources')
param location string

@description('Resource naming prefix')
param resourcePrefix string

@description('Resource naming prefix without dashes (for storage account)')
param resourcePrefixNoDash string

@description('Tags to apply to resources')
param tags object

@description('Name of the Key Vault for storing connection strings')
param keyVaultName string

@description('Principal ID of the API managed identity')
param apiIdentityPrincipalId string

@description('Principal ID of the Worker managed identity')
param workerIdentityPrincipalId string

// ============================================================================
// Variables
// ============================================================================

var cosmosDbAccountName = 'cosmos-${resourcePrefix}'
var cosmosDbDatabaseName = 'voice-journal'
var cosmosDbContainerName = 'journal-entries'
// Storage account names must be 3-24 chars, lowercase alphanumeric only
var storageAccountName = take('st${resourcePrefixNoDash}data', 24)
var audioBlobContainerName = 'audio-files'

// Role definition IDs
var cosmosDbDataContributorRoleId = '00000000-0000-0000-0000-000000000002' // Cosmos DB Built-in Data Contributor
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

// ============================================================================
// Cosmos DB Account
// ============================================================================

@description('Azure Cosmos DB account for storing journal entries')
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosDbAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    disableLocalAuth: false // Enable for managed identity auth
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
  }
}

// ============================================================================
// Cosmos DB Database
// ============================================================================

@description('Cosmos DB database for voice journal')
resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosDbAccount
  name: cosmosDbDatabaseName
  properties: {
    resource: {
      id: cosmosDbDatabaseName
    }
  }
}

// ============================================================================
// Cosmos DB Container (Journal Entries)
// ============================================================================

@description('Cosmos DB container for journal entries, partitioned by user_id')
resource cosmosDbContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDbDatabase
  name: cosmosDbContainerName
  properties: {
    resource: {
      id: cosmosDbContainerName
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/transcript/*'
          }
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: -1 // No expiration by default
    }
  }
}

// ============================================================================
// Cosmos DB RBAC Role Assignments
// ============================================================================

@description('API identity has Cosmos DB Data Contributor access')
resource apiCosmosDbRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, apiIdentityPrincipalId, cosmosDbDataContributorRoleId)
  properties: {
    principalId: apiIdentityPrincipalId
    roleDefinitionId: '${cosmosDbAccount.id}/sqlRoleDefinitions/${cosmosDbDataContributorRoleId}'
    scope: cosmosDbAccount.id
  }
}

@description('Worker identity has Cosmos DB Data Contributor access')
resource workerCosmosDbRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, workerIdentityPrincipalId, cosmosDbDataContributorRoleId)
  properties: {
    principalId: workerIdentityPrincipalId
    roleDefinitionId: '${cosmosDbAccount.id}/sqlRoleDefinitions/${cosmosDbDataContributorRoleId}'
    scope: cosmosDbAccount.id
  }
}

// ============================================================================
// Storage Account
// ============================================================================

@description('Azure Storage account for audio files')
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ============================================================================
// Blob Service & Container
// ============================================================================

@description('Blob service for storage account')
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

@description('Blob container for audio files')
resource audioBlobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: audioBlobContainerName
  properties: {
    publicAccess: 'None'
  }
}

// ============================================================================
// Storage RBAC Role Assignments
// ============================================================================

@description('API identity has Storage Blob Data Contributor access')
resource apiStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, apiIdentityPrincipalId, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    principalId: apiIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

@description('Worker identity has Storage Blob Data Contributor access')
resource workerStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, workerIdentityPrincipalId, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    principalId: workerIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Key Vault Secrets (store connection info)
// ============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

@description('Store Cosmos DB endpoint in Key Vault')
resource cosmosDbEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmos-db-endpoint'
  properties: {
    value: cosmosDbAccount.properties.documentEndpoint
  }
}

@description('Store Storage account name in Key Vault')
resource storageAccountNameSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'storage-account-name'
  properties: {
    value: storageAccount.name
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Cosmos DB account endpoint')
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint

@description('Cosmos DB database name')
output cosmosDbDatabaseName string = cosmosDbDatabaseName

@description('Cosmos DB container name')
output cosmosDbContainerName string = cosmosDbContainerName

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Storage account blob endpoint')
output storageBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Audio blob container name')
output audioBlobContainerName string = audioBlobContainerName
