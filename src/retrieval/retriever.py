import numpy as np
from langchain_openai import OpenAIEmbeddings
from config import cfg

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OpenAIEmbeddings(
            model=cfg.EMBEDDING_MODEL,
            api_key=cfg.OPENAI_API_KEY,
        )
    return _embedding_model


def retrieve(query: str, index, chunks, k: int = 3):
    """Return top-k chunks for a query."""
    query_emb = _get_embedding_model().embed_query(query)
    query_emb = np.array([query_emb]).astype("float32")
    D, I = index.search(query_emb, k)
    results = []
    for rank, idx in enumerate(I[0]):
        results.append({
            "rank": rank + 1,
            "chunk": chunks[idx].page_content,
            "distance": float(D[0][rank]),
            "chunk_index": chunks[idx].metadata.get("chunk_index"),
        })
    return results


def build_rag_prompt(question: str, retrieved_chunks: list) -> str:
    context = "\n\n".join(retrieved_chunks)
    return (
        "Answer the question using only the context below.\n"
        "If the answer is not in the context, say: I don't know.\n\n"
        "Context:\n" + context + "\n\n"
        "Question:\n" + question + "\n\n"
        "Answer:"
    )
