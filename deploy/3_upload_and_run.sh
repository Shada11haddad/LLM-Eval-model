#!/bin/bash
# ============================================================
# STEP 3 — Upload project & run the evaluation
# Run from your LOCAL machine inside the LLM-Eval-model folder:
#   bash deploy/3_upload_and_run.sh <VM_PUBLIC_IP>
#
# Prerequisites:
#   - .env file exists in the LLM-Eval-model root with your OPENAI_API_KEY
# ============================================================

set -e

VM_IP="${1:?Usage: bash deploy/3_upload_and_run.sh <VM_PUBLIC_IP>}"
ADMIN_USER="azureuser"
REMOTE_DIR="/home/$ADMIN_USER/llm_eval"

# Check .env exists
if [ ! -f ".env" ]; then
  echo "ERROR: .env file not found in current directory."
  echo "Copy deploy/.env.example to .env and fill in your keys."
  exit 1
fi

echo ">>> Uploading project files..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "mkdir -p $REMOTE_DIR"

rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
  -e "ssh -o StrictHostKeyChecking=no" \
  ./ $ADMIN_USER@$VM_IP:$REMOTE_DIR/

echo ">>> Installing Python dependencies on VM..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "
  cd $REMOTE_DIR
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install langchain-ollama
"

echo ">>> Running evaluation (output will stream here)..."
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "
  cd $REMOTE_DIR
  source venv/bin/activate
  python scripts/run_full_evaluation.py
"

echo ""
echo "=========================================="
echo "  Evaluation complete! Downloading results..."
echo "=========================================="

mkdir -p outputs
scp -o StrictHostKeyChecking=no \
  $ADMIN_USER@$VM_IP:$REMOTE_DIR/outputs/*.csv \
  ./outputs/

echo "Results saved to ./outputs/"
