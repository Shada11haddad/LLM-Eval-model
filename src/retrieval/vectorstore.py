import numpy as np
import faiss
import pickle
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from config import cfg

def build_embeddings_and_index(chunks):
    """Generate embeddings and build FAISS index"""
    texts = [chunk.page_content for chunk in chunks]
    
    total_chars = sum(len(t) for t in texts)
    est_tokens = total_chars / 4
    est_cost = est_tokens / 1_000_000 * cfg.EMBEDDING_COST_PER_1M
    print(f"Chunks to embed: {len(texts):,}")
    print(f"Estimated tokens: {est_tokens:,.0f}, cost: ${est_cost:.4f}")
    
    embedding_model = OpenAIEmbeddings(
        model=cfg.EMBEDDING_MODEL,
        api_key=cfg.OPENAI_API_KEY,
    )
    
    BATCH_SIZE = 100
    embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Embedding"):
        batch = texts[i:i+BATCH_SIZE]
        batch_embeds = embedding_model.embed_documents(batch)
        embeddings.extend(batch_embeds)
    
    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save
    faiss.write_index(index, cfg.FAISS_INDEX_PATH)
    with open(cfg.CHUNKS_PKL_PATH, "wb") as f:
        pickle.dump(chunks, f)
    
    print(f"✅ FAISS index saved: {index.ntotal} vectors, dim={dimension}")
    return index, chunks, embeddings, est_cost

def load_vectorstore():
    """Load existing FAISS index and chunks"""
    import pickle
    index = faiss.read_index(cfg.FAISS_INDEX_PATH)
    with open(cfg.CHUNKS_PKL_PATH, "rb") as f:
        chunks = pickle.load(f)
    print(f"✅ Loaded FAISS index with {index.ntotal} vectors")
    return index, chunks