variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "llm-eval-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "llm-eval-vm"
}

variable "vm_size" {
  description = "Azure VM size. Standard_D4s_v3 = 4 vCPU / 16 GB RAM. Upgrade to Standard_D8s_v3 after quota increase."
  type        = string
  default     = "Standard_D4s_v3"
}

variable "admin_username" {
  description = "SSH admin username for the VM"
  type        = string
  default     = "azureuser"
}

variable "vm_zone" {
  description = "Availability zone for the VM and public IP (1, 2, or 3). Required for zone-restricted SKUs on free-trial subscriptions."
  type        = string
  default     = "1"
}

# No SSH key variable needed — Terraform generates the key pair automatically via tls_private_key
