provider "azurerm" {
  features {}
}

# Create Resource Group for Cost Watchdog
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
    purpose    = "cost-monitoring"
  }
}

# Create Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "ai-costwatchdog-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "other"

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
  }

  retention_in_days = var.application_insights_retention_days
}

# Create Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-costwatchdog-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "pergb2018"

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
  }

  retention_in_days = var.log_analytics_retention_days
}

# Storage Account for Function App
resource "azurerm_storage_account" "storage" {
  name                     = "stcostwatchdog${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
  }
}

# Create Storage Container for logs
resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# Create Storage Container for monitoring results
resource "azurerm_storage_container" "results" {
  name                  = "results"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# Create Service Plan for Function App
resource "azurerm_service_plan" "main" {
  name                = "asp-costwatchdog-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "python"
  sku_size            = var.function_app_sku
  sku_tier            = "Basic"

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
  }
}

# Main Function App for VM monitoring
resource "azurerm_function_app" "main" {
  name                = "func-costwatchdog-${random_string.suffix.result}"
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
    "ApplicationInsightsConnectionString" = azurerm_application_insights.main.connection_string
    "LogAnalyticsWorkspaceId" = azurerm_log_analytics_workspace.main.id
  }

  tags = {
    environment = var.environment
    project     = "azure-cloud-cost-watchdog"
  }

  lifecycle {
    ignore_changes = [tags]
  }
}

# Application Insights monitoring
resource "azurerm_monitor_metric_alert" "cost_watchdog_alert" {
  name                = "cost-watchdog-alert-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_function_app.main.id]
  location            = var.location

  criteria {
    name    = "high-error-rate"
    enabled = true

    aggregation = "Count"
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Requests"

    operator          = "GreaterThan"
    threshold         = 100
    time_greater_than = "PT5M"
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  auto_mitigate_enabled = true
  description            = "Alert when error rate exceeds threshold"
}

# Action Group for alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "cost-watchdog-action-group-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  short_name         = "costwatchdog"

  webhook {
    service_uri = var.webhook_url
    use_aad_auth = false
  }

  tags = {
    environment = var.environment
  }
}

# Function App source control integration
resource "azurerm_function_app_source_control" "main" {
  name           = "func-costwatchdog-sourcecontrol-${random_string.suffix.result}"
  function_app_id = azurerm_function_app.main.id

  repo_url         = "https://github.com/your-org/azure-cloud-cost-watchdog.git"
  branch          = "main"
  runtime_stack   = "python"
  deployed_to_slot = false

  count = var.enable_github_actions ? 1 : 0
}

# Random suffix for resource naming
data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Enable GitHub Actions variable for source control
variable "enable_github_actions" {
  description = "Enable GitHub Actions integration"
  type        = bool
  default     = false
}

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

output "application_insights_name" {
  description = "Name of Application Insights resource"
  value       = azurerm_application_insights.main.name
}

output "log_analytics_workspace_name" {
  description = "Name of Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.name
}

output "function_app_url" {
  description = "URL of the Function App"
  value       = "https://${azurerm_function_app.main.name}.azurewebsites.net"
}
