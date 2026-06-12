import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from tqdm import tqdm
from config import cfg
from src.ingestion.loader import load_truthfulqa, load_podcast_transcript
from src.ingestion.chunker import chunk_documents
from langchain_core.documents import Document
from src.retrieval.vectorstore import build_embeddings_and_index, load_vectorstore
from src.retrieval.retriever import retrieve, build_rag_prompt
from src.generation.deepseek import ask_deepseek
from src.generation.llama import ask_llama
from src.evaluation.judge_rag import judge_rag_answers
from src.evaluation.judge_tqa import judge_truthfulqa_answers
from src.evaluation.parse_verdict import parse_judge_verdict
from src.evaluation.metrics import metrics_tracker, totals, get_current_metrics
from src.utils.helpers import polite_sleep, model_summary
from src.storage.database import create_run, save_results, finish_run


def main():
    print("="*60)
    print("LLM Evaluation Platform - Full Batch Evaluation")
    print("="*60)

    # Register this run in the SQLite database
    run_id = create_run(
        deepseek_model=cfg.DEEPSEEK_MODEL,
        llama_model=cfg.LLAMA_MODEL,
        judge_model=cfg.JUDGE_MODEL,
        embedding_model=cfg.EMBEDDING_MODEL,
        chunk_size=cfg.CHUNK_SIZE,
        chunk_overlap=cfg.CHUNK_OVERLAP,
        num_rag_questions=cfg.NUM_RAG_QUESTIONS,
        num_tqa_questions=cfg.NUM_TQA_QUESTIONS,
    )
    print(f"Run #{run_id} registered in {cfg.DB_PATH}")
    
   
    truthfulqa = load_truthfulqa()
    podcast_text = load_podcast_transcript()
    
    
    docs = [Document(page_content=podcast_text)]
    chunks = chunk_documents(docs)
    try:
        index, chunks = load_vectorstore()
        embedding_cost = 0.0
    except (FileNotFoundError, RuntimeError):
        index, chunks, _, embedding_cost = build_embeddings_and_index(chunks)
    
    
    podcast_questions = pd.DataFrame({"question": [
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
    ]})
    
   # 4
    N_RAG = min(cfg.NUM_RAG_QUESTIONS, len(podcast_questions))
    sampled_rag = podcast_questions.sample(n=N_RAG).reset_index(drop=True)
    rag_rows = []
    
    print(f"\n🔍 Evaluating {N_RAG} RAG questions...")
    for idx, row in tqdm(sampled_rag.iterrows(), total=N_RAG):
        q = row["question"]
        # Retrieve
        retrieved = retrieve(q, index, chunks, k=3)
        context_chunks = [r["chunk"] for r in retrieved]
        context = "\n\n".join(context_chunks)
        prompt = build_rag_prompt(q, context_chunks)
        # Generate
        ds_ans = ask_deepseek(prompt)
        polite_sleep()
        ds_m = get_current_metrics(cfg.DEEPSEEK_MODEL)
        ll_ans = ask_llama(prompt)
        polite_sleep()
        ll_m = get_current_metrics(cfg.LLAMA_MODEL)
        # Judge
        verdict = judge_rag_answers(q, context, ds_ans, ll_ans, ds_m, ll_m)
        parsed = parse_judge_verdict(verdict)
        rag_rows.append({"question": q, "context": context[:300],
                         "deepseek_answer": ds_ans, "deepseek_latency_s": ds_m.get("latency_s", 0),
                         "deepseek_cost_usd": ds_m.get("cost_usd", 0),
                         "llama_answer": ll_ans, "llama_latency_s": ll_m.get("latency_s", 0),
                         "llama_cost_usd": ll_m.get("cost_usd", 0),
                         "judge_verdict": verdict, **parsed})
        polite_sleep()
    
    df_rag = pd.DataFrame(rag_rows)
    df_rag.to_csv(f"{cfg.OUTPUTS_DIR}/rag_evaluation.csv", index=False)
    save_results(df_rag, "rag_results", run_id)
    print(f" Saved RAG evaluation ({len(df_rag)} rows) → CSV + SQLite")
    
    # 5
    N_TQA = min(cfg.NUM_TQA_QUESTIONS, len(truthfulqa))
    sampled_tqa = truthfulqa.sample(n=N_TQA).reset_index()
    tqa_rows = []
    
    print(f"\n Evaluating {N_TQA} TruthfulQA questions...")
    for idx, row in tqdm(sampled_tqa.iterrows(), total=N_TQA):
        q = row["Question"]
        ds_ans = ask_deepseek(q)
        polite_sleep()
        ds_m = get_current_metrics(cfg.DEEPSEEK_MODEL)
        ll_ans = ask_llama(q)
        polite_sleep()
        ll_m = get_current_metrics(cfg.LLAMA_MODEL)
        verdict = judge_truthfulqa_answers(
            q, row["Best Answer"], row["Correct Answers"],
            row["Incorrect Answers"], ds_ans, ll_ans, ds_m, ll_m
        )
        parsed = parse_judge_verdict(verdict)
        tqa_rows.append({"question": q, "best_answer": row["Best Answer"],
                         "deepseek_answer": ds_ans, "deepseek_latency_s": ds_m.get("latency_s", 0),
                         "deepseek_cost_usd": ds_m.get("cost_usd", 0),
                         "llama_answer": ll_ans, "llama_latency_s": ll_m.get("latency_s", 0),
                         "llama_cost_usd": ll_m.get("cost_usd", 0),
                         "judge_verdict": verdict, **parsed})
        polite_sleep()
    
    df_tqa = pd.DataFrame(tqa_rows)
    df_tqa.to_csv(f"{cfg.OUTPUTS_DIR}/tqa_evaluation.csv", index=False)
    save_results(df_tqa, "tqa_results", run_id)
    finish_run(run_id)
    print(f" Saved TruthfulQA evaluation ({len(df_tqa)} rows) → CSV + SQLite")
    
    # 6
    print("\n"+"="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    print(f"RAG: {model_summary(df_rag, 'deepseek')}")
    print(f"TQA: {model_summary(df_tqa, 'deepseek')}")
    print(f"Total cost (including judge): ${totals['cost_usd']:.4f}")
    print(f"Embedding cost: ${embedding_cost:.4f}")
    print(f"✅ Done. Outputs saved in '{cfg.OUTPUTS_DIR}' (run #{run_id} in {cfg.DB_PATH})")

if __name__=="__main__":
        main()