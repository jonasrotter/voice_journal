<#
.SYNOPSIS
    Creates an Azure Automation Task to automatically start PostgreSQL Flexible Server.

.DESCRIPTION
    This script creates a Logic App automation task that:
    1. Monitors the PostgreSQL server state
    2. Automatically starts the server if it's stopped
    3. Runs on a configurable schedule (default: every 6 hours)

.PARAMETER ResourceGroup
    The Azure resource group containing the PostgreSQL server.

.PARAMETER ServerName
    The name of the PostgreSQL Flexible Server.

.PARAMETER CheckIntervalHours
    How often to check the server state (default: 6 hours).

.EXAMPLE
    .\postgres-start-automation.ps1 -ResourceGroup "rg-voicejournal-dev" -ServerName "psql-voicejournal-dev"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$ServerName,

    [Parameter(Mandatory = $false)]
    [int]$CheckIntervalHours = 6
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     PostgreSQL Auto-Start Automation Setup                   ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Resource Group: $ResourceGroup" -ForegroundColor Cyan
Write-Host "║  Server Name:    $ServerName" -ForegroundColor Cyan
Write-Host "║  Check Interval: Every $CheckIntervalHours hours" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if the server exists
Write-Host ">> Checking PostgreSQL server..." -ForegroundColor Yellow
$server = az postgres flexible-server show `
    --resource-group $ResourceGroup `
    --name $ServerName `
    --query "{name:name, state:state, location:location}" `
    -o json 2>$null | ConvertFrom-Json

if (-not $server) {
    Write-Host "[ERROR] PostgreSQL server '$ServerName' not found in resource group '$ResourceGroup'" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Found server: $($server.name) (State: $($server.state))" -ForegroundColor Green

# Get subscription ID
$subscriptionId = az account show --query id -o tsv

# Create the Logic App workflow
$logicAppName = "la-$ServerName-autostart"
$location = $server.location

Write-Host ""
Write-Host ">> Creating Logic App: $logicAppName..." -ForegroundColor Yellow

# Define the Logic App workflow definition
$workflowDefinition = @{
    '$schema' = "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"
    contentVersion = "1.0.0.0"
    triggers = @{
        Recurrence = @{
            type = "Recurrence"
            recurrence = @{
                frequency = "Hour"
                interval = $CheckIntervalHours
            }
        }
    }
    actions = @{
        Get_Server_Status = @{
            type = "Http"
            runAfter = @{}
            inputs = @{
                method = "GET"
                uri = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/$ServerName`?api-version=2024-08-01"
                authentication = @{
                    type = "ManagedServiceIdentity"
                }
            }
        }
        Check_If_Stopped = @{
            type = "If"
            runAfter = @{
                Get_Server_Status = @("Succeeded")
            }
            expression = @{
                and = @(
                    @{
                        equals = @(
                            "@body('Get_Server_Status')?['properties']?['state']"
                            "Stopped"
                        )
                    }
                )
            }
            actions = @{
                Start_Server = @{
                    type = "Http"
                    inputs = @{
                        method = "POST"
                        uri = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/$ServerName/start?api-version=2024-08-01"
                        authentication = @{
                            type = "ManagedServiceIdentity"
                        }
                    }
                }
            }
            else = @{
                actions = @{}
            }
        }
    }
} | ConvertTo-Json -Depth 20

# Save workflow definition to a temp file
$tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.json'
$workflowDefinition | Out-File -FilePath $tempFile -Encoding utf8

try {
    # Create the Logic App
    az logic workflow create `
        --resource-group $ResourceGroup `
        --name $logicAppName `
        --location $location `
        --definition "@$tempFile" `
        --output none

    Write-Host "[OK] Logic App created: $logicAppName" -ForegroundColor Green

    # Enable system-assigned managed identity
    Write-Host ""
    Write-Host ">> Enabling managed identity..." -ForegroundColor Yellow
    
    az logic workflow identity assign `
        --resource-group $ResourceGroup `
        --name $logicAppName `
        --system-assigned `
        --output none

    Write-Host "[OK] Managed identity enabled" -ForegroundColor Green

    # Get the Logic App's managed identity principal ID
    $identityPrincipalId = az logic workflow show `
        --resource-group $ResourceGroup `
        --name $logicAppName `
        --query identity.principalId `
        -o tsv

    # Assign Contributor role to the Logic App for the PostgreSQL server
    Write-Host ""
    Write-Host ">> Assigning permissions..." -ForegroundColor Yellow
    
    $serverResourceId = "/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/$ServerName"
    
    az role assignment create `
        --assignee-object-id $identityPrincipalId `
        --assignee-principal-type ServicePrincipal `
        --role "Contributor" `
        --scope $serverResourceId `
        --output none 2>$null

    Write-Host "[OK] Permissions assigned" -ForegroundColor Green

    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  SUCCESS: PostgreSQL Auto-Start Automation Created!          ║" -ForegroundColor Green
    Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║  Logic App: $logicAppName" -ForegroundColor Green
    Write-Host "║  Schedule:  Every $CheckIntervalHours hours" -ForegroundColor Green
    Write-Host "║                                                              ║" -ForegroundColor Green
    Write-Host "║  The server will automatically restart if stopped.           ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green

} finally {
    # Clean up temp file
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}
