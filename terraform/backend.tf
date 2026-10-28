# AzureCloudCostWatchdog/terraform/backend.tf

# Terraform backend configuration for state storage
# This can be changed to use Azure Blob Storage for production

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Example Azure backend (uncomment and configure for production use)
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "rg-terraform-state"
#     storage_account_name = "stterraformstate${random_string.suffix.result}"
#     container_name       = "terraform-state"
#     key                  = "cost-watchdog/terraform.tfstate"
#   }
# }

# Storage account for Terraform state (if using Azure backend)
# resource "azurerm_storage_account" "terraform_state" {
#   name                     = "stterraformstate${random_string.suffix.result}"
#   resource_group_name      = azurerm_resource_group.terraform_state_rg.name
#   location                 = var.location
#   account_tier             = "Standard"
#   account_replication_type = "LRS"
# }

# Resource group for Terraform state
# resource "azurerm_resource_group" "terraform_state_rg" {
#   name     = "rg-terraform-state"
#   location = var.location
# }

# Container for Terraform state
# resource "azurerm_storage_container" "terraform_state_container" {
#   name                  = "terraform-state"
#   storage_account_name  = azurerm_storage_account.terraform_state.name
#   container_access_type = "private"
# }

# Ensure Terraform state file is included in the container
# resource "azurerm_storage_blob" "terraform_state" {
#   name                   = "terraform.tfstate"
#   storage_account_name   = azurerm_storage_account.terraform_state.name
#   storage_container_name = azurerm_storage_container.terraform_state_container.name
#   type                   = "Block"
#   content    = "${data.external.terraform_state_json.output.content}"
# }

# Data source to read existing Terraform state (for Azure backend)
# data "external" "terraform_state_json" {
#   program = ["sh", "-c", "cat ${path.module}/terraform.tfstate || echo '{}'"
# ]
# }

# Note: When using Azure backend for Terraform state, ensure proper access
# permissions are configured for the storage account.
