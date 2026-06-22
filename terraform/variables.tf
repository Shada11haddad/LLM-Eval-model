variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "llm-eval-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "app_name" {
  description = "Base name used for all resources"
  type        = string
  default     = "llm-eval"
}

variable "openai_api_key" {
  description = "OpenAI API key — injected as a secret into the API container"
  type        = string
  sensitive   = true
}

variable "hf_token" {
  description = "HuggingFace token — injected as a secret into the API container. Optional; leave empty to skip."
  type        = string
  sensitive   = true
  default     = ""
}
