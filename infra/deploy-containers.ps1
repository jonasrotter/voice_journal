<#
.SYNOPSIS
    Builds and deploys Voice Journal containers to Azure Container Apps.

.DESCRIPTION
    This script:
    1. Creates an Azure Container Registry (if needed)
    2. Builds Docker images for API and UI
    3. Pushes images to ACR
    4. Deploys/updates Container Apps

.PARAMETER Environment
    The deployment environment: dev, staging, or prod. Default is 'dev'.

.PARAMETER ResourceGroupName
    Name of the resource group. Default is 'rg-voicejournal-dev'.

.PARAMETER BaseName
    Base name for resources. Default is 'voicejournal'.

.PARAMETER SkipBuild
    Skip Docker build and only deploy existing images.

.PARAMETER BuildOnly
    Only build and push images, don't deploy to Container Apps.

.EXAMPLE
    .\deploy-containers.ps1 -Environment dev

.EXAMPLE
    .\deploy-containers.ps1 -BuildOnly
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',

    [Parameter()]
    [string]$ResourceGroupName = 'rg-voicejournal-dev',

    [Parameter()]
    [string]$BaseName = 'voicejournal',

    [Parameter()]
    [switch]$SkipBuild,

    [Parameter()]
    [switch]$BuildOnly
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = 'Stop'
$InformationPreference = 'Continue'

# Derived names
$acrName = "${BaseName}${Environment}acr".Replace('-', '')
$apiAppName = "ca-${BaseName}-${Environment}-api"
$uiAppName = "ca-${BaseName}-${Environment}-ui"
$imageTag = Get-Date -Format 'yyyyMMdd-HHmmss'

# Paths
$ScriptRoot = $PSScriptRoot
$RepoRoot = Split-Path $ScriptRoot -Parent
$ApiPath = Join-Path $RepoRoot 'api'
$UiPath = Join-Path $RepoRoot 'ui'

# ============================================================================
# Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n>> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check Azure CLI
    $azVersion = az version 2>$null | ConvertFrom-Json
    if (-not $azVersion) {
        Write-ErrorMessage "Azure CLI is not installed"
        exit 1
    }
    Write-Success "Azure CLI: $($azVersion.'azure-cli')"
    
    # Check Docker
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
    if (-not $dockerVersion) {
        Write-ErrorMessage "Docker is not running or not installed"
        exit 1
    }
    Write-Success "Docker: $dockerVersion"
    
    # Check logged in
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-ErrorMessage "Not logged in to Azure. Run 'az login' first."
        exit 1
    }
    Write-Success "Azure account: $($account.user.name)"
    
    return $account
}

