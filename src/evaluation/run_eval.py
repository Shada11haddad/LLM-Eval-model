import os
import time
import pandas as pd
from langchain_core.documents import Document
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import cfg
from src.ingestion.loader import detect_task_type, load_qa_dataset, load_document
from src.ingestion.chunker import chunk_documents
from src.retrieval.vectorstore import get_or_build_vectorstore
from src.retrieval.retriever import retrieve
from src.generation.model_router import generate_answer
from src.generation.qa_generation import generate_qa_pairs
from src.evaluation.judge import judge_rag_answers, judge_open_qa_answers
from src.evaluation.parse_verdict import parse_judge_verdict
from src.evaluation.metrics import get_current_metrics, totals
from src.storage.database import create_run, finish_run, save_results
from src.utils.helpers import build_comparison_table
from src.ingestion.loader import normalize_unknown_qa_file


# How many questions to evaluate at once. Higher = faster, but too high can trip
# rate limits. 5 is the proven sweet spot.
MAX_WORKERS = 5


# ── Prompt templates (for PROMPT ITERATION) ──────────────────────────────────
# These are the DEFAULTS. To iterate, pass a custom string to
# run_evaluation(prompt_template=...). Use the {question} placeholder — and
# {context} as well for the RAG track. They get filled in per question.
DEFAULT_OPEN_QA_PROMPT = (
    "Answer the following question concisely and factually.\n\n"
    "Question:\n{question}\n\nAnswer:"
)

DEFAULT_RAG_PROMPT = """Answer the question using only the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{question}

Answer:"""
# ─────────────────────────────────────────────────────────────────────────────


