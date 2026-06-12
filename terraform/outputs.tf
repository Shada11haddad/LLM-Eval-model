output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.pip.ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the VM using the generated key"
  value       = "ssh -i terraform/generated_key.pem ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}

output "deploy_command" {
  description = "Command to deploy with Docker"
  value       = "bash deploy/docker_deploy.sh ${azurerm_public_ip.pip.ip_address}"
}

output "api_url" {
  description = "FastAPI base URL (available after docker compose up)"
  value       = "http://${azurerm_public_ip.pip.ip_address}:8000"
}

output "api_docs_url" {
  description = "Interactive Swagger UI"
  value       = "http://${azurerm_public_ip.pip.ip_address}:8000/docs"
}

output "private_key_pem" {
  description = "Generated SSH private key — used by CI/CD to connect to the VM"
  value       = tls_private_key.ssh.private_key_openssh
  sensitive   = true
}
