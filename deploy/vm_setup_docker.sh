#!/bin/bash
# ============================================================
# Runs ON the VM — installs Docker & Docker Compose
# Uploaded and executed automatically by docker_deploy.sh
# ============================================================

set -e

echo "--- [1/3] System update ---"
sudo apt-get update -y

echo "--- [2/3] Install Docker ---"
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # allow running docker without sudo

echo "--- [3/3] Install Docker Compose plugin ---"
sudo apt-get install -y docker-compose-plugin

echo ""
echo "Docker installed:"
docker --version
docker compose version
