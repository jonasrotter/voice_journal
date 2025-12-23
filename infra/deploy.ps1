<#
.SYNOPSIS
    Deploys the Voice Journal infrastructure to Azure.

.DESCRIPTION
    This script deploys the Voice Journal application infrastructure using Azure Bicep.
    It creates a resource group (if needed) and deploys all required Azure resources.

.PARAMETER Environment
    The deployment environment: dev, staging, or prod. Default is 'dev'.

.PARAMETER Location
    The Azure region for deployment. Default is 'swedencentral'.

.PARAMETER BaseName
    Base name for all resources (3-20 chars). Default is 'voicejournal'.

.PARAMETER ResourceGroupName
    Name of the resource group. Default is 'rg-{baseName}-{environment}'.

.PARAMETER SubscriptionId
    Azure subscription ID. If not provided, uses current subscription.

.PARAMETER WhatIf
    Shows what would happen without actually deploying.

.EXAMPLE
    .\deploy.ps1 -Environment dev -Location swedencentral

.EXAMPLE
    .\deploy.ps1 -Environment prod -Location westeurope -BaseName myjournal

.EXAMPLE
    .\deploy.ps1 -WhatIf
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter()]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',

    [Parameter()]
    [string]$Location = 'swedencentral',

    [Parameter()]
    [ValidateLength(3, 20)]
    [string]$BaseName = 'voicejournal',

    [Parameter()]
    [string]$ResourceGroupName,

    [Parameter()]
    [string]$SubscriptionId
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = 'Stop'
$InformationPreference = 'Continue'

# Set default resource group name if not provided
if (-not $ResourceGroupName) {
    $ResourceGroupName = "rg-$BaseName-$Environment"
}

# Script location
$ScriptPath = $PSScriptRoot
$MainBicepFile = Join-Path $ScriptPath 'main.bicep'

# ============================================================================
# Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n▶ $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-AzureCLI {
    Write-Step "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    $azVersion = az version 2>$null | ConvertFrom-Json
    if (-not $azVersion) {
        Write-ErrorMessage "Azure CLI is not installed. Please install it from https://aka.ms/installazurecli"
        exit 1
    }
    Write-Success "Azure CLI version: $($azVersion.'azure-cli')"

    # Check if logged in
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-ErrorMessage "Not logged in to Azure. Please run 'az login' first."
        exit 1
    }
    Write-Success "Logged in as: $($account.user.name)"
    Write-Success "Current subscription: $($account.name) ($($account.id))"

    # Check if Bicep is available
    $bicepVersion = az bicep version 2>$null
    if (-not $bicepVersion) {
        Write-Host "Installing Bicep CLI..." -ForegroundColor Yellow
        az bicep install
    }
    Write-Success "Bicep CLI is available"

    return $account
}

function Set-Subscription {
    param([string]$SubId)
    
    if ($SubId) {
        Write-Step "Setting subscription to: $SubId"
        az account set --subscription $SubId
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to set subscription"
            exit 1
        }
        Write-Success "Subscription set successfully"
    }
}

function New-ResourceGroup {
    param(
        [string]$Name,
        [string]$Location
    )
    
    Write-Step "Checking resource group: $Name"
    
    $rgExists = az group exists --name $Name 2>$null
    if ($rgExists -eq 'true') {
        Write-Success "Resource group already exists"
    } else {
        Write-Host "Creating resource group..." -ForegroundColor Yellow
        az group create --name $Name --location $Location --output none
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMessage "Failed to create resource group"
            exit 1
        }
        Write-Success "Resource group created"
    }
}

