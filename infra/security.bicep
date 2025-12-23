// ============================================================================
// Voice Journal Infrastructure - Security Module
// ============================================================================
// This module creates:
// - Azure Key Vault for secrets management
// - Managed Identities for Container Apps
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

// ============================================================================
// Variables
// ============================================================================

var keyVaultName = replace('kv-${resourcePrefix}', '-', '')

// ============================================================================
// Managed Identities
// ============================================================================

@description('Managed identity for the API container app')
resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${resourcePrefix}-api'
  location: location
  tags: tags
}

@description('Managed identity for the UI container app')
resource uiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${resourcePrefix}-ui'
  location: location
  tags: tags
}

@description('Managed identity for the Worker container app')
resource workerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${resourcePrefix}-worker'
  location: location
  tags: tags
}

// ============================================================================
// Key Vault
// ============================================================================

@description('Azure Key Vault for storing secrets')
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true // Cannot be disabled once enabled
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ============================================================================
// Key Vault RBAC - Secret User Role Assignments
// ============================================================================

// Role definition IDs
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

@description('API identity can read secrets from Key Vault')
resource apiKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, apiIdentity.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: apiIdentity.properties.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

@description('Worker identity can read secrets from Key Vault')
resource workerKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, workerIdentity.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: workerIdentity.properties.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Name of the Key Vault')
output keyVaultName string = keyVault.name

@description('URI of the Key Vault')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Resource ID of the API managed identity')
output apiIdentityId string = apiIdentity.id

@description('Principal ID of the API managed identity')
output apiIdentityPrincipalId string = apiIdentity.properties.principalId

@description('Client ID of the API managed identity')
output apiIdentityClientId string = apiIdentity.properties.clientId

@description('Resource ID of the UI managed identity')
output uiIdentityId string = uiIdentity.id

@description('Principal ID of the UI managed identity')
output uiIdentityPrincipalId string = uiIdentity.properties.principalId

@description('Resource ID of the Worker managed identity')
output workerIdentityId string = workerIdentity.id

@description('Principal ID of the Worker managed identity')
output workerIdentityPrincipalId string = workerIdentity.properties.principalId

@description('Client ID of the Worker managed identity')
output workerIdentityClientId string = workerIdentity.properties.clientId
