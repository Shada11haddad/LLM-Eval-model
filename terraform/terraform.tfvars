# ── terraform.tfvars ──────────────────────────────────────────────────────────
# This file is gitignored — never commit it.
# SSH keys are generated automatically — nothing to paste here.
# Run: terraform -chdir=terraform plan -out=tfplan
# ─────────────────────────────────────────────────────────────────────────────

resource_group_name = "llm-eval-rg"
location            = "eastus"           # change to region nearest to you
vm_name             = "llm-eval-vm"
vm_size             = "Standard_D4s_v3"  # 4 vCPU / 16 GB — fits free-tier quota; swap to Standard_D8s_v3 after quota increase
admin_username      = "azureuser"
