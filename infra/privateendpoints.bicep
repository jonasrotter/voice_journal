// ============================================================================
// Voice Journal Infrastructure - Private Endpoints Module
// ============================================================================
// This module creates:
// - Private DNS Zones for Azure services
// - Private Endpoints for Storage, PostgreSQL, and OpenAI
// - DNS Zone Virtual Network Links
// ============================================================================

// ============================================================================
// Parameters
// ============================================================================

@description('Azure region for resources')
param location string

@description('Resource naming prefix (reserved for future use)')
#disable-next-line no-unused-params
param resourcePrefix string

@description('Tags to apply to resources')
param tags object

@description('Virtual Network ID to link DNS zones')
param vnetId string

@description('Virtual Network name for DNS zone links')
param vnetName string

@description('Subnet ID for private endpoints')
param privateEndpointsSubnetId string

@description('Storage Account resource ID')
param storageAccountId string

@description('Storage Account name')
param storageAccountName string

@description('PostgreSQL Server resource ID')
param postgresServerId string

@description('PostgreSQL Server name')
param postgresServerName string

@description('Azure OpenAI resource ID')
param openAiId string

@description('Azure OpenAI name')
param openAiName string

// ============================================================================
// Variables
// ============================================================================

var storageBlobDnsZoneName = 'privatelink.blob.core.windows.net'
var postgresDnsZoneName = 'privatelink.postgres.database.azure.com'
var openAiDnsZoneName = 'privatelink.openai.azure.com'

// ============================================================================
// Private DNS Zone: Storage Blob
// ============================================================================

@description('Private DNS Zone for Azure Blob Storage')
resource storageBlobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: storageBlobDnsZoneName
  location: 'global'
  tags: tags
}

@description('Link Storage Blob DNS Zone to VNet')
resource storageBlobDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: storageBlobDnsZone
  name: '${vnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// ============================================================================
// Private DNS Zone: PostgreSQL
// ============================================================================

@description('Private DNS Zone for Azure PostgreSQL')
resource postgresDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: postgresDnsZoneName
  location: 'global'
  tags: tags
}

@description('Link PostgreSQL DNS Zone to VNet')
resource postgresDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresDnsZone
  name: '${vnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// ============================================================================
// Private DNS Zone: Azure OpenAI
// ============================================================================

@description('Private DNS Zone for Azure OpenAI')
resource openAiDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: openAiDnsZoneName
  location: 'global'
  tags: tags
}

@description('Link Azure OpenAI DNS Zone to VNet')
resource openAiDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: openAiDnsZone
  name: '${vnetName}-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// ============================================================================
// Private Endpoint: Storage Blob
// ============================================================================

@description('Private Endpoint for Azure Blob Storage')
resource storageBlobPrivateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-${storageAccountName}-blob'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${storageAccountName}-blob-connection'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

@description('DNS Zone Group for Storage Blob Private Endpoint')
resource storageBlobDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: storageBlobPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-blob-core-windows-net'
        properties: {
          privateDnsZoneId: storageBlobDnsZone.id
        }
      }
    ]
  }
}

// ============================================================================
// Private Endpoint: PostgreSQL
// ============================================================================

@description('Private Endpoint for Azure PostgreSQL')
resource postgresPrivateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-${postgresServerName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${postgresServerName}-connection'
        properties: {
          privateLinkServiceId: postgresServerId
          groupIds: [
            'postgresqlServer'
          ]
        }
      }
    ]
  }
}

@description('DNS Zone Group for PostgreSQL Private Endpoint')
resource postgresDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: postgresPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-postgres-database-azure-com'
        properties: {
          privateDnsZoneId: postgresDnsZone.id
        }
      }
    ]
  }
}

// ============================================================================
// Private Endpoint: Azure OpenAI
// ============================================================================

@description('Private Endpoint for Azure OpenAI')
resource openAiPrivateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-${openAiName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-${openAiName}-connection'
        properties: {
          privateLinkServiceId: openAiId
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

@description('DNS Zone Group for Azure OpenAI Private Endpoint')
resource openAiDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: openAiPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-openai-azure-com'
        properties: {
          privateDnsZoneId: openAiDnsZone.id
        }
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Storage Blob Private DNS Zone ID')
output storageBlobDnsZoneId string = storageBlobDnsZone.id

@description('PostgreSQL Private DNS Zone ID')
output postgresDnsZoneId string = postgresDnsZone.id

@description('Azure OpenAI Private DNS Zone ID')
output openAiDnsZoneId string = openAiDnsZone.id

@description('Storage Blob Private Endpoint ID')
output storageBlobPrivateEndpointId string = storageBlobPrivateEndpoint.id

@description('PostgreSQL Private Endpoint ID')
output postgresPrivateEndpointId string = postgresPrivateEndpoint.id

@description('Azure OpenAI Private Endpoint ID')
output openAiPrivateEndpointId string = openAiPrivateEndpoint.id
