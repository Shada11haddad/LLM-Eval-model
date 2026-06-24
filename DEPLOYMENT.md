# Deployment Guide

This project deploys to **Azure Container Apps** via **Terraform**, driven by a
**GitHub Actions** pipeline. A push to `main` builds the Docker image, pushes it
to Docker Hub, and provisions/updates all Azure infrastructure automatically.

---

## Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │              Azure (resource group)          │
   GitHub push (main)     │                                              │
        │                 │   ┌────────────────────────────────────┐     │
        ▼                 │   │   Application Gateway (WAF_v2)      │     │
  ┌───────────┐  image    │   │   public IP  ─  OWASP WAF policy   │     │
  │  GitHub   │ ────────► │   └───────────────┬────────────────────┘     │
  │  Actions  │ Docker Hub│                   │ (HTTP :80)               │
  └─────┬─────┘           │                   ▼                          │
        │ terraform       │   ┌────────────────────────────────────┐     │
        └───────────────► │   │     Container App Environment       │    │
                          │   │  ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
                          │   │  │ api      │ │ streamlit│ │ prom │ │    │
                          │   │  │ FastAPI  │ │  MEYAR   │ │ etheus│ │   │
                          │   │  │ :8000    │ │  :8501   │ │ :9090 │ │   │
                          │   │  └──────────┘ └──────────┘ └──────┘ │    │
                          │   └────────────────────────────────────┘     │
                          │       VNet · subnets · Log Analytics         │
                          └──────────────────────────────────────────────┘
```

### Resources provisioned (`terraform/main.tf`)

| Resource | Purpose |
|---|---|
| `azurerm_resource_group` | Holds everything (name pinned — see below) |
| `azurerm_log_analytics_workspace` | Container Apps logs |
| `azurerm_virtual_network` + 2 subnets | `appgw-subnet` (/24), `container-apps-subnet` (/23, delegated to `Microsoft.App/environments`) |
| `azurerm_public_ip` | Static public IP for the gateway |
| `azurerm_web_application_firewall_policy` | OWASP 3.2, Prevention mode |
| `azurerm_application_gateway` (WAF_v2) | Public entry point, TLS policy `AppGwSslPolicy20220101` |
| `azurerm_container_app_environment` | Shared environment for the apps |
| `azurerm_container_app.api` | FastAPI backend, external, port 8000 |
| `azurerm_container_app.streamlit` | MEYAR Streamlit UI, external, port 8501 |
| `azurerm_container_app.prometheus` | Metrics, internal, port 9090 |

The **API**, **Streamlit**, and **Prometheus** apps all run from the **same Docker
image** (`shadsahaddad11111/llm-eval-model:latest`) — only the start command differs.

---

## Prerequisites

1. An **Azure subscription** and a **service principal** (SP) with **Contributor**
   on it (Contributor is required so the pipeline can register resource providers).
2. A **Docker Hub** account for the image registry.
3. **GitHub repository secrets** (Settings → Secrets and variables → Actions):

   | Secret | What it is |
   |---|---|
   | `AZURE_CLIENT_ID` | SP application (client) ID |
   | `AZURE_CLIENT_SECRET` | SP client secret |
   | `AZURE_SUBSCRIPTION_ID` | Target subscription ID |
   | `AZURE_TENANT_ID` | Azure AD tenant ID |
   | `DOCKERHUB_USERNAME` | Docker Hub username |
   | `DOCKERHUB_TOKEN` | Docker Hub access token |
   | `OPENAI_API_KEY` | OpenAI key (injected as a container secret) |
   | `HF_TOKEN` | HuggingFace token (optional — omit to skip) |

   > **Paste secrets cleanly — no trailing newline.** A stray `\n` in
   > `OPENAI_API_KEY` produces `Illegal header value b'Bearer sk-...\n'` at
   > runtime. Terraform now `trimspace()`s these as a safety net, but a clean
   > value is the real fix.

---

## How the pipeline works (`.github/workflows/docker.yml`)

On every push to `main`:

1. **build-and-push** — builds the image from `Dockerfile` and pushes it to
   Docker Hub (`latest` + a `sha-` tag).
2. **terraform** (runs after the build):
   - **Azure login** with the SP (`creds` JSON form — required for client-secret auth).
   - **Bootstrap remote state** — creates the state storage account
     (`llmevaltfstate` in `llm-eval-tfstate-rg`, container `tfstate`) and
     **registers resource providers** (`Microsoft.Storage`, `Microsoft.App`,
     `Microsoft.Network`, `Microsoft.OperationalInsights`,
     `Microsoft.ManagedIdentity`). A fresh subscription needs this or ARM
     returns a misleading `SubscriptionNotFound`.
   - **`terraform init`** — connects to the Azure Blob backend.
   - **`terraform apply`** — provisions/updates everything. Secrets are passed
     with `-var`, never committed.
   - **Print deployment URLs** — echoes the public IP and app URLs.

### Remote state

State lives in **Azure Blob Storage**, not in git (`terraform/main.tf` →
`backend "azurerm"`). This lets CI and any developer share one authoritative,
locked state. The local `terraform.tfstate` file is unused and gitignored.

---

## Deployment URLs

After a successful run, the final step prints (and `terraform output` exposes):

| Output | Example |
|---|---|
| `public_ip` | `20.67.110.45` |
| `api_url` | `http://<public_ip>` (FastAPI via the gateway) |
| `api_docs_url` | `http://<public_ip>/docs` (Swagger) |
| `streamlit_url` | `https://llm-eval-streamlit.<region>.azurecontainerapps.io` (MEYAR UI) |

