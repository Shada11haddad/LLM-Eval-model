output "vm_public_ip" {
  description = "Public IP address of the VM — pass this to docker_deploy.sh"
  value       = azurerm_public_ip.pip.ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}

output "deploy_command" {
  description = "Command to deploy with Docker"
  value       = "bash deploy/docker_deploy.sh ${azurerm_public_ip.pip.ip_address}"
}
