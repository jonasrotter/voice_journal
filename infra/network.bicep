// ============================================================================
// Voice Journal Infrastructure - Network Module
// ============================================================================
// This module creates:
// - Virtual Network with subnets
// - Network Security Groups
// - Subnet delegations for Container Apps
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

@description('VNet address space')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Container Apps subnet address prefix (minimum /23 required)')
param containerAppsSubnetPrefix string = '10.0.0.0/23'

@description('Private endpoints subnet address prefix')
param privateEndpointsSubnetPrefix string = '10.0.2.0/24'

@description('GitHub Codespaces subnet address prefix (for VNet integration)')
param codespacesSubnetPrefix string = '10.0.3.0/24'

// ============================================================================
// Variables
// ============================================================================

var vnetName = 'vnet-${resourcePrefix}'
var containerAppsSubnetName = 'snet-container-apps'
var privateEndpointsSubnetName = 'snet-private-endpoints'
var codespacesSubnetName = 'snet-codespaces'
var containerAppsNsgName = 'nsg-${resourcePrefix}-container-apps'
var privateEndpointsNsgName = 'nsg-${resourcePrefix}-private-endpoints'
var codespacesNsgName = 'nsg-${resourcePrefix}-codespaces'

// ============================================================================
// Network Security Groups
// ============================================================================

@description('NSG for Container Apps subnet')
resource containerAppsNsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: containerAppsNsgName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowHTTPS'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'AllowHTTP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '80'
        }
      }
    ]
  }
}

@description('NSG for Private Endpoints subnet')
resource privateEndpointsNsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: privateEndpointsNsgName
  location: location
  tags: tags
  properties: {
    securityRules: []
  }
}

@description('NSG for GitHub Codespaces subnet - allows dev access to private endpoints')
resource codespacesNsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: codespacesNsgName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowPostgreSQL'
        properties: {
          priority: 100
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'VirtualNetwork'
          destinationPortRange: '5432'
          description: 'Allow PostgreSQL access to private endpoint'
        }
      }
      {
        name: 'AllowStorage'
        properties: {
          priority: 110
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'Storage'
          destinationPortRange: '443'
          description: 'Allow Azure Storage access'
        }
      }
      {
        name: 'AllowOpenAI'
        properties: {
          priority: 120
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'AzureOpenAI'
          destinationPortRange: '443'
          description: 'Allow Azure OpenAI access'
        }
      }
      {
        name: 'AllowKeyVault'
        properties: {
          priority: 130
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'AzureKeyVault'
          destinationPortRange: '443'
          description: 'Allow Key Vault access for secrets'
        }
      }
    ]
  }
}

// ============================================================================
// Virtual Network
// ============================================================================

@description('Virtual Network for Voice Journal application')
resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: containerAppsSubnetName
        properties: {
          addressPrefix: containerAppsSubnetPrefix
          networkSecurityGroup: {
            id: containerAppsNsg.id
          }
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
      {
        name: privateEndpointsSubnetName
        properties: {
          addressPrefix: privateEndpointsSubnetPrefix
          networkSecurityGroup: {
            id: privateEndpointsNsg.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
      {
        name: codespacesSubnetName
        properties: {
          addressPrefix: codespacesSubnetPrefix
          networkSecurityGroup: {
            id: codespacesNsg.id
          }
          // GitHub Codespaces VNet integration requires this delegation
          delegations: [
            {
              name: 'GitHub.Network.networkSettings'
              properties: {
                serviceName: 'GitHub.Network/networkSettings'
              }
            }
          ]
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Virtual Network resource ID')
output vnetId string = vnet.id

@description('Virtual Network name')
output vnetName string = vnet.name

@description('Container Apps subnet resource ID')
output containerAppsSubnetId string = vnet.properties.subnets[0].id

@description('Container Apps subnet name')
output containerAppsSubnetName string = containerAppsSubnetName

@description('Private Endpoints subnet resource ID')
output privateEndpointsSubnetId string = vnet.properties.subnets[1].id

@description('Private Endpoints subnet name')
output privateEndpointsSubnetName string = privateEndpointsSubnetName

@description('GitHub Codespaces subnet resource ID')
output codespacesSubnetId string = vnet.properties.subnets[2].id

@description('GitHub Codespaces subnet name')
output codespacesSubnetName string = codespacesSubnetName
