#!/bin/bash
# ============================================================
# STEP 1 — Create Azure VM for RAG Evaluation
# Run this ONCE from your local machine (needs Azure CLI installed)
# Install Azure CLI: https://aka.ms/installazurecliwindows
# ============================================================

set -e

# ---------- EDIT THESE ----------
RESOURCE_GROUP="rag-eval-rg"
VM_NAME="rag-eval-vm"
LOCATION="eastus"           # change to a region near you
VM_SIZE="Standard_D8s_v3"   # 8 vCPUs, 32 GB RAM — runs Ollama on CPU
                             # For GPU inference use: Standard_NC4as_T4_v3
ADMIN_USER="azureuser"
# --------------------------------

echo ">>> Logging in to Azure..."
az login

echo ">>> Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION

echo ">>> Creating VM: $VM_NAME  (size: $VM_SIZE)"
az vm create \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --image Ubuntu2204 \
  --size $VM_SIZE \
  --admin-username $ADMIN_USER \
  --generate-ssh-keys \
  --output json \
  --verbose

echo ">>> Opening port 22 (SSH)"
az vm open-port --port 22 --resource-group $RESOURCE_GROUP --name $VM_NAME

# Get the public IP
PUBLIC_IP=$(az vm show -d -g $RESOURCE_GROUP -n $VM_NAME --query publicIps -o tsv)
echo ""
echo "=========================================="
echo "  VM is ready!"
echo "  IP address : $PUBLIC_IP"
echo "  Connect via: ssh $ADMIN_USER@$PUBLIC_IP"
echo ""
echo "  Next step  : run  2_bootstrap_vm.sh  $PUBLIC_IP"
echo "=========================================="