function Deploy-Infrastructure {
    param(
        [string]$ResourceGroup,
        [string]$BicepFile,
        [string]$Environment,
        [string]$BaseName,
        [bool]$WhatIf
    )
    
    Write-Step "Deploying infrastructure..."
    Write-Host "  Resource Group: $ResourceGroup"
    Write-Host "  Environment: $Environment"
    Write-Host "  Base Name: $BaseName"
    Write-Host "  Template: $BicepFile"
    
    $deploymentName = "voicejournal-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    $deployArgs = @(
        'deployment', 'group', 'create',
        '--resource-group', $ResourceGroup,
        '--template-file', $BicepFile,
        '--name', $deploymentName,
        '--parameters', "environment=$Environment", "baseName=$BaseName",
        '--output', 'json'
    )
    
    if ($WhatIf) {
        $deployArgs += '--what-if'
        Write-Host "`nRunning what-if analysis..." -ForegroundColor Yellow
    }
    
    Write-Host "`nThis may take 10-15 minutes..." -ForegroundColor Yellow
    
    $result = az @deployArgs 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMessage "Deployment failed!"
        Write-Host $result -ForegroundColor Red
        exit 1
    }
    
    if (-not $WhatIf) {
        Write-Success "Deployment completed successfully!"
        return $result | ConvertFrom-Json
    }
    
    return $null
}

function Show-Outputs {
    param($DeploymentResult)
    
    if (-not $DeploymentResult) { return }
    
    Write-Step "Deployment Outputs"
    
    $outputs = $DeploymentResult.properties.outputs
    
    Write-Host "`n┌─────────────────────────────────────────────────────────────────┐" -ForegroundColor Green
    Write-Host "│                    DEPLOYMENT COMPLETE                          │" -ForegroundColor Green
    Write-Host "├─────────────────────────────────────────────────────────────────┤" -ForegroundColor Green
    
    if ($outputs.uiAppUrl) {
        Write-Host "│  UI URL:        $($outputs.uiAppUrl.value.PadRight(40))│" -ForegroundColor Green
    }
    if ($outputs.apiAppUrl) {
        Write-Host "│  API URL:       $($outputs.apiAppUrl.value.PadRight(40))│" -ForegroundColor Green
    }
    if ($outputs.keyVaultName) {
        Write-Host "│  Key Vault:     $($outputs.keyVaultName.value.PadRight(40))│" -ForegroundColor Green
    }
    if ($outputs.cosmosDbEndpoint) {
        $cosmosShort = $outputs.cosmosDbEndpoint.value
        if ($cosmosShort.Length -gt 40) { $cosmosShort = $cosmosShort.Substring(0, 37) + "..." }
        Write-Host "│  Cosmos DB:     $($cosmosShort.PadRight(40))│" -ForegroundColor Green
    }
    if ($outputs.openAiEndpoint) {
        $oaiShort = $outputs.openAiEndpoint.value
        if ($oaiShort.Length -gt 40) { $oaiShort = $oaiShort.Substring(0, 37) + "..." }
        Write-Host "│  OpenAI:        $($oaiShort.PadRight(40))│" -ForegroundColor Green
    }
    
    Write-Host "└─────────────────────────────────────────────────────────────────┘" -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  1. Build and push your container images to a registry"
    Write-Host "  2. Update the container apps with your images:"
    Write-Host "     az containerapp update --name ca-$BaseName-$Environment-api --resource-group $ResourceGroupName --image <your-api-image>"
    Write-Host "  3. Configure any additional secrets in Key Vault"
    Write-Host ""
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║           Voice Journal Infrastructure Deployment                 ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

# Check prerequisites
$account = Test-AzureCLI

# Set subscription if specified
Set-Subscription -SubId $SubscriptionId

# Validate Bicep file exists
if (-not (Test-Path $MainBicepFile)) {
    Write-ErrorMessage "Bicep file not found: $MainBicepFile"
    exit 1
}

# Create resource group
if (-not $WhatIfPreference) {
    New-ResourceGroup -Name $ResourceGroupName -Location $Location
}

# Deploy infrastructure
$result = Deploy-Infrastructure `
    -ResourceGroup $ResourceGroupName `
    -BicepFile $MainBicepFile `
    -Environment $Environment `
    -BaseName $BaseName `
    -WhatIf $WhatIfPreference

# Show outputs
Show-Outputs -DeploymentResult $result

Write-Host ""
