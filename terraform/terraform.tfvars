# ── terraform.tfvars ──────────────────────────────────────────────────────────
# Non-secret variable values for the Container Apps deployment.
# Secrets (openai_api_key, hf_token) are passed via -var on the CLI / CI, never here.
#
# IMPORTANT: resource_group_name is PINNED. Do NOT change it between runs.
# The remote state backend tracks every resource, so keeping the same name lets
# Terraform run incrementally (seconds). Changing it forces a full destroy +
# recreate of the whole stack — including a ~5 min Container App Environment
# teardown. To delete an old/orphaned RG, do it out-of-band and async:
#   az group delete -n <old-rg-name> --yes --no-wait
# ─────────────────────────────────────────────────────────────────────────────

resource_group_name = "llm-eval-rg" # PINNED — leave this alone
location            = "eastus"  # better free-trial capacity than eastus
