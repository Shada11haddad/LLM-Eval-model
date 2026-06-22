terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.3.0"

  # Remote state stored in Azure Blob Storage
  # The storage account is created by the GitHub Actions bootstrap step
  backend "azurerm" {
    resource_group_name  = "llm-eval-tfstate-rg"
    storage_account_name = "llmevaltfstate"
    container_name       = "tfstate"
    key                  = "llm-eval.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# ── Resource Group ─────────────────────────────────────────────
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# ── Log Analytics ──────────────────────────────────────────────
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.app_name}-logs"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# ═══════════════════════════════════════════════════════════════
#  NETWORKING
# ═══════════════════════════════════════════════════════════════

resource "azurerm_virtual_network" "vnet" {
  name                = "${var.app_name}-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]
}

# Dedicated subnet for Application Gateway
resource "azurerm_subnet" "appgw" {
  name                 = "appgw-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Subnet for Container Apps Environment (/23 minimum required)
resource "azurerm_subnet" "container_apps" {
  name                 = "container-apps-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/23"]

  # Container App Environments require the subnet to be delegated to
  # Microsoft.App/environments, otherwise CreateOrUpdate fails with
  # ManagedEnvironmentSubnetDelegationError.
  delegation {
    name = "Microsoft.App.environments"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# ═══════════════════════════════════════════════════════════════
#  APPLICATION GATEWAY  (WAF_v2 — single public IP + WAF)
# ═══════════════════════════════════════════════════════════════

resource "azurerm_public_ip" "appgw" {
  name                = "${var.app_name}-appgw-pip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

# Inline waf_configuration on the gateway has been retired by Azure; WAF
# settings now live in a standalone policy attached via firewall_policy_id.
resource "azurerm_web_application_firewall_policy" "appgw" {
  name                = "${var.app_name}-waf-policy"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  policy_settings {
    enabled                     = true
    mode                        = "Prevention"
    file_upload_limit_in_mb     = 100
    max_request_body_size_in_kb = 128
    request_body_check          = true
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
    }
  }
}

resource "azurerm_application_gateway" "appgw" {
  name                = "${var.app_name}-appgw"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  firewall_policy_id  = azurerm_web_application_firewall_policy.appgw.id

  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 2
  }

  # Without this, the gateway defaults to AppGwSslPolicy20150501 (TLS 1.0/1.1),
  # which Azure now rejects. Pin a modern predefined policy (TLS 1.2 minimum).
  ssl_policy {
    policy_type = "Predefined"
    policy_name = "AppGwSslPolicy20220101"
  }

  gateway_ip_configuration {
    name      = "appgw-ip-config"
    subnet_id = azurerm_subnet.appgw.id
  }

  frontend_ip_configuration {
    name                 = "frontend-ip"
    public_ip_address_id = azurerm_public_ip.appgw.id
  }

  frontend_port {
    name = "port-80"
    port = 80
  }

  # Backend pool — FastAPI Container App
  backend_address_pool {
    name  = "api-backend-pool"
    fqdns = [azurerm_container_app.api.ingress[0].fqdn]
  }

  backend_http_settings {
    name                                = "api-http-settings"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 120
    pick_host_name_from_backend_address = true
    probe_name                          = "api-health-probe"
  }

  probe {
    name                                      = "api-health-probe"
    protocol                                  = "Https"
    path                                      = "/health"
    interval                                  = 30
    timeout                                   = 10
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = true
    match {
      status_code = ["200"]
    }
  }

  http_listener {
    name                           = "http-listener"
    frontend_ip_configuration_name = "frontend-ip"
    frontend_port_name             = "port-80"
    protocol                       = "Http"
  }

  request_routing_rule {
    name                       = "routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "http-listener"
    backend_address_pool_name  = "api-backend-pool"
    backend_http_settings_name = "api-http-settings"
    priority                   = 100
  }
}

# ═══════════════════════════════════════════════════════════════
#  CONTAINER APPS
# ═══════════════════════════════════════════════════════════════

resource "azurerm_container_app_environment" "env" {
  name                       = "${var.app_name}-env"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
  infrastructure_subnet_id   = azurerm_subnet.container_apps.id
}

# ── FastAPI ────────────────────────────────────────────────────
resource "azurerm_container_app" "api" {
  name                         = "${var.app_name}-api"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }
  # Only create the hf-token secret when a value is supplied — Azure rejects
  # empty secret values (ContainerAppSecretInvalid).
  dynamic "secret" {
    for_each = var.hf_token != "" ? [1] : []
    content {
      name  = "hf-token"
      value = var.hf_token
    }
  }

  template {
    container {
      name    = "api"
      image   = "shadsahaddad11111/llm-eval-model:latest"
      cpu     = 1.0
      memory  = "2Gi"
      command = ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }
      dynamic "env" {
        for_each = var.hf_token != "" ? [1] : []
        content {
          name        = "HF_TOKEN"
          secret_name = "hf-token"
        }
      }
    }

    min_replicas = 1
    max_replicas = 5

    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = 20
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

# ── Prometheus ─────────────────────────────────────────────────
resource "azurerm_container_app" "prometheus" {
  name                         = "${var.app_name}-prometheus"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  template {
    container {
      name   = "prometheus"
      image  = "prom/prometheus:latest"
      cpu    = 0.5
      memory = "1Gi"

      args = [
        "--config.file=/etc/prometheus/prometheus.yml",
        "--storage.tsdb.path=/prometheus",
        "--web.enable-lifecycle",
      ]

      env {
        name  = "API_FQDN"
        value = azurerm_container_app.api.ingress[0].fqdn
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    external_enabled = false
    target_port      = 9090
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

# ── Streamlit UI (MEYAR) ───────────────────────────────────────
# Same image as the API; only the start command differs. Talks to the
# FastAPI app over HTTPS via the API_URL env var (app.py reads API_URL).
resource "azurerm_container_app" "streamlit" {
  name                         = "${var.app_name}-streamlit"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  template {
    container {
      name   = "streamlit"
      image  = "shadsahaddad11111/llm-eval-model:latest"
      cpu    = 0.5
      memory = "1Gi"

      command = [
        "streamlit", "run", "src/app/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        # Behind the Container Apps ingress proxy these must be off or the
        # websocket/session handshake is blocked.
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
      ]

      env {
        name  = "API_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
