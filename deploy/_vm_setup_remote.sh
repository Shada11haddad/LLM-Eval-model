#!/bin/bash
# ============================================================
# This script runs ON THE VM (uploaded automatically by step 2)
# Do NOT run this on your local machine
# ============================================================

set -e

echo "--- [1/5] System update ---"
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git curl unzip

echo "--- [2/5] Install Ollama ---"
curl -fsSL https://ollama.com/install.sh | sh

echo "--- [3/5] Start Ollama service ---"
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 5   # wait for daemon to be ready

echo "--- [4/5] Pull models (this is the slow part) ---"
ollama pull deepseek-r1:7b
ollama pull llama3.2

echo "--- [5/5] Verify models loaded ---"
ollama list

echo ""
echo "VM setup complete. Ollama is running with DeepSeek-R1 7B and Llama 3.2."
