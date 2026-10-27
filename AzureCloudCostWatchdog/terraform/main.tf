# AzureCloudCostWatchdog/terraform/main.tf

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.100.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "=3.6.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Variables
variable "webhook_url" {
  description = "Webhook URL for notifications"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-cost-watchdog"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# Storage Account for Function App
resource "azurerm_storage_account" "storage" {
  name                     = "stcostwatchdog${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = {
    environment = "production"
    project     = "azure-cloud-cost-watchdog"
  }
}

# Random suffix for storage account name
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Storage Container for logs
resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# Function App for VM monitoring
resource "azurerm_function_app" "main" {
  name                = "func-costwatchdog${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  storage_account_id = azurerm_storage_account.storage.id
  service_plan_id    = azurerm_service_plan.main.id
  
  builtin_logging_disabled = false
  
  app_settings = {
    "AzureWebJobsStorage" = "DefaultEndpointsProtocol=https;AccountName=${azurerm_storage_account.storage.name};EndpointSuffix=${data.azurerm_client_config.current.dns_suffix}"
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "WebHookUrl" = var.webhook_url
    "SubscriptionId" = data.azurerm_client_config.current.subscription_id
  }
  
  tags = {
    environment = "production"
    project     = "azure-cloud-cost-watchdog"
  }
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "asp-costwatchdog${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "python"
  sku_size            = "B1"
  sku_tier            = "Basic"
  
  tags = {
    environment = "production"
    project     = "azure-cloud-cost-watchdog"
  }
}

# Function App source code
resource "azurerm_function_app_source_control" "main" {
  name           = "func-costwatchdog-sourcecontrol${random_string.suffix.result}"
  function_app_id = azurerm_function_app.main.id
  
  git_token        = "github-token"
  repo_url         = "https://github.com/your-org/azure-cloud-cost-watchdog.git"
  branch          = "main"
  runtime_stack   = "python"
  deployed_to_slot = false
}

# Data sources
data "azurerm_client_config" "current" {}

# Output variables
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "function_app_name" {
  description = "Name of the Function App"
  value       = azurerm_function_app.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.storage.name
}

output "webhook_url" {
  description = "Webhook URL for notifications"
  value       = var.webhook_url
}