function New-ContainerRegistry {
    Write-Step "Ensuring Azure Container Registry exists: $acrName"
    
    $acr = az acr show --name $acrName --resource-group $ResourceGroupName 2>$null | ConvertFrom-Json
    
    if (-not $acr) {
        Write-Host "Creating Container Registry..." -ForegroundColor Yellow
        az acr create `
            --name $acrName `
            --resource-group $ResourceGroupName `
            --sku Basic `
            --admin-enabled true `
            --output none
        
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to create ACR"
            exit 1
        }
        Write-Success "Container Registry created"
    } else {
        Write-Success "Container Registry already exists"
    }
    
    # Get login server
    $loginServer = az acr show --name $acrName --query loginServer -o tsv
    return $loginServer
}

function Build-AndPushImages {
    param([string]$LoginServer)
    
    Write-Step "Logging in to Container Registry..."
    az acr login --name $acrName
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMessage "Failed to login to ACR"
        exit 1
    }
    Write-Success "Logged in to ACR"
    
    # Build and push API image
    Write-Step "Building API image..."
    $apiImage = "${LoginServer}/voice-journal-api:${imageTag}"
    $apiImageLatest = "${LoginServer}/voice-journal-api:latest"
    
    Push-Location $ApiPath
    try {
        docker build -t $apiImage -t $apiImageLatest .
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to build API image"
            exit 1
        }
        Write-Success "API image built: $apiImage"
        
        Write-Host "Pushing API image..." -ForegroundColor Yellow
        docker push $apiImage
        docker push $apiImageLatest
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to push API image"
            exit 1
        }
        Write-Success "API image pushed"
    } finally {
        Pop-Location
    }
    
    # Build and push UI image
    Write-Step "Building UI image..."
    $uiImage = "${LoginServer}/voice-journal-ui:${imageTag}"
    $uiImageLatest = "${LoginServer}/voice-journal-ui:latest"
    
    Push-Location $UiPath
    try {
        docker build -t $uiImage -t $uiImageLatest .
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to build UI image"
            exit 1
        }
        Write-Success "UI image built: $uiImage"
        
        Write-Host "Pushing UI image..." -ForegroundColor Yellow
        docker push $uiImage
        docker push $uiImageLatest
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to push UI image"
            exit 1
        }
        Write-Success "UI image pushed"
    } finally {
        Pop-Location
    }
    
    return @{
        ApiImage = $apiImage
        UiImage = $uiImage
    }
}

function Deploy-ContainerApps {
    param(
        [string]$LoginServer,
        [hashtable]$Images
    )
    
    Write-Step "Getting ACR credentials..."
    $acrUsername = az acr credential show --name $acrName --query username -o tsv
    $acrPassword = az acr credential show --name $acrName --query "passwords[0].value" -o tsv
    
    # Get existing Container Apps Environment
    Write-Step "Looking for Container Apps Environment..."
    $caEnvName = "cae-${BaseName}-${Environment}"
    $caEnv = az containerapp env show --name $caEnvName --resource-group $ResourceGroupName 2>$null | ConvertFrom-Json
    
    if (-not $caEnv) {
        Write-ErrorMessage "Container Apps Environment '$caEnvName' not found. Run the main infrastructure deployment first."
        exit 1
    }
    Write-Success "Found Container Apps Environment: $caEnvName"
    
    # Get existing resources for environment variables
    Write-Step "Getting existing resource configurations..."
    
    # Get PostgreSQL info
    $pgServer = az postgres flexible-server list --resource-group $ResourceGroupName --query "[0]" 2>$null | ConvertFrom-Json
    $pgHost = if ($pgServer) { $pgServer.fullyQualifiedDomainName } else { "" }
    
    # Get Storage Account info
    $storageAccount = az storage account list --resource-group $ResourceGroupName --query "[0]" 2>$null | ConvertFrom-Json
    $storageName = if ($storageAccount) { $storageAccount.name } else { "" }
    
    # Get OpenAI info
    $openai = az cognitiveservices account list --resource-group $ResourceGroupName --query "[?kind=='OpenAI'] | [0]" 2>$null | ConvertFrom-Json
    $openaiEndpoint = if ($openai) { $openai.properties.endpoint } else { "" }
    
    # Get Managed Identity
    $apiIdentity = az identity list --resource-group $ResourceGroupName --query "[?contains(name, 'api')]|[0]" 2>$null | ConvertFrom-Json
    $apiIdentityId = if ($apiIdentity) { $apiIdentity.id } else { "" }
    $apiClientId = if ($apiIdentity) { $apiIdentity.clientId } else { "" }
    
    # Deploy or update API Container App
    Write-Step "Deploying API Container App..."
    
    $apiExists = az containerapp show --name $apiAppName --resource-group $ResourceGroupName 2>$null
    
    if ($apiExists) {
        # Update existing app
        Write-Host "Updating existing API Container App..." -ForegroundColor Yellow
        az containerapp update `
            --name $apiAppName `
            --resource-group $ResourceGroupName `
            --image $Images.ApiImage `
            --set-env-vars `
                "AZURE_CLIENT_ID=$apiClientId" `
                "POSTGRES_HOST=$pgHost" `
                "POSTGRES_DATABASE=voicejournal" `
                "POSTGRES_USER=psqladmin" `
                "AZURE_STORAGE_ACCOUNT_NAME=$storageName" `
                "AZURE_STORAGE_CONTAINER_NAME=audio-files" `
                "AZURE_OPENAI_ENDPOINT=$openaiEndpoint" `
                "AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o" `
                "AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper" `
            --output none
    } else {
        # Create new app
        Write-Host "Creating new API Container App..." -ForegroundColor Yellow
        az containerapp create `
            --name $apiAppName `
            --resource-group $ResourceGroupName `
            --environment $caEnvName `
            --image $Images.ApiImage `
            --target-port 8000 `
            --ingress external `
            --registry-server $LoginServer `
            --registry-username $acrUsername `
            --registry-password $acrPassword `
            --cpu 0.5 `
            --memory 1Gi `
            --min-replicas 1 `
            --max-replicas 10 `
            --user-assigned $apiIdentityId `
            --env-vars `
                "AZURE_CLIENT_ID=$apiClientId" `
                "POSTGRES_HOST=$pgHost" `
                "POSTGRES_DATABASE=voicejournal" `
                "POSTGRES_USER=psqladmin" `
                "AZURE_STORAGE_ACCOUNT_NAME=$storageName" `
                "AZURE_STORAGE_CONTAINER_NAME=audio-files" `
                "AZURE_OPENAI_ENDPOINT=$openaiEndpoint" `
                "AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o" `
                "AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper" `
            --output none
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMessage "Failed to deploy API Container App"
        exit 1
    }
    Write-Success "API Container App deployed"
    
    # Get API URL for UI configuration
    $apiUrl = az containerapp show --name $apiAppName --resource-group $ResourceGroupName --query "properties.configuration.ingress.fqdn" -o tsv
    $apiFullUrl = "https://$apiUrl"
    Write-Success "API URL: $apiFullUrl"
    
    # Deploy or update UI Container App
    Write-Step "Deploying UI Container App..."
    
    $uiExists = az containerapp show --name $uiAppName --resource-group $ResourceGroupName 2>$null
    
    if ($uiExists) {
        # Update existing app
        Write-Host "Updating existing UI Container App..." -ForegroundColor Yellow
        az containerapp update `
            --name $uiAppName `
            --resource-group $ResourceGroupName `
            --image $Images.UiImage `
            --set-env-vars "API_URL=$apiFullUrl" `
            --output none
    } else {
        # Create new app
        Write-Host "Creating new UI Container App..." -ForegroundColor Yellow
        az containerapp create `
            --name $uiAppName `
            --resource-group $ResourceGroupName `
            --environment $caEnvName `
            --image $Images.UiImage `
            --target-port 80 `
            --ingress external `
            --registry-server $LoginServer `
            --registry-username $acrUsername `
            --registry-password $acrPassword `
            --cpu 0.25 `
            --memory 0.5Gi `
            --min-replicas 1 `
            --max-replicas 5 `
            --env-vars "API_URL=$apiFullUrl" `
            --output none
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMessage "Failed to deploy UI Container App"
        exit 1
    }
    Write-Success "UI Container App deployed"
    
    # Get UI URL
    $uiUrl = az containerapp show --name $uiAppName --resource-group $ResourceGroupName --query "properties.configuration.ingress.fqdn" -o tsv
    $uiFullUrl = "https://$uiUrl"
    
    return @{
        ApiUrl = $apiFullUrl
        UiUrl = $uiFullUrl
    }
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║     Voice Journal - Container Deployment                     ║
╠══════════════════════════════════════════════════════════════╣
║  Environment:    $Environment                                        
║  Resource Group: $ResourceGroupName                     
║  ACR Name:       $acrName                                   
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# Check prerequisites
$account = Test-Prerequisites

# Ensure ACR exists
$loginServer = New-ContainerRegistry

# Build and push images (unless skipped)
$images = @{
    ApiImage = "${loginServer}/voice-journal-api:latest"
    UiImage = "${loginServer}/voice-journal-ui:latest"
}

if (-not $SkipBuild) {
    $buildResult = Build-AndPushImages -LoginServer $loginServer
    # Extract only the hashtable from the result (last item)
    if ($buildResult -is [array]) {
        $images = $buildResult[-1]
    } else {
        $images = $buildResult
    }
}

# Deploy to Container Apps (unless build only)
if (-not $BuildOnly) {
    $urls = Deploy-ContainerApps -LoginServer $loginServer -Images $images
    
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║     Deployment Complete!                                     ║
╠══════════════════════════════════════════════════════════════╣
║  API URL:  $($urls.ApiUrl)
║  UI URL:   $($urls.UiUrl)
╚══════════════════════════════════════════════════════════════╝

Test the deployment:
  1. Open the UI URL in your browser
  2. Test API health: curl $($urls.ApiUrl)/api/health

"@ -ForegroundColor Green
} else {
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║     Build Complete!                                          ║
╠══════════════════════════════════════════════════════════════╣
║  API Image: $($images.ApiImage)
║  UI Image:  $($images.UiImage)
╚══════════════════════════════════════════════════════════════╝

Run without -BuildOnly to deploy to Container Apps.

"@ -ForegroundColor Green
}
