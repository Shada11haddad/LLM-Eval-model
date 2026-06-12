"""
quick_test.py - Runs 10 RAG + 10 TQA questions with clear output
so you can confirm the full pipeline is working on Azure.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tqdm import tqdm
from langchain_core.documents import Document
from config import cfg
from src.ingestion.loader import load_truthfulqa, load_podcast_transcript
from src.ingestion.chunker import chunk_documents
from src.retrieval.vectorstore import build_embeddings_and_index, load_vectorstore
from src.retrieval.retriever import retrieve, build_rag_prompt
from src.generation.deepseek import ask_deepseek
from src.generation.llama import ask_llama
from src.evaluation.judge_rag import judge_rag_answers
from src.evaluation.judge_tqa import judge_truthfulqa_answers
from src.evaluation.parse_verdict import parse_judge_verdict
from src.evaluation.metrics import get_current_metrics, totals
from src.storage.database import create_run, save_results, finish_run
from src.utils.helpers import polite_sleep

SEP = "=" * 60

def check_ollama():
    import urllib.request
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        urllib.request.urlopen(host, timeout=5)
        print(f"[OK] Ollama reachable at {host}")
    except Exception as e:
        print(f"[FAIL] Ollama not reachable at {host}: {e}")
        print("       Make sure the ollama container is running.")
        sys.exit(1)

def check_openai():
    if not cfg.OPENAI_API_KEY:
        print("[FAIL] OPENAI_API_KEY not set - check your .env file")
        sys.exit(1)
    print("[OK] OpenAI API key found")

def print_result_table(df, model_col_prefix):
    wins_ds = (df["winner"].str.lower().str.contains("deepseek", na=False)).sum()
    wins_ll = (df["winner"].str.lower().str.contains("llama", na=False)).sum()
    avg_lat_ds = df[f"{model_col_prefix[0]}_latency_s"].mean()
    avg_lat_ll = df[f"{model_col_prefix[1]}_latency_s"].mean()
    print(f"  DeepSeek wins : {wins_ds}/{len(df)}  |  avg latency: {avg_lat_ds:.1f}s")
    print(f"  Llama wins    : {wins_ll}/{len(df)}  |  avg latency: {avg_lat_ll:.1f}s")

def main():
    print(SEP)
    print("  LLM EVAL - 10 RAG + 10 TQA (Azure validation run)")
    print(SEP)

    # Pre-flight checks
    print("\n[0] Pre-flight checks...")
    check_ollama()
    check_openai()

    # Register run in DB
    run_id = create_run(
        deepseek_model=cfg.DEEPSEEK_MODEL,
        llama_model=cfg.LLAMA_MODEL,
        judge_model=cfg.JUDGE_MODEL,
        embedding_model=cfg.EMBEDDING_MODEL,
        chunk_size=cfg.CHUNK_SIZE,
        chunk_overlap=cfg.CHUNK_OVERLAP,
        num_rag_questions=cfg.NUM_RAG_QUESTIONS,
        num_tqa_questions=cfg.NUM_TQA_QUESTIONS,
        notes="azure_validation",
    )
    print(f"[OK] Run #{run_id} registered in {cfg.DB_PATH}")

    # Load data
    print("\n[1] Loading data and vector index...")
    truthfulqa = load_truthfulqa()
    podcast_text = load_podcast_transcript()
    docs = [Document(page_content=podcast_text)]
    chunks = chunk_documents(docs)
    try:
        index, chunks = load_vectorstore()
        embedding_cost = 0.0
        print("[OK] Loaded existing FAISS index")
    except (FileNotFoundError, RuntimeError):
        index, chunks, _, embedding_cost = build_embeddings_and_index(chunks)
        print(f"[OK] Built new FAISS index (cost: ${embedding_cost:.4f})")

    # RAG evaluation - 10 questions
    podcast_questions = [
        "What is the Acquired podcast about?",
        "What is NVIDIA's CUDA platform?",
        "How did Apple build its supply chain in China?",
        "What made TSMC dominant?",
        "Why did Disney acquire Pixar?",
        "How did Netflix transition to streaming?",
        "What is Costco's business model?",
        "How did Walmart expand into e-commerce?",
        "What is Berkshire Hathaway's philosophy?",
        "How did Spotify disrupt music?",
    ]
    N_RAG = min(cfg.NUM_RAG_QUESTIONS, len(podcast_questions))
    rag_rows = []

    print(f"\n[2] RAG evaluation ({N_RAG} questions)...")
    for i, q in enumerate(tqdm(podcast_questions[:N_RAG], desc="RAG")):
        retrieved = retrieve(q, index, chunks, k=3)
        context_chunks = [r["chunk"] for r in retrieved]
        context = "\n\n".join(context_chunks)
        prompt = build_rag_prompt(q, context_chunks)

        ds_ans = ask_deepseek(prompt)
        polite_sleep()
        ds_m = get_current_metrics(cfg.DEEPSEEK_MODEL)

        ll_ans = ask_llama(prompt)
        polite_sleep()
        ll_m = get_current_metrics(cfg.LLAMA_MODEL)

        verdict = judge_rag_answers(q, context, ds_ans, ll_ans, ds_m, ll_m)
        parsed = parse_judge_verdict(verdict)
        rag_rows.append({
            "question": q,
            "context": context[:300],
            "deepseek_answer": ds_ans,
            "deepseek_latency_s": ds_m.get("latency_s", 0),
            "deepseek_cost_usd": ds_m.get("cost_usd", 0),
            "llama_answer": ll_ans,
            "llama_latency_s": ll_m.get("latency_s", 0),
            "llama_cost_usd": ll_m.get("cost_usd", 0),
            "judge_verdict": verdict,
            **parsed,
        })
        polite_sleep()

    df_rag = pd.DataFrame(rag_rows)
    df_rag.to_csv(f"{cfg.OUTPUTS_DIR}/rag_evaluation.csv", index=False)
    save_results(df_rag, "rag_results", run_id)

    # TQA evaluation - 10 questions
    N_TQA = min(cfg.NUM_TQA_QUESTIONS, len(truthfulqa))
    sampled_tqa = truthfulqa.sample(n=N_TQA).reset_index()
    tqa_rows = []

    print(f"\n[3] TruthfulQA evaluation ({N_TQA} questions)...")
    for _, row in tqdm(sampled_tqa.iterrows(), total=N_TQA, desc="TQA"):
        q = row["Question"]
        ds_ans = ask_deepseek(q)
        polite_sleep()
        ds_m = get_current_metrics(cfg.DEEPSEEK_MODEL)

        ll_ans = ask_llama(q)
        polite_sleep()
        ll_m = get_current_metrics(cfg.LLAMA_MODEL)

        verdict = judge_truthfulqa_answers(
            q, row["Best Answer"], row["Correct Answers"],
            row["Incorrect Answers"], ds_ans, ll_ans, ds_m, ll_m,
        )
        parsed = parse_judge_verdict(verdict)
        tqa_rows.append({
            "question": q,
            "best_answer": row["Best Answer"],
            "deepseek_answer": ds_ans,
            "deepseek_latency_s": ds_m.get("latency_s", 0),
            "deepseek_cost_usd": ds_m.get("cost_usd", 0),
            "llama_answer": ll_ans,
            "llama_latency_s": ll_m.get("latency_s", 0),
            "llama_cost_usd": ll_m.get("cost_usd", 0),
            "judge_verdict": verdict,
            **parsed,
        })
        polite_sleep()

    df_tqa = pd.DataFrame(tqa_rows)
    df_tqa.to_csv(f"{cfg.OUTPUTS_DIR}/tqa_evaluation.csv", index=False)
    save_results(df_tqa, "tqa_results", run_id)
    finish_run(run_id)

    # Results summary
    print("\n" + SEP)
    print("  RESULTS SUMMARY")
    print(SEP)
    print(f"\nRAG ({N_RAG} questions):")
    print_result_table(df_rag, ("deepseek", "llama"))
    print(f"\nTruthfulQA ({N_TQA} questions):")
    print_result_table(df_tqa, ("deepseek", "llama"))
    print(f"\nTotal judge cost : ${totals['cost_usd']:.4f}")
    print(f"Embedding cost   : ${embedding_cost:.4f}")
    print(f"Results saved to : {cfg.OUTPUTS_DIR}/")
    print(f"Database         : {cfg.DB_PATH}  (run #{run_id})")
    print(SEP)
    print("[DONE] Pipeline confirmed working on Azure!")
    print(SEP)


if __name__ == "__main__":
    main()
