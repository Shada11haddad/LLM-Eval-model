import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Paths
    DATA_RAW_DIR = "data/raw"
    DATA_PROCESSED_DIR = "data/processed"
    OUTPUTS_DIR = "outputs"
    
    # Chunking
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Embedding
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_COST_PER_1M = 0.02
    
    # Models
    DEEPSEEK_MODEL = "deepseek-r1:7b"
    LLAMA_MODEL = "llama3.2"
    JUDGE_MODEL = "gpt-5.5"  
    
    # Pricing per 1M tokens (input, output)
    PRICING = {
        DEEPSEEK_MODEL: {"input": 0.07, "output": 0.27},
        LLAMA_MODEL: {"input": 0.06, "output": 0.06},
        "text-embedding-3-small": {"input": 0.02, "output": 0.00},
        JUDGE_MODEL: {"input": 5.00, "output": 15.00},
    }
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # FAISS files
    FAISS_INDEX_PATH = os.path.join(DATA_PROCESSED_DIR, "podcast_index.faiss")
    CHUNKS_PKL_PATH = os.path.join(DATA_PROCESSED_DIR, "podcast_chunks.pkl")
    
    # Evaluation counts (reduce if hitting rate limits)
    NUM_RAG_QUESTIONS = 10
    NUM_TQA_QUESTIONS = 10

cfg = Config()

# إنشاء المجلدات إذا لم توجد
for d in [cfg.DATA_RAW_DIR, cfg.DATA_PROCESSED_DIR, cfg.OUTPUTS_DIR]:
    os.makedirs(d, exist_ok=True)