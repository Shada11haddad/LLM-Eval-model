# Required GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

| Secret name            | What it is | How to get it |
|------------------------|-----------|---------------|
| `AZURE_CLIENT_ID`      | Azure service principal app ID | See instructions below |
| `AZURE_CLIENT_SECRET`  | Azure service principal password | See instructions below |
| `AZURE_SUBSCRIPTION_ID`| Your Azure subscription ID | `az account show --query id -o tsv` |
| `AZURE_TENANT_ID`      | Your Azure tenant ID | `az account show --query tenantId -o tsv` |
| `SSH_PRIVATE_KEY`      | Contents of `~/.ssh/id_rsa` | `cat ~/.ssh/id_rsa` |
| `SSH_PUBLIC_KEY`       | Contents of `~/.ssh/id_rsa.pub` | `cat ~/.ssh/id_rsa.pub` |
| `OPENAI_API_KEY`       | Your OpenAI API key | platform.openai.com |
| `HF_TOKEN`             | HuggingFace token (optional) | huggingface.co/settings/tokens |

---

## Create an Azure Service Principal

Run this once in your terminal (needs Azure CLI):

```bash
az ad sp create-for-rbac \
  --name "llm-eval-github-actions" \
  --role Contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID> \
  --sdk-auth
```

This outputs JSON. Map the fields to secrets:

```
clientId       → AZURE_CLIENT_ID
clientSecret   → AZURE_CLIENT_SECRET
subscriptionId → AZURE_SUBSCRIPTION_ID
tenantId       → AZURE_TENANT_ID
```
