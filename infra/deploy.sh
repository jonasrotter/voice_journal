#!/bin/bash
# ============================================================================
# Voice Journal Infrastructure Deployment Script
# ============================================================================
# This script deploys the Voice Journal application infrastructure to Azure.
#
# Usage:
#   ./deploy.sh                          # Deploy with defaults (dev environment)
#   ./deploy.sh -e prod -l westeurope    # Deploy to production in West Europe
#   ./deploy.sh --help                   # Show help
#
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================

ENVIRONMENT="dev"
LOCATION="swedencentral"
BASE_NAME="voicejournal"
RESOURCE_GROUP=""
SUBSCRIPTION_ID=""
WHAT_IF=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_BICEP_FILE="$SCRIPT_DIR/main.bicep"

# ============================================================================
# Colors
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

show_help() {
    cat << EOF
Voice Journal Infrastructure Deployment

Usage: $(basename "$0") [OPTIONS]

Options:
    -e, --environment   Deployment environment: dev, staging, prod (default: dev)
    -l, --location      Azure region (default: swedencentral)
    -n, --name          Base name for resources (default: voicejournal)
    -g, --resource-group Resource group name (default: rg-{name}-{env})
    -s, --subscription  Azure subscription ID
    -w, --what-if       Preview changes without deploying
    -h, --help          Show this help message

Examples:
    $(basename "$0")                              # Deploy dev environment
    $(basename "$0") -e prod -l westeurope        # Deploy production
    $(basename "$0") -w                           # Preview deployment
    $(basename "$0") -n myapp -e staging          # Custom name, staging env

EOF
}

log_step() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it from https://aka.ms/installazurecli"
        exit 1
    fi
    
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null)
    log_success "Azure CLI version: $AZ_VERSION"
    
    # Check if logged in
    ACCOUNT=$(az account show 2>/dev/null)
    if [ -z "$ACCOUNT" ]; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    USER_NAME=$(echo "$ACCOUNT" | jq -r '.user.name')
    SUB_NAME=$(echo "$ACCOUNT" | jq -r '.name')
    SUB_ID=$(echo "$ACCOUNT" | jq -r '.id')
    
    log_success "Logged in as: $USER_NAME"
    log_success "Current subscription: $SUB_NAME ($SUB_ID)"
    
    # Check if Bicep is available
    if ! az bicep version &> /dev/null; then
        log_warning "Installing Bicep CLI..."
        az bicep install
    fi
    log_success "Bicep CLI is available"
    
    # Check if jq is installed (used for parsing JSON)
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
}

set_subscription() {
    if [ -n "$SUBSCRIPTION_ID" ]; then
        log_step "Setting subscription to: $SUBSCRIPTION_ID"
        az account set --subscription "$SUBSCRIPTION_ID"
        log_success "Subscription set successfully"
    fi
}

create_resource_group() {
    log_step "Checking resource group: $RESOURCE_GROUP"
    
    RG_EXISTS=$(az group exists --name "$RESOURCE_GROUP" 2>/dev/null)
    
    if [ "$RG_EXISTS" == "true" ]; then
        log_success "Resource group already exists"
    else
        log_warning "Creating resource group..."
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
        log_success "Resource group created"
    fi
}

deploy_infrastructure() {
    log_step "Deploying infrastructure..."
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  Environment: $ENVIRONMENT"
    echo "  Base Name: $BASE_NAME"
    echo "  Template: $MAIN_BICEP_FILE"
    
    DEPLOYMENT_NAME="voicejournal-$(date +%Y%m%d-%H%M%S)"
    
    DEPLOY_ARGS=(
        "deployment" "group" "create"
        "--resource-group" "$RESOURCE_GROUP"
        "--template-file" "$MAIN_BICEP_FILE"
        "--name" "$DEPLOYMENT_NAME"
        "--parameters" "environment=$ENVIRONMENT" "baseName=$BASE_NAME"
        "--output" "json"
    )
    
    if [ "$WHAT_IF" = true ]; then
        DEPLOY_ARGS+=("--what-if")
        log_warning "Running what-if analysis..."
    else
        echo -e "\n${YELLOW}This may take 10-15 minutes...${NC}"
    fi
    
    RESULT=$(az "${DEPLOY_ARGS[@]}" 2>&1)
    
    if [ $? -ne 0 ]; then
        log_error "Deployment failed!"
        echo "$RESULT"
        exit 1
    fi
    
    if [ "$WHAT_IF" = false ]; then
        log_success "Deployment completed successfully!"
        echo "$RESULT"
    fi
}

show_outputs() {
    if [ "$WHAT_IF" = true ]; then
        return
    fi
    
    log_step "Deployment Outputs"
    
    # Get deployment outputs
    OUTPUTS=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$(az deployment group list --resource-group "$RESOURCE_GROUP" --query '[0].name' -o tsv)" \
        --query 'properties.outputs' \
        -o json 2>/dev/null)
    
    if [ -n "$OUTPUTS" ] && [ "$OUTPUTS" != "null" ]; then
        UI_URL=$(echo "$OUTPUTS" | jq -r '.uiAppUrl.value // "N/A"')
        API_URL=$(echo "$OUTPUTS" | jq -r '.apiAppUrl.value // "N/A"')
        KEY_VAULT=$(echo "$OUTPUTS" | jq -r '.keyVaultName.value // "N/A"')
        COSMOS_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.cosmosDbEndpoint.value // "N/A"')
        OPENAI_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.openAiEndpoint.value // "N/A"')
        
        echo -e "\n${GREEN}┌─────────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${GREEN}│                    DEPLOYMENT COMPLETE                          │${NC}"
        echo -e "${GREEN}├─────────────────────────────────────────────────────────────────┤${NC}"
        echo -e "${GREEN}│  UI URL:        ${UI_URL}${NC}"
        echo -e "${GREEN}│  API URL:       ${API_URL}${NC}"
        echo -e "${GREEN}│  Key Vault:     ${KEY_VAULT}${NC}"
        echo -e "${GREEN}│  Cosmos DB:     ${COSMOS_ENDPOINT:0:50}...${NC}"
        echo -e "${GREEN}│  OpenAI:        ${OPENAI_ENDPOINT:0:50}...${NC}"
        echo -e "${GREEN}└─────────────────────────────────────────────────────────────────┘${NC}"
    fi
    
    echo -e "\n${CYAN}Next Steps:${NC}"
    echo "  1. Build and push your container images to a registry"
    echo "  2. Update the container apps with your images:"
    echo "     az containerapp update --name ca-$BASE_NAME-$ENVIRONMENT-api --resource-group $RESOURCE_GROUP --image <your-api-image>"
    echo "  3. Configure any additional secrets in Key Vault"
    echo ""
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -n|--name)
            BASE_NAME="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -w|--what-if)
            WHAT_IF=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Set default resource group name if not provided
if [ -z "$RESOURCE_GROUP" ]; then
    RESOURCE_GROUP="rg-$BASE_NAME-$ENVIRONMENT"
fi

# ============================================================================
# Main Execution
# ============================================================================

echo ""
echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║           Voice Journal Infrastructure Deployment                 ║${NC}"
echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════════════╝${NC}"

# Check prerequisites
check_prerequisites

# Set subscription if specified
set_subscription

# Validate Bicep file exists
if [ ! -f "$MAIN_BICEP_FILE" ]; then
    log_error "Bicep file not found: $MAIN_BICEP_FILE"
    exit 1
fi

# Create resource group
if [ "$WHAT_IF" = false ]; then
    create_resource_group
fi

# Deploy infrastructure
deploy_infrastructure

# Show outputs
show_outputs

echo ""
