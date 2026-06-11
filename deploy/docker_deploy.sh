#!/bin/bash
# ============================================================
# Deploy with Docker to Azure VM
# Run from inside the LLM-Eval-model folder:
#
#   # If using Terraform (recommended):
#   bash deploy/docker_deploy.sh $(cd terraform && terraform output -raw vm_public_ip)
#
#   # Or pass IP directly:
#   bash deploy/docker_deploy.sh <VM_PUBLIC_IP>
#
# Prerequisites:
#   - VM already provisioned (via Terraform or 1_create_vm.sh)
#   - .env file in project root with OPENAI_API_KEY
# ============================================================

set -e

VM_IP="${1:?Usage: bash deploy/docker_deploy.sh <VM_PUBLIC_IP>}"
ADMIN_USER="azureuser"
REMOTE_DIR="/home/$ADMIN_USER/llm_eval"

# Check .env
if [ ! -f ".env" ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and add your keys."
  exit 1
fi

# ── Step 1: Install Docker on VM ──────────────────────────────────────────────
echo ">>> [1/4] Setting up Docker on VM..."
scp -o StrictHostKeyChecking=no deploy/vm_setup_docker.sh $ADMIN_USER@$VM_IP:~/
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "bash ~/vm_setup_docker.sh"

# ── Step 2: Upload project ────────────────────────────────────────────────────
echo ">>> [2/4] Uploading project..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "mkdir -p $REMOTE_DIR"
rsync -avz \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.git'        --exclude 'outputs/*' \
  --exclude 'terraform/.terraform' \
  -e "ssh -o StrictHostKeyChecking=no" \
  ./ $ADMIN_USER@$VM_IP:$REMOTE_DIR/

# ── Step 3: Build & run ───────────────────────────────────────────────────────
echo ">>> [3/4] Building Docker image on VM and starting containers..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "
  cd $REMOTE_DIR
  sudo docker compose up --build
"

# ── Step 4: Download results ──────────────────────────────────────────────────
echo ">>> [4/4] Downloading results..."
mkdir -p outputs
scp -o StrictHostKeyChecking=no \
  "$ADMIN_USER@$VM_IP:$REMOTE_DIR/outputs/*.csv" \
  ./outputs/ 2>/dev/null && echo "Results saved to ./outputs/" || echo "No CSV outputs yet."

echo ""
echo "=========================================="
echo "  Done!  Check ./outputs/ for results."
echo "  Live logs: ssh $ADMIN_USER@$VM_IP"
echo "             cd $REMOTE_DIR && sudo docker compose logs -f app"
echo "=========================================="
