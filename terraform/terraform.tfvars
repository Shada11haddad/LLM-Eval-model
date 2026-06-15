# ── terraform.tfvars ──────────────────────────────────────────────────────────
# This file is gitignored — never commit it.
# SSH keys are generated automatically — nothing to paste here.
# Run: terraform -chdir=terraform plan -out=tfplan
# ─────────────────────────────────────────────────────────────────────────────

resource_group_name = "llm-eval-rg"
location            = "swedencentral"          # better free-trial capacity than eastus
vm_name             = "llm-eval-vm"
vm_size             = "Standard_B4ms"    # 4 vCPU / 16 GB — ~$0.166/hr, burstable, reliable on free trial
admin_username      = "azureuser"



##eastus2 replaced with swedencentral 
