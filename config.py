import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Paths
    DATA_RAW_DIR = "data/raw"
    DATA_PROCESSED_DIR = "data/processed"
    OUTPUTS_DIR = "outputs"
    
    # Chunking
    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200
    
    # Embedding
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_COST_PER_1M = 0.02
    
    MODELS = {
    "deepseek": {
        "provider": "huggingface",
        "model": "deepseek-ai/DeepSeek-V4-Flash",
        "hf_provider": "novita"
    },
    "llama": {
        "provider": "huggingface",
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "hf_provider": "novita"
    },
    "qwen": {
        "provider": "huggingface",
        "model": "Qwen/Qwen3-8B",
        "hf_provider": "nscale"
    },
    "gpt4o": {
        "provider": "openai",
        "model": "gpt-4o"
    },
    "judge": {
        "provider": "openai",
        "model": "gpt-5.5"
    }
}
     


    PRICING = {

    "gpt-4o": {"input": 2.50,"output": 10.00},

    "gpt-5.5": {"input": 1.25,"output": 10.00},

    "text-embedding-3-small": {"input": 0.02,"output": 0.0},

    "deepseek-ai/DeepSeek-V4-Flash": {"input": 0.28,"output": 0.0},

    "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.05,"output": 0.0},

    "Qwen/Qwen3-8B": {"input": 0.18,"output": 0.0},
}
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # FAISS files
    FAISS_DIR = os.path.join (DATA_PROCESSED_DIR,"faiss")

    # SQLite #databse just added
    DB_PATH = os.path.join(OUTPUTS_DIR, "meyar.db")

cfg = Config()

for d in [Config.DATA_RAW_DIR,
              Config.DATA_PROCESSED_DIR,
              Config.OUTPUTS_DIR,
              Config.FAISS_DIR
              ]:
        os.makedirs(d, exist_ok=True)