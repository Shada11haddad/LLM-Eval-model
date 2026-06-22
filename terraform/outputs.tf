output "public_ip" {
  description = "Application Gateway public IP — share this with your team"
  value       = azurerm_public_ip.appgw.ip_address
}

output "api_url" {
  description = "FastAPI public URL (WAF-protected, load-balanced)"
  value       = "http://${azurerm_public_ip.appgw.ip_address}"
}

output "api_docs_url" {
  description = "Swagger UI"
  value       = "http://${azurerm_public_ip.appgw.ip_address}/docs"
}

output "api_fqdn" {
  description = "Container App internal FQDN — used by CI/CD"
  value       = azurerm_container_app.api.ingress[0].fqdn
}
