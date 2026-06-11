FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    loguru python-dotenv \
    langchain langchain-openai langchain-ollama langchain-text-splitters \
    faiss-cpu kagglehub pandas tqdm openai numpy matplotlib sentence_transformers

# Copy project files
COPY . .

# Create output/data directories
RUN mkdir -p outputs data/raw data/processed

CMD ["python", "scripts/run_full_evaluation.py"]