---

## ⚠️ The resource group name is PINNED

`resource_group_name` in `terraform/terraform.tfvars` is set to **`llm-eval-rg`**
and **must not change**. Because the remote backend tracks every resource,
keeping the name stable lets Terraform run **incrementally** (seconds).

**Changing the name forces a full destroy + recreate** of the entire stack,
including a **~5-minute Container App Environment teardown**. To remove an old or
orphaned resource group, do it out-of-band and asynchronously instead:

```bash
az group delete -n <old-rg-name> --yes --no-wait   # returns immediately
```

> Never delete `llm-eval-tfstate-rg` — it holds the Terraform state.

---

## Running Terraform locally (optional)

CI normally handles this. To run by hand:

```bash
cd terraform
terraform init
terraform apply \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="hf_token=$HF_TOKEN"

terraform output            # show all URLs
```

You must be logged in to the same Azure subscription (`az login`) with rights to
the state storage account.

---

## Running locally with Docker Compose

`docker-compose.yml` runs the full stack on your machine (Ollama for local
models, FastAPI, the Streamlit UI, and a one-shot batch evaluation):

```bash
docker compose up --build
# FastAPI   → http://localhost:8000  (docs at /docs)
# Streamlit → http://localhost:8501
```

Put `OPENAI_API_KEY` / `HF_TOKEN` in a local `.env` (gitignored).

---

## Common operations

| Task | How |
|---|---|
| Deploy / update | Push to `main` (CI runs automatically) |
| See live URLs | `cd terraform && terraform output` |
| Roll a new image build | Push any code change to `main` |
| Tear everything down | `cd terraform && terraform destroy` (slow — ~5 min for the environment) |
| Delete an orphaned RG | `az group delete -n <name> --yes --no-wait` |

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `SubscriptionNotFound` on a `Microsoft.Storage`/`Microsoft.App` call | Provider not registered on a fresh subscription. The bootstrap step registers them; ensure the SP has Contributor. |
| `Unexpected input 'client-secret'` / federated token error | Use the `creds:` JSON form of `azure/login`, not separate `client-id`/`client-secret` inputs (that triggers OIDC). |
| `ManagedEnvironmentSubnetDelegationError` | The container-apps subnet must be delegated to `Microsoft.App/environments` (already configured). |
| `ContainerAppSecretInvalid: ... 'hf-token' ... value ... should be provided` | `HF_TOKEN` secret is empty. Add it, or leave it unset — the secret/env are only created when a value is present. |
| `ApplicationGatewayWafConfigurationDeprecated` | Inline WAF on the gateway is retired; WAF lives in `azurerm_web_application_firewall_policy` attached via `firewall_policy_id` (already configured). |
| `ApplicationGatewayDeprecatedTlsVersionUsedInSslPolicy` | Gateway needs an explicit modern `ssl_policy` (`AppGwSslPolicy20220101`, already configured). |
| OpenAI shows `Illegal header value b'Bearer sk-...\n'` | Trailing newline in `OPENAI_API_KEY`. Re-save the secret without it; Terraform also `trimspace()`s it. |
| Deploy "fails" only at the **Print deployment URLs** step | Transient state-read blip. The step reads all outputs in one call and is `continue-on-error` — the actual deploy succeeded. |
| Code change pushed but app not updated | Apps reference the `:latest` image tag; an unchanged Terraform config won't roll a new revision. Switch to SHA-tagged images if you need every push to redeploy. |
