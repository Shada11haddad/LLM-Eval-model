
import os
import pickle
import numpy as np
import faiss
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from config import cfg


def _get_paths(name: str):
    """Build index/chunks file paths for a given document/run name"""
    index_path = os.path.join(cfg.FAISS_DIR, f"{name}_index.faiss")
    chunks_path = os.path.join(cfg.FAISS_DIR, f"{name}_chunks.pkl")
    return index_path, chunks_path


def build_embeddings_and_index(chunks, name: str):
    """Generate embeddings and build FAISS index for a specific document"""
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
        batch = texts[i:i + BATCH_SIZE]
        batch_embeds = embedding_model.embed_documents(batch)
        embeddings.extend(batch_embeds)

    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    index_path, chunks_path = _get_paths(name)

    faiss.write_index(index, index_path)
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    print(f"FAISS index saved: {index.ntotal} vectors, dim={dimension} -> {index_path}")
    return index, chunks, embeddings, est_cost


def load_vectorstore(name: str):
    """Load existing FAISS index and chunks for a specific document"""
    index_path, chunks_path = _get_paths(name)

    index = faiss.read_index(index_path)
    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    print(f"Loaded FAISS index '{name}' with {index.ntotal} vectors")
    return index, chunks


def get_or_build_vectorstore(name: str, chunks=None):
    """Load if exists, build if not, for a specific document"""
    index_path, chunks_path = _get_paths(name)

    if os.path.exists(index_path) and os.path.exists(chunks_path):
        print(f"Found existing index for '{name}', loading...")
        return load_vectorstore(name)
    else:
        print(f"No index found for '{name}', building...")
        if chunks is None:
            raise ValueError(
                f"No existing index found for '{name}' and no chunks provided to build one."
            )
        return build_embeddings_and_index(chunks, name)