def _normalize_qa_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map any accepted answer column name to 'reference_answer'"""
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ["answer", "ground_truth", "reference_answer"]:
            rename_map[col] = "reference_answer"
        elif col_lower == "question":
            rename_map[col] = "question"
    return df.rename(columns=rename_map)


def _process_open_qa_question(question, reference_answer, selected_models, prompt_template):
    """Evaluate ONE open_qa question across all models + judge. Returns a row dict."""
    prompt = prompt_template.replace("{question}", question)

    model_answers = {}
    model_metrics = {}
    for model_name in selected_models:
        answer, metrics = generate_answer(model_name, prompt)
        model_answers[model_name] = answer
        model_metrics[model_name] = metrics

    verdict = judge_open_qa_answers(question, reference_answer, model_answers, model_metrics)
    parsed = parse_judge_verdict(verdict)

    row_data = {"question": question, "reference_answer": reference_answer}
    for model_name in selected_models:
        row_data[f"{model_name}_answer"] = model_answers[model_name]
        row_data[f"{model_name}_latency_s"] = model_metrics[model_name].get("latency_s", 0)
        row_data[f"{model_name}_cost_usd"] = model_metrics[model_name].get("cost_usd", 0)
    row_data["judge_verdict"] = verdict
    row_data.update(parsed)
    return row_data


def _process_rag_question(question, reference_answer, selected_models, index, indexed_chunks, prompt_template):
    """Evaluate ONE rag question (retrieve -> models -> judge). Returns a row dict."""
    retrieved = retrieve(question, index, indexed_chunks, k=3)
    context_chunks = [r["chunk"] for r in retrieved]
    context = "\n\n".join(context_chunks)
    prompt = prompt_template.replace("{context}", context).replace("{question}", question)

    model_answers = {}
    model_metrics = {}
    for model_name in selected_models:
        answer, metrics = generate_answer(model_name, prompt)
        model_answers[model_name] = answer
        model_metrics[model_name] = metrics

    verdict = judge_rag_answers(question, context, reference_answer, model_answers, model_metrics)
    parsed = parse_judge_verdict(verdict)

    row_data = {"question": question, "reference_answer": reference_answer, "context": context}
    for model_name in selected_models:
        row_data[f"{model_name}_answer"] = model_answers[model_name]
        row_data[f"{model_name}_latency_s"] = model_metrics[model_name].get("latency_s", 0)
        row_data[f"{model_name}_cost_usd"] = model_metrics[model_name].get("cost_usd", 0)
    row_data["judge_verdict"] = verdict
    row_data.update(parsed)
    return row_data


def _run_parallel(worker, task_args_list):
    """
    Run `worker(*args)` for each args tuple, up to MAX_WORKERS at a time.
    Preserves input order. Skips (with a warning) any question that errors.
    Prints progress + timing.
    """
    total = len(task_args_list)
    results = [None] * total

    def _safe(i, args):
        try:
            return i, worker(*args)
        except Exception as e:
            print(f"    [skip] question {i + 1} failed: {type(e).__name__}: {e}")
            return i, None

    start = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_safe, i, args) for i, args in enumerate(task_args_list)]
        for fut in as_completed(futures):
            i, row = fut.result()
            results[i] = row
            done += 1
            print(f"    [{done}/{total}] questions done ({time.time() - start:.1f}s elapsed)")

    print(f"    All questions finished in {time.time() - start:.1f}s")
    return [r for r in results if r is not None]


def run_evaluation(file_path: str, selected_models: list, prompt_template: str = None,
                   chunk_size: int = None, chunk_overlap: int = None, num_questions: int = None):
    """
    Main evaluation entrypoint.

    Args:
        file_path: path to the uploaded file (Open QA dataset or RAG document)
        selected_models: list of model keys from cfg.MODELS (must NOT include "judge")
        prompt_template: optional custom prompt for PROMPT ITERATION. A string using
            the {question} placeholder (plus {context} for the RAG track). If None,
            the track's default prompt is used. The template actually used is saved
            to the run's `notes` column, so every run is traceable to its prompt.
        chunk_size / chunk_overlap: optional RAG chunking overrides. If None, the
            config defaults (cfg.CHUNK_SIZE / cfg.CHUNK_OVERLAP) are used. Only
            affects the RAG track.
        num_questions: optional cap on how many questions to evaluate. If None, the
            default applies (all questions, up to 50 for QA files). For RAG, it limits
            how many chunks get turned into questions (the full set is still indexed
            for retrieval).

    Returns:
        dict with run_id, task_type, results, comparison_table, and total cost.
    """
    if not selected_models:
        raise ValueError("No models selected for evaluation")

    if "judge" in selected_models:
        raise ValueError("'judge' is reserved and cannot be selected as an evaluated model")

    task_type = detect_task_type(file_path)


    if task_type == "open_qa_needs_normalization":

        normalized_df = normalize_unknown_qa_file(file_path)
        task_type = "open_qa"
    else:
        normalized_df = None
    
    # Resolve the prompt: custom if given, else the track's default.
    if task_type == "open_qa":
        effective_prompt = prompt_template or DEFAULT_OPEN_QA_PROMPT
    elif task_type == "rag":
        effective_prompt = prompt_template or DEFAULT_RAG_PROMPT
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    # Resolve chunking: custom overrides if given, else cfg defaults.
    effective_chunk_size = chunk_size if chunk_size is not None else cfg.CHUNK_SIZE
    effective_chunk_overlap = chunk_overlap if chunk_overlap is not None else cfg.CHUNK_OVERLAP

    run_id = create_run(
        dataset_name=os.path.basename(file_path),
        task_type=task_type,
        judge_model=cfg.MODELS["judge"]["model"],
        embedding_model=cfg.EMBEDDING_MODEL,
        chunk_size=effective_chunk_size,
        chunk_overlap=effective_chunk_overlap,
        notes=effective_prompt,          # ← prompt used, recorded for traceability
    )

    rows = []

    if task_type == "open_qa":

        if normalized_df is not None:
             df = normalized_df   
        else:
             df = load_qa_dataset(file_path)
             df = _normalize_qa_columns(df)

        # Cap the number of questions. A custom num_questions overrides the default 50.
        limit = num_questions if num_questions is not None else 50
        if len(df) > limit:
            df = df.sample(n=limit, random_state=42)

        task_args = [
            (row["question"], row["reference_answer"], selected_models, effective_prompt)
            for _, row in df.iterrows()
        ]
        rows = _run_parallel(_process_open_qa_question, task_args)

        table_name = "open_qa_results"

    else:  # rag (already validated above)

        text = load_document(file_path)
        docs = [Document(page_content=text)]
        chunks = chunk_documents(docs, chunk_size=effective_chunk_size, chunk_overlap=effective_chunk_overlap)

        index_name = f"run_{run_id}_{int(time.time())}"
        index, indexed_chunks, *_ = get_or_build_vectorstore(index_name, chunks)

        # One QA pair per chunk. If num_questions is set, only generate for the
        # first N chunks — the full set is still indexed for retrieval.
        qa_source_chunks = indexed_chunks[:num_questions] if num_questions is not None else indexed_chunks
        qa_df = generate_qa_pairs(qa_source_chunks)

        task_args = [
            (row["question"], row["reference_answer"], selected_models, index, indexed_chunks, effective_prompt)
            for _, row in qa_df.iterrows()
        ]
        rows = _run_parallel(_process_rag_question, task_args)

        table_name = "rag_results"

    from src.evaluation.ragas_eval import ragas_score_batch

    results_df = pd.DataFrame(rows)

    # RAGAS scores per model (RAG track only) — alongside the GPT judge
    if task_type == "rag":
        for model_name in selected_models:
            samples = [
                {
                    "question":  r["question"],
                    "answer":    r[f"{model_name}_answer"],
                    "contexts":  r.get("context", "").split("\n\n") if isinstance(r.get("context"), str) else [],
                    "reference": r["reference_answer"],
                }
                for r in rows
            ]
            ragas_df = ragas_score_batch(samples)
            for col in ragas_df.columns:
                results_df[f"{model_name}_{col}"] = ragas_df[col].values

    save_results(results_df, table_name, run_id)
    finish_run(run_id)
    comparison_df = build_comparison_table(results_df, selected_models)
    return {
        "run_id": run_id,
        "task_type": task_type,
        "table_name": table_name,
        "results": results_df.to_dict(orient="records"),
        "comparison_table": comparison_df.to_dict(orient="records"),
        "total_cost_usd": totals["cost_usd"],
    }