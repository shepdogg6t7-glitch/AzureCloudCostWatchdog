# AzureCloudCostWatchdog/terraform/variables.tf

# Input variables for Azure Cloud Cost Watchdog deployment

variable "webhook_url" {
  description = "Webhook URL for sending notifications to Microsoft Teams/Slack or Email via Logic Apps"
  type        = string
  
  validation {
    condition     = length(var.webhook_url) > 0
    error_message = "Webhook URL cannot be empty."
  }
}

variable "resource_group_name" {
  description = "Name of the Azure resource group where resources will be deployed"
  type        = string
  default     = "rg-cost-watchdog"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9-]{1,90}$", var.resource_group_name))
    error_message = "Resource group name must be 1-90 characters and contain only letters, numbers, and hyphens."
  }
}

variable "location" {
  description = "Azure region where resources will be deployed"
  type        = string
  default     = "eastus"
  
  validation {
    condition     = contains(["eastus", "westus", "centralus", "westeurope", "southeastasia"], var.location)
    error_message = "Location must be one of: eastus, westus, centralus, westeurope, southeastasia"
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "function_app_sku" {
  description = "SKU size for the Function App service plan"
  type        = string
  default     = "B1"
  
  validation {
    condition     = contains(["B1", "B2", "B3", "S1", "S2", "S3"], var.function_app_sku)
    error_message = "Function App SKU must be one of: B1, B2, B3, S1, S2, S3"
  }
}

variable "storage_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  
  validation {
    condition     = contains(["LRS", "GRS", "GZRS", "ZRS"], var.storage_replication_type)
    error_message = "Storage replication type must be one of: LRS, GRS, GZRS, ZRS"
  }
}

# Additional configuration variables
variable "application_insights_retention_days" {
  description = "Retention period for Application Insights data (days)"
  type        = number
  default     = 90
}

variable "log_analytics_retention_days" {
  description = "Retention period for Log Analytics data (days)"
  type        = number
  default     = 30
}

variable "monitoring_schedule_minutes" {
  description = "Frequency of VM monitoring in minutes"
  type        = number
  default     = 60
}

variable "notification_email" {
  description = "Email address for critical notifications"
  type        = string
  default     = "admin@example.com"
}
