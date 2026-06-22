#!/bin/bash
# ============================================================
# STEP 4 (optional) — Delete Azure resources when you're done
# This stops billing.  Run from your local machine.
# ============================================================

RESOURCE_GROUP="rag-eval-rg"

echo "WARNING: This will permanently delete the VM and all related resources."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" == "yes" ]; then
  az group delete --name $RESOURCE_GROUP --yes --no-wait
  echo "Deletion started. Resources will be removed in a few minutes."
else
  echo "Aborted."
fi
