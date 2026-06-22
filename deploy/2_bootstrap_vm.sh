#!/bin/bash
# ============================================================
# STEP 2 — Bootstrap the VM (install Python, Ollama, pull models)
# Run from your LOCAL machine:
#   bash 2_bootstrap_vm.sh <VM_PUBLIC_IP>
# ============================================================

set -e

VM_IP="${1:?Usage: bash 2_bootstrap_vm.sh <VM_PUBLIC_IP>}"
ADMIN_USER="azureuser"

echo ">>> Uploading setup script to VM..."
scp -o StrictHostKeyChecking=no _vm_setup_remote.sh $ADMIN_USER@$VM_IP:~/setup.sh

echo ">>> Running setup on VM (this takes ~10-15 min — models are large)..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "bash ~/setup.sh"

echo ""
echo "=========================================="
echo "  VM is bootstrapped!"
echo "  Next step: run  3_upload_and_run.sh  $VM_IP"
echo "=========================================="
