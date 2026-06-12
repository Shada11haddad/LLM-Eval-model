# GitHub Secrets — Team Setup

Go to: **Repo → Settings → Secrets and variables → Actions → New repository secret**

## Required secrets

| Secret name               | What it is                          | How to get it                        |
|---------------------------|-------------------------------------|--------------------------------------|
| `AZURE_CLIENT_ID`         | Service principal app ID            | See "Create service principal" below |
| `AZURE_CLIENT_SECRET`     | Service principal password          | See "Create service principal" below |
| `AZURE_SUBSCRIPTION_ID`   | Your Azure subscription ID          | `az account show --query id -o tsv`  |
| `AZURE_TENANT_ID`         | Your Azure tenant ID                | `az account show --query tenantId -o tsv` |
| `OPENAI_API_KEY`          | OpenAI API key (judge + embeddings) | platform.openai.com                  |
| `TFSTATE_RESOURCE_GROUP`  | Resource group for Terraform state  | See "Remote state" below             |
| `TFSTATE_STORAGE_ACCOUNT` | Storage account for Terraform state | See "Remote state" below             |

## Not needed
- ~~`SSH_PRIVATE_KEY`~~ — Terraform auto-generates the SSH key pair
- ~~`SSH_PUBLIC_KEY``~~ — same as above
- `HF_TOKEN` — only add if you use a gated HuggingFace dataset

---

## Create an Azure Service Principal (one-time, run as admin)

```bash
az login

# Get your subscription ID
az account show --query id -o tsv

# Create the service principal
az ad sp create-for-rbac \
  --name "llm-eval-github-actions" \
  --role Contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>
```

Output JSON — map to secrets:
```
clientId       → AZURE_CLIENT_ID
clientSecret   → AZURE_CLIENT_SECRET
subscriptionId → AZURE_SUBSCRIPTION_ID
tenantId       → AZURE_TENANT_ID
```

---

## Remote Terraform state (one-time bootstrap — required for teams)

Without this, every CI/CD run starts fresh and fails on re-deploy with
"resource already exists". Set this up once and all team members share state.

```bash
az group create -n llm-eval-tfstate-rg -l eastus

# Note the storage account name it prints — you'll need it
az storage account create \
  -n llmevaltfstate$RANDOM \
  -g llm-eval-tfstate-rg \
  -l eastus \
  --sku Standard_LRS

az storage container create \
  -n tfstate \
  --account-name <STORAGE_ACCOUNT_NAME> \
  --auth-mode login
```

Then add to GitHub Secrets:
```
TFSTATE_RESOURCE_GROUP  = llm-eval-tfstate-rg
TFSTATE_STORAGE_ACCOUNT = <STORAGE_ACCOUNT_NAME>
```

---

## How the pipeline runs

1. Any team member pushes to `main`
2. **CI** runs automatically (lint + import checks)
3. **CD** runs automatically when CI passes:
   - Terraform provisions Azure VM
   - SSH key auto-generated — no manual key management needed
   - Docker builds image on VM and runs `run_full_evaluation.py`
   - Results (CSV + meyar.db) uploaded as GitHub Actions artifact
4. To **destroy the VM** (stop billing): go to Actions tab → CD workflow → Run workflow → set `destroy=true`
