// ============================================================================
// Voice Journal Infrastructure - Data Module
// ============================================================================
// This module creates:
// - Azure PostgreSQL Flexible Server for journal entries
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

@description('PostgreSQL administrator login name')
@minLength(1)
param postgresAdminLogin string = 'pgadmin'

@description('PostgreSQL administrator password')
@secure()
param postgresAdminPassword string

@description('PostgreSQL version')
@allowed(['16', '15', '14', '13', '12'])
param postgresVersion string = '16'

@description('PostgreSQL SKU name (compute size)')
param postgresSku string = 'Standard_B1ms'

@description('PostgreSQL SKU tier')
@allowed(['Burstable', 'GeneralPurpose', 'MemoryOptimized'])
param postgresSkuTier string = 'Burstable'

@description('PostgreSQL storage size in GB')
@minValue(32)
@maxValue(16384)
param postgresStorageSizeGB int = 32

@description('Enable private endpoint connectivity (disables public access)')
param enablePrivateEndpoints bool = false

// ============================================================================
// Variables
// ============================================================================

var postgresServerName = 'psql-${resourcePrefix}'
var postgresDatabaseName = 'voicejournal'
// Storage account names must be 3-24 chars, lowercase alphanumeric only
var storageAccountName = take('st${resourcePrefixNoDash}data', 24)
var audioBlobContainerName = 'audio-files'

// Role definition IDs
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

// ============================================================================
// PostgreSQL Flexible Server
// ============================================================================

@description('Azure PostgreSQL Flexible Server for storing journal entries')
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgresServerName
  location: location
  tags: tags
  sku: {
    name: postgresSku
    tier: postgresSkuTier
  }
  properties: {
    version: postgresVersion
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: postgresStorageSizeGB
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
  }
}

// ============================================================================
// PostgreSQL Database
// ============================================================================

@description('PostgreSQL database for voice journal')
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgresServer
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// ============================================================================
// PostgreSQL Firewall Rules
// ============================================================================

@description('Allow Azure services to access PostgreSQL (only when not using private endpoints)')
resource postgresFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = if (!enablePrivateEndpoints) {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
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
    allowSharedKeyAccess: !enablePrivateEndpoints
    publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: enablePrivateEndpoints ? 'Deny' : 'Allow'
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

@description('Store PostgreSQL connection string in Key Vault')
resource postgresConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-connection-string'
  properties: {
    value: 'postgresql://${postgresAdminLogin}:${postgresAdminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/${postgresDatabaseName}?sslmode=require'
  }
}

@description('Store PostgreSQL host in Key Vault')
resource postgresHostSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-host'
  properties: {
    value: postgresServer.properties.fullyQualifiedDomainName
  }
}

@description('Store PostgreSQL password in Key Vault')
resource postgresPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-password'
  properties: {
    value: postgresAdminPassword
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

@description('PostgreSQL server fully qualified domain name')
output postgresHost string = postgresServer.properties.fullyQualifiedDomainName

@description('PostgreSQL database name')
output postgresDatabaseName string = postgresDatabaseName

@description('PostgreSQL admin login')
output postgresAdminLogin string = postgresAdminLogin

@description('PostgreSQL server name')
output postgresServerName string = postgresServer.name

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Storage account blob endpoint')
output storageBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Audio blob container name')
output audioBlobContainerName string = audioBlobContainerName

@description('PostgreSQL server resource ID')
output postgresServerId string = postgresServer.id

@description('Storage account resource ID')
output storageAccountId string = storageAccount.id
