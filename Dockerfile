FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output/data directories
RUN mkdir -p outputs data/raw data/processed

# Default: batch evaluation (overridden by docker-compose per service)
CMD ["python", "scripts/run_full_evaluation.py"]
