# ── terraform.tfvars ──────────────────────────────────────────────────────────
# Non-secret variable values for the Container Apps deployment.
# Secrets (openai_api_key, hf_token) are passed via -var on the CLI / CI, never here.
#
# NOTE: a fresh resource_group_name is used per deployment because the old RG is
# not destroyed between runs. Bump the suffix (rg5 -> rg6) for the next run unless
# the previous RG has been deleted.
# ─────────────────────────────────────────────────────────────────────────────

resource_group_name = "llm-eval-rg5"
location            = "westeurope" # better free-trial capacity than eastus
