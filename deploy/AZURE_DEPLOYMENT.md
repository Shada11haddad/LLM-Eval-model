# Azure Deployment Guide — LLM Evaluation Platform

## What gets deployed

| Component | Where it runs |
|---|---|
| DeepSeek R1 7B | Azure VM via Ollama |
| Llama 3.2 | Azure VM via Ollama |
| GPT judge + embeddings | OpenAI API (unchanged) |

## Prerequisites

1. **Azure CLI** installed on your computer → https://aka.ms/installazurecliwindows
2. An **Azure account** with an active subscription
3. Your **OpenAI API key**

---

## Step-by-step

### Step 1 — Create the VM

```bash
bash deploy/1_create_vm.sh
```

This creates a **Standard_D8s_v3** VM (8 vCPUs, 32 GB RAM) in Azure.
At the end it prints the VM's public IP address — **save it**.

> 💡 Want GPU inference? Change `VM_SIZE` in the script to `Standard_NC4as_T4_v3` (costs more but runs models 5-10× faster).

---

### Step 2 — Bootstrap the VM

```bash
bash deploy/2_bootstrap_vm.sh <VM_PUBLIC_IP>
```

Installs Python, Ollama, and pulls both models onto the VM (~10-15 min).

---

### Step 3 — Set up your .env file

Copy the example and fill in your OpenAI key:

```bash
cp deploy/.env.example .env
# then open .env and add your OPENAI_API_KEY
```

---

### Step 4 — Upload and run

From inside the RAG_EVAL folder:

```bash
bash deploy/3_upload_and_run.sh <VM_PUBLIC_IP>
```

This:
- Uploads your code to the VM
- Installs Python dependencies
- Runs `run_full_evaluation.py`
- Downloads the result CSVs back to your local `outputs/` folder

---

### Step 5 — Clean up (stop billing)

When you're done, delete the VM so Azure stops charging you:

```bash
bash deploy/4_cleanup.sh
```

---

## Estimated costs

| Item | Cost |
|---|---|
| Standard_D8s_v3 VM | ~$0.38/hour |
| OpenAI embeddings + judge | ~$0.05–0.20 per full run |
| Storage / networking | negligible |

A typical evaluation run takes 15-30 minutes, so total Azure cost is **under $0.20 per run**.

---

## Troubleshooting

**SSH permission denied** — Make sure your SSH key was generated (`~/.ssh/id_rsa`). Re-run `az vm create` with `--generate-ssh-keys`.

**Ollama model pull times out** — The VM may need more time. SSH in manually and run `ollama pull deepseek-r1:7b` again.

**OpenAI rate limit errors** — Reduce `NUM_RAG_QUESTIONS` and `NUM_TQA_QUESTIONS` in `config.py`.

**rsync not found (Windows)** — Use Git Bash or WSL to run the shell scripts, or install rsync via `choco install rsync`.
