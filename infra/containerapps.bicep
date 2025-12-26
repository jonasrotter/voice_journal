// ============================================================================
// Voice Journal Infrastructure - Container Apps Module
// ============================================================================
// This module creates:
// - Container Apps Environment with Log Analytics
// - API Container App (FastAPI backend)
// - UI Container App (React frontend)
// - Worker Container App (background processing)
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

@description('Container image for the API')
param apiContainerImage string

@description('Container image for the UI')
param uiContainerImage string

@description('Container image for the Worker')
param workerContainerImage string

@description('Resource ID of the API managed identity')
param apiIdentityId string

@description('Client ID of the API managed identity')
param apiIdentityClientId string

@description('Resource ID of the UI managed identity')
param uiIdentityId string

@description('Resource ID of the Worker managed identity')
param workerIdentityId string

@description('Client ID of the Worker managed identity')
param workerIdentityClientId string

@description('Name of the Key Vault')
param keyVaultName string

@description('PostgreSQL host')
param postgresHost string

@description('PostgreSQL database name')
param postgresDatabaseName string

@description('PostgreSQL admin login')
param postgresAdminLogin string

@description('Storage account name')
param storageAccountName string

@description('Storage blob endpoint URL')
param storageBlobEndpoint string

@description('Azure OpenAI endpoint URL')
param openAiEndpoint string

@description('Azure OpenAI chat deployment name')
param openAiChatDeploymentName string

@description('Azure OpenAI Whisper deployment name')
param openAiWhisperDeploymentName string

@description('Service Bus namespace name')
param serviceBusNamespace string

@description('Service Bus queue name')
param serviceBusQueueName string

@description('Enable VNet integration for private endpoint connectivity')
param enableVnetIntegration bool = false

@description('Subnet ID for Container Apps (required when enableVnetIntegration is true)')
param containerAppsSubnetId string = ''

// ============================================================================
// Variables
// ============================================================================

var containerAppsEnvName = 'cae-${resourcePrefix}'
var logAnalyticsName = 'log-${resourcePrefix}'
var apiAppName = 'ca-${resourcePrefix}-api'
var uiAppName = 'ca-${resourcePrefix}-ui'
var workerAppName = 'ca-${resourcePrefix}-worker'

// ============================================================================
// Log Analytics Workspace
// ============================================================================

@description('Log Analytics workspace for Container Apps monitoring')
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================================
// Container Apps Environment
// ============================================================================

@description('Container Apps Environment')
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: enableVnetIntegration ? {
      infrastructureSubnetId: containerAppsSubnetId
      internal: false // Allow external ingress
    } : null
    zoneRedundant: false
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ============================================================================
// API Container App
// ============================================================================

@description('API Container App - FastAPI backend')
resource apiContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: apiAppName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${apiIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      registries: []
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiContainerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: apiIdentityClientId
            }
            {
              name: 'POSTGRES_HOST'
              value: postgresHost
            }
            {
              name: 'POSTGRES_DATABASE'
              value: postgresDatabaseName
            }
            {
              name: 'POSTGRES_USER'
              value: postgresAdminLogin
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storageAccountName
            }
            {
              name: 'STORAGE_ACCOUNT_NAME'
              value: storageAccountName
            }
            {
              name: 'STORAGE_BLOB_ENDPOINT'
              value: storageBlobEndpoint
            }
            {
              name: 'SERVICE_BUS_NAMESPACE'
              value: '${serviceBusNamespace}.servicebus.windows.net'
            }
            {
              name: 'SERVICE_BUS_QUEUE_NAME'
              value: serviceBusQueueName
            }
            {
              name: 'KEY_VAULT_NAME'
              value: keyVaultName
            }
            {
              name: 'AI_PROCESSING_MODE'
              value: 'azure_openai'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'
              value: openAiChatDeploymentName
            }
            {
              name: 'AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME'
              value: openAiWhisperDeploymentName
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// UI Container App
// ============================================================================

@description('UI Container App - React frontend')
resource uiContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: uiAppName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uiIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
        allowInsecure: false
      }
      registries: []
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'ui'
          image: uiContainerImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'VITE_API_URL'
              value: 'https://${apiAppName}.${containerAppsEnv.properties.defaultDomain}'
            }
            {
              name: 'API_URL'
              value: 'https://${apiAppName}.${containerAppsEnv.properties.defaultDomain}'
            }
            {
              name: 'API_HOST'
              value: '${apiAppName}.${containerAppsEnv.properties.defaultDomain}'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [
    apiContainerApp
  ]
}

// ============================================================================
// Worker Container App
// ============================================================================

@description('Worker Container App - Background audio processing')
resource workerContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: workerAppName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${workerIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      // No ingress - worker is not exposed externally
      registries: []
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerContainerImage
          resources: {
            cpu: json('1')
            memory: '2Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: workerIdentityClientId
            }
            {
              name: 'POSTGRES_HOST'
              value: postgresHost
            }
            {
              name: 'POSTGRES_DATABASE'
              value: postgresDatabaseName
            }
            {
              name: 'POSTGRES_USER'
              value: postgresAdminLogin
            }
            {
              name: 'STORAGE_ACCOUNT_NAME'
              value: storageAccountName
            }
            {
              name: 'STORAGE_BLOB_ENDPOINT'
              value: storageBlobEndpoint
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'
              value: openAiChatDeploymentName
            }
            {
              name: 'AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME'
              value: openAiWhisperDeploymentName
            }
            {
              name: 'SERVICE_BUS_NAMESPACE'
              value: '${serviceBusNamespace}.servicebus.windows.net'
            }
            {
              name: 'SERVICE_BUS_QUEUE_NAME'
              value: serviceBusQueueName
            }
            {
              name: 'KEY_VAULT_NAME'
              value: keyVaultName
            }
            {
              name: 'AI_PROCESSING_MODE'
              value: 'azure_openai'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'queue-scaling'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                queueName: serviceBusQueueName
                namespace: serviceBusNamespace
                messageCount: '5'
              }
              auth: [
                {
                  secretRef: 'service-bus-connection-string'
                  triggerParameter: 'connection'
                }
              ]
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Container Apps Environment ID')
output containerAppsEnvId string = containerAppsEnv.id

@description('Container Apps Environment default domain')
output containerAppsEnvDomain string = containerAppsEnv.properties.defaultDomain

@description('API Container App URL')
output apiAppUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'

@description('UI Container App URL')
output uiAppUrl string = 'https://${uiContainerApp.properties.configuration.ingress.fqdn}'

@description('API Container App name')
output apiAppName string = apiContainerApp.name

@description('UI Container App name')
output uiAppName string = uiContainerApp.name

@description('Worker Container App name')
output workerAppName string = workerContainerApp.name
