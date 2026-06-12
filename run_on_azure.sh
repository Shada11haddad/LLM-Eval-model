#!/bin/bash
# ============================================================
# run_on_azure.sh
# One command to provision Azure, deploy, run the evaluation,
# and show you the results.
#
# Run from inside the LLM-Eval-model folder:
#   bash run_on_azure.sh
#
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Terraform installed
#   - .env file with OPENAI_API_KEY
#   - terraform/terraform.tfvars exists
# ============================================================

set -e
SEP="=================================================="

# ── Check .env ────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and add your OPENAI_API_KEY."
  exit 1
fi

echo ""
echo $SEP
echo "  STEP 1/4  Provisioning Azure VM with Terraform"
echo $SEP
cd terraform
terraform init -upgrade
terraform apply -auto-approve
VM_IP=$(terraform output -raw vm_public_ip)
terraform output -raw private_key_pem > generated_key.pem
chmod 600 generated_key.pem
cd ..

echo ""
echo "VM is ready at: $VM_IP"
echo "SSH key saved to: terraform/generated_key.pem"

# Give the VM a moment to fully boot
echo "Waiting 20s for VM to finish booting..."
sleep 20

# ── Deploy with Docker ────────────────────────────────────────────────────────
echo ""
echo $SEP
echo "  STEP 2/4  Installing Docker and deploying containers"
echo $SEP

# Override the SSH key path for docker_deploy.sh
export SSH_KEY_PATH="terraform/generated_key.pem"

# Upload Docker setup to VM
scp -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  deploy/vm_setup_docker.sh azureuser@$VM_IP:~/

ssh -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  azureuser@$VM_IP "bash ~/vm_setup_docker.sh"

echo ""
echo $SEP
echo "  STEP 3/4  Uploading project and running evaluation"
echo "            (models download on first run: ~10-15 min)"
echo $SEP

REMOTE_DIR="/home/azureuser/llm_eval"
ssh -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  azureuser@$VM_IP "mkdir -p $REMOTE_DIR"

rsync -avz \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.git'        --exclude 'outputs/*' \
  --exclude 'terraform/.terraform' --exclude 'terraform/generated_key.pem' \
  -e "ssh -i terraform/generated_key.pem -o StrictHostKeyChecking=no" \
  ./ azureuser@$VM_IP:$REMOTE_DIR/

# Run docker compose — streams all logs so you see progress in real time
ssh -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  azureuser@$VM_IP "cd $REMOTE_DIR && sudo docker compose up --build"

# ── Download results ──────────────────────────────────────────────────────────
echo ""
echo $SEP
echo "  STEP 4/4  Downloading results"
echo $SEP

mkdir -p outputs
scp -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  "azureuser@$VM_IP:$REMOTE_DIR/outputs/rag_evaluation.csv" \
  ./outputs/ 2>/dev/null && echo "Downloaded: rag_evaluation.csv" || true

scp -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  "azureuser@$VM_IP:$REMOTE_DIR/outputs/tqa_evaluation.csv" \
  ./outputs/ 2>/dev/null && echo "Downloaded: tqa_evaluation.csv" || true

scp -i terraform/generated_key.pem -o StrictHostKeyChecking=no \
  "azureuser@$VM_IP:$REMOTE_DIR/outputs/meyar.db" \
  ./outputs/ 2>/dev/null && echo "Downloaded: meyar.db" || true

# ── Show results in terminal ──────────────────────────────────────────────────
echo ""
echo $SEP
echo "  RESULTS"
echo $SEP

if [ -f "outputs/rag_evaluation.csv" ]; then
  echo ""
  echo "RAG Evaluation (top 5 rows):"
  python3 -c "
import pandas as pd
df = pd.read_csv('outputs/rag_evaluation.csv')
cols = ['question','winner','deepseek_latency_s','llama_latency_s']
cols = [c for c in cols if c in df.columns]
print(df[cols].head(5).to_string(index=False))
print(f'  -> DeepSeek wins: {df[\"winner\"].str.lower().str.contains(\"deepseek\",na=False).sum()}/{len(df)}')
print(f'  -> Llama wins:    {df[\"winner\"].str.lower().str.contains(\"llama\",na=False).sum()}/{len(df)}')
"
fi

if [ -f "outputs/tqa_evaluation.csv" ]; then
  echo ""
  echo "TruthfulQA Evaluation (top 5 rows):"
  python3 -c "
import pandas as pd
df = pd.read_csv('outputs/tqa_evaluation.csv')
cols = ['question','winner','deepseek_latency_s','llama_latency_s']
cols = [c for c in cols if c in df.columns]
print(df[cols].head(5).to_string(index=False))
print(f'  -> DeepSeek wins: {df[\"winner\"].str.lower().str.contains(\"deepseek\",na=False).sum()}/{len(df)}')
print(f'  -> Llama wins:    {df[\"winner\"].str.lower().str.contains(\"llama\",na=False).sum()}/{len(df)}')
"
fi

echo ""
echo $SEP
echo "  DONE - Check outputs/ for full CSV results and meyar.db"
echo ""
echo "  To destroy the VM and stop billing:"
echo "    cd terraform && terraform destroy -auto-approve"
echo $SEP
