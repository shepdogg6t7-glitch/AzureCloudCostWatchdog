# AzureCloudCostWatchdog/terraform/outputs.tf

output "resource_group_name" {
  description = "Name of the Azure resource group created for the Cost Watchdog"
  value       = azurerm_resource_group.main.name
}

output "function_app_name" {
  description = "Name of the Azure Function App that runs the VM monitoring logic"
  value       = azurerm_function_app.main.name
}

output "storage_account_name" {
  description = "Name of the Azure Storage Account used for logging and data storage"
  value       = azurerm_storage_account.storage.name
}

output "webhook_url" {
  description = "Configured webhook URL for sending notifications"
  value       = var.webhook_url
}

output "location" {
  description = "Azure region where resources are deployed"
  value       = var.location
}

output "monitoring_schedule" {
  description = "Schedule configuration for VM monitoring (1 hour by default)"
  value       = var.monitoring_schedule_minutes
}

output "function_app_url" {
  description = "URL of the Azure Function App endpoint"
  value       = "https://${azurerm_function_app.main.name}.azurewebsites.net"
}

output "storage_container_url" {
  description = "URL of the storage container for logs and results"
  value       = "https://${azurerm_storage_account.storage.name}.blob.core.windows.net/${azurerm_storage_container.logs.name}"
}

output "cost_watchdog_dashboard_url" {
  description = "URL to the Azure Cost Watchdog monitoring dashboard (if Application Insights is configured)"
  value       = "https://portal.azure.com/#blade/Microsoft_Azure_Monitoring/AzureMonitoringBrowseBlade"
}
