# ── terraform.tfvars ──────────────────────────────────────────────────────────
# This file is gitignored — never commit it.
# SSH keys are generated automatically — nothing to paste here.
# Run: terraform -chdir=terraform plan -out=tfplan
# ─────────────────────────────────────────────────────────────────────────────

resource_group_name = "llm-eval-rg4"
location            = "eastasia"          # better free-trial capacity than eastus
vm_name             = "llm-eval-vm"
vm_size             = "Standard_D4s_v3"    # 4 vCPU / 16 GB — minimum to run the models
admin_username      = "azureuser"



##eastus2 replaced with swedencentral to now with westeurope, eastasia
##Standard_B4ms repalced with Standard_B1s
##every new run needs a new resource_group_name, now its llm-eval-rg2, next time it weill be llm-eval-rg3 unless we deleted the llm-eval-rg2.
