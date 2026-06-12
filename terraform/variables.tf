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
  description = "Azure VM size. Standard_D8s_v3 = 8 vCPU / 32 GB RAM (CPU inference). Use Standard_NC4as_T4_v3 for GPU."
  type        = string
  default     = "Standard_D8s_v3"
}

variable "admin_username" {
  description = "SSH admin username for the VM"
  type        = string
  default     = "azureuser"
}

# No SSH key variable needed — Terraform generates the key pair automatically via tls_private_key